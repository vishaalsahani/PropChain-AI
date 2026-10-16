"""AC-1 upload validation: accepted formats processed; bad input rejected clearly.

Spec (Review-III slide 12, AC-1): "PDF and image files are accepted; unsupported
formats are rejected with a clear message."

Validation is signature-level on purpose: the magic bytes prove the container
format, while decoding happens downstream in the OCR stage (covered by the
engine tests). The fake engines never open the file, so these tests exercise
exactly the upload contract.
"""

import base64

import pytest

#: Minimal well-formed PDF (signature + catalog + EOF).
MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
#: 1x1 transparent PNG (canonical minimal PNG).
MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
#: JPEG signature + filler — enough for the signature check under fake engines.
MINIMAL_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


@pytest.fixture(scope="module")
def flow(app_client):
    client = app_client
    r = client.post(
        "/auth/register",
        json={"email": "ac1-upload@example.com", "full_name": "AC1 Upload", "password": "secret123"},
    )
    assert r.status_code == 200, r.text
    r = client.post("/auth/login", data={"username": "ac1-upload@example.com", "password": "secret123"})
    assert r.status_code == 200, r.text
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.post("/properties", headers=headers, json={"title": "AC-1 Upload Checks", "state": "Maharashtra"})
    assert r.status_code == 200, r.text
    return {"client": client, "headers": headers, "property_id": r.json()["id"]}


def _upload(flow, filename, data, content_type="application/octet-stream"):
    return flow["client"].post(
        f"/documents/upload/{flow['property_id']}",
        headers=flow["headers"],
        files={"file": (filename, data, content_type)},
    )


def test_unsupported_extension_rejected_with_clear_message(flow):
    r = _upload(flow, "notes.txt", b"just some text")
    assert r.status_code == 400, r.text
    detail = r.json()["detail"]
    assert "Unsupported file type" in detail
    assert "PDF" in detail and "PNG" in detail


def test_unrecognised_bytes_rejected(flow):
    r = _upload(flow, "scan.pdf", b"this is not a pdf at all")
    assert r.status_code == 400, r.text
    assert "Unsupported file content" in r.json()["detail"]


def test_content_extension_mismatch_rejected(flow):
    r = _upload(flow, "fake.pdf", MINIMAL_PNG)
    assert r.status_code == 400, r.text
    detail = r.json()["detail"]
    assert "does not match its extension" in detail
    assert "PNG" in detail


def test_empty_file_rejected(flow):
    r = _upload(flow, "empty.pdf", b"")
    assert r.status_code == 400, r.text
    assert "Empty file" in r.json()["detail"]


def test_oversized_file_rejected(flow, monkeypatch):
    # Import inside the test: conftest purges and re-imports app modules, so a
    # module-level import would hold the pre-purge settings instance.
    from app.config import settings

    monkeypatch.setattr(settings, "max_upload_mb", 0)
    r = _upload(flow, "big.pdf", MINIMAL_PDF)
    assert r.status_code == 413, r.text
    assert "too large" in r.json()["detail"]


def test_valid_pdf_accepted_and_processed(flow):
    r = _upload(flow, "deed.pdf", MINIMAL_PDF, "application/pdf")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "completed"
    assert len(body["file_hash"]) == 64
    assert body["filename"] == "deed.pdf"


def test_valid_png_accepted_and_processed(flow):
    r = _upload(flow, "scan.png", MINIMAL_PNG, "image/png")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "completed"
    assert body["filename"] == "scan.png"


def test_valid_jpeg_signature_accepted(flow):
    r = _upload(flow, "photo.jpeg", MINIMAL_JPEG, "image/jpeg")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"
