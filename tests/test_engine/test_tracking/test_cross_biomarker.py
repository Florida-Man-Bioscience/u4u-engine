"""
Unit tests for the GATED cross-biomarker covariance design stub
(``engine/tracking/cross_biomarker.py``).

These exercise the *pure* helpers only. The key contract is that the module is
inert (``CROSS_BIOMARKER_ENABLED is False``) and that an identity correlation
reduces the cluster covariance to the diagonal independent-per-marker case that
Phase 0 already computes.
"""
from __future__ import annotations

import math

import pytest

from engine.tracking import cross_biomarker as cb


# ── Inertness gate ──────────────────────────────────────────────────────────

def test_module_is_gated_off():
    assert cb.CROSS_BIOMARKER_ENABLED is False


# ── CorrelationMatrix builder / validation ──────────────────────────────────

def test_builder_defaults_to_identity():
    r = cb.correlation_matrix(("a", "b", "c"))
    assert r.size == 3
    for i in range(3):
        for j in range(3):
            assert r.rows[i][j] == (1.0 if i == j else 0.0)


def test_builder_fills_symmetric_pairs():
    r = cb.correlation_matrix(("weight", "hba1c"), {("weight", "hba1c"): 0.6})
    assert r.get("weight", "hba1c") == 0.6
    assert r.get("hba1c", "weight") == 0.6  # symmetric
    assert r.get("weight", "weight") == 1.0
    r.validate()  # does not raise


def test_builder_rejects_duplicate_labels():
    with pytest.raises(ValueError):
        cb.correlation_matrix(("a", "a"))


def test_builder_rejects_unknown_pairwise_label():
    with pytest.raises(ValueError):
        cb.correlation_matrix(("a", "b"), {("a", "z"): 0.5})


def test_builder_rejects_self_pair():
    with pytest.raises(ValueError):
        cb.correlation_matrix(("a", "b"), {("a", "a"): 0.5})


def test_validate_rejects_out_of_range():
    bad = cb.CorrelationMatrix(labels=("a", "b"),
                               rows=((1.0, 1.5), (1.5, 1.0)))
    with pytest.raises(ValueError):
        bad.validate()


def test_validate_rejects_asymmetric():
    bad = cb.CorrelationMatrix(labels=("a", "b"),
                               rows=((1.0, 0.3), (0.4, 1.0)))
    with pytest.raises(ValueError):
        bad.validate()


def test_validate_rejects_nonunit_diagonal():
    bad = cb.CorrelationMatrix(labels=("a", "b"),
                               rows=((0.9, 0.0), (0.0, 1.0)))
    with pytest.raises(ValueError):
        bad.validate()


# ── PSD checking ────────────────────────────────────────────────────────────

def test_identity_is_psd():
    assert cb.is_psd(cb.correlation_matrix(("a", "b", "c")))


def test_valid_positive_correlation_is_psd():
    r = cb.correlation_matrix(("a", "b"), {("a", "b"): 0.5})
    assert cb.is_psd(r)


def test_degenerate_rank1_correlation_is_psd():
    # All-ones off-diagonal ⇒ exactly singular (rank 1) but still PSD.
    r = cb.correlation_matrix(("a", "b", "c"),
                              {("a", "b"): 1.0, ("a", "c"): 1.0, ("b", "c"): 1.0})
    assert cb.is_psd(r)


def test_indefinite_matrix_is_not_psd():
    # Classic non-PSD example: pairwise correlations individually in [-1,1]
    # but jointly inconsistent.
    r = cb.correlation_matrix(
        ("a", "b", "c"),
        {("a", "b"): 0.9, ("a", "c"): 0.9, ("b", "c"): -0.9},
    )
    r.validate()          # each entry is individually valid
    assert not cb.is_psd(r)   # but the matrix is not PSD


# ── Σ assembly + the identity-reduces-to-independent contract ───────────────

def test_identity_correlation_yields_diagonal_variance():
    """R = I  ⇒  Σ = diag(σ0²): exactly the independent per-marker case."""
    sds = (0.10, 0.25, 0.4)
    r = cb.correlation_matrix(("a", "b", "c"))
    sigma = cb.assemble_cluster_covariance(sds, r)
    for i in range(3):
        for j in range(3):
            if i == j:
                assert sigma[i][j] == pytest.approx(sds[i] ** 2)
            else:
                assert sigma[i][j] == 0.0


def test_covariance_matches_D_R_D():
    sds = (2.0, 3.0)
    r = cb.correlation_matrix(("a", "b"), {("a", "b"): 0.5})
    sigma = cb.assemble_cluster_covariance(sds, r)
    # Σ_ab = σ_a · r · σ_b = 2 · 0.5 · 3 = 3.0
    assert sigma[0][1] == pytest.approx(3.0)
    assert sigma[1][0] == pytest.approx(3.0)
    assert sigma[0][0] == pytest.approx(4.0)
    assert sigma[1][1] == pytest.approx(9.0)


def test_covariance_is_symmetric_and_psd():
    sds = (0.1, 0.2, 0.3)
    r = cb.correlation_matrix(
        ("a", "b", "c"),
        {("a", "b"): 0.4, ("a", "c"): 0.3, ("b", "c"): 0.2},
    )
    sigma = cb.assemble_cluster_covariance(sds, r)
    for i in range(3):
        for j in range(3):
            assert sigma[i][j] == pytest.approx(sigma[j][i])
    # A PSD correlation scaled by a diagonal stays PSD.
    assert cb.is_psd(r)


def test_assemble_rejects_size_mismatch():
    r = cb.correlation_matrix(("a", "b"))
    with pytest.raises(ValueError):
        cb.assemble_cluster_covariance((0.1,), r)


def test_assemble_rejects_negative_sd():
    r = cb.correlation_matrix(("a", "b"))
    with pytest.raises(ValueError):
        cb.assemble_cluster_covariance((0.1, -0.2), r)


# ── Shared-η induced coupling ───────────────────────────────────────────────

def test_shared_eta_same_sign_loadings_are_positively_coupled():
    # Both markers move the same direction under η ⇒ positive off-diagonal.
    cov = cb.shared_eta_covariance((0.5, 0.3), var_eta=0.02)
    assert cov[0][1] > 0
    assert cov[0][1] == pytest.approx(0.02 * 0.5 * 0.3)


def test_shared_eta_opposite_sign_loadings_are_negatively_coupled():
    cov = cb.shared_eta_covariance((0.5, -0.3), var_eta=0.02)
    assert cov[0][1] < 0
    assert cov[0][1] == pytest.approx(0.02 * 0.5 * -0.3)


def test_shared_eta_is_rank_one():
    # Var(η)·e eᵀ has a zero 2x2 minor: cov00·cov11 - cov01² == 0.
    e = (0.4, 0.6, -0.2)
    cov = cb.shared_eta_covariance(e, var_eta=0.05)
    minor = cov[0][0] * cov[1][1] - cov[0][1] * cov[1][0]
    assert minor == pytest.approx(0.0, abs=1e-12)


def test_shared_eta_zero_variance_is_zero_matrix():
    cov = cb.shared_eta_covariance((0.5, 0.3), var_eta=0.0)
    assert all(v == 0.0 for row in cov for v in row)


def test_shared_eta_rejects_negative_variance():
    with pytest.raises(ValueError):
        cb.shared_eta_covariance((0.5, 0.3), var_eta=-0.01)


# ── Mechanism cluster reference matches the panel names ─────────────────────

def test_glp1_cluster_names_match_panel():
    from engine.peptides import get_biomarker_panel

    cluster = cb.MECHANISM_CLUSTERS["GLP-1 RA"]
    panel = get_biomarker_panel("Semaglutide")
    panel_names = {m.name for m in panel.measurements}
    for name in cluster:
        assert name in panel_names, f"{name!r} not a Semaglutide panel marker"
