"""
engine/users/models.py
======================
Dataclass(es) representing a row of the users table.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class User:
    id: str
    authentik_uid: str
    username: str
    email: str | None
    full_name: str | None
    groups: str | None
    created_at: str
    last_seen_at: str
    disabled_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "authentik_uid": self.authentik_uid,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "groups": (
                [g.strip() for g in self.groups.split(",") if g.strip()]
                if self.groups
                else []
            ),
            "created_at": self.created_at,
            "last_seen_at": self.last_seen_at,
            "disabled_at": self.disabled_at,
        }
