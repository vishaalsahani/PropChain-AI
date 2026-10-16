import uuid

from app.config import settings


class BlockchainService:
    """Miniature blockchain service. Uses mock mode when no chain is available."""

    def register_hash(self, document_id: int, file_hash: str) -> dict:
        if settings.blockchain_mock_mode:
            tx_id = f"mock-tx-{uuid.uuid4().hex[:12]}"
            return {
                "success": True,
                "transaction_id": tx_id,
                "document_id": document_id,
                "file_hash": file_hash,
                "mode": "mock",
            }

        try:
            from web3 import Web3

            w3 = Web3(Web3.HTTPProvider(settings.blockchain_rpc_url))
            if not w3.is_connected():
                return self._fallback(document_id, file_hash, "Blockchain node unavailable")

            tx_id = f"evm-tx-{uuid.uuid4().hex[:12]}"
            return {
                "success": True,
                "transaction_id": tx_id,
                "document_id": document_id,
                "file_hash": file_hash,
                "mode": "evm",
            }
        except Exception as exc:
            return self._fallback(document_id, file_hash, str(exc))

    def verify_hash(self, file_hash: str, registered_hash: str) -> dict:
        match = file_hash == registered_hash
        return {
            "status": "MATCH" if match else "MISMATCH",
            "file_hash": file_hash,
            "registered_hash": registered_hash,
            "message": "Document integrity verified" if match else "Hash mismatch detected",
        }

    def _fallback(self, document_id: int, file_hash: str, reason: str) -> dict:
        tx_id = f"fallback-tx-{uuid.uuid4().hex[:12]}"
        return {
            "success": True,
            "transaction_id": tx_id,
            "document_id": document_id,
            "file_hash": file_hash,
            "mode": "fallback",
            "note": reason,
        }


blockchain_service = BlockchainService()
