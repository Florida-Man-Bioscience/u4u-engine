"""
Tests for the HealthKit proxy → biomarker-observation bridge and the
per-observation noise-scale mechanism it rides on.

Covers:
  * body mass in kg and lb → correct 'Body weight' (kg) observations,
  * GLP-1 peptide → class-qualified 'Body weight (GLP-1 RA)' binding,
  * resting heart rate mapping,
  * daily-median aggregation,
  * no-mapping / no-subject → [] and an unchanged prediction,
  * wearable observations *widen* (do not falsely tighten) the posterior,
  * noise_scales=None is byte-for-byte identical to all-ones (the invariant
    that keeps the clinical-only path — and the calibration backtest —
    unchanged).
"""
from __future__ import annotations

import random
from uuid import uuid4

import pytest

from engine.healthkit import db as hk_db
from engine.tracking import analysis, healthkit_bridge, service
from engine.tracking.bayes import joint_fit_likelihood
from engine.tracking.genetics import generate_synthetic_profile
from engine.tracking.healthkit_identity import link_subject_to_patient

_KG_PER_LB = 0.45359237


# ── Fixtures / helpers ──────────────────────────────────────────────────────

@pytest.fixture
def hk_conn():
    hk_db.reset_initialized()
    with hk_db.get_conn(":memory:") as c:
        yield c


def _add_sample(conn, subject_id, hk_type, value, unit, start_iso):
    conn.execute(
        "INSERT INTO healthkit_subjects (id) VALUES (?) ON CONFLICT (id) DO NOTHING",
        (subject_id,),
    )
    conn.execute(
        """INSERT INTO healthkit_samples
             (sample_uuid, subject_id, sample_class, type_identifier,
              value, unit, start_time, end_time)
           VALUES (?,?,?,?,?,?,?,?)""",
        (str(uuid4()), subject_id, "quantity", hk_type, value, unit,
         start_iso, start_iso),
    )
    conn.commit()


# ── Unit conversion + mapping ───────────────────────────────────────────────

def test_bodymass_kg_maps_to_body_weight(hk_conn):
    link_subject_to_patient(hk_conn, "subj-1", "P-1")
    _add_sample(hk_conn, "subj-1", "HKQuantityTypeIdentifierBodyMass",
                78.0, "kg", "2026-01-08T09:00:00Z")
    obs = healthkit_bridge.healthkit_observations(
        None, "P-1", "AOD-9604", "Body weight", "2026-01-01T00:00:00Z",
        hk_conn=hk_conn,
    )
    assert len(obs) == 1
    weeks, value = obs[0]
    assert value == pytest.approx(78.0)
    # 2026-01-01T00:00 → 2026-01-08T09:00 = 7 days 9 h ≈ 1.05 weeks.
    assert weeks == pytest.approx(7.375 / 7)


def test_bodymass_lb_converts_to_kg(hk_conn):
    link_subject_to_patient(hk_conn, "subj-2", "P-2")
    _add_sample(hk_conn, "subj-2", "HKQuantityTypeIdentifierBodyMass",
                180.0, "lb", "2026-01-08T09:00:00Z")
    obs = healthkit_bridge.healthkit_observations(
        None, "P-2", "AOD-9604", "Body weight", "2026-01-01T00:00:00Z",
        hk_conn=hk_conn,
    )
    assert len(obs) == 1
    assert obs[0][1] == pytest.approx(180.0 * _KG_PER_LB)


def test_unrecognized_mass_unit_is_skipped(hk_conn):
    link_subject_to_patient(hk_conn, "subj-u", "P-u")
    _add_sample(hk_conn, "subj-u", "HKQuantityTypeIdentifierBodyMass",
                78.0, "furlongs", "2026-01-08T09:00:00Z")
    obs = healthkit_bridge.healthkit_observations(
        None, "P-u", "AOD-9604", "Body weight", "2026-01-01T00:00:00Z",
        hk_conn=hk_conn,
    )
    assert obs == []


def test_resting_heart_rate_maps_bpm(hk_conn):
    link_subject_to_patient(hk_conn, "subj-3", "P-3")
    _add_sample(hk_conn, "subj-3", "HKQuantityTypeIdentifierRestingHeartRate",
                61.0, "count/min", "2026-01-08T06:00:00Z")
    obs = healthkit_bridge.healthkit_observations(
        None, "P-3", "Semaglutide", "Resting heart rate", "2026-01-01T00:00:00Z",
        hk_conn=hk_conn,
    )
    assert len(obs) == 1
    assert obs[0][1] == pytest.approx(61.0)


# ── GLP-1 class-qualified binding ───────────────────────────────────────────

def test_glp1_binds_class_qualified_name(hk_conn):
    link_subject_to_patient(hk_conn, "subj-g", "P-g")
    _add_sample(hk_conn, "subj-g", "HKQuantityTypeIdentifierBodyMass",
                95.0, "kg", "2026-01-08T09:00:00Z")

    # For a GLP-1 peptide, body mass binds to the class-qualified marker.
    binding = healthkit_bridge.resolve_proxy("Semaglutide", "Body weight (GLP-1 RA)")
    assert binding is not None
    assert binding.biomarker_name == "Body weight (GLP-1 RA)"

    obs = healthkit_bridge.healthkit_observations(
        None, "P-g", "Semaglutide", "Body weight (GLP-1 RA)",
        "2026-01-01T00:00:00Z", hk_conn=hk_conn,
    )
    assert len(obs) == 1

    # The GLP-1 proxy must NOT bleed onto the generic 'Body weight' marker.
    assert healthkit_bridge.resolve_proxy("Semaglutide", "Body weight") is None
    bleed = healthkit_bridge.healthkit_observations(
        None, "P-g", "Semaglutide", "Body weight",
        "2026-01-01T00:00:00Z", hk_conn=hk_conn,
    )
    assert bleed == []


def test_generic_peptide_does_not_bind_glp1_name(hk_conn):
    # A non-GLP-1 peptide's body mass binds only to the generic marker.
    assert healthkit_bridge.resolve_proxy("AOD-9604", "Body weight") is not None
    assert healthkit_bridge.resolve_proxy("AOD-9604", "Body weight (GLP-1 RA)") is None


# ── Daily-median aggregation ────────────────────────────────────────────────

def test_daily_median_aggregation(hk_conn):
    link_subject_to_patient(hk_conn, "subj-d", "P-d")
    # Day 1: three samples → median 78.0. Day 2: two samples → median 76.5.
    for hour, v in zip(("06", "12", "20"), (77.0, 78.0, 82.0), strict=True):
        _add_sample(hk_conn, "subj-d", "HKQuantityTypeIdentifierBodyMass",
                    v, "kg", f"2026-01-08T{hour}:00:00Z")
    for hour, v in zip(("07", "19"), (76.0, 77.0), strict=True):
        _add_sample(hk_conn, "subj-d", "HKQuantityTypeIdentifierBodyMass",
                    v, "kg", f"2026-01-15T{hour}:00:00Z")
    obs = healthkit_bridge.healthkit_observations(
        None, "P-d", "AOD-9604", "Body weight", "2026-01-01T00:00:00Z",
        hk_conn=hk_conn,
    )
    assert len(obs) == 2  # one observation per calendar day
    values = sorted(v for _, v in obs)
    assert values == pytest.approx([76.5, 78.0])


# ── Graceful empties ────────────────────────────────────────────────────────

def test_no_proxy_biomarker_returns_empty(hk_conn):
    link_subject_to_patient(hk_conn, "subj-n", "P-n")
    _add_sample(hk_conn, "subj-n", "HKQuantityTypeIdentifierBodyMass",
                78.0, "kg", "2026-01-08T09:00:00Z")
    # 'Serum IGF-1' has no proxy counterpart.
    obs = healthkit_bridge.healthkit_observations(
        None, "P-n", "CJC-1295", "Serum IGF-1", "2026-01-01T00:00:00Z",
        hk_conn=hk_conn,
    )
    assert obs == []


def test_no_subject_mapping_returns_empty(hk_conn):
    # Samples exist but the patient is not linked to any subject.
    _add_sample(hk_conn, "subj-orphan", "HKQuantityTypeIdentifierBodyMass",
                78.0, "kg", "2026-01-08T09:00:00Z")
    obs = healthkit_bridge.healthkit_observations(
        None, "P-unlinked", "AOD-9604", "Body weight", "2026-01-01T00:00:00Z",
        hk_conn=hk_conn,
    )
    assert obs == []


# ── Noise-scale mechanism (bayes-level) ─────────────────────────────────────

_FIT_KW = dict(
    tau_weeks=8.0,
    baseline_prior_mean=78.0,
    baseline_prior_sd=23.4,
    noise_pct=0.015,
)


def test_none_scales_identical_to_all_ones():
    """noise_scales=None must be byte-for-byte identical to all-ones weights —
    the invariant that keeps the clinical-only path unchanged."""
    obs = [(0.5, 78.0), (4.0, 76.5), (8.0, 75.0), (12.0, 74.0), (16.0, 73.5)]
    fit_none = joint_fit_likelihood(observations=obs, **_FIT_KW)
    fit_ones = joint_fit_likelihood(
        observations=obs, noise_scales=[1.0] * len(obs), **_FIT_KW
    )
    assert fit_none is not None and fit_ones is not None
    assert fit_none.likelihood.to_dict() == fit_ones.likelihood.to_dict()
    assert fit_none.baseline == fit_ones.baseline
    assert fit_none.baseline_sd == fit_ones.baseline_sd


def test_wearable_mix_widens_not_tightens():
    """Down-weighting a subset as wearable-grade (scale > 1) must WIDEN the θ
    likelihood versus treating the identical points as all clinical-grade —
    the honesty contract: proxies inform but do not swamp lab measurements."""
    obs = [(0.5, 78.0), (4.0, 76.5), (8.0, 75.0), (12.0, 74.0), (16.0, 73.5)]
    all_clinical = joint_fit_likelihood(
        observations=obs, noise_scales=[1.0] * len(obs), **_FIT_KW
    )
    # First two are clinical labs; the trailing three are wearable proxies.
    mixed = joint_fit_likelihood(
        observations=obs,
        noise_scales=[1.0, 1.0, 2.5, 2.5, 2.5],
        **_FIT_KW,
    )
    assert mixed.likelihood.sd_pct_change > all_clinical.likelihood.sd_pct_change


def test_appended_proxies_do_not_falsely_tighten_via_count():
    """Regression for the raw-count bug: appending down-weighted wearable
    observations to a small clinical set must tighten θ LESS than appending
    the same points as clinical labs — the effective-sample-size fix ensures
    proxies don't buy Student-t degrees of freedom / noise-floor they haven't
    earned."""
    labs = [(0.5, 78.0), (8.0, 75.0), (16.0, 73.5)]
    extra = [(2.0, 77.0), (6.0, 76.0), (10.0, 74.5), (14.0, 74.0), (20.0, 73.0)]
    obs = labs + extra
    as_clinical = joint_fit_likelihood(
        observations=obs, noise_scales=[1.0] * len(obs), **_FIT_KW
    )
    as_wearable = joint_fit_likelihood(
        observations=obs,
        noise_scales=[1.0] * len(labs) + [2.5] * len(extra),
        **_FIT_KW,
    )
    assert as_wearable.likelihood.sd_pct_change > as_clinical.likelihood.sd_pct_change


def test_noise_scales_length_mismatch_raises():
    obs = [(0.5, 78.0), (4.0, 76.5)]
    with pytest.raises(ValueError):
        joint_fit_likelihood(observations=obs, noise_scales=[1.0], **_FIT_KW)


def test_nonpositive_noise_scale_raises():
    obs = [(1.0, 78.0), (4.0, 76.0)]
    with pytest.raises(ValueError):
        joint_fit_likelihood(observations=obs, noise_scales=[1.0, 0.0], **_FIT_KW)


# ── Integration through predict_response ────────────────────────────────────

def _seed_patient(conn, peptide, biomarker, start):
    p = service.create_patient(conn, label="INT-1")
    service.set_genetic_profile(
        conn, p.id, generate_synthetic_profile(random.Random(7)).to_json()
    )
    service.create_treatment(
        conn, patient_id=p.id, peptide_name=peptide, start_date=start,
    )
    # A couple of clinical measurements so a likelihood exists.
    service.create_measurement(
        conn, patient_id=p.id, biomarker_name=biomarker, value=78.0,
        measured_at="2026-01-02T00:00:00Z",
    )
    service.create_measurement(
        conn, patient_id=p.id, biomarker_name=biomarker, value=75.0,
        measured_at="2026-02-15T00:00:00Z",
    )
    return p


def test_predict_response_no_healthkit_is_a_noop(conn, monkeypatch):
    """With no subject mapping the bridge returns [] and the prediction is
    identical to explicitly disabling the bridge — the wiring is a true
    no-op on the clinical-only path."""
    p = _seed_patient(conn, "AOD-9604", "Body weight", "2026-01-01T00:00:00Z")
    kw = dict(patient_id=p.id, peptide_name="AOD-9604", biomarker_name="Body weight")

    real = analysis.predict_response(conn, **kw)

    monkeypatch.setattr(
        healthkit_bridge, "healthkit_observations",
        lambda *a, **k: [],
    )
    disabled = analysis.predict_response(conn, **kw)
    assert real == disabled


def test_predict_response_appends_healthkit_observations(conn, monkeypatch):
    """Injected wearable proxy observations flow into the likelihood and move
    the posterior — the append path is live."""
    p = _seed_patient(conn, "AOD-9604", "Body weight", "2026-01-01T00:00:00Z")
    kw = dict(patient_id=p.id, peptide_name="AOD-9604", biomarker_name="Body weight")

    baseline = analysis.predict_response(conn, **kw)

    hk_obs = [(6.0, 76.0), (10.0, 74.5), (14.0, 73.5)]
    monkeypatch.setattr(
        healthkit_bridge, "healthkit_observations",
        lambda *a, **k: list(hk_obs),
    )
    with_hk = analysis.predict_response(conn, **kw)

    # More observations entered the fit → n_effective changes and the
    # posterior is not identical to the clinical-only run.
    assert with_hk["posterior"] != baseline["posterior"]
    assert with_hk["likelihood"]["n_observations"] > baseline["likelihood"]["n_observations"]
