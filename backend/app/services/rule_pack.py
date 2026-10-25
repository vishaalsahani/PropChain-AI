"""Declarative rule-pack evaluation (Phase 4).

A rule is a small, versioned record in the ``legal_rules`` table. The
``conditions`` JSON column selects one of the evaluators below; the editable
metadata (title, description, severity, confidence, action, source, effective
dates and active flag) stays in the database. This keeps the catalogue editable
without turning the application into a general-purpose expression interpreter.

The same evaluator runs the built-in ``mh-v1`` pack (used by the code-level
fallback engine) and the database-backed pack used by the analysis pipeline, so
the two can be compared directly in tests.

Condition vocabulary
--------------------

``no_documents`` (``short_circuit`` optional)
    No completed document extraction.
``missing_doc_type`` (``doc_type``)
    A required document type is absent.
``profile_identifier_missing`` (``state``, ``fields``)
    The profile has none of the listed identifiers.
``identifier_mismatch`` (``fields``)
    A profile identifier differs from a document extraction (one match per
    field).
``ownership_gap``
    At least one ownership step has ``gap_flag``.
``agreement_only`` (``registered_transfer_types``)
    Only an agreement to sale is present.
``empty_ownership``
    The ownership chain is empty.
``document_type_present`` (``doc_types``, ``label``)
    At least one listed document type is present.
``area_deviation`` (``tolerance``)
    A document area deviates from the profile by more than ``tolerance``.
``hash_mismatch``
    A document's registered hash is marked as mismatched.
``state_is`` (``state``)
    The property state equals the configured value.
``all`` / ``any`` (``conditions``)
    Boolean composition of the conditions above.
``not`` (``condition``)
    Negation of one condition.

Every evaluator returns plain ``ConditionMatch`` objects. Rule text is rendered
with the match variables, so an administrator can write
``"Profile {field} differs from documents"`` once and get one finding per
mismatched identifier.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from app.services import normalize
from app.services.interfaces import FlagDraft

logger = logging.getLogger(__name__)

PACK_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "mh_rule_pack_v1.json"


@dataclass(frozen=True)
class RuleDefinition:
    """One evaluable rule, independent of the ORM."""

    rule_code: str
    title: str
    description: str | None
    category: str
    severity: str
    confidence: float = 0.8
    conditions: dict[str, Any] | None = None
    evidence_required: Any | None = None
    recommended_action: str | None = None
    law_name: str | None = None
    section: str | None = None
    source_url: str | None = None
    jurisdiction: str = "Maharashtra"
    effective_from: date | None = None
    effective_to: date | None = None
    is_active: bool = True
    rule_id: int | None = None
    version: int | None = 1
    sort_order: int = 0

    def snapshot(self) -> dict[str, Any]:
        """Stable JSON view stored in ``legal_rule_versions.snapshot``."""
        return {
            "rule_code": self.rule_code,
            "jurisdiction": self.jurisdiction,
            "law_name": self.law_name,
            "section": self.section,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "severity": self.severity,
            "confidence": self.confidence,
            "conditions": self.conditions,
            "evidence_required": self.evidence_required,
            "recommended_action": self.recommended_action,
            "source_url": self.source_url,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "is_active": self.is_active,
            "version": self.version or 1,
        }


@dataclass
class ConditionMatch:
    """One triggered occurrence, with text for the finding."""

    evidence: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionOutcome:
    matches: list[ConditionMatch] = field(default_factory=list)
    short_circuit: bool = False


@dataclass
class RuleContext:
    profile: dict[str, Any]
    extracted: list[dict[str, Any]]
    documents: list[dict[str, Any]]
    doc_types: set[str]
    ownership: list[dict[str, Any]]

    @property
    def document_labels(self) -> list[str]:
        """Filenames when every extraction can be matched to a document."""
        documents = self.profile.get("documents")
        if isinstance(documents, list) and len(documents) == len(self.extracted):
            labels: list[str] = []
            for index, item in enumerate(documents):
                filename = item.get("filename") if isinstance(item, dict) else None
                labels.append(str(filename) if filename else f"document {index + 1}")
            return labels
        return [f"document {index + 1}" for index in range(len(self.extracted))]


def _documents(profile: dict, extracted: list[dict]) -> list[dict[str, Any]]:
    documents = profile.get("documents")
    if isinstance(documents, list) and documents:
        return [
            {
                "doc_id": item.get("doc_id"),
                "filename": str(item.get("filename") or f"document {item.get('doc_id')}"),
                "doc_type": item.get("doc_type") or "unknown",
                "blockchain_verified": item.get("blockchain_verified"),
            }
            for item in documents
            if isinstance(item, dict)
        ]
    return [
        {
            "doc_id": None,
            "filename": f"document {index + 1}",
            "doc_type": payload.get("doc_type") or "unknown",
            "blockchain_verified": None,
        }
        for index, payload in enumerate(extracted)
        if isinstance(payload, dict)
    ]


def _ownership(profile: dict) -> list[dict[str, Any]]:
    ownership = profile.get("ownership")
    if isinstance(ownership, list):
        return [node for node in ownership if isinstance(node, dict)]
    return []


def build_context(profile: dict | None, extracted: list[dict] | None) -> RuleContext:
    profile = profile or {}
    extracted = [payload for payload in (extracted or []) if isinstance(payload, dict)]
    documents = _documents(profile, extracted)
    return RuleContext(
        profile=profile,
        extracted=extracted,
        documents=documents,
        doc_types={document["doc_type"] for document in documents if document["doc_type"]},
        ownership=_ownership(profile),
    )


def _hash_mismatch(value: Any) -> bool:
    """True when a verification result says the stored hash did not match."""
    return value is False or value == 0


def _one(evidence: str | None, **variables: Any) -> ConditionOutcome:
    return ConditionOutcome(matches=[ConditionMatch(evidence=evidence, variables=variables)])


def _none() -> ConditionOutcome:
    return ConditionOutcome()


def _eval_no_documents(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    if ctx.documents:
        return _none()
    return _one("Zero completed document extractions")


def _eval_missing_doc_type(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    doc_type = str(condition.get("doc_type") or "")
    if doc_type in ctx.doc_types:
        return _none()
    label = str(condition.get("label") or doc_type.replace("_", " ") or "required document")
    evidence = str(condition.get("evidence") or f"No document classified as {label} among the uploads")
    return _one(evidence, doc_type=doc_type, label=label)


def _eval_profile_identifier_missing(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    expected_state = condition.get("state")
    if expected_state and ctx.profile.get("state") != expected_state:
        return _none()
    fields = condition.get("fields") or ["survey_number", "gat_number", "cts_number"]
    if any(str(ctx.profile.get(field) or "").strip() for field in fields):
        return _none()
    return _one("Property profile missing survey/Gat/CTS number", fields=fields)


def _eval_identifier_mismatch(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    matches: list[ConditionMatch] = []
    labels = ctx.document_labels
    for field_name in condition.get("fields") or ["survey_number", "gat_number", "cts_number"]:
        profile_value = str(ctx.profile.get(field_name) or "").strip()
        if not profile_value:
            continue
        wanted = normalize.normalize_identifier(profile_value)
        disagreements: list[str] = []
        for index, payload in enumerate(ctx.extracted):
            raw = payload.get(field_name)
            if not raw:
                continue
            observed = normalize.normalize_identifier(str(raw))
            if observed and observed != wanted:
                disagreements.append(f"{raw} in {labels[index]}")
        if not disagreements:
            continue
        field_label = str(field_name).replace("_", " ")
        joined = ", ".join(disagreements)
        matches.append(
            ConditionMatch(
                evidence=f"Profile: {profile_value}; extracted: {joined}",
                variables={
                    "field": field_label,
                    "profile_value": profile_value,
                    "disagreements": joined,
                },
            )
        )
    return ConditionOutcome(matches=matches)


def _eval_ownership_gap(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    gaps = [node for node in ctx.ownership if node.get("gap_flag")]
    if not gaps:
        return _none()
    evidence = " | ".join(
        "Step {sequence}: {from_part} → {to} ({ref})".format(
            sequence=node.get("sequence"),
            from_part=node.get("from_party") or "unknown transferor",
            to=node.get("to_party") or "unknown",
            ref=node.get("document_ref") or "no document",
        )
        for node in gaps
    )
    return _one(evidence, gaps=len(gaps))


def _eval_agreement_only(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    transfer_types = {str(node.get("transfer_type") or "") for node in ctx.ownership}
    registered = set(condition.get("registered_transfer_types") or ["sale", "gift", "partition", "mutation"])
    if "agreement" in transfer_types and not transfer_types & registered:
        return _one("Ownership chain contains only an agreement step")
    return _none()


def _eval_empty_ownership(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    if ctx.ownership:
        return _none()
    return _one("Ownership chain is empty")


def _eval_document_type_present(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    wanted = {str(value) for value in (condition.get("doc_types") or [])}
    present = [document for document in ctx.documents if document["doc_type"] in wanted]
    if not present:
        return _none()
    label = str(condition.get("label") or "Documents")
    filenames = ", ".join(document["filename"] for document in present)
    return _one(f"{label}: {filenames}", doc_types=sorted(wanted), documents=filenames)


def _eval_area_deviation(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    try:
        profile_area = float(ctx.profile.get("area_sqft"))
    except (TypeError, ValueError):
        return _none()
    if profile_area <= 0:
        return _none()
    try:
        tolerance = float(condition.get("tolerance", 0.05))
    except (TypeError, ValueError):
        tolerance = 0.05

    deviations: list[tuple[float, float]] = []
    for payload in ctx.extracted:
        raw = payload.get("area_sqft")
        try:
            document_area = float(raw) if raw is not None else None
        except (TypeError, ValueError):
            document_area = None
        if document_area is None or document_area <= 0:
            continue
        spread = abs(document_area - profile_area) / max(profile_area, document_area)
        if spread > tolerance:
            deviations.append((document_area, spread))
    if not deviations:
        return _none()

    evidence = (
        f"Profile: {profile_area:.0f} sqft; documents: "
        + ", ".join(f"{area:.0f} sqft ({spread:.0%} off)" for area, spread in deviations)
    )
    return _one(evidence, profile_area=profile_area, tolerance=tolerance)


def _eval_hash_mismatch(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    mismatched = [
        document["filename"]
        for document in ctx.documents
        if _hash_mismatch(document.get("blockchain_verified"))
    ]
    if not mismatched:
        return _none()
    return _one("Hash mismatch on: " + ", ".join(mismatched), documents=", ".join(mismatched))


def _eval_state_is(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    expected = str(condition.get("state") or "")
    if expected and ctx.profile.get("state") == expected:
        return _one(f"Property state is {expected}", state=expected)
    return _none()


def _eval_all(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    children = condition.get("conditions") or []
    matches: list[ConditionMatch] = []
    variables: dict[str, Any] = {}
    evidence: list[str] = []
    short_circuit = bool(condition.get("short_circuit"))
    for child in children:
        outcome = evaluate_condition(child, ctx)
        if not outcome.matches:
            return _none()
        for match in outcome.matches:
            if match.evidence:
                evidence.append(match.evidence)
            variables.update(match.variables)
        matches.extend(outcome.matches)
        short_circuit = short_circuit or outcome.short_circuit
    return ConditionOutcome(
        matches=matches or [ConditionMatch(evidence="; ".join(evidence) or None, variables=variables)],
        short_circuit=short_circuit,
    )


def _eval_any(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    short_circuit = bool(condition.get("short_circuit"))
    for child in condition.get("conditions") or []:
        outcome = evaluate_condition(child, ctx)
        if outcome.matches:
            return ConditionOutcome(matches=outcome.matches, short_circuit=short_circuit or outcome.short_circuit)
    return _none()


def _eval_not(ctx: RuleContext, condition: dict) -> ConditionOutcome:
    child = condition.get("condition")
    if not isinstance(child, dict):
        return _none()
    outcome = evaluate_condition(child, ctx)
    if outcome.matches:
        return _none()
    return _one("Condition did not match", negated=child.get("type"))


_EVALUATORS = {
    "no_documents": _eval_no_documents,
    "missing_doc_type": _eval_missing_doc_type,
    "profile_identifier_missing": _eval_profile_identifier_missing,
    "identifier_mismatch": _eval_identifier_mismatch,
    "ownership_gap": _eval_ownership_gap,
    "agreement_only": _eval_agreement_only,
    "empty_ownership": _eval_empty_ownership,
    "document_type_present": _eval_document_type_present,
    "area_deviation": _eval_area_deviation,
    "hash_mismatch": _eval_hash_mismatch,
    "state_is": _eval_state_is,
    "all": _eval_all,
    "any": _eval_any,
    "not": _eval_not,
}


def evaluate_condition(condition: dict, ctx: RuleContext) -> ConditionOutcome:
    """Evaluate one condition; unknown types are a no-match at runtime."""
    if not isinstance(condition, dict):
        return _none()
    evaluator = _EVALUATORS.get(str(condition.get("type") or ""))
    if evaluator is None:
        logger.warning("Unknown rule condition type %r; rule will not fire", condition.get("type"))
        return _none()
    outcome = evaluator(ctx, condition)
    if condition.get("short_circuit") and outcome.matches:
        outcome.short_circuit = True
    return outcome


class _SafeVars(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def render_template(template: str | None, variables: dict[str, Any]) -> str:
    if not template:
        return ""
    try:
        return str(template).format_map(_SafeVars(variables))
    except (KeyError, ValueError):
        return str(template)


def evaluate_pack(
    rules: list[RuleDefinition],
    profile: dict | None,
    extracted: list[dict] | None,
) -> list[FlagDraft]:
    """Evaluate a rule catalogue, preserving the catalogue order."""
    ctx = build_context(profile, extracted)
    findings: list[FlagDraft] = []
    ordered = sorted(rules, key=lambda rule: (rule.sort_order, rule.rule_code))
    for rule in ordered:
        if not rule.is_active or not rule.conditions:
            continue
        outcome = evaluate_condition(rule.conditions, ctx)
        for match in outcome.matches:
            variables = {"rule_code": rule.rule_code, **match.variables}
            findings.append(
                FlagDraft(
                    category=rule.category,
                    title=render_template(rule.title, variables) or rule.rule_code,
                    description=render_template(rule.description, variables),
                    severity=rule.severity,
                    confidence=float(rule.confidence),
                    evidence=match.evidence,
                    rule_ref=rule.rule_code,
                    recommended_action=render_template(rule.recommended_action, variables) or None,
                    rule_id=rule.rule_id,
                    rule_version=rule.version,
                )
            )
        if outcome.short_circuit and outcome.matches:
            break
    return findings


def pack_signature(rules: list[RuleDefinition]) -> str:
    """SHA-256 of the canonical active catalogue (version included)."""
    payload = [rule.snapshot() for rule in sorted(rules, key=lambda rule: rule.rule_code)]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_ALLOWED_KEYS: dict[str, set[str]] = {
    "no_documents": {"type", "short_circuit"},
    "missing_doc_type": {"type", "doc_type", "evidence", "label", "short_circuit"},
    "profile_identifier_missing": {"type", "state", "fields", "short_circuit"},
    "identifier_mismatch": {"type", "fields", "short_circuit"},
    "ownership_gap": {"type", "evidence", "short_circuit"},
    "agreement_only": {"type", "registered_transfer_types", "short_circuit"},
    "empty_ownership": {"type", "evidence", "short_circuit"},
    "document_type_present": {"type", "doc_types", "label", "evidence", "short_circuit"},
    "area_deviation": {"type", "tolerance", "short_circuit"},
    "hash_mismatch": {"type", "evidence", "short_circuit"},
    "state_is": {"type", "state", "short_circuit"},
    "all": {"type", "conditions", "short_circuit"},
    "any": {"type", "conditions", "short_circuit"},
    "not": {"type", "condition", "short_circuit"},
}


def _non_empty_list(value: Any, name: str) -> list:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{name} must contain non-empty strings")
    return value


def validate_condition(condition: dict | None) -> None:
    """Validate a condition tree; raises ``ValueError`` with a useful message."""
    if condition is None:
        return
    if not isinstance(condition, dict):
        raise ValueError("conditions must be an object")
    condition_type = str(condition.get("type") or "")
    if condition_type not in _ALLOWED_KEYS:
        raise ValueError(f"unknown condition type: {condition_type or '<missing>'}")
    unknown = set(condition) - _ALLOWED_KEYS[condition_type]
    if unknown:
        raise ValueError(f"unknown keys for {condition_type}: {', '.join(sorted(unknown))}")
    if "short_circuit" in condition and not isinstance(condition["short_circuit"], bool):
        raise ValueError("short_circuit must be true or false")
    if "evidence" in condition and not isinstance(condition["evidence"], str):
        raise ValueError("evidence must be a string")

    if condition_type == "missing_doc_type":
        if not str(condition.get("doc_type") or "").strip():
            raise ValueError("missing_doc_type requires doc_type")
    elif condition_type in {"document_type_present"}:
        _non_empty_list(condition.get("doc_types"), "doc_types")
    elif condition_type in {"profile_identifier_missing", "identifier_mismatch"}:
        _non_empty_list(condition.get("fields"), "fields")
    elif condition_type == "agreement_only":
        _non_empty_list(condition.get("registered_transfer_types"), "registered_transfer_types")
    elif condition_type == "area_deviation":
        try:
            tolerance = float(condition.get("tolerance", 0.05))
        except (TypeError, ValueError) as exc:
            raise ValueError("tolerance must be a number between 0 and 1") from exc
        if not 0 <= tolerance <= 1:
            raise ValueError("tolerance must be between 0 and 1")
    elif condition_type == "state_is":
        if not str(condition.get("state") or "").strip():
            raise ValueError("state_is requires state")
    elif condition_type in {"all", "any"}:
        children = condition.get("conditions")
        if not isinstance(children, list) or not children:
            raise ValueError(f"{condition_type} requires a non-empty conditions list")
        for child in children:
            validate_condition(child)
    elif condition_type == "not":
        child = condition.get("condition")
        if not isinstance(child, dict):
            raise ValueError("not requires a condition object")
        validate_condition(child)


def _load_pack_data(path: Path = PACK_DATA_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_builtin_pack() -> tuple[dict[str, Any], list[RuleDefinition]]:
    data = _load_pack_data()
    rules: list[RuleDefinition] = []
    for index, item in enumerate(data["rules"]):
        validate_condition(item.get("conditions"))
        rules.append(
            RuleDefinition(
                rule_code=item["rule_code"],
                title=item["title"],
                description=item.get("description"),
                category=item["category"],
                severity=item["severity"],
                confidence=float(item.get("confidence", 0.8)),
                conditions=item.get("conditions"),
                evidence_required=item.get("evidence_required"),
                recommended_action=item.get("recommended_action"),
                law_name=item.get("law_name"),
                section=item.get("section"),
                source_url=item.get("source_url"),
                jurisdiction=data["jurisdiction"],
                is_active=bool(item.get("is_active", True)),
                version=1,
                sort_order=index,
            )
        )
    return data, rules


PACK_META, BUILTIN_MH_RULES = _load_builtin_pack()
BUILTIN_PACK_CODE = str(PACK_META["pack_code"])
BUILTIN_PACK_JURISDICTION = str(PACK_META["jurisdiction"])
BUILTIN_PACK_NAME = str(PACK_META["name"])


def pack_name(jurisdiction: str) -> str:
    if jurisdiction == BUILTIN_PACK_JURISDICTION:
        return BUILTIN_PACK_NAME
    return f"{jurisdiction} screening pack"
