"""Admin-only endpoints (Phase 1, task B5/B6).

``GET /admin/audit-events`` is the read side of the audit trail written by
``app.services.audit``. Responses are plain dicts on purpose: the audit row is a
flat, append-only record and a schema for it would only add a second place to
keep in sync.

Mounting: the app registers this router in ``app/main.py`` (see the main agent).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import AuditEvent, User, UserRole
from app.services.audit import list_events

router = APIRouter(prefix="/admin", tags=["admin"])


def _serialize(event: AuditEvent) -> dict:
    return {
        "id": event.id,
        "action": event.action,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "actor_user_id": event.actor_user_id,
        "detail": event.detail,
        "ip_address": event.ip_address,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


@router.get("/audit-events")
def list_audit_events(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """Newest-first audit trail. Admins only."""
    return [_serialize(event) for event in list_events(db, limit=limit, offset=offset)]
