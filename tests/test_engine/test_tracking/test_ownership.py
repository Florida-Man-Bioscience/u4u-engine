"""
tests/test_engine/test_tracking/test_ownership.py
==================================================
Closes the IDOR that motivated the end-user-auth feature: every
per-patient tracking endpoint must 404 for a caller who doesn't own the
patient, and list endpoints must be scoped to the caller.

DB isolation (both engine/users/db.py and engine/tracking/db.py) is
handled by the autouse ``_isolate_dbs`` fixture in this directory's
conftest.py — these tests run against per-test tmp SQLite files, never
the real data/users.db or data/biomarker_tracking.db.
"""
import api
from fastapi.testclient import TestClient


def test_list_patients_scoped_to_owner():
    with TestClient(api.app) as c:
        r = c.post("/tracking/patients", json={"label": "MINE"})
        pid = r.json()["id"]
        listed = c.get("/tracking/patients").json()
        assert any(p["id"] == pid for p in listed)


def test_list_patients_excludes_foreign_owner():
    """GET /tracking/patients must be scoped to the caller — a patient
    owned by someone else must never appear in the list. This is the
    exact IDOR (mass patient-list leak) the owns() filter in
    list_patients() closes; deleting that filter must fail this test."""
    from engine.tracking import db as tdb, service

    with tdb.get_conn() as conn:
        foreign = service.create_patient(conn, label="THEIRS",
                                          created_by_user_id="someone-else")
    with TestClient(api.app) as c:
        r = c.post("/tracking/patients", json={"label": "MINE"})
        pid = r.json()["id"]
        listed = c.get("/tracking/patients").json()
        listed_ids = {p["id"] for p in listed}
        assert pid in listed_ids
        assert foreign.id not in listed_ids


def test_foreign_patient_is_404():
    # Seed a patient owned by someone else directly via the service.
    from engine.tracking import db as tdb, service
    with tdb.get_conn() as conn:
        other = service.create_patient(conn, label="THEIRS",
                                        created_by_user_id="someone-else")
    with TestClient(api.app) as c:
        assert c.get(f"/tracking/patients/{other.id}").status_code == 404
        assert c.get(f"/tracking/patients/{other.id}/predictions",
                     params={"peptide": "BPC-157", "biomarker": "CRP"}).status_code == 404


def test_foreign_patient_delete_is_404():
    from engine.tracking import db as tdb, service
    with tdb.get_conn() as conn:
        other = service.create_patient(conn, label="THEIRS",
                                        created_by_user_id="someone-else")
    with TestClient(api.app) as c:
        assert c.delete(f"/tracking/patients/{other.id}").status_code == 404
    # Still there — the guard fired before the delete.
    with tdb.get_conn() as conn:
        assert service.get_patient(conn, other.id) is not None


def test_foreign_patient_treatments_are_404():
    from engine.tracking import db as tdb, service
    with tdb.get_conn() as conn:
        other = service.create_patient(conn, label="THEIRS",
                                        created_by_user_id="someone-else")
    with TestClient(api.app) as c:
        assert c.get(f"/tracking/patients/{other.id}/treatments").status_code == 404
        r = c.post(
            f"/tracking/patients/{other.id}/treatments",
            json={"peptide_name": "BPC-157", "start_date": "2026-01-01"},
        )
        assert r.status_code == 404


def test_foreign_patient_measurements_are_404():
    from engine.tracking import db as tdb, service
    with tdb.get_conn() as conn:
        other = service.create_patient(conn, label="THEIRS",
                                        created_by_user_id="someone-else")
    with TestClient(api.app) as c:
        assert c.get(f"/tracking/patients/{other.id}/measurements").status_code == 404
        r = c.post(
            "/tracking/measurements",
            json={"patient_id": other.id, "biomarker_name": "CRP",
                  "value": 1.0, "measured_at": "2026-01-01"},
        )
        assert r.status_code == 404
        r = c.post(
            "/tracking/measurements/bulk",
            json={"measurements": [
                {"patient_id": other.id, "biomarker_name": "CRP",
                 "value": 1.0, "measured_at": "2026-01-01"},
            ]},
        )
        assert r.status_code == 404
        csv = f"patient_id,biomarker_name,value,measured_at\n{other.id},CRP,1.0,2026-01-01\n"
        r = c.post(
            "/tracking/measurements/csv",
            files={"file": ("m.csv", csv, "text/csv")},
        )
        assert r.status_code == 404


def test_foreign_patient_genetics_are_404():
    from engine.tracking import db as tdb, service
    with tdb.get_conn() as conn:
        other = service.create_patient(conn, label="THEIRS",
                                        created_by_user_id="someone-else")
    with TestClient(api.app) as c:
        assert c.get(f"/tracking/patients/{other.id}/genetics").status_code == 404
        assert c.post(f"/tracking/patients/{other.id}/genetics/synthetic").status_code == 404
        assert c.get(f"/tracking/patients/{other.id}/priors").status_code == 404


def test_null_owner_patient_is_404():
    """A NULL owner (e.g. a legacy row) is treated the same as someone
    else's — never accessible, never leaked as existing."""
    from engine.tracking import db as tdb, service
    with tdb.get_conn() as conn:
        other = service.create_patient(conn, label="ORPHAN", created_by_user_id=None)
    with TestClient(api.app) as c:
        assert c.get(f"/tracking/patients/{other.id}").status_code == 404


def test_create_patient_from_job_guards_job_owner():
    import uuid

    job_id = str(uuid.uuid4())
    api._jobs[job_id] = {
        "status": "done",
        "filename": "x.vcf",
        "created_by_user_id": "someone-else",
        "results": {"variants": [], "peptide_recommendations": {}},
    }
    try:
        with TestClient(api.app) as c:
            r = c.post(f"/tracking/patients/from-job/{job_id}")
            assert r.status_code == 404
    finally:
        api._jobs.pop(job_id, None)


def test_seed_endpoint_403_when_oidc_configured(monkeypatch):
    """POST /tracking/seed is dev/demo-only: gated behind required_user
    AND dev-bypass (no OIDC configured). In "configured" (prod-shaped)
    mode it must 403 even for an authenticated caller."""
    from engine.tracking import api as tracking_api
    from engine.users.models import User
    from engine.users.deps import required_user

    fake_user = User(
        id="u1", authentik_uid="u1", username="u1", email=None, full_name=None,
        groups=None, issuer="https://id.example", created_at="", last_seen_at="",
        disabled_at=None,
    )
    monkeypatch.setattr(tracking_api.oidc, "oidc_settings", lambda: object())
    api.app.dependency_overrides[required_user] = lambda: fake_user
    try:
        with TestClient(api.app) as c:
            r = c.post("/tracking/seed", json={"patients": 1})
            assert r.status_code == 403
    finally:
        api.app.dependency_overrides.pop(required_user, None)
