"""
engine/tracking/feature_adapters/healthkit_behavior_adapter.py
=============================================================
HealthKit *behavioural-covariate* feature adapter (Phase 1 fan-out).

Role split (see ``docs/models/peptide-response-model.md`` §4). HealthKit data
enters the model in two disjoint roles that must never be conflated:

  1. **Proxy observations** — quantities that *are* a tracked biomarker (resting
     HR, body mass, VO₂max). Those update the **likelihood** on θ.
  2. **Behavioural covariates** — signals that modulate *responsiveness* but are
     not the outcome (activity, sleep, adherence proxies). Those enter the
     **prior** as feature-adapter contributions to the responder index η.

This adapter implements role (2) only. It summarises a patient's *recent*
HealthKit activity into a handful of standardised effect-modifier features that
nudge the responder index. It NEVER emits an observation of θ.

Signals (each gated independently — a missing signal simply drops its feature):

  * ``hk_steps``    — mean daily step count (``HKQuantityTypeIdentifierStepCount``)
  * ``hk_sleep``    — mean nightly asleep hours (``HKCategoryTypeIdentifierSleepAnalysis``)
  * ``hk_workouts`` — workout frequency (workouts per observed week)

Each raw aggregate is centred/scaled against a coarse population reference so
the standardised value ``z`` is O(1); with modest, ridge-shrunk β the whole
adapter keeps ``βᵀx`` O(1) and cannot dominate the anchored genetics feature.

Sign assumptions (documented conservatively — these are priors, not fitted):
higher baseline activity, more sleep, and more frequent workouts *plausibly*
improve response to metabolic/regenerative peptides, and rising activity is an
engagement/adherence proxy for *any* therapy — so all three β are **positive**
and **small**. Because the direction is an assumption, each feature also carries
a deliberately **wide** feature-value variance ``var_j`` (order one standardised
unit, inflated further when few days were observed): the covariate is allowed to
move the prior mean, but it does so with honest, non-trivial uncertainty. (The
frozen composition rule in spec §2.3 re-linearises the whole index at the joint
operating point, so this does not translate into a guaranteed net SD change —
honesty lives in the inputs, not in an asserted net effect.)

Aggregation normalisation. All three signals normalise by *observed* activity,
not by the nominal window length: steps average over observed calendar days,
sleep over observed nights, and workout frequency over the observed data span
(floored at one week). This keeps a patient with a short sync history from being
spuriously flagged sedentary.

Known simplifications (documented, not bugs): raw step samples from multiple
sources (iPhone + Watch) are summed without HealthKit source-priority
de-duplication, and calendar-date bucketing is done in whatever timezone the
backend returns timestamps in. These can bias magnitudes but not the sign of the
covariate; the wide ``var_j`` above absorbs the resulting slop.

Reachability / graceful no-op contract
--------------------------------------
The adapter is **optional** (``required = False``). It contributes NOTHING —
returns ``{}`` — whenever HealthKit data is not reachable for this prediction:

  * no live DB handle on the context (``context.conn is None``),
  * no patient handle / patient id,
  * the patient has no ``subject_id`` mapping,
  * the patient has no HealthKit samples in the window,
  * the connection cannot see the ``healthkit_*`` tables at all.

The last case is the SQLite dev/test reality: tracking and HealthKit live in
*separate* SQLite files, so the tracking connection raises
``sqlite3.OperationalError`` ("no such table"). We catch **only** that DB-level
error and no-op quietly; any *other* exception (a genuine logic bug) propagates
to ``build_feature_vector``, which isolates and *logs* it. In Postgres prod both
live in the same database (migrations run at startup), so the tables are always
reachable.

Pure stdlib (``math``/``datetime``/``sqlite3``) — matches the surrounding code.
"""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from ..healthkit_identity import resolve_subject_id
from ..responder_index import Feature, ResponderContext, register_adapter

# ── Aggregation window ───────────────────────────────────────────────────────
# Anchored on the patient's *latest* sample timestamp, not wall-clock, so the
# window is deterministic for a fixed dataset (and tests with frozen timestamps
# behave identically regardless of when they run).
_WINDOW_DAYS = 30
_MIN_SPAN_DAYS = 7           # floor for the workout-frequency denominator.
_READ_LIMIT = 50_000         # generous per-type cap for a ~month of samples.

# HealthKit type identifiers.
_STEP_TYPE = "HKQuantityTypeIdentifierStepCount"
_SLEEP_TYPE = "HKCategoryTypeIdentifierSleepAnalysis"

# HKCategoryValueSleepAnalysis values that count as *asleep* (vs in-bed/awake):
#   1 = asleepUnspecified (legacy), 3 = asleepCore, 4 = asleepDeep, 5 = asleepREM.
_ASLEEP_VALUES = {1, 3, 4, 5}

# Coarse population references for standardisation z = (raw - center) / scale.
_STEPS_CENTER, _STEPS_SCALE = 7000.0, 4000.0        # steps / day
_SLEEP_CENTER, _SLEEP_SCALE = 7.0, 1.5              # hours / night
_WORKOUTS_CENTER, _WORKOUTS_SCALE = 3.0, 3.0        # workouts / week

_Z_CLAMP = 3.0  # clamp standardised values so one outlier day can't blow up βᵀx.

# Modest, ridge-shrunk coefficients (all positive; see sign assumptions above).
_BETA_STEPS = 0.12
_BETA_SLEEP = 0.10
_BETA_WORKOUTS = 0.10

# Wide base variance on each standardised feature value (standardised units²),
# inflated when few days informed the aggregate: var = BASE · (1 + K / n_days).
_BASE_VAR = 1.0
_VAR_SPARSITY_K = 1.0


def _clamp_z(raw: float, center: float, scale: float) -> float:
    z = (raw - center) / scale
    return max(-_Z_CLAMP, min(_Z_CLAMP, z))


def _var_for(n_units: int) -> float:
    """Wide feature-value variance, inflated for sparse observation windows."""
    n = max(1, n_units)
    return _BASE_VAR * (1.0 + _VAR_SPARSITY_K / n)


def _parse_ts(value) -> datetime | None:
    """Parse an ISO-8601 start/end timestamp as returned by read_samples.

    Naive timestamps (some clients omit an offset) are treated as UTC so
    downstream comparisons never mix aware/naive datetimes (which would raise).
    """
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


@register_adapter
class HealthKitBehaviorAdapter:
    """Recent-activity behavioural covariates on the responder index."""

    name = "healthkit_behavior"
    # Optional: HealthKit is not present for most predictions, and a covariate
    # source must never sink the index. Any absence → no features.
    required = False

    def peptide_mask(self, peptide_name: str) -> bool:
        # All peptides. Activity/sleep are general metabolic/regenerative
        # effect-modifiers, and step-trend-to-zero is an adherence/engagement
        # signal that applies to *any* therapy — so we do not restrict to the
        # metabolic/regenerative families. β are small enough that an irrelevant
        # peptide is barely nudged.
        return True

    def features(self, context: ResponderContext) -> dict[str, Feature]:
        conn = context.conn
        patient = context.patient
        # Hard guards: emit nothing unless HK data is genuinely reachable. The
        # genetics-only golden tests build contexts with conn=None / patient=None
        # and assert an exactly-genetics feature vector, so any emission here
        # would break backward-compat.
        if conn is None or patient is None or not getattr(patient, "id", None):
            return {}

        try:
            subject_id = resolve_subject_id(conn, patient.id)
            if subject_id is None:
                return {}
            window = self._read_window(conn, subject_id)
        except sqlite3.OperationalError:
            # Unreachable HK tables (SQLite dev: separate file → "no such
            # table") → contribute nothing, quietly. Any other error is a real
            # bug and is left to propagate (build_feature_vector logs + skips).
            return {}

        if window is None:
            return {}
        step_rows, sleep_rows, workout_rows, span_days = window

        feats: dict[str, Feature] = {}

        steps = self._step_feature(step_rows)
        if steps is not None:
            feats["hk_steps"] = steps

        sleep = self._sleep_feature(sleep_rows)
        if sleep is not None:
            feats["hk_sleep"] = sleep

        workouts = self._workout_feature(workout_rows, span_days)
        if workouts is not None:
            feats["hk_workouts"] = workouts

        return feats

    # ── data access ─────────────────────────────────────────────────────────

    def _read_window(self, conn, subject_id: str):
        """Fetch the per-signal samples within ``_WINDOW_DAYS`` of the patient's
        latest sample. Returns ``(step_rows, sleep_rows, workout_rows,
        span_days)`` or ``None`` if there is no data.

        Reads are **per-type** and window-bounded (``since=cutoff``) so a
        high-frequency signal (e.g. heart rate) cannot consume a shared row
        budget and truncate steps/sleep out of the window. The window is
        anchored on the data (latest sample), not wall-clock, for determinism.
        """
        from engine.healthkit import service

        latest_rows = service.read_samples(conn, subject_id=subject_id, limit=1)
        if not latest_rows:
            return None
        latest = _parse_ts(latest_rows[0].get("start_time"))
        if latest is None:
            return None
        cutoff = latest - timedelta(days=_WINDOW_DAYS)
        cutoff_iso = cutoff.isoformat()

        step_rows = service.read_samples(
            conn, subject_id=subject_id, type_identifier=_STEP_TYPE,
            since=cutoff_iso, limit=_READ_LIMIT,
        )
        sleep_rows = service.read_samples(
            conn, subject_id=subject_id, type_identifier=_SLEEP_TYPE,
            since=cutoff_iso, limit=_READ_LIMIT,
        )
        workout_rows = self._read_workouts(conn, subject_id, cutoff_iso)

        if not (step_rows or sleep_rows or workout_rows):
            return None

        # Parse timestamps once and derive the observed data span → the honest
        # denominator for workout frequency (consistent with steps/sleep, which
        # normalise by observed units).
        earliest = latest
        for r in (*step_rows, *sleep_rows, *workout_rows):
            ts = _parse_ts(r.get("start_time"))
            if ts is not None:
                r["_start_dt"] = ts
                if ts < earliest:
                    earliest = ts
        span_days = max(_MIN_SPAN_DAYS, (latest - earliest).days)

        return step_rows, sleep_rows, workout_rows, span_days

    @staticmethod
    def _read_workouts(conn, subject_id: str, cutoff_iso: str) -> list[dict]:
        """Window-bounded read of workout samples (by ``sample_class``), so the
        frequency count is not subject to another signal's row budget."""
        ph = "%s" if getattr(conn, "_is_pg", False) else "?"
        rows = conn.execute(
            f"SELECT start_time FROM healthkit_samples "
            f"WHERE subject_id = {ph} AND sample_class = 'workout' "
            f"AND start_time >= {ph} "
            f"ORDER BY start_time DESC LIMIT {ph}",
            (subject_id, cutoff_iso, _READ_LIMIT),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── per-signal features (each independently gated) ───────────────────────

    def _step_feature(self, rows: list[dict]) -> Feature | None:
        """Mean daily step count over observed days.

        Multiple step samples on the same calendar day are summed (a day may
        carry many partial samples). Days with no samples do not dilute the mean.
        """
        per_day: dict[str, float] = {}
        for r in rows:
            value = r.get("value")
            ts: datetime | None = r.get("_start_dt")
            if value is None or ts is None:
                continue
            key = ts.date().isoformat()
            per_day[key] = per_day.get(key, 0.0) + float(value)
        if not per_day:
            return None

        mean_daily = sum(per_day.values()) / len(per_day)
        z = _clamp_z(mean_daily, _STEPS_CENTER, _STEPS_SCALE)
        return Feature(
            name="hk_steps",
            value=z,
            beta=_BETA_STEPS,
            variance=_var_for(len(per_day)),
            source=self.name,
        )

    def _sleep_feature(self, rows: list[dict]) -> Feature | None:
        """Mean nightly asleep hours over observed nights.

        Asleep duration = (end - start) summed over asleep-stage category
        samples; in-bed/awake stages are excluded. A "night" is bucketed with a
        noon boundary (``start - 12h`` date) so an overnight session that
        crosses midnight is attributed to a single night rather than split.
        """
        per_night_hours: dict[str, float] = {}
        for r in rows:
            value = r.get("value")
            try:
                if value is None or int(value) not in _ASLEEP_VALUES:
                    continue
            except (TypeError, ValueError):
                continue
            start: datetime | None = r.get("_start_dt")
            end = _parse_ts(r.get("end_time"))
            if start is None or end is None:
                continue
            hours = (end - start).total_seconds() / 3600.0
            if hours <= 0:
                continue
            key = (start - timedelta(hours=12)).date().isoformat()
            per_night_hours[key] = per_night_hours.get(key, 0.0) + hours
        if not per_night_hours:
            return None

        mean_nightly = sum(per_night_hours.values()) / len(per_night_hours)
        z = _clamp_z(mean_nightly, _SLEEP_CENTER, _SLEEP_SCALE)
        return Feature(
            name="hk_sleep",
            value=z,
            beta=_BETA_SLEEP,
            variance=_var_for(len(per_night_hours)),
            source=self.name,
        )

    def _workout_feature(self, rows: list[dict], span_days: int) -> Feature | None:
        """Workout frequency (workouts per observed week) over the window."""
        n_workouts = len(rows)
        if n_workouts == 0:
            return None

        weeks = span_days / 7.0
        per_week = n_workouts / weeks
        z = _clamp_z(per_week, _WORKOUTS_CENTER, _WORKOUTS_SCALE)
        return Feature(
            name="hk_workouts",
            value=z,
            beta=_BETA_WORKOUTS,
            variance=_var_for(n_workouts),
            source=self.name,
        )
