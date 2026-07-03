"""
engine/health/auth.py
====================
Device-token authentication for HealthKit ingestion.

The iOS app stores one long-lived opaque bearer token in its Keychain and sends
it as ``Authorization: Bearer <token>``. Tokens are stored hashed (SHA-256); the
raw value is only shown once, at creation (see scripts/create_device_token.py).
"""
from __future__ import annotations

import hashlib
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from engine.health.db import get_session
from engine.health.models import DeviceToken

_bearer = HTTPBearer(auto_error=True)


def hash_token(raw: str) -> str:
    """SHA-256 hex digest of a raw token — what we store and compare against."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> UUID:
    """Resolve the bearer token to a user id, or 401."""
    token_hash = hash_token(credentials.credentials)
    row = (
        await session.execute(
            select(DeviceToken).where(
                DeviceToken.token_hash == token_hash,
                DeviceToken.revoked.is_(False),
            )
        )
    ).scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=401, detail="Invalid or revoked device token.")
    return row.user_id
