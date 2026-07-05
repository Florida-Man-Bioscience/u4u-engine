"""
engine/tracking/dose_response.py
================================
Saturating dose-response multiplier — **DESIGN-ONLY STUB (Phase 1, gated OFF)**.

Status
------
This module is a *design stub*. It is **not** wired into any live prediction
path — nothing in ``predict_response`` (or anywhere else in ``engine/``) imports
it, and the feature is gated behind the module constant
:data:`DOSE_RESPONSE_ENABLED`, which defaults to ``False``. Importing this
module has no effect on the running model; it exists so the maths, the
parameterisation, and the intended wiring point can be reviewed and tested
ahead of the dose-varied cohort data needed to actually calibrate it.

**Do not wire this into ``predict_response`` until dose-stratified cohort data
exists.** The current tracking cohort is effectively single-dose per peptide, so
``EC50`` is unidentifiable — fitting it against single-dose data would fit noise
and break the calibrated 95% coverage that ``tests/.../test_calibration.py``
guards. See the "Dose–response (gated)" section of
``docs/models/peptide-response-model.md``.

The model
---------
The latent effect θ in :mod:`engine.tracking.bayes` is the fractional change
from baseline *at plateau* under a peptide's reference dose. When a patient is
dosed above or below that reference, we would like to scale θ by how far the
dose sits along a saturating (Emax / EC50) response curve.

Raw Emax response (Hill coefficient fixed at 1):

    emax(dose) = dose / (dose + EC50)

This is monotonic increasing in ``dose`` and saturates at 1 as ``dose → ∞``.
Because θ is *defined at the reference dose*, we work with the response
**normalised against the reference dose** so the multiplier is exactly 1 there:

    s(dose) = emax(dose) / emax(ref_dose)
            = (dose / (dose + EC50)) / (ref_dose / (ref_dose + EC50))

Key properties (all covered by ``test_dose_response.py``):
    * ``s(ref_dose) == 1``           — the reference dose is the anchor.
    * ``s`` is strictly increasing in ``dose``.
    * ``s`` saturates: as ``dose → ∞``, ``s → 1 + EC50/ref_dose`` (a finite
      plateau **> 1**, *not* 1 — the raw Emax saturates at 1, but dividing by
      ``emax(ref) < 1`` lifts the normalised plateau above 1).

Scaling the latent effect
--------------------------
The intended use is an *effective* latent effect:

    θ_eff = θ · s(dose) / s(ref_dose)

Since ``s(ref_dose) == 1`` by construction, the ``/ s(ref_dose)`` term is
identically 1 — it is kept explicit in :func:`effective_theta` to mirror the
spec and make the "θ reduces to θ at the reference dose" invariant obvious, not
because it performs a second normalisation.
"""
from __future__ import annotations

from dataclasses import dataclass

# ── Feature gate ────────────────────────────────────────────────────────────
# Off by default. Kept as a plain module constant on purpose: no env-var
# reading, so there is no accidental-truthy surface. Flipping this to True does
# NOT wire the module in either — it is a design stub with no live call site.
DOSE_RESPONSE_ENABLED = False


@dataclass(frozen=True)
class DoseResponseParams:
    """Per-peptide dose-response placeholders.

    Attributes
    ----------
    ec50:
        Dose (in the peptide's native unit) at which the *raw* Emax response
        reaches half of its maximum. **Placeholder** — not fit from data.
    ref_dose:
        Reference dose at which the latent θ is defined; the normalised
        multiplier :func:`s` equals 1 here.
    unit:
        Human-readable dose unit, for documentation only.
    """
    ec50: float
    ref_dose: float
    unit: str = ""


# Placeholder parameters. These are illustrative anchors, NOT calibrated
# values — real EC50s require dose-varied cohort data the study does not yet
# have. ref_dose values are drawn from the dose ranges used by
# ``engine/tracking/seed.py`` scenarios (mid-range for CJC-1295 and MOTS-c;
# the higher of the two seeded doses for BPC-157) so the stub is at least
# roughly self-consistent with the seed data.
DEFAULT_PARAMS = DoseResponseParams(ec50=1.0, ref_dose=1.0, unit="")

PEPTIDE_PARAMS: dict[str, DoseResponseParams] = {
    # EC50 / ref_dose are placeholders pending dose-stratified data.
    "BPC-157": DoseResponseParams(ec50=250.0, ref_dose=500.0, unit="mcg"),
    "CJC-1295": DoseResponseParams(ec50=1.5, ref_dose=2.0, unit="mg"),
    "MOTS-c": DoseResponseParams(ec50=8.0, ref_dose=15.0, unit="mg"),
}


def params_for(peptide: str) -> DoseResponseParams:
    """Return placeholder dose-response params for ``peptide``.

    Falls back to :data:`DEFAULT_PARAMS` for peptides without an explicit
    entry. (Design stub — the returned params are not calibrated.)
    """
    return PEPTIDE_PARAMS.get(peptide, DEFAULT_PARAMS)


def _emax(dose: float, ec50: float) -> float:
    """Raw saturating Emax response ``dose / (dose + EC50)`` (Hill = 1).

    Strictly increasing on ``dose ≥ 0`` and saturating at 1 as ``dose → ∞``.
    Doses below 0 are clamped to 0 (non-physical), so the curve is flat — not
    strictly increasing — on the negative domain.
    """
    if ec50 <= 0:
        raise ValueError("ec50 must be positive")
    d = max(dose, 0.0)
    return d / (d + ec50)


def s(dose: float, *, ec50: float, ref_dose: float) -> float:
    """Saturating dose multiplier normalised so ``s(ref_dose) == 1``.

        s(dose) = emax(dose) / emax(ref_dose)

    Parameters
    ----------
    dose:
        Administered dose (same unit as ``ref_dose``); clamped at ``0``.
    ec50:
        Half-maximal dose for the raw Emax curve. Must be positive.
    ref_dose:
        Reference dose at which θ is defined. Must be positive.

    Returns
    -------
    float
        The normalised multiplier. Equals ``1.0`` at ``dose == ref_dose``,
        increases monotonically with ``dose`` on ``dose ≥ 0`` (doses below 0
        clamp to 0), and approaches the finite plateau ``1 + ec50 / ref_dose``
        as ``dose → ∞``.
    """
    if ref_dose <= 0:
        raise ValueError("ref_dose must be positive")
    return _emax(dose, ec50) / _emax(ref_dose, ec50)


def effective_theta(
    theta: float,
    dose: float,
    *,
    ec50: float,
    ref_dose: float,
) -> float:
    """Dose-scaled latent effect ``θ_eff = θ · s(dose) / s(ref_dose)``.

    Since :func:`s` is normalised so ``s(ref_dose) == 1``, the
    ``/ s(ref_dose)`` factor is identically 1; it is written explicitly to
    mirror the spec and make the reference-dose invariant (``θ_eff == θ`` when
    ``dose == ref_dose``) self-evident.

    **Stub — not called by any live prediction path.** When wired (see the
    docs), this would scale the prior mean μ₀ = η · expected_pct before the
    conjugate update in ``predict_response``.
    """
    return theta * s(dose, ec50=ec50, ref_dose=ref_dose) / s(
        ref_dose, ec50=ec50, ref_dose=ref_dose
    )
