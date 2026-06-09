import math

from engine.tracking.bayes import (
    Likelihood,
    approach,
    effective_observation,
    estimate_baseline,
    predictive_curve,
    update,
)


def test_approach_monotonic_and_bounded():
    assert approach(0.0, 4.0) == 0.0
    assert 0 < approach(2.0, 4.0) < 1
    assert approach(100.0, 4.0) > 0.99


def test_update_with_no_likelihood_returns_prior():
    post = update(prior_mean=0.2, prior_sd=0.1, likelihood=None)
    assert post.mean_pct_change == 0.2
    assert post.sd_pct_change == 0.1
    assert post.n_effective == 0


def test_normal_normal_pulls_toward_observation():
    """A strong, low-variance observation should pull μ_post toward ȳ
    and shrink σ_post."""
    post = update(
        prior_mean=0.0,
        prior_sd=0.2,
        likelihood=Likelihood(
            mean_pct_change=0.5,
            sd_pct_change=0.05,
            n_observations=4,
            baseline=100.0,
        ),
    )
    assert 0.4 < post.mean_pct_change < 0.5
    assert post.sd_pct_change < 0.05


def test_credible_interval_is_symmetric_about_mean():
    post = update(
        prior_mean=0.3, prior_sd=0.1,
        likelihood=Likelihood(0.3, 0.1, 1, 100.0),
    )
    width = post.credible_hi_95 - post.credible_lo_95
    centre = (post.credible_hi_95 + post.credible_lo_95) / 2
    assert math.isclose(centre, post.mean_pct_change, rel_tol=1e-6)
    # 95% interval ≈ ±1.96 σ → width ≈ 3.92 σ
    assert math.isclose(width / post.sd_pct_change, 3.92, rel_tol=0.01)


def test_effective_observation_recovers_theta():
    """Observations generated under θ = +0.4 with τ = 4 should yield a
    pooled estimate near +0.4."""
    baseline = 100.0
    theta = 0.4
    tau = 4.0
    points = [
        (w, baseline * (1 + theta * approach(w, tau)))
        for w in (2.0, 4.0, 8.0, 12.0)
    ]
    lik = effective_observation(
        baseline=baseline, observations=points, tau_weeks=tau, noise_pct=0.05,
    )
    assert lik is not None
    assert math.isclose(lik.mean_pct_change, theta, abs_tol=0.02)
    assert lik.n_observations == 4


def test_effective_observation_filters_baseline_points():
    """Measurements taken before the min_weeks threshold contribute no
    information about θ."""
    lik = effective_observation(
        baseline=100.0,
        observations=[(0.0, 100.0), (0.2, 100.0)],
        tau_weeks=4.0,
    )
    assert lik is None


def test_baseline_estimate_uses_pre_window():
    obs = [(0.0, 100.0), (0.5, 110.0), (4.0, 200.0)]
    base = estimate_baseline(obs, baseline_window_weeks=1.5)
    # Median of (100, 110) = 105
    assert math.isclose(base, 105.0)


def test_baseline_estimate_falls_back_to_earliest():
    obs = [(4.0, 200.0), (8.0, 240.0)]
    assert estimate_baseline(obs, baseline_window_weeks=1.5) == 200.0


def test_predictive_curve_grows_with_approach():
    post = update(prior_mean=0.3, prior_sd=0.05, likelihood=None)
    curve = predictive_curve(
        baseline=100.0, posterior=post, tau_weeks=4.0,
        week_grid=[0.0, 2.0, 8.0, 24.0],
    )
    means = [p.mean for p in curve.points]
    # Should be monotone non-decreasing for a positive posterior mean.
    assert all(b >= a - 1e-6 for a, b in zip(means, means[1:]))
    # At week 0 mean equals baseline.
    assert math.isclose(means[0], 100.0)
    # At long time the mean approaches baseline * (1 + 0.3) = 130.
    assert 125 < means[-1] < 135
    # Credible band widens then asymptotes with the approach factor.
    widths = [p.hi_95 - p.lo_95 for p in curve.points]
    assert widths[0] == 0  # a(0)=0 → band width zero
    assert widths[-1] > 0
