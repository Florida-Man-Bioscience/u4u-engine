import pytest

import api
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolate_users_db(tmp_path, monkeypatch):
    from engine.users import db as _udb
    monkeypatch.setattr(_udb, "_DEFAULT_PATH", tmp_path / "users.db")
    _udb.reset_initialized()
    yield
    _udb.reset_initialized()


def _seed_job(owner):
    jid = "job-" + (owner or "none")
    with api._jobs_lock:
        api._jobs[jid] = {
            "status": "complete", "progress": {"step": "done", "pct": 100},
            "count": 0, "results": {"variants": []}, "partial_results": [],
            "error": None, "filename": "f.vcf", "file_size": 1,
            "created_at": "2026-01-01T00:00:00+00:00", "started_at": None,
            "finished_at": None, "created_by_user_id": owner,
        }
    return jid


def test_owner_can_read_own_job(monkeypatch):
    with TestClient(api.app) as c:
        # discover the dev user's id, then own a job as them
        me = c.get("/users/me").json()
        jid = _seed_job(me["id"])
        assert c.get(f"/jobs/{jid}").status_code == 200


def test_other_users_job_is_404(monkeypatch):
    with TestClient(api.app) as c:
        jid = _seed_job("someone-else")
        assert c.get(f"/jobs/{jid}").status_code == 404


def test_null_owner_job_is_404(monkeypatch):
    with TestClient(api.app) as c:
        jid = _seed_job(None)
        assert c.get(f"/jobs/{jid}").status_code == 404


def test_public_job_does_not_leak_owner(monkeypatch):
    with TestClient(api.app) as c:
        me = c.get("/users/me").json()
        jid = _seed_job(me["id"])
        body = c.get(f"/jobs/{jid}").json()
        assert "created_by_user_id" not in body
