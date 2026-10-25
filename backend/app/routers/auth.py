from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import client_ip, get_current_user
from app.models import User, UserRole
from app.schemas import Token, UserCreate, UserOut
from app.services.audit import record
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user; the UI uses the role to gate edit controls."""
    return current_user

# Public self-registration may only mint these roles. ``reviewer``/``admin`` are
# provisioned by an administrator, so POST /auth/register can not escalate.
SELF_REGISTER_ROLES = frozenset({UserRole.buyer, UserRole.owner})


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)):
    if payload.role not in SELF_REGISTER_ROLES:
        allowed = ", ".join(sorted(role.value for role in SELF_REGISTER_ROLES))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Role '{payload.role.value}' can not be self-registered. Allowed roles: {allowed}.",
        )

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()  # assigns user.id so the audit row references it in the same commit
    record(
        db,
        "user.registered",
        "user",
        entity_id=user.id,
        actor_user_id=user.id,
        detail={"email": user.email, "role": user.role.value},
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Audited internally only: the HTTP response is identical whether or not
        # the account exists, so the trail can not be used to enumerate users.
        record(
            db,
            "user.login_failed",
            "user",
            detail={"email": form_data.username},
            ip_address=client_ip(request),
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    record(
        db,
        "user.login",
        "user",
        entity_id=user.id,
        actor_user_id=user.id,
        ip_address=client_ip(request),
    )
    db.commit()
    return Token(access_token=create_access_token(user.email))
