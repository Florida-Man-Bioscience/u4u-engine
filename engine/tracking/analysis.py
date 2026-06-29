"""
engine/tracking/analysis.py
==========================
Cross-patient cohort analysis.

The headline query is `cohort_trajectories`: for one peptide + biomarker,
return every measurement time-aligned to its treatment_start, plus
per-time-bin median/IQR, plus the expected direction from the peptide's
panel so the chart can overlay "expected response."

All math is plain stdlib (statistics module). No numpy/pandas — keeps
the deploy footprint small and the queries readable.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from engine.peptides import get_biomarker_panel
from engine.peptides.biomarkers import BiomarkerMeasurement

from . import bayes, pooling, service
from .biomarker_params import expected_pct_change, params_for
from .genetics import GeneticProfile, derive_prior


# ── Helpers ─────────────────────────────────────────────────────────────────

def _parse_dt(value: str) -> datetime | None:
    """Accept either 'YYYY-MM-DD' or ISO datetime."""
    if not value:
        return None
    try:
        if "T" in value:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _weeks_between(start: str, end: str) -> float | None:
    a, b = _parse_dt(start), _parse_dt(end)
    if a is None or b is None:
        return None
    return (b - a).total_seconds() / (7 * 86400)


def _expected_for(peptide_name: str, biomarker_name: str) -> BiomarkerMeasurement | None:
    panel = get_biomarker_panel(peptide_name)
    if panel is None:
        return None
    target = biomarker_name.lower().strip()
    for m in panel.measurements:
        if m.name.lower().strip() == target:
            return m
    return None


# ── Trajectory model ────────────────────────────────────────────────────────

@dataclass
class TrajectoryPoint:
    """One measurement, time-aligned to its treatment_start."""
    patient_id: str
    treatment_id: str
    weeks_since_start: float
    value: float
    dose: float | None
    dose_unit: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "treatment_id": self.treatment_id,
            "weeks_since_start": round(self.weeks_since_start, 3),
            "value": self.value,
            "dose": self.dose,
            "dose_unit": self.dose_unit,
        }


@dataclass
class TimeBin:
    """Aggregate stats for a time window across the cohort."""
    weeks_label: float                # bin center, weeks since start
    n: int
    median: float
    q1: float
    q3: float
    min: float
    max: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "weeks_label": self.weeks_label,
            "n": self.n,
            "median": self.median,
            "q1": self.q1,
            "q3": self.q3,
            "min": self.min,
            "max": self.max,
        }


@dataclass
class DoseResponse:
    """One per (dose, dose_unit) bucket: aggregate effect over the window."""
    dose: float
    dose_unit: str
    n_patients: int
    n_measurements: int
    median_value: float
    pct_change_from_baseline: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dose": self.dose,
            "dose_unit": self.dose_unit,
            "n_patients": self.n_patients,
            "n_measurements": self.n_measurements,
            "median_value": self.median_value,
            "pct_change_from_baseline": self.pct_change_from_baseline,
        }


@dataclass
class CohortResult:
    peptide: str
    biomarker_name: str
    n_patients: int
    n_measurements: int
    expected: dict[str, Any] | None    # BiomarkerMeasurement.to_dict() for overlay
    trajectories: list[TrajectoryPoint] = field(default_factory=list)
    time_bins: list[TimeBin] = field(default_factory=list)
    dose_response: list[DoseResponse] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "peptide": self.peptide,
            "biomarker_name": self.biomarker_name,
            "n_patients": self.n_patients,
            "n_measurements": self.n_measurements,
            "expected": self.expected,
            "trajectories": [t.to_dict() for t in self.trajectories],
            "time_bins": [b.to_dict() for b in self.time_bins],
            "dose_response": [d.to_dict() for d in self.dose_response],
        }


# ── Bin selection ───────────────────────────────────────────────────────────

def _choose_bins(expected: BiomarkerMeasurement | None) -> list[tuple[float, float]]:
    """Return (lo, hi) week windows. Centered on the expected timeframe when
    we have one, else a default 0-26 week schedule."""
    if expected and expected.timeframe_weeks_max is not None:
        hi = max(expected.timeframe_weeks_max * 1.5, 12.0)
    else:
        hi = 26.0
    # log-ish schedule that's denser early
    raw = [0, 0.5, 1, 2, 3, 4, 6, 8, 12, 16, 20, 26, 36, 52, 78, 104]
    edges = [w for w in raw if w <= hi] + ([hi] if hi not in raw else [])
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]


def _aggregate_bin(values: list[float], center: float) -> TimeBin | None:
    if not values:
        return None
    if len(values) == 1:
        v = values[0]
        return TimeBin(center, 1, v, v, v, v, v)
    qs = statistics.quantiles(values, n=4) if len(values) >= 4 else None
    q1 = qs[0] if qs else min(values)
    q3 = qs[2] if qs else max(values)
    return TimeBin(
        weeks_label=round(center, 2),
        n=len(values),
        median=statistics.median(values),
        q1=q1,
        q3=q3,
        min=min(values),
        max=max(values),
    )


# ── Core query ──────────────────────────────────────────────────────────────

def cohort_trajectories(
    conn,
    *,
    peptide_name: str,
    biomarker_name: str,
    dose_min: float | None = None,
    dose_max: float | None = None,
) -> CohortResult:
    """Time-align every (peptide, biomarker) measurement across all patients."""
    expected = _expected_for(peptide_name, biomarker_name)
    expected_dict = expected.to_dict() if expected else None

    from .service import _ph
    ph = _ph(conn)
    sql = f"""
        SELECT m.patient_id, m.value, m.measured_at,
               t.id AS treatment_id, t.dose, t.dose_unit, t.start_date
        FROM measurements m
        JOIN treatments t
          ON t.patient_id = m.patient_id
         AND (m.treatment_id IS NULL OR m.treatment_id = t.id)
        WHERE t.peptide_name = {ph}
          AND m.biomarker_name = {ph}
    """
    params: list[Any] = [peptide_name, biomarker_name]
    if dose_min is not None:
        sql += f" AND t.dose >= {ph}"
        params.append(dose_min)
    if dose_max is not None:
        sql += f" AND t.dose <= {ph}"
        params.append(dose_max)
    sql += " ORDER BY m.measured_at"

    rows = conn.execute(sql, params).fetchall()

    trajectories: list[TrajectoryPoint] = []
    seen_patients: set[str] = set()
    for r in rows:
        weeks = _weeks_between(r["start_date"], r["measured_at"])
        if weeks is None or weeks < 0:
            continue
        trajectories.append(TrajectoryPoint(
            patient_id=r["patient_id"],
            treatment_id=r["treatment_id"],
            weeks_since_start=weeks,
            value=r["value"],
            dose=r["dose"],
            dose_unit=r["dose_unit"],
        ))
        seen_patients.add(r["patient_id"])

    # Time-bin aggregation
    bins = _choose_bins(expected)
    time_bins: list[TimeBin] = []
    for lo, hi in bins:
        vals = [t.value for t in trajectories if lo <= t.weeks_since_start < hi]
        center = (lo + hi) / 2
        agg = _aggregate_bin(vals, center)
        if agg:
            time_bins.append(agg)

    # Dose-response: bucket by exact (dose, dose_unit), compute median + %Δ from t<2wk baseline
    dose_buckets: dict[tuple[float, str], list[TrajectoryPoint]] = {}
    for t in trajectories:
        if t.dose is None or t.dose_unit is None:
            continue
        dose_buckets.setdefault((t.dose, t.dose_unit), []).append(t)

    dose_response: list[DoseResponse] = []
    for (dose, unit), pts in sorted(dose_buckets.items()):
        baseline = [p.value for p in pts if p.weeks_since_start < 2]
        post = [p.value for p in pts if p.weeks_since_start >= 2]
        target = post if post else [p.value for p in pts]
        if not target:
            continue
        if baseline and post:
            b_med = statistics.median(baseline)
            p_med = statistics.median(post)
            pct = ((p_med - b_med) / b_med * 100) if b_med else None
            pct = round(pct, 2) if pct is not None and math.isfinite(pct) else None
        else:
            pct = None
        dose_response.append(DoseResponse(
            dose=dose,
            dose_unit=unit,
            n_patients=len({p.patient_id for p in pts}),
            n_measurements=len(pts),
            median_value=round(statistics.median(target), 4),
            pct_change_from_baseline=pct,
        ))

    return CohortResult(
        peptide=peptide_name,
        biomarker_name=biomarker_name,
        n_patients=len(seen_patients),
        n_measurements=len(trajectories),
        expected=expected_dict,
        trajectories=trajectories,
        time_bins=time_bins,
        dose_response=dose_response,
    )


# ── Catalog endpoints ───────────────────────────────────────────────────────

def available_biomarkers(conn, peptide_name: str) -> list[dict[str, Any]]:
    """Return measurements panel + count of observed values per marker."""
    panel = get_biomarker_panel(peptide_name)
    if panel is None:
        return []
    from .service import _ph
    ph = _ph(conn)
    counts = {
        row["biomarker_name"]: row["n"]
        for row in conn.execute(
            f"""SELECT m.biomarker_name AS biomarker_name, COUNT(*) AS n
               FROM measurements m
               JOIN treatments t ON t.patient_id = m.patient_id
               WHERE t.peptide_name = {ph}
               GROUP BY m.biomarker_name""",
            (peptide_name,),
        ).fetchall()
    }
    out: list[dict[str, Any]] = []
    for m in panel.measurements:
        d = m.to_dict()
        d["n_observed"] = counts.get(m.name, 0)
        out.append(d)
    return out


# ── Bayesian per-patient predictions ────────────────────────────────────────

def _weeks_since(start: str, when: str) -> float | None:
    return _weeks_between(start, when)


def _tau_for(expected: BiomarkerMeasurement | None,
             *, default_weeks: float = 4.0) -> float:
    """Use the panel's expected timeframe as the approach time constant."""
    if expected is None:
        return default_weeks
    if expected.timeframe_weeks_max:
        return max(expected.timeframe_weeks_max / 2.0, 1.0)
    if expected.timeframe_weeks_min:
        return max(expected.timeframe_weeks_min, 1.0)
    return default_weeks


def predict_response(
    conn,
    *,
    patient_id: str,
    peptide_name: str,
    biomarker_name: str,
) -> dict[str, Any]:
    """Bayesian prediction for one (patient, peptide, biomarker).

    Returns a payload containing:
      - prior:           GeneticPrior derived from the patient's profile
      - likelihood:      effective observation summarising measurements
      - posterior:       Normal-Normal update
      - expected:        the BiomarkerMeasurement panel entry (for context)
      - baseline:        baseline value used (median of pre-window measurements)
      - posterior_predictive: trajectory + 95% credible band over weeks
      - prior_predictive:     same shape, using only the genetic prior
    """
    panel = get_biomarker_panel(peptide_name)
    expected: BiomarkerMeasurement | None = None
    if panel is not None:
        target = biomarker_name.lower().strip()
        for m in panel.measurements:
            if m.name.lower().strip() == target:
                expected = m
                break

    # ── Prior from genetics ──
    # The prior is biomarker-specific: μ = r · expected_pct_panel[biomarker].
    # That keeps the prior mean in the right direction and magnitude per
    # biomarker (e.g. HbA1c gets a small negative prior, GH peak a large
    # positive one), rather than a one-size-fits-all peptide-level number.
    expected_pct = expected_pct_change(expected, biomarker_name)
    raw = service.get_genetic_profile_json(conn, patient_id)
    if raw is None:
        prior = None
        # No genetics: prior centred on the panel's expected effect with
        # wide uncertainty (responder strength unknown, treat as 1.0 ± 0.4).
        prior_mean = expected_pct
        prior_sd = max(0.04, 0.4 * abs(expected_pct))
    else:
        profile = GeneticProfile.from_json(raw[0])
        prior = derive_prior(
            profile,
            peptide_name,
            expected_pct=expected_pct,
            biomarker_name=biomarker_name,
        )
        prior_mean, prior_sd = prior.mean_pct_change, prior.sd_pct_change

    # ── Find the active treatment for this peptide ──
    treatments = service.list_treatments_for_patient(conn, patient_id)
    treatment = next((t for t in treatments if t.peptide_name == peptide_name), None)

    measurements = service.list_measurements_for_patient(
        conn, patient_id, biomarker_name=biomarker_name
    )

    # Time-align measurements to treatment_start. If there's no treatment,
    # we still expose the prior but cannot fit a likelihood.
    observations: list[tuple[float, float]] = []
    if treatment is not None:
        for m in measurements:
            w = _weeks_since(treatment.start_date, m.measured_at)
            if w is None or w < 0:
                continue
            observations.append((w, m.value))

    tau = _tau_for(expected)

    # Baseline prior: anchor on the panel's documented physiologic baseline
    # (BIOMARKER_PARAMS) with ~30% relative SD. If the patient has a
    # genuine pre-treatment measurement, tighten the prior around that
    # observed value instead. The joint fit then disentangles baseline b
    # and θ from the measurements regardless of whether a sample was
    # taken before treatment started.
    panel_params = params_for(expected, biomarker_name)
    baseline_prior_mean = panel_params.baseline if panel_params.baseline > 0 else 100.0
    baseline_prior_sd = max(abs(baseline_prior_mean) * 0.30, 1.0)

    pre_baseline_values = [y for w, y in observations if w < 1.0]
    if pre_baseline_values:
        observed_baseline = statistics.median(pre_baseline_values)
        if observed_baseline > 0:
            baseline_prior_mean = observed_baseline
            baseline_prior_sd = max(observed_baseline * 0.08, 0.5)

    # Empirical-Bayes pooling: refine the genetic prior with cohort-derived
    # evidence of how other patients on this (peptide, biomarker) actually
    # respond. The donor pool excludes this patient (leave-one-out), so the
    # combined prior is honest about what we know *before* seeing the
    # patient's own data. With < pooling.MIN_DONORS donors or a degenerate
    # cohort, ``estimate_population_prior`` returns None and ``combine_priors``
    # is a no-op.
    donors = pooling.collect_donor_fits(
        conn,
        peptide_name=peptide_name,
        biomarker_name=biomarker_name,
        tau_weeks=tau,
        baseline_prior_mean=(
            panel_params.baseline if panel_params.baseline > 0 else 100.0
        ),
        baseline_prior_sd=max(
            abs(panel_params.baseline if panel_params.baseline > 0 else 100.0) * 0.30,
            1.0,
        ),
        noise_pct=panel_params.noise_pct,
        exclude_patient_id=patient_id,
    )
    population_prior = pooling.estimate_population_prior(
        donors, peptide=peptide_name, biomarker=biomarker_name,
    )
    prior_mean, prior_sd = pooling.combine_priors(
        genetic_mean=prior_mean,
        genetic_sd=prior_sd,
        population=population_prior,
    )

    fit = (
        bayes.joint_fit_likelihood(
            observations=observations,
            tau_weeks=tau,
            baseline_prior_mean=baseline_prior_mean,
            baseline_prior_sd=baseline_prior_sd,
            noise_pct=panel_params.noise_pct,
        )
        if observations else None
    )
    if fit is not None:
        likelihood = fit.likelihood
        baseline = fit.baseline
        baseline_sd = fit.baseline_sd
    else:
        likelihood = None
        baseline = bayes.estimate_baseline(observations)
        # No fit → baseline came from a single measurement (or panel
        # fallback); treat it as deterministic so the predictive curve
        # falls back to the old behaviour.
        baseline_sd = 0.0
        # Brand-new patient: no usable measurements yet, so
        # ``estimate_baseline`` returns None and the predictive curves
        # would come back empty — leaving the chart blank exactly when the
        # *prior* prediction ("what we expect before any data") is the only
        # thing we have to show. Anchor on the panel's documented
        # physiologic baseline and carry its uncertainty so the prior
        # predictive renders a credible band around the genetic prior.
        if baseline is None and baseline_prior_mean > 0:
            baseline = baseline_prior_mean
            baseline_sd = baseline_prior_sd

    # When a pre-treatment measurement directly pins b, propagating its
    # joint-fit σ_b through ``predictive_curve`` ends up double-counting
    # uncertainty already absorbed by σ_θ (via the delta-method in
    # joint_fit_likelihood). The calibration backtest flagged this as
    # 100% predictive-band coverage. Treat baseline as observed when we
    # have pre-treatment samples; only carry σ_b forward when the fit
    # had to infer baseline from post-treatment data alone.
    if pre_baseline_values:
        baseline_sd = 0.0

    posterior = bayes.update(
        prior_mean=prior_mean,
        prior_sd=prior_sd,
        likelihood=likelihood,
    )

    # ── Predictive trajectories ──
    #
    # Project past the last observation so the user sees where the
    # marker is heading at the current dose, not just the fitted region.
    # The horizon is the largest of:
    #   - 52 weeks (one year — typical clinical follow-up window)
    #   - 3·τ (~95% of asymptotic approach; lets the user see the plateau)
    #   - last_observed_week + 16 (so projection always extends materially
    #     past the most recent measurement)
    # The grid stays dense early (when a(w) is changing fast) and sparse
    # late (where the curve has plateaued and extra points add nothing).
    max_w = max((w for w, _ in observations), default=0.0)
    cap = max(52.0, 3.0 * tau, max_w + 16.0)
    week_grid = [
        round(x, 2)
        for x in (
            0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0, 26.0,
            36.0, 52.0, 78.0, 104.0,
        )
        if x <= cap
    ]
    if not week_grid or week_grid[-1] < cap:
        week_grid.append(round(cap, 2))

    posterior_predictive = (
        bayes.predictive_curve(
            baseline=baseline,
            posterior=posterior,
            tau_weeks=tau,
            week_grid=week_grid,
            baseline_sd=baseline_sd,
        )
        if baseline is not None else bayes.PredictiveCurve(points=[])
    )

    # Prior-only predictive: posterior == prior (no likelihood). Carry
    # the prior's own baseline uncertainty (the panel-prior SD) so the
    # dashed prior curve doesn't claim more precision than the data did.
    prior_only = bayes.update(prior_mean=prior_mean, prior_sd=prior_sd, likelihood=None)
    prior_predictive = (
        bayes.predictive_curve(
            baseline=baseline,
            posterior=prior_only,
            tau_weeks=tau,
            week_grid=week_grid,
            baseline_sd=baseline_prior_sd if observations else baseline_sd,
        )
        if baseline is not None else bayes.PredictiveCurve(points=[])
    )

    # Bayes-informed expected timeframe: when do we expect the change to
    # show up, and when has it plateaued, given the posterior?
    posterior_window = bayes.expected_window(posterior=posterior, tau_weeks=tau)
    prior_window = bayes.expected_window(posterior=prior_only, tau_weeks=tau)

    return {
        "patient_id": patient_id,
        "peptide": peptide_name,
        "biomarker_name": biomarker_name,
        "expected": expected.to_dict() if expected else None,
        "treatment_id": treatment.id if treatment else None,
        "treatment_start": treatment.start_date if treatment else None,
        "tau_weeks": tau,
        "baseline": baseline,
        "n_measurements": len(observations),
        # Last week with an observed measurement. Frontend uses this to
        # visually distinguish the fitted region (≤ last_observed_week)
        # from the forward projection. None when no measurements exist.
        "last_observed_week": max_w if observations else None,
        "prior": prior.to_dict() if prior else None,
        "population_prior": (
            population_prior.to_dict() if population_prior else None
        ),
        "likelihood": likelihood.to_dict() if likelihood else None,
        "posterior": posterior.to_dict(),
        "posterior_predictive": posterior_predictive.to_dict(),
        "prior_predictive": prior_predictive.to_dict(),
        "expected_window": posterior_window.to_dict(),
        "prior_expected_window": prior_window.to_dict(),
    }


def peptides_with_data(conn) -> list[dict[str, Any]]:
    """List peptides that have at least one treatment recorded."""
    rows = conn.execute(
        """SELECT t.peptide_name AS peptide_name,
                  COUNT(DISTINCT t.patient_id) AS n_patients,
                  COUNT(DISTINCT t.id) AS n_treatments,
                  COUNT(m.id) AS n_measurements
           FROM treatments t
           LEFT JOIN measurements m
             ON m.patient_id = t.patient_id
            AND (m.treatment_id IS NULL OR m.treatment_id = t.id)
           GROUP BY t.peptide_name
           ORDER BY n_patients DESC, t.peptide_name""",
    ).fetchall()
    return [dict(r) for r in rows]
