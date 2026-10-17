from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import client_ip, get_current_user
from app.models import AnalysisRun, Finding, OwnershipNode, Property, User
from app.schemas import AnalysisResult, FindingOut, OwnershipNodeOut, VerdictOut
from app.services.analysis_engine import run_property_analysis
from app.services.audit import record

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _latest_run(db: Session, property_id: int) -> AnalysisRun | None:
    return (
        db.query(AnalysisRun)
        .filter(AnalysisRun.property_id == property_id)
        .order_by(AnalysisRun.id.desc())
        .first()
    )


@router.post("/run/{property_id}", response_model=AnalysisResult)
def run_analysis(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = db.query(Property).filter(Property.id == property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    prop = run_property_analysis(db, prop)
    detail = {"risk_score": prop.risk_score} if prop.risk_score is not None else None
    record(
        db,
        "analysis.run_completed",
        "property",
        entity_id=property_id,
        actor_user_id=current_user.id,
        detail=detail,
        ip_address=client_ip(request),
    )
    db.commit()
    findings = db.query(Finding).filter(Finding.property_id == property_id).all()
    nodes = db.query(OwnershipNode).filter(OwnershipNode.property_id == property_id).order_by(OwnershipNode.sequence).all()
    run = _latest_run(db, property_id)
    verdict_reasons = (run.verdict_reasons if run else None) or {}

    return AnalysisResult(
        property_id=property_id,
        findings=[FindingOut.model_validate(f) for f in findings],
        ownership_chain=[OwnershipNodeOut.model_validate(n) for n in nodes],
        risk_score=prop.risk_score or 0,
        summary=f"Analysis completed with {len(findings)} findings and {len(nodes)} ownership nodes.",
        verdict=run.verdict.value if run and run.verdict else None,
        verdict_reasons=verdict_reasons or None,
    )


@router.get("/{property_id}/findings", response_model=list[FindingOut])
def get_findings(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prop = db.query(Property).filter(Property.id == property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return db.query(Finding).filter(Finding.property_id == property_id).all()


@router.get("/{property_id}/ownership", response_model=list[OwnershipNodeOut])
def get_ownership(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prop = db.query(Property).filter(Property.id == property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return db.query(OwnershipNode).filter(OwnershipNode.property_id == property_id).order_by(OwnershipNode.sequence).all()


@router.get("/{property_id}/verdict", response_model=VerdictOut)
def get_verdict(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Latest FR-8 verdict for the property (404 when no run exists yet)."""
    prop = db.query(Property).filter(Property.id == property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    run = _latest_run(db, property_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No analysis run for this property yet")

    reasons = run.verdict_reasons or {}
    return VerdictOut(
        property_id=property_id,
        analysis_run_id=run.id,
        verdict=run.verdict.value if run.verdict else None,
        reasons=list(reasons.get("reasons") or []),
        not_checked=list(reasons.get("not_checked") or []),
        risk_score=run.risk_score,
        engine_version=run.engine_version,
    )
