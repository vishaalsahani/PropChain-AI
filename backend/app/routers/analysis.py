from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import client_ip, get_current_user
from app.models import AnalysisRun, Finding, OwnershipNode, Property, User
from app.schemas import AnalysisResult, AnalysisRunOut, FindingOut, OwnershipNodeOut, VerdictOut
from app.services.access import property_for_read
from app.services.analysis_engine import run_property_analysis
from app.services.audit import record
from app.services.review import latest_run, run_out

router = APIRouter(prefix="/analysis", tags=["analysis"])


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
    run = latest_run(db, property_id)
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
    verdict_reasons = (run.verdict_reasons if run else None) or {}

    return AnalysisResult(
        property_id=property_id,
        findings=[FindingOut.model_validate(f) for f in findings],
        ownership_chain=[OwnershipNodeOut.model_validate(n) for n in nodes],
        risk_score=prop.risk_score or 0,
        summary=(run.summary if run and run.summary else
                 f"Analysis completed with {len(findings)} "
                 f"finding{'s' if len(findings) != 1 else ''} and {len(nodes)} "
                 f"ownership node{'s' if len(nodes) != 1 else ''}."),
        verdict=run.verdict.value if run and run.verdict else None,
        verdict_reasons=verdict_reasons or None,
    )


@router.get("/{property_id}/findings", response_model=list[FindingOut])
def get_findings(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    property_for_read(db, current_user, property_id)
    run = latest_run(db, property_id)
    if run is None:
        return []
    return (
        db.query(Finding)
        .filter(Finding.property_id == property_id, Finding.analysis_run_id == run.id)
        .all()
    )


@router.get("/{property_id}/ownership", response_model=list[OwnershipNodeOut])
def get_ownership(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    property_for_read(db, current_user, property_id)
    run = latest_run(db, property_id)
    if run is None:
        return []
    return (
        db.query(OwnershipNode)
        .filter(
            OwnershipNode.property_id == property_id,
            OwnershipNode.analysis_run_id == run.id,
        )
        .order_by(OwnershipNode.sequence)
        .all()
    )


@router.get("/{property_id}/runs", response_model=list[AnalysisRunOut])
def list_runs(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Immutable run history, newest first (Phase 6)."""
    property_for_read(db, current_user, property_id)
    runs = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.property_id == property_id)
        .order_by(AnalysisRun.id.desc())
        .all()
    )
    return [run_out(db, run) for run in runs]


@router.get("/{property_id}/verdict", response_model=VerdictOut)
def get_verdict(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Latest FR-8 verdict for the property (404 when no run exists yet)."""
    property_for_read(db, current_user, property_id)

    run = latest_run(db, property_id)
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
        review_status=run.review_status or "pending",
        review_verdict=run.review_verdict,
        review_note=run.review_note,
        reviewed_at=run.reviewed_at,
    )
