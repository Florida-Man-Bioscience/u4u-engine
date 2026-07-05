"""
Tests for engine/tracking/pooling.py — empirical-Bayes hierarchical prior.
"""
import math
import random
from datetime import datetime, timedelta

import pytest

from engine.tracking import analysis, pooling, service

# ── Variance-components estimator on synthetic donor fits ──────────────────

def _donor(theta_hat: float, sigma: float, n_obs: int = 5) -> pooling.DonorFit:
    return pooling.DonorFit(
        patient_id=f"donor-{theta_hat:.3f}-{sigma:.3f}",
        theta_hat=theta_hat,
        sigma_theta=sigma,
        n_obs=n_obs,
    )


def test_pop_prior_is_none_below_min_donors():
    donors = [_donor(0.3, 0.05), _donor(0.4, 0.05)]
    assert pooling.estimate_population_prior(
        donors, peptide="X", biomarker="Y",
    ) is None


def test_pop_prior_mean_matches_average_theta():
    donors = [_donor(0.20, 0.05), _donor(0.30, 0.05), _donor(0.40, 0.05)]
    pp = pooling.estimate_population_prior(donors, peptide="X", biomarker="Y")
    assert pp is not None
    assert math.isclose(pp.mean_pct_change, 0.30, abs_tol=1e-9)
    assert pp.n_donors == 3


def test_pop_prior_subtracts_within_patient_variance():
    """When all observed spread between donor θ̂s is explained by their
    own fit uncertainty, σ_pop should be 0 — no real cohort spread to
    borrow from."""
    # σ²_total = 0.01 (sd 0.1); within-patient σ² = 0.01 too.
    donors = [
        _donor(0.20, 0.10),
        _donor(0.30, 0.10),
        _donor(0.40, 0.10),
    ]
    pp = pooling.estimate_population_prior(donors, peptide="X", biomarker="Y")
    assert pp is not None
    # Total Var ≈ 0.01, mean_within_var ≈ 0.01 → pop_var clamped to 0.
    assert pp.sd_pct_change == 0.0
    assert pp.raw_total_sd > 0


def test_pop_prior_recovers_population_sd_with_low_within_noise():
    """With sharply-fit donors (σ_within ≈ 0), the population SD should
    track the actual cross-donor SD of θ̂."""
    donors = [
        _donor(0.10, 0.005),
        _donor(0.30, 0.005),
        _donor(0.50, 0.005),
        _donor(0.40, 0.005),
        _donor(0.20, 0.005),
    ]
    pp = pooling.estimate_population_prior(donors, peptide="X", biomarker="Y")
    assert pp is not None
    # SD of [0.1, 0.3, 0.5, 0.4, 0.2] with n-1 = 0.158
    assert 0.13 < pp.sd_pct_change < 0.18


# ── Combine priors ─────────────────────────────────────────────────────────

def test_combine_no_population_returns_genetic_unchanged():
    m, s = pooling.combine_priors(
        genetic_mean=0.30, genetic_sd=0.10, population=None,
    )
    assert (m, s) == (0.30, 0.10)


def test_combine_with_population_shifts_toward_cohort():
    pop = pooling.PopulationPrior(
        peptide="X", biomarker="Y", n_donors=10,
        mean_pct_change=0.60, sd_pct_change=0.05,
        raw_total_sd=0.05, mean_within_sd=0.0,
    )
    m, s = pooling.combine_priors(
        genetic_mean=0.20, genetic_sd=0.10, population=pop,
    )
    # The population precision (1/0.05² = 400) is 4× the genetic
    # precision (1/0.10² = 100). Combined mean should sit closer to 0.60.
    assert 0.45 < m < 0.55
    # Combined SD shrinks below both.
    assert s < 0.05


def test_combine_with_degenerate_population_returns_genetic():
    pop = pooling.PopulationPrior(
        peptide="X", biomarker="Y", n_donors=5,
        mean_pct_change=0.40, sd_pct_change=0.0,  # within-noise ate the spread
        raw_total_sd=0.05, mean_within_sd=0.05,
    )
    m, s = pooling.combine_priors(
        genetic_mean=0.20, genetic_sd=0.10, population=pop,
    )
    assert (m, s) == (0.20, 0.10)


# ── End-to-end: donor collection + LOO + integration ───────────────────────

def _seed_cohort_on_peptide(conn, *, peptide_name, biomarker_name,
                            cohort_thetas, baseline=180.0, tau=3.0):
    """Helper: create a cohort of donors with known true θ for one
    (peptide, biomarker) and synthetic measurements that reflect it."""
    rng = random.Random(0)
    start = datetime(2026, 1, 1)
    weeks = [0.0, 2.0, 4.0, 8.0, 12.0]
    created = []
    for i, theta_true in enumerate(cohort_thetas):
        p = service.create_patient(conn, label=f"COHORT-{i:02d}")
        t = service.create_treatment(
            conn, patient_id=p.id, peptide_name=peptide_name,
            start_date=start.date().isoformat(),
            dose=2.0, dose_unit="mg",
        )
        for w in weeks:
            a = 1 - math.exp(-w / tau)
            val = baseline * (1 + theta_true * a) + rng.gauss(0, baseline * 0.04)
            measured_at = (start + timedelta(weeks=w)).date().isoformat()
            service.create_measurement(
                conn, patient_id=p.id, treatment_id=t.id,
                biomarker_name=biomarker_name, value=val,
                measured_at=measured_at, modality="hormone",
            )
        created.append(p)
    return created


def test_collect_donor_fits_excludes_target_patient(conn):
    """Leave-one-out: the patient we're predicting for must NOT show up in
    the donor set, or they'd borrow strength from themselves."""
    cohort = _seed_cohort_on_peptide(
        conn,
        peptide_name="CJC-1295",
        biomarker_name="Serum IGF-1",
        cohort_thetas=[0.40, 0.50, 0.60, 0.55],
    )
    target = cohort[0]
    donors = pooling.collect_donor_fits(
        conn,
        peptide_name="CJC-1295",
        biomarker_name="Serum IGF-1",
        tau_weeks=3.0,
        baseline_prior_mean=180.0,
        baseline_prior_sd=180.0 * 0.30,
        noise_pct=0.06,
        exclude_patient_id=target.id,
    )
    donor_ids = {d.patient_id for d in donors}
    assert target.id not in donor_ids
    assert len(donors) == 3


def test_predict_response_with_pooling_payload(conn):
    """predict_response should now expose the population_prior field with
    a non-null payload when enough donors exist."""
    cohort = _seed_cohort_on_peptide(
        conn,
        peptide_name="CJC-1295",
        biomarker_name="Serum IGF-1",
        cohort_thetas=[0.40, 0.50, 0.60, 0.55, 0.45],
    )
    target = cohort[0]
    pred = analysis.predict_response(
        conn, patient_id=target.id, peptide_name="CJC-1295",
        biomarker_name="Serum IGF-1",
    )
    pp = pred["population_prior"]
    assert pp is not None
    # 4 donors after LOO (5 in cohort minus the target).
    assert pp["n_donors"] == 4
    # Population mean should land near the cohort mean of the OTHER patients.
    other_mean = (0.50 + 0.60 + 0.55 + 0.45) / 4
    assert abs(pp["mean_pct_change"] - other_mean) < 0.10


def test_predict_response_without_cohort_returns_no_population_prior(conn):
    """Single patient = no donors → population_prior is None."""
    p = service.create_patient(conn, label="SOLO")
    t = service.create_treatment(
        conn, patient_id=p.id, peptide_name="CJC-1295",
        start_date="2026-01-01", dose=2.0, dose_unit="mg",
    )
    for date, val in [
        ("2026-01-01", 180.0),
        ("2026-02-01", 220.0),
        ("2026-03-01", 240.0),
        ("2026-04-01", 250.0),
    ]:
        service.create_measurement(
            conn, patient_id=p.id, treatment_id=t.id,
            biomarker_name="Serum IGF-1", value=val,
            measured_at=date, modality="hormone",
        )
    pred = analysis.predict_response(
        conn, patient_id=p.id, peptide_name="CJC-1295",
        biomarker_name="Serum IGF-1",
    )
    assert pred["population_prior"] is None


def test_pooling_shrinks_prior_toward_strong_responder_cohort(conn):
    """A patient whose only data point is the genetic prior (no
    measurements yet) should see their effective prior shift toward the
    cohort mean when the cohort is full of strong responders.

    The cohort thetas span 0.45–0.95 (mean ~0.70) — wide enough that the
    variance-components estimator can recover a positive σ_pop above
    the individual fit noise floor. A clinically uniform cohort would
    yield σ_pop ≈ 0 and pooling would correctly become a no-op.
    """
    _seed_cohort_on_peptide(
        conn,
        peptide_name="CJC-1295",
        biomarker_name="Serum IGF-1",
        cohort_thetas=[0.45, 0.60, 0.70, 0.80, 0.95],
    )
    # Predict for a *new* patient — no measurements at all.
    target = service.create_patient(conn, label="NEWBIE")
    service.create_treatment(
        conn, patient_id=target.id, peptide_name="CJC-1295",
        start_date="2026-01-01", dose=2.0, dose_unit="mg",
    )
    pred = analysis.predict_response(
        conn, patient_id=target.id, peptide_name="CJC-1295",
        biomarker_name="Serum IGF-1",
    )
    # No genetic profile → the analysis falls back to a panel prior centred
    # on the documented expected_pct (+0.55 for CJC-1295 / IGF-1). With
    # pooling on a strong-responder cohort, the posterior (= prior, since
    # likelihood is None) should shift toward the cohort mean of ~0.70.
    posterior_mean = pred["posterior"]["mean_pct_change"]
    panel_baseline_mean = 0.55
    cohort_mean = 0.70
    # Posterior should land between the panel prior and the cohort,
    # closer to the cohort than the panel prior because the cohort
    # precision is high.
    assert panel_baseline_mean < posterior_mean < 0.75, (
        f"posterior={posterior_mean:.3f} should sit between panel "
        f"({panel_baseline_mean}) and cohort ({cohort_mean})"
    )
    # population_prior is surfaced and reflects the cohort.
    pp = pred["population_prior"]
    assert pp is not None and pp["n_donors"] == 5
    assert 0.65 < pp["mean_pct_change"] < 0.75


# ── Correlation-aware fusion (genetics × cohort double-counting) ─────────────

def _pop(mean: float, sd: float, n: int = 5) -> pooling.PopulationPrior:
    return pooling.PopulationPrior(
        peptide="X", biomarker="Y", n_donors=n,
        mean_pct_change=mean, sd_pct_change=sd,
        raw_total_sd=sd, mean_within_sd=0.01,
    )


def test_combine_priors_rho0_matches_precision_addition():
    """ρ=0 (the default) reduces exactly to τ_g + τ_p precision-weighted fusion,
    and an explicit correlation=0.0 is byte-identical to the default."""
    pop = _pop(0.20, 0.10)
    m, s = pooling.combine_priors(genetic_mean=0.40, genetic_sd=0.10, population=pop)
    tau = 1 / 0.10 ** 2 + 1 / 0.10 ** 2
    assert math.isclose(s, math.sqrt(1 / tau), rel_tol=1e-12)
    assert math.isclose(m, 0.30, rel_tol=1e-12)  # equal σ → simple average
    m0, s0 = pooling.combine_priors(
        genetic_mean=0.40, genetic_sd=0.10, population=pop, correlation=0.0
    )
    assert (m0, s0) == (m, s)


def test_combine_priors_correlation_widens_equal_sigma():
    """At σ_g=σ_p=σ and correlation ρ, Var = σ²(1+ρ)/2 (closed form); higher
    assumed ρ ⇒ wider (less confident) fused σ, bounded by the single source."""
    sd = 0.12
    pop = _pop(0.30, sd)
    for rho in (0.0, 0.3, 0.6, 0.9):
        _, s = pooling.combine_priors(
            genetic_mean=0.30, genetic_sd=sd, population=pop, correlation=rho
        )
        assert math.isclose(s, sd * math.sqrt((1 + rho) / 2), rel_tol=1e-12)
    sds = [
        pooling.combine_priors(
            genetic_mean=0.30, genetic_sd=sd, population=pop, correlation=r
        )[1]
        for r in (0.0, 0.5, 0.9)
    ]
    assert sds[0] < sds[1] < sds[2]      # monotone in assumed correlation
    assert sds[2] <= sd                  # never worse than a single source
    assert math.isclose(sds[0], sd / math.sqrt(2), rel_tol=1e-12)  # ρ=0 anchor


def test_combine_priors_redundant_source_falls_back_to_more_precise():
    """When one source is far noisier than the other at high ρ, a BLUE weight
    goes ≤0 and we keep only the more precise source — no negative-weight
    extrapolation outside [μ_g, μ_p]."""
    pop = _pop(0.30, 0.60)   # σ_p=0.60 ≫ σ_g=0.05; ρ high ⇒ w_p = σ_g²−ρσ_gσ_p ≤ 0
    m, s = pooling.combine_priors(
        genetic_mean=0.10, genetic_sd=0.05, population=pop, correlation=0.9
    )
    assert (m, s) == (0.10, 0.05)        # genetics kept alone
    pop2 = _pop(0.25, 0.05)              # symmetric: genetics much noisier
    m2, s2 = pooling.combine_priors(
        genetic_mean=0.10, genetic_sd=0.60, population=pop2, correlation=0.9
    )
    assert (m2, s2) == (0.25, 0.05)      # population kept alone


def test_combine_priors_rho_clamped_below_one():
    """ρ is clamped below 1 so the fusion never hits the singular limit."""
    pop = _pop(0.30, 0.12)
    _, s = pooling.combine_priors(
        genetic_mean=0.30, genetic_sd=0.12, population=pop, correlation=1.5
    )
    assert 0 < s <= 0.12                 # finite, positive, ≤ single source
