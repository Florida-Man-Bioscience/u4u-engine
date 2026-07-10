"""Startup migration behaviour.

A failed migration must abort startup loudly rather than silently proceeding
against a half-built schema — the failure mode that let missing tracking
tables reach production and 500 on the first query (see api._run_db_migrations).
"""
from __future__ import annotations

import pytest

import api
import db.migrate


def test_migration_failure_aborts_startup(monkeypatch):
    """When DATABASE_URL is set and a migration raises, the error propagates
    so the process crashes (visible in k8s) instead of serving on a broken
    schema."""
    monkeypatch.setattr(api, "_DB_URL", "postgresql:///whatever")

    def _boom(dsn):
        raise RuntimeError("migration 002 failed")

    monkeypatch.setattr(db.migrate, "run_migrations", _boom)

    with pytest.raises(RuntimeError, match="migration 002 failed"):
        api._run_db_migrations()


def test_no_database_url_is_a_noop(monkeypatch):
    """SQLite / local dev (no DATABASE_URL) must not attempt migrations or
    raise — the schema is created lazily on first use there."""
    monkeypatch.setattr(api, "_DB_URL", "")

    def _should_not_run(dsn):  # pragma: no cover - asserts it's never called
        raise AssertionError("run_migrations must not be called without DATABASE_URL")

    monkeypatch.setattr(db.migrate, "run_migrations", _should_not_run)

    api._run_db_migrations()  # no exception
