"""
engine/users/service.py
========================
CRUD + upsert-from-headers for the users table.

Same dual-dialect pattern as engine/tracking/service.py — SQL written
with portable ON CONFLICT and a placeholder helper that picks `%s` for
Postgres and `?` for SQLite.
"""
from __future__ import annotations

import secrets
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from .models import User


def _new_id() -> str:
    """16-byte hex token — short enough for URLs, long enough that
    collisions are negligible. Used in the SQLite fallback path where
    we can't lean on Postgres's gen_random_uuid()."""
    return secrets.token_hex(16)


def _row(row) -> dict[str, Any]:
    """Normalise psycopg2 RealDictRow / sqlite3.Row to a plain dict and
    coerce datetimes to ISO strings so the dataclass roundtrips cleanly
    across dialects."""
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
        elif v is not None and not isinstance(v, (str, int, float, bool, list, dict)):
            # uuid.UUID, etc.
            d[k] = str(v)
    return d


def _ph(conn) -> str:
    return "%s" if getattr(conn, "_is_pg", False) else "?"


# ── Reads ─────────────────────────────────────────────────────────────────


def get_user(conn, user_id: str) -> User | None:
    ph = _ph(conn)
    row = conn.execute(
        f"SELECT * FROM users WHERE id = {ph}", (user_id,)
    ).fetchone()
    return User(**_row(row)) if row else None


def get_user_by_authentik_uid(conn, uid: str) -> User | None:
    ph = _ph(conn)
    row = conn.execute(
        f"SELECT * FROM users WHERE authentik_uid = {ph}", (uid,)
    ).fetchone()
    return User(**_row(row)) if row else None


def get_user_by_issuer_sub(conn, issuer: str, sub: str) -> User | None:
    ph = _ph(conn)
    row = conn.execute(
        f"SELECT * FROM users WHERE issuer = {ph} AND authentik_uid = {ph}",
        (issuer, sub),
    ).fetchone()
    return User(**_row(row)) if row else None


def list_users(conn) -> list[User]:
    rows = conn.execute(
        "SELECT * FROM users ORDER BY created_at DESC"
    ).fetchall()
    return [User(**_row(r)) for r in rows]


# ── Writes ────────────────────────────────────────────────────────────────


def upsert_from_headers(conn, headers: Mapping[str, str]) -> User | None:
    """Materialise a User row from the Authentik forward-auth headers.

    Returns the user on success, or None when the proxy hasn't sent us
    enough information to identify a subject (the bare-minimum we
    require is the stable subject id; without it we refuse to invent
    one because that would create a separate user every request).

    On every hit:
      - INSERT a new row when the subject id is new.
      - UPDATE the username/email/full_name/groups when the subject is
        known (the IdP is the source of truth for profile fields, so we
        re-mirror them on each request rather than letting them drift).
      - Bump last_seen_at to now.

    The headers we read are the Authentik proxy defaults (see
    https://docs.goauthentik.io/docs/providers/proxy/server_nginx —
    every reverse-proxy integration uses the same X-Authentik-* set).
    Header lookup is case-insensitive because FastAPI's Headers mapping
    normalises to lowercase.
    """
    h = {k.lower(): v for k, v in headers.items() if v}

    uid = (h.get("x-authentik-uid") or "").strip()
    if not uid:
        return None  # no subject id → can't anchor a user row

    username = (h.get("x-authentik-username") or uid).strip()
    email = (h.get("x-authentik-email") or "").strip() or None
    full_name = (h.get("x-authentik-name") or "").strip() or None
    groups = (h.get("x-authentik-groups") or "").strip() or None

    ph = _ph(conn)
    is_pg = getattr(conn, "_is_pg", False)

    # Generate an id up front so we can hand the same value to both
    # branches of the upsert. Postgres would also accept a DEFAULT-
    # generated UUID, but it's simpler to keep ID minting in one place
    # so both dialects produce string-shaped ids that round-trip the
    # same way.
    new_id = _new_id()

    if is_pg:
        # Postgres: full upsert with RETURNING so we get the row back
        # in one round trip.
        sql = f"""
            INSERT INTO users
                (id, authentik_uid, username, email, full_name, groups)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            ON CONFLICT (authentik_uid) DO UPDATE SET
                username     = EXCLUDED.username,
                email        = EXCLUDED.email,
                full_name    = EXCLUDED.full_name,
                groups       = EXCLUDED.groups,
                last_seen_at = NOW()
            RETURNING *
        """
        row = conn.execute(
            sql,
            (new_id, uid, username, email, full_name, groups),
        ).fetchone()
        conn.commit()
        return User(**_row(row))

    # SQLite path: ON CONFLICT is supported (sqlite ≥ 3.24) but
    # RETURNING is only in sqlite ≥ 3.35. To stay portable to older
    # builds we do the upsert then SELECT.
    conn.execute(
        f"""INSERT INTO users
              (id, authentik_uid, username, email, full_name, groups)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            ON CONFLICT(authentik_uid) DO UPDATE SET
                username     = excluded.username,
                email        = excluded.email,
                full_name    = excluded.full_name,
                groups       = excluded.groups,
                last_seen_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
        (new_id, uid, username, email, full_name, groups),
    )
    conn.commit()
    row = conn.execute(
        f"SELECT * FROM users WHERE authentik_uid = {ph}", (uid,)
    ).fetchone()
    return User(**_row(row)) if row else None


def disable_user(conn, user_id: str) -> bool:
    """Soft-delete: set disabled_at = now. Returns False if user not
    found. Leaves all FKs from other tables intact so historical data
    keeps its provenance."""
    ph = _ph(conn)
    is_pg = getattr(conn, "_is_pg", False)
    now_expr = "NOW()" if is_pg else "strftime('%Y-%m-%dT%H:%M:%fZ','now')"
    cur = conn.execute(
        f"UPDATE users SET disabled_at = {now_expr} "
        f"WHERE id = {ph} AND disabled_at IS NULL",
        (user_id,),
    )
    conn.commit()
    return cur.rowcount > 0
