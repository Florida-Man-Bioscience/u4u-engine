"""
engine/annotation_cache.py
===========================
Universal SQLite cache for all external API annotation results.

Provides a simple key-value store keyed by (source, lookup_key) that
persists JSON-serialized API responses to disk. Each annotator checks
the cache before making network calls.

Public interface
----------------
    get(source: str, key: str) -> dict | list | None
    put(source: str, key: str, result: dict | list | None) -> None

Storage
-------
    File: data/annotation_cache.db  (same directory as rsid_cache.db)
    Table: annotation_cache (source TEXT, lookup_key TEXT, result_json TEXT, created_at TEXT)
"""

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone

_CACHE_DB_PATH = os.path.join(os.getenv("DATA_DIR", "data"), "annotation_cache.db")

# Thread-local storage for per-thread SQLite connections
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Get or create a thread-local SQLite connection."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(_CACHE_DB_PATH, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS annotation_cache (
                source      TEXT,
                lookup_key  TEXT,
                result_json TEXT,
                created_at  TEXT,
                PRIMARY KEY (source, lookup_key)
            )
        """)
        _local.conn = conn
    return conn


def get(source: str, key: str):
    """
    Retrieve a cached annotation result.

    Parameters
    ----------
    source : str   Annotator name (e.g. "vep", "clinvar", "gnomad").
    key    : str   Lookup key (e.g. rsID, "chrom-pos-ref-alt", gene symbol).

    Returns
    -------
    dict | list | None
        The cached result, or None if not found.
    """
    try:
        conn = _get_conn()
        cur = conn.execute(
            "SELECT result_json FROM annotation_cache WHERE source = ? AND lookup_key = ?",
            (source, key),
        )
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return None
    except Exception:
        return None


def put(source: str, key: str, result) -> None:
    """
    Store an annotation result in the cache.

    Parameters
    ----------
    source : str           Annotator name.
    key    : str           Lookup key.
    result : dict | list | None   The API result to cache.
    """
    try:
        conn = _get_conn()
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO annotation_cache (source, lookup_key, result_json, created_at) VALUES (?, ?, ?, ?)",
            (source, key, json.dumps(result), now),
        )
        conn.commit()
    except Exception:
        pass  # Cache write failure is non-fatal
