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
from .oidc import cluster_issuer

_CLUSTER_ISSUER_FALLBACK = "cluster-authentik"


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


def _upsert_user(
    conn, *, issuer: str, sub: str, username: str, email: str | None,
    full_name: str | None, groups: str | None,
) -> User:
    """Shared upsert core for both header- and token-derived identities.

    Conflicts on the composite (issuer, authentik_uid) key — the same
    subject id from two different IdPs must not collide, but a re-login
    from the same IdP/subject re-mirrors profile fields onto the
    existing row rather than creating a duplicate.
    """
    ph = _ph(conn)
    is_pg = getattr(conn, "_is_pg", False)

    # Generate an id up front so we can hand the same value to both
    # branches of the upsert. Postgres would also accept a DEFAULT-
    # generated UUID, but it's simpler to keep ID minting in one place
    # so both dialects produce string-shaped ids that round-trip the
    # same way.
    new_id = _new_id()
    cols = "(id, authentik_uid, username, email, full_name, groups, issuer)"
    vals = (new_id, sub, username, email, full_name, groups, issuer)
    conflict = "(issuer, authentik_uid)"

    if is_pg:
        # Postgres: full upsert with RETURNING so we get the row back
        # in one round trip.
        row = conn.execute(
            f"""INSERT INTO users {cols}
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                ON CONFLICT {conflict} DO UPDATE SET
                    username     = EXCLUDED.username,
                    email        = EXCLUDED.email,
                    full_name    = EXCLUDED.full_name,
                    groups       = EXCLUDED.groups,
                    last_seen_at = NOW()
                RETURNING *""",
            vals,
        ).fetchone()
        conn.commit()
        return User(**_row(row))

    # SQLite path: ON CONFLICT is supported (sqlite ≥ 3.24) but
    # RETURNING is only in sqlite ≥ 3.35. To stay portable to older
    # builds we do the upsert then SELECT.
    conn.execute(
        f"""INSERT INTO users {cols}
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            ON CONFLICT{conflict} DO UPDATE SET
                username     = excluded.username,
                email        = excluded.email,
                full_name    = excluded.full_name,
                groups       = excluded.groups,
                last_seen_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
        vals,
    )
    conn.commit()
    return get_user_by_issuer_sub(conn, issuer, sub)


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

    These headers always come from the cluster-admin Authentik (the
    forward-auth proxy in front of the app), so we stamp `issuer` with
    that IdP's issuer URL — falling back to a placeholder literal when
    `U4U_CLUSTER_AUTHENTIK_ISSUER` isn't configured (local dev/tests).
    """
    h = {k.lower(): v for k, v in headers.items() if v}

    uid = (h.get("x-authentik-uid") or "").strip()
    if not uid:
        return None  # no subject id → can't anchor a user row

    username = (h.get("x-authentik-username") or uid).strip()
    email = (h.get("x-authentik-email") or "").strip() or None
    full_name = (h.get("x-authentik-name") or "").strip() or None
    groups = (h.get("x-authentik-groups") or "").strip() or None
    issuer = cluster_issuer() or _CLUSTER_ISSUER_FALLBACK

    return _upsert_user(
        conn, issuer=issuer, sub=uid, username=username, email=email,
        full_name=full_name, groups=groups,
    )


def upsert_from_token(conn, *, issuer: str, claims: Mapping[str, Any]) -> User:
    """Materialise a User row from a validated end-user OIDC access
    token's claims. Keyed on (issuer, sub) — the dedicated end-user
    Authentik is a distinct issuer from the cluster-admin one, so the
    same `sub` value from each IdP maps to a different local row.

    End-users get no staff `groups` — that concept only applies to the
    cluster-admin population authenticated via upsert_from_headers.
    """
    sub = str(claims["sub"]).strip()
    username = (claims.get("preferred_username") or claims.get("email") or sub).strip()
    email = (claims.get("email") or "").strip() or None
    full_name = (claims.get("name") or "").strip() or None
    return _upsert_user(
        conn, issuer=issuer, sub=sub, username=username, email=email,
        full_name=full_name, groups=None,
    )


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
