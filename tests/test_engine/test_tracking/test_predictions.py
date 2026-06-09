import random

from engine.tracking import analysis, service
from engine.tracking.genetics import generate_synthetic_profile
from engine.tracking.seed import seed


def test_predict_response_returns_full_payload(conn):
    """End-to-end: seed → predict_response gives prior + likelihood + posterior
    + a non-empty posterior predictive curve."""
    seed(conn, rng=random.Random(42), n_patients=5)
    # Pick a patient with at least one treatment + a biomarker.
    row = conn.execute(
        """SELECT p.id AS pid, t.peptide_name AS pep, m.biomarker_name AS bm
           FROM patients p
           JOIN treatments t ON t.patient_id = p.id
           JOIN measurements m ON m.patient_id = p.id
           LIMIT 1"""
    ).fetchone()
    assert row is not None
    result = analysis.predict_response(
        conn, patient_id=row["pid"], peptide_name=row["pep"], biomarker_name=row["bm"],
    )
    assert result["prior"] is not None
    assert result["likelihood"] is not None
    assert result["posterior"]["mean_pct_change"] is not None
    assert result["posterior_predictive"]["points"]
    assert result["prior_predictive"]["points"]


def test_predict_response_without_treatment_falls_back_to_prior(conn):
    """If the patient has a profile but no treatment for the peptide, the
    posterior should equal the prior (no likelihood)."""
    p = service.create_patient(conn, label="P-001")
    profile = generate_synthetic_profile(random.Random(0))
    service.set_genetic_profile(conn, p.id, profile.to_json())
    result = analysis.predict_response(
        conn, patient_id=p.id, peptide_name="CJC-1295", biomarker_name="Serum IGF-1",
    )
    assert result["likelihood"] is None
    assert result["prior"] is not None
    # Posterior mean should match the prior mean exactly.
    assert result["posterior"]["mean_pct_change"] == result["prior"]["mean_pct_change"]


def test_predict_response_without_genetics_uses_flat_prior(conn):
    """No genetic profile → prior is (0, 0.3) and posterior follows likelihood."""
    p = service.create_patient(conn, label="P-002")
    t = service.create_treatment(
        conn, patient_id=p.id, peptide_name="CJC-1295",
        start_date="2026-01-01", dose=2.0, dose_unit="mg",
    )
    # Inject a clear +30% trajectory
    for date, val in [
        ("2026-01-02", 180.0),
        ("2026-01-15", 200.0),
        ("2026-02-01", 220.0),
        ("2026-03-01", 234.0),
    ]:
        service.create_measurement(
            conn, patient_id=p.id, treatment_id=t.id,
            biomarker_name="Serum IGF-1", value=val, measured_at=date,
            modality="hormone", unit="ng/mL",
        )
    result = analysis.predict_response(
        conn, patient_id=p.id, peptide_name="CJC-1295", biomarker_name="Serum IGF-1",
    )
    assert result["prior"] is None
    post = result["posterior"]["mean_pct_change"]
    assert 0.1 < post < 0.6  # genuinely positive change


def test_predict_response_genetics_visibly_shifts_prior(conn):
    """Two patients with different genetic profiles should yield different
    priors for the same peptide."""
    p1 = service.create_patient(conn, label="A")
    p2 = service.create_patient(conn, label="B")
    rng1 = random.Random(1)
    rng2 = random.Random(99)
    service.set_genetic_profile(conn, p1.id, generate_synthetic_profile(rng1).to_json())
    service.set_genetic_profile(conn, p2.id, generate_synthetic_profile(rng2).to_json())
    r1 = analysis.predict_response(
        conn, patient_id=p1.id, peptide_name="CJC-1295", biomarker_name="Serum IGF-1",
    )
    r2 = analysis.predict_response(
        conn, patient_id=p2.id, peptide_name="CJC-1295", biomarker_name="Serum IGF-1",
    )
    assert r1["prior"]["mean_pct_change"] != r2["prior"]["mean_pct_change"]
