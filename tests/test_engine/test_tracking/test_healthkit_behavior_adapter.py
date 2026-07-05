"""
Unit tests for the HealthKit behavioural-covariate feature adapter.

The adapter summarises a patient's recent HealthKit activity into standardised
effect-modifier features on the responder index η (the *prior*), NOT observations
of θ. These tests inject a synthetic in-memory HealthKit SQLite connection
carrying a subject-map row + healthkit_samples (mirroring test_healthkit_identity),
and drive ``features()`` directly so we exercise the aggregation + guards without
the full predict path.

Covered:
  * active vs sedentary patient → different (opposite-signed) standardised features
  * workout frequency normalised by observed span (positive for a genuinely active
    patient) and dropped when there are no workouts
  * multi-sample-per-day step summation
  * sleep asleep/awake filtering (awake & in-bed stages excluded)
  * out-of-window samples dropped by the 30-day cutoff
  * feature-value variance is wide and inflates for sparse histories
  * no subject mapping → no features
  * subject mapped but no samples → no features
  * missing conn / missing patient handle / unreachable tables → no features
"""
from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from engine.healthkit import db as hk_db
from engine.healthkit import service
from engine.healthkit.db import get_conn
from engine.healthkit.schemas import SampleIn, WorkoutIn
from engine.tracking.feature_adapters.healthkit_behavior_adapter import (
    _STEPS_CENTER,
    _STEPS_SCALE,
    HealthKitBehaviorAdapter,
    _clamp_z,
)
from engine.tracking.healthkit_identity import link_subject_to_patient
from engine.tracking.responder_index import PatientHandle, ResponderContext

_BASE = datetime(2026, 6, 1, 8, 0, tzinfo=UTC)

_STEP_TYPE = "HKQuantityTypeIdentifierStepCount"
_SLEEP_TYPE = "HKCategoryTypeIdentifierSleepAnalysis"


def _step_sample(when: datetime, steps: float) -> SampleIn:
    return SampleIn(
        uuid=uuid.uuid4(),
        cls="quantity",
        type=_STEP_TYPE,
        value=steps,
        unit="count",
        start=when,
        end=when,
    )


def _sleep_sample(when: datetime, hours: float, value: int = 3) -> SampleIn:
    return SampleIn(
        uuid=uuid.uuid4(),
        cls="category",
        type=_SLEEP_TYPE,
        value=value,  # 3 = asleepCore; 0 = inBed, 2 = awake (excluded)
        unit=None,
        start=when,
        end=when + timedelta(hours=hours),
    )


def _workout_sample(when: datetime) -> SampleIn:
    return SampleIn(
        uuid=uuid.uuid4(),
        cls="workout",
        type="HKWorkoutTypeIdentifier",
        value=None,
        unit=None,
        start=when,
        end=when + timedelta(minutes=45),
        workout=WorkoutIn(
            activityType="running",
            durationSeconds=2700.0,
            totalEnergyKcal=400.0,
            totalDistanceMeters=6000.0,
        ),
    )


def _seed(conn, subject_id, patient_id, samples: list[SampleIn]):
    service.ingest(conn, subject_id=subject_id, samples=samples)
    link_subject_to_patient(conn, subject_id, patient_id)


def _seed_profile(conn, subject_id, patient_id, *, steps, sleep_hours, n_workouts, n_days=20):
    samples: list[SampleIn] = []
    for d in range(n_days):
        day = _BASE + timedelta(days=d)
        samples.append(_step_sample(day, steps))
        # Sleep at ~06:00 (crosses the noon bucket boundary onto a single night).
        samples.append(_sleep_sample(day - timedelta(hours=2), sleep_hours))
    for d in range(n_workouts):
        samples.append(_workout_sample(_BASE + timedelta(days=d, hours=1)))
    _seed(conn, subject_id, patient_id, samples)


@pytest.fixture
def conn():
    hk_db.reset_initialized()
    with get_conn(":memory:") as c:
        yield c


def _ctx(conn, patient_id):
    return ResponderContext(
        peptide_name="CJC-1295",
        profile=None,
        patient=PatientHandle(id=patient_id),
        conn=conn,
    )


def _feats(conn, patient_id):
    return HealthKitBehaviorAdapter().features(_ctx(conn, patient_id))


def test_active_patient_yields_positive_features(conn):
    _seed_profile(conn, "subj-active", "P-active", steps=13000, sleep_hours=8.0, n_workouts=12)
    feats = _feats(conn, "P-active")

    assert set(feats) == {"hk_steps", "hk_sleep", "hk_workouts"}
    # High activity/sleep/workout frequency all standardise to positive z.
    assert feats["hk_steps"].value > 0
    assert feats["hk_sleep"].value > 0
    assert feats["hk_workouts"].value > 0  # 12 workouts over ~19 observed days
    # Modest positive β and a wide, non-trivial variance (honesty in the input).
    assert 0 < feats["hk_steps"].beta < 0.3
    assert feats["hk_steps"].variance > 1.0
    assert all(f.source == "healthkit_behavior" for f in feats.values())


def test_sedentary_patient_yields_negative_features(conn):
    _seed_profile(conn, "subj-sed", "P-sed", steps=1500, sleep_hours=5.0, n_workouts=0)
    feats = _feats(conn, "P-sed")

    # No workouts → that feature drops out; steps/sleep still present & negative.
    assert "hk_workouts" not in feats
    assert feats["hk_steps"].value < 0
    assert feats["hk_sleep"].value < 0


def test_active_and_sedentary_differ(conn):
    _seed_profile(conn, "subj-a", "P-a", steps=14000, sleep_hours=8.5, n_workouts=10)
    _seed_profile(conn, "subj-b", "P-b", steps=1200, sleep_hours=4.5, n_workouts=0)
    a = _feats(conn, "P-a")
    b = _feats(conn, "P-b")
    assert a["hk_steps"].value > b["hk_steps"].value
    assert a["hk_sleep"].value > b["hk_sleep"].value


def test_workout_frequency_uses_observed_span_not_fixed_window(conn):
    """A patient with a short (10-day) history and 6 workouts is ~4.2/wk, well
    above the population center — must standardise positive, not be diluted by a
    fixed 30-day denominator."""
    samples = [_step_sample(_BASE + timedelta(days=d), 8000) for d in range(10)]
    samples += [_workout_sample(_BASE + timedelta(days=d, hours=1)) for d in range(6)]
    _seed(conn, "subj-short", "P-short", samples)
    feats = _feats(conn, "P-short")
    assert feats["hk_workouts"].value > 0


def test_multi_sample_per_day_steps_are_summed(conn):
    """Two step samples on the same day sum to the daily total (not overwritten
    or averaged)."""
    day = _BASE
    _seed(conn, "subj-multi", "P-multi", [
        _step_sample(day.replace(hour=9), 4000),
        _step_sample(day.replace(hour=18), 4000),
    ])
    feats = _feats(conn, "P-multi")
    # Summed daily total 8000 → positive z; a single 4000 sample would be < 0.
    expected = _clamp_z(8000.0, _STEPS_CENTER, _STEPS_SCALE)
    assert math.isclose(feats["hk_steps"].value, expected, abs_tol=1e-9)
    assert feats["hk_steps"].value > 0


def test_awake_and_inbed_sleep_stages_are_excluded(conn):
    """Only asleep stages count toward sleep hours; in-bed(0)/awake(2) excluded."""
    night = _BASE.replace(hour=23)
    _seed(conn, "subj-sleep", "P-sleep", [
        _sleep_sample(night, 7.0, value=3),          # asleepCore → counts
        _sleep_sample(night, 3.0, value=0),          # inBed → excluded
        _sleep_sample(night, 2.0, value=2),          # awake → excluded
        _step_sample(_BASE, 8000),                   # anchor so window has data
    ])
    feats = _feats(conn, "P-sleep")
    # Effective asleep hours = 7.0 → z = (7 - 7)/1.5 = 0. If the excluded stages
    # leaked in (7+3+2=12h) the sleeper would look far above center.
    assert math.isclose(feats["hk_sleep"].value, 0.0, abs_tol=1e-9)


def test_only_awake_sleep_yields_no_sleep_feature(conn):
    """A subject with only awake/in-bed stages has no asleep time → no feature."""
    night = _BASE.replace(hour=23)
    _seed(conn, "subj-awake", "P-awake", [
        _sleep_sample(night, 3.0, value=2),          # awake only
        _step_sample(_BASE, 8000),
    ])
    feats = _feats(conn, "P-awake")
    assert "hk_sleep" not in feats


def test_out_of_window_samples_are_dropped(conn):
    """Samples older than the 30-day window (relative to the latest sample) are
    excluded, so a stale low-activity day cannot drag the recent aggregate."""
    recent = [_step_sample(_BASE + timedelta(days=d), 12000) for d in range(5)]
    stale = [_step_sample(_BASE - timedelta(days=40), 100)]  # >30d before latest
    _seed(conn, "subj-win", "P-win", recent + stale)
    feats = _feats(conn, "P-win")
    # Only the 5 recent 12k-step days count → mean 12000, not diluted by the 100.
    expected = _clamp_z(12000.0, _STEPS_CENTER, _STEPS_SCALE)
    assert math.isclose(feats["hk_steps"].value, expected, abs_tol=1e-9)
    # 5 observed days → variance = 1 + 1/5 = 1.2 (would be 1 + 1/6 if stale leaked).
    assert math.isclose(feats["hk_steps"].variance, 1.0 + 1.0 / 5, abs_tol=1e-9)


def test_sparse_history_has_wider_variance(conn):
    """Feature-value variance inflates when fewer days informed the aggregate."""
    _seed(conn, "subj-one", "P-one", [_step_sample(_BASE, 9000)])  # 1 day
    _seed_profile(conn, "subj-many", "P-many", steps=9000, sleep_hours=7, n_workouts=0, n_days=20)
    one = _feats(conn, "P-one")["hk_steps"].variance
    many = _feats(conn, "P-many")["hk_steps"].variance
    assert one > many
    assert math.isclose(one, 2.0, abs_tol=1e-9)          # 1 + 1/1
    assert math.isclose(many, 1.0 + 1.0 / 20, abs_tol=1e-9)


def test_no_mapping_yields_no_features(conn):
    # Samples exist for a subject, but no subject→patient map row for this patient.
    service.ingest(conn, subject_id="subj-unmapped",
                   samples=[_step_sample(_BASE + timedelta(days=d), 9000) for d in range(10)])
    assert _feats(conn, "P-nomap") == {}


def test_mapping_but_no_samples_yields_no_features(conn):
    link_subject_to_patient(conn, "subj-empty", "P-empty")
    assert _feats(conn, "P-empty") == {}


def test_missing_conn_yields_no_features():
    ctx = ResponderContext(
        peptide_name="CJC-1295",
        profile=None,
        patient=PatientHandle(id="P-x"),
        conn=None,
    )
    assert HealthKitBehaviorAdapter().features(ctx) == {}


def test_missing_patient_yields_no_features(conn):
    ctx = ResponderContext(peptide_name="CJC-1295", profile=None, patient=None, conn=conn)
    assert HealthKitBehaviorAdapter().features(ctx) == {}


def test_unreachable_tables_yield_no_features():
    """A connection that cannot see the healthkit_* tables (the SQLite dev
    reality: tracking + healthkit are separate files) → no-op, not a crash."""
    import sqlite3

    bare = sqlite3.connect(":memory:")
    bare.row_factory = sqlite3.Row
    ctx = ResponderContext(
        peptide_name="CJC-1295",
        profile=None,
        patient=PatientHandle(id="P-x"),
        conn=bare,
    )
    try:
        assert HealthKitBehaviorAdapter().features(ctx) == {}
    finally:
        bare.close()


def test_adapter_is_registered_and_optional():
    from engine.tracking.responder_index import registered_adapters

    adapters = registered_adapters()
    assert "healthkit_behavior" in adapters
    assert adapters["healthkit_behavior"].required is False
    assert adapters["healthkit_behavior"].peptide_mask("BPC-157") is True
