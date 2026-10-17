"""Property-level verdict policy (Phase 3, FR-8, AC-6).

The specification fixes the vocabulary — **Verified / Needs Review / Flagged**
(``app.models.enums.Verdict``) — but not the mapping from findings to a verdict,
so this module is the documented, project-defined policy:

* no completed document → **Needs Review** (nothing could be checked);
* any ``critical``/``high`` finding, or any ownership step whose transferor is
  not evidenced → **Flagged**;
* only ``medium``/``low`` findings → **Needs Review**;
* no findings at all → **Verified**.

The verdict is always accompanied by reasons: the findings that drove it, the
ownership gaps, and — honouring the Responsible-AI rule — an explicit list of
checks that were **not** performed (RERA, litigation history, planning/land-use,
encumbrance when no EC was uploaded). "Not checked" is stated, never turned into
a finding.

Output is a plain dataclass so the analysis pipeline, the AC-3 harness and the
API can all share it without importing ORM models.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.interfaces import FlagDraft, OwnershipDraft

#: Severity order for the reason list (most serious first).
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

#: Severities that make a run "Flagged".
_FLAGGING_SEVERITIES = ("critical", "high")

#: Reasons list length cap (the full detail always lives on the findings rows).
MAX_REASONS = 6


@dataclass
class VerdictOutcome:
    """Verdict plus the reasons and the explicit not-checked list."""

    verdict: str
    reasons: list[str] = field(default_factory=list)
    not_checked: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "reasons": list(self.reasons),
            "not_checked": list(self.not_checked),
        }


def derive_verdict(
    drafts: list[FlagDraft],
    ownership_drafts: list[OwnershipDraft],
    documents: list[dict],
) -> VerdictOutcome:
    """Apply the documented policy to one analysis run's results."""
    not_checked = _not_checked(documents)

    if not documents:
        return VerdictOutcome(
            verdict="needs_review",
            reasons=[
                "No documents have been processed yet, so none of the due-diligence "
                "checks could run."
            ],
            not_checked=not_checked,
        )

    reasons: list[str] = []
    gaps = [node for node in ownership_drafts if node.gap_flag]

    serious = [
        draft for draft in drafts if draft.severity in _FLAGGING_SEVERITIES
    ]
    if serious or gaps:
        for draft in _ordered(serious):
            reasons.append(_finding_reason(draft))
        for node in gaps:
            reasons.append(
                "Ownership step {sequence} ({from_part} → {to}) is not evidenced: "
                "{ref}".format(
                    sequence=node.sequence,
                    from_part=node.from_party or "unknown transferor",
                    to=node.to_party,
                    ref=node.document_ref or "no document reference",
                )
            )
        return VerdictOutcome(
            verdict="flagged",
            reasons=(reasons or ["A serious finding requires review."])[:MAX_REASONS],
            not_checked=not_checked,
        )

    if drafts:
        reasons = [_finding_reason(draft) for draft in _ordered(drafts)][:MAX_REASONS]
        return VerdictOutcome(
            verdict="needs_review",
            reasons=reasons or ["Minor observations need a reviewer's confirmation."],
            not_checked=not_checked,
        )

    return VerdictOutcome(
        verdict="verified",
        reasons=[
            "No ownership, identity, area, encumbrance or document-integrity "
            "findings were raised by the automated checks."
        ],
        not_checked=not_checked,
    )


def _ordered(drafts: list[FlagDraft]) -> list[FlagDraft]:
    return sorted(drafts, key=lambda draft: _SEVERITY_ORDER.get(draft.severity, 9))


def _finding_reason(draft: FlagDraft) -> str:
    ref = f" ({draft.rule_ref})" if draft.rule_ref else ""
    return f"{draft.severity.capitalize()}: {draft.title}{ref}"


def _not_checked(documents: list[dict]) -> list[str]:
    doc_types = {str(document.get("doc_type") or "") for document in documents}
    missing: list[str] = []

    if "rera" not in doc_types:
        missing.append(
            "RERA registration: not checked — no RERA document or project details "
            "were uploaded."
        )
    if "court_document" not in doc_types:
        missing.append(
            "Court/litigation history: not checked — no court records were uploaded "
            "and no court-search service is connected."
        )
    if not doc_types & {"ec", "mortgage_deed"}:
        missing.append(
            "Encumbrance beyond the documents: not checked — no encumbrance "
            "certificate or mortgage deed was uploaded."
        )
    if not doc_types & {"7_12_extract", "property_card"}:
        missing.append(
            "Planning/land-use approvals: not checked — no land record or sanctioned "
            "plan was uploaded."
        )
    return missing
