from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Finding, OwnershipNode, Property, User
from app.schemas import AnalysisResult, FindingOut, OwnershipNodeOut
from app.services.analysis_engine import run_property_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run/{property_id}", response_model=AnalysisResult)
def run_analysis(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prop = db.query(Property).filter(Property.id == property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    prop = run_property_analysis(db, prop)
    findings = db.query(Finding).filter(Finding.property_id == property_id).all()
    nodes = db.query(OwnershipNode).filter(OwnershipNode.property_id == property_id).order_by(OwnershipNode.sequence).all()

    return AnalysisResult(
        property_id=property_id,
        findings=[FindingOut.model_validate(f) for f in findings],
        ownership_chain=[OwnershipNodeOut.model_validate(n) for n in nodes],
        risk_score=prop.risk_score or 0,
        summary=f"Analysis completed with {len(findings)} findings and {len(nodes)} ownership nodes.",
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
