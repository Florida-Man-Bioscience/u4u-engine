"""
engine/tracking/feature_adapters/prs_adapter.py
===============================================
Polygenic inflammatory-baseline responder feature (Phase-1 fan-out).

Turns the patient's *systemic-inflammation* polygenic risk score into a small,
signed, standardised responder feature. A genetically high inflammatory
baseline (elevated CRP / IL-6 / TNF-α set-point) reflects a chronic
pro-inflammatory, catabolic milieu that modestly **dampens** the tissue-
regenerative and metabolic response to peptide therapy — the same "inflammaging"
axis that impairs wound healing and drives inflammation-linked insulin
resistance. So:

    higher inflammatory PRS  ⇒  positive feature value  ⇒  (β < 0) lower η
    lower  inflammatory PRS  ⇒  negative feature value  ⇒  (β < 0) higher η

The magnitude is deliberately modest and the feature carries wide uncertainty:
it enters the responder-index *mean* only a little (ridge-regularised, small
|β|) while its variance widens ``Var(η)`` — the honest "we have a weak signal"
posture required by the HBRI honesty contract. It must never produce a large,
confident mean shift.

Data sourcing — why we read the pipeline's ``prs_profile``, not the profile
--------------------------------------------------------------------------
The adapter needs an INF-PRS computed in the PRS panel's *own* effect-allele
orientation. The pipeline already produces exactly that object:
``engine.annotators.prs_calculator.calculate_prs`` runs over the raw annotated
variants and emits a ``prs_profile`` dict on the ``/analyze`` result. That is
the sound source, so we read it from ``ResponderContext.extra["prs_profile"]``.

We deliberately do **not** recompute the PRS from the tracking
``GeneticProfile.variants``. That store is (a) catalog-scoped — the real-data
path (:mod:`engine.tracking.pharmgkb_catalog`) is GLP-1-only and carries none
of the ten INF-PRS SNPs — and (b) stored in the *tracking catalog's* effect-
allele orientation, which is not the INF-PRS panel's. Concretely rs1800795 is
``effect_allele="C"`` in ``VARIANT_CATALOG`` but ``"G"`` in the INF-PRS panel,
so a homozygous genotype would feed the PRS an inverted dosage. Recomputing
from the tracking profile is therefore not merely lossy but *wrong*, and a
flipped-allele PRS is precisely the confident-wrong mean shift the contract
forbids.

Two follow-ups this implies (see ``docs/models/peptide-response-model.md``):
  1. *Persistence / threading.* Persist ``run_pipeline``'s ``prs_profile``
     alongside the tracking genetic profile and populate
     ``ResponderContext.extra["prs_profile"]`` in ``analysis.predict_response``
     so this adapter actually activates. (Out of scope here — the Phase-1
     contract forbids editing ``analysis.py``.)
  2. *Allele-orientation.* Only if a future path ever recomputes INF-PRS from
     the tracking profile: reconcile the tracking-catalog vs INF-PRS-panel
     effect-allele orientation first (see the rs1800795 example above).

Persistence gap (follow-up)
---------------------------
Per follow-up (1) above, nothing threads ``prs_profile`` into
``ResponderContext.extra`` yet (``analysis.predict_response`` builds the context
without it, and the tracking profile store does not persist the PRS). Until
that is wired, this adapter is a graceful no-op — it fires only when a caller
supplies a ``prs_profile`` and
otherwise contributes nothing.
"""
from __future__ import annotations

from ..responder_index import Feature, ResponderContext, register_adapter

# ── Peptide mask ────────────────────────────────────────────────────────────
# Peptides whose response is mechanistically sensitive to the systemic
# inflammatory set-point: tissue-regenerative / repair families and the
# metabolic / insulin-axis families. Anti-inflammatory peptides (KPV, LL-37,
# Thymosin Alpha-1, Selank) are intentionally EXCLUDED — for them inflammation
# is the therapeutic *target*, not a response dampener, so the sign would be
# wrong. Names must match the catalog / panel spelling exactly.
_MASKED_PEPTIDES: frozenset[str] = frozenset({
    # Regenerative / tissue-repair
    "BPC-157",
    "TB-500",
    "Thymosin Beta-4",
    "GHK-Cu",
    "MGF",
    # Metabolic / insulin-axis
    "MOTS-c",
    "AOD-9604",
    # GLP-1 receptor agonist class (metabolic)
    "Semaglutide",
    "Tirzepatide",
    "Liraglutide",
})

# Require a minimally informative INF-PRS before firing: at least this many of
# the ten panel SNPs must have been genotyped. Below this the score is noise,
# so we contribute nothing rather than a spurious signal.
_MIN_INFLAM_VARIANTS = 3

# Ridge-regularised, non-genetic coefficient. NEGATIVE: high inflammation
# dampens response. Small magnitude keeps βᵀx (and hence the mean shift) modest
# — with the standardisation below the extreme-HIGH mean shift is ~0.12 on η.
_BETA = -0.10

# The INF-PRS ``prs_score`` is a 0–1 percentile (≈ uniform under the reference
# population), so centre at 0.5 and scale by the uniform SD (1/√12 ≈ 0.2887) to
# get a standardised value in roughly [-1.7, +1.7]; βᵀx stays O(1).
_SCORE_CENTER = 0.5
_UNIFORM_SD = (1.0 / 12.0) ** 0.5

# Wide uncertainty on the (standardised) feature value: PRS is a coarse, noisy
# predictor of the actual inflammatory milieu and of its effect on response, so
# we treat the patient's value as about as uncertain as the population spread.
# This is the SD half of the honesty contract — it widens Var(η).
_FEATURE_VARIANCE = 1.0


def _inflammatory_score(context: ResponderContext) -> float | None:
    """Return the systemic-inflammation ``prs_score`` (0–1) for this patient,
    or ``None`` when no sufficiently-informed PRS is available (graceful no-op).

    Reads only the pipeline-computed ``prs_profile`` handed in via
    ``context.extra`` — see the module docstring for why we do not recompute
    from the tracking profile.
    """
    extra = context.extra or {}
    prs_profile = extra.get("prs_profile")
    if not isinstance(prs_profile, dict):
        return None

    trait_scores = prs_profile.get("trait_scores")
    if not isinstance(trait_scores, dict):
        return None
    inf = trait_scores.get("systemic_inflammation")
    if not isinstance(inf, dict):
        return None

    if int(inf.get("variants_found", 0)) < _MIN_INFLAM_VARIANTS:
        return None

    score = inf.get("prs_score")
    if not isinstance(score, (int, float)):
        return None
    return float(score)


@register_adapter
class PRSInflammatoryBaselineAdapter:
    """Signed inflammatory-baseline responder feature (optional, β < 0)."""

    name = "prs_inflammatory_baseline"
    # Optional adapter: absent PRS data is an honest no-op, and any failure is
    # isolated by build_feature_vector rather than sinking the whole index.
    required = False

    def peptide_mask(self, peptide_name: str) -> bool:
        return peptide_name in _MASKED_PEPTIDES

    def features(self, context: ResponderContext) -> dict[str, Feature]:
        score = _inflammatory_score(context)
        if score is None:
            return {}
        # Standardise the 0–1 percentile to a signed, O(1) value: positive =
        # high inflammatory baseline. With β < 0 this dampens η.
        value = (score - _SCORE_CENTER) / _UNIFORM_SD
        return {
            self.name: Feature(
                name=self.name,
                value=value,
                beta=_BETA,
                variance=_FEATURE_VARIANCE,
                source=self.name,
            )
        }
