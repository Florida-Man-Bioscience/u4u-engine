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
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

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


@dataclass(frozen=True)
class JointFit:
    """Return shape of :func:`joint_fit_likelihood`.

    ``likelihood`` is the marginal likelihood on θ for the conjugate
    update. ``baseline`` and ``baseline_sd`` are the posterior mean and
    SD of ``b`` — exposed so :func:`predictive_curve` can carry baseline
    uncertainty into the credible bands when no pre-treatment sample was
    available.
    """
    likelihood: Likelihood
    baseline: float
    baseline_sd: float


@dataclass(frozen=True)
class ExpectedWindow:
    """Bayes-informed window in which the biomarker is expected to change.

    Derived from the posterior on θ together with the panel-derived time
    constant τ: weeks_min is when the predicted change first reaches
    ``detection_fraction`` of its asymptote, weeks_max is when it has
    plateaued (``plateau_fraction`` of asymptote).

    ``credible`` is True iff the 95% credible interval on θ excludes 0,
    i.e. we are statistically confident the biomarker will move at all.
    When False, the window is still defined (so the chart has something to
    draw) but the direction is reported as 'inconclusive'.
    """
    weeks_min: float
    weeks_max: float
    direction: str
    asymptote_pct_change: float
    credible: bool
    detection_fraction: float
    plateau_fraction: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "weeks_min": round(self.weeks_min, 2),
            "weeks_max": round(self.weeks_max, 2),
            "direction": self.direction,
            "asymptote_pct_change": round(self.asymptote_pct_change, 4),
            "credible": self.credible,
            "detection_fraction": self.detection_fraction,
            "plateau_fraction": self.plateau_fraction,
        }


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
    baseline_sd: float = 0.0,
) -> PredictiveCurve:
    """Project the posterior on θ forward through the approach curve,
    producing a mean trajectory in value-space with a 95% credible band.

    When ``baseline_sd > 0`` the band also incorporates baseline
    uncertainty — appropriate when the baseline was estimated from the
    measurements themselves rather than measured pre-treatment. The
    decomposition treats baseline and θ as independent (a conservative
    overstatement of uncertainty post-update) and propagates::

        V(w) = b · (1 + θ · a(w))
        Var(V) ≈ σ_b² · (1 + μ_θ · a)² + b² · a² · σ_θ²

    With ``baseline_sd = 0`` (the default and pre-existing behaviour),
    the band shrinks to ±1.96 · |b| · a(w) · σ_θ — the old formula.
    """
    pts: list[PredictivePoint] = []
    sigma_b2 = baseline_sd ** 2
    for w in week_grid:
        a = approach(w, tau_weeks)
        mean_val = baseline * (1.0 + posterior.mean_pct_change * a)
        var_v = (
            sigma_b2 * (1.0 + posterior.mean_pct_change * a) ** 2
            + (baseline ** 2) * (a ** 2) * (posterior.sd_pct_change ** 2)
        )
        delta = _Z95 * math.sqrt(max(var_v, 0.0))
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


# ── Joint Bayesian fit for (baseline, θ) ────────────────────────────────────

def joint_fit_likelihood(
    *,
    observations: Sequence[tuple[float, float]],
    tau_weeks: float,
    baseline_prior_mean: float,
    baseline_prior_sd: float,
    noise_pct: float = 0.10,
    min_weeks: float = 0.0,
    noise_scales: Sequence[float] | None = None,
) -> JointFit | None:
    """Jointly estimate baseline ``b`` and θ from raw measurements.

    Model
    -----
        y_i = b · (1 + θ · a(w_i)) + ε_i,    ε_i ~ N(0, (σ·s_i)²)

    Reparameterised as a linear regression in (b, φ) with φ ≡ b·θ::

        y_i = b + φ · a(w_i) + ε_i

    Prior:  b ~ Normal(b₀, σ_b²) (informative — typically the panel's
            documented physiologic baseline). φ has an essentially flat
            prior so the data drives the slope.

    The likelihood on θ is recovered via the delta method::

        θ̂ = φ̂ / b̂
        Var(θ̂) ≈ Var(φ̂)/b̂² + Var(b̂)·φ̂²/b̂⁴ − 2·Cov(b̂,φ̂)·φ̂/b̂³

    Per-observation noise scales
    ----------------------------
    ``noise_scales`` optionally supplies a per-observation multiplier ``s_i``
    on the measurement standard deviation, turning the fit into a *weighted*
    least-squares regression with weights ``w_i = 1/s_iⁿ²``. This lets a
    noisier data source (e.g. wearable-derived HealthKit proxies) inform the
    posterior without swamping tighter clinical labs — a scale of 2.0 makes
    an observation count for a quarter of the information of a lab value.
    ``None`` (the default) means every observation has scale 1.0, which
    reduces exactly to the ordinary-least-squares fit — existing
    clinical-only behaviour is byte-for-byte unchanged.

    Why this matters
    ----------------
    The previous approach used the earliest measurement as baseline. If
    that measurement was already weeks into treatment, the baseline got
    biased upward and θ̂ collapsed toward zero. The joint fit instead
    anchors b on the panel's documented baseline and lets the slope across
    the approach curve a(w) reveal θ, regardless of whether a pre-baseline
    sample exists.

    Returns ``(Likelihood, refined_baseline)`` or ``None`` if the system
    is underdetermined (e.g. zero usable observations).
    """
    if noise_scales is None:
        paired = [(w, y, 1.0) for w, y in observations if w >= min_weeks]
    else:
        if len(noise_scales) != len(observations):
            raise ValueError("noise_scales must align 1:1 with observations")
        if any(s <= 0 for s in noise_scales):
            raise ValueError("noise_scales must be strictly positive")
        paired = [
            (w, y, s)
            for (w, y), s in zip(observations, noise_scales, strict=True)
            if w >= min_weeks
        ]
    if not paired:
        return None
    if baseline_prior_mean <= 0 or baseline_prior_sd <= 0:
        return None

    a_vec = [approach(w, tau_weeks) for w, _, _ in paired]
    y_vec = [y for _, y, _ in paired]
    # Precision weight per observation: 1/s_iⁿ². s_i = 1 → weight 1 → OLS.
    wt_vec = [1.0 / (s * s) for _, _, s in paired]
    n = len(paired)

    # Initial σ² from the panel's noise estimate; refined from residuals.
    sigma2 = max((noise_pct * baseline_prior_mean) ** 2, 1e-9)
    sigma_b2 = baseline_prior_sd ** 2
    # Very weak prior on φ — used only to prevent singularity when every
    # measurement is at the same a(w) (rare but possible).
    sigma_phi2 = max((10.0 * baseline_prior_sd) ** 2, 1.0)

    sw = sum(wt_vec)
    sx = sum(wt * a for wt, a in zip(wt_vec, a_vec, strict=False))
    sxx = sum(wt * a * a for wt, a in zip(wt_vec, a_vec, strict=False))
    sy = sum(wt * y for wt, y in zip(wt_vec, y_vec, strict=False))
    sxy = sum(wt * a * y for wt, a, y in zip(wt_vec, a_vec, y_vec, strict=False))

    b_hat = baseline_prior_mean
    phi_hat = 0.0
    var_b = sigma_b2
    var_phi = sigma_phi2
    cov_bp = 0.0

    for _ in range(4):
        # Posterior precision Λ = Xᵀ W X/σ² + diag(1/σ_b², 1/σ_φ²)
        A = sw / sigma2 + 1.0 / sigma_b2
        B = sx / sigma2
        D = sxx / sigma2 + 1.0 / sigma_phi2

        det = A * D - B * B
        if abs(det) < 1e-18:
            return None

        rhs0 = sy / sigma2 + baseline_prior_mean / sigma_b2
        rhs1 = sxy / sigma2  # φ prior centred at 0 → no contribution

        # μ = Λ⁻¹ · rhs;   Σ = Λ⁻¹
        b_hat = (D * rhs0 - B * rhs1) / det
        phi_hat = (-B * rhs0 + A * rhs1) / det
        var_b = D / det
        var_phi = A / det
        cov_bp = -B / det

        if n >= 3:
            # Refine σ² from weighted residuals (degrees of freedom = n − 2).
            resid = [y - (b_hat + phi_hat * a) for y, a in zip(y_vec, a_vec, strict=False)]
            ss = sum(wt * r * r for wt, r in zip(wt_vec, resid, strict=False))
            df = max(n - 2, 1)
            sigma2_new = ss / df
            # Floor σ² at ~25% of the panel-noise estimate to avoid
            # underconfidence on tightly-fitted but small samples.
            sigma2_new = max(sigma2_new, 0.25 * (noise_pct * abs(b_hat)) ** 2)
            if abs(sigma2_new - sigma2) / sigma2 < 1e-3:
                sigma2 = sigma2_new
                break
            sigma2 = sigma2_new

    if b_hat <= 0:
        return None

    theta_hat = phi_hat / b_hat
    # Delta-method variance on θ = φ / b.
    var_theta = (
        var_phi / (b_hat ** 2)
        + var_b * (phi_hat ** 2) / (b_hat ** 4)
        - 2.0 * cov_bp * phi_hat / (b_hat ** 3)
    )
    # Effective sample size (Kish): n_eff = (Σw)² / Σw². With uniform weights
    # (the clinical-only / noise_scales=None path) n_eff == n exactly, so the
    # floor and t-inflation below are byte-for-byte unchanged. When noisier,
    # down-weighted observations are mixed in (e.g. wearable HealthKit
    # proxies), they contribute *fractional* effective observations — so
    # appending them cannot shrink the noise floor or buy Student-t degrees of
    # freedom as if they were full-precision clinical draws. This is what
    # keeps noisy proxies from swamping a small set of clinical labs.
    sw2 = sum(wt * wt for wt in wt_vec)
    n_eff = (sw * sw / sw2) if sw2 > 0 else float(n)
    # Floor at the per-observation pooled-noise scale so we never claim
    # zero uncertainty even with a perfect fit.
    floor = (noise_pct / max(math.sqrt(n_eff), 1.0)) ** 2
    sd_theta = math.sqrt(max(var_theta, floor, 1e-9))
    # Bayesian-linear-regression with unknown σ has Student-t marginals,
    # not Normal — with small n the χ² tails on σ² translate into fatter
    # θ tails. The conjugate update downstream treats σ_θ as a Normal
    # standard deviation; scaling by t_0.975(df) / z_0.975 makes the
    # 95% interval that *would* be drawn at ±1.96·σ_θ instead match the
    # honest t-interval. df = n_eff − 2 because we fit two parameters
    # (baseline and slope); n_eff (not raw n) so a burst of down-weighted
    # proxies doesn't collapse the small-sample correction. Without this
    # correction the calibration backtest under-covers θ at ~88% when n=5
    # and noise is low.
    df = max(n_eff - 2.0, 1.0)
    sd_theta *= _t_inflation_factor(df)

    likelihood = Likelihood(
        mean_pct_change=theta_hat,
        sd_pct_change=sd_theta,
        n_observations=n,
        baseline=b_hat,
    )
    # σ_b is taken straight from the joint posterior — no artificial
    # floor. When the data identifies b precisely (e.g. a pre-baseline
    # measurement at w≈0 pins it), the posterior σ_b is small and the
    # predictive band correctly narrows. An earlier 2%-of-baseline floor
    # caused the predictive band to over-cover (100% vs. nominal 95%)
    # in the calibration backtest.
    sd_baseline = math.sqrt(max(var_b, 1e-12))
    return JointFit(likelihood=likelihood, baseline=b_hat, baseline_sd=sd_baseline)


# Student-t 0.975 quantile divided by Normal 0.975 quantile (≈1.96),
# tabulated for small df. Above df=30 the ratio is within 4% of 1.0;
# we return 1.0 there.
_T_INFLATION_TABLE: dict[int, float] = {
    1:  12.71  / _Z95,
    2:   4.303 / _Z95,
    3:   3.182 / _Z95,
    4:   2.776 / _Z95,
    5:   2.571 / _Z95,
    6:   2.447 / _Z95,
    7:   2.365 / _Z95,
    8:   2.306 / _Z95,
    9:   2.262 / _Z95,
    10:  2.228 / _Z95,
    12:  2.179 / _Z95,
    15:  2.131 / _Z95,
    20:  2.086 / _Z95,
    25:  2.060 / _Z95,
    30:  2.042 / _Z95,
}


def _t_inflation_factor(df: float) -> float:
    """Return t_0.975(df) / Z_0.975, capped to ≥1.0 for very large df.

    ``df`` may be fractional (effective degrees of freedom from a weighted
    fit); an integer-valued float hits the table exactly (``3.0 in table`` is
    True), a fractional one interpolates between the neighbouring rows."""
    if df >= 30:
        return 1.0
    if df in _T_INFLATION_TABLE:
        return _T_INFLATION_TABLE[df]
    # Linear interpolation between nearest tabulated points.
    keys = sorted(_T_INFLATION_TABLE.keys())
    for i in range(len(keys) - 1):
        lo, hi = keys[i], keys[i + 1]
        if lo < df < hi:
            t_lo = _T_INFLATION_TABLE[lo]
            t_hi = _T_INFLATION_TABLE[hi]
            frac = (df - lo) / (hi - lo)
            return t_lo + frac * (t_hi - t_lo)
    return 1.0


# ── Bayes-informed expected timeframe ───────────────────────────────────────

def expected_window(
    *,
    posterior: Posterior,
    tau_weeks: float,
    detection_noise_pct: float = 0.05,
    plateau_fraction: float = 0.95,
) -> ExpectedWindow:
    """Posterior-derived 'when do we expect to see this change' window.

    The timing flows from the posterior magnitude — a strong responder
    crosses the detection threshold earlier than a weak one. Specifically:

        weeks_min   first week the predicted |Δ/baseline| exceeds
                    ``detection_noise_pct`` (~ 1 measurement-noise s.d.).
                    Solve  |θ_post| · a(w) = detection_noise_pct  ⇒
                    w = -τ · ln(1 - detection_noise_pct / |θ_post|).
        weeks_max   ``plateau_fraction`` of the asymptotic approach
                    (≈ 3·τ at 95%).

    A larger |θ_post| → earlier weeks_min. A posterior so weak it never
    crosses the detection threshold yields weeks_min = weeks_max (window
    collapses) and ``credible = False`` so the chart can de-emphasise it.

    ``detection_fraction`` is exposed as the implied fraction-of-asymptote
    that was crossed at weeks_min, for display.
    """
    plateau_fraction = min(max(plateau_fraction, 0.5), 0.999)
    weeks_max = -tau_weeks * math.log(1.0 - plateau_fraction) if tau_weeks > 0 else 0.0

    theta = posterior.mean_pct_change
    abs_theta = abs(theta)

    credible = (
        posterior.credible_lo_95 > 0
        or posterior.credible_hi_95 < 0
    )

    if not credible or abs_theta <= detection_noise_pct or tau_weeks <= 0:
        # Posterior can't promise the effect ever exceeds noise. Collapse
        # the window to the plateau marker so the chart still renders
        # something, but flag it inconclusive.
        direction = "inconclusive"
        weeks_min = weeks_max
        detection_fraction = 0.0
    else:
        detection_fraction = detection_noise_pct / abs_theta
        # Cap detection_fraction at plateau_fraction so weeks_min <= weeks_max
        # in the rare case detection_noise_pct/|θ| > plateau_fraction.
        detection_fraction = min(detection_fraction, plateau_fraction)
        weeks_min = -tau_weeks * math.log(1.0 - detection_fraction)
        direction = "increase" if theta > 0 else "decrease"

    return ExpectedWindow(
        weeks_min=weeks_min,
        weeks_max=weeks_max,
        direction=direction,
        asymptote_pct_change=theta,
        credible=credible,
        detection_fraction=detection_fraction,
        plateau_fraction=plateau_fraction,
    )
