from io import BytesIO

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import client_ip, get_current_user
from app.models import AnalysisRun, Document, Finding, OwnershipNode, User
from app.services.access import property_for_read
from app.services.audit import record

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{property_id}/pdf")
def download_report(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = property_for_read(db, current_user, property_id)
    run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.property_id == property_id)
        .order_by(AnalysisRun.id.desc())
        .first()
    )
    findings = (
        db.query(Finding)
        .filter(Finding.property_id == property_id, Finding.analysis_run_id == (run.id if run else -1))
        .all()
    )
    nodes = (
        db.query(OwnershipNode)
        .filter(
            OwnershipNode.property_id == property_id,
            OwnershipNode.analysis_run_id == (run.id if run else -1),
        )
        .order_by(OwnershipNode.sequence)
        .all()
    )
    documents = db.query(Document).filter(Document.property_id == property_id).all()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    def line(text: str, gap: int = 16):
        nonlocal y
        pdf.drawString(50, y, text[:100])
        y -= gap
        if y < 60:
            pdf.showPage()
            y = height - 50

    line("PropChain-AI Due Diligence Report", 24)
    line(f"Property: {prop.title}")
    line(f"Location: {prop.village}, {prop.taluka}, {prop.district}, {prop.state}")
    line(f"Survey/Gat/CTS: {prop.survey_number} / {prop.gat_number} / {prop.cts_number}")
    line(f"Risk Score: {prop.risk_score or 'N/A'}")
    if run:
        line(f"Analysis Run: {run.id} ({run.engine_version})")
        line(f"System Verdict: {(run.verdict.value if run.verdict else 'N/A').replace('_', ' ')}")
        review = run.review_verdict or (run.verdict.value if run.verdict else None) or "N/A"
        line(f"Review Status: {run.review_status or 'pending'} ({review.replace('_', ' ')})")
        if run.review_note:
            line(f"Reviewer Note: {run.review_note}")
    line("")
    line("Documents Analyzed:")
    for doc in documents:
        line(f"- {doc.filename} ({doc.doc_type})")
    line("")
    line("Ownership Chain:")
    for node in nodes:
        line(f"- {node.sequence}. {node.person_name} ({node.transaction_type}, {node.transaction_date})")
    line("")
    line("Findings:")
    for finding in findings:
        line(f"- [{finding.severity.value.upper()}] {finding.title}")
    line("")
    line("Disclaimer: This report is AI-assisted documentary analysis only.")
    line("It does not establish legal title or replace professional advice.")
    pdf.save()
    buffer.seek(0)

    record(
        db,
        "report.generated",
        "property",
        entity_id=property_id,
        actor_user_id=current_user.id,
        ip_address=client_ip(request),
    )
    db.commit()

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=propchain-report-{property_id}.pdf"},
    )
