"""Phase 5 anchoring: mock provenance, fail-closed EVM errors and bytes32 conversion."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pymupdf  # type: ignore[import-untyped]
import pytest

EMAIL = "chain-owner@propchainai.com"
PASSWORD = "chain-pass-1234"


def make_pdf(path: Path) -> Path:
    doc = pymupdf.open()
    try:
        page = doc.new_page()
        page.insert_text((72, 72), "Sale Deed - chain fixture")
        doc.save(str(path))
    finally:
        doc.close()
    return path


def fetch_one(db_path: Path, sql: str, params: tuple = ()) -> tuple | None:
    connection = sqlite3.connect(str(db_path))
    try:
        return connection.execute(sql, params).fetchone()
    finally:
        connection.close()


class ChainFlow:
    def __init__(self, client, db_path: Path):
        self.client = client
        self.db_path = Path(db_path)
        self.headers: dict[str, str] = {}
        self.property_id: int | None = None
        self.document_id: int | None = None
        self.file_hash: str | None = None


@pytest.fixture(scope="module")
def flow(app_env) -> ChainFlow:
    return ChainFlow(app_env["client"], app_env["db_path"])


def test_file_hash_conversion():
    from app.services.blockchain_service import file_hash_to_bytes32

    digest = "ab" * 32
    assert file_hash_to_bytes32(digest) == bytes.fromhex(digest)
    assert file_hash_to_bytes32("0x" + digest) == bytes.fromhex(digest)
    with pytest.raises(ValueError):
        file_hash_to_bytes32("not-a-hash")


def test_setup_document(flow, tmp_path):
    registered = flow.client.post(
        "/auth/register",
        json={"email": EMAIL, "full_name": "Chain Owner", "password": PASSWORD},
    )
    assert registered.status_code == 200, registered.text
    login = flow.client.post("/auth/login", data={"username": EMAIL, "password": PASSWORD})
    assert login.status_code == 200, login.text
    flow.headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    prop = flow.client.post(
        "/properties",
        headers=flow.headers,
        json={"title": "Chain Plot", "state": "Maharashtra", "survey_number": "77"},
    )
    assert prop.status_code == 200, prop.text
    flow.property_id = prop.json()["id"]

    pdf = make_pdf(tmp_path / "sale_deed_chain.pdf")
    with pdf.open("rb") as handle:
        upload = flow.client.post(
            f"/documents/upload/{flow.property_id}",
            headers=flow.headers,
            files={"file": ("sale_deed_chain.pdf", handle, "application/pdf")},
        )
    assert upload.status_code == 200, upload.text
    flow.document_id = upload.json()["id"]
    flow.file_hash = upload.json()["file_hash"]


def test_status_reports_mock(flow):
    response = flow.client.get("/blockchain/status")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "mock"
    assert body["connected"] is True
    assert "Mock" in body["message"]


def test_register_writes_provenance_and_mock_record(flow):
    response = flow.client.post(
        f"/blockchain/register/{flow.document_id}", headers=flow.headers
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "REGISTERED"
    assert body["mode"] == "mock"
    assert body["network"] == "mock"
    assert body["chain_id"] is None
    assert body["blockchain_tx"].startswith("mock-tx-")
    assert body["registered_hash"] == flow.file_hash

    record = fetch_one(
        flow.db_path,
        "SELECT network, tx_hash, registered_hash, status FROM blockchain_records "
        "WHERE document_id = ? ORDER BY id DESC",
        (flow.document_id,),
    )
    assert record is not None
    assert record[0] == "mock"
    assert record[1].startswith("mock-tx-")
    assert record[2] == flow.file_hash
    assert record[3] == "mock"


def test_verify_matches_then_detects_tamper(flow, storage_path):
    match = flow.client.post(
        f"/blockchain/verify/{flow.document_id}", headers=flow.headers
    )
    assert match.status_code == 200, match.text
    assert match.json()["status"] == "MATCH"
    assert match.json()["mode"] == "mock"

    row = fetch_one(
        flow.db_path,
        "SELECT file_path FROM documents WHERE id = ?",
        (flow.document_id,),
    )
    assert row is not None
    path = Path(row[0])
    if not path.is_absolute():
        path = Path(storage_path) / path.name
    path.write_bytes(path.read_bytes() + b"\n tampered")

    mismatch = flow.client.post(
        f"/blockchain/verify/{flow.document_id}", headers=flow.headers
    )
    assert mismatch.status_code == 200, mismatch.text
    assert mismatch.json()["status"] == "MISMATCH"

    documents = flow.client.get(
        f"/documents/property/{flow.property_id}", headers=flow.headers
    ).json()
    document = next(item for item in documents if item["id"] == flow.document_id)
    assert document["blockchain_verified"] is False


def test_real_mode_fails_closed_when_node_is_unreachable(flow, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "blockchain_mock_mode", False)
    monkeypatch.setattr(settings, "blockchain_rpc_url", "http://127.0.0.1:1")
    response = flow.client.post(
        f"/blockchain/register/{flow.document_id}", headers=flow.headers
    )
    assert response.status_code == 503, response.text
    assert "unavailable" in response.json()["detail"].lower()
