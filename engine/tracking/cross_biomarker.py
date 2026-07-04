"""
engine/tracking/cross_biomarker.py
==================================
Cross-biomarker residual covariance — **Phase 1 design stub (GATED, INERT)**.

Status
------
This module is a *documented scaffold only*. Nothing here is wired into
``analysis.predict_response``; the master switch

    CROSS_BIOMARKER_ENABLED = False

is off and there is no code path (in this module or elsewhere) that flips it.
The helpers below are pure functions over small matrices (plain ``math`` /
stdlib, matching the rest of ``engine/tracking``) so they can be unit-tested in
isolation, but they do **not** touch the posterior. Turning this on requires
real multi-biomarker cohort volume to *estimate* the covariance — see
"Why this is gated" below and the matching section in
``docs/models/peptide-response-model.md``.

--------------------------------------------------------------------------
The model
--------------------------------------------------------------------------
Today (Phase 0) each biomarker ``k`` for a (patient, peptide) is fit with its
own **independent** scalar latent

    θ_k ~ N(μ0_k, σ0_k²),   μ0_k = η · expected_pct_k

and updated by a 1-D Normal-Normal conjugate step. The biomarkers within a
peptide's mechanism are *not* independent, though: GLP-1's body-weight, HbA1c,
waist and HOMA-IR all move together because they are downstream of the same
incretin response. This module specifies how that co-movement would be modelled
as a **residual covariance Σ** over the cluster's θ vector.

Let a *mechanism cluster* be the ordered biomarker list
``(k_1, …, k_K)`` for one peptide (e.g. the "GLP-1 RA" cluster). Collect the
latents into a vector ``θ = (θ_{k_1}, …, θ_{k_K})``. The joint prior becomes a
**multivariate normal**

    θ ~ N(μ0,  Σ),          μ0 = η · e,   e = (expected_pct_{k_1}, …)
    Σ = D R D,              D = diag(σ0_{k_1}, …, σ0_{k_K}),  R = correlation.

``R`` is a symmetric, unit-diagonal, positive-semidefinite (PSD) correlation
matrix — the empirical correlation of the *standardised* per-marker responses
``z_k = (θ_k − μ0_k)/σ0_k`` across the cohort. ``D`` scales those correlations
back to the per-marker prior SDs already computed in Phase 0. Because ``D``
already carries the shared-η magnitude (see below), ``R`` is **not** η-partialled:
a shared η surfaces as a nonzero off-diagonal in ``R`` rather than being removed
from it.

--------------------------------------------------------------------------
Why a shared η ALREADY induces positive coupling (and Σ extends it)
--------------------------------------------------------------------------
The Phase-0 responder index (``responder_index.py``) is a single scalar η
*shared by every biomarker* of a (patient, peptide). Crucially η is itself
uncertain: the HBRI reports ``Var(η)``. Because each prior mean is a linear
image of that one shared, uncertain η,

    θ_k = η · expected_pct_k          (viewing η as the random quantity)

the biomarkers are already coupled through η *before any full Σ is introduced*.
Propagating the shared-η uncertainty gives an induced covariance

    Cov(θ_j, θ_k) = expected_pct_j · expected_pct_k · Var(η)                (1)

i.e. a **rank-1** term ``Var(η) · e eᵀ`` (see :func:`shared_eta_covariance`).
Its sign is ``sign(expected_pct_j · expected_pct_k)``: markers the peptide
pushes the *same* direction are positively coupled, opposite-direction markers
negatively — automatically, with no new parameters. A strong responder signal
therefore already nudges every co-directional marker together via η.

Crucially, Phase-0's own per-marker variance is **already the diagonal** of that
rank-1 shared-η matrix. The Phase-0 prior SD is (``genetics.derive_prior``)

    σ0_k = hypot( sd(η)·|e_k|,  panel_rel_sd·|e_k| )
    ⇒  σ0_k² = Var(η)·e_k²  +  panel_rel_sd²·e_k²

whose first summand is exactly the ``k``-th diagonal entry of ``Var(η)·e eᵀ``.
So Phase 0 keeps the shared-η term **only on the diagonal** and discards its
off-diagonal — i.e. it pins the cross-marker correlation to zero.

The gated extension therefore does **not** add a second covariance on top of
``σ0²`` (that would double-count the shared-η variance already inside ``σ0²``).
It replaces the diagonal-only prior with a single joint covariance ``Σ = D R D``
that **reuses the same** per-marker SDs ``D = diag(σ0_k)`` and turns on the
off-diagonal through the standardised-response correlation ``R`` (defined above).
``R = I`` recovers Phase 0 exactly (``assemble_cluster_covariance`` returns
``diag(σ0_k²)``); a positive off-diagonal restores the coupling a shared η
already implies. The rank-1 ``Var(η)·e eᵀ`` (:func:`shared_eta_covariance`) is
the **justification for the sign pattern** of R's off-diagonals — co-directional
markers (``sign(e_j e_k) > 0``) correlate positively — not a term summed
alongside ``D R D``.

--------------------------------------------------------------------------
How the joint posterior would work
--------------------------------------------------------------------------
With a multivariate-normal prior ``θ ~ N(μ0, Σ)`` and a Gaussian observation
vector ``ȳ`` with observation covariance ``Σ_obs`` (per-marker likelihoods,
off-diagonal zero if measurements are marker-independent), the conjugate update
is the multivariate Normal-Normal step in **precision (information) form**:

    Λ0 = Σ⁻¹                         prior precision
    Λy = Σ_obs⁻¹                     observation precision
    Λ_post = Λ0 + Λy                                                        (2)
    μ_post = Λ_post⁻¹ (Λ0 μ0 + Λy ȳ)                                        (3)

Off-diagonal entries of ``Λ_post`` are exactly the channel through which a
strong, well-measured signal in one marker sharpens the posterior of a coupled,
sparsely-measured marker — the entire point of the extension.

**Reduction to Phase 0.** If ``Σ`` and ``Σ_obs`` are both diagonal (``R = I``),
then ``Λ0``, ``Λy``, ``Λ_post`` are diagonal and (2)-(3) decouple into ``K``
independent scalar updates ``τ_post = τ0 + τy`` — byte-for-byte the current
``bayes.update``. This is the inert-by-construction guarantee: the gated code,
if ever switched on with an identity correlation, changes nothing.

--------------------------------------------------------------------------
Why this is gated (do NOT wire in)
--------------------------------------------------------------------------
1. **Σ is unidentifiable without cohort volume.** A K×K correlation needs
   O(K²) residual pairs per cluster to estimate stably; the tracking cohort is
   far too small today. A plugged-in-but-unvalidated Σ would inject correlations
   that are mostly sampling noise.
2. **It breaks the coverage contract.** Off-diagonal precision *sharpens*
   posteriors (narrows credible intervals). If those correlations are wrong,
   intervals get overconfident and the calibration backtest's coverage
   guarantee (the load-bearing honesty contract for this whole subsystem)
   silently fails. Independent-per-marker is the conservative default: it never
   claims cross-marker information it cannot back.
3. **Integration point when un-gated.** ``analysis.predict_response`` currently
   loops one biomarker at a time. Wiring Σ means grouping a (patient, peptide)'s
   requested markers into their mechanism cluster and replacing the per-marker
   ``bayes.update`` with a single multivariate update (2)-(3) over the cluster,
   then slicing μ_post/Λ_post back to the requested marker. That is a real
   refactor of the prediction loop — deliberately out of scope for this stub.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

# ── Master gate ─────────────────────────────────────────────────────────────
# OFF. No code path flips this. Present so the intent is greppable and so a
# future enabling PR is a single, reviewable switch rather than scattered edits.
CROSS_BIOMARKER_ENABLED = False

# Numerical tolerance for symmetry / PSD checks on the small (K ≲ 8) matrices
# a mechanism cluster produces.
_TOL = 1e-9


# ── Illustrative mechanism clusters (DESIGN REFERENCE ONLY) ─────────────────
# These are documentation of *which* biomarkers would share a Σ, not a wired
# registry. The class-qualified "(GLP-1 RA)" names match the panel entries in
# ``engine/peptides/measurements.py`` so the intended clustering is unambiguous.
# Nothing consumes this dict yet.
MECHANISM_CLUSTERS: dict[str, tuple[str, ...]] = {
    "GLP-1 RA": (
        "Body weight (GLP-1 RA)",
        "Waist circumference (GLP-1 RA)",
        "HbA1c (GLP-1 RA)",
        "HOMA-IR (GLP-1 RA)",
    ),
}


# ── Correlation matrix data structure ───────────────────────────────────────

@dataclass(frozen=True)
class CorrelationMatrix:
    """A symmetric, unit-diagonal biomarker correlation matrix ``R``.

    ``labels`` are the ordered biomarker names; ``rows`` is the K×K matrix as a
    tuple of tuples (row-major). Construct via :func:`correlation_matrix` rather
    than directly so the invariants are validated once.
    """
    labels: tuple[str, ...]
    rows: tuple[tuple[float, ...], ...]

    @property
    def size(self) -> int:
        return len(self.labels)

    def get(self, a: str, b: str) -> float:
        """Correlation between two biomarkers by name."""
        i = self.labels.index(a)
        j = self.labels.index(b)
        return self.rows[i][j]

    def validate(self) -> None:
        """Raise ``ValueError`` unless R is square, symmetric, unit-diagonal and
        every entry lies in [-1, 1]. Does **not** check PSD — use
        :func:`is_psd` for that (it is a separate, more expensive property)."""
        k = self.size
        if len(self.rows) != k or any(len(r) != k for r in self.rows):
            raise ValueError("correlation matrix must be square and match labels")
        for i in range(k):
            if abs(self.rows[i][i] - 1.0) > _TOL:
                raise ValueError(f"diagonal entry [{i}][{i}] must be 1.0")
            for j in range(k):
                v = self.rows[i][j]
                if not math.isfinite(v) or abs(v) > 1.0 + _TOL:
                    raise ValueError(f"entry [{i}][{j}]={v} outside [-1, 1]")
                if abs(v - self.rows[j][i]) > _TOL:
                    raise ValueError(f"matrix not symmetric at [{i}][{j}]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "labels": list(self.labels),
            "rows": [[round(v, 6) for v in row] for row in self.rows],
        }


def correlation_matrix(
    labels: tuple[str, ...],
    pairwise: dict[tuple[str, str], float] | None = None,
) -> CorrelationMatrix:
    """Build a validated :class:`CorrelationMatrix`.

    Diagonal is forced to 1.0; off-diagonal defaults to 0.0. ``pairwise`` maps
    an unordered pair of labels to their correlation and fills both symmetric
    entries. The result is validated (symmetry / range) before return; PSD is a
    separate check (:func:`is_psd`) because a matrix of individually-valid
    pairwise correlations need not be jointly PSD.
    """
    k = len(labels)
    if len(set(labels)) != k:
        raise ValueError("labels must be unique")
    idx = {name: i for i, name in enumerate(labels)}
    mat = [[1.0 if i == j else 0.0 for j in range(k)] for i in range(k)]
    for (a, b), r in (pairwise or {}).items():
        if a not in idx or b not in idx:
            raise ValueError(f"pairwise key ({a!r}, {b!r}) references unknown label")
        i, j = idx[a], idx[b]
        if i == j:
            raise ValueError(f"pairwise correlation given for identical label {a!r}")
        mat[i][j] = mat[j][i] = float(r)
    cm = CorrelationMatrix(labels=labels, rows=tuple(tuple(row) for row in mat))
    cm.validate()
    return cm


# ── Pure matrix helpers (stdlib only) ───────────────────────────────────────

def _cholesky(mat: list[list[float]]) -> list[list[float]] | None:
    """Cholesky factor ``L`` (lower-triangular, ``L Lᵀ = mat``) or ``None`` if
    the matrix is not positive-definite. Pure stdlib; used only for the small
    cluster matrices, so an O(K³) textbook implementation is fine."""
    k = len(mat)
    L = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(i + 1):
            s = sum(L[i][p] * L[j][p] for p in range(j))
            if i == j:
                diag = mat[i][i] - s
                if diag <= _TOL:
                    return None  # not positive-definite
                L[i][j] = math.sqrt(diag)
            else:
                L[i][j] = (mat[i][j] - s) / L[j][j]
    return L


def is_psd(corr: CorrelationMatrix, *, jitter: float = 1e-8) -> bool:
    """True iff ``R`` is positive-semidefinite (to numerical tolerance).

    A correlation matrix must be PSD to be a valid Gaussian covariance shape; a
    matrix assembled from independently-plausible pairwise correlations can fail
    this (the classic reason cluster correlations cannot be hand-set — they must
    be estimated jointly). Implemented as a Cholesky on ``R + jitter·I`` so an
    exactly-singular but valid PSD matrix (e.g. identity, or a degenerate rank-1
    correlation) is accepted rather than rejected for a floating-point zero
    pivot."""
    k = corr.size
    m = [[corr.rows[i][j] + (jitter if i == j else 0.0) for j in range(k)]
         for i in range(k)]
    return _cholesky(m) is not None


def assemble_cluster_covariance(
    sds: tuple[float, ...],
    corr: CorrelationMatrix,
) -> tuple[tuple[float, ...], ...]:
    """Assemble the mechanism-cluster prior covariance ``Σ = D R D``.

    ``sds`` are the per-biomarker prior SDs ``σ0_k`` (Phase 0's
    ``prior.sd_pct_change``, in cluster order); ``corr`` is the residual
    correlation ``R``. Returns ``Σ`` as a tuple-of-tuples.

    Identity reduction (the inert guarantee): when ``R = I``, ``Σ`` is diagonal
    with ``Σ_kk = σ0_k²`` and the multivariate update (docstring eqns 2-3)
    decouples into the current independent per-marker 1-D updates.
    """
    k = corr.size
    if len(sds) != k:
        raise ValueError("sds length must match correlation matrix size")
    if any((not math.isfinite(s)) or s < 0 for s in sds):
        raise ValueError("prior SDs must be finite and non-negative")
    sigma = [
        [sds[i] * corr.rows[i][j] * sds[j] for j in range(k)]
        for i in range(k)
    ]
    return tuple(tuple(row) for row in sigma)


def shared_eta_covariance(
    loadings: tuple[float, ...],
    var_eta: float,
) -> tuple[tuple[float, ...], ...]:
    """The rank-1 covariance ``Var(η) · e eᵀ`` induced by the shared responder
    index η (docstring eqn 1).

    ``loadings`` is ``e = (expected_pct_{k_1}, …)`` — how strongly η loads onto
    each biomarker's prior mean; ``var_eta`` is the HBRI's ``Var(η)``. This term
    is **already implicitly present** in Phase 0 through the single shared η; it
    is exposed here only to make the decomposition
    ``Σ_total = Var(η)·e eᵀ + D R_resid D`` explicit and testable. Same-sign
    loadings ⇒ non-negative off-diagonals ⇒ positive coupling.
    """
    if not math.isfinite(var_eta) or var_eta < 0:
        raise ValueError("var_eta must be finite and non-negative")
    k = len(loadings)
    return tuple(
        tuple(var_eta * loadings[i] * loadings[j] for j in range(k))
        for i in range(k)
    )
