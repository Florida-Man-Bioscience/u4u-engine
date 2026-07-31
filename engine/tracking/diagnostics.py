"""
engine/tracking/diagnostics.py
==============================
Predictive-performance diagnostics for the Bayesian response model.

Where ``test_calibration.py`` checks calibration on *synthetic* data (draw a
truth, simulate, measure coverage), this module measures how well the model
predicts the *real* measurements already recorded in the tracking DB. It runs
a leave-one-out backtest:

    For every (patient, peptide, biomarker) series with enough post-treatment
    measurements, hold out one measurement at a time, refit the model on the
    remaining points, and compare the held-out point's predicted value (and
    95% predictive band) against what was actually observed.

Aggregating the held-out points gives three headline numbers a reviewer can
act on:

  - **MAE / RMSE** (as a percent of baseline, so they're comparable across
    biomarkers on wildly different scales) — how far off the point prediction
    is on average.
  - **95% coverage** — the fraction of held-out observations that landed
    inside the model's 95% predictive band. A well-calibrated model lands
    near 0.95; much lower means the bands are too tight (over-confident),
    much higher means they're too wide.
  - **bias** — mean signed error, to expose systematic over/under-prediction.

The backtest deliberately exercises the documented genetics + likelihood
reference path (the same one pinned by the genetics-only section of the
calibration backtest): it does not fold in cohort pooling or HealthKit
proxies, so the number reflects the core model rather than the incidental
composition of the demo cohort. Everything is plain stdlib math — no
numpy/pandas — matching the rest of ``engine/tracking``.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any

from . import bayes, service
from .analysis import _expected_for, _tau_for, _weeks_since
from .biomarker_params import expected_pct_change, params_for
from .genetics import GeneticProfile, derive_prior

# A biomarker series needs at least this many post-treatment observations for a
# leave-one-out backtest to be meaningful: hold one out and still leave enough
# behind to fit baseline + θ.
MIN_SERIES_POINTS = 3


@dataclass
class BacktestPoint:
    """One held-out prediction vs. its actual observed value."""
    patient_id: str
    patient_label: str
    peptide: str
    biomarker: str
    weeks_since_start: float
    baseline: float
    predicted: float
    predicted_lo_95: float
    predicted_hi_95: float
    observed: float
    covered: bool

    @property
    def error(self) -> float:
        return self.observed - self.predicted

    @property
    def pct_error(self) -> float:
        """Signed error as a percent of baseline (scale-free)."""
        denom = abs(self.baseline) if self.baseline else 1.0
        return 100.0 * self.error / denom

    def to_dict(self) -> dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "patient_label": self.patient_label,
            "peptide": self.peptide,
            "biomarker": self.biomarker,
            "weeks_since_start": round(self.weeks_since_start, 2),
            "baseline": round(self.baseline, 4),
            "predicted": round(self.predicted, 4),
            "predicted_lo_95": round(self.predicted_lo_95, 4),
            "predicted_hi_95": round(self.predicted_hi_95, 4),
            "observed": round(self.observed, 4),
            "covered": self.covered,
            "pct_error": round(self.pct_error, 2),
        }


@dataclass
class GroupMetrics:
    """Aggregate metrics over a set of held-out points."""
    label: str
    n_points: int
    n_series: int
    coverage_95: float | None
    mae_pct: float | None
    rmse_pct: float | None
    bias_pct: float | None

    def to_dict(self) -> dict[str, Any]:
        def r(x: float | None) -> float | None:
            return None if x is None else round(x, 3)

        return {
            "label": self.label,
            "n_points": self.n_points,
            "n_series": self.n_series,
            "coverage_95": r(self.coverage_95),
            "mae_pct": r(self.mae_pct),
            "rmse_pct": r(self.rmse_pct),
            "bias_pct": r(self.bias_pct),
        }


def _metrics(label: str, points: list[BacktestPoint], n_series: int) -> GroupMetrics:
    if not points:
        return GroupMetrics(label, 0, n_series, None, None, None, None)
    pct_errors = [p.pct_error for p in points]
    coverage = sum(1 for p in points if p.covered) / len(points)
    mae = statistics.fmean(abs(e) for e in pct_errors)
    rmse = math.sqrt(statistics.fmean(e * e for e in pct_errors))
    bias = statistics.fmean(pct_errors)
    return GroupMetrics(label, len(points), n_series, coverage, mae, rmse, bias)


def _predict_heldout(
    *,
    observations: list[tuple[float, float]],
    target_week: float,
    tau: float,
    prior_mean: float,
    prior_sd: float,
    baseline_panel: float,
    noise_pct: float,
) -> tuple[float, float, float] | None:
    """Fit the genetics-prior + joint-fit model on ``observations`` and return
    the (mean, lo_95, hi_95) predicted value at ``target_week``.

    Mirrors the reference path of ``analysis.predict_response`` (baseline
    prior, joint fit, conjugate update, predictive curve) but on an explicit
    training subset so the caller can hold points out.
    """
    if not observations:
        return None

    baseline_prior_mean = baseline_panel if baseline_panel > 0 else 100.0
    baseline_prior_sd = max(abs(baseline_prior_mean) * 0.30, 1.0)
    pre_baseline_values = [y for w, y in observations if w < 1.0]
    if pre_baseline_values:
        observed_baseline = statistics.median(pre_baseline_values)
        if observed_baseline > 0:
            baseline_prior_mean = observed_baseline
            baseline_prior_sd = max(observed_baseline * 0.08, 0.5)

    fit = bayes.joint_fit_likelihood(
        observations=observations,
        tau_weeks=tau,
        baseline_prior_mean=baseline_prior_mean,
        baseline_prior_sd=baseline_prior_sd,
        noise_pct=noise_pct,
    )
    baseline = fit.baseline
    baseline_sd = fit.baseline_sd
    # A pre-treatment sample pins the baseline directly; carrying σ_b forward
    # then double-counts uncertainty already in σ_θ (same reasoning as
    # predict_response), so treat it as observed.
    if pre_baseline_values:
        baseline_sd = 0.0

    posterior = bayes.update(
        prior_mean=prior_mean, prior_sd=prior_sd, likelihood=fit.likelihood,
    )
    curve = bayes.predictive_curve(
        baseline=baseline,
        posterior=posterior,
        tau_weeks=tau,
        week_grid=[target_week],
        baseline_sd=baseline_sd,
    )
    if not curve.points:
        return None
    pt = curve.points[0]
    return pt.mean, pt.lo_95, pt.hi_95


def _backtest_series(
    conn,
    *,
    patient_id: str,
    patient_label: str,
    peptide_name: str,
    biomarker_name: str,
    observations: list[tuple[float, float]],
) -> list[BacktestPoint]:
    """Leave-one-out backtest of one (patient, peptide, biomarker) series."""
    expected = _expected_for(peptide_name, biomarker_name)
    tau = _tau_for(expected)
    panel_params = params_for(expected, biomarker_name)
    expected_pct = expected_pct_change(expected, biomarker_name)

    # Genetic prior on θ (same derivation as predict_response). Falls back to
    # the panel-expected effect with wide uncertainty when the patient has no
    # stored genetic profile.
    raw = service.get_genetic_profile_json(conn, patient_id)
    if raw is None:
        prior_mean = expected_pct
        prior_sd = max(0.04, 0.4 * abs(expected_pct))
    else:
        profile = GeneticProfile.from_json(raw[0])
        prior = derive_prior(
            profile, peptide_name,
            expected_pct=expected_pct, biomarker_name=biomarker_name,
        )
        prior_mean, prior_sd = prior.mean_pct_change, prior.sd_pct_change

    points: list[BacktestPoint] = []
    for i, (w_h, y_h) in enumerate(observations):
        # Only hold out post-treatment points — a pre-baseline point carries no
        # response signal to predict, and removing it would strip the baseline
        # anchor from the training set.
        if w_h < 1.0:
            continue
        train = observations[:i] + observations[i + 1:]
        if len(train) < 2:
            continue
        pred = _predict_heldout(
            observations=train,
            target_week=w_h,
            tau=tau,
            prior_mean=prior_mean,
            prior_sd=prior_sd,
            baseline_panel=panel_params.baseline,
            noise_pct=panel_params.noise_pct,
        )
        if pred is None:
            continue
        mean, lo, hi = pred
        # Baseline the error is normalised against: the training fit's own
        # baseline estimate (median of pre-window training points, else panel).
        fit_baseline = statistics.median(
            [y for w, y in train if w < 1.0]
        ) if any(w < 1.0 for w, _ in train) else (
            panel_params.baseline if panel_params.baseline > 0 else 100.0
        )
        points.append(BacktestPoint(
            patient_id=patient_id,
            patient_label=patient_label,
            peptide=peptide_name,
            biomarker=biomarker_name,
            weeks_since_start=w_h,
            baseline=fit_baseline,
            predicted=mean,
            predicted_lo_95=lo,
            predicted_hi_95=hi,
            observed=y_h,
            covered=lo <= y_h <= hi,
        ))
    return points


def run_diagnostics(conn, patients: list[service.Patient]) -> dict[str, Any]:
    """Leave-one-out backtest across the given patients.

    Returns overall metrics, per-peptide and per-biomarker breakdowns, and the
    raw held-out points (predicted vs observed) for a scatter plot.
    """
    all_points: list[BacktestPoint] = []
    series_count = 0
    peptide_series: dict[str, int] = {}
    biomarker_series: dict[str, int] = {}

    for patient in patients:
        treatments = service.list_treatments_for_patient(conn, patient.id)
        if not treatments:
            continue
        measurements = service.list_measurements_for_patient(conn, patient.id)
        # Group measurements by biomarker.
        by_biomarker: dict[str, list] = {}
        for m in measurements:
            by_biomarker.setdefault(m.biomarker_name, []).append(m)

        for treatment in treatments:
            for biomarker_name, rows in by_biomarker.items():
                observations: list[tuple[float, float]] = []
                for m in rows:
                    w = _weeks_since(treatment.start_date, m.measured_at)
                    if w is None or w < 0:
                        continue
                    observations.append((w, m.value))
                observations.sort(key=lambda kv: kv[0])
                if len(observations) < MIN_SERIES_POINTS:
                    continue
                pts = _backtest_series(
                    conn,
                    patient_id=patient.id,
                    patient_label=patient.label,
                    peptide_name=treatment.peptide_name,
                    biomarker_name=biomarker_name,
                    observations=observations,
                )
                if not pts:
                    continue
                series_count += 1
                peptide_series[treatment.peptide_name] = (
                    peptide_series.get(treatment.peptide_name, 0) + 1
                )
                biomarker_series[biomarker_name] = (
                    biomarker_series.get(biomarker_name, 0) + 1
                )
                all_points.extend(pts)

    overall = _metrics("overall", all_points, series_count)

    by_peptide = []
    for name in sorted(peptide_series):
        pts = [p for p in all_points if p.peptide == name]
        by_peptide.append(_metrics(name, pts, peptide_series[name]).to_dict())

    by_biomarker = []
    for name in sorted(biomarker_series):
        pts = [p for p in all_points if p.biomarker == name]
        by_biomarker.append(_metrics(name, pts, biomarker_series[name]).to_dict())

    return {
        "method": "leave-one-out",
        "reference_path": "genetics+likelihood",
        "min_series_points": MIN_SERIES_POINTS,
        "n_patients": len(patients),
        "n_series": series_count,
        "n_points": len(all_points),
        "overall": overall.to_dict(),
        "by_peptide": by_peptide,
        "by_biomarker": by_biomarker,
        "points": [p.to_dict() for p in all_points],
    }
