import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Document, DocumentStatus, Finding, FindingSeverity, OwnershipNode, Property
from app.services.rule_engine import evaluate_rules


def run_document_pipeline(db: Session, document: Document) -> Document:
    """Miniature OCR/NLP pipeline — returns mock extracted data for demo."""
    document.status = DocumentStatus.processing
    db.commit()

    mock_data = {
        "doc_type": _guess_doc_type(document.filename),
        "owner_name": "Rajesh Patil",
        "seller_name": "Suresh Deshmukh",
        "buyer_name": "Rajesh Patil",
        "survey_number": "124/A",
        "gat_number": "456",
        "area_sqft": 1200.0,
        "registration_date": "2019-03-15",
        "registration_number": "MH-PUN-2019-12345",
        "language": "marathi",
        "confidence": 0.87,
    }

    document.doc_type = mock_data["doc_type"]
    document.extracted_data = json.dumps(mock_data)
    document.status = DocumentStatus.completed
    db.commit()
    db.refresh(document)
    return document


def run_property_analysis(db: Session, property_obj: Property) -> Property:
    """Cross-document comparison, ownership graph, and rule evaluation."""
    documents = (
        db.query(Document)
        .filter(Document.property_id == property_obj.id, Document.status == DocumentStatus.completed)
        .all()
    )

    db.query(Finding).filter(Finding.property_id == property_obj.id).delete()
    db.query(OwnershipNode).filter(OwnershipNode.property_id == property_obj.id).delete()

    extracted_values = []
    for doc in documents:
        if doc.extracted_data:
            extracted_values.append(json.loads(doc.extracted_data))

    findings = _compare_documents(property_obj, extracted_values)
    for finding in findings:
        db.add(finding)

    rule_findings = evaluate_rules(property_obj, extracted_values)
    for finding in rule_findings:
        db.add(finding)

    ownership_nodes = _build_ownership_chain(property_obj, documents)
    for node in ownership_nodes:
        db.add(node)

    severity_weights = {"low": 1, "medium": 3, "high": 6, "critical": 10}
    all_findings = findings + rule_findings
    if all_findings:
        total = sum(severity_weights.get(f.severity.value, 1) for f in all_findings)
        property_obj.risk_score = min(100.0, total * 5)
    else:
        property_obj.risk_score = 10.0

    property_obj.status = "analyzed"
    db.commit()
    db.refresh(property_obj)
    return property_obj


def _guess_doc_type(filename: str) -> str:
    lower = filename.lower()
    mapping = {
        "sale": "sale_deed",
        "712": "7_12_extract",
        "7_12": "7_12_extract",
        "8a": "8a_record",
        "ferfar": "ferfar",
        "property": "property_card",
        "gift": "gift_deed",
        "mortgage": "mortgage_deed",
    }
    for key, value in mapping.items():
        if key in lower:
            return value
    return "sale_deed"


def _compare_documents(property_obj: Property, extracted_values: list[dict]) -> list[Finding]:
    findings: list[Finding] = []
    if len(extracted_values) < 2:
        return findings

    survey_numbers = {v.get("survey_number") for v in extracted_values if v.get("survey_number")}
    if len(survey_numbers) > 1:
        findings.append(
            Finding(
                property_id=property_obj.id,
                category="identifier",
                title="Survey number mismatch",
                description="Extracted survey numbers differ across uploaded documents.",
                severity=FindingSeverity.high,
                confidence=0.82,
                evidence=f"Values found: {', '.join(survey_numbers)}",
                rule_ref="CONSISTENCY-SURVEY-001",
            )
        )

    areas = {v.get("area_sqft") for v in extracted_values if v.get("area_sqft")}
    if len(areas) > 1:
        findings.append(
            Finding(
                property_id=property_obj.id,
                category="area",
                title="Area discrepancy detected",
                description="Document area values do not match.",
                severity=FindingSeverity.medium,
                confidence=0.75,
                evidence=f"Areas (sqft): {', '.join(str(a) for a in areas)}",
                rule_ref="CONSISTENCY-AREA-001",
            )
        )

    return findings


def _build_ownership_chain(property_obj: Property, documents: list[Document]) -> list[OwnershipNode]:
    nodes = [
        OwnershipNode(
            property_id=property_obj.id,
            person_name="Suresh Deshmukh",
            transaction_type="sale",
            transaction_date="2015-06-10",
            document_ref="Predecessor Sale Deed (not uploaded)",
            sequence=1,
        ),
        OwnershipNode(
            property_id=property_obj.id,
            person_name="Rajesh Patil",
            transaction_type="sale",
            transaction_date="2019-03-15",
            document_ref=documents[0].filename if documents else "Sale Deed",
            sequence=2,
        ),
    ]

    if not any("Predecessor" in (n.document_ref or "") for n in nodes):
        return nodes

    return nodes
