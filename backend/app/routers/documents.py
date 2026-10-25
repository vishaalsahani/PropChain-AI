import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import client_ip, get_current_user
from app.models import Document, Property, User
from app.schemas import DocumentOut
from app.services.access import property_for_read
from app.services.analysis_engine import run_document_pipeline
from app.services.audit import record
from app.utils.hashing import sha256_file

router = APIRouter(prefix="/documents", tags=["documents"])

#: Accepted formats (Specs p.1: "PDF, JPG, JPEG, and PNG for the prototype")
#: and their magic-byte signatures — an extension alone is not proof of
#: content, so both are checked (AC-1).
_SIGNATURES: tuple[tuple[str, bytes, str], ...] = (
    ("pdf", b"%PDF-", "application/pdf"),
    ("jpeg", b"\xff\xd8\xff", "image/jpeg"),
    ("png", b"\x89PNG\r\n\x1a\n", "image/png"),
)
_EXTENSION_CLASS = {".pdf": "pdf", ".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png"}
_ACCEPTED_MESSAGE = "Accepted formats are PDF, JPG, JPEG and PNG"


def _sniff_content(data: bytes) -> tuple[str, str] | None:
    """Return (content-class, mime) from the file signature, or None."""
    for content_class, magic, mime in _SIGNATURES:
        if data.startswith(magic):
            return content_class, mime
    return None


@router.post("/upload/{property_id}", response_model=DocumentOut)
async def upload_document(
    property_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = db.query(Property).filter(Property.id == property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    suffix = Path(file.filename or "upload.bin").suffix.lower()
    expected_class = _EXTENSION_CLASS.get(suffix)
    if expected_class is None:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {_ACCEPTED_MESSAGE}")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: the limit is {settings.max_upload_mb} MB",
        )

    sniffed = _sniff_content(data)
    if sniffed is None:
        raise HTTPException(status_code=400, detail=f"Unsupported file content: {_ACCEPTED_MESSAGE}")
    content_class, content_type = sniffed
    if content_class != expected_class:
        raise HTTPException(
            status_code=400,
            detail=(
                "File content does not match its extension: "
                f"a {suffix} file containing {content_class.upper()} data is not accepted"
            ),
        )

    storage_dir = Path(settings.storage_path) / f"property_{property_id}"
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    stored_path = storage_dir / stored_name
    stored_path.write_bytes(data)

    file_hash = sha256_file(stored_path)
    document = Document(
        property_id=property_id,
        filename=file.filename or stored_name,
        file_path=str(stored_path),
        file_hash=file_hash,
        content_type=content_type,
        uploaded_by=current_user.id,
    )
    db.add(document)
    db.flush()  # assigns document.id so the audit row references it in the same commit
    record(
        db,
        "document.uploaded",
        "document",
        entity_id=document.id,
        actor_user_id=current_user.id,
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(document)

    try:
        run_document_pipeline(db, document)
    except Exception as exc:
        # The row stays in status=failed so the user can see what happened.
        raise HTTPException(status_code=502, detail=f"Document processing failed: {exc}") from exc
    return document


@router.get("/property/{property_id}", response_model=list[DocumentOut])
def list_documents(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    property_for_read(db, current_user, property_id)
    return db.query(Document).filter(Document.property_id == property_id).order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    property_for_read(db, current_user, document.property_id)
    return document


@router.get("/{document_id}/extracted")
def get_extracted_data(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    property_for_read(db, current_user, document.property_id)
    return json.loads(document.extracted_data) if document.extracted_data else {}
