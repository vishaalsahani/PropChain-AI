"""Reviewer workflow endpoints (Phase 6).

Reviewers and admins can see every property, disposition individual findings
and record a final decision on the latest analysis run. Findings and run rows
are append-only across re-analysis; this router only flips reviewer state and
writes an audit event in the same transaction.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import client_ip, require_role
from app.models import (
    AnalysisRun,
    AnalysisRunStatus,
    Finding,
    Property,
    PropertyStatus,
    RiskFlag,
    User,
    UserRole,
)
from app.schemas import (
    AnalysisRunOut,
    FindingOut,
    FindingReviewRequest,
    ReviewQueueItemOut,
    RunReviewRequest,
)
from app.services.access import property_for_read
from app.services.audit import record
from app.services.review import latest_run, run_out

router = APIRouter(prefix="/review", tags=["review"])

FINAL_PROPERTY_STATUS = {
    "verified": PropertyStatus.analyzed,
    "needs_review": PropertyStatus.needs_review,
    "flagged": PropertyStatus.flagged,
}


@router.get("/queue", response_model=list[ReviewQueueItemOut])
def review_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.reviewer, UserRole.admin)),
):
    """Latest completed run per property, with open-finding counts."""
    latest_ids = (
        db.query(
            AnalysisRun.property_id.label("property_id"),
            func.max(AnalysisRun.id).label("run_id"),
        )
        .filter(
            AnalysisRun.status == AnalysisRunStatus.completed,
            AnalysisRun.verdict.isnot(None),
        )
        .group_by(AnalysisRun.property_id)
        .subquery()
    )
    rows = (
        db.query(AnalysisRun, Property)
        .join(Property, Property.id == AnalysisRun.property_id)
        .join(latest_ids, latest_ids.c.run_id == AnalysisRun.id)
        .all()
    )

    total_counts = dict(
        db.query(RiskFlag.analysis_run_id, func.count(RiskFlag.id))
        .group_by(RiskFlag.analysis_run_id)
        .all()
    )
    open_counts = dict(
        db.query(RiskFlag.analysis_run_id, func.count(RiskFlag.id))
        .filter(RiskFlag.status.in_(["open", "needs_evidence"]))
        .group_by(RiskFlag.analysis_run_id)
        .all()
    )

    items = []
    for run, prop in rows:
        items.append(
            ReviewQueueItemOut(
                property_id=prop.id,
                title=prop.title,
                village=prop.village,
                district=prop.district,
                run_id=run.id,
                verdict=run.verdict.value if run.verdict else None,
                risk_score=run.risk_score,
                review_status=run.review_status or "pending",
                review_verdict=run.review_verdict,
                open_findings=open_counts.get(run.id, 0),
                total_findings=total_counts.get(run.id, 0),
                finished_at=run.finished_at,
            )
        )

    verdict_priority = {"flagged": 0, "needs_review": 1, "verified": 2, None: 3}
    items.sort(
        key=lambda item: (
            1 if item.review_status in {"confirmed", "overridden"} else 0,
            verdict_priority.get(item.verdict, 3),
            -item.run_id,
        )
    )
    return items


@router.patch("/findings/{finding_id}", response_model=FindingOut)
def review_finding(
    finding_id: int,
    payload: FindingReviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.reviewer, UserRole.admin)),
):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    property_for_read(db, current_user, finding.property_id)

    newest = latest_run(db, finding.property_id)
    if newest is None or newest.id != finding.analysis_run_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A newer analysis run exists. Review findings from the latest run instead.",
        )

    if payload.expected_status and payload.expected_status != finding.status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Finding status changed (expected {payload.expected_status}, "
                f"found {finding.status}). Reload before saving."
            ),
        )

    previous = finding.status
    finding.status = payload.status
    finding.reviewed_by = current_user.id
    finding.reviewed_at = datetime.now(timezone.utc)
    finding.review_note = (payload.note or "").strip() or None

    record(
        db,
        "finding.reviewed",
        "risk_flag",
        entity_id=finding.id,
        actor_user_id=current_user.id,
        detail={
            "property_id": finding.property_id,
            "run_id": finding.analysis_run_id,
            "from": previous,
            "to": finding.status,
            "note": finding.review_note,
        },
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(finding)
    return finding


@router.post("/runs/{run_id}/decision", response_model=AnalysisRunOut)
def decide_run(
    run_id: int,
    payload: RunReviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.reviewer, UserRole.admin)),
):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis run not found")
    prop = property_for_read(db, current_user, run.property_id)

    if run.status != AnalysisRunStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a completed run can be reviewed.",
        )
    newest = latest_run(db, run.property_id)
    if newest is None or newest.id != run.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A newer analysis run exists. Review the latest run instead.",
        )

    if payload.decision == "overridden":
        final_verdict = payload.verdict
    else:
        final_verdict = run.verdict.value if run.verdict else None
    if final_verdict is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The run has no system verdict to confirm.",
        )

    run.review_status = payload.decision
    run.review_verdict = final_verdict
    run.reviewed_by = current_user.id
    run.reviewed_at = datetime.now(timezone.utc)
    run.review_note = payload.note.strip()

    prop.status = FINAL_PROPERTY_STATUS.get(final_verdict, prop.status)
    record(
        db,
        "analysis.reviewed",
        "analysis_run",
        entity_id=run.id,
        actor_user_id=current_user.id,
        detail={
            "property_id": run.property_id,
            "system_verdict": run.verdict.value if run.verdict else None,
            "decision": payload.decision,
            "final_verdict": final_verdict,
            "note": run.review_note,
        },
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(run)
    return run_out(db, run)
