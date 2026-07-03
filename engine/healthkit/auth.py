"""
engine/healthkit/auth.py
========================
Interim per-device bearer-token auth for HealthKit ingestion, so the endpoint is
not an open write endpoint in production.

Enforcement is fail-closed in prod, open in local dev:
  * A token is REQUIRED when a real database is configured (DATABASE_URL set) or
    when HEALTHKIT_REQUIRE_TOKEN is truthy.
  * Anonymous ingestion is allowed only in the SQLite dev/test fallback (no
    DATABASE_URL) — or forced open with HEALTHKIT_ALLOW_ANONYMOUS=1.

Tokens are opaque (`pep_hk_…`), stored only as SHA-256 hex (see
scripts/create_healthkit_token.py). A token may optionally be bound to a single
`subject_id`; when bound, it may only write that subject.

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
    """Whether a valid device token is required for ingestion (fail-closed in prod)."""
    if os.getenv("HEALTHKIT_ALLOW_ANONYMOUS", "").strip().lower() in _TRUTHY:
        return False
    if os.getenv("HEALTHKIT_REQUIRE_TOKEN", "").strip().lower() in _TRUTHY:
        return True
    from db.pool import DATABASE_URL
    return bool(DATABASE_URL)


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


def enforce_subject(token: dict | None, subject_id: str) -> None:
    """If the token is bound to a subject, reject writes to any other subject."""
    if token is not None and token.get("subject_id") and token["subject_id"] != subject_id:
        raise HTTPException(
            status_code=403,
            detail="Device token is bound to a different subject_id.",
        )
