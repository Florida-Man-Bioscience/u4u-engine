import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from engine.tracking import db  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    # The migrated tracking API opens its own connection per request via
    # get_conn() — there is no shared injected connection anymore. So the test
    # DB must be a real file that persists across those per-request
    # connections; an in-memory DB would hand each request a separate empty
    # database. Point the tracking default path at a temp file and force the
    # SQLite branch so the test stays hermetic regardless of any DATABASE_URL
    # in the environment.
    monkeypatch.setattr(db, "_DEFAULT_PATH", tmp_path / "tracking.db")
    monkeypatch.setattr(db, "_is_postgres_configured", lambda path: False)
    db.reset_initialized()
    from api import app
    with TestClient(app) as c:
        yield c


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


def test_create_patient_from_job_carries_real_priors(client):
    """End-to-end: drop a finished /analyze job into the job store,
    POST /tracking/patients/from-job/<id>, and confirm we get back a
    patient with a non-synthetic genetic profile + a list of peptides
    that have evidence-backed signal for THIS patient's genotypes."""
    import uuid

    import api as root_api

    # The job must be owned by the same (dev-bypass) user the TestClient
    # authenticates as, or create_patient_from_job's ownership guard 404s
    # it — get that id the same way the API does, by making an
    # authenticated call and reading back who it stamped as owner.
    owner_id = client.post("/tracking/patients", json={"label": "owner-probe"}).json()[
        "created_by_user_id"
    ]

    job_id = str(uuid.uuid4())
    root_api._jobs[job_id] = {
        "status": "done",
        "filename": "alice.vcf.gz",
        "created_by_user_id": owner_id,
        "results": {
            # Mix of real catalog rsIDs and a noise variant. The TCF7L2
            # T allele should produce a non-zero Semaglutide effect.
            "variants": [
                {"rsid": "rs7903146", "alt": "T", "zygosity": "heterozygous",
                 "genes": ["TCF7L2"]},
                {"rsid": "rs6923761", "alt": "A", "zygosity": "homozygous_alt",
                 "genes": ["GLP1R"]},
                {"rsid": "rs99999999", "alt": "C", "zygosity": "het",
                 "genes": ["UNKNOWN"]},
            ],
            "peptide_recommendations": {
                "recommendations": [
                    {"peptide_name": "BPC-157", "category": "regenerative",
                     "predicted_tier": "Likely Reduced",
                     "prediction_description": "Reduced pathway activity."},
                    {"peptide_name": "Semaglutide", "category": "glp1",
                     "predicted_tier": "Strong Fit",
                     "prediction_description": "Strong T2D risk profile."},
                    {"peptide_name": "MOTS-c", "category": "metabolic",
                     "predicted_tier": "Possible Fit",
                     "prediction_description": "Possible metabolic match."},
                ]
            },
        },
    }
    try:
        r = client.post(f"/tracking/patients/from-job/{job_id}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["source"] == f"job:{job_id}"
        assert body["patient"]["label"] == "Patient from alice.vcf.gz"
        # The catalog covers GLP-1 RAs; the patient carries real signal.
        assert "Semaglutide" in body["peptides_with_patient_signal"]
        assert "Liraglutide" in body["peptides_with_patient_signal"]
        # Variant evidence list should carry citations for the carried
        # variants only (the off-catalog noise variant is excluded).
        carried_rsids = {v["rsid"] for v in body["variants_carried"]}
        assert "rs7903146" in carried_rsids
        assert "rs6923761" in carried_rsids
        assert "rs99999999" not in carried_rsids
        for v in body["variants_carried"]:
            assert v["evidence"] is not None
            assert v["evidence"]["pmid"]
            assert v["evidence"]["pharmgkb_level"] in {"1A", "1B", "2A", "2B", "3"}

        # Profile should now be queryable via the genetics endpoint.
        gen = client.get(f"/tracking/patients/{body['patient']['id']}/genetics")
        assert gen.status_code == 200
        assert gen.json()["source"] == f"job:{job_id}"

        # Engine recommendations should come back ranked: Strong Fit
        # first, Possible Fit next, Likely Reduced last. Semaglutide
        # (Strong Fit AND has patient signal) must lead.
        recs = body["engine_recommendations"]
        assert [r["peptide_name"] for r in recs] == [
            "Semaglutide", "MOTS-c", "BPC-157",
        ]
        sema = recs[0]
        assert sema["has_pharmgkb_evidence"] is True
        assert sema["has_patient_signal"] is True
        bpc = recs[2]
        assert bpc["has_pharmgkb_evidence"] is False
    finally:
        root_api._jobs.pop(job_id, None)


def test_create_patient_from_job_404_when_job_missing(client):
    r = client.post("/tracking/patients/from-job/nonexistent")
    assert r.status_code == 404


def test_create_patient_from_job_404_when_job_not_done(client):
    import uuid

    import api as root_api

    job_id = str(uuid.uuid4())
    root_api._jobs[job_id] = {"status": "running", "filename": "x.vcf"}
    try:
        r = client.post(f"/tracking/patients/from-job/{job_id}")
        assert r.status_code == 404
    finally:
        root_api._jobs.pop(job_id, None)


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
