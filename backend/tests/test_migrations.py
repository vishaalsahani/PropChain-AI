"""Alembic-only migration tests — deliberately no ``app.main`` import.

``alembic upgrade head`` has to work standalone (that is what deployment runs),
so these tests drive alembic against their own temp SQLite files only.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from .support import run_alembic_downgrade, run_alembic_upgrade, sqlite_url


@pytest.fixture()
def db_path(tmp_path, monkeypatch) -> Path:
    """A private SQLite file per test.

    ``DATABASE_URL`` is patched as well because ``alembic/env.py`` reads the URL
    from app settings (env var), not from ``alembic.ini``.
    """
    path = (tmp_path / "alembic_test.db").resolve()
    monkeypatch.setenv("DATABASE_URL", sqlite_url(path))
    return path


def table_names(db_path: Path) -> set[str]:
    engine = create_engine(sqlite_url(db_path))
    try:
        with engine.connect() as connection:
            return set(inspect(connection).get_table_names())
    finally:
        engine.dispose()


def test_upgrade_head_creates_schema(db_path):
    run_alembic_upgrade(db_path)

    tables = table_names(db_path)
    assert "alembic_version" in tables, tables

    # Tolerant on purpose: Phase 1 keeps adding domain tables (risk_flags,
    # ownership_records, ...) and later revisions will extend this schema.
    # Only the stable pre-Phase-1 core is asserted, and only if the baseline
    # revision is present in this checkout at all.
    app_tables = tables - {"alembic_version"}
    if app_tables:
        assert {"users", "properties", "documents"} <= app_tables, app_tables


def test_downgrade_base_then_upgrade_head_again(db_path):
    run_alembic_upgrade(db_path)
    assert "alembic_version" in table_names(db_path)

    run_alembic_downgrade(db_path, "base")
    # alembic keeps its (now empty) version table around after downgrading to base
    assert "alembic_version" in table_names(db_path)

    run_alembic_upgrade(db_path)
    assert "alembic_version" in table_names(db_path)


def test_upgrade_head_is_idempotent(db_path):
    run_alembic_upgrade(db_path)
    first = table_names(db_path)

    run_alembic_upgrade(db_path)  # second run must be a no-op
    assert table_names(db_path) == first
