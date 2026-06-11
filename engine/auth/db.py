"""
engine/auth/db.py
=================
SQLite connection helper for auth (users + sessions). Default path is
``data/auth.db``; override with ``AUTH_DB_PATH`` env var or pass
``path=`` directly (used in tests).

Mirrors the ``engine/tracking/db.py`` pattern so the two subsystems stay
consistent — but auth lives in its own database so the two domains stay
decoupled.
"""
from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")
_DEFAULT_PATH = Path(os.getenv("DATA_DIR", "data")) / "auth.db"

_lock = threading.Lock()
_initialized: set[str] = set()
# Cache one connection per (resolved) path. The auth DB sits on the hot
# path of every protected API request, so opening a fresh connection per
# request would be wasteful (and would leak: middleware never closes
# them). SQLite + WAL + check_same_thread=False is safe to share across
# FastAPI's worker threads — concurrent reads run in parallel; writes
# serialize internally.
_connections: dict[str, sqlite3.Connection] = {}


def _ensure_schema(conn: sqlite3.Connection, key: str) -> None:
    with _lock:
        if key in _initialized:
            return
        with open(_SCHEMA_PATH, encoding="utf-8") as fh:
            conn.executescript(fh.read())
        conn.commit()
        _initialized.add(key)


def get_conn(path: str | os.PathLike | None = None) -> sqlite3.Connection:
    """Return the cached SQLite connection for the resolved auth DB path,
    opening it on first use. Subsequent calls reuse the same connection.

    Tests can still inject their own DB by monkeypatching ``get_conn`` or
    by calling ``set_connection_for_test``."""
    p = Path(path) if path else (
        Path(os.getenv("AUTH_DB_PATH")) if os.getenv("AUTH_DB_PATH") else _DEFAULT_PATH
    )
    key = str(p)
    with _lock:
        cached = _connections.get(key)
        if cached is not None:
            return cached
    if key != ":memory:":
        p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(key, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    _ensure_schema(conn, key)
    with _lock:
        # Another thread may have raced us; honour whatever got installed
        # first to keep a single conn per path.
        existing = _connections.get(key)
        if existing is not None:
            conn.close()
            return existing
        _connections[key] = conn
    return conn


def reset_initialized() -> None:
    """Test helper — close any cached connections and force schema
    re-init on the next ``get_conn`` call."""
    with _lock:
        for c in _connections.values():
            try:
                c.close()
            except Exception:
                pass
        _connections.clear()
        _initialized.clear()
