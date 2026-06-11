"""
Tests for the /auth/* router and the api.py middleware's new session-token
path. Skipped in the nix dev shell where fastapi isn't installed.
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


@pytest.fixture
def auth_conn(monkeypatch):
    """Inject an in-memory auth DB into the router AND the middleware.

    ``check_same_thread=False`` is required because the FastAPI TestClient
    serves requests from a worker thread different from the one that
    created the connection.
    """
    auth_db.reset_initialized()
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    auth_db._ensure_schema(conn, ":memory:")
    auth_api.set_test_conn(conn)
    # Middleware reads from auth_db.get_conn(); monkeypatch it to our memory DB.
    monkeypatch.setattr(auth_db, "get_conn", lambda path=None: conn)
    yield conn
    auth_api.set_test_conn(None)
    conn.close()


@pytest.fixture
def client():
    return TestClient(api.app)


def test_login_succeeds_with_correct_credentials(monkeypatch, auth_conn, client):
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", set())
    auth_service.create_user(auth_conn, username="alice", password="hunter2")
    r = client.post("/auth/login", json={"username": "alice", "password": "hunter2"})
    assert r.status_code == 200
    body = r.json()
    assert body["token"]
    assert body["user"]["username"] == "alice"


def test_login_rejects_bad_credentials(monkeypatch, auth_conn, client):
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", set())
    auth_service.create_user(auth_conn, username="alice", password="hunter2")
    r = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
    assert r.status_code == 401


def test_session_token_authorises_protected_endpoint(monkeypatch, auth_conn, client):
    """The whole point of the new auth path: a session token from /auth/login
    should pass the middleware on a normally-protected route."""
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", set())
    auth_service.create_user(auth_conn, username="alice", password="hunter2")

    # First, anonymous request fails because no creds are present.
    assert client.get("/jobs/none").status_code == 401

    # Log in, then retry with the token.
    token = client.post(
        "/auth/login", json={"username": "alice", "password": "hunter2"},
    ).json()["token"]
    r = client.get("/jobs/none", headers={"Authorization": f"Bearer {token}"})
    # Past auth — 404 because the job doesn't exist.
    assert r.status_code == 404


def test_api_key_still_works_alongside_session_tokens(monkeypatch, auth_conn, client):
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", {"service-secret"})
    r = client.get("/jobs/none", headers={"X-API-Key": "service-secret"})
    assert r.status_code == 404  # past auth


def test_logout_revokes_token(monkeypatch, auth_conn, client):
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", set())
    auth_service.create_user(auth_conn, username="alice", password="hunter2")
    token = client.post(
        "/auth/login", json={"username": "alice", "password": "hunter2"},
    ).json()["token"]
    # Logout returns 200 with revoked=True.
    r = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200 and r.json()["revoked"] is True
    # The same token is now rejected.
    r2 = client.get("/jobs/none", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 401


def test_me_returns_user_for_session_token(monkeypatch, auth_conn, client):
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", set())
    auth_service.create_user(auth_conn, username="alice", password="hunter2")
    token = client.post(
        "/auth/login", json={"username": "alice", "password": "hunter2"},
    ).json()["token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["via"] == "session"
    assert body["user"]["username"] == "alice"


def test_me_with_api_key_returns_sentinel(monkeypatch, auth_conn, client):
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", {"service-secret"})
    r = client.get("/auth/me", headers={"X-API-Key": "service-secret"})
    assert r.status_code == 200
    body = r.json()
    assert body["via"] == "api_key"
    assert body["user"] is None


def test_fails_closed_when_nothing_configured(monkeypatch, auth_conn, client):
    """No API keys AND no users → 503 (truthful: no way to authenticate)."""
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", set())
    assert client.get("/jobs/none").status_code == 503


def test_fails_with_401_when_users_exist_but_no_credentials(
    monkeypatch, auth_conn, client,
):
    """Users exist → server *can* authenticate, just not this request → 401, not 503."""
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", set())
    auth_service.create_user(auth_conn, username="alice", password="hunter2")
    assert client.get("/jobs/none").status_code == 401
