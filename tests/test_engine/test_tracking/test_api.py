import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from engine.tracking import db, get_conn  # noqa: E402
from engine.tracking.api import set_test_conn  # noqa: E402


@pytest.fixture
def client():
    db.reset_initialized()
    conn = get_conn(":memory:")
    set_test_conn(conn)
    from api import app
    with TestClient(app) as c:
        yield c
    set_test_conn(None)
    conn.close()


def test_create_patient_and_treatment_and_measurement(client):
    r = client.post("/tracking/patients", json={"label": "P-001", "sex": "M", "birth_year": 1990})
    assert r.status_code == 200, r.text
    pid = r.json()["id"]

    r = client.post(
        f"/tracking/patients/{pid}/treatments",
        json={"peptide_name": "BPC-157", "start_date": "2026-01-01",
              "dose": 250, "dose_unit": "mcg"},
    )
    assert r.status_code == 200
    tid = r.json()["id"]

    r = client.post(
        "/tracking/measurements",
        json={"patient_id": pid, "treatment_id": tid,
              "biomarker_name": "Pain VAS", "value": 6.0,
              "measured_at": "2026-01-01"},
    )
    assert r.status_code == 200

    r = client.get(f"/tracking/patients/{pid}/measurements")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_cohort_endpoint_returns_expected_direction(client):
    r = client.post("/tracking/patients", json={"label": "A"})
    pid = r.json()["id"]
    client.post(
        f"/tracking/patients/{pid}/treatments",
        json={"peptide_name": "CJC-1295", "start_date": "2026-01-01",
              "dose": 2.0, "dose_unit": "mg"},
    )
    for date, val in [("2026-01-02", 180.0), ("2026-01-29", 230.0), ("2026-02-26", 270.0)]:
        client.post(
            "/tracking/measurements",
            json={"patient_id": pid, "biomarker_name": "Serum IGF-1",
                  "value": val, "measured_at": date, "unit": "ng/mL"},
        )
    r = client.get("/tracking/cohort", params={"peptide": "CJC-1295", "biomarker": "Serum IGF-1"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["n_patients"] == 1
    assert body["expected"]["direction"] == "increase"
    assert body["trajectories"]


def test_seed_endpoint_is_idempotent(client):
    # First call: empty DB → seeds.
    r = client.post("/tracking/seed", json={"patients": 4})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["patients"] == 4
    assert body["skipped"] == 0
    assert body["treatments"] > 0
    assert body["measurements"] > 0

    # Second call: already seeded → skips.
    r = client.post("/tracking/seed", json={"patients": 4})
    assert r.status_code == 200
    body = r.json()
    assert body["skipped"] == 4
    assert body["patients"] == 0


def test_seed_force_wipes_and_reseeds(client):
    r = client.post("/tracking/seed", json={"patients": 3})
    assert r.json()["patients"] == 3
    # force=true should wipe then reseed with a different count
    r = client.post("/tracking/seed", json={"patients": 5, "force": True})
    assert r.status_code == 200, r.text
    assert r.json()["patients"] == 5
    # Verify the GET reflects the new count.
    listed = client.get("/tracking/patients").json()
    assert len(listed) == 5


def test_csv_upload(client):
    r = client.post("/tracking/patients", json={"label": "C"})
    pid = r.json()["id"]
    csv = (
        "patient_id,biomarker_name,value,measured_at,unit\n"
        f"{pid},Serum IGF-1,210,2026-01-01,ng/mL\n"
        f"{pid},Serum IGF-1,250,2026-02-01,ng/mL\n"
    )
    r = client.post(
        "/tracking/measurements/csv",
        files={"file": ("m.csv", csv, "text/csv")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["created"] == 2
