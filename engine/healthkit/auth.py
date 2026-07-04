"""
engine/healthkit/auth.py
========================
Interim per-device bearer-token auth for HealthKit ingestion, so the endpoint is
not an open write endpoint in production.

Enforcement is fail-closed in prod, open in local dev:
  * When a real database is configured (DATABASE_URL set) a token is ALWAYS
    required — no env var can open a Postgres-backed deployment.
  * Only the local SQLite dev/test fallback (no DATABASE_URL) is open, and even
    that closes with HEALTHKIT_REQUIRE_TOKEN=1.

Tokens are opaque (`pep_hk_…`), stored only as SHA-256 hex (see
scripts/create_healthkit_token.py). A token may optionally be bound to a single
`subject_id`; a bound token may only touch that subject, and read endpoints
require a bound token so a shared token can't read every subject's data.

This is the interim closure of the auth gap. The documented longer-term target
is Authentik (device-code flow / forward-auth) — see docs/healthkit-storage.md.
"""
from __future__ import annotations

import hashlib
import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .db import get_conn

_bearer = HTTPBearer(auto_error=False)

_TRUTHY = {"1", "true", "yes", "on"}


def hash_token(raw: str) -> str:
    """SHA-256 hex digest of a raw token — what we store and compare against."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def token_required() -> bool:
    """Whether a valid device token is required for ingestion.

    Fail-closed in prod: when a real database is configured (DATABASE_URL set) a
    token is ALWAYS required and cannot be turned off — no env var opens a
    Postgres-backed deployment. Only the local SQLite dev/test fallback (no
    DATABASE_URL) is open, and even that closes with HEALTHKIT_REQUIRE_TOKEN=1.
    """
    from db.pool import DATABASE_URL
    if DATABASE_URL:
        return True
    return os.getenv("HEALTHKIT_REQUIRE_TOKEN", "").strip().lower() in _TRUTHY


def require_device_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict | None:
    """Resolve a bearer token to its row, or None when anonymous is allowed.

    Raises 401 when a token is required and missing/invalid/revoked.
    """
    if credentials is None:
        if token_required():
            raise HTTPException(status_code=401, detail="Missing device bearer token.")
        return None

    token_hash = hash_token(credentials.credentials)
    with get_conn() as conn:
        ph = "%s" if getattr(conn, "_is_pg", False) else "?"
        row = conn.execute(
            f"SELECT * FROM healthkit_device_tokens "
            f"WHERE token_hash = {ph} AND NOT revoked",
            (token_hash,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Invalid or revoked device token.")
        # Best-effort last-used bookkeeping.
        now_fn = "NOW()" if ph == "%s" else "strftime('%Y-%m-%dT%H:%M:%fZ','now')"
        conn.execute(
            f"UPDATE healthkit_device_tokens SET last_used_at = {now_fn} "
            f"WHERE token_hash = {ph}",
            (token_hash,),
        )
        conn.commit()
        return dict(row)


def enforce_subject(token: dict | None, subject_id: str, *, require_bound: bool = False) -> None:
    """Authorize a token for `subject_id`.

    A `None` token is the open dev/test path (no scoping). For a real token:
    - if it is bound to a subject (``subject_id IS NOT NULL``, tested with
      ``is not None`` so an empty-string binding is NOT treated as unbound), it
      may only touch that subject;
    - if `require_bound` is set (read endpoints), an *unbound* token is rejected
      so a shared device token can't read every subject's data.
    """
    if token is None:
        return
    bound = token.get("subject_id")
    if require_bound and bound is None:
        raise HTTPException(
            status_code=403,
            detail="This endpoint requires a subject-bound device token.",
        )
    if bound is not None and bound != subject_id:
        raise HTTPException(
            status_code=403,
            detail="Device token is bound to a different subject_id.",
        )
