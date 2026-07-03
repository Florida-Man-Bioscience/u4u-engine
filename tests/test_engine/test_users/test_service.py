"""
Tests for the users service layer.

The fixture in conftest.py gives us a fresh in-memory SQLite database
per test (mirrors engine/tracking's setup). All upsert / read paths go
through the same code that runs in production, just against SQLite.
"""
from __future__ import annotations

import pytest

from engine.users import service


def _headers(**kw):
    """Build a CaseInsensitive-ish header mapping. The service layer
    lowercases keys internally so any casing is fine here, but we use
    the same casing Authentik actually sends so the tests double as
    documentation of the header contract."""
    return {
        f"X-Authentik-{k.replace('_', '-').title()}": v
        for k, v in kw.items()
        if v is not None
    }


def test_upsert_requires_subject_id(conn):
    """Without X-Authentik-Uid we can't anchor a user — service should
    return None rather than mint a fresh row every request."""
    user = service.upsert_from_headers(conn, {"X-Authentik-Username": "alice"})
    assert user is None
    assert service.list_users(conn) == []


def test_upsert_creates_user_on_first_sight(conn):
    user = service.upsert_from_headers(
        conn,
        _headers(
            uid="ak-1234",
            username="alice",
            email="alice@example.com",
            name="Alice Example",
            groups="staff,clinical",
        ),
    )
    assert user is not None
    assert user.authentik_uid == "ak-1234"
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.full_name == "Alice Example"
    assert user.groups == "staff,clinical"
    assert user.disabled_at is None
    assert user.id  # populated
    assert user.created_at  # populated
    assert user.last_seen_at  # populated


def test_upsert_groups_serialise_to_list_in_dict(conn):
    """to_dict() splits the stored CSV groups string into a JSON-friendly
    list. Empty / missing groups → empty list."""
    user = service.upsert_from_headers(
        conn,
        _headers(uid="ak-2", username="b", groups="a,b, c"),
    )
    assert user is not None
    assert user.to_dict()["groups"] == ["a", "b", "c"]

    user2 = service.upsert_from_headers(conn, _headers(uid="ak-3", username="c"))
    assert user2 is not None
    assert user2.to_dict()["groups"] == []


def test_upsert_updates_profile_fields_on_re_login(conn):
    """The IdP is the source of truth for profile fields — we re-mirror
    them on every request rather than letting them drift."""
    first = service.upsert_from_headers(
        conn,
        _headers(uid="ak-9", username="old-name", email="old@x.com"),
    )
    assert first is not None
    second = service.upsert_from_headers(
        conn,
        _headers(uid="ak-9", username="new-name", email="new@x.com", name="New Name"),
    )
    assert second is not None
    # Same row (same id), but profile fields refreshed.
    assert second.id == first.id
    assert second.username == "new-name"
    assert second.email == "new@x.com"
    assert second.full_name == "New Name"


def test_upsert_falls_back_to_uid_when_username_missing(conn):
    """Authentik always sends a uid; username may be missing if the
    proxy is misconfigured. Fall back to uid so the row is still
    addressable instead of failing."""
    user = service.upsert_from_headers(conn, _headers(uid="ak-7"))
    assert user is not None
    assert user.username == "ak-7"


def test_upsert_normalises_header_casing(conn):
    """FastAPI normalises header names to lowercase. Make sure the
    service handles either casing without dropping fields."""
    user = service.upsert_from_headers(
        conn,
        {
            "x-authentik-uid": "ak-mixed",
            "X-AUTHENTIK-USERNAME": "carol",
            "X-Authentik-Email": "carol@example.com",
        },
    )
    assert user is not None
    assert user.username == "carol"
    assert user.email == "carol@example.com"


def test_get_user_by_authentik_uid(conn):
    service.upsert_from_headers(conn, _headers(uid="ak-find", username="d"))
    found = service.get_user_by_authentik_uid(conn, "ak-find")
    assert found is not None
    assert found.username == "d"
    assert service.get_user_by_authentik_uid(conn, "ak-nope") is None


def test_disable_user_is_soft_delete(conn):
    user = service.upsert_from_headers(conn, _headers(uid="ak-bye", username="e"))
    assert user is not None
    assert service.disable_user(conn, user.id) is True
    # Row still exists — soft delete preserves history.
    reloaded = service.get_user(conn, user.id)
    assert reloaded is not None
    assert reloaded.disabled_at is not None
    # Re-disabling a disabled user returns False (no rows updated by
    # the `disabled_at IS NULL` clause).
    assert service.disable_user(conn, user.id) is False


def test_disable_unknown_user_returns_false(conn):
    assert service.disable_user(conn, "nonexistent") is False


def test_list_users_returns_newest_first(conn):
    import time

    service.upsert_from_headers(conn, _headers(uid="ak-a", username="a"))
    time.sleep(0.01)
    service.upsert_from_headers(conn, _headers(uid="ak-b", username="b"))
    time.sleep(0.01)
    service.upsert_from_headers(conn, _headers(uid="ak-c", username="c"))

    listed = service.list_users(conn)
    assert [u.username for u in listed] == ["c", "b", "a"]
