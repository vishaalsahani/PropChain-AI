"""Blockchain integrity endpoints (Phase 5).

Registration and verification both talk to ``DocumentRegistry`` when mock mode
is off. Failures are surfaced as 5xx/409 responses; they never downgrade to a
synthetic success. The response carries the network, chain id, contract and
block number so the UI can tell a real anchor from a mock one.
"""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import client_ip, get_current_user
from app.models import BlockchainRecord, BlockchainRecordStatus, Document, Property, User
from app.schemas import BlockchainStatusOut, BlockchainVerifyResult
from app.services.audit import record
from app.services.blockchain_service import (
    BlockchainConflict,
    BlockchainTransactionError,
    BlockchainUnavailable,
    blockchain_service,
)
from app.utils.hashing import sha256_file

router = APIRouter(prefix="/blockchain", tags=["blockchain"])


def _owned_document(db: Session, document_id: int, user: User) -> Document:
    document = (
        db.query(Document)
        .join(Property)
        .filter(Document.id == document_id, Property.owner_id == user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def _latest_record(db: Session, document_id: int) -> BlockchainRecord | None:
    return (
        db.query(BlockchainRecord)
        .filter(BlockchainRecord.document_id == document_id)
        .order_by(BlockchainRecord.id.desc())
        .first()
    )


@router.get("/status", response_model=BlockchainStatusOut)
def blockchain_status():
    """Report the configured anchoring mode without touching a document."""
    return blockchain_service.get_status()


@router.post("/register/{document_id}", response_model=BlockchainVerifyResult)
def register_document_hash(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = _owned_document(db, document_id, current_user)

    try:
        result = blockchain_service.register_hash(document.id, document.file_hash)
    except BlockchainConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except BlockchainUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except BlockchainTransactionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - surface a clear chain failure to the UI
        raise HTTPException(status_code=502, detail=f"Blockchain registration failed: {exc}") from exc

    existing = _latest_record(db, document.id)
    tx_hash = result["transaction_id"]
    # Idempotent re-registration returns an on-chain marker rather than a tx;
    # preserve the original transaction id already stored in the DB.
    if existing and tx_hash.startswith("on-chain-record-"):
        tx_hash = existing.tx_hash

    now = datetime.now(timezone.utc)
    status = (
        BlockchainRecordStatus.mock
        if result.get("mode") == "mock"
        else BlockchainRecordStatus.confirmed
    )
    if existing is None:
        existing = BlockchainRecord(document_id=document.id, property_id=document.property_id)
        db.add(existing)
    existing.property_id = document.property_id
    existing.network = result.get("network") or result.get("mode") or "mock"
    existing.chain_id = result.get("chain_id")
    existing.contract_address = result.get("contract_address")
    existing.tx_hash = tx_hash
    existing.block_number = result.get("block_number")
    existing.registered_hash = document.file_hash
    existing.status = status
    existing.verified_at = now

    document.blockchain_tx = tx_hash
    document.blockchain_verified = True
    record(
        db,
        "blockchain.registered",
        "document",
        entity_id=document.id,
        actor_user_id=current_user.id,
        detail={
            "mode": result.get("mode"),
            "network": result.get("network"),
            "chain_id": result.get("chain_id"),
            "tx": tx_hash,
        },
        ip_address=client_ip(request),
    )
    db.commit()

    return BlockchainVerifyResult(
        document_id=document.id,
        file_hash=document.file_hash,
        status="REGISTERED",
        blockchain_tx=tx_hash,
        message=f"Hash registered ({result.get('mode', 'unknown')} mode).",
        mode=result.get("mode"),
        network=result.get("network"),
        chain_id=result.get("chain_id"),
        contract_address=result.get("contract_address"),
        block_number=result.get("block_number"),
        registered_hash=document.file_hash,
    )


@router.post("/verify/{document_id}", response_model=BlockchainVerifyResult)
def verify_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = _owned_document(db, document_id, current_user)
    path = Path(document.file_path)
    if not path.exists():
        raise HTTPException(status_code=410, detail="The stored file is missing from the off-chain store.")
    current_hash = sha256_file(path)

    try:
        result = blockchain_service.verify_hash(
            document.id, current_hash, registered_hash=document.file_hash
        )
    except BlockchainUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Blockchain verification failed: {exc}") from exc

    document.blockchain_verified = result["status"] == "MATCH"
    if document.blockchain_verified:
        latest = _latest_record(db, document.id)
        if latest:
            latest.verified_at = datetime.now(timezone.utc)
    record(
        db,
        "blockchain.verified"
        if result["status"] == "MATCH"
        else "blockchain.verification_failed",
        "document",
        entity_id=document.id,
        actor_user_id=current_user.id,
        detail={
            "status": result["status"],
            "mode": result.get("mode"),
            "chain_id": result.get("chain_id"),
        },
        ip_address=client_ip(request),
    )
    db.commit()

    return BlockchainVerifyResult(
        document_id=document.id,
        file_hash=current_hash,
        status=result["status"],
        blockchain_tx=document.blockchain_tx,
        message=result["message"],
        mode=result.get("mode"),
        network=result.get("network"),
        chain_id=result.get("chain_id"),
        contract_address=result.get("contract_address"),
        block_number=result.get("block_number"),
        registered_hash=result.get("registered_hash"),
    )
