"""
engine/tracking/db.py
=====================
Database connection helper for biomarker tracking.

In production (DATABASE_URL set): yields a psycopg2 connection from the
shared pool via the get_conn() context manager.

In local dev / tests (no DATABASE_URL, or path explicitly provided): opens
a SQLite connection as before so that tests and the dev shell work without
a Postgres instance.
"""
from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")
_DEFAULT_PATH = Path(os.getenv("DATA_DIR", "data")) / "biomarker_tracking.db"

_lock = threading.Lock()
_sqlite_initialized: set[str] = set()


def _ensure_sqlite_schema(conn, key: str) -> None:
    import sqlite3
    with _lock:
        if key in _sqlite_initialized:
            return
        with open(_SCHEMA_PATH, encoding="utf-8") as fh:
            conn.executescript(fh.read())
        _ensure_user_id_columns(conn)
        conn.commit()
        _sqlite_initialized.add(key)


def _ensure_user_id_columns(conn) -> None:
    """Bring pre-existing dev databases up to the current schema.

    CREATE TABLE IF NOT EXISTS is a no-op against an existing table, so a
    dev who created their data/biomarker_tracking.db before migration 005
    would otherwise miss the created_by_user_id column. SQLite lacks
    ADD COLUMN IF NOT EXISTS, so we read PRAGMA table_info and add what's
    missing. Idempotent — costs three PRAGMA queries on a hot dev DB.
    """
    for table in ("patients", "treatments", "measurements"):
        cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if "created_by_user_id" not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN created_by_user_id TEXT")


def _is_postgres_configured(path) -> bool:
    from db.pool import DATABASE_URL
    return bool(DATABASE_URL) and path is None


@contextmanager
def get_conn(path: str | os.PathLike | None = None) -> Generator:
    """
    Context manager yielding a database connection for tracking operations.

    When DATABASE_URL is set and no explicit path is given, yields a
    psycopg2 connection from the shared pool. Otherwise opens a per-call
    SQLite connection (suitable for tests and local dev).

    Usage::

        with get_conn() as conn:
            service.create_patient(conn, label="P-001")
    """
    if _is_postgres_configured(path):
        from db.pool import get_conn as pg_get_conn
        with pg_get_conn() as conn:
            yield conn
    else:
        import sqlite3
        p = Path(path) if path else _DEFAULT_PATH
        if str(p) != ":memory:":
            p.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(p), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        _ensure_sqlite_schema(conn, str(p))
        try:
            yield conn
        finally:
            conn.close()


def reset_initialized() -> None:
    """Test helper — force SQLite schema re-init on next get_conn."""
    with _lock:
        _sqlite_initialized.clear()
