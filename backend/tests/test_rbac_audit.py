"""RBAC + audit-trail tests (Phase 1, tasks B5 and B6).

Ordered end-to-end journey through the module-scoped temp DB from ``conftest.py``:

register(admin/reviewer) -> 422 ; register(owner)+login ; property ; upload ;
analysis ; blockchain register ; report ; failed login ; audit endpoints.

The two audit assertions live *after* a direct role flip in the temp DB, because
nothing in the public API can promote a user to ``admin`` any more (that is the
whole point of the ``/auth/register`` fix).
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pymupdf  # type: ignore[import-untyped]
import pytest

OWNER_EMAIL = "rbac-owner@propchainai.com"  # .test/.example TLDs are rejected by email-validator
BUYER_EMAIL = "rbac-buyer@propchainai.com"
PASSWORD = "rbac-pass-1234"

EXPECTED_ACTIONS = {
    "user.registered",
    "user.login",
    "user.login_failed",
    "property.created",
    "document.uploaded",
    "analysis.run_completed",
    "blockchain.registered",
    "report.generated",
}


def make_pdf(path: Path) -> Path:
    """Create a small real PDF at runtime (text layer, no OCR needed)."""
    doc = pymupdf.open()
    try:
        page = doc.new_page()
        page.insert_text((72, 72), "Sale Deed - RBAC/audit fixture")
        doc.save(str(path))
    finally:
        doc.close()
    return path


def set_role(db_path: Path, email: str, role: str) -> None:
    """Flip a user's role straight in the temp DB (no API can do this any more)."""
    connection = sqlite3.connect(str(db_path))
    try:
        connection.execute("UPDATE users SET role = ? WHERE email = ?", (role, email))
        connection.commit()
        stored = connection.execute("SELECT role FROM users WHERE email = ?", (email,)).fetchone()
        assert stored == (role,), stored
    finally:
        connection.close()


def fetch_one(db_path: Path, sql: str, params: tuple = ()) -> tuple | None:
    connection = sqlite3.connect(str(db_path))
    try:
        return connection.execute(sql, params).fetchone()
    finally:
        connection.close()


class AuditFlow:
    """Mutable state shared by the ordered tests of this module."""

    def __init__(self, client, db_path: Path):
        self.client = client
        self.db_path = Path(db_path)
        self.owner_headers: dict[str, str] = {}
        self.buyer_headers: dict[str, str] = {}
        self.owner_id: int | None = None
        self.property_id: int | None = None
        self.document_id: int | None = None
        self.risk_score: float | None = None
        self.events: list[dict] = []

    def auth_headers(self) -> dict[str, str]:
        assert self.owner_headers, "login must run before this step"
        return self.owner_headers

    def action(self, name: str) -> dict | None:
        return next((event for event in self.events if event["action"] == name), None)

    def event_for(self, name: str, **match) -> dict:
        """The newest event named ``name`` whose fields match ``match``."""
        for event in self.events:
            if event["action"] == name and all(event.get(key) == value for key, value in match.items()):
                return event
        raise AssertionError(f"no {name!r} event matching {match} in {len(self.events)} events")


@pytest.fixture(scope="module")
def flow(app_env) -> AuditFlow:
    return AuditFlow(app_env["client"], app_env["db_path"])


@pytest.fixture(scope="module")
def admin_mounted(app_env) -> bool:
    """Skip the /admin tests until ``app.main`` mounts the admin router.

    Mounting it is the main agent's step (``app.include_router(admin.router)``); this
    fixture keeps the suite honest instead of reporting a 404 as a security failure.
    ``PROPCHAIN_TEST_MOUNT_ADMIN=1`` mounts it locally for a verification run only
    (used while app/main.py was still out of this task's scope) and runs the real
    assertions instead of skipping them.
    """
    app = app_env["app"]
    if "/admin/audit-events" in {getattr(route, "path", "") for route in app.routes}:
        return True

    if os.environ.get("PROPCHAIN_TEST_MOUNT_ADMIN") == "1":
        from app.routers import admin as admin_router

        app.include_router(admin_router.router)
        return True

    pytest.skip("app.main does not mount the admin router yet (pending include_router(admin.router))")


def test_register_rejects_privileged_roles(app_client):
    for role in ("admin", "reviewer"):
        r = app_client.post(
            "/auth/register",
            json={"email": f"self-{role}@propchainai.com", "full_name": "Self", "password": PASSWORD, "role": role},
        )
        assert r.status_code == 422, f"self-registration as {role} was accepted: {r.text}"
        assert role in r.json()["detail"]


def test_register_owner(flow):
    r = flow.client.post(
        "/auth/register",
        json={"email": OWNER_EMAIL, "full_name": "Owner User", "password": PASSWORD, "role": "owner"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "owner"
    flow.owner_id = r.json()["id"]


def test_register_buyer_for_rbac_checks(flow):
    r = flow.client.post(
        "/auth/register",
        json={"email": BUYER_EMAIL, "full_name": "Buyer User", "password": PASSWORD},
    )
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "buyer"  # default role, unchanged


def test_login(flow):
    for email, attribute in ((OWNER_EMAIL, "owner_headers"), (BUYER_EMAIL, "buyer_headers")):
        r = flow.client.post("/auth/login", data={"username": email, "password": PASSWORD})
        assert r.status_code == 200, r.text
        setattr(flow, attribute, {"Authorization": f"Bearer {r.json()['access_token']}"})


def test_create_property(flow):
    r = flow.client.post(
        "/properties",
        headers=flow.auth_headers(),
        json={"title": "RBAC Test Plot", "state": "Maharashtra", "district": "Pune", "survey_number": "124/A"},
    )
    assert r.status_code == 200, r.text
    flow.property_id = r.json()["id"]


def test_upload_sets_uploaded_by(flow, tmp_path):
    pdf = make_pdf(tmp_path / "sale_deed_rbac.pdf")
    with pdf.open("rb") as handle:
        r = flow.client.post(
            f"/documents/upload/{flow.property_id}",
            headers=flow.auth_headers(),
            files={"file": ("sale_deed_rbac.pdf", handle, "application/pdf")},
        )
    assert r.status_code == 200, r.text
    flow.document_id = r.json()["id"]

    row = fetch_one(flow.db_path, "SELECT uploaded_by FROM documents WHERE id = ?", (flow.document_id,))
    assert row is not None and row[0] == flow.owner_id, f"uploaded_by not attributed: {row}"


def test_run_analysis(flow):
    r = flow.client.post(f"/analysis/run/{flow.property_id}", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    flow.risk_score = r.json()["risk_score"]


def test_blockchain_register(flow):
    r = flow.client.post(f"/blockchain/register/{flow.document_id}", headers=flow.auth_headers())
    assert r.status_code == 200, r.text


def test_download_report(flow):
    r = flow.client.get(f"/reports/{flow.property_id}/pdf", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    assert r.content[:4] == b"%PDF"


def test_failed_login_is_401_and_indistinguishable(app_client):
    wrong_password = app_client.post("/auth/login", data={"username": OWNER_EMAIL, "password": "wrong-password"})
    unknown_user = app_client.post("/auth/login", data={"username": "nobody@propchainai.com", "password": "wrong-password"})
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()  # no user enumeration


def test_audit_events_reject_non_admins(flow, admin_mounted):
    assert flow.client.get("/admin/audit-events").status_code == 401
    r = flow.client.get("/admin/audit-events", headers=flow.buyer_headers)
    assert r.status_code == 403, r.text
    assert r.json()["detail"] == "Insufficient permissions"


def test_audit_events_for_admin(flow, admin_mounted):
    set_role(flow.db_path, OWNER_EMAIL, "admin")

    # the owner token is unchanged on purpose: the role must come from the DB
    r = flow.client.get("/admin/audit-events", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    flow.events = r.json()
    assert isinstance(flow.events, list) and flow.events

    assert [event["id"] for event in flow.events] == sorted((event["id"] for event in flow.events), reverse=True)
    actions = {event["action"] for event in flow.events}
    assert EXPECTED_ACTIONS <= actions, f"missing: {sorted(EXPECTED_ACTIONS - actions)}"

    keys = {"id", "action", "entity_type", "entity_id", "actor_user_id", "detail", "ip_address", "created_at"}
    assert keys <= set(flow.events[0]), sorted(flow.events[0])
    assert "T" in flow.events[0]["created_at"]  # ISO string


def test_audit_events_carry_actor_entity_and_detail(flow, admin_mounted):
    # three accounts registered in this module, so match the owner's own event
    registration = flow.event_for("user.registered", entity_id=flow.owner_id)
    assert registration["actor_user_id"] == flow.owner_id

    uploaded = flow.action("document.uploaded")
    assert (uploaded["entity_type"], uploaded["entity_id"]) == ("document", flow.document_id)
    assert uploaded["actor_user_id"] == flow.owner_id

    analysis = flow.action("analysis.run_completed")
    assert (analysis["entity_type"], analysis["entity_id"]) == ("property", flow.property_id)
    assert analysis["detail"] == {"risk_score": flow.risk_score}

    blockchain = flow.action("blockchain.registered")
    assert (blockchain["entity_type"], blockchain["entity_id"]) == ("document", flow.document_id)

    report = flow.action("report.generated")
    assert (report["entity_type"], report["entity_id"]) == ("property", flow.property_id)

    # the module also fails a login for an unknown address, so match the owner's
    failed_login = flow.event_for("user.login_failed", detail={"email": OWNER_EMAIL})
    assert failed_login["actor_user_id"] is None

    assert all(event["ip_address"] for event in flow.events)


def test_audit_events_paging(flow, admin_mounted):
    r = flow.client.get("/admin/audit-events?limit=2&offset=1", headers=flow.auth_headers())
    assert r.status_code == 200, r.text
    assert [event["id"] for event in r.json()] == [event["id"] for event in flow.events[1:3]]
