"""
engine/tracking/feature_adapters/covariates_adapter.py
======================================================
Demographic effect-modifier features for the responder index (Phase 1).

``PatientIn`` / the ``patients`` table already collect ``sex`` and
``birth_year`` (and a caller may pass ``weight_kg`` through
``ResponderContext.extra``), but Phase 0 left them **unused** by the model.
This adapter exposes them as standardised, ridge-shrunk effect modifiers on the
responder index η — a *general* covariate source that fires for every peptide.

Design contract (honest, weak priors)
-------------------------------------
These are population-level nudges, not dominant terms. Each feature therefore
carries:

* a **modest, ridge-shrunk point coefficient** ``β_j`` (see ``_AGE_BETA`` etc.)
  so the mean of the prior moves only slightly; and
* a **coefficient-uncertainty variance** folded into the framework's per-value
  ``var_j`` so that including the feature *widens* the responder SD (it never
  fabricates precision).

Coefficient-uncertainty encoding
--------------------------------
The generalised index (``responder_index.py`` §2.1) propagates a variance
``var_j`` sitting on the feature *value* through ``Var(βᵀx) = Σ_j β_j² var_j``.
Our real uncertainty, though, is about the *coefficient*: model the true
contribution as ``c_j = β_j · x_j`` with a ridge prior ``β_j ~ N(β̂_j, σ_β²)``.
Then ``E[c_j] = β̂_j·x_j`` and ``Var(c_j) = x_j² · σ_β²``. To reproduce that
variance through the value-space channel we report::

    value    = x_j                       (standardised demographic)
    beta     = β̂_j                       (ridge-shrunk point estimate)
    variance = (x_j · σ_β / β̂_j)²        ⇒  β̂_j² · variance = x_j² · σ_β²

so the delta method widens ``Var(η)`` by exactly the coefficient uncertainty,
and both the mean nudge and the widening vanish continuously as ``x_j → 0``
(a patient at the reference point contributes nothing). Features whose
standardised value is exactly 0 are omitted entirely so a perfectly-neutral
covariate does not spuriously mark the vector as "rich" (which would flip the
double-counting cap gate in ``analysis.predict_response``).

Sign / mechanism assumptions (deliberately conservative)
--------------------------------------------------------
* **Age** — a weak prior that anabolic/regenerative responsiveness declines
  modestly with age (GH/IGF axis attenuation, slower tissue repair). Sign is a
  conservative population assumption; magnitude is ridge-shrunk toward zero and
  ``σ_β ≈ |β̂|`` (a genuinely weak prior).
* **Sex** — direction is peptide-dependent and genuinely uncertain, so the
  coefficient is the smallest of the three and encoded as a signed contrast
  (male ``+1`` / female ``−1``); any other/unknown value contributes nothing.
* **Weight** — only fires when a caller supplies ``weight_kg`` via
  ``context.extra`` (not persisted in the ``patients`` schema today). Heavier
  body mass mildly dilutes a fixed per-injection dose, so the prior is a small
  negative nudge, ridge-shrunk.

Missing demographics contribute nothing (partial feature vectors are fine); a
patient with no demographics at all yields no features.

Pure stdlib — matches the surrounding tracking code.
"""
from __future__ import annotations

import datetime

from ..responder_index import Feature, ResponderContext, register_adapter

# ── Standardisation reference points ────────────────────────────────────────
# Age centred at 50 and scaled by 20 years so the standardised feature is O(1)
# across a realistic adult span (30 → −1.0, 70 → +1.0).
_AGE_CENTER = 50.0
_AGE_SCALE = 20.0

# Weight centred at 80 kg, scaled by 20 kg (only used when weight_kg is supplied
# through context.extra — see module docstring).
_WEIGHT_CENTER_KG = 80.0
_WEIGHT_SCALE_KG = 20.0

# ── Ridge-shrunk point coefficients (β̂) and their ridge SDs (σ_β) ───────────
# All small: demographics nudge, they do not dominate the genetic weight w
# (which runs ~0.3–1.6). σ_β ≈ |β̂| keeps every prior genuinely weak.
_AGE_BETA = -0.06
_AGE_SIGMA_BETA = 0.06

_SEX_BETA = 0.04            # applied to a signed male(+1)/female(−1) contrast
_SEX_SIGMA_BETA = 0.06

_WEIGHT_BETA = -0.04
_WEIGHT_SIGMA_BETA = 0.05


def _coeff_uncertainty_variance(value: float, beta: float, sigma_beta: float) -> float:
    """Value-space variance that reproduces coefficient uncertainty
    ``Var(c_j) = value² · σ_β²`` through ``β² · var_j`` (see module docstring)."""
    return (value * sigma_beta / beta) ** 2


def _current_year(context: ResponderContext) -> int:
    """Reference year for the age computation. Overridable via
    ``context.extra['current_year']`` so tests are deterministic."""
    override = context.extra.get("current_year") if context.extra else None
    if override is not None:
        return int(override)
    return datetime.date.today().year


def _sex_sign(sex: str | None) -> float | None:
    """Map a free-text sex label to a signed contrast, or ``None`` to abstain.

    Accepts the schema's 'M'/'F'/'other' plus fuller 'male'/'female' spellings
    (``PatientIn.sex`` allows up to 16 chars). Unknown / other / empty abstains.
    """
    if not sex:
        return None
    s = sex.strip().lower()
    if s.startswith("m"):
        return 1.0
    if s.startswith("f"):
        return -1.0
    return None


@register_adapter
class CovariatesAdapter:
    """General demographic effect-modifier features (age, sex, optional weight).

    Optional (``required = False``): a failure here is isolated by
    ``build_feature_vector`` and never sinks the index.
    """

    name = "covariates"
    required = False

    def peptide_mask(self, peptide_name: str) -> bool:
        # Demographics modulate responsiveness generally, so they inform every
        # peptide (unlike a peptide-specific biology adapter).
        return True

    def features(self, context: ResponderContext) -> dict[str, Feature]:
        patient = context.patient
        if patient is None:
            return {}

        feats: dict[str, Feature] = {}

        # ── Age ──────────────────────────────────────────────────────────────
        birth_year = getattr(patient, "birth_year", None)
        if birth_year:
            age = _current_year(context) - int(birth_year)
            x_age = (age - _AGE_CENTER) / _AGE_SCALE
            if x_age != 0.0:  # skip the exactly-neutral case (no signal, no widening)
                feats["age"] = Feature(
                    name="age",
                    value=x_age,
                    beta=_AGE_BETA,
                    variance=_coeff_uncertainty_variance(
                        x_age, _AGE_BETA, _AGE_SIGMA_BETA
                    ),
                    source=self.name,
                )

        # ── Sex ──────────────────────────────────────────────────────────────
        sign = _sex_sign(getattr(patient, "sex", None))
        if sign is not None:
            feats["sex"] = Feature(
                name="sex",
                value=sign,
                beta=_SEX_BETA,
                variance=_coeff_uncertainty_variance(
                    sign, _SEX_BETA, _SEX_SIGMA_BETA
                ),
                source=self.name,
            )

        # ── Weight (optional; only via context.extra) ────────────────────────
        # Truthiness (not ``is not None``) so a 0 / non-positive sentinel is
        # treated as "no weight" — mirroring the ``if birth_year`` guard above.
        # Without this, ``weight_kg = 0`` would standardise to x = −4.0 and fire
        # a large spurious feature.
        weight_kg = context.extra.get("weight_kg") if context.extra else None
        if weight_kg and weight_kg > 0:
            x_w = (float(weight_kg) - _WEIGHT_CENTER_KG) / _WEIGHT_SCALE_KG
            if x_w != 0.0:
                feats["weight"] = Feature(
                    name="weight",
                    value=x_w,
                    beta=_WEIGHT_BETA,
                    variance=_coeff_uncertainty_variance(
                        x_w, _WEIGHT_BETA, _WEIGHT_SIGMA_BETA
                    ),
                    source=self.name,
                )

        return feats
