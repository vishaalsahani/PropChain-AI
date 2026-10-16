from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Document, Finding, OwnershipNode, Property, User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{property_id}/pdf")
def download_report(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prop = db.query(Property).filter(Property.id == property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    findings = db.query(Finding).filter(Finding.property_id == property_id).all()
    nodes = db.query(OwnershipNode).filter(OwnershipNode.property_id == property_id).order_by(OwnershipNode.sequence).all()
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

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=propchain-report-{property_id}.pdf"},
    )
