"""Admin-only rule-catalogue endpoints (Phase 4).

Read endpoints expose the full catalogue including inactive rules and the
append-only version history. Write endpoints create a new snapshot on every
change and write an ``AuditEvent`` in the same transaction.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import client_ip, require_role
from app.models import LegalRule, User, UserRole
from app.schemas import (
    RuleCreate,
    RuleDetailOut,
    RuleOut,
    RulePackOut,
    RulePackSummaryOut,
    RuleResetRequest,
    RuleRollbackRequest,
    RuleUpdate,
)
from app.services.audit import record
from app.services.rule_store import (
    RuleConflict,
    RuleNotFound,
    create_rule,
    get_rule,
    list_pack_summaries,
    list_rules,
    list_versions,
    pack_detail,
    reset_pack,
    rollback_rule,
    serialize_rule,
    serialize_version,
    update_rule,
)

router = APIRouter(prefix="/admin/rule-packs", tags=["admin"])


def _detail(db: Session, rule: LegalRule) -> dict:
    payload = serialize_rule(rule)
    payload["versions"] = [serialize_version(version) for version in list_versions(db, rule)]
    return payload


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("", response_model=list[RulePackSummaryOut])
def list_rule_packs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    return list_pack_summaries(db, include_inactive=True)


@router.get("/{jurisdiction}", response_model=RulePackOut)
def get_rule_pack(
    jurisdiction: str,
    include_inactive: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    exists = db.query(LegalRule).filter(LegalRule.jurisdiction == jurisdiction).first()
    if not exists:
        raise _not_found(f"No rule pack for {jurisdiction}")
    return pack_detail(db, jurisdiction, include_inactive=include_inactive)


@router.get("/{jurisdiction}/rules/{rule_code}", response_model=RuleDetailOut)
def get_rule_detail(
    jurisdiction: str,
    rule_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    try:
        rule = get_rule(db, jurisdiction, rule_code)
    except RuleNotFound as exc:
        raise _not_found(str(exc)) from exc
    return _detail(db, rule)


@router.post(
    "/{jurisdiction}/rules",
    response_model=RuleOut,
    status_code=status.HTTP_201_CREATED,
)
def create_rule_endpoint(
    jurisdiction: str,
    payload: RuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    values = payload.model_dump()
    change_note = values.pop("change_note")
    try:
        rule = create_rule(
            db,
            jurisdiction,
            values,
            actor_user_id=current_user.id,
            change_note=change_note,
        )
    except RuleConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    record(
        db,
        "rule.created",
        "legal_rule",
        entity_id=rule.id,
        actor_user_id=current_user.id,
        detail={"rule_code": rule.rule_code, "jurisdiction": jurisdiction},
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(rule)
    return serialize_rule(rule)


@router.patch("/{jurisdiction}/rules/{rule_code}", response_model=RuleDetailOut)
def update_rule_endpoint(
    jurisdiction: str,
    rule_code: str,
    payload: RuleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    try:
        rule = get_rule(db, jurisdiction, rule_code)
    except RuleNotFound as exc:
        raise _not_found(str(exc)) from exc

    values = payload.model_dump(exclude_unset=True)
    change_note = values.pop("change_note", None)
    expected_version = values.pop("expected_version", None)
    try:
        rule = update_rule(
            db,
            rule,
            values,
            actor_user_id=current_user.id,
            change_note=change_note,
            expected_version=expected_version,
        )
    except RuleConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    record(
        db,
        "rule.updated",
        "legal_rule",
        entity_id=rule.id,
        actor_user_id=current_user.id,
        detail={
            "rule_code": rule.rule_code,
            "jurisdiction": jurisdiction,
            "version": rule.current_version,
            "fields": sorted(values),
        },
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(rule)
    return _detail(db, rule)


@router.post(
    "/{jurisdiction}/rules/{rule_code}/rollback",
    response_model=RuleDetailOut,
)
def rollback_rule_endpoint(
    jurisdiction: str,
    rule_code: str,
    payload: RuleRollbackRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    try:
        rule = get_rule(db, jurisdiction, rule_code)
        rule = rollback_rule(
            db,
            rule,
            payload.version,
            actor_user_id=current_user.id,
            change_note=payload.change_note,
        )
    except RuleNotFound as exc:
        raise _not_found(str(exc)) from exc
    except RuleConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    record(
        db,
        "rule.rolled_back",
        "legal_rule",
        entity_id=rule.id,
        actor_user_id=current_user.id,
        detail={
            "rule_code": rule.rule_code,
            "jurisdiction": jurisdiction,
            "restored_from": payload.version,
            "new_version": rule.current_version,
        },
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(rule)
    return _detail(db, rule)


@router.post("/{jurisdiction}/reset", response_model=RulePackOut)
def reset_rule_pack(
    jurisdiction: str,
    payload: RuleResetRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    try:
        reset_pack(
            db,
            jurisdiction,
            actor_user_id=current_user.id,
            change_note=payload.change_note,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except RuleConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    record(
        db,
        "rule.pack_reset",
        "rule_pack",
        entity_id=None,
        actor_user_id=current_user.id,
        detail={"jurisdiction": jurisdiction, "pack": "mh-v1"},
        ip_address=client_ip(request),
    )
    db.commit()
    return pack_detail(db, jurisdiction, include_inactive=True)
