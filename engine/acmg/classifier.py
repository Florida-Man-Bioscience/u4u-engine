"""
engine/acmg/classifier.py
=========================
Assemble ACMG/AMP evidence codes for a variant from the annotations the engine
already has, then combine them (``criteria.combine``) into a five-tier
classification.

IMPORTANT — scope and honesty
-----------------------------
This is an *automated evidence-assembly* aid, NOT a final clinical
classification. It only applies the subset of ACMG/AMP codes that can be
derived defensibly from available data (population frequency, predicted
consequence, optional in-silico calls). It deliberately does **not** invent
evidence it cannot support:

  - PVS1 (null variant) is only *counted* when the gene is in a configured
    loss-of-function-mechanism set; otherwise it is reported as a *candidate*
    code requiring curation (a null variant in a gene where LoF is not the
    disease mechanism must not be called PVS1).
  - PM2 is applied at SUPPORTING strength (ClinGen SVI recommendation) and only
    when a real population frequency is known (absence of data ≠ absence in
    population).
  - ClinVar is NOT converted into an ACMG code (PP5/BP6 are deprecated); the
    ClinVar value is returned alongside for the reviewer to compare.
  - Functional, segregation, de novo, case-control, and codon-level evidence
    (PS3/BS3, PP1/BS4, PS2/PM6, PS4, PS1/PM5) are not assessed here.

For clinical use, a qualified laboratory professional must review the assembled
evidence and sign out the final classification (``requires_human_review`` is
always True).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .criteria import Classification, EvidenceCode, Strength, combine

# Null / loss-of-function consequences (SO terms) relevant to PVS1.
_NULL_CONSEQUENCES = frozenset({
    "stop_gained", "frameshift_variant", "splice_donor_variant",
    "splice_acceptor_variant", "start_lost", "transcript_ablation",
})
# Protein-length-changing consequences relevant to PM4.
_LENGTH_CHANGING = frozenset({
    "stop_lost", "inframe_deletion", "inframe_insertion",
})

_DISCLAIMER = (
    "Automated ACMG/AMP (2015) evidence assembly from available annotations. "
    "This is NOT a final clinical classification: only a subset of criteria is "
    "assessed (population frequency, predicted consequence, optional in-silico), "
    "and functional/segregation/de novo/case-control/codon evidence is not. A "
    "qualified laboratory professional must review the evidence and sign out the "
    "final classification."
)


@dataclass(frozen=True)
class AcmgConfig:
    ba1_af: float = 0.05            # stand-alone benign at/above this AF
    bs1_af: float = 0.01           # strong benign at/above this AF (below BA1)
    pm2_af: float = 0.0001         # moderate→supporting rare threshold (below this)
    lof_mechanism_genes: frozenset = field(default_factory=frozenset)


def _freq(variant: dict):
    """Prefer popmax; fall back to global AF. Returns float or None."""
    popmax = variant.get("gnomad_popmax")
    if isinstance(popmax, (int, float)):
        return float(popmax)
    af = variant.get("gnomad_af")
    if isinstance(af, (int, float)):
        return float(af)
    return None


def assign_codes(variant: dict, config: AcmgConfig | None = None) -> tuple[list[EvidenceCode], list[EvidenceCode]]:
    """
    Return (applied, candidate) evidence codes for a variant.

    ``applied`` codes are counted toward the classification; ``candidate`` codes
    are surfaced for a curator but not counted (insufficient automated support).
    """
    cfg = config or AcmgConfig()
    applied: list[EvidenceCode] = []
    candidate: list[EvidenceCode] = []

    genes = variant.get("genes") or []
    if isinstance(genes, str):
        genes = [genes]
    genes_upper = {g.upper() for g in genes if g}
    consequence = variant.get("consequence") or "unknown"
    af = _freq(variant)

    # ── Population frequency: BA1 / BS1 / PM2 ────────────────────────────────
    if af is not None:
        if af >= cfg.ba1_af:
            applied.append(EvidenceCode(
                "BA1", Strength.STAND_ALONE,
                f"Allele frequency {af:.3g} ≥ {cfg.ba1_af:.3g} (stand-alone benign)."))
        elif af >= cfg.bs1_af:
            applied.append(EvidenceCode(
                "BS1", Strength.BENIGN_STRONG,
                f"Allele frequency {af:.3g} ≥ {cfg.bs1_af:.3g} (greater than expected for disorder)."))
        elif af < cfg.pm2_af:
            applied.append(EvidenceCode(
                "PM2_Supporting", Strength.SUPPORTING,
                f"Allele frequency {af:.3g} < {cfg.pm2_af:.3g} (rare/absent; ClinGen-downgraded PM2)."))
    else:
        candidate.append(EvidenceCode(
            "PM2_Supporting", Strength.SUPPORTING,
            "No population frequency available — cannot confirm rarity (absence of data ≠ absent)."))

    # ── PVS1: null variant in a LoF-mechanism gene ───────────────────────────
    if consequence in _NULL_CONSEQUENCES:
        lof_gene = genes_upper & set(cfg.lof_mechanism_genes)
        rationale = f"Null variant ({consequence}) in {', '.join(sorted(genes_upper)) or 'unknown gene'}"
        if lof_gene:
            applied.append(EvidenceCode(
                "PVS1", Strength.VERY_STRONG,
                rationale + "; LoF is an established mechanism for this gene."))
        else:
            candidate.append(EvidenceCode(
                "PVS1", Strength.VERY_STRONG,
                rationale + "; PVS1 not counted — LoF mechanism not confirmed for this gene "
                "(requires curation, NMD/last-exon assessment)."))

    # ── PM4: protein length change (inframe indel / stop-loss) ───────────────
    if consequence in _LENGTH_CHANGING:
        applied.append(EvidenceCode(
            "PM4", Strength.MODERATE,
            f"Protein length change ({consequence}). Caveat: not assessed for repeat regions."))

    # ── PP3 / BP4: optional in-silico call, only if explicitly provided ──────
    insilico = (variant.get("insilico_pred") or "").lower()
    if insilico in ("deleterious", "damaging", "pathogenic"):
        applied.append(EvidenceCode(
            "PP3", Strength.SUPPORTING, f"In-silico meta-prediction: {insilico}."))
    elif insilico in ("benign", "tolerated", "neutral"):
        applied.append(EvidenceCode(
            "BP4", Strength.BENIGN_SUPPORTING, f"In-silico meta-prediction: {insilico}."))

    return applied, candidate


def classify_acmg(variant: dict, config: AcmgConfig | None = None) -> dict:
    """
    Produce the automated ACMG/AMP evidence assembly + classification for a
    variant. Always flags ``requires_human_review=True``.
    """
    applied, candidate = assign_codes(variant, config)
    classification = combine(applied)
    return {
        "classification": classification.value,
        "applied_codes": [c.to_dict() for c in applied],
        "candidate_codes": [c.to_dict() for c in candidate],
        # ClinVar is reported for comparison, NOT used as an ACMG code.
        "clinvar_comparison": variant.get("clinvar_raw") or variant.get("clinvar"),
        "requires_human_review": True,
        "method": "ACMG/AMP 2015 automated evidence assembly (subset)",
        "disclaimer": _DISCLAIMER,
    }
