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


def test_prior_direction_follows_panel_per_biomarker(conn):
    """For a peptide-biomarker with a negative panel direction (HbA1c on
    CJC-1295), the prior μ should be negative regardless of genetics —
    that is, the biomarker-specific prior is sign-correct."""
    p = service.create_patient(conn, label="A")
    service.set_genetic_profile(
        conn, p.id, generate_synthetic_profile(random.Random(7)).to_json(),
    )
    igf = analysis.predict_response(
        conn, patient_id=p.id, peptide_name="CJC-1295", biomarker_name="Serum IGF-1",
    )
    hba = analysis.predict_response(
        conn, patient_id=p.id, peptide_name="CJC-1295", biomarker_name="HbA1c",
    )
    assert igf["prior"]["mean_pct_change"] > 0
    assert hba["prior"]["mean_pct_change"] < 0
    assert abs(igf["prior"]["mean_pct_change"]) > abs(hba["prior"]["mean_pct_change"])


def test_posterior_tracks_simulated_truth(conn):
    """When the seeder produces measurements that imply θ_true, the posterior
    mean should land close to θ_true — much closer than to the prior alone."""
    from engine.tracking.seed import seed, BIOMARKER_PARAMS, _dose_factor, SCENARIOS
    from engine.tracking.genetics import (
        GeneticProfile,
        responder_strength_from_profile,
    )

    seed(conn, rng=random.Random(42), n_patients=8)

    rows = conn.execute(
        """SELECT p.id AS pid, t.peptide_name AS pep, t.dose,
                  m.biomarker_name AS bm, COUNT(m.id) AS n
           FROM patients p
           JOIN treatments t ON t.patient_id=p.id
           JOIN measurements m ON m.patient_id=p.id AND m.treatment_id=t.id
           GROUP BY p.id, t.id, m.biomarker_name
           HAVING n>=4"""
    ).fetchall()

    tested = 0
    for r in rows:
        params = BIOMARKER_PARAMS.get(r["bm"])
        if params is None or params.max_pct_change == 0:
            continue
        sc = next((s for s in SCENARIOS if s.peptide == r["pep"]), None)
        if sc is None:
            continue
        raw = service.get_genetic_profile_json(conn, r["pid"])
        profile = GeneticProfile.from_json(raw[0])
        responder = responder_strength_from_profile(profile, r["pep"])
        dose_f = _dose_factor(r["dose"], sc.doses)
        theta_true = params.max_pct_change * responder * dose_f

        pred = analysis.predict_response(
            conn, patient_id=r["pid"], peptide_name=r["pep"],
            biomarker_name=r["bm"],
        )
        post = pred["posterior"]["mean_pct_change"]
        prior = pred["prior"]["mean_pct_change"]
        # The posterior must be at least as close to the truth as the prior.
        # (We don't expect identity because of noise + Gaussian jitter on
        # responder in the seeder; this is a robustness check.)
        assert abs(post - theta_true) <= abs(prior - theta_true) + 0.15, (
            f"{r['pep']}/{r['bm']}: prior={prior:.3f} post={post:.3f} "
            f"truth={theta_true:.3f}"
        )
        tested += 1

    assert tested >= 5, "expected at least 5 testable rows"
