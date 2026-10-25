"""Shared serialization for analysis-run history and reviewer state (Phase 6)."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import AnalysisRun, RiskFlag
from app.schemas import AnalysisRunOut


def latest_run(db: Session, property_id: int) -> AnalysisRun | None:
    return (
        db.query(AnalysisRun)
        .filter(AnalysisRun.property_id == property_id)
        .order_by(AnalysisRun.id.desc())
        .first()
    )


def run_out(db: Session, run: AnalysisRun) -> AnalysisRunOut:
    finding_count = (
        db.query(func.count(RiskFlag.id)).filter(RiskFlag.analysis_run_id == run.id).scalar() or 0
    )
    return AnalysisRunOut(
        id=run.id,
        property_id=run.property_id,
        status=run.status.value if hasattr(run.status, "value") else str(run.status),
        engine_version=run.engine_version,
        verdict=run.verdict.value if run.verdict else None,
        risk_score=run.risk_score,
        summary=run.summary,
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_by=run.created_by,
        review_status=run.review_status or "pending",
        review_verdict=run.review_verdict,
        reviewed_by=run.reviewed_by,
        reviewed_at=run.reviewed_at,
        review_note=run.review_note,
        finding_count=finding_count,
    )
