"""Database-backed rule catalogue (Phase 4).

The ``legal_rules`` table is the editable catalogue; every change is written
as a new ``legal_rule_versions`` snapshot. The analysis pipeline loads the
active rules in the property's jurisdiction, converts them into the frozen
``RuleDefinition`` shape and evaluates them with the same pure evaluator as the
built-in pack.

Two deliberate safety properties:

* A rule with no ``conditions`` is metadata-only (the cross-validator owns those
  findings); it is never evaluated by this engine.
* If an administrator deactivates every evaluable rule, the engine does not
  silently return "no findings". It raises a high-severity coverage finding so
  the verdict cannot become Verified on an empty catalogue.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import LegalRule, LegalRuleVersion
from app.services.interfaces import FlagDraft
from app.services.rule_pack import (
    BUILTIN_MH_RULES,
    BUILTIN_PACK_CODE,
    BUILTIN_PACK_JURISDICTION,
    BUILTIN_PACK_NAME,
    RuleDefinition,
    evaluate_pack,
    pack_name,
    pack_signature,
    validate_condition,
)

logger = logging.getLogger(__name__)

#: Display/evaluation order for the shipped rules; custom rules follow by id.
_BUILTIN_ORDER = {definition.rule_code: definition.sort_order for definition in BUILTIN_MH_RULES}

EDITABLE_FIELDS = frozenset(
    {
        "law_name",
        "section",
        "title",
        "description",
        "category",
        "severity",
        "confidence",
        "conditions",
        "evidence_required",
        "recommended_action",
        "source_url",
        "effective_from",
        "effective_to",
        "is_active",
    }
)


class RuleNotFound(LookupError):
    """No rule with that code in the requested jurisdiction."""


class RuleConflict(ValueError):
    """A rule code already exists or the optimistic version is stale."""


@dataclass
class LoadedRulePack:
    """The evaluable slice of a jurisdiction catalogue, plus coverage counts."""

    jurisdiction: str
    rules: list[RuleDefinition]
    signature: str
    total_count: int
    active_count: int
    evaluable_count: int
    code: str
    name: str


class DatabaseRuleEngine:
    """Evaluate the active DB catalogue; compatible with the RuleEngine protocol."""

    def __init__(self, pack: LoadedRulePack):
        self.pack = pack
        suffix = pack.signature[:8] if pack.signature else "empty"
        self.engine_version = f"mh-db-v1@{suffix}"

    def evaluate(self, property_profile: dict, extracted: list[dict]) -> list[FlagDraft]:
        if not self.pack.rules:
            return [_empty_pack_finding(self.pack.jurisdiction)]
        return evaluate_pack(self.pack.rules, property_profile, extracted)


def _empty_pack_finding(jurisdiction: str) -> FlagDraft:
    return FlagDraft(
        category="missing-document",
        title="No active screening rules for this jurisdiction",
        description=(
            f"The {jurisdiction or 'configured'} rule pack has no active, evaluable "
            "rules. The automated checks could not run, so this result is not a "
            "clean verdict."
        ),
        severity="high",
        confidence=1.0,
        evidence=(
            "Catalogue coverage: 0 active evaluable rules. An administrator must "
            "activate or create at least one rule."
        ),
        rule_ref="PACK-EMPTY-001",
        recommended_action=(
            "Open the rule pack in the admin catalogue, activate an evaluable rule "
            "or reset the pack, then re-run the analysis."
        ),
    )


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _in_effect(rule: LegalRule, on_date: date) -> bool:
    if rule.effective_from and rule.effective_from > on_date:
        return False
    if rule.effective_to and rule.effective_to < on_date:
        return False
    return True


def _jurisdiction_code(jurisdiction: str) -> str:
    if jurisdiction == BUILTIN_PACK_JURISDICTION:
        return BUILTIN_PACK_CODE
    slug = re.sub(r"[^a-z0-9]+", "-", jurisdiction.lower()).strip("-") or "rules"
    return f"{slug}-v1"


def _order_key(rule: LegalRule) -> tuple[int, int]:
    return (_BUILTIN_ORDER.get(rule.rule_code, len(_BUILTIN_ORDER)), int(rule.id or 0))


def ordered_rules(rules: list[LegalRule]) -> list[LegalRule]:
    return sorted(rules, key=_order_key)


def rule_to_definition(rule: LegalRule, sort_order: int = 0) -> RuleDefinition:
    """Convert one ORM row to the pure evaluator shape."""
    category = rule.category.value if hasattr(rule.category, "value") else str(rule.category)
    severity = rule.severity.value if hasattr(rule.severity, "value") else str(rule.severity)
    return RuleDefinition(
        rule_code=rule.rule_code,
        title=rule.title,
        description=rule.description,
        category=category,
        severity=severity,
        confidence=float(rule.confidence if rule.confidence is not None else 0.8),
        conditions=rule.conditions,
        evidence_required=rule.evidence_required,
        recommended_action=rule.recommended_action,
        law_name=rule.law_name,
        section=rule.section,
        source_url=rule.source_url,
        jurisdiction=rule.jurisdiction,
        effective_from=rule.effective_from,
        effective_to=rule.effective_to,
        is_active=bool(rule.is_active),
        rule_id=rule.id,
        version=int(rule.current_version or 1),
        sort_order=sort_order,
    )


def _definition_from_seed(definition: RuleDefinition) -> dict[str, Any]:
    return {
        "law_name": definition.law_name,
        "section": definition.section,
        "title": definition.title,
        "description": definition.description,
        "category": definition.category,
        "severity": definition.severity,
        "confidence": definition.confidence,
        "conditions": definition.conditions,
        "evidence_required": definition.evidence_required,
        "recommended_action": definition.recommended_action,
        "source_url": definition.source_url,
        "effective_from": definition.effective_from,
        "effective_to": definition.effective_to,
        "is_active": definition.is_active,
    }


def load_rule_pack(db: Session, jurisdiction: str, on_date: date | None = None) -> LoadedRulePack:
    """Load and snapshot the active catalogue for one jurisdiction."""
    on_date = on_date or _today()
    rows = ordered_rules(
        db.query(LegalRule).filter(LegalRule.jurisdiction == jurisdiction).all()
    )
    active = [rule for rule in rows if rule.is_active and _in_effect(rule, on_date)]
    evaluable = [rule for rule in active if rule.conditions]
    definitions = [rule_to_definition(rule, index) for index, rule in enumerate(evaluable)]
    return LoadedRulePack(
        jurisdiction=jurisdiction,
        rules=definitions,
        signature=pack_signature(definitions) if definitions else "",
        total_count=len(rows),
        active_count=len(active),
        evaluable_count=len(definitions),
        code=_jurisdiction_code(jurisdiction),
        name=pack_name(jurisdiction),
    )


def list_rules(db: Session, jurisdiction: str, include_inactive: bool = True) -> list[LegalRule]:
    query = db.query(LegalRule).filter(LegalRule.jurisdiction == jurisdiction)
    if not include_inactive:
        query = query.filter(LegalRule.is_active.is_(True))
    return ordered_rules(query.all())


def get_rule(db: Session, jurisdiction: str, rule_code: str) -> LegalRule:
    rule = (
        db.query(LegalRule)
        .filter(LegalRule.jurisdiction == jurisdiction, LegalRule.rule_code == rule_code)
        .first()
    )
    if not rule:
        raise RuleNotFound(f"rule {rule_code!r} not found in {jurisdiction!r}")
    return rule


def list_versions(db: Session, rule: LegalRule) -> list[LegalRuleVersion]:
    return (
        db.query(LegalRuleVersion)
        .filter(LegalRuleVersion.rule_id == rule.id)
        .order_by(LegalRuleVersion.version.desc())
        .all()
    )


def snapshot(rule: LegalRule) -> dict[str, Any]:
    """Canonical snapshot used by the version history."""
    definition = rule_to_definition(rule)
    return definition.snapshot()


def serialize_version(version: LegalRuleVersion) -> dict[str, Any]:
    return {
        "version": version.version,
        "snapshot": version.snapshot,
        "change_note": version.change_note,
        "created_by": version.created_by,
        "created_at": version.created_at,
    }


def serialize_rule(rule: LegalRule) -> dict[str, Any]:
    category = rule.category.value if hasattr(rule.category, "value") else rule.category
    severity = rule.severity.value if hasattr(rule.severity, "value") else rule.severity
    return {
        "id": rule.id,
        "rule_code": rule.rule_code,
        "jurisdiction": rule.jurisdiction,
        "law_name": rule.law_name,
        "section": rule.section,
        "title": rule.title,
        "description": rule.description,
        "category": category,
        "severity": severity,
        "confidence": rule.confidence,
        "conditions": rule.conditions,
        "evidence_required": rule.evidence_required,
        "recommended_action": rule.recommended_action,
        "source_url": rule.source_url,
        "effective_from": rule.effective_from,
        "effective_to": rule.effective_to,
        "is_active": bool(rule.is_active),
        "current_version": int(rule.current_version or 1),
        "is_evaluable": bool(rule.conditions),
        "created_at": rule.created_at,
    }


def pack_summary(db: Session, jurisdiction: str, include_inactive: bool = True) -> dict[str, Any]:
    rows = list_rules(db, jurisdiction, include_inactive=include_inactive)
    on_date = _today()
    active = [rule for rule in rows if rule.is_active and _in_effect(rule, on_date)]
    evaluable = [rule for rule in active if rule.conditions]
    definitions = [rule_to_definition(rule, index) for index, rule in enumerate(evaluable)]
    latest_version = (
        db.query(func.max(LegalRuleVersion.created_at))
        .join(LegalRule, LegalRule.id == LegalRuleVersion.rule_id)
        .filter(LegalRule.jurisdiction == jurisdiction)
        .scalar()
    )
    updated_at = latest_version or max((rule.created_at for rule in rows), default=None)
    return {
        "jurisdiction": jurisdiction,
        "code": _jurisdiction_code(jurisdiction),
        "name": pack_name(jurisdiction),
        "version": max((int(rule.current_version or 1) for rule in rows), default=0),
        "rule_count": len(rows),
        "active_rule_count": len(active),
        "evaluable_rule_count": len(evaluable),
        "signature": pack_signature(definitions) if definitions else "",
        "updated_at": updated_at,
    }


def list_pack_summaries(db: Session, include_inactive: bool = True) -> list[dict[str, Any]]:
    jurisdictions = [
        row[0]
        for row in db.query(LegalRule.jurisdiction).distinct().order_by(LegalRule.jurisdiction)
    ]
    if BUILTIN_PACK_JURISDICTION not in jurisdictions:
        jurisdictions.append(BUILTIN_PACK_JURISDICTION)
    return [
        pack_summary(db, jurisdiction, include_inactive=include_inactive)
        for jurisdiction in jurisdictions
    ]


def pack_detail(db: Session, jurisdiction: str, include_inactive: bool = True) -> dict[str, Any]:
    summary = pack_summary(db, jurisdiction, include_inactive=include_inactive)
    summary["rules"] = [
        serialize_rule(rule)
        for rule in list_rules(db, jurisdiction, include_inactive=include_inactive)
    ]
    return summary


def _validate_rule_values(values: dict[str, Any]) -> None:
    for field_name in ("title", "severity", "confidence", "is_active"):
        if field_name in values and values[field_name] is None:
            raise ValueError(f"{field_name} cannot be null")
    if "conditions" in values:
        validate_condition(values["conditions"])
    if "confidence" in values and values["confidence"] is not None:
        confidence = float(values["confidence"])
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
    start = values.get("effective_from")
    end = values.get("effective_to")
    if start and end and start > end:
        raise ValueError("effective_from must not be after effective_to")


def _add_version(
    db: Session,
    rule: LegalRule,
    actor_user_id: int | None,
    change_note: str | None,
) -> LegalRuleVersion:
    version = LegalRuleVersion(
        rule_id=rule.id,
        version=int(rule.current_version or 1),
        snapshot=snapshot(rule),
        change_note=change_note,
        created_by=actor_user_id,
    )
    db.add(version)
    return version


def create_rule(
    db: Session,
    jurisdiction: str,
    values: dict[str, Any],
    actor_user_id: int | None = None,
    change_note: str | None = None,
) -> LegalRule:
    """Create a rule and its version 1 snapshot. Caller commits."""
    rule_code = str(values.pop("rule_code"))
    if db.query(LegalRule).filter(LegalRule.rule_code == rule_code).first():
        raise RuleConflict(f"rule code {rule_code!r} already exists")
    values = {key: value for key, value in values.items() if key in EDITABLE_FIELDS}
    _validate_rule_values(values)
    rule = LegalRule(
        rule_code=rule_code,
        jurisdiction=jurisdiction,
        current_version=1,
        confidence=values.pop("confidence", 0.8),
        is_active=values.pop("is_active", True),
        **values,
    )
    db.add(rule)
    db.flush()
    _add_version(db, rule, actor_user_id, change_note or "Rule created")
    db.flush()
    return rule


def update_rule(
    db: Session,
    rule: LegalRule,
    values: dict[str, Any],
    actor_user_id: int | None = None,
    change_note: str | None = None,
    expected_version: int | None = None,
) -> LegalRule:
    """Apply an edit, bump the version and record a snapshot. Caller commits."""
    if expected_version is not None and int(expected_version) != int(rule.current_version or 1):
        raise RuleConflict(
            f"version conflict: expected {expected_version}, current {rule.current_version}"
        )
    changes = {key: value for key, value in values.items() if key in EDITABLE_FIELDS}
    if not changes:
        return rule
    _validate_rule_values(changes)
    for key, value in changes.items():
        setattr(rule, key, value)
    # A partial PATCH can still create an invalid pair (e.g. move only the end
    # date before an existing start date), so validate the merged row too.
    _validate_rule_values(
        {
            "title": rule.title,
            "severity": rule.severity,
            "confidence": rule.confidence,
            "is_active": rule.is_active,
            "conditions": rule.conditions,
            "effective_from": rule.effective_from,
            "effective_to": rule.effective_to,
        }
    )
    rule.current_version = int(rule.current_version or 1) + 1
    _add_version(db, rule, actor_user_id, change_note or "Rule updated")
    db.flush()
    return rule


def rollback_rule(
    db: Session,
    rule: LegalRule,
    target_version: int,
    actor_user_id: int | None = None,
    change_note: str | None = None,
) -> LegalRule:
    """Restore an old snapshot as a *new* version (history stays append-only)."""
    version = (
        db.query(LegalRuleVersion)
        .filter(
            LegalRuleVersion.rule_id == rule.id,
            LegalRuleVersion.version == target_version,
        )
        .first()
    )
    if not version or not isinstance(version.snapshot, dict):
        raise RuleNotFound(f"version {target_version} not found for {rule.rule_code}")
    values = {
        key: value
        for key, value in version.snapshot.items()
        if key in EDITABLE_FIELDS
    }
    _validate_rule_values(values)
    for key, value in values.items():
        setattr(rule, key, value)
    rule.current_version = int(rule.current_version or 1) + 1
    _add_version(
        db,
        rule,
        actor_user_id,
        change_note or f"Rolled back to version {target_version}",
    )
    db.flush()
    return rule


def reset_pack(
    db: Session,
    jurisdiction: str,
    actor_user_id: int | None = None,
    change_note: str | None = None,
) -> list[LegalRule]:
    """Restore the built-in ``mh-v1`` rules for the built-in jurisdiction."""
    if jurisdiction != BUILTIN_PACK_JURISDICTION:
        raise ValueError(f"no built-in pack for {jurisdiction!r}")
    seeded_codes = {definition.rule_code for definition in BUILTIN_MH_RULES}
    rules: list[LegalRule] = []
    for definition in BUILTIN_MH_RULES:
        existing = (
            db.query(LegalRule).filter(LegalRule.rule_code == definition.rule_code).first()
        )
        values = _definition_from_seed(definition)
        if existing is None:
            rules.append(
                create_rule(
                    db,
                    BUILTIN_PACK_JURISDICTION,
                    {"rule_code": definition.rule_code, **values},
                    actor_user_id=actor_user_id,
                    change_note=change_note or "Restored built-in mh-v1 pack",
                )
            )
        else:
            update_rule(
                db,
                existing,
                values,
                actor_user_id=actor_user_id,
                change_note=change_note or "Restored built-in mh-v1 pack",
            )
            rules.append(existing)
    # Custom rules are retained for history but switched off by a reset.
    for existing in list_rules(db, jurisdiction, include_inactive=True):
        if existing.rule_code not in seeded_codes and existing.is_active:
            update_rule(
                db,
                existing,
                {"is_active": False},
                actor_user_id=actor_user_id,
                change_note=change_note or "Deactivated by mh-v1 reset",
            )
            rules.append(existing)
    db.flush()
    return rules


def catalogue_hash(rules: list[LegalRule]) -> str:
    """Convenience hash for callers that only have ORM rows."""
    definitions = [rule_to_definition(rule, index) for index, rule in enumerate(rules)]
    return hashlib.sha256(
        json.dumps(
            [definition.snapshot() for definition in definitions],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
