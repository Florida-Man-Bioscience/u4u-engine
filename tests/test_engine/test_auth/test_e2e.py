"""
End-to-end auth integration test.

Follows the realistic operator path so a future refactor can't silently
break the whole flow even if every individual unit test still passes:

    bootstrap admin from env
      → log in
      → call a tracking endpoint with the issued bearer
      → change password
      → old token is rejected
      → new token works
      → logout revokes the new token
"""
import sqlite3

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

import api  # noqa: E402
from engine.auth import api as auth_api  # noqa: E402
from engine.auth import db as auth_db  # noqa: E402
from engine.auth import service as auth_service  # noqa: E402
from engine.auth.rate_limit import login_limiter  # noqa: E402
from engine.tracking import api as tracking_api  # noqa: E402
from engine.tracking import db as tracking_db  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_login_limiter():
    login_limiter.reset()
    yield
    login_limiter.reset()


@pytest.fixture
def app_client(monkeypatch):
    """In-memory auth + tracking DBs, both wired into the live app, with
    the bootstrap env vars set so the startup hook seeds an admin."""
    # Fresh auth DB.
    auth_db.reset_initialized()
    auth_conn = sqlite3.connect(":memory:", check_same_thread=False)
    auth_conn.row_factory = sqlite3.Row
    auth_conn.execute("PRAGMA foreign_keys = ON")
    auth_db._ensure_schema(auth_conn, ":memory:")
    auth_api.set_test_conn(auth_conn)
    monkeypatch.setattr(auth_db, "get_conn", lambda path=None: auth_conn)

    # Fresh tracking DB so /tracking endpoints don't reach the host's file.
    tracking_db.reset_initialized()
    tracking_conn = sqlite3.connect(":memory:", check_same_thread=False)
    tracking_conn.row_factory = sqlite3.Row
    tracking_conn.execute("PRAGMA foreign_keys = ON")
    tracking_db._ensure_schema(tracking_conn, ":memory:")
    tracking_api.set_test_conn(tracking_conn)
    monkeypatch.setattr(tracking_db, "get_conn", lambda path=None: tracking_conn)

    # Force the fail-closed code path so the test runs the real auth flow.
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", set())

    # Make the startup bootstrap actually create a user.
    monkeypatch.setenv("AUTH_BOOTSTRAP_USERNAME", "admin")
    monkeypatch.setenv("AUTH_BOOTSTRAP_PASSWORD", "initial-password")

    with TestClient(api.app) as client:
        # ``with TestClient`` triggers the lifespan handler, which calls
        # bootstrap_admin. Confirm it actually seeded.
        assert auth_service.get_user_by_username(auth_conn, "admin") is not None
        yield client

    auth_api.set_test_conn(None)
    tracking_api.set_test_conn(None)


def test_full_login_to_tracking_and_password_rotation(app_client):
    c = app_client

    # 1. Log in with the bootstrapped credentials.
    r = c.post("/auth/login", json={"username": "admin", "password": "initial-password"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]

    # 2. The bearer token gates a normally-protected tracking endpoint.
    r = c.get("/tracking/patients", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []  # fresh in-memory DB

    # Without the token, the same call is 401.
    assert c.get("/tracking/patients").status_code == 401

    # 3. Change the password using the session token.
    r = c.post(
        "/auth/password",
        json={
            "current_password": "initial-password",
            "new_password": "rotated-password-2026",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    new_token = r.json()["token"]
    assert new_token != token

    # 4. Old token no longer authenticates (revoked by the rotation).
    assert c.get(
        "/tracking/patients", headers={"Authorization": f"Bearer {token}"},
    ).status_code == 401

    # 5. New token still works.
    assert c.get(
        "/tracking/patients", headers={"Authorization": f"Bearer {new_token}"},
    ).status_code == 200

    # 6. Logging in with the OLD password is rejected.
    r = c.post(
        "/auth/login", json={"username": "admin", "password": "initial-password"},
    )
    assert r.status_code == 401

    # 7. Logging in with the new password works.
    r = c.post(
        "/auth/login", json={"username": "admin", "password": "rotated-password-2026"},
    )
    assert r.status_code == 200

    # 8. /auth/logout revokes the active token.
    r = c.post(
        "/auth/logout", headers={"Authorization": f"Bearer {new_token}"},
    )
    assert r.status_code == 200 and r.json()["revoked"] is True
    assert c.get(
        "/tracking/patients", headers={"Authorization": f"Bearer {new_token}"},
    ).status_code == 401


def test_bootstrap_is_idempotent_across_restarts(app_client, monkeypatch):
    """If the user changes AUTH_BOOTSTRAP_PASSWORD later, restarting must
    NOT silently rotate the live account — that's the seed-only-on-empty
    invariant. Verifies the bootstrap path is a no-op once a user exists."""
    c = app_client
    # First login confirms the seeded creds.
    r = c.post(
        "/auth/login", json={"username": "admin", "password": "initial-password"},
    )
    assert r.status_code == 200

    # Pretend the operator edits env to a "new" password and the app
    # restarts. We can't recreate the TestClient inside this test, but we
    # can call bootstrap_admin directly with the new env in place — that
    # is exactly what the lifespan handler does.
    monkeypatch.setenv("AUTH_BOOTSTRAP_PASSWORD", "ATTACKER-TAKEOVER")
    seeded = auth_service.bootstrap_admin(auth_db.get_conn())
    assert seeded is None  # no-op because admin already exists.

    # The original password still authenticates.
    r = c.post(
        "/auth/login", json={"username": "admin", "password": "initial-password"},
    )
    assert r.status_code == 200
    # The would-be takeover password does NOT.
    r = c.post(
        "/auth/login", json={"username": "admin", "password": "ATTACKER-TAKEOVER"},
    )
    assert r.status_code == 401
