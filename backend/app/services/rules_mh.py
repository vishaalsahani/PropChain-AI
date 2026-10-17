"""Maharashtra due-diligence rule pack v1 (Phase 3, FR-5, AC-6).

``MaharashtraRuleEngine`` evaluates the property profile (enriched by
``analysis_engine.run_property_analysis`` with the uploaded ``documents`` and
the built ``ownership`` chain) plus the per-document extractions. Every rule
below is a *screening indicator*, worded so a reviewer can verify it — none of
them declares fraud or an invalid title (Conflict-Handling rule, master plan
1.4).

Rules (id → what triggers it):

===================  =======================================================
``MH-DOC-001``       no completed document extraction at all
``MH-LAND-712``      no 7/12 extract among the uploads
``MH-IDENT-001``     Maharashtra property profile without survey/Gat/CTS
``MH-IDENT-002``     profile identifier disagrees with an extracted one
``MH-CHAIN-001``     an ownership step whose transferor is not evidenced
``MH-CHAIN-002``     only an agreement to sale, no registered transfer
``MH-CHAIN-003``     no ownership evidence (no transfer, no holder record)
``MH-ENC-001``       a mortgage deed is among the documents
``MH-SUCC-001``      a will or partition deed needs succession review
``MH-LIT-001``       a court document is among the documents
``MH-AREA-001``      a document area deviates >5% from the profile area
``MH-INTEGRITY-001`` an uploaded document's hash is recorded as mismatched
===================  =======================================================

The DB-backed, versioned rule catalogue (``legal_rules``) stays Phase 4; this
module is the code-level pack the package ships with.
"""

from __future__ import annotations

from typing import Any

from app.services import normalize
from app.services.interfaces import FlagDraft

#: Document area vs profile area mismatch tolerance (same 5% as the validator).
AREA_TOLERANCE = 0.05

#: Transfer types that convey title (used to tell "transfer" from "agreement").
_REGISTERED_TRANSFERS = ("sale", "gift", "partition", "mutation")


class MaharashtraRuleEngine:
    """Code-level Maharashtra screening rules (v1)."""

    engine_version = "mh-v1"

    def evaluate(self, property_profile: dict, extracted: list[dict]) -> list[FlagDraft]:
        profile = property_profile or {}
        documents = _documents(profile, extracted)
        doc_types = {document["doc_type"] for document in documents if document["doc_type"]}
        ownership = _ownership(profile)

        findings: list[FlagDraft] = []

        if not documents:
            findings.append(_no_documents())
            return findings

        findings += _land_record_rules(doc_types)
        findings += _identity_rules(profile, extracted)
        findings += _ownership_rules(ownership)
        findings += _charge_rules(documents)
        findings += _area_rules(profile, extracted)
        findings += _integrity_rules(documents)
        return findings


def _documents(profile: dict, extracted: list[dict]) -> list[dict[str, Any]]:
    """Normalized document list from the enriched profile, else extractions."""
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


def _document_labels(profile: dict, count: int) -> list[str]:
    """Human labels for the extraction list: filenames when the profile has them."""
    documents = profile.get("documents")
    if isinstance(documents, list) and len(documents) == count:
        labels: list[str] = []
        for index, item in enumerate(documents):
            filename = item.get("filename") if isinstance(item, dict) else None
            labels.append(str(filename) if filename else f"document {index + 1}")
        return labels
    return [f"document {index + 1}" for index in range(count)]


def _hash_mismatch(value: Any) -> bool:
    """True when a verification result says the stored hash did not match.

    Accepts the ORM ``Boolean`` (``False``) and a JSON ``0``; ``None`` means
    verification has not been run and is never treated as a mismatch.
    """
    return value is False or value == 0


def _no_documents() -> FlagDraft:
    return FlagDraft(
        category="missing-document",
        title="No processed documents",
        description="Upload and process property documents before due diligence.",
        severity="medium",
        confidence=1.0,
        evidence="Zero completed document extractions",
        rule_ref="MH-DOC-001",
        recommended_action="Upload at least the 7/12 extract and the latest transfer deed.",
    )


def _land_record_rules(doc_types: set[str]) -> list[FlagDraft]:
    if "7_12_extract" in doc_types:
        return []
    return [
        FlagDraft(
            category="missing-document",
            title="7/12 extract not found",
            description=(
                "Maharashtra land due diligence typically requires a 7/12 extract "
                "(record of rights) for the latest position."
            ),
            severity="high",
            confidence=0.9,
            evidence="No document classified as 7/12 among the uploads",
            rule_ref="MH-LAND-712",
            recommended_action="Download the current 7/12 extract from Mahabhulekh and upload it.",
        )
    ]


def _identity_rules(profile: dict, extracted: list[dict]) -> list[FlagDraft]:
    findings: list[FlagDraft] = []
    profile_ids = {
        field: str(profile.get(field) or "").strip()
        for field in ("survey_number", "gat_number", "cts_number")
    }
    if profile.get("state") == "Maharashtra" and not any(profile_ids.values()):
        findings.append(
            FlagDraft(
                category="identity",
                title="Survey/Gat number missing in property profile",
                description=(
                    "The property profile carries no survey, Gat or CTS number, so "
                    "documents cannot be tied to a land record."
                ),
                severity="medium",
                confidence=0.85,
                evidence="Property profile missing survey/Gat/CTS number",
                rule_ref="MH-IDENT-001",
                recommended_action="Add the survey/Gat number from the 7/12 extract to the profile.",
            )
        )

    for field, profile_value in profile_ids.items():
        if not profile_value:
            continue
        wanted = normalize.normalize_identifier(profile_value)
        labels = _document_labels(profile, len(extracted))
        disagreements = []
        for index, payload in enumerate(extracted):
            if not isinstance(payload, dict):
                continue
            raw = payload.get(field)
            if not raw:
                continue
            observed = normalize.normalize_identifier(str(raw))
            if observed and observed != wanted:
                disagreements.append(f"{raw} in {labels[index]}")
        if disagreements:
            findings.append(
                FlagDraft(
                    category="identity",
                    title=f"Profile {field.replace('_', ' ')} differs from documents",
                    description=(
                        "The identifier in the property profile does not match the "
                        "value extracted from the uploaded documents."
                    ),
                    severity="high",
                    confidence=0.85,
                    evidence=(
                        f"Profile: {profile_value}; extracted: " + ", ".join(disagreements)
                    ),
                    rule_ref="MH-IDENT-002",
                    recommended_action=(
                        "Confirm which identifier is correct against the 7/12 extract "
                        "and correct the profile or re-upload the document."
                    ),
                )
            )
    return findings


def _ownership_rules(ownership: list[dict]) -> list[FlagDraft]:
    findings: list[FlagDraft] = []

    gaps = [node for node in ownership if node.get("gap_flag")]
    if gaps:
        evidence = " | ".join(
            "Step {sequence}: {from_part} → {to} ({ref})".format(
                sequence=node.get("sequence"),
                from_part=node.get("from_party") or "unknown transferor",
                to=node.get("to_party") or "unknown",
                ref=node.get("document_ref") or "no document",
            )
            for node in gaps
        )
        findings.append(
            FlagDraft(
                category="ownership",
                title="Ownership chain has an unevidenced step",
                description=(
                    "At least one transfer in the ownership chain cannot be linked to "
                    "an uploaded document; the missing instrument must be produced "
                    "before the chain can be treated as continuous."
                ),
                severity="high",
                confidence=0.8,
                evidence=evidence,
                rule_ref="MH-CHAIN-001",
                recommended_action=(
                    "Request the missing predecessor deed/mutation from the seller "
                    "and upload it to close the chain."
                ),
            )
        )

    transfer_types = {
        str(node.get("transfer_type") or "") for node in ownership
    }
    if "agreement" in transfer_types and not transfer_types & set(_REGISTERED_TRANSFERS):
        findings.append(
            FlagDraft(
                category="ownership",
                title="Only an agreement to sale is available",
                description=(
                    "An agreement to sale does not by itself convey title; no "
                    "registered transfer (sale/gift/partition/mutation) was found."
                ),
                severity="medium",
                confidence=0.8,
                evidence="Ownership chain contains only an agreement step",
                rule_ref="MH-CHAIN-002",
                recommended_action="Ask for the executed and registered sale deed that followed the agreement.",
            )
        )

    if not ownership:
        findings.append(
            FlagDraft(
                category="ownership",
                title="No ownership evidence in the uploaded documents",
                description=(
                    "The uploads contain neither a transfer instrument nor a land "
                    "record naming the holder, so no ownership chain could be built."
                ),
                severity="medium",
                confidence=0.9,
                evidence="Ownership chain is empty",
                rule_ref="MH-CHAIN-003",
                recommended_action="Upload a transfer deed and/or the current 7/12 extract or property card.",
            )
        )
    return findings


def _charge_rules(documents: list[dict]) -> list[FlagDraft]:
    findings: list[FlagDraft] = []

    mortgage_docs = [d["filename"] for d in documents if d["doc_type"] == "mortgage_deed"]
    if mortgage_docs:
        findings.append(
            FlagDraft(
                category="mortgage",
                title="Mortgage deed among the documents",
                description=(
                    "A mortgage creates a charge against the property; it must be "
                    "cleared or consented to at transfer."
                ),
                severity="high",
                confidence=0.85,
                evidence="Mortgage deed: " + ", ".join(mortgage_docs),
                rule_ref="MH-ENC-001",
                recommended_action=(
                    "Verify the charge in the encumbrance certificate and obtain the "
                    "bank's no-dues / release deed."
                ),
            )
        )

    succession_docs = [
        d["filename"] for d in documents if d["doc_type"] in ("will", "partition_deed")
    ]
    if succession_docs:
        findings.append(
            FlagDraft(
                category="succession",
                title="Succession document requires verification",
                description=(
                    "A will or partition introduces succession-derived ownership; "
                    "probate/partition formalities and all legal heirs must be verified."
                ),
                severity="medium",
                confidence=0.8,
                evidence="Succession-related documents: " + ", ".join(succession_docs),
                rule_ref="MH-SUCC-001",
                recommended_action="Obtain the probate/partition deed and confirm the legal-heir chain.",
            )
        )

    court_docs = [d["filename"] for d in documents if d["doc_type"] == "court_document"]
    if court_docs:
        findings.append(
            FlagDraft(
                category="litigation",
                title="Court document among the documents",
                description=(
                    "A filed document suggests pending or past proceedings touching "
                    "the property; the current status must be checked."
                ),
                severity="high",
                confidence=0.85,
                evidence="Court document: " + ", ".join(court_docs),
                rule_ref="MH-LIT-001",
                recommended_action="Search the court case status and obtain a certified copy of the order.",
            )
        )
    return findings


def _area_rules(profile: dict, extracted: list[dict]) -> list[FlagDraft]:
    try:
        profile_area = float(profile.get("area_sqft"))
    except (TypeError, ValueError):
        return []
    if profile_area <= 0:
        return []

    deviations: list[tuple[float, float]] = []
    for payload in extracted:
        if not isinstance(payload, dict):
            continue
        raw = payload.get("area_sqft")
        try:
            document_area = float(raw) if raw is not None else None
        except (TypeError, ValueError):
            document_area = None
        if document_area is None or document_area <= 0:
            continue
        spread = abs(document_area - profile_area) / max(profile_area, document_area)
        if spread > AREA_TOLERANCE:
            deviations.append((document_area, spread))
    if not deviations:
        return []

    evidence = (
        f"Profile: {profile_area:.0f} sqft; documents: "
        + ", ".join(f"{area:.0f} sqft ({spread:.0%} off)" for area, spread in deviations)
    )
    return [
        FlagDraft(
            category="area",
            title="Document area differs from the property profile",
            description=(
                f"At least one document deviates by more than {AREA_TOLERANCE:.0%} "
                "from the area recorded in the property profile."
            ),
            severity="medium",
            confidence=0.75,
            evidence=evidence,
            rule_ref="MH-AREA-001",
            recommended_action="Re-check the area against the 7/12 extract and re-measure if needed.",
        )
    ]


def _integrity_rules(documents: list[dict]) -> list[FlagDraft]:
    mismatched = [
        document["filename"]
        for document in documents
        if _hash_mismatch(document.get("blockchain_verified"))
    ]
    if not mismatched:
        return []
    return [
        FlagDraft(
            category="document-integrity",
            title="Registered hash does not match the file",
            description=(
                "One or more documents changed after their hash was recorded: the "
                "on-chain record and the file no longer agree."
            ),
            severity="critical",
            confidence=0.95,
            evidence="Hash mismatch on: " + ", ".join(mismatched),
            rule_ref="MH-INTEGRITY-001",
            recommended_action="Re-obtain the document from the source; treat the changed file as untrusted.",
        )
    ]
