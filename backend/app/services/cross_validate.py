"""Cross-document consistency validation (Phase 3, FR-4, AC-3).

``MatrixCrossValidator`` compares the *extracted* field values of one property's
documents against each other. Every disagreement becomes a ``FlagDraft`` whose
evidence names the documents and the values compared, so a reviewer can see
exactly what conflicted. Documents that simply do not carry a field are never
turned into mismatches — "missing" is not "different" (Responsible-AI: unknown
states stay representable).

Comparison rules (the "matrix" tolerances):

* identifiers (survey / Gat / CTS, registration numbers): canonical equality
  after the same normalization the extractor emits;
* person and place names: fuzzy match ≥ :data:`NAME_MATCH_THRESHOLD`
  (honorific-, case- and punctuation-insensitive);
* areas: in square feet, relative spread > :data:`AREA_TOLERANCE` (5%) flags;
  the unit conversion happens in extraction, so this compares like with like;
* boundaries: fuzzy match ≥ :data:`BOUNDARY_THRESHOLD` counts as agreeing
  (wording legitimately varies between offices);
* dates: ``execution_date`` must not fall after ``registration_date`` inside
  one document.

Rule refs are stable: ``MATCH-<FIELD>-<KIND>``. Categories come from the
specification's 12-item Risk Output list (Specs p.4 Table 6), so the current
category strings are the normative ones (no aliases needed).
"""

from __future__ import annotations

from typing import Any

from app.services import normalize
from app.services.interfaces import FlagDraft

#: Fuzzy-match threshold for names/places to count as "the same" (0-100).
NAME_MATCH_THRESHOLD = 85.0

#: Boundaries wording varies more; below this similarity it is a disagreement.
BOUNDARY_THRESHOLD = 70.0

#: Relative area spread (max vs min) above which documents disagree.
AREA_TOLERANCE = 0.05

#: Identifier fields compared across documents, with their rule-ref suffix.
_IDENTIFIER_FIELDS = (
    ("survey_number", "SURVEY"),
    ("gat_number", "GAT"),
    ("cts_number", "CTS"),
)

#: Name/place fields compared across documents.
_NAME_FIELDS = (
    ("owner_name", "OWNER"),
    ("village", "VILLAGE"),
    ("district", "DISTRICT"),
)


class MatrixCrossValidator:
    """Pairwise field matrix over one property's extracted documents."""

    engine_version = "matrix-v1"

    def validate(
        self,
        extracted: dict[int, dict],
        document_meta: dict[int, dict],
    ) -> list[FlagDraft]:
        docs = _documents(extracted, document_meta)
        findings: list[FlagDraft] = []
        findings += _identifier_findings(docs)
        findings += _name_findings(docs)
        findings += _area_findings(docs)
        findings += _boundary_findings(docs)
        findings += _registration_findings(docs)
        findings += _date_order_findings(docs)
        findings += _integrity_findings(docs)
        return findings


class _Doc:
    """One extracted document with the labels used in evidence text."""

    __slots__ = ("doc_id", "filename", "doc_type", "payload", "blockchain_verified")

    def __init__(self, doc_id: int, meta: dict[str, Any], payload: dict[str, Any]):
        self.doc_id = doc_id
        self.filename = str(meta.get("filename") or f"document {doc_id}")
        self.doc_type = str(meta.get("doc_type") or "unknown")
        self.payload = payload
        # The pipeline carries the on-chain verification result in document_meta;
        # older callers put it in the extracted blob. Accept either.
        verified = meta.get("blockchain_verified")
        if verified is None:
            verified = payload.get("blockchain_verified")
        self.blockchain_verified = verified

    def label(self) -> str:
        return f"{self.filename} ({self.doc_type})"

    def get(self, field: str) -> Any:
        value = self.payload.get(field)
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value


def _documents(
    extracted: dict[int, dict],
    document_meta: dict[int, dict],
) -> list[_Doc]:
    docs = []
    for doc_id in sorted(extracted):
        payload = extracted.get(doc_id)
        if not isinstance(payload, dict):
            continue
        docs.append(_Doc(doc_id, document_meta.get(doc_id, {}), payload))
    return docs


def _value_label(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _hash_mismatch(value: Any) -> bool:
    """True when a verification result says the stored hash did not match.

    Accepts the ORM ``Boolean`` (``False``) and a JSON ``0``; ``None`` means
    verification has not been run and is never treated as a mismatch.
    """
    return value is False or value == 0


def _identifier_findings(docs: list[_Doc]) -> list[FlagDraft]:
    findings: list[FlagDraft] = []
    for field, suffix in _IDENTIFIER_FIELDS:
        observed: dict[str, list[_Doc]] = {}
        for doc in docs:
            raw = doc.get(field)
            if raw is None:
                continue
            key = normalize.normalize_identifier(str(raw))
            if key:
                observed.setdefault(key, []).append(doc)
        if len(observed) < 2:
            continue  # nothing to disagree with (0 or 1 distinct value seen)
        parts = [
            f"{key} in " + ", ".join(doc.label() for doc in grouped)
            for key, grouped in sorted(observed.items())
        ]
        findings.append(
            FlagDraft(
                category="identity",
                title=f"{field.replace('_', ' ').title()} mismatch across documents",
                description=(
                    f"The uploaded documents state different {field.replace('_', ' ')} "
                    "values for the same property."
                ),
                severity="high",
                confidence=0.85,
                evidence="; ".join(parts),
                rule_ref=f"MATCH-{suffix}-001",
                recommended_action=(
                    "Confirm which identifier belongs to the property; request the "
                    "corrected document or a certified record."
                ),
            )
        )
    return findings


def _name_findings(docs: list[_Doc]) -> list[FlagDraft]:
    findings: list[FlagDraft] = []
    for field, suffix in _NAME_FIELDS:
        seen: list[tuple[str, _Doc]] = []
        for doc in docs:
            raw = doc.get(field)
            if raw is None:
                continue
            seen.append((normalize.normalize_whitespace(str(raw)), doc))
        if len(seen) < 2:
            continue

        groups: list[list[tuple[str, _Doc]]] = []
        for name, doc in seen:
            placed = False
            for group in groups:
                if normalize.name_similarity(group[0][0], name) >= NAME_MATCH_THRESHOLD:
                    group.append((name, doc))
                    placed = True
                    break
            if not placed:
                groups.append([(name, doc)])
        if len(groups) < 2:
            continue

        parts = [
            f"{group[0][0]} in " + ", ".join(doc.label() for _, doc in group)
            for group in groups
        ]
        findings.append(
            FlagDraft(
                category="identity",
                title=(
                    "Owner name mismatch across documents"
                    if field == "owner_name"
                    else f"{field.title()} mismatch across documents"
                ),
                description=(
                    "The documents name different "
                    f"{'owners' if field == 'owner_name' else field + 's'} "
                    "for the property."
                ),
                severity="high" if field == "owner_name" else "medium",
                confidence=0.8 if field == "owner_name" else 0.7,
                evidence="; ".join(parts),
                rule_ref=f"MATCH-{suffix}-001",
                recommended_action=(
                    "Verify the owner's identity against the latest land record "
                    "(7/12 or property card) and the supporting deeds."
                ),
            )
        )
    return findings


def _area_findings(docs: list[_Doc]) -> list[FlagDraft]:
    areas: list[tuple[float, _Doc, str]] = []
    for doc in docs:
        raw = doc.get("area_sqft")
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value <= 0:
            continue
        unit = doc.get("area_unit") or "sqft"
        areas.append((value, doc, str(unit)))
    if len(areas) < 2:
        return []

    smallest = min(areas, key=lambda item: item[0])
    largest = max(areas, key=lambda item: item[0])
    spread = (largest[0] - smallest[0]) / largest[0]
    if spread <= AREA_TOLERANCE:
        return []

    evidence = "; ".join(
        f"{_value_label(value)} sqft ({unit} as printed) in {doc.label()}"
        for value, doc, unit in sorted(areas, key=lambda item: item[0])
    )
    return [
        FlagDraft(
            category="area",
            title="Area discrepancy detected",
            description=(
                "Document areas disagree by more than "
                f"{AREA_TOLERANCE:.0%} after unit conversion."
            ),
            severity="medium",
            confidence=0.8,
            evidence=evidence,
            rule_ref="MATCH-AREA-001",
            recommended_action=(
                "Re-measure against the 7/12 extract and the property card; a "
                "material difference needs a surveyor's confirmation."
            ),
        )
    ]


def _boundary_findings(docs: list[_Doc]) -> list[FlagDraft]:
    seen: list[tuple[str, _Doc]] = [
        (normalize.normalize_whitespace(str(doc.get("boundaries"))), doc)
        for doc in docs
        if doc.get("boundaries") is not None
    ]
    if len(seen) < 2:
        return []

    conflicts: list[str] = []
    for index, (text_a, doc_a) in enumerate(seen):
        for text_b, doc_b in seen[index + 1:]:
            if normalize.name_similarity(text_a, text_b) < BOUNDARY_THRESHOLD:
                conflicts.append(f"{doc_a.label()} says \"{text_a}\"; {doc_b.label()} says \"{text_b}\"")
    if not conflicts:
        return []

    return [
        FlagDraft(
            category="area",
            title="Boundary description mismatch",
            description="Documents describe different boundaries for the property.",
            severity="medium",
            confidence=0.65,
            evidence=" | ".join(conflicts[:3]),
            rule_ref="MATCH-BOUNDARY-001",
            recommended_action="Compare the boundary descriptions with the latest land record and site plan.",
        )
    ]


def _registration_findings(docs: list[_Doc]) -> list[FlagDraft]:
    observed: dict[str, list[_Doc]] = {}
    for doc in docs:
        # A mutation (ferfar) quotes the registration number of the instrument
        # it records — that repetition is the correct behaviour, not a clash.
        if doc.doc_type == "ferfar":
            continue
        raw = doc.get("registration_number")
        if raw is None:
            continue
        key = normalize.normalize_registration_number(str(raw))
        if key:
            observed.setdefault(key, []).append(doc)
    duplicates = {key: grouped for key, grouped in observed.items() if len(grouped) > 1}
    if not duplicates:
        return []

    parts = [
        f"{key} appears in " + ", ".join(doc.label() for doc in grouped)
        for key, grouped in sorted(duplicates.items())
    ]
    return [
        FlagDraft(
            category="identity",
            title="Registration number reused across documents",
            description=(
                "The same registration number appears on more than one uploaded "
                "document; registration numbers are unique per registered instrument."
            ),
            severity="medium",
            confidence=0.75,
            evidence="; ".join(parts),
            rule_ref="MATCH-REGNO-001",
            recommended_action="Check the documents against the sub-registrar's index for a copy or a transcription error.",
        )
    ]


def _date_order_findings(docs: list[_Doc]) -> list[FlagDraft]:
    findings: list[FlagDraft] = []
    for doc in docs:
        execution = normalize.parse_iso_date(str(doc.get("execution_date") or ""))
        registration = normalize.parse_iso_date(str(doc.get("registration_date") or ""))
        if not execution or not registration or execution <= registration:
            continue
        findings.append(
            FlagDraft(
                category="identity",
                title="Execution date after registration date",
                description="The document was executed after its stated registration date.",
                severity="medium",
                confidence=0.7,
                evidence=f"{doc.label()}: execution {execution}, registration {registration}",
                rule_ref="MATCH-DATE-001",
                recommended_action="Verify the dates against the registered instrument copy.",
            )
        )
    return findings


def _integrity_findings(docs: list[_Doc]) -> list[FlagDraft]:
    findings: list[FlagDraft] = []
    for doc in docs:
        if _hash_mismatch(doc.blockchain_verified):
            findings.append(
                FlagDraft(
                    category="document-integrity",
                    title="Hash verification failed",
                    description=(
                        "The document's current SHA-256 hash does not match the hash "
                        "recorded for it — the file may have changed since registration."
                    ),
                    severity="critical",
                    confidence=0.95,
                    evidence=f"{doc.label()}: stored hash mismatch on verification",
                    rule_ref="MATCH-INTEGRITY-001",
                    recommended_action="Re-obtain the document from the source and re-register its hash.",
                )
            )
    return findings
