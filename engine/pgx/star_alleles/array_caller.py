"""
engine/pgx/star_alleles/array_caller.py
========================================
CPIC-style named-allele matcher for variants from a VCF or 23andMe array.

Algorithm (PharmCAT-inspired):
  1. Index input variants by rsID.
  2. For each PGx gene, evaluate each defining-variant set.
  3. Resolve a diplotype from the calls and zygosity. We don't have phasing,
     so we approximate: each present heterozygous variant contributes one
     non-reference haplotype; homozygous variants contribute to both.
  4. Look up activity score per haplotype and sum to a per-gene activity score.
  5. Bin into a phenotype via PHENOTYPE_BINS.

Output: list[StarAlleleCall]
"""
from __future__ import annotations

from ..types import Phenotype, StarAlleleCall
from .allele_definitions import (
    ALLELE_FUNCTIONS,
    ARRAY_LIMITED_GENES,
    DEFINING_VARIANTS,
    PHENOTYPE_BINS,
)


def _zygosity(variant: dict) -> str:
    """Return 'hom' | 'het' | 'ref' based on standard fields if present."""
    gt = variant.get("genotype") or variant.get("gt") or variant.get("zygosity")
    if not gt:
        # Best effort from genotype tuple
        alleles = variant.get("alleles")
        if isinstance(alleles, (list, tuple)) and len(alleles) == 2:
            ref = variant.get("ref")
            if alleles[0] == alleles[1]:
                return "ref" if alleles[0] == ref else "hom"
            return "het"
        return "het"
    gt = str(gt).lower()
    if gt in ("hom", "homozygous", "1/1", "1|1", "aa"):
        return "hom"
    if gt in ("het", "heterozygous", "0/1", "1/0", "0|1", "1|0"):
        return "het"
    return "het"


def _alt_matches(variant: dict, required: str) -> bool:
    """Check whether the variant's ALT allele matches the required letter/marker."""
    if required in ("del", "TA7", "TA8"):
        # Indel-like markers — accept any non-ref call as a positive
        return True
    alt = (variant.get("alt") or "").upper()
    return alt == required.upper() or required.upper() in alt


def _phenotype_for_score(gene: str, score: float) -> Phenotype:
    bins = PHENOTYPE_BINS.get(gene)
    if not bins:
        return Phenotype.INDETERMINATE
    for lo, hi, code in bins:
        if lo - 1e-6 <= score <= hi + 1e-6:
            return Phenotype(code)
    # Outside defined bins → highest or lowest neighbour
    if score > bins[-1][1]:
        return Phenotype(bins[-1][2])
    return Phenotype.INDETERMINATE


def _diplotype_string(allele_calls: list[tuple[str, str]]) -> str:
    """Render a diplotype from two (allele, zygosity) picks."""
    if not allele_calls:
        return "*1/*1"
    if len(allele_calls) == 1:
        return f"*1/{allele_calls[0][0]}"
    return f"{allele_calls[0][0]}/{allele_calls[1][0]}"


def _resolve_gene(
    gene: str,
    var_by_rsid: dict[str, dict],
) -> StarAlleleCall | None:
    defs = DEFINING_VARIANTS.get(gene)
    funcs = ALLELE_FUNCTIONS.get(gene, {})
    if not defs:
        return None

    # Find all alleles whose defining variants are present.
    present_alleles: list[tuple[str, str]] = []  # (allele_name, "het"|"hom")
    for allele_name, defining in defs:
        matched_zygosities: list[str] = []
        all_match = True
        for rsid, required in defining.items():
            v = var_by_rsid.get(rsid)
            if not v or not _alt_matches(v, required):
                all_match = False
                break
            matched_zygosities.append(_zygosity(v))
        if all_match:
            # If any defining variant is hom, the haplotype is on both copies.
            zyg = "hom" if "hom" in matched_zygosities else "het"
            present_alleles.append((allele_name, zyg))

    # TPMT *3A = *3B + *3C co-occurrence
    if gene == "TPMT":
        names = {a for a, _ in present_alleles}
        if "*3B" in names and "*3C" in names:
            zyg = "hom" if all(z == "hom" for n, z in present_alleles if n in ("*3B", "*3C")) else "het"
            present_alleles = [("*3A", zyg)]

    # No variant alleles present → *1/*1
    if not present_alleles:
        score = 2.0 * funcs.get("*1", 1.0) if gene in PHENOTYPE_BINS else None
        if gene == "VKORC1":
            return StarAlleleCall(
                gene=gene, diplotype="G/G", activity_score=2.0,
                phenotype=Phenotype.NORMAL,
                callers_agreed=["array_named_allele"],
                confidence=0.9, evidence_tier="definitive",
            )
        return StarAlleleCall(
            gene=gene, diplotype="*1/*1", activity_score=score,
            phenotype=_phenotype_for_score(gene, score) if score is not None else Phenotype.NORMAL,
            callers_agreed=["array_named_allele"],
            confidence=0.85 if gene not in ARRAY_LIMITED_GENES else 0.6,
            evidence_tier="definitive" if gene not in ARRAY_LIMITED_GENES else "tentative-no-sv",
        )

    # Pick the two highest-priority (lowest-function first → more clinically relevant)
    # Sort so PM/IM alleles dominate the diplotype display
    present_alleles.sort(key=lambda x: funcs.get(x[0], 1.0))

    # Resolve diplotype slots
    haps: list[str] = []
    for allele_name, zyg in present_alleles:
        if zyg == "hom":
            haps = [allele_name, allele_name]
            break
        haps.append(allele_name)
        if len(haps) == 2:
            break
    if len(haps) == 1:
        haps.append("*1")

    # Activity score
    if gene == "VKORC1":
        # Special handling: rs9923231 — homozygous T (A) → 1.0 score (high warfarin sensitivity)
        v = var_by_rsid.get("rs9923231")
        zyg = _zygosity(v) if v else "ref"
        if zyg == "hom":
            score = 1.0
            diplotype = "T/T"
        elif zyg == "het":
            score = 1.5
            diplotype = "G/T"
        else:
            score = 2.0
            diplotype = "G/G"
        return StarAlleleCall(
            gene=gene, diplotype=diplotype, activity_score=score,
            phenotype=Phenotype.NORMAL if score == 2.0 else Phenotype.INTERMEDIATE,
            callers_agreed=["array_named_allele"],
            confidence=0.95, evidence_tier="definitive",
        )

    score = sum(funcs.get(h, 1.0) for h in haps)
    pheno = _phenotype_for_score(gene, score)

    return StarAlleleCall(
        gene=gene,
        diplotype=f"{haps[0]}/{haps[1]}",
        activity_score=round(score, 3),
        phenotype=pheno,
        callers_agreed=["array_named_allele"],
        confidence=0.85 if gene not in ARRAY_LIMITED_GENES else 0.55,
        evidence_tier="definitive" if gene not in ARRAY_LIMITED_GENES else "tentative-no-sv",
        raw_calls={a: z for a, z in present_alleles},
    )


def call_star_alleles_from_variants(variants: list[dict]) -> list[StarAlleleCall]:
    """
    Call star-allele diplotypes for all supported PGx genes from a variant list.

    Each variant dict should include 'rsid', 'ref', 'alt', and ideally
    'genotype' / 'alleles' / 'zygosity' for accurate diplotype resolution.
    """
    var_by_rsid: dict[str, dict] = {}
    for v in variants:
        rsid = v.get("rsid")
        if rsid:
            var_by_rsid[rsid] = v

    calls: list[StarAlleleCall] = []
    for gene in DEFINING_VARIANTS.keys():
        c = _resolve_gene(gene, var_by_rsid)
        if c is not None:
            calls.append(c)
    return calls
