"""Audit-trail service (Phase 1, task B6).

A single writer for the ``AuditEvent`` table so every router records access the
same way. ``record`` only stages the event on the caller's session -- the caller
owns the transaction, which is what keeps the audit row atomic with the state
change it describes (same ``db``, one commit).

Actions currently in use (keep this list in sync with the routers):

``user.registered``, ``user.login``, ``user.login_failed``, ``property.created``,
``document.uploaded``, ``analysis.run_completed``, ``blockchain.registered``,
``report.generated``, ``rule.created``, ``rule.updated``, ``rule.rolled_back``,
``rule.pack_reset``.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditEvent


def record(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    actor_user_id: int | None = None,
    detail: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditEvent:
    """Stage an ``AuditEvent`` on ``db`` and return it; the caller commits."""
    event = AuditEvent(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(event)
    return event


def list_events(db: Session, limit: int = 50, offset: int = 0) -> list[AuditEvent]:
    """Audit events, newest first (``created_at`` then ``id``, both descending)."""
    return (
        db.query(AuditEvent)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
