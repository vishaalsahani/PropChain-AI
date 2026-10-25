"""Document-registry anchoring (Phase 5).

Two modes share one interface:

* ``mock``  - no chain is touched. The transaction id is synthetic and the API
  says so. This keeps a fresh checkout runnable without Hardhat.
* ``evm``   - ``DocumentRegistry.sol`` is called on the configured RPC. A hash
  is written by a funded signer and read back from the contract; a missing
  chain, contract or signer is an error, never a silent "success".

Only SHA-256 fingerprints leave the machine. File contents and extracted text
stay in the off-chain store.
"""

from __future__ import annotations

import re
import uuid

from app.config import settings

#: Minimal ABI for the deployed contract (contracts/src/DocumentRegistry.sol).
DOCUMENT_REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "documentId", "type": "uint256"},
            {"internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
        ],
        "name": "registerDocument",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "documentId", "type": "uint256"},
            {"internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
        ],
        "name": "verifyDocument",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "records",
        "outputs": [
            {"internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "address", "name": "uploader", "type": "address"},
            {"internalType": "bool", "name": "exists", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

_SHA256_HEX = re.compile(r"^[0-9a-fA-F]{64}$")


class BlockchainUnavailable(RuntimeError):
    """The configured EVM node, contract or signer is not usable."""


class BlockchainConflict(RuntimeError):
    """The document id is already anchored to a different hash."""


class BlockchainTransactionError(RuntimeError):
    """The chain rejected or did not confirm the registration."""


def file_hash_to_bytes32(file_hash: str) -> bytes:
    """Convert a 64-character SHA-256 hex digest to a contract ``bytes32``."""
    value = file_hash[2:] if file_hash.startswith("0x") else file_hash
    if not _SHA256_HEX.match(value):
        raise ValueError("file_hash must be a 64-character SHA-256 hex digest")
    return bytes.fromhex(value)


def bytes32_to_hash(value: bytes) -> str:
    return value.hex()


class BlockchainService:
    def get_status(self) -> dict:
        if settings.blockchain_mock_mode:
            return {
                "mode": "mock",
                "connected": True,
                "network": "mock",
                "chain_id": None,
                "contract_address": None,
                "account": None,
                "message": "Mock anchoring is active; no EVM node is contacted.",
            }

        try:
            w3 = self._web3()
            account = self._account()
            contract = self._contract(w3)
            code = w3.eth.get_code(contract.address)
            if not code:
                raise BlockchainUnavailable(
                    f"No contract bytecode at {contract.address} on chain {w3.eth.chain_id}."
                )
            return {
                "mode": "evm",
                "connected": True,
                "network": settings.blockchain_network,
                "chain_id": w3.eth.chain_id,
                "contract_address": contract.address,
                "account": account.address,
                "message": "DocumentRegistry is reachable.",
            }
        except Exception as exc:
            return {
                "mode": "evm",
                "connected": False,
                "network": settings.blockchain_network,
                "chain_id": None,
                "contract_address": settings.blockchain_contract_address,
                "account": None,
                "message": str(exc),
            }

    def register_hash(self, document_id: int, file_hash: str) -> dict:
        if settings.blockchain_mock_mode:
            tx_id = f"mock-tx-{uuid.uuid4().hex[:12]}"
            return {
                "success": True,
                "transaction_id": tx_id,
                "document_id": document_id,
                "file_hash": file_hash,
                "mode": "mock",
                "network": "mock",
                "chain_id": None,
                "contract_address": None,
                "block_number": None,
                "note": "Synthetic transaction; no chain write.",
            }

        w3 = self._web3()
        account = self._account()
        contract = self._contract(w3)
        digest = file_hash_to_bytes32(file_hash)

        existing = self._read_record(contract, document_id)
        if existing and existing["exists"]:
            if existing["file_hash"] == bytes32_to_hash(digest):
                return {
                    "success": True,
                    "transaction_id": existing["tx_hash"],
                    "document_id": document_id,
                    "file_hash": file_hash,
                    "mode": "evm",
                    "network": settings.blockchain_network,
                    "chain_id": w3.eth.chain_id,
                    "contract_address": contract.address,
                    "block_number": existing.get("block_number"),
                    "note": "Document id was already anchored to this hash.",
                }
            raise BlockchainConflict(
                f"Document {document_id} is already anchored to a different hash."
            )

        function = contract.functions.registerDocument(document_id, digest)
        try:
            gas_estimate = function.estimate_gas({"from": account.address})
        except Exception:
            gas_estimate = settings.blockchain_gas_limit
        transaction = function.build_transaction(
            {
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "chainId": w3.eth.chain_id,
                "gas": min(max(int(gas_estimate), 100_000), settings.blockchain_gas_limit),
                "gasPrice": w3.eth.gas_price,
            }
        )
        signed = account.sign_transaction(transaction)
        raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction")
        try:
            tx_hash = w3.eth.send_raw_transaction(raw)
            receipt = w3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.blockchain_tx_timeout
            )
        except Exception as exc:
            raise BlockchainTransactionError(str(exc)) from exc

        if receipt.status != 1:
            raise BlockchainTransactionError(
                f"DocumentRegistry rejected the registration (tx {tx_hash.hex()})."
            )

        tx_hex = tx_hash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = f"0x{tx_hex}"
        return {
            "success": True,
            "transaction_id": tx_hex,
            "document_id": document_id,
            "file_hash": file_hash,
            "mode": "evm",
            "network": settings.blockchain_network,
            "chain_id": w3.eth.chain_id,
            "contract_address": contract.address,
            "block_number": receipt.blockNumber,
            "note": "Hash confirmed on-chain.",
        }

    def verify_hash(
        self,
        document_id: int,
        file_hash: str,
        registered_hash: str | None = None,
    ) -> dict:
        """Verify a file hash against the chain (or the local mock record).

        In ``evm`` mode the on-chain record is authoritative. A local database
        row is not accepted as proof of anchoring.
        """
        if settings.blockchain_mock_mode:
            compare_to = registered_hash or ""
            match = file_hash == compare_to
            return {
                "status": "MATCH" if match else "MISMATCH",
                "file_hash": file_hash,
                "registered_hash": compare_to or None,
                "mode": "mock",
                "network": "mock",
                "chain_id": None,
                "contract_address": None,
                "block_number": None,
                "message": (
                    "Hash matches the stored mock record."
                    if match
                    else "Hash mismatch detected against the stored mock record."
                ),
            }

        w3 = self._web3()
        contract = self._contract(w3)
        record = self._read_record(contract, document_id)
        if not record or not record["exists"]:
            return {
                "status": "NOT_REGISTERED",
                "file_hash": file_hash,
                "registered_hash": None,
                "mode": "evm",
                "network": settings.blockchain_network,
                "chain_id": w3.eth.chain_id,
                "contract_address": contract.address,
                "block_number": None,
                "message": "No on-chain record exists for this document.",
            }

        claimed = file_hash[2:] if file_hash.startswith("0x") else file_hash
        match = claimed.lower() == record["file_hash"].lower()
        return {
            "status": "MATCH" if match else "MISMATCH",
            "file_hash": file_hash,
            "registered_hash": record["file_hash"],
            "mode": "evm",
            "network": settings.blockchain_network,
            "chain_id": w3.eth.chain_id,
            "contract_address": contract.address,
            "block_number": record.get("block_number"),
            "message": (
                "On-chain hash matches the current file."
                if match
                else "On-chain hash does not match the current file."
            ),
        }

    # -- internals ---------------------------------------------------------

    def _web3(self):
        if not settings.blockchain_rpc_url:
            raise BlockchainUnavailable("BLOCKCHAIN_RPC_URL is not configured.")
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(settings.blockchain_rpc_url))
        if not w3.is_connected():
            raise BlockchainUnavailable(
                f"EVM node is unavailable at {settings.blockchain_rpc_url}."
            )
        if settings.blockchain_chain_id and w3.eth.chain_id != settings.blockchain_chain_id:
            raise BlockchainUnavailable(
                f"Expected chain {settings.blockchain_chain_id}, connected to {w3.eth.chain_id}."
            )
        return w3

    def _account(self):
        if not settings.blockchain_private_key:
            raise BlockchainUnavailable("BLOCKCHAIN_PRIVATE_KEY is not configured.")
        from eth_account import Account

        try:
            return Account.from_key(settings.blockchain_private_key)
        except Exception as exc:
            raise BlockchainUnavailable("BLOCKCHAIN_PRIVATE_KEY is invalid.") from exc

    def _contract(self, w3):
        if not settings.blockchain_contract_address:
            raise BlockchainUnavailable("BLOCKCHAIN_CONTRACT_ADDRESS is not configured.")
        from web3 import Web3

        if not Web3.is_address(settings.blockchain_contract_address):
            raise BlockchainUnavailable("BLOCKCHAIN_CONTRACT_ADDRESS is not a valid address.")
        address = Web3.to_checksum_address(settings.blockchain_contract_address)
        return w3.eth.contract(address=address, abi=DOCUMENT_REGISTRY_ABI)

    def _read_record(self, contract, document_id: int) -> dict | None:
        try:
            file_hash, timestamp, uploader, exists = contract.functions.records(
                document_id
            ).call()
        except Exception as exc:
            raise BlockchainUnavailable(f"Could not read DocumentRegistry: {exc}") from exc
        if not exists:
            return None
        return {
            "file_hash": file_hash.hex() if isinstance(file_hash, bytes) else str(file_hash),
            "timestamp": int(timestamp),
            "uploader": uploader,
            "exists": True,
            "block_number": None,
            "tx_hash": f"on-chain-record-{document_id}",
        }


blockchain_service = BlockchainService()
