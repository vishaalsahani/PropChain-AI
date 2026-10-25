"""Read-access helpers for the Phase 6 reviewer workflow.

Owners see their own files. Reviewers and admins see every file so a queue can
be worked without impersonating the owner. This helper is deliberately read
only; uploads and analysis runs remain owner actions.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Property, User, UserRole

REVIEW_ROLES = frozenset({UserRole.reviewer, UserRole.admin})


def is_reviewer(user: User) -> bool:
    return user.role in REVIEW_ROLES


def property_for_read(db: Session, user: User, property_id: int) -> Property:
    """Return a property the user may read, or raise 404 (not 403).

    Using 404 for another owner's property preserves the pre-Phase-6 privacy
    behaviour: the API does not reveal that an inaccessible id exists.
    """
    query = db.query(Property).filter(Property.id == property_id)
    if not is_reviewer(user):
        query = query.filter(Property.owner_id == user.id)
    prop = query.first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop
