from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Property, User
from app.schemas import PropertyCreate, PropertyOut

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("", response_model=PropertyOut)
def create_property(
    payload: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = Property(owner_id=current_user.id, **payload.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


@router.get("", response_model=list[PropertyOut])
def list_properties(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Property).filter(Property.owner_id == current_user.id).order_by(Property.created_at.desc()).all()


@router.get("/{property_id}", response_model=PropertyOut)
def get_property(property_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prop = db.query(Property).filter(Property.id == property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop
