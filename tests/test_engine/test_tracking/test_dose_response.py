"""Unit tests for the gated dose-response stub (engine/tracking/dose_response).

These exercise the maths only. The module is a design stub and is not wired
into any live prediction path, so nothing here touches ``predict_response`` or
the calibration backtest.
"""
import math

import pytest

from engine.tracking import dose_response as dr


def test_feature_gate_off_by_default():
    """The stub must ship gated OFF so it cannot alter live predictions."""
    assert dr.DOSE_RESPONSE_ENABLED is False


def test_s_equals_one_at_reference_dose():
    """s(ref) == 1 — the reference dose is the normalisation anchor."""
    assert math.isclose(dr.s(2.0, ec50=1.5, ref_dose=2.0), 1.0, rel_tol=1e-12)


def test_s_is_monotonic_increasing():
    prev = -math.inf
    for dose in [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 64.0]:
        val = dr.s(dose, ec50=1.5, ref_dose=2.0)
        assert val > prev
        prev = val


def test_s_below_reference_is_less_than_one():
    assert dr.s(1.0, ec50=1.5, ref_dose=2.0) < 1.0


def test_s_above_reference_is_greater_than_one():
    assert dr.s(4.0, ec50=1.5, ref_dose=2.0) > 1.0


def test_s_saturates_to_finite_plateau():
    """As dose → ∞, s → 1 + EC50/ref_dose with shrinking increments."""
    ec50, ref = 1.5, 2.0
    plateau = 1.0 + ec50 / ref
    # Approaches the plateau from below.
    assert dr.s(1e6, ec50=ec50, ref_dose=ref) < plateau
    assert math.isclose(dr.s(1e9, ec50=ec50, ref_dose=ref), plateau, rel_tol=1e-6)
    # Increments shrink (concave saturation): s(8)-s(4) < s(4)-s(2).
    s2 = dr.s(2.0, ec50=ec50, ref_dose=ref)
    s4 = dr.s(4.0, ec50=ec50, ref_dose=ref)
    s8 = dr.s(8.0, ec50=ec50, ref_dose=ref)
    assert (s8 - s4) < (s4 - s2)


def test_dose_zero_gives_zero_multiplier():
    assert dr.s(0.0, ec50=1.5, ref_dose=2.0) == 0.0


def test_effective_theta_reduces_to_theta_at_reference():
    theta = 0.3
    assert math.isclose(
        dr.effective_theta(theta, 2.0, ec50=1.5, ref_dose=2.0),
        theta,
        rel_tol=1e-12,
    )


def test_effective_theta_scales_with_dose():
    theta = 0.3
    low = dr.effective_theta(theta, 1.0, ec50=1.5, ref_dose=2.0)
    ref = dr.effective_theta(theta, 2.0, ec50=1.5, ref_dose=2.0)
    high = dr.effective_theta(theta, 4.0, ec50=1.5, ref_dose=2.0)
    assert low < ref < high


def test_effective_theta_preserves_sign():
    """A negative (decreasing) effect stays negative under dose scaling."""
    assert dr.effective_theta(-0.2, 4.0, ec50=1.5, ref_dose=2.0) < 0.0


def test_invalid_params_raise():
    with pytest.raises(ValueError):
        dr.s(1.0, ec50=0.0, ref_dose=2.0)
    with pytest.raises(ValueError):
        dr.s(1.0, ec50=1.5, ref_dose=0.0)


def test_params_for_falls_back_to_default():
    assert dr.params_for("does-not-exist") is dr.DEFAULT_PARAMS
    assert dr.params_for("BPC-157").ref_dose == 500.0
