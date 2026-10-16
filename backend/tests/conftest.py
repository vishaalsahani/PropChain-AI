"""Shared pytest fixtures for the PropChain-AI backend suite.

Bootstrap order matters and mirrors a real deployment:

1. allocate a temp directory for the test module;
2. point the app at it with environment variables *before anything imports app*
   (``DATABASE_URL``, ``STORAGE_PATH``, ``BLOCKCHAIN_MOCK_MODE``, ``SECRET_KEY``);
3. run ``alembic upgrade head`` programmatically against that same temp DB;
4. only then import ``app.main`` — it calls ``Base.metadata.create_all`` at
   import time, so migrations must create the schema first (``create_all`` is a
   check-first no-op for tables alembic already created).

Each test module that requests the fixtures gets its own temp DB and storage
directory, so modules can not leak state into each other.
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

from .support import purge_app_modules, run_alembic_upgrade, sqlite_url

TEST_SECRET_KEY = "test-secret"


@pytest.fixture(scope="module")
def app_env(tmp_path_factory):
    """Boot a fresh app instance against a module-private temp DB + storage dir.

    Returns a dict with the ``TestClient``, the live ``FastAPI`` app, the temp
    storage directory used for file assertions, and the temp DB path.
    """
    tmp_dir = tmp_path_factory.mktemp("propchain_test")
    db_path = tmp_dir / "test.db"
    storage_path = tmp_dir / "storage"
    storage_path.mkdir(parents=True, exist_ok=True)

    # 1. environment first — app.config reads these at import time.
    purge_app_modules()
    os.environ["DATABASE_URL"] = sqlite_url(db_path)
    os.environ["STORAGE_PATH"] = storage_path.as_posix()
    os.environ["BLOCKCHAIN_MOCK_MODE"] = "true"
    os.environ["SECRET_KEY"] = TEST_SECRET_KEY

    # 2. schema via migrations, before app.main gets imported (it would otherwise
    #    create tables itself with create_all and hide migration breakage).
    run_alembic_upgrade(db_path)

    # 3. import the app and wrap it in an in-process TestClient.
    app_main = importlib.import_module("app.main")
    from fastapi.testclient import TestClient

    resolved_storage = Path(app_main.settings.storage_path)
    assert resolved_storage == storage_path, (
        f"STORAGE_PATH not honoured by app settings: {resolved_storage} != {storage_path}"
    )

    yield {
        "client": TestClient(app_main.app),
        "app": app_main.app,
        "storage": resolved_storage,
        "db_path": db_path,
        "tmp_dir": tmp_dir,
    }


@pytest.fixture(scope="module")
def app_client(app_env):
    """``fastapi.testclient.TestClient`` bound to the module's temp DB."""
    return app_env["client"]


@pytest.fixture(scope="module")
def storage_path(app_env):
    """Temp storage directory the app writes uploads into (for file assertions)."""
    return app_env["storage"]
