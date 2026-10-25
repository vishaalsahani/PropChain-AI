"""Provision the demo reviewer/admin accounts (Phase 4 and Phase 6).

Public registration can only create buyers and owners. This script is the
operator path for the privileged demo accounts:

    python scripts/seed_demo_roles.py
    python scripts/seed_demo_roles.py --reset-passwords

Existing accounts keep their password unless ``--reset-passwords`` is passed.
Run from ``backend/`` with the backend virtualenv active.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Allow ``python scripts/seed_demo_roles.py`` from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models import User, UserRole  # noqa: E402
from app.utils.security import hash_password  # noqa: E402

DEMO_USERS = (
    ("reviewer@propchainai.com", "Demo Reviewer", "review1234", UserRole.reviewer),
    ("admin@propchainai.com", "Demo Admin", "admin1234", UserRole.admin),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the PropChain-AI demo roles")
    parser.add_argument(
        "--reset-passwords",
        action="store_true",
        help="reset existing accounts to the documented demo passwords",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        for email, full_name, password, role in DEMO_USERS:
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                user = User(
                    email=email,
                    full_name=full_name,
                    hashed_password=hash_password(password),
                    role=role,
                )
                db.add(user)
                print(f"created {email} ({role.value})")
            else:
                user.role = role
                user.full_name = full_name
                user.is_active = True
                if args.reset_passwords:
                    user.hashed_password = hash_password(password)
                db.add(user)
                print(f"updated {email} ({role.value})")
        db.commit()
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
