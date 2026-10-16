from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Document, Property, User
from app.schemas import BlockchainVerifyResult
from app.services.blockchain_service import blockchain_service
from app.utils.hashing import sha256_file

router = APIRouter(prefix="/blockchain", tags=["blockchain"])


@router.post("/register/{document_id}", response_model=BlockchainVerifyResult)
def register_document_hash(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .join(Property)
        .filter(Document.id == document_id, Property.owner_id == current_user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    result = blockchain_service.register_hash(document.id, document.file_hash)
    document.blockchain_tx = result["transaction_id"]
    document.blockchain_verified = True
    db.commit()

    return BlockchainVerifyResult(
        document_id=document.id,
        file_hash=document.file_hash,
        status="REGISTERED",
        blockchain_tx=result["transaction_id"],
        message=f"Hash registered on blockchain ({result.get('mode', 'unknown')} mode)",
    )


@router.post("/verify/{document_id}", response_model=BlockchainVerifyResult)
def verify_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .join(Property)
        .filter(Document.id == document_id, Property.owner_id == current_user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    current_hash = sha256_file(Path(document.file_path))
    result = blockchain_service.verify_hash(current_hash, document.file_hash)
    document.blockchain_verified = result["status"] == "MATCH"
    db.commit()

    return BlockchainVerifyResult(
        document_id=document.id,
        file_hash=current_hash,
        status=result["status"],
        blockchain_tx=document.blockchain_tx,
        message=result["message"],
    )
