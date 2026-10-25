"""Phase 4 API: public catalogue reads, admin versioning and DB-backed analysis."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

ADMIN_EMAIL = "rules-admin@propchainai.com"
BUYER_EMAIL = "rules-buyer@propchainai.com"
PASSWORD = "rules-pass-1234"
JURISDICTION = "Maharashtra"


def set_role(db_path: Path, email: str, role: str) -> None:
    connection = sqlite3.connect(str(db_path))
    try:
        connection.execute("UPDATE users SET role = ? WHERE email = ?", (role, email))
        connection.commit()
    finally:
        connection.close()


class RulesFlow:
    def __init__(self, client, db_path: Path):
        self.client = client
        self.db_path = Path(db_path)
        self.admin: dict[str, str] = {}
        self.buyer: dict[str, str] = {}
        self.base = f"/admin/rule-packs/{JURISDICTION}"
        self.property_id: int | None = None
        self.original_version: int | None = None


@pytest.fixture(scope="module")
def flow(app_env) -> RulesFlow:
    return RulesFlow(app_env["client"], app_env["db_path"])


def register_and_login(flow: RulesFlow, email: str, name: str) -> dict[str, str]:
    response = flow.client.post(
        "/auth/register",
        json={"email": email, "full_name": name, "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    login = flow.client.post("/auth/login", data={"username": email, "password": PASSWORD})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_setup_accounts(flow):
    flow.admin = register_and_login(flow, ADMIN_EMAIL, "Rules Admin")
    flow.buyer = register_and_login(flow, BUYER_EMAIL, "Rules Buyer")
    set_role(flow.db_path, ADMIN_EMAIL, "admin")


def test_public_catalogue_is_readable_without_auth(flow):
    packs = flow.client.get("/rule-packs")
    assert packs.status_code == 200, packs.text
    assert any(pack["jurisdiction"] == JURISDICTION for pack in packs.json())

    pack = flow.client.get(f"/rule-packs/{JURISDICTION}")
    assert pack.status_code == 200, pack.text
    body = pack.json()
    assert body["code"] == "mh-v1"
    assert body["active_rule_count"] == 14
    assert len(body["rules"]) == 14
    assert any(rule["rule_code"] == "MH-DOC-001" for rule in body["rules"])


def test_catalogue_writes_are_admin_only(flow):
    assert flow.client.get("/admin/rule-packs", headers=flow.buyer).status_code == 403
    response = flow.client.patch(
        f"{flow.base}/rules/MH-DOC-001",
        headers=flow.buyer,
        json={"title": "Buyer edit attempt"},
    )
    assert response.status_code == 403, response.text
    assert flow.client.get("/admin/rule-packs", headers=flow.admin).status_code == 200


def test_admin_reads_full_rule_detail(flow):
    response = flow.client.get(f"{flow.base}/rules/MH-DOC-001", headers=flow.admin)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rule_code"] == "MH-DOC-001"
    assert body["current_version"] >= 1
    assert body["versions"]
    assert body["versions"][0]["version"] == body["current_version"]
    flow.original_version = body["current_version"]


def test_update_creates_a_version_and_audit_event(flow):
    response = flow.client.patch(
        f"{flow.base}/rules/MH-DOC-001",
        headers=flow.admin,
        json={
            "title": "Custom no-documents rule",
            "severity": "critical",
            "expected_version": flow.original_version,
            "change_note": "Tighten the empty-file check for the test.",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "Custom no-documents rule"
    assert body["severity"] == "critical"
    assert body["current_version"] == flow.original_version + 1
    assert body["versions"][0]["version"] == body["current_version"]

    public_pack = flow.client.get(f"/rule-packs/{JURISDICTION}").json()
    rule = next(row for row in public_pack["rules"] if row["rule_code"] == "MH-DOC-001")
    assert rule["title"] == "Custom no-documents rule"
    assert rule["severity"] == "critical"

    audit = flow.client.get("/admin/audit-events?limit=100", headers=flow.admin).json()
    event = next(
        (
            row
            for row in audit
            if row["action"] == "rule.updated"
            and row["detail"]
            and row["detail"].get("rule_code") == "MH-DOC-001"
        ),
        None,
    )
    assert event is not None
    assert event["actor_user_id"] is not None


def test_stale_version_is_rejected(flow):
    response = flow.client.patch(
        f"{flow.base}/rules/MH-DOC-001",
        headers=flow.admin,
        json={"title": "Stale edit", "expected_version": flow.original_version},
    )
    assert response.status_code == 409, response.text


def test_rollback_restores_previous_content_as_a_new_version(flow):
    response = flow.client.post(
        f"{flow.base}/rules/MH-DOC-001/rollback",
        headers=flow.admin,
        json={"version": flow.original_version, "change_note": "Restore built-in title."},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] != "Custom no-documents rule"
    assert body["current_version"] > flow.original_version + 1
    assert body["versions"][0]["version"] == body["current_version"]

    audit = flow.client.get("/admin/audit-events?limit=100", headers=flow.admin).json()
    assert any(row["action"] == "rule.rolled_back" for row in audit)


def test_create_and_duplicate_rule(flow):
    payload = {
        "rule_code": "TEST-RULE-001",
        "title": "Custom test rule",
        "description": "Created by the Phase 4 API test.",
        "category": "missing-document",
        "severity": "low",
        "confidence": 0.5,
        "conditions": {"type": "no_documents", "short_circuit": False},
        "recommended_action": "Review the custom test condition.",
        "is_active": True,
        "change_note": "Create the test rule.",
    }
    created = flow.client.post(f"{flow.base}/rules", headers=flow.admin, json=payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["current_version"] == 1
    assert body["rule_code"] == "TEST-RULE-001"

    duplicate = flow.client.post(f"{flow.base}/rules", headers=flow.admin, json=payload)
    assert duplicate.status_code == 409, duplicate.text

    audit = flow.client.get("/admin/audit-events?limit=100", headers=flow.admin).json()
    assert any(row["action"] == "rule.created" for row in audit)


def test_db_catalogue_drives_analysis_and_findings_are_traceable(flow, monkeypatch):
    from app.services.rules_mh import MaharashtraRuleEngine

    prop = flow.client.post(
        "/properties",
        headers=flow.buyer,
        json={"title": "Rules-backed analysis", "state": "Maharashtra", "survey_number": "404"},
    )
    assert prop.status_code == 200, prop.text
    flow.property_id = prop.json()["id"]

    updated = flow.client.patch(
        f"{flow.base}/rules/MH-DOC-001",
        headers=flow.admin,
        json={
            "title": "Catalogue-backed empty check",
            "severity": "critical",
            "change_note": "Prove the DB catalogue is evaluated.",
        },
    )
    assert updated.status_code == 200, updated.text
    updated_version = updated.json()["current_version"]

    # The pytest environment pins RULE_ENGINE=fake. Selecting the real
    # Maharashtra engine activates the database catalogue path inside the
    # analysis engine without changing the rest of the fake pipeline.
    monkeypatch.setattr(
        "app.services.analysis_engine.get_rule_engine",
        lambda: MaharashtraRuleEngine(),
    )

    analysis = flow.client.post(
        f"/analysis/run/{flow.property_id}", headers=flow.buyer
    )
    assert analysis.status_code == 200, analysis.text
    result = analysis.json()
    verdict = flow.client.get(
        f"/analysis/{flow.property_id}/verdict", headers=flow.buyer
    )
    assert verdict.status_code == 200, verdict.text
    assert "mh-db-v1@" in verdict.json()["engine_version"]
    finding = next(
        (row for row in result["findings"] if row["rule_ref"] == "MH-DOC-001"), None
    )
    assert finding is not None, result["findings"]
    assert finding["title"] == "Catalogue-backed empty check"
    assert finding["severity"] == "critical"
    assert finding["rule_id"] is not None
    assert finding["rule_version"] == updated_version


def test_reset_restores_builtin_pack_and_deactivates_custom_rows(flow):
    response = flow.client.post(
        f"{base(flow)}/reset",
        headers=flow.admin,
        json={"change_note": "Reset after the Phase 4 API test."},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    active = [rule for rule in body["rules"] if rule["is_active"]]
    assert len(active) == 14
    assert not any(rule["rule_code"] == "TEST-RULE-001" for rule in active)

    public_pack = flow.client.get(f"/rule-packs/{JURISDICTION}").json()
    assert public_pack["active_rule_count"] == 14
    assert all(rule["rule_code"] != "TEST-RULE-001" for rule in public_pack["rules"])

    audit = flow.client.get("/admin/audit-events?limit=100", headers=flow.admin).json()
    assert any(row["action"] == "rule.pack_reset" for row in audit)


def base(flow: RulesFlow) -> str:
    return f"/admin/rule-packs/{JURISDICTION}"
