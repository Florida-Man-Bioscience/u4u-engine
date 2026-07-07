"""
Unit tests for the demographic covariate feature adapter (Phase 1).

The adapter exposes ``sex`` / ``birth_year`` (and optional ``weight_kg`` via
``context.extra``) as ridge-shrunk effect-modifier features on the responder
index. These tests pin the sign/mechanism assumptions and the honesty
contract: demographics nudge the mean and *widen* Var(η); missing demographics
contribute nothing.
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

import pytest

from engine.tracking import analysis, pooling, service
from engine.tracking.feature_adapters.covariates_adapter import (
    _AGE_BETA,
    _AGE_SIGMA_BETA,
    CovariatesAdapter,
)
from engine.tracking.genetics import R_DELTA_SCALE, generate_synthetic_profile
from engine.tracking.responder_index import (
    PatientHandle,
    ResponderContext,
    build_feature_vector,
    registered_adapters,
    responder_index,
)

_YEAR = 2026  # deterministic reference year (passed via context.extra)


def _ctx(*, sex=None, birth_year=None, peptide="CJC-1295", extra=None):
    e = {"current_year": _YEAR}
    if extra:
        e.update(extra)
    return ResponderContext(
        peptide_name=peptide,
        profile=None,
        patient=PatientHandle(id="P-1", sex=sex, birth_year=birth_year),
        extra=e,
    )


def _feats(**kw):
    return CovariatesAdapter().features(_ctx(**kw))


# ── Registration + masking ───────────────────────────────────────────────────

def test_adapter_registered_and_optional():
    adapters = registered_adapters()
    assert "covariates" in adapters
    assert adapters["covariates"].required is False
    # General covariates apply to every peptide.
    assert adapters["covariates"].peptide_mask("CJC-1295") is True
    assert adapters["covariates"].peptide_mask("BPC-157") is True


# ── Age: young vs old ────────────────────────────────────────────────────────

def test_age_young_vs_old_have_opposite_signs():
    young = _feats(birth_year=_YEAR - 30)["age"]   # age 30 → x = -1.0
    old = _feats(birth_year=_YEAR - 70)["age"]     # age 70 → x = +1.0
    assert math.isclose(young.value, -1.0)
    assert math.isclose(old.value, 1.0)
    # β is negative: older → lower linear contribution than younger.
    assert old.beta * old.value < young.beta * young.value


def test_age_center_emits_no_feature():
    # Exactly the reference age (50) is a neutral standardised value (x = 0):
    # no signal and no widening, so the feature is omitted (avoids spuriously
    # marking the vector "rich").
    assert "age" not in _feats(birth_year=_YEAR - 50)


def test_age_variance_reproduces_coefficient_uncertainty():
    old = _feats(birth_year=_YEAR - 70)["age"]  # x = +1.0
    # β² · var == x² · σ_β²  (the coefficient-uncertainty encoding).
    assert math.isclose(
        old.beta ** 2 * old.variance,
        old.value ** 2 * _AGE_SIGMA_BETA ** 2,
        rel_tol=1e-12,
    )
    # And β̂ itself is the documented modest value.
    assert old.beta == _AGE_BETA
    # Pin the numeric variance too: variance = (x·σ_β/β)² = (1·0.06/−0.06)² = 1.0.
    assert math.isclose(old.variance, 1.0, rel_tol=1e-12)


# ── Sex: each sex ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("label", ["M", "male", "Male"])
def test_sex_male_positive(label):
    f = _feats(sex=label)["sex"]
    assert f.value == 1.0
    assert f.beta > 0


@pytest.mark.parametrize("label", ["F", "female", "Female"])
def test_sex_female_negative(label):
    f = _feats(sex=label)["sex"]
    assert f.value == -1.0


@pytest.mark.parametrize("label", ["other", "", None, "unknown", "X"])
def test_sex_unknown_abstains(label):
    assert "sex" not in _feats(sex=label)


def test_male_vs_female_linear_differ():
    m = _feats(sex="M")["sex"]
    f = _feats(sex="F")["sex"]
    assert (m.beta * m.value) != (f.beta * f.value)


# ── Weight (optional, via extra) ─────────────────────────────────────────────

def test_weight_only_from_extra():
    # Not present without extra…
    assert "weight" not in _feats(birth_year=_YEAR - 40)
    # …present and standardised when supplied.
    f = _feats(birth_year=_YEAR - 40, extra={"weight_kg": 100.0})["weight"]
    assert math.isclose(f.value, (100.0 - 80.0) / 20.0)  # x = +1.0
    assert f.beta < 0  # heavier → mild negative nudge


@pytest.mark.parametrize("bad", [0, 0.0, -5, None])
def test_weight_zero_or_nonpositive_sentinel_is_ignored(bad):
    # A 0 / non-positive weight sentinel must NOT fire a feature (it would
    # otherwise standardise to a large spurious value, e.g. weight=0 → x=−4.0).
    assert "weight" not in _feats(birth_year=_YEAR - 40, extra={"weight_kg": bad})


# ── Partial / all-missing ────────────────────────────────────────────────────

def test_partial_features_ok():
    # Only birth_year → only the age feature fires.
    feats = _feats(birth_year=_YEAR - 60)
    assert set(feats) == {"age"}


def test_all_missing_yields_no_features():
    assert _feats(sex=None, birth_year=None) == {}


def test_no_patient_yields_no_features():
    ctx = ResponderContext(peptide_name="CJC-1295", profile=None, patient=None)
    assert CovariatesAdapter().features(ctx) == {}


# ── Integration with the responder index ─────────────────────────────────────

def test_demographics_nudge_mean_and_widen_linear_variance():
    """With genetics + demographics, η shifts modestly and the variance of the
    linear predictor Var(βᵀx)=Σβ²var strictly grows (uncertainty added, never
    fabricated). We assert on Var(βᵀx) rather than Var(η) because, per the
    frozen composition rule (spec §2.3), the genetics contribution to Var(η)
    re-linearises at the shifted operating point — a second-order effect that
    can move either way — whereas Σβ²var is monotone in the feature set."""
    profile = generate_synthetic_profile(random.Random(7))

    geno_ctx = ResponderContext(
        peptide_name="CJC-1295", profile=profile, patient=PatientHandle(id="P-1")
    )
    demo_ctx = ResponderContext(
        peptide_name="CJC-1295",
        profile=profile,
        patient=PatientHandle(id="P-1", sex="M", birth_year=_YEAR - 70),
        extra={"current_year": _YEAR},
    )

    genetics_only = responder_index(geno_ctx)
    with_demo = responder_index(demo_ctx)

    # A covariate feature actually fired.
    assert any(f.source == "covariates" for f in with_demo.features)
    # Mean moved, but only modestly (nudge, not dominate) — well inside Δ.
    assert with_demo.eta != genetics_only.eta
    assert abs(with_demo.eta - genetics_only.eta) < 0.5 * R_DELTA_SCALE
    # Adding uncertain demographic features strictly widened Var(βᵀx).
    assert build_feature_vector(demo_ctx).var_linear > \
        build_feature_vector(geno_ctx).var_linear


# ── Integration: arming the spec §3 fused-precision cap ──────────────────────

def _seed_cohort(conn, *, peptide, biomarker, thetas, baseline=180.0, tau=3.0):
    """Minimal donor cohort with known true θ and synthetic measurements."""
    rng = random.Random(0)
    start = datetime(2026, 1, 1)
    weeks = [0.0, 2.0, 4.0, 8.0, 12.0]
    created = []
    for i, theta in enumerate(thetas):
        p = service.create_patient(conn, label=f"COV-COHORT-{i:02d}")
        t = service.create_treatment(
            conn, patient_id=p.id, peptide_name=peptide,
            start_date=start.date().isoformat(), dose=2.0, dose_unit="mg",
        )
        for w in weeks:
            a = 1 - math.exp(-w / tau)
            val = baseline * (1 + theta * a) + rng.gauss(0, baseline * 0.04)
            service.create_measurement(
                conn, patient_id=p.id, treatment_id=t.id,
                biomarker_name=biomarker, value=val,
                measured_at=(start + timedelta(weeks=w)).date().isoformat(),
                modality="hormone",
            )
        created.append(p)
    return created


def test_demographics_arm_fused_precision_cap_path(conn):
    """Integration (spec §3): a patient with BOTH a genetic profile AND
    demographics is the first case to arm the fused-precision cap gate
    (``n_nongenetic_features >= 1``) once a donor cohort is present. This is an
    intended Phase-1 activation — guard that the path runs end-to-end and yields
    a finite, positive prior SD rather than crashing or degrading the prior.

    Note: ``predict_response`` only assembles responder features when the
    patient has a genetics profile (``raw is not None``), so demographics alone
    (no genetics) never arm the cap — both must be present.
    """
    cohort = _seed_cohort(
        conn, peptide="CJC-1295", biomarker="Serum IGF-1",
        thetas=[0.40, 0.50, 0.60, 0.55, 0.45],
    )
    target = cohort[0]
    # Genetics → the responder-index block runs; demographics → covariates fires.
    service.set_genetic_profile(
        conn, target.id, generate_synthetic_profile(random.Random(1)).to_json()
    )
    conn.execute(
        "UPDATE patients SET sex = 'M', birth_year = 1956 WHERE id = ?",
        (target.id,),
    )
    conn.commit()

    pred = analysis.predict_response(
        conn, patient_id=target.id, peptide_name="CJC-1295",
        biomarker_name="Serum IGF-1",
    )
    # A covariate feature fired → the cap gate is armed (≥1 non-genetic feature).
    assert "covariates" in {f["source"] for f in pred["responder_features"]}
    # ≥ MIN_DONORS donors after LOO (5 in cohort − 1 target = 4), so the cap
    # path actually executed.
    assert pred["population_prior"]["n_donors"] >= pooling.MIN_DONORS
    # Prior remains sane (finite, positive) through the cap.
    assert pred["prior"] is not None
    sd = pred["prior"]["sd_pct_change"]
    assert math.isfinite(sd) and sd > 0
