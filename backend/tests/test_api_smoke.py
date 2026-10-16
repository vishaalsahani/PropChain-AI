"""End-to-end API smoke test — pytest port of the Phase 0 ``smoke_api.py`` script.

Runs fully in-process through ``fastapi.testclient.TestClient`` against a temp
SQLite DB and temp storage directory (see ``conftest.py``); it never touches the
live server on port 8000.

The tests below are intentionally ordered (pytest preserves definition order
within a module) and share one ``flow`` object, because they walk a single
sequential user journey: register -> login -> property -> uploads -> analysis ->
blockchain register/verify/tamper -> PDF report.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pymupdf  # type: ignore[import-untyped]
import pytest

EMAIL = "demo@propchainai.com"  # .test/.example TLDs are rejected by email-validator
PASSWORD = "demo1234"

# Parity contract for the two-document demo flow (sale_deed + 7_12_extract):
# exactly one rule finding (missing predecessor document, severity=high -> 6
# points * 5 == 30.0) and the two-node demo ownership chain.
EXPECTED_FINDINGS = 1
EXPECTED_OWNERSHIP_NODES = 2
EXPECTED_RISK_SCORE = 30.0


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_pdf(path: Path, heading: str) -> Path:
    """Create a small real PDF at runtime (text layer, no OCR needed)."""
    doc = pymupdf.open()
    try:
        page = doc.new_page()
        page.insert_text((72, 72), heading)
        page.insert_text((72, 96), "PropChain-AI runtime test fixture.")
        doc.save(str(path))
    finally:
        doc.close()
    return path


class SmokeFlow:
    """Mutable state shared by the ordered tests of this module."""

    def __init__(self, client, storage: Path):
        self.client = client
        self.storage = Path(storage)
        self.headers: dict[str, str] = {}
        self.property_id: int | None = None
        self.documents: list[dict] = []
        self.analysis: dict | None = None

    def auth_headers(self) -> dict[str, str]:
        assert self.headers, "login must run before this step"
        return self.headers

    def analyze(self) -> dict:
        """Run the property analysis once and cache the response body."""
        if self.analysis is None:
            r = self.client.post(f"/analysis/run/{self.property_id}", headers=self.auth_headers())
            assert r.status_code == 200, r.text
            self.analysis = r.json()
        return self.analysis


@pytest.fixture(scope="module")
def flow(app_client, storage_path) -> SmokeFlow:
    return SmokeFlow(app_client, storage_path)


def test_health(app_client):
    r = app_client.get("/health")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert body["components"]["blockchain"] == "mock"  # BLOCKCHAIN_MOCK_MODE=true


def test_register(flow):
    r = flow.client.post(
        "/auth/register",
        json={"email": EMAIL, "full_name": "Demo User", "password": PASSWORD},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == EMAIL
    assert body["role"] == "buyer"


def test_login(flow):
    r = flow.client.post("/auth/login", data={"username": EMAIL, "password": PASSWORD})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    assert token
    flow.headers = {"Authorization": f"Bearer {token}"}


def test_list_properties_empty(flow):
    r = flow.client.get("/properties", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    assert r.json() == []


def test_create_property(flow):
    r = flow.client.post(
        "/properties",
        headers=flow.auth_headers(),
        json={
            "title": "Smoke Test Plot",
            "state": "Maharashtra",
            "district": "Pune",
            "taluka": "Haveli",
            "village": "Wagholi",
            "survey_number": "124/A",
            "gat_number": "456",
            "area_sqft": 1200,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["title"] == "Smoke Test Plot"
    assert body["status"] == "draft"
    assert body["risk_score"] is None
    flow.property_id = body["id"]


def test_upload_two_documents(flow, tmp_path):
    expected = {"sale_deed_demo.pdf": "sale_deed", "7_12_extract_demo.pdf": "7_12_extract"}
    for filename, doc_type in expected.items():
        pdf = make_pdf(tmp_path / filename, filename.replace("_", " "))
        with pdf.open("rb") as handle:
            r = flow.client.post(
                f"/documents/upload/{flow.property_id}",
                headers=flow.auth_headers(),
                files={"file": (filename, handle, "application/pdf")},
            )
        assert r.status_code == 200, r.text
        body = r.json()
        # filename-based classifier must map the two demo names to their doc types
        assert body["doc_type"] == doc_type, body
        assert body["status"] == "completed"
        assert len(body["file_hash"]) == 64
        flow.documents.append(body)

    assert len(flow.documents) == 2


def test_list_documents(flow):
    r = flow.client.get(f"/documents/property/{flow.property_id}", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body) >= 2
    assert {d["id"] for d in body} >= {d["id"] for d in flow.documents}


def test_extracted_data(flow):
    doc = flow.documents[0]
    r = flow.client.get(f"/documents/{doc['id']}/extracted", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["doc_type"] == doc["doc_type"]
    # mock extraction payload drives the analysis parity contract below, so the
    # identifier fields the rule engine/compare step reads must be present
    assert body["survey_number"]
    assert body["area_sqft"]


def test_run_analysis(flow):
    body = flow.analyze()
    assert body["property_id"] == flow.property_id
    # parity contract — a refactor must not change these numbers
    assert len(body["findings"]) == EXPECTED_FINDINGS, body["findings"]
    assert len(body["ownership_chain"]) == EXPECTED_OWNERSHIP_NODES, body["ownership_chain"]
    assert body["risk_score"] == EXPECTED_RISK_SCORE, body["risk_score"]


def test_get_findings(flow):
    flow.analyze()  # idempotent: analysis already ran for the parity assertions
    r = flow.client.get(f"/analysis/{flow.property_id}/findings", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    findings = r.json()
    assert len(findings) == EXPECTED_FINDINGS, findings
    # severity=high is what makes EXPECTED_RISK_SCORE = 6 points * 5 (parity contract)
    assert findings[0]["severity"] == "high"
    assert findings[0]["title"]


def test_get_ownership_chain(flow):
    flow.analyze()
    r = flow.client.get(f"/analysis/{flow.property_id}/ownership", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    chain = r.json()
    assert len(chain) == EXPECTED_OWNERSHIP_NODES, chain
    assert [node["sequence"] for node in chain] == [1, 2]
    assert all(node["person_name"] for node in chain)


def test_blockchain_register_and_verify_match(flow):
    doc = flow.documents[0]
    r = flow.client.post(f"/blockchain/register/{doc['id']}", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "REGISTERED"
    assert r.json()["blockchain_tx"].startswith("mock-tx-")

    r = flow.client.post(f"/blockchain/verify/{doc['id']}", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "MATCH", r.json()


def test_tamper_detection(flow, storage_path):
    doc = flow.documents[0]
    storage = Path(storage_path)

    # Repeated runs can leave several stored copies sharing the uploaded bytes
    # (same demo content -> same hash), so tamper *every* copy or verify may read
    # an untouched duplicate and legitimately stay MATCH.
    copies = [p for p in storage.rglob("*") if p.is_file() and sha256_file(p) == doc["file_hash"]]
    assert copies, f"no stored file under {storage} matched the registered hash"

    originals = {p: p.read_bytes() for p in copies}
    try:
        for path in copies:
            path.write_bytes(originals[path] + b"tampered")
        r = flow.client.post(f"/blockchain/verify/{doc['id']}", headers=flow.auth_headers())
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "MISMATCH", r.json()
    finally:
        for path, content in originals.items():
            path.write_bytes(content)

    r = flow.client.post(f"/blockchain/verify/{doc['id']}", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "MATCH", r.json()


def test_download_pdf_report(flow):
    r = flow.client.get(f"/reports/{flow.property_id}/pdf", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content[:4] == b"%PDF"
    assert len(r.content) > 1000
