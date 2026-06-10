import math

from engine.tracking.bayes import (
    Likelihood,
    Posterior,
    approach,
    effective_observation,
    estimate_baseline,
    expected_window,
    joint_fit_likelihood,
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


def test_joint_fit_recovers_theta_without_pre_baseline():
    """The whole point of the joint fit: even when every measurement is
    post-treatment-start, we should recover θ rather than collapse to 0."""
    baseline_true = 180.0
    theta_true = 0.50
    tau = 3.0
    obs = [
        (w, baseline_true * (1 + theta_true * approach(w, tau)))
        for w in (4.0, 8.0, 12.0, 16.0)
    ]
    fit = joint_fit_likelihood(
        observations=obs,
        tau_weeks=tau,
        baseline_prior_mean=baseline_true,
        baseline_prior_sd=baseline_true * 0.3,
        noise_pct=0.06,
    )
    assert fit is not None
    lik, baseline_hat = fit
    assert abs(lik.mean_pct_change - theta_true) < 0.10
    assert abs(baseline_hat - baseline_true) / baseline_true < 0.15


def test_joint_fit_uses_pre_baseline_measurement():
    """When a pre-treatment measurement is included it should anchor b
    tightly and the slope estimate should be near-perfect."""
    baseline_true = 180.0
    theta_true = 0.40
    tau = 3.0
    obs = [(0.0, baseline_true)] + [
        (w, baseline_true * (1 + theta_true * approach(w, tau)))
        for w in (2.0, 4.0, 8.0, 12.0)
    ]
    fit = joint_fit_likelihood(
        observations=obs,
        tau_weeks=tau,
        baseline_prior_mean=baseline_true,
        baseline_prior_sd=baseline_true * 0.3,
        noise_pct=0.06,
    )
    assert fit is not None
    lik, baseline_hat = fit
    assert abs(lik.mean_pct_change - theta_true) < 0.03
    assert abs(baseline_hat - baseline_true) < 2.0


def test_joint_fit_handles_noisy_data_without_pre_baseline():
    """With ±5% noise and no pre-baseline measurement, θ should still land
    in a reasonable neighbourhood of truth — the regime where the previous
    (baseline = earliest measurement) estimator failed worst."""
    import random
    baseline_true = 180.0
    theta_true = 0.50
    tau = 3.0
    rng = random.Random(7)
    obs = []
    for w in (3.0, 5.0, 8.0, 12.0, 16.0):
        true_val = baseline_true * (1 + theta_true * approach(w, tau))
        noisy = true_val * rng.gauss(1.0, 0.05)
        obs.append((w, noisy))
    fit = joint_fit_likelihood(
        observations=obs,
        tau_weeks=tau,
        baseline_prior_mean=baseline_true,
        baseline_prior_sd=baseline_true * 0.3,
        noise_pct=0.05,
    )
    assert fit is not None
    lik, _ = fit
    assert 0.30 <= lik.mean_pct_change <= 0.70, (
        f"θ̂={lik.mean_pct_change:.3f}, want ~0.50"
    )


def test_joint_fit_returns_none_when_no_observations():
    fit = joint_fit_likelihood(
        observations=[],
        tau_weeks=4.0,
        baseline_prior_mean=100.0,
        baseline_prior_sd=30.0,
    )
    assert fit is None


def test_expected_window_credible_when_posterior_excludes_zero():
    post = Posterior(
        mean_pct_change=0.40, sd_pct_change=0.05,
        credible_lo_95=0.30, credible_hi_95=0.50, n_effective=5.0,
    )
    win = expected_window(posterior=post, tau_weeks=4.0)
    assert win.credible
    assert win.direction == "increase"
    # weeks_max at 95% of asymptote → -4·ln(0.05) ≈ 11.98
    assert 11.5 < win.weeks_max < 12.5
    # weeks_min < weeks_max for a credible signal
    assert 0 < win.weeks_min < win.weeks_max


def test_expected_window_inconclusive_when_posterior_straddles_zero():
    post = Posterior(
        mean_pct_change=0.02, sd_pct_change=0.10,
        credible_lo_95=-0.18, credible_hi_95=0.22, n_effective=0.5,
    )
    win = expected_window(posterior=post, tau_weeks=4.0)
    assert not win.credible
    assert win.direction == "inconclusive"


def test_expected_window_direction_negative_for_decrease():
    post = Posterior(
        mean_pct_change=-0.30, sd_pct_change=0.05,
        credible_lo_95=-0.40, credible_hi_95=-0.20, n_effective=3.0,
    )
    win = expected_window(posterior=post, tau_weeks=4.0)
    assert win.credible
    assert win.direction == "decrease"


def test_expected_window_stronger_posterior_detects_earlier():
    """The whole point of making the window posterior-informed: a larger
    |θ| should cross detection threshold sooner."""
    strong = Posterior(
        mean_pct_change=0.60, sd_pct_change=0.05,
        credible_lo_95=0.50, credible_hi_95=0.70, n_effective=5.0,
    )
    weak = Posterior(
        mean_pct_change=0.10, sd_pct_change=0.02,
        credible_lo_95=0.06, credible_hi_95=0.14, n_effective=5.0,
    )
    w_strong = expected_window(posterior=strong, tau_weeks=4.0)
    w_weak = expected_window(posterior=weak, tau_weeks=4.0)
    assert w_strong.credible and w_weak.credible
    assert w_strong.weeks_min < w_weak.weeks_min


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
