"""
engine/users/db.py
==================
Connection helper for the users table. Same Postgres-or-SQLite switch
pattern as engine/tracking/db.py.
"""
from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")
_DEFAULT_PATH = Path(os.getenv("DATA_DIR", "data")) / "users.db"

_lock = threading.Lock()
_sqlite_initialized: set[str] = set()


def _ensure_sqlite_schema(conn, key: str) -> None:
    with _lock:
        if key in _sqlite_initialized:
            return
        with open(_SCHEMA_PATH, encoding="utf-8") as fh:
            conn.executescript(fh.read())
        conn.commit()
        _sqlite_initialized.add(key)


def _is_postgres_configured(path) -> bool:
    from db.pool import DATABASE_URL
    return bool(DATABASE_URL) and path is None


@contextmanager
def get_conn(path: str | os.PathLike | None = None) -> Generator:
    """Context manager — Postgres in prod, SQLite for dev/tests."""
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
