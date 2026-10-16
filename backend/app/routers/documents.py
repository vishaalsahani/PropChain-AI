import json
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Document, Property, User
from app.schemas import DocumentOut
from app.services.analysis_engine import run_document_pipeline
from app.utils.hashing import sha256_file

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload/{property_id}", response_model=DocumentOut)
async def upload_document(
    property_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = db.query(Property).filter(Property.id == property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    allowed = {".pdf", ".jpg", ".jpeg", ".png"}
    suffix = Path(file.filename or "upload.bin").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    storage_dir = Path(settings.storage_path) / f"property_{property_id}"
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    stored_path = storage_dir / stored_name

    with stored_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_hash = sha256_file(stored_path)
    document = Document(
        property_id=property_id,
        filename=file.filename or stored_name,
        file_path=str(stored_path),
        file_hash=file_hash,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    run_document_pipeline(db, document)
    return document


@router.get("/property/{property_id}", response_model=list[DocumentOut])
def list_documents(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = db.query(Property).filter(Property.id == property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    return db.query(Document).filter(Document.property_id == property_id).order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).join(Property).filter(Document.id == document_id, Property.owner_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/extracted")
def get_extracted_data(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).join(Property).filter(Document.id == document_id, Property.owner_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return json.loads(document.extracted_data) if document.extracted_data else {}
