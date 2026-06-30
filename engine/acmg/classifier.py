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

import os
from dataclasses import dataclass, field
from pathlib import Path

from .criteria import EvidenceCode, Strength, combine

_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "acmg"
_LOF_GENES_PATH = os.getenv("ACMG_LOF_GENES", str(_DATA_DIR / "lof_mechanism_genes.txt"))
_KNOWN_AA_PATH = os.getenv("ACMG_KNOWN_PATHOGENIC_AA", str(_DATA_DIR / "known_pathogenic_aa.tsv"))


def load_lof_mechanism_genes(path: str | None = None) -> frozenset:
    """
    Load the curated set of genes for which LoF is an established mechanism
    (used to decide whether PVS1 may be counted). Returns an empty set if the
    file is absent.
    """
    p = Path(path or _LOF_GENES_PATH)
    if not p.exists():
        return frozenset()
    genes = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        genes.add(s.upper())
    return frozenset(genes)


def load_known_pathogenic_aa(path: str | None = None) -> dict:
    """
    Load the known-pathogenic-amino-acid reference for PS1/PM5 from a TSV with
    columns ``gene<TAB>protein_pos<TAB>alt_aa`` (blank lines and #-comments
    ignored). Returns ``{(GENE_UPPER, pos): {alt_aa, ...}}`` — empty when the
    file is absent or has no data rows (so PS1/PM5 stay unapplied by default).
    """
    p = Path(path or _KNOWN_AA_PATH)
    if not p.exists():
        return {}
    ref: dict = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.replace(",", "\t").split("\t")
        if len(parts) < 3:
            continue
        gene, pos_s, alt_aa = parts[0].strip().upper(), parts[1].strip(), parts[2].strip().upper()
        try:
            pos = int(pos_s)
        except ValueError:
            continue
        if gene and alt_aa:
            ref.setdefault((gene, pos), set()).add(alt_aa)
    return ref

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
    # Reference of known-pathogenic amino-acid changes for PS1/PM5, keyed by
    # (GENE_UPPER, protein_pos) -> set of pathogenic alt amino acids. Empty by
    # default, so PS1/PM5 are only applied when a real reference is supplied.
    known_pathogenic_aa: dict = field(default_factory=dict)


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

    # ── PS1 / PM5: codon-level, only when a known-pathogenic-AA reference is
    #    supplied (default empty → not assessed). ──────────────────────────────
    ps1_pm5 = _ps1_pm5(variant, genes_upper, cfg)
    if ps1_pm5:
        applied.append(ps1_pm5)

    # ── PP3 / BP4: in-silico call (explicit meta-predictor, or concordant
    #    SIFT + PolyPhen). Supporting strength; conservative (requires
    #    concordance) to avoid over-calling. ────────────────────────────────
    call, basis = _insilico_call(variant)
    if call == "deleterious":
        applied.append(EvidenceCode(
            "PP3", Strength.SUPPORTING, f"In-silico computational evidence: {basis}."))
    elif call == "benign":
        applied.append(EvidenceCode(
            "BP4", Strength.BENIGN_SUPPORTING, f"In-silico computational evidence: {basis}."))

    return applied, candidate


def _ps1_pm5(variant: dict, genes_upper: set, cfg: AcmgConfig) -> EvidenceCode | None:
    """
    PS1 (same amino-acid change as a known pathogenic variant) or PM5 (a
    different change at a residue with a known pathogenic missense), using the
    configured ``known_pathogenic_aa`` reference. Returns the strongest
    applicable code, or None.
    """
    ref = cfg.known_pathogenic_aa
    if not ref:
        return None
    pos = variant.get("protein_pos")
    alt_aa = (variant.get("alt_aa") or "").upper()
    if pos is None or not alt_aa:
        return None
    for gene in genes_upper:
        known = ref.get((gene, pos))
        if not known:
            continue
        known = {a.upper() for a in known}
        if alt_aa in known:
            return EvidenceCode(
                "PS1", Strength.STRONG,
                f"Same amino-acid change ({gene} p.{pos}{alt_aa}) as a known pathogenic variant.")
        return EvidenceCode(
            "PM5", Strength.MODERATE,
            f"Novel change at {gene} residue {pos}, where a different missense is known pathogenic.")
    return None


def _insilico_call(variant: dict) -> tuple[str | None, str]:
    """
    Resolve an in-silico deleterious/benign call.

    Priority: an explicit ``insilico_pred`` (e.g. a calibrated meta-predictor
    such as REVEL mapped to a label) wins; otherwise require **concordant**
    SIFT + PolyPhen (``sift_pred`` / ``polyphen_pred``). Returns
    ``(call, basis_text)`` where call is "deleterious" | "benign" | None.
    """
    explicit = (variant.get("insilico_pred") or "").lower()
    if explicit in ("deleterious", "damaging", "pathogenic"):
        return "deleterious", f"meta-predictor={explicit}"
    if explicit in ("benign", "tolerated", "neutral"):
        return "benign", f"meta-predictor={explicit}"

    sift = (variant.get("sift_pred") or "").lower()
    polyphen = (variant.get("polyphen_pred") or "").lower()
    if sift == "deleterious" and polyphen == "probably_damaging":
        return "deleterious", "SIFT=deleterious & PolyPhen=probably_damaging"
    if sift == "tolerated" and polyphen == "benign":
        return "benign", "SIFT=tolerated & PolyPhen=benign"
    return None, ""


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
        # Sign-out lifecycle (see engine/acmg/signoff.py)
        "status": "pending_review",
        "final_classification": None,
        "sign_out": None,
    }
