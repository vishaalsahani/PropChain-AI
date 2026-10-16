"""Small helpers shared by the test suite (no app import at module level).

Everything here is deliberately import-safe: importing this module must not pull
in ``app.*``, because the app reads ``DATABASE_URL``/``STORAGE_PATH`` at import
time and tests need those env vars set *first*.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# backend/  — needed so `import app` works no matter which directory pytest was
# launched from (alembic/env.py also imports app.*, so this must be in place
# before any migration runs).
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

ALEMBIC_INI = BACKEND_DIR / "alembic.ini"
ALEMBIC_DIR = BACKEND_DIR / "alembic"


def sqlite_url(db_path: Path) -> str:
    """Build a ``sqlite:///`` URL using forward slashes (Windows-safe)."""
    return f"sqlite:///{Path(db_path).as_posix()}"


def purge_app_modules() -> None:
    """Forget cached ``app.*`` modules so freshly set env vars are re-read.

    ``app.config`` builds its ``Settings`` object at import time, so a module
    cached by an earlier alembic run (or an earlier test module) would keep the
    old database URL/storage path. Purging before each (re)bootstraps makes every
    test module independent.
    """
    for name in [module for module in sys.modules if module == "app" or module.startswith("app.")]:
        del sys.modules[name]


def alembic_config(db_path: Path):
    """Alembic ``Config`` for ``db_path``, with app modules purged first.

    ``alembic/env.py`` resolves the database URL from app settings (env var), so
    we set both the env var and the ini option to keep any env.py variant happy.
    Purging makes env.py import a *fresh* ``app.config.Settings`` pointed at
    ``db_path`` instead of reusing a cached instance from an earlier run.
    """
    from alembic.config import Config

    url = sqlite_url(db_path)
    purge_app_modules()
    os.environ["DATABASE_URL"] = url

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_DIR))
    config.set_main_option("sqlalchemy.url", url)
    return config


def run_alembic_upgrade(db_path: Path, revision: str = "head") -> None:
    """Run ``alembic upgrade <revision>`` against ``db_path`` in-process."""
    from alembic import command

    command.upgrade(alembic_config(db_path), revision)


def run_alembic_downgrade(db_path: Path, revision: str = "base") -> None:
    """Run ``alembic downgrade <revision>`` against ``db_path`` in-process."""
    from alembic import command

    command.downgrade(alembic_config(db_path), revision)
