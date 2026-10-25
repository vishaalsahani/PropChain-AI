"""Public read-only rule catalogue (Phase 4).

The full catalogue is available for transparency: a reviewer can see the
screening rule, its legal reference, severity and the exact condition that
would trigger it. Editing lives under ``/admin/rule-packs`` and is admin-only.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LegalRule
from app.schemas import RulePackOut, RulePackSummaryOut
from app.services.rule_store import list_pack_summaries, pack_detail

router = APIRouter(prefix="/rule-packs", tags=["rule-packs"])


@router.get("", response_model=list[RulePackSummaryOut])
def list_rule_packs(db: Session = Depends(get_db)):
    return list_pack_summaries(db, include_inactive=False)


@router.get("/{jurisdiction}", response_model=RulePackOut)
def get_rule_pack(jurisdiction: str, db: Session = Depends(get_db)):
    exists = (
        db.query(LegalRule)
        .filter(LegalRule.jurisdiction == jurisdiction, LegalRule.is_active.is_(True))
        .first()
    )
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active rule pack for {jurisdiction}",
        )
    return pack_detail(db, jurisdiction, include_inactive=False)
