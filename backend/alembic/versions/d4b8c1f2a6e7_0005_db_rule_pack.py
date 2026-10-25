"""0005: versioned, database-backed rule catalogue (Phase 4).

Adds the columns the editable catalogue needs:

* ``legal_rules.confidence`` - risk-engine confidence carried by a rule;
* ``legal_rules.current_version`` - latest snapshot number;
* ``risk_flags.rule_version`` - the catalogue version a finding was evaluated
  against, so later edits do not rewrite history.

It then loads the full built-in ``mh-v1`` pack from
``app/data/mh_rule_pack_v1.json``. Existing rows (the six Phase-1 seeds) are
updated in place and receive a new snapshot; missing rules are inserted with
version 1. The two cross-validator metadata rows keep ``conditions = NULL``:
they are catalogue entries, not evaluable rule-pack rules.

Revision ID: d4b8c1f2a6e7
Revises: c81f2a4d9e05
Create Date: 2026-10-25
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4b8c1f2a6e7"
down_revision: Union[str, None] = "c81f2a4d9e05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PACK_PATH = Path(__file__).resolve().parents[2] / "app" / "data" / "mh_rule_pack_v1.json"


def _json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _date(value: Any) -> date | None:
    if not value:
        return None
    return date.fromisoformat(str(value)[:10])


def _snapshot(rule: dict[str, Any], jurisdiction: str, version: int) -> dict[str, Any]:
    return {
        "rule_code": rule["rule_code"],
        "jurisdiction": jurisdiction,
        "law_name": rule.get("law_name"),
        "section": rule.get("section"),
        "title": rule["title"],
        "description": rule.get("description"),
        "category": rule["category"],
        "severity": rule["severity"],
        "confidence": rule.get("confidence", 0.8),
        "conditions": rule.get("conditions"),
        "evidence_required": rule.get("evidence_required"),
        "recommended_action": rule.get("recommended_action"),
        "source_url": rule.get("source_url"),
        "effective_from": rule.get("effective_from"),
        "effective_to": rule.get("effective_to"),
        "is_active": bool(rule.get("is_active", True)),
        "version": version,
    }


def upgrade() -> None:
    with op.batch_alter_table("legal_rules") as batch_op:
        batch_op.add_column(
            sa.Column("confidence", sa.Float(), nullable=False, server_default="0.8")
        )
        batch_op.add_column(
            sa.Column("current_version", sa.Integer(), nullable=False, server_default="1")
        )
    with op.batch_alter_table("risk_flags") as batch_op:
        batch_op.add_column(sa.Column("rule_version", sa.Integer(), nullable=True))

    data = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    jurisdiction = str(data["jurisdiction"])
    now = datetime.now(timezone.utc)
    bind = op.get_bind()

    existing = {
        row["rule_code"]: row
        for row in bind.execute(
            sa.text("SELECT id, rule_code, current_version FROM legal_rules")
        ).mappings()
    }

    for rule in data["rules"]:
        code = str(rule["rule_code"])
        current = existing.get(code)
        if current:
            latest = bind.execute(
                sa.text(
                    "SELECT COALESCE(MAX(version), 0) AS latest "
                    "FROM legal_rule_versions WHERE rule_id = :rule_id"
                ),
                {"rule_id": current["id"]},
            ).scalar_one()
            new_version = max(int(current["current_version"] or 1), int(latest or 0)) + 1
            params = {
                "id": current["id"],
                "law_name": rule.get("law_name"),
                "section": rule.get("section"),
                "title": rule["title"],
                "description": rule.get("description"),
                "category": rule["category"],
                "severity": rule["severity"],
                "confidence": rule.get("confidence", 0.8),
                "conditions": _json(rule.get("conditions")),
                "evidence_required": _json(rule.get("evidence_required")),
                "recommended_action": rule.get("recommended_action"),
                "source_url": rule.get("source_url"),
                "effective_from": _date(rule.get("effective_from")),
                "effective_to": _date(rule.get("effective_to")),
                "is_active": bool(rule.get("is_active", True)),
                "current_version": new_version,
            }
            bind.execute(
                sa.text(
                    "UPDATE legal_rules SET "
                    "law_name = :law_name, section = :section, title = :title, "
                    "description = :description, category = :category, severity = :severity, "
                    "confidence = :confidence, conditions = :conditions, "
                    "evidence_required = :evidence_required, "
                    "recommended_action = :recommended_action, source_url = :source_url, "
                    "effective_from = :effective_from, effective_to = :effective_to, "
                    "is_active = :is_active, current_version = :current_version "
                    "WHERE id = :id"
                ),
                params,
            )
            rule_id = current["id"]
        else:
            new_version = 1
            bind.execute(
                sa.text(
                    "INSERT INTO legal_rules ("
                    "rule_code, jurisdiction, law_name, section, title, description, "
                    "category, severity, confidence, conditions, evidence_required, "
                    "recommended_action, source_url, effective_from, effective_to, "
                    "is_active, current_version, created_at"
                    ") VALUES ("
                    ":rule_code, :jurisdiction, :law_name, :section, :title, :description, "
                    ":category, :severity, :confidence, :conditions, :evidence_required, "
                    ":recommended_action, :source_url, :effective_from, :effective_to, "
                    ":is_active, :current_version, :created_at"
                    ")"
                ),
                {
                    "rule_code": code,
                    "jurisdiction": jurisdiction,
                    "law_name": rule.get("law_name"),
                    "section": rule.get("section"),
                    "title": rule["title"],
                    "description": rule.get("description"),
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "confidence": rule.get("confidence", 0.8),
                    "conditions": _json(rule.get("conditions")),
                    "evidence_required": _json(rule.get("evidence_required")),
                    "recommended_action": rule.get("recommended_action"),
                    "source_url": rule.get("source_url"),
                    "effective_from": _date(rule.get("effective_from")),
                    "effective_to": _date(rule.get("effective_to")),
                    "is_active": bool(rule.get("is_active", True)),
                    "current_version": new_version,
                    "created_at": now,
                },
            )
            rule_id = bind.execute(
                sa.text("SELECT id FROM legal_rules WHERE rule_code = :rule_code"),
                {"rule_code": code},
            ).scalar_one()

        bind.execute(
            sa.text(
                "INSERT INTO legal_rule_versions "
                "(rule_id, version, snapshot, change_note, created_by, created_at) "
                "VALUES (:rule_id, :version, :snapshot, :change_note, NULL, :now)"
            ),
            {
                "rule_id": rule_id,
                "version": new_version,
                "snapshot": _json(_snapshot(rule, jurisdiction, new_version)),
                "change_note": "Phase 4: loaded the editable mh-v1 rule pack",
                "now": now,
            },
        )


def downgrade() -> None:
    # Catalogue rows are intentionally left in place; the pre-Phase-4 app
    # ignores the extra data and the rules remain useful documentation.
    with op.batch_alter_table("risk_flags") as batch_op:
        batch_op.drop_column("rule_version")
    with op.batch_alter_table("legal_rules") as batch_op:
        batch_op.drop_column("current_version")
        batch_op.drop_column("confidence")
