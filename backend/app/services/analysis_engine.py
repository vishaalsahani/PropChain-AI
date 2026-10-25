"""Analysis pipeline orchestration (Phase 2; verdict since Phase 3; DB rules since Phase 4).

The engine contains no business logic: OCR, classification, field extraction,
cross-document validation, ownership-chain building, rule evaluation and the
FR-8 verdict are delegated to the swappable engines in ``app.services.registry``
(plus the pure verdict policy in ``app.services.verdict``). This module:

  * drives the per-document pipeline (OCR -> language -> classification ->
    extraction -> normalization -> persistence) and stores page-level evidence,
  * records one AnalysisRun per analysis,
  * converts returned FlagDraft/OwnershipDraft objects into ORM rows linked to
    that run.

Decision D10 (revised in Phase 6): every run owns its risk flags and ownership
records. Re-running the analysis creates a new run and leaves earlier rows
attached to their original run, so a reviewer's decision on an old finding is
never silently rewritten. The API reads the latest run by default.

Engine selection lives in ``backend/.env`` (see ``app.config``): the fake
engines keep a fresh machine bootable, the real OCR/NLP engines are opt-in per
machine and tests pin the fakes.
"""

import json
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    AnalysisRun,
    AnalysisRunStatus,
    Document,
    DocumentStatus,
    ExtractedField,
    FieldValueStatus,
    LegalRule,
    OwnershipRecord,
    Property,
    PropertyStatus,
    RiskCategory,
    RiskFlag,
    Severity,
    Verdict,
)
from app.services.registry import (
    get_cross_validator,
    get_doc_classifier,
    get_nlp_extractor,
    get_ocr_service,
    get_ownership_builder,
    get_rule_engine,
)
from app.services.rule_store import DatabaseRuleEngine, load_rule_pack
from app.services.rules_mh import MaharashtraRuleEngine
from app.services.verdict import derive_verdict

#: Pages inside ``ocr_text`` are separated with a form feed (the frozen
#: convention documented in ``app.services.interfaces``).
PAGE_SEPARATOR = "\f"

SEVERITY_WEIGHTS = {"low": 1, "medium": 3, "high": 6, "critical": 10}

#: Pre-Phase-1 category strings -> specification vocabulary (Specs p.4 Table 6).
CATEGORY_ALIASES = {
    "identifier": "identity",
    "missing_document": "missing-document",
    "document_integrity": "document-integrity",
    "land_use": "land-use",
}


def pipeline_engine_version(rule_engine_tag: str | None = None) -> str:
    """Run-level engine tag composed from the configured components.

    Fits ``AnalysisRun.engine_version`` (String(120), widened in migration 0004);
    per-field provenance is stored on ``ExtractedField.extractor_version``.
    ``rule_engine_tag`` lets the caller record the actual DB catalogue signature
    used by the run instead of the registry default.
    """
    parts = [
        get_ocr_service().engine_version,
        get_doc_classifier().engine_version,
        get_nlp_extractor().engine_version,
        get_cross_validator().engine_version,
        get_ownership_builder().engine_version,
        rule_engine_tag or get_rule_engine().engine_version,
    ]
    return ("phase-4|" + "|".join(parts))[:120]


def run_document_pipeline(db: Session, document: Document) -> Document:
    """OCR, classify and extract one document (pipeline stages 3-7).

    A processing failure marks the document ``failed`` and re-raises so the
    caller can surface a clear error; only ``completed`` documents feed the
    property-level analysis.
    """
    document.status = DocumentStatus.processing
    db.commit()

    ocr_service = get_ocr_service()
    classifier = get_doc_classifier()
    nlp = get_nlp_extractor()

    try:
        ocr_result = ocr_service.extract(document.file_path, ["marathi", "english"])
        page_text = PAGE_SEPARATOR.join(page.text for page in ocr_result.pages)
        classification = classifier.classify(document.filename, page_text)
        candidates = nlp.extract(classification.doc_type, page_text)
    except Exception:
        document.status = DocumentStatus.failed
        db.commit()
        raise

    document.doc_type = classification.doc_type
    document.doc_type_confidence = classification.confidence
    document.language = ocr_result.language
    document.page_count = len(ocr_result.pages)
    document.ocr_text = "\n".join(page.text for page in ocr_result.pages)
    document.ocr_pages = [
        {"page": page.page_number, "text": page.text, "confidence": page.confidence}
        for page in ocr_result.pages
    ]

    # Re-run semantics: this document's extracted fields reflect the latest pass.
    db.query(ExtractedField).filter(ExtractedField.document_id == document.id).delete()
    for candidate in candidates:
        db.add(
            ExtractedField(
                document_id=document.id,
                property_id=document.property_id,
                field_name=candidate.field_name,
                raw_value=candidate.raw_value,
                normalized_value=candidate.normalized_value,
                value_type=candidate.value_type,
                value_status=FieldValueStatus.present,
                page=candidate.page,
                snippet=candidate.snippet,
                confidence=candidate.confidence,
                extractor_version=nlp.engine_version,
            )
        )

    document.extracted_data = json.dumps(
        _extracted_blob(classification.doc_type, ocr_result.language, candidates),
        ensure_ascii=False,
    )
    document.status = DocumentStatus.completed
    db.commit()
    db.refresh(document)
    return document


def _extracted_blob(doc_type: str, language: str | None, candidates: list) -> dict:
    """Legacy ``extracted_data`` blob rebuilt from real field candidates.

    Top-level keys keep the pre-Phase-1 names working (the frontend and the
    demo cross-validator read ``survey_number``, ``area_sqft``, ...). Only
    extracted fields appear — a missing key means "unknown", never an invented
    value.
    """
    data: dict = {"doc_type": doc_type}
    for candidate in candidates:
        if candidate.field_name in data:
            continue  # first candidate wins; extraction order is deterministic
        value = _blob_value(candidate)
        if value is not None:
            data[candidate.field_name] = value

    confidences = [c.confidence for c in candidates if c.confidence is not None]
    data["language"] = language
    data["confidence"] = round(sum(confidences) / len(confidences), 4) if confidences else 0.0
    return data


def _blob_value(candidate) -> object | None:
    """Canonical value for the blob: normalized when available, else raw."""
    value = (
        candidate.normalized_value
        if candidate.normalized_value is not None
        else candidate.raw_value
    )
    if value is None:
        return None
    if candidate.value_type == "number":
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    return value


def run_property_analysis(db: Session, property_obj: Property) -> Property:
    """Cross-document validation, ownership graph, rule evaluation and verdict."""
    documents = (
        db.query(Document)
        .filter(Document.property_id == property_obj.id, Document.status == DocumentStatus.completed)
        .all()
    )

    extracted: dict[int, dict] = {}
    extracted_values: list[dict] = []
    document_meta: dict[int, dict] = {}
    profile_documents: list[dict] = []
    for doc in documents:
        payload = json.loads(doc.extracted_data) if doc.extracted_data else None
        # Phase 3: the meta carries everything the ownership builder needs; the
        # fake engines ignore the extra keys (contract stays signature-compatible).
        document_meta[doc.id] = {
            "filename": doc.filename,
            "doc_type": doc.doc_type,
            "language": doc.language,
            "file_hash": doc.file_hash,
            "blockchain_verified": doc.blockchain_verified,
            "extracted": payload,
        }
        profile_documents.append(
            {
                "doc_id": doc.id,
                "filename": doc.filename,
                "doc_type": doc.doc_type,
                "blockchain_verified": doc.blockchain_verified,
            }
        )
        if payload:
            extracted[doc.id] = payload
            extracted_values.append(payload)

    ownership_drafts = get_ownership_builder().build(document_meta)
    drafts = get_cross_validator().validate(extracted, document_meta)
    property_profile = {
        "state": property_obj.state,
        "district": property_obj.district,
        "taluka": property_obj.taluka,
        "village": property_obj.village,
        "survey_number": property_obj.survey_number,
        "gat_number": property_obj.gat_number,
        "cts_number": property_obj.cts_number,
        "area_sqft": property_obj.area_sqft,
        "area_unit": property_obj.area_unit.value,
        # Phase 3 enrichment: the rule pack evaluates the chain it did not build.
        "documents": profile_documents,
        "ownership": [
            {
                "from_party": node.from_party,
                "to_party": node.to_party,
                "transfer_type": node.transfer_type,
                "transfer_date": node.transfer_date,
                "document_ref": node.document_ref,
                "sequence": node.sequence,
                "gap_flag": node.gap_flag,
            }
            for node in ownership_drafts
        ],
    }

    # Phase 4: when the real Maharashtra engine is selected, prefer the active
    # database catalogue. An empty table (fresh install before 0005, or a
    # non-Maharashtra jurisdiction) falls back to the code-level v1 pack.
    rule_engine = get_rule_engine()
    rule_engine_tag = getattr(rule_engine, "engine_version", "unknown")
    if isinstance(rule_engine, MaharashtraRuleEngine):
        loaded_pack = load_rule_pack(db, property_obj.state or "Maharashtra")
        if loaded_pack.total_count:
            rule_engine = DatabaseRuleEngine(loaded_pack)
            rule_engine_tag = rule_engine.engine_version
    drafts += rule_engine.evaluate(property_profile, extracted_values)

    verdict = derive_verdict(drafts, ownership_drafts, profile_documents)

    # Phase 6: do not delete the previous run's rows. Each run is an immutable
    # slice of evidence; readers select the latest run explicitly.
    now = datetime.now(timezone.utc)
    run = AnalysisRun(
        property_id=property_obj.id,
        status=AnalysisRunStatus.completed,
        engine_version=pipeline_engine_version(rule_engine_tag=rule_engine_tag),
        verdict=Verdict(verdict.verdict),
        verdict_reasons=verdict.to_dict(),
        started_at=now,
        finished_at=now,
    )
    db.add(run)
    db.flush()  # assign run.id for the rows below

    # Phase 4 traceability: link every finding to the catalogue row/version that
    # produced it. Cross-validator findings whose ref is not in the legal
    # catalogue keep rule_id NULL and remain traceable by rule_ref.
    catalogue = {rule.rule_code: rule for rule in db.query(LegalRule).all()}
    for draft in drafts:
        linked_rule = catalogue.get(draft.rule_ref) if draft.rule_ref else None
        db.add(
            RiskFlag(
                property_id=property_obj.id,
                analysis_run_id=run.id,
                category=_risk_category(draft.category),
                title=draft.title,
                description=draft.description,
                severity=Severity(draft.severity),
                confidence=draft.confidence,
                evidence=draft.evidence,
                rule_ref=draft.rule_ref,
                rule_id=draft.rule_id or (linked_rule.id if linked_rule else None),
                rule_version=(
                    draft.rule_version
                    or (int(linked_rule.current_version or 1) if linked_rule else None)
                ),
                recommended_action=draft.recommended_action,
            )
        )

    for draft in ownership_drafts:
        db.add(
            OwnershipRecord(
                property_id=property_obj.id,
                analysis_run_id=run.id,
                from_party=draft.from_party,
                to_party=draft.to_party,
                transfer_type=draft.transfer_type,
                transfer_date=_parse_date(draft.transfer_date),
                document_ref=draft.document_ref,
                gap_flag=draft.gap_flag,
                sequence=draft.sequence,
            )
        )

    if drafts:
        total = sum(SEVERITY_WEIGHTS.get(draft.severity, 1) for draft in drafts)
        property_obj.risk_score = min(100.0, total * 5)
    else:
        property_obj.risk_score = 10.0

    run.risk_score = property_obj.risk_score
    finding_count = len(drafts)
    node_count = len(ownership_drafts)
    run.summary = (
        f"Verdict {verdict.verdict.replace('_', ' ')}: "
        f"{finding_count} finding{'s' if finding_count != 1 else ''}, "
        f"{node_count} ownership node{'s' if node_count != 1 else ''}."
    )
    property_obj.status = _property_status(verdict.verdict)
    db.commit()
    db.refresh(property_obj)
    return property_obj


#: FR-8 verdict -> the property-level status it mirrors (enums.PropertyStatus).
_PROPERTY_STATUS = {
    "verified": PropertyStatus.analyzed,
    "needs_review": PropertyStatus.needs_review,
    "flagged": PropertyStatus.flagged,
}


def _property_status(verdict: str) -> PropertyStatus:
    return _PROPERTY_STATUS.get(verdict, PropertyStatus.analyzed)


def _risk_category(value: str) -> RiskCategory:
    """Map an engine category onto the specification vocabulary (fails loudly)."""
    return RiskCategory(CATEGORY_ALIASES.get(value, value))


def _parse_date(value: str | None) -> date | None:
    """Best-effort ISO date parsing; unparseable values stay unset for now."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
