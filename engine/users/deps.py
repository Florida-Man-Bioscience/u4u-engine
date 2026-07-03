"""
engine/users/deps.py
=====================
FastAPI dependencies that resolve the current Authentik subject to a
local ``users`` row.

Two flavors:

* ``current_user`` — soft. Returns ``None`` when Authentik headers are
  missing. Use this on data-creation endpoints so dev mode (no proxy in
  front) keeps working: the resulting row is written with
  ``created_by_user_id = NULL`` instead of 401-ing the request.

* ``required_user`` — hard. Raises 401 when no subject is present. Use
  this on endpoints that genuinely need an authenticated operator
  (e.g. ``/users/me``, anything that mutates ``users`` itself).

The dependencies open a short-lived users-DB connection per request via
``engine.users.db.get_conn`` and run ``upsert_from_headers`` so the
``users`` row is also refreshed on every hit (Authentik is the source of
truth for username/email/groups — we never let local copies drift).
"""
from __future__ import annotations

from fastapi import HTTPException, Request

from . import service
from .db import get_conn
from .models import User


def current_user(request: Request) -> User | None:
    """Soft dependency: returns the upserted user, or ``None`` in dev
    mode / when Authentik hasn't forwarded a subject id."""
    with get_conn() as conn:
        return service.upsert_from_headers(conn, request.headers)


def required_user(request: Request) -> User:
    """Hard dependency: 401 when no Authentik subject is present."""
    user = current_user(request)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="no authenticated user — Authentik headers missing",
        )
    return user
