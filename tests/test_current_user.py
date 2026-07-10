"""
Tests for engine/users/deps.py — the FastAPI dependencies that resolve
the current request's authenticated end-user (OIDC Bearer token, or
the dev-bypass user when no OIDC issuer is configured) to a local
users row.

Runs against the SQLite fallback (no DATABASE_URL) so the test suite is
hermetic. The dependency itself is the same code in prod; the only
difference is which backend get_conn() yields.

This file focuses on ``current_user`` (the *soft* dependency) — the
one behavior not exercised by
tests/test_engine/test_users/test_deps_auth.py, which only calls
``required_user``. In particular it proves the soft/hard reconciliation
from Task 6: ``current_user`` must swallow an invalid token
(``TokenError``) into ``None`` (never 500 a soft endpoint on a garbage
Authorization header) while still propagating a JWKS outage
(``JwksUnavailable``) so callers can fail closed.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from engine.users import db as users_db
from engine.users import deps, service
from engine.users.deps import current_user, required_user
from engine.users.oidc import OidcSettings
from engine.users.token_validator import JwksUnavailable, TokenError

_FAKE_SETTINGS = OidcSettings(
    issuer="https://id.example/app",
    audience="u4u-web",
    jwks_url="https://id.example/app/jwks",
)


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


def _req(headers=None):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request({"type": "http", "headers": raw})


# ── Dev-bypass mode (no OIDC issuer configured — the default here) ────────


def test_current_user_returns_dev_user_when_unconfigured():
    """No OIDC issuer configured (dev/test default): current_user always
    returns the fixed dev-bypass user, regardless of headers."""
    first = current_user(_req())
    assert first is not None
    assert first.authentik_uid == deps.DEV_BYPASS_SUB

    # Stable identity across calls — same local row, not a duplicate.
    second = current_user(_req())
    assert second.id == first.id

    with users_db.get_conn() as conn:
        rows = [u for u in service.list_users(conn) if u.issuer == "dev-bypass"]
    assert len(rows) == 1


def test_required_user_returns_dev_user_when_unconfigured():
    user = required_user(_req())
    assert user.authentik_uid == deps.DEV_BYPASS_SUB


# ── OIDC mode ───────────────────────────────────────────────────────────


def test_current_user_returns_none_without_bearer(monkeypatch):
    monkeypatch.setattr(deps.oidc, "oidc_settings", lambda: _FAKE_SETTINGS)
    assert current_user(_req()) is None


def test_current_user_returns_none_on_invalid_token(monkeypatch):
    """A present-but-invalid token must be swallowed to None by the soft
    dependency, not raised — a garbage Authorization header must never
    turn a soft endpoint into a 500."""
    monkeypatch.setattr(deps.oidc, "oidc_settings", lambda: _FAKE_SETTINGS)
    monkeypatch.setattr(
        deps, "validate_token",
        lambda t, s: (_ for _ in ()).throw(TokenError("bad")),
    )
    assert current_user(_req({"Authorization": "Bearer x"})) is None


def test_current_user_propagates_jwks_unavailable(monkeypatch):
    """A JWKS outage means validity is unknown — current_user must fail
    closed by propagating JwksUnavailable rather than downgrading to
    anonymous (None)."""
    monkeypatch.setattr(deps.oidc, "oidc_settings", lambda: _FAKE_SETTINGS)
    monkeypatch.setattr(
        deps, "validate_token",
        lambda t, s: (_ for _ in ()).throw(JwksUnavailable("down")),
    )
    with pytest.raises(JwksUnavailable):
        current_user(_req({"Authorization": "Bearer x"}))


def test_current_user_upserts_and_returns_user_for_valid_token(monkeypatch):
    monkeypatch.setattr(deps.oidc, "oidc_settings", lambda: _FAKE_SETTINGS)
    monkeypatch.setattr(
        deps, "validate_token",
        lambda t, s: {"sub": "ak-001", "preferred_username": "alice",
                       "email": "alice@example.com"},
    )
    user = current_user(_req({"Authorization": "Bearer good"}))
    assert user is not None
    assert user.authentik_uid == "ak-001"
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.issuer == _FAKE_SETTINGS.issuer

    # Same (issuer, sub) on a second call resolves to the same row.
    again = current_user(_req({"Authorization": "Bearer good"}))
    assert again is not None
    assert again.id == user.id


def test_required_user_raises_401_without_bearer(monkeypatch):
    monkeypatch.setattr(deps.oidc, "oidc_settings", lambda: _FAKE_SETTINGS)
    with pytest.raises(HTTPException) as exc:
        required_user(_req())
    assert exc.value.status_code == 401


def test_required_user_returns_user_when_present(monkeypatch):
    monkeypatch.setattr(deps.oidc, "oidc_settings", lambda: _FAKE_SETTINGS)
    monkeypatch.setattr(
        deps, "validate_token",
        lambda t, s: {"sub": "ak-003", "preferred_username": "carol"},
    )
    user = required_user(_req({"Authorization": "Bearer good"}))
    assert user.authentik_uid == "ak-003"
