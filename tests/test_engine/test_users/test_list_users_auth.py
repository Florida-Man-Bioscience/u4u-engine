# tests/test_engine/test_users/test_list_users_auth.py
"""
FIX 2 (whole-branch review): GET /users returned every user's PII
(username/email) with no auth dependency at all. It is now gated:
allowed in dev-bypass mode (no OIDC configured) or for staff callers
(cluster-Authentik issuer); 403 for an authenticated end-user caller
whose issuer is the dedicated end-user IdP.

Uses the full FastAPI app (api.app) via TestClient since that's where
the /users router is mounted and where dev-bypass/OIDC mode is
resolved end-to-end. The autouse isolated_users_db fixture in this
directory's conftest.py redirects the users DB to a per-test tmp file.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import api
from engine.users import oidc
from engine.users.deps import required_user
from engine.users.models import User


def _user(issuer: str) -> User:
    return User(
        id="u-1", authentik_uid="sub-1", username="enduser", email="e@x.co",
        full_name=None, groups=None, issuer=issuer,
        created_at="t", last_seen_at="t", disabled_at=None,
    )


def test_list_users_200_in_dev_bypass_mode(monkeypatch):
    # Default test environment: no U4U_OIDC_* configured -> dev-bypass.
    with TestClient(api.app) as c:
        resp = c.get("/users")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_users_403_for_non_staff_end_user(monkeypatch):
    monkeypatch.setattr(
        "engine.users.api.oidc.oidc_settings",
        lambda: oidc.OidcSettings(
            issuer="https://enduser-idp.example/app",
            audience="u4u-web",
            jwks_url="https://enduser-idp.example/app/jwks",
        ),
    )
    with TestClient(api.app) as c:
        c.app.dependency_overrides[required_user] = lambda: _user(
            "https://enduser-idp.example/app"
        )
        try:
            resp = c.get("/users")
        finally:
            c.app.dependency_overrides.pop(required_user, None)
    assert resp.status_code == 403


def test_list_users_200_for_staff_cluster_authentik_user(monkeypatch):
    monkeypatch.setattr(
        "engine.users.api.oidc.oidc_settings",
        lambda: oidc.OidcSettings(
            issuer="https://enduser-idp.example/app",
            audience="u4u-web",
            jwks_url="https://enduser-idp.example/app/jwks",
        ),
    )
    with TestClient(api.app) as c:
        c.app.dependency_overrides[required_user] = lambda: _user("cluster-authentik")
        try:
            resp = c.get("/users")
        finally:
            c.app.dependency_overrides.pop(required_user, None)
    assert resp.status_code == 200
