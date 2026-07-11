"""
engine/users/ownership.py
==========================
Ownership guard for per-user resources (jobs, and anything else keyed
by a ``created_by_user_id``-style column).

Rule: a resource with a NULL owner is never "owned" by anyone — it is
treated the same as a resource owned by someone else. Both cases 404
(not 403) so an unauthorized caller can never distinguish "this id
belongs to someone else" from "this id doesn't exist" (no IDOR
existence leak).
"""
from __future__ import annotations

from fastapi import HTTPException

from .models import User


def owns(resource_owner_id: str | None, user: User) -> bool:
    return resource_owner_id is not None and resource_owner_id == user.id


def guard_owner(resource_owner_id: str | None, user: User) -> None:
    if not owns(resource_owner_id, user):
        # 404 (not 403): do not reveal that the id exists.
        raise HTTPException(status_code=404, detail="not found")
