"""
engine/tracking/pooling.py
==========================
Empirical-Bayes hierarchical prior for (peptide, biomarker) responses.

Problem
-------
The per-patient Bayesian fit currently uses only the patient's own
measurements together with a static, genetics-derived prior on θ. A
new patient with two measurements barely moves off the prior; a patient
without a genetic profile gets a panel-only prior with σ ≈ 0.4·|θ|.

If we already have a small cohort on the same peptide, that cohort
contains direct evidence of *how patients in this population actually
respond*. Empirical Bayes lets a new patient borrow that strength
without committing to a full hierarchical MCMC.

Model
-----
For each (peptide, biomarker), we treat each donor patient's joint-fit
θ̂_i as a noisy estimate of an unobserved per-patient true θ_i drawn
from a population distribution::

    θ_i ~ Normal(μ_pop, σ²_pop)            # cross-patient variation
    θ̂_i | θ_i ~ Normal(θ_i, σ²_within,i)  # individual fit uncertainty

Variance-components estimator (method of moments):

    μ̂_pop = mean(θ̂_i)
    σ̂²_pop = max(0, Var(θ̂_i) − mean(σ̂²_within,i))

The total observed spread of θ̂_i has two contributors: real
population spread σ²_pop and individual fit uncertainty σ²_within.
Subtracting the within-patient component gives an honest estimate of
how much patients genuinely differ from each other.

For a new patient, we combine the population prior with the
patient's genetic prior via precision weighting (treating them as
independent sources of information about θ):

    τ_combined = τ_genetic + τ_population
    μ_combined = (τ_g·μ_g + τ_p·μ_p) / τ_combined

Leave-one-out
-------------
When predicting for patient X, X must NOT contribute to the population
estimate that becomes their own prior — otherwise the patient borrows
strength from themselves and the calibration assumption breaks. Every
public entry point takes ``exclude_patient_id`` and the donor query
filters X out.

Limits
------
- Pure stdlib (no scipy/numpy). The MoM estimator is closed-form.
- The combination assumes the genetic and population priors carry
  independent information. They are correlated (cohort response also
  depends on genetics) but for small cohorts the redundancy is small;
  we accept the approximation rather than build a full latent model.
- A minimum of 3 donors is required before pooling is applied — fewer
  yields a population variance estimate noisier than the static prior.
"""
from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from . import bayes

MIN_DONORS = 3


# ── Donor extraction ────────────────────────────────────────────────────────

def _weeks_between(start: str, end: str) -> float | None:
    try:
        a = datetime.fromisoformat(start)
        if "T" in end:
            b = datetime.fromisoformat(end.replace("Z", "+00:00"))
        else:
            b = datetime.fromisoformat(end)
    except ValueError:
        return None
    return (b - a).total_seconds() / (7 * 86400)


@dataclass(frozen=True)
class DonorFit:
    """One donor patient's joint-fit summary for a (peptide, biomarker)."""
    patient_id: str
    theta_hat: float
    sigma_theta: float
    n_obs: int


def collect_donor_fits(
    conn,
    *,
    peptide_name: str,
    biomarker_name: str,
    tau_weeks: float,
    baseline_prior_mean: float,
    baseline_prior_sd: float,
    noise_pct: float,
    exclude_patient_id: str | None = None,
    min_observations: int = 3,
) -> list[DonorFit]:
    """Run the joint fit on every donor patient and return the (θ̂, σ_θ̂) list.

    A "donor" is any patient with a treatment for ``peptide_name`` and
    at least ``min_observations`` measurements of ``biomarker_name``
    that align positively to their treatment start. ``exclude_patient_id``
    is dropped so leave-one-out is the default.
    """
    from .service import _ph
    ph = _ph(conn)
    sql = f"""
        SELECT t.patient_id AS pid, t.start_date AS start_date,
               m.measured_at AS measured_at, m.value AS value
        FROM treatments t
        JOIN measurements m
          ON m.patient_id = t.patient_id
         AND (m.treatment_id IS NULL OR m.treatment_id = t.id)
        WHERE t.peptide_name = {ph}
          AND m.biomarker_name = {ph}
    """
    params: list[Any] = [peptide_name, biomarker_name]
    if exclude_patient_id is not None:
        sql += f" AND t.patient_id != {ph}"
        params.append(exclude_patient_id)

    by_patient: dict[str, list[tuple[float, float]]] = {}
    for row in conn.execute(sql, params).fetchall():
        w = _weeks_between(row["start_date"], row["measured_at"])
        if w is None or w < 0:
            continue
        by_patient.setdefault(row["pid"], []).append((w, row["value"]))

    donors: list[DonorFit] = []
    for pid, obs in by_patient.items():
        if len(obs) < min_observations:
            continue
        # Tighten baseline prior to a pre-measurement when present —
        # mirrors what analysis.predict_response does so the donor fit
        # uses the same baseline-anchoring rules.
        pre = [y for w, y in obs if w < 1.0]
        bpm = baseline_prior_mean
        bps = baseline_prior_sd
        if pre:
            med = statistics.median(pre)
            if med > 0:
                bpm = med
                bps = max(med * 0.08, 0.5)

        fit = bayes.joint_fit_likelihood(
            observations=obs,
            tau_weeks=tau_weeks,
            baseline_prior_mean=bpm,
            baseline_prior_sd=bps,
            noise_pct=noise_pct,
        )
        if fit is None:
            continue
        donors.append(DonorFit(
            patient_id=pid,
            theta_hat=fit.likelihood.mean_pct_change,
            sigma_theta=fit.likelihood.sd_pct_change,
            n_obs=len(obs),
        ))
    return donors


# ── Population prior (variance-components MoM) ──────────────────────────────

@dataclass(frozen=True)
class PopulationPrior:
    """Empirical-Bayes prior derived from a donor cohort.

    ``sd_pct_change`` is the cross-patient spread *after* subtracting
    individual fit uncertainty; when the within-patient noise dominates
    the observed spread, this is 0 and pooling should not be applied.
    """
    peptide: str
    biomarker: str
    n_donors: int
    mean_pct_change: float
    sd_pct_change: float
    raw_total_sd: float       # SD of θ̂ before subtracting within-patient noise
    mean_within_sd: float     # √(mean σ²_within) — diagnostic

    def to_dict(self) -> dict[str, Any]:
        return {
            "peptide": self.peptide,
            "biomarker": self.biomarker,
            "n_donors": self.n_donors,
            "mean_pct_change": round(self.mean_pct_change, 4),
            "sd_pct_change": round(self.sd_pct_change, 4),
            "raw_total_sd": round(self.raw_total_sd, 4),
            "mean_within_sd": round(self.mean_within_sd, 4),
        }


def estimate_population_prior(
    donors: Sequence[DonorFit],
    *,
    peptide: str,
    biomarker: str,
    min_donors: int = MIN_DONORS,
) -> PopulationPrior | None:
    """Method-of-moments variance-components estimator for the cohort.

    Returns ``None`` when fewer than ``min_donors`` patients contribute —
    a 2-patient cohort gives a population variance estimate with so much
    noise that pooling would harm rather than help.
    """
    if len(donors) < min_donors:
        return None

    n = len(donors)
    theta_hats = [d.theta_hat for d in donors]
    mean_theta = sum(theta_hats) / n
    var_total = sum((t - mean_theta) ** 2 for t in theta_hats) / max(n - 1, 1)
    mean_within_var = sum(d.sigma_theta ** 2 for d in donors) / n
    pop_var = max(0.0, var_total - mean_within_var)

    return PopulationPrior(
        peptide=peptide,
        biomarker=biomarker,
        n_donors=n,
        mean_pct_change=mean_theta,
        sd_pct_change=math.sqrt(pop_var),
        raw_total_sd=math.sqrt(var_total),
        mean_within_sd=math.sqrt(mean_within_var),
    )


# ── Prior combination ───────────────────────────────────────────────────────

# ── Genetics × cohort correlation (double-counting correction) ──────────────

# The genetic prior and the cohort-pooled population prior are two views of the
# SAME latent responder effect θ, and they are NOT independent: a donor cohort's
# response to a peptide is itself partly a function of the donors' genetics, so
# the two priors share signal. Fusing them as if independent (τ_g + τ_p) double-
# counts that shared signal and makes the posterior under-cover (the calibration
# backtest's correlated-source regime).
#
# ``combine_priors`` therefore takes an assumed error correlation ``ρ``. It
# defaults to ``0.0`` — precision addition, byte-identical to the legacy fusion,
# so every existing caller is unchanged. ``predict_response`` opts into
# ``GENETIC_COHORT_CORRELATION`` (a conservative structural assumption: the two
# priors share ~half their information). It is a documented assumption, not a
# fitted quantity — ideally estimated once cohort volume allows (cf. the gated
# cross-biomarker Σ). ``_RHO_MAX`` clamps ρ below the singular fully-redundant
# limit (identical estimators), where the error covariance is non-invertible.
GENETIC_COHORT_CORRELATION = 0.5
_RHO_MAX = 0.99


def combine_priors(
    *,
    genetic_mean: float,
    genetic_sd: float,
    population: PopulationPrior | None,
    correlation: float = 0.0,
) -> tuple[float, float]:
    """Best-linear-unbiased fusion of the genetic and population priors.

    The genetic prior ``N(genetic_mean, genetic_sd²)`` and the cohort-pooled
    population prior ``N(population.mean, population.sd²)`` are two noisy views of
    the same latent θ. Treating their errors as jointly Normal with correlation
    ``correlation`` (``ρ``), the minimum-variance unbiased estimate of θ is the
    GLS combination under ``Σ = [[σ_g², ρσ_gσ_p], [ρσ_gσ_p, σ_p²]]``:

        w_g ∝ σ_p² − ρσ_gσ_p,   w_p ∝ σ_g² − ρσ_gσ_p
        μ   = (w_g·μ_g + w_p·μ_p) / (w_g + w_p)
        Var = σ_g²σ_p²(1 − ρ²) / (w_g + w_p)

    At ``ρ = 0`` (the default) this reduces **exactly** to precision-weighted
    fusion (``τ = τ_g + τ_p``) — every existing caller is unchanged. At ``ρ > 0``
    the combined precision is lower, correcting the genetics×cohort
    double-counting. If one BLUE weight is ≤ 0 (a source so much noisier than the
    other that at this ρ it carries no independent information) the more precise
    source is used alone.

    If the population prior is missing/degenerate (σ ≤ 0) or the genetic σ is
    non-positive, returns the genetic (resp. population) prior unchanged.
    Returns ``(combined_mean, combined_sd)``.
    """
    if population is None or population.sd_pct_change <= 0:
        return genetic_mean, genetic_sd
    if genetic_sd <= 0:
        return population.mean_pct_change, population.sd_pct_change

    sg, sp = genetic_sd, population.sd_pct_change
    mg, mp = genetic_mean, population.mean_pct_change
    rho = min(max(correlation, 0.0), _RHO_MAX)

    cov = rho * sg * sp
    w_g = sp * sp - cov
    w_p = sg * sg - cov
    # A non-positive weight means one source is fully redundant given the other
    # at this correlation — keep only the more precise (smaller-σ) source.
    if w_g <= 0.0 or w_p <= 0.0:
        return (mg, sg) if sg <= sp else (mp, sp)

    denom = w_g + w_p
    det = sg * sg * sp * sp * (1.0 - rho * rho)
    mean_combined = (w_g * mg + w_p * mp) / denom
    sd_combined = math.sqrt(det / denom)
    return mean_combined, sd_combined
