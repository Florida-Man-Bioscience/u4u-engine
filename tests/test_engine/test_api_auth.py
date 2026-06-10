"""
Tests for API authentication (fail-closed) on api.py.
"""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402
import api  # noqa: E402


def _client():
    return TestClient(api.app)


def test_health_is_open(monkeypatch):
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", {"secret"})
    with _client() as c:
        assert c.get("/health").status_code == 200


def test_protected_endpoint_requires_valid_key(monkeypatch):
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", {"secret"})
    with _client() as c:
        # No key → 401
        assert c.get("/jobs/none").status_code == 401
        # Wrong key → 401
        assert c.get("/jobs/none", headers={"X-API-Key": "nope"}).status_code == 401
        # Valid bearer key → passes auth (404 because the job doesn't exist)
        assert c.get("/jobs/none", headers={"Authorization": "Bearer secret"}).status_code == 404
        # Valid X-API-Key → passes auth
        assert c.get("/jobs/none", headers={"X-API-Key": "secret"}).status_code == 404


def test_fails_closed_when_no_keys_configured(monkeypatch):
    monkeypatch.setattr(api, "ALLOW_INSECURE_NO_AUTH", False)
    monkeypatch.setattr(api, "API_KEYS", set())
    with _client() as c:
        assert c.get("/jobs/none").status_code == 503
