"""Phase 6 reviewer workflow: findings, run decisions and immutable history."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pymupdf  # type: ignore[import-untyped]
import pytest

OWNER_EMAIL = "review-owner@propchainai.com"
REVIEWER_EMAIL = "review-reviewer@propchainai.com"
OTHER_EMAIL = "review-other@propchainai.com"
PASSWORD = "review-pass-1234"


def make_pdf(path: Path, heading: str) -> Path:
    doc = pymupdf.open()
    try:
        page = doc.new_page()
        page.insert_text((72, 72), heading)
        page.insert_text((72, 96), "PropChain-AI reviewer workflow fixture.")
        doc.save(str(path))
    finally:
        doc.close()
    return path


def set_role(db_path: Path, email: str, role: str) -> None:
    connection = sqlite3.connect(str(db_path))
    try:
        connection.execute("UPDATE users SET role = ? WHERE email = ?", (role, email))
        connection.commit()
    finally:
        connection.close()


def fetch_one(db_path: Path, sql: str, params: tuple = ()) -> tuple | None:
    connection = sqlite3.connect(str(db_path))
    try:
        return connection.execute(sql, params).fetchone()
    finally:
        connection.close()


class ReviewFlow:
    def __init__(self, client, db_path: Path):
        self.client = client
        self.db_path = Path(db_path)
        self.owner_headers: dict[str, str] = {}
        self.reviewer_headers: dict[str, str] = {}
        self.other_headers: dict[str, str] = {}
        self.property_id: int | None = None
        self.finding_id: int | None = None
        self.run_id: int | None = None

    def owner(self) -> dict[str, str]:
        return self.owner_headers

    def reviewer(self) -> dict[str, str]:
        return self.reviewer_headers


@pytest.fixture(scope="module")
def flow(app_env) -> ReviewFlow:
    return ReviewFlow(app_env["client"], app_env["db_path"])


def login(flow: ReviewFlow, email: str, attribute: str) -> None:
    response = flow.client.post("/auth/login", data={"username": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    setattr(flow, attribute, {"Authorization": f"Bearer {response.json()['access_token']}"})


def test_register_accounts(flow):
    for email, name in (
        (OWNER_EMAIL, "Review Owner"),
        (REVIEWER_EMAIL, "Review Reviewer"),
        (OTHER_EMAIL, "Other Owner"),
    ):
        response = flow.client.post(
            "/auth/register",
            json={"email": email, "full_name": name, "password": PASSWORD},
        )
        assert response.status_code == 200, response.text
    # The public API intentionally cannot mint reviewer/admin accounts.
    set_role(flow.db_path, REVIEWER_EMAIL, "reviewer")
    login(flow, OWNER_EMAIL, "owner_headers")
    login(flow, REVIEWER_EMAIL, "reviewer_headers")
    login(flow, OTHER_EMAIL, "other_headers")


def test_owner_creates_and_analyses_property(flow, tmp_path):
    response = flow.client.post(
        "/properties",
        headers=flow.owner(),
        json={
            "title": "Review Flow Plot",
            "state": "Maharashtra",
            "district": "Pune",
            "taluka": "Haveli",
            "village": "Wagholi",
            "survey_number": "991",
            "gat_number": "42",
            "area_sqft": 1500,
        },
    )
    assert response.status_code == 200, response.text
    flow.property_id = response.json()["id"]

    for filename in ("sale_deed_review.pdf", "7_12_extract_review.pdf"):
        pdf = make_pdf(tmp_path / filename, filename.replace("_", " "))
        with pdf.open("rb") as handle:
            uploaded = flow.client.post(
                f"/documents/upload/{flow.property_id}",
                headers=flow.owner(),
                files={"file": (filename, handle, "application/pdf")},
            )
        assert uploaded.status_code == 200, uploaded.text

    analyzed = flow.client.post(
        f"/analysis/run/{flow.property_id}", headers=flow.owner()
    )
    assert analyzed.status_code == 200, analyzed.text
    body = analyzed.json()
    assert body["findings"], body
    flow.finding_id = body["findings"][0]["id"]

    runs = flow.client.get(f"/analysis/{flow.property_id}/runs", headers=flow.owner())
    assert runs.status_code == 200, runs.text
    flow.run_id = runs.json()[0]["id"]
    assert runs.json()[0]["review_status"] == "pending"
    assert runs.json()[0]["finding_count"] >= 1


def test_owner_can_read_review_state_but_cannot_review(flow):
    response = flow.client.get(f"/review/queue", headers=flow.owner())
    assert response.status_code == 403, response.text

    response = flow.client.patch(
        f"/review/findings/{flow.finding_id}",
        headers=flow.owner(),
        json={"status": "confirmed", "note": "I agree"},
    )
    assert response.status_code == 403, response.text

    verdict = flow.client.get(f"/analysis/{flow.property_id}/verdict", headers=flow.owner())
    assert verdict.status_code == 200, verdict.text
    assert verdict.json()["review_status"] == "pending"


def test_other_owner_cannot_read_the_file(flow):
    response = flow.client.get(f"/properties/{flow.property_id}", headers=flow.other_headers)
    assert response.status_code == 404, response.text
    response = flow.client.get(
        f"/analysis/{flow.property_id}/findings", headers=flow.other_headers
    )
    assert response.status_code == 404, response.text


def test_reviewer_can_read_everything(flow):
    for path in (
        f"/properties/{flow.property_id}",
        f"/documents/property/{flow.property_id}",
        f"/analysis/{flow.property_id}/findings",
        f"/analysis/{flow.property_id}/ownership",
        f"/analysis/{flow.property_id}/verdict",
        f"/analysis/{flow.property_id}/runs",
    ):
        response = flow.client.get(path, headers=flow.reviewer())
        assert response.status_code == 200, f"{path}: {response.text}"


def test_queue_lists_latest_run(flow):
    response = flow.client.get("/review/queue", headers=flow.reviewer())
    assert response.status_code == 200, response.text
    items = response.json()
    item = next((row for row in items if row["property_id"] == flow.property_id), None)
    assert item is not None, items
    assert item["run_id"] == flow.run_id
    assert item["review_status"] == "pending"
    assert item["open_findings"] >= 1


def test_finding_review_validates_and_records_note(flow):
    no_note = flow.client.patch(
        f"/review/findings/{flow.finding_id}",
        headers=flow.reviewer(),
        json={"status": "dismissed"},
    )
    assert no_note.status_code == 422, no_note.text

    stale = flow.client.patch(
        f"/review/findings/{flow.finding_id}",
        headers=flow.reviewer(),
        json={
            "status": "confirmed",
            "note": "Checked against the deed.",
            "expected_status": "dismissed",
        },
    )
    assert stale.status_code == 409, stale.text

    response = flow.client.patch(
        f"/review/findings/{flow.finding_id}",
        headers=flow.reviewer(),
        json={
            "status": "confirmed",
            "note": "Checked against the sale deed.",
            "expected_status": "open",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["review_note"] == "Checked against the sale deed."
    assert body["reviewed_by"] is not None
    assert body["reviewed_at"]

    event = fetch_one(
        flow.db_path,
        "SELECT action, detail FROM audit_events WHERE action = 'finding.reviewed' ORDER BY id DESC",
    )
    assert event is not None


def test_run_decision_and_history(flow):
    response = flow.client.post(
        f"/review/runs/{flow.run_id}/decision",
        headers=flow.reviewer(),
        json={
            "decision": "overridden",
            "verdict": "verified",
            "note": "Manual inspection completed; no title defect found.",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["review_status"] == "overridden"
    assert body["review_verdict"] == "verified"
    assert body["review_note"].startswith("Manual inspection")

    verdict = flow.client.get(f"/analysis/{flow.property_id}/verdict", headers=flow.owner())
    assert verdict.status_code == 200, verdict.text
    assert verdict.json()["review_status"] == "overridden"
    assert verdict.json()["review_verdict"] == "verified"

    property_body = flow.client.get(f"/properties/{flow.property_id}", headers=flow.owner()).json()
    assert property_body["status"] == "analyzed"

    queue = flow.client.get("/review/queue", headers=flow.reviewer()).json()
    item = next(row for row in queue if row["property_id"] == flow.property_id)
    assert item["review_status"] == "overridden"
    assert item["review_verdict"] == "verified"


def test_rerun_preserves_reviewed_history_and_scopes_reads(flow):
    rerun = flow.client.post(f"/analysis/run/{flow.property_id}", headers=flow.owner())
    assert rerun.status_code == 200, rerun.text

    runs = flow.client.get(f"/analysis/{flow.property_id}/runs", headers=flow.owner()).json()
    new_run_id = runs[0]["id"]
    assert new_run_id != flow.run_id
    assert [run["id"] for run in runs][:2] == [new_run_id, flow.run_id]
    assert runs[0]["review_status"] == "pending"
    assert runs[1]["review_status"] == "overridden"
    assert runs[1]["review_verdict"] == "verified"

    findings = flow.client.get(
        f"/analysis/{flow.property_id}/findings", headers=flow.owner()
    ).json()
    assert findings
    rows = sqlite3.connect(str(flow.db_path)).execute(
        "SELECT id FROM risk_flags WHERE analysis_run_id = ?", (new_run_id,)
    ).fetchall()
    assert {finding["id"] for finding in findings} == {row[0] for row in rows}

    old_count = fetch_one(
        flow.db_path,
        "SELECT COUNT(*) FROM risk_flags WHERE analysis_run_id = ?",
        (flow.run_id,),
    )
    assert old_count and old_count[0] >= 1

    stale = flow.client.post(
        f"/review/runs/{flow.run_id}/decision",
        headers=flow.reviewer(),
        json={"decision": "confirmed", "note": "Stale review attempt."},
    )
    assert stale.status_code == 409, stale.text

    stale_finding = flow.client.patch(
        f"/review/findings/{flow.finding_id}",
        headers=flow.reviewer(),
        json={"status": "dismissed", "note": "Stale finding review."},
    )
    assert stale_finding.status_code == 409, stale_finding.text
