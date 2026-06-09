"""
engine/tracking/bayes.py
========================
Normal-Normal conjugate Bayesian update for peptide-response predictions.

The model
---------
For one (patient, peptide, biomarker) we treat the latent quantity θ as the
fractional change from baseline at the panel's expected timeframe — e.g.
θ = 0.30 means "IGF-1 will end up +30% above baseline once the effect
plateaus."

Prior:        θ ~ Normal(μ₀, σ₀²)            from the genetic profile
Likelihood:   ŷᵢ | θ ~ Normal(θ · a(wᵢ), σ²) where a(w) = 1 − exp(−w/τ)
                                              is the panel's expected
                                              approach curve

We summarise the patient's observed measurements as one effective
observation (ȳ, σ̄) of θ, using the inverse-variance combination of each
post-baseline measurement after dividing by its approach factor.

Posterior is then the standard Normal-Normal conjugate:
    τ_post  = τ_prior + n_eff/σ_obs²
    μ_post  = (τ_prior·μ_prior + τ_obs·ȳ) / τ_post

Posterior predictive at week w:
    value(w) ~ Normal(baseline · (1 + μ_post · a(w)),
                       baseline² · a(w)² · σ_post² + σ_meas²)
For the chart we usually want the credible band on the mean curve
(without measurement noise), since the noise is per-point not structural.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Sequence


_Z95 = 1.959963984540054  # qnorm(0.975)


@dataclass(frozen=True)
class Likelihood:
    """Effective observation of θ derived from the measurements."""
    mean_pct_change: float       # ȳ
    sd_pct_change: float         # σ̄ (per-observation noise on θ)
    n_observations: int
    baseline: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_pct_change": round(self.mean_pct_change, 4),
            "sd_pct_change": round(self.sd_pct_change, 4),
            "n_observations": self.n_observations,
            "baseline": round(self.baseline, 4),
        }


@dataclass(frozen=True)
class Posterior:
    """Posterior on θ after combining prior with likelihood."""
    mean_pct_change: float
    sd_pct_change: float
    credible_lo_95: float
    credible_hi_95: float
    n_effective: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_pct_change": round(self.mean_pct_change, 4),
            "sd_pct_change": round(self.sd_pct_change, 4),
            "credible_lo_95": round(self.credible_lo_95, 4),
            "credible_hi_95": round(self.credible_hi_95, 4),
            "n_effective": round(self.n_effective, 2),
        }


@dataclass
class PredictivePoint:
    weeks_since_start: float
    mean: float
    lo_95: float
    hi_95: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "weeks_since_start": round(self.weeks_since_start, 2),
            "mean": round(self.mean, 4),
            "lo_95": round(self.lo_95, 4),
            "hi_95": round(self.hi_95, 4),
        }


@dataclass
class PredictiveCurve:
    points: list[PredictivePoint] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"points": [p.to_dict() for p in self.points]}


# ── Helpers ─────────────────────────────────────────────────────────────────

def approach(weeks: float, tau_weeks: float) -> float:
    """Exponential approach factor a(w) = 1 - exp(-w/τ). Clamped to ≥ 0."""
    if tau_weeks <= 0:
        return 1.0
    return 1.0 - math.exp(-max(weeks, 0.0) / tau_weeks)


def effective_observation(
    *,
    baseline: float,
    observations: Sequence[tuple[float, float]],   # (weeks_since_start, value)
    tau_weeks: float,
    noise_pct: float = 0.10,
    min_weeks: float = 0.5,
) -> Likelihood | None:
    """Summarise a series of (week, value) measurements as one observation of θ.

    Each post-baseline measurement is converted to an estimate of θ via:
        θ̂ᵢ = (yᵢ / baseline - 1) / a(wᵢ)
    These are pooled inverse-variance. Observations with a(wᵢ) close to zero
    are discarded because they carry almost no information about θ.

    Returns None if no usable observations.
    """
    if baseline <= 0 or not observations:
        return None
    theta_hats: list[tuple[float, float]] = []
    for w, y in observations:
        a = approach(w, tau_weeks)
        if w < min_weeks or a < 0.1:
            continue
        theta_hat = (y / baseline - 1.0) / a
        # Per-observation σ on θ̂ = (σ_y / baseline) / a(w); σ_y ≈ baseline · noise_pct.
        sigma_i = noise_pct / a
        theta_hats.append((theta_hat, sigma_i))

    if not theta_hats:
        return None

    # Inverse-variance pooling: τ_pool = Σ 1/σᵢ²; μ_pool = Σ θᵢ/σᵢ² / τ_pool
    tau_total = sum(1.0 / (s * s) for _, s in theta_hats)
    mu_pool = sum(t / (s * s) for t, s in theta_hats) / tau_total
    sd_pool = math.sqrt(1.0 / tau_total)

    return Likelihood(
        mean_pct_change=mu_pool,
        sd_pct_change=sd_pool,
        n_observations=len(theta_hats),
        baseline=baseline,
    )


# ── Conjugate update ────────────────────────────────────────────────────────

def update(
    *,
    prior_mean: float,
    prior_sd: float,
    likelihood: Likelihood | None,
) -> Posterior:
    """Normal-Normal conjugate update for the latent θ."""
    if prior_sd <= 0:
        prior_sd = 1e-3
    tau_prior = 1.0 / (prior_sd * prior_sd)

    if likelihood is None:
        mu_post, sd_post, n_eff = prior_mean, prior_sd, 0.0
    else:
        tau_like = 1.0 / (likelihood.sd_pct_change * likelihood.sd_pct_change)
        tau_post = tau_prior + tau_like
        mu_post = (tau_prior * prior_mean + tau_like * likelihood.mean_pct_change) / tau_post
        sd_post = math.sqrt(1.0 / tau_post)
        n_eff = tau_like / tau_prior

    return Posterior(
        mean_pct_change=mu_post,
        sd_pct_change=sd_post,
        credible_lo_95=mu_post - _Z95 * sd_post,
        credible_hi_95=mu_post + _Z95 * sd_post,
        n_effective=n_eff,
    )


# ── Posterior predictive trajectory ─────────────────────────────────────────

def predictive_curve(
    *,
    baseline: float,
    posterior: Posterior,
    tau_weeks: float,
    week_grid: Sequence[float],
) -> PredictiveCurve:
    """Project the posterior on θ forward through the approach curve, producing
    a mean trajectory in value-space with a 95% credible band."""
    pts: list[PredictivePoint] = []
    for w in week_grid:
        a = approach(w, tau_weeks)
        mean_val = baseline * (1.0 + posterior.mean_pct_change * a)
        delta = _Z95 * abs(baseline) * a * posterior.sd_pct_change
        pts.append(PredictivePoint(
            weeks_since_start=w,
            mean=mean_val,
            lo_95=mean_val - delta,
            hi_95=mean_val + delta,
        ))
    return PredictiveCurve(points=pts)


def estimate_baseline(observations: Sequence[tuple[float, float]],
                      *, baseline_window_weeks: float = 1.5) -> float | None:
    """Estimate baseline from measurements taken before `baseline_window_weeks`.
    Falls back to the earliest measurement if no pre-window points exist."""
    if not observations:
        return None
    early = [y for w, y in observations if w < baseline_window_weeks]
    if early:
        return statistics.median(early)
    # Fallback: take the chronologically earliest measurement.
    return min(observations, key=lambda kv: kv[0])[1]
