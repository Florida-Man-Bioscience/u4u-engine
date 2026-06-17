"""
Tests for engine/users/deps.py — the FastAPI dependencies that resolve
Authentik forward-auth headers to a local users row.

Runs against the SQLite fallback (no DATABASE_URL) so the test suite is
hermetic. The dependency itself is the same code in prod; the only
difference is which backend get_conn() yields.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from engine.users import db as users_db
from engine.users import service
from engine.users.deps import current_user, required_user


@pytest.fixture(autouse=True)
def isolated_users_db(tmp_path, monkeypatch):
    """Redirect the users default DB path to a per-test tmp file.

    engine/users/db._DEFAULT_PATH is captured at module import time, so
    monkeypatch the attribute directly and reset the schema-init memo so
    the new file gets a fresh schema run.
    """
    monkeypatch.setattr(users_db, "_DEFAULT_PATH", tmp_path / "users.db")
    users_db.reset_initialized()
    yield
    users_db.reset_initialized()


def _fake_request(headers: dict[str, str]):
    """Stub Request — current_user only touches request.headers."""
    return SimpleNamespace(headers=headers)


def test_current_user_returns_none_without_authentik_uid():
    """Dev mode: no proxy in front, headers absent. The dep must return
    None so endpoints can record NULL ownership instead of 401-ing."""
    assert current_user(_fake_request({})) is None
    assert current_user(_fake_request({"X-Authentik-Username": "alice"})) is None


def test_current_user_upserts_and_returns_user():
    user = current_user(
        _fake_request(
            {
                "X-Authentik-Uid": "ak-001",
                "X-Authentik-Username": "alice",
                "X-Authentik-Email": "alice@example.com",
            }
        )
    )
    assert user is not None
    assert user.authentik_uid == "ak-001"
    assert user.username == "alice"
    assert user.email == "alice@example.com"

    # The row should now be persisted — a second call returns the same
    # internal id, not a duplicate.
    again = current_user(
        _fake_request({"X-Authentik-Uid": "ak-001", "X-Authentik-Username": "alice"})
    )
    assert again is not None
    assert again.id == user.id

    with users_db.get_conn() as conn:
        rows = service.list_users(conn)
    assert len(rows) == 1


def test_current_user_refreshes_profile_fields():
    """Authentik is the source of truth — profile fields must update on
    each request so a username change in the IdP doesn't go stale."""
    first = current_user(
        _fake_request({"X-Authentik-Uid": "ak-002", "X-Authentik-Username": "bob"})
    )
    second = current_user(
        _fake_request(
            {
                "X-Authentik-Uid": "ak-002",
                "X-Authentik-Username": "bob-renamed",
                "X-Authentik-Email": "bob@example.com",
            }
        )
    )
    assert first is not None and second is not None
    assert second.id == first.id
    assert second.username == "bob-renamed"
    assert second.email == "bob@example.com"


def test_required_user_raises_401_without_uid():
    with pytest.raises(HTTPException) as exc:
        required_user(_fake_request({}))
    assert exc.value.status_code == 401


def test_required_user_returns_user_when_present():
    user = required_user(
        _fake_request({"X-Authentik-Uid": "ak-003", "X-Authentik-Username": "carol"})
    )
    assert user.authentik_uid == "ak-003"
