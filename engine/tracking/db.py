"""
engine/tracking/db.py
=====================
SQLite connection helper for biomarker tracking. Default path is
data/biomarker_tracking.db; override with TRACKING_DB_PATH env var or
pass `path=` directly (used in tests).
"""
from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")
_DEFAULT_PATH = Path(os.getenv("DATA_DIR", "data")) / "biomarker_tracking.db"

_lock = threading.Lock()
_initialized: set[str] = set()


def _ensure_schema(conn: sqlite3.Connection, key: str) -> None:
    with _lock:
        if key in _initialized:
            return
        with open(_SCHEMA_PATH, encoding="utf-8") as fh:
            conn.executescript(fh.read())
        conn.commit()
        _initialized.add(key)


def get_conn(path: str | os.PathLike | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with FK enforcement and Row factory."""
    p = Path(path) if path else _DEFAULT_PATH
    if str(p) != ":memory:":
        p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    _ensure_schema(conn, str(p))
    return conn


def reset_initialized() -> None:
    """Test helper — force schema re-init on next get_conn."""
    with _lock:
        _initialized.clear()
