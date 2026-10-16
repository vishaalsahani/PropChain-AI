"""DEPRECATED (Phase 1): superseded by the registry-backed engine.

The live path is ``app.services.registry.get_rule_engine()`` (contract in
``app.services.interfaces``, demo implementation ``FakeRuleEngine`` in
``app.services.fakes``). This module is no longer imported by the app and is kept
only as a reference for the pre-Phase-1 behaviour it used to provide.
"""

from app.models import Finding, FindingSeverity, Property


def evaluate_rules(property_obj: Property, extracted_values: list[dict]) -> list[Finding]:
    """Miniature Maharashtra rule engine with a few demo rules."""
    findings: list[Finding] = []

    if not extracted_values:
        findings.append(
            Finding(
                property_id=property_obj.id,
                category="missing_document",
                title="No processed documents",
                description="Upload and process property documents before due diligence.",
                severity=FindingSeverity.medium,
                confidence=1.0,
                evidence="Zero completed document extractions",
                rule_ref="MH-DOC-001",
            )
        )
        return findings

    doc_types = {v.get("doc_type") for v in extracted_values}
    if "7_12_extract" not in doc_types:
        findings.append(
            Finding(
                property_id=property_obj.id,
                category="missing_document",
                title="7/12 extract not found",
                description="Maharashtra land due diligence typically requires a 7/12 extract.",
                severity=FindingSeverity.high,
                confidence=0.9,
                evidence="No document classified as 7/12",
                rule_ref="MH-LAND-712",
            )
        )

    if property_obj.state == "Maharashtra" and not property_obj.survey_number:
        findings.append(
            Finding(
                property_id=property_obj.id,
                category="identity",
                title="Survey/Gat number missing in property profile",
                description="Property profile should include survey or Gat number for Maharashtra records.",
                severity=FindingSeverity.medium,
                confidence=0.85,
                evidence="Property profile missing identifier",
                rule_ref="MH-IDENT-001",
            )
        )

    findings.append(
        Finding(
            property_id=property_obj.id,
            category="ownership",
            title="Missing predecessor document reference",
            description="Ownership chain references a prior sale deed that was not uploaded.",
            severity=FindingSeverity.high,
            confidence=0.78,
            evidence="Predecessor Sale Deed (not uploaded)",
            rule_ref="MH-CHAIN-001",
        )
    )

    return findings
