"""Fake engine implementations.

Every class here is a byte-for-byte behavioural port of the logic that used to
live in ``app.services.analysis_engine`` / ``app.services.rule_engine``: given
the same inputs they produce exactly the same findings, ownership chain and
risk-relevant output, but they return plain dataclasses instead of ORM rows so
they stay independent of ``app.models``.

Today's demo behaviour reproduced here (2 documents: sale_deed_demo.pdf and
7_12_extract_demo.pdf, property state "Maharashtra" with survey_number set):
1 finding (MH-CHAIN-001, high), a 2-node ownership chain, risk score 30.0.

Deliberate deviation from the legacy strings (spec vocabulary, Specs p.4
Table 6 / app.models.enums.RiskCategory): the cross-validator emits category
"identity" (was "identifier") and the rule engine emits "missing-document"
(was "missing_document").
"""

from __future__ import annotations

from pathlib import Path

from app.services.interfaces import (
    ClassificationResult,
    FieldCandidate,
    FlagDraft,
    OcrPage,
    OcrResult,
    OwnershipDraft,
)

ENGINE_VERSION = "fake-v1"

#: Filename keyword -> doc_type, copied 1:1 from analysis_engine._guess_doc_type
#: (dict order matters: the first matching key wins).
DOC_TYPE_KEYWORDS: dict[str, str] = {
    "sale": "sale_deed",
    "712": "7_12_extract",
    "7_12": "7_12_extract",
    "8a": "8a_record",
    "ferfar": "ferfar",
    "property": "property_card",
    "gift": "gift_deed",
    "mortgage": "mortgage_deed",
}
DEFAULT_DOC_TYPE = "sale_deed"
CLASSIFIER_CONFIDENCE = 0.9

#: (field_name, raw_value, value_type) for the current hardcoded mock extraction.
MOCK_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("owner_name", "Rajesh Patil", "string"),
    ("seller_name", "Suresh Deshmukh", "string"),
    ("buyer_name", "Rajesh Patil", "string"),
    ("survey_number", "124/A", "string"),
    ("gat_number", "456", "string"),
    ("area_sqft", "1200.0", "number"),
    ("registration_date", "2019-03-15", "date"),
    ("registration_number", "MH-PUN-2019-12345", "string"),
)
MOCK_FIELD_CONFIDENCE = 0.87
MOCK_LANGUAGE = "marathi"


class FakeDocClassifier:
    """Filename keyword classifier — same mapping as ``_guess_doc_type``."""

    engine_version: str = ENGINE_VERSION

    def classify(self, filename: str, text: str | None = None) -> ClassificationResult:
        lower = (filename or "").lower()
        for key, value in DOC_TYPE_KEYWORDS.items():
            if key in lower:
                return ClassificationResult(
                    doc_type=value,
                    confidence=CLASSIFIER_CONFIDENCE,
                    engine_version=ENGINE_VERSION,
                )
        return ClassificationResult(
            doc_type=DEFAULT_DOC_TYPE,
            confidence=CLASSIFIER_CONFIDENCE,
            engine_version=ENGINE_VERSION,
        )


class FakeOcrService:
    """Single-page placeholder OCR that mentions the document it was given."""

    engine_version: str = ENGINE_VERSION

    def extract(self, path: str, languages: list[str]) -> OcrResult:
        name = Path(path).name or str(path)
        text = (
            f"Mock OCR of {name}: scanned property document in Marathi, "
            "survey number 124/A, Pune, Maharashtra."
        )
        return OcrResult(
            pages=[OcrPage(page_number=1, text=text, confidence=MOCK_FIELD_CONFIDENCE)],
            language=MOCK_LANGUAGE,
            engine_version=ENGINE_VERSION,
        )


class FakeNLPExtractor:
    """Returns the hardcoded demo field values with confidence 0.87."""

    engine_version: str = ENGINE_VERSION

    def extract(self, doc_type: str, ocr_text: str) -> list[FieldCandidate]:
        return [
            FieldCandidate(
                field_name=field_name,
                raw_value=raw_value,
                value_type=value_type,
                confidence=MOCK_FIELD_CONFIDENCE,
            )
            for field_name, raw_value, value_type in MOCK_FIELDS
        ]


class FakeCrossValidator:
    """Cross-document consistency checks — port of ``_compare_documents``."""

    engine_version: str = ENGINE_VERSION

    def validate(self, extracted: dict[int, dict], document_meta: dict[int, dict]) -> list[FlagDraft]:
        findings: list[FlagDraft] = []
        extracted_values = list(extracted.values())
        if len(extracted_values) < 2:
            return findings

        survey_numbers = {v.get("survey_number") for v in extracted_values if v.get("survey_number")}
        if len(survey_numbers) > 1:
            findings.append(
                FlagDraft(
                    category="identity",
                    title="Survey number mismatch",
                    description="Extracted survey numbers differ across uploaded documents.",
                    severity="high",
                    confidence=0.82,
                    evidence=f"Values found: {', '.join(survey_numbers)}",
                    rule_ref="CONSISTENCY-SURVEY-001",
                )
            )

        areas = {v.get("area_sqft") for v in extracted_values if v.get("area_sqft")}
        if len(areas) > 1:
            findings.append(
                FlagDraft(
                    category="area",
                    title="Area discrepancy detected",
                    description="Document area values do not match.",
                    severity="medium",
                    confidence=0.75,
                    evidence=f"Areas (sqft): {', '.join(str(a) for a in areas)}",
                    rule_ref="CONSISTENCY-AREA-001",
                )
            )

        return findings


class FakeOwnershipGraphBuilder:
    """Two-node demo chain — port of ``_build_ownership_chain``."""

    engine_version: str = ENGINE_VERSION

    def build(self, document_meta: dict[int, dict]) -> list[OwnershipDraft]:
        document_ref = "Sale Deed"
        if document_meta:
            first_meta = next(iter(document_meta.values()))
            filename = first_meta.get("filename") if isinstance(first_meta, dict) else None
            if filename:
                document_ref = str(filename)

        return [
            OwnershipDraft(
                from_party=None,
                to_party="Suresh Deshmukh",
                transfer_type="sale",
                transfer_date="2015-06-10",
                document_ref="Predecessor Sale Deed (not uploaded)",
                sequence=1,
                gap_flag=True,
            ),
            OwnershipDraft(
                from_party="Suresh Deshmukh",
                to_party="Rajesh Patil",
                transfer_type="sale",
                transfer_date="2019-03-15",
                document_ref=document_ref,
                sequence=2,
                gap_flag=False,
            ),
        ]


class FakeRuleEngine:
    """Maharashtra demo rules — port of ``evaluate_rules``.

    The MH-CHAIN-001 flag is appended unconditionally and therefore always last.
    """

    engine_version: str = ENGINE_VERSION

    def evaluate(self, property_profile: dict, extracted: list[dict]) -> list[FlagDraft]:
        findings: list[FlagDraft] = []

        if not extracted:
            findings.append(
                FlagDraft(
                    category="missing-document",
                    title="No processed documents",
                    description="Upload and process property documents before due diligence.",
                    severity="medium",
                    confidence=1.0,
                    evidence="Zero completed document extractions",
                    rule_ref="MH-DOC-001",
                )
            )
            return findings

        doc_types = {v.get("doc_type") for v in extracted}
        if "7_12_extract" not in doc_types:
            findings.append(
                FlagDraft(
                    category="missing-document",
                    title="7/12 extract not found",
                    description="Maharashtra land due diligence typically requires a 7/12 extract.",
                    severity="high",
                    confidence=0.9,
                    evidence="No document classified as 7/12",
                    rule_ref="MH-LAND-712",
                )
            )

        if property_profile.get("state") == "Maharashtra" and not property_profile.get("survey_number"):
            findings.append(
                FlagDraft(
                    category="identity",
                    title="Survey/Gat number missing in property profile",
                    description="Property profile should include survey or Gat number for Maharashtra records.",
                    severity="medium",
                    confidence=0.85,
                    evidence="Property profile missing identifier",
                    rule_ref="MH-IDENT-001",
                )
            )

        findings.append(
            FlagDraft(
                category="ownership",
                title="Missing predecessor document reference",
                description="Ownership chain references a prior sale deed that was not uploaded.",
                severity="high",
                confidence=0.78,
                evidence="Predecessor Sale Deed (not uploaded)",
                rule_ref="MH-CHAIN-001",
            )
        )

        return findings


def mock_extracted_data(
    doc_type: str,
    language: str = MOCK_LANGUAGE,
    confidence: float = MOCK_FIELD_CONFIDENCE,
) -> dict:
    """The exact mock payload ``run_document_pipeline`` writes today (same key order).

    Kept here so the pipeline can rebuild the identical JSON blob from the
    fake NLP candidates without duplicating the constants.
    """
    data: dict = {"doc_type": doc_type}
    for field_name, raw_value, value_type in MOCK_FIELDS:
        data[field_name] = float(raw_value) if value_type == "number" else raw_value
    data["language"] = language
    data["confidence"] = confidence
    return data
