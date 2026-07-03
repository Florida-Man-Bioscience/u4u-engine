#!/usr/bin/env python3
"""
scripts/create_device_token.py
==============================
Mint a long-lived device token for the peptodyssey iOS app.

Creates the user (by email) if needed, generates an opaque token, stores only
its SHA-256 hash, and prints the raw token ONCE. Paste that token into the app's
Backend settings.

Usage:
    DATABASE_URL=postgresql+asyncpg://u4u:u4u@localhost:5432/u4u \
        python scripts/create_device_token.py user@example.com --device "Curtis iPhone"
"""
from __future__ import annotations

import argparse
import asyncio
import secrets
import sys

from sqlalchemy import select

from engine.health.auth import hash_token
from engine.health.db import HEALTH_DB_ENABLED, dispose, init_models, session_factory
from engine.health.models import DeviceToken, User


async def _create(email: str, device_name: str | None) -> str:
    await init_models()
    raw_token = "pep_" + secrets.token_urlsafe(32)

    async with session_factory()() as session:
        user = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if user is None:
            user = User(email=email)
            session.add(user)
            await session.flush()

        session.add(
            DeviceToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                device_name=device_name,
            )
        )
        await session.commit()

    await dispose()
    return raw_token


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a peptodyssey device token.")
    parser.add_argument("email", help="user email (created if new)")
    parser.add_argument("--device", default=None, help="device label, e.g. 'Curtis iPhone'")
    args = parser.parse_args()

    if not HEALTH_DB_ENABLED:
        sys.exit("DATABASE_URL is not set — cannot reach the health datastore.")

    token = asyncio.run(_create(args.email, args.device))
    print("\nDevice token (store now — it is not recoverable):\n")
    print(f"    {token}\n")


if __name__ == "__main__":
    main()
