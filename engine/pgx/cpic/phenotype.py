"""
engine/pgx/cpic/phenotype.py
=============================
Activity score → phenotype mapping per CPIC's standard scale.

We re-use the per-gene PHENOTYPE_BINS table from
engine/pgx/star_alleles/allele_definitions.py so there is a single source of
truth for the activity-score → phenotype map. Diplotype → phenotype lookup
delegates to the array caller's resolver where possible; for diplotypes from
the BAM consensus path we use ALLELE_FUNCTIONS directly.
"""
from __future__ import annotations

from ..types import Phenotype
from ..star_alleles.allele_definitions import (
    ALLELE_FUNCTIONS,
    PHENOTYPE_BINS,
)


def activity_score(gene: str, diplotype: str) -> float | None:
    """Compute activity score by summing the two haplotype functions in a diplotype."""
    if not diplotype or "/" not in diplotype:
        return None
    parts = diplotype.split("/")
    if len(parts) != 2:
        return None
    funcs = ALLELE_FUNCTIONS.get(gene)
    if not funcs:
        return None
    a, b = parts
    fa = funcs.get(a)
    fb = funcs.get(b)
    if fa is None or fb is None:
        return None
    return fa + fb


def diplotype_to_phenotype(gene: str, diplotype: str) -> Phenotype:
    """Map a diplotype string to a CPIC phenotype code."""
    score = activity_score(gene, diplotype)
    if score is None:
        return Phenotype.INDETERMINATE
    return score_to_phenotype(gene, score)


def score_to_phenotype(gene: str, score: float) -> Phenotype:
    bins = PHENOTYPE_BINS.get(gene)
    if not bins:
        return Phenotype.INDETERMINATE
    for lo, hi, code in bins:
        if lo - 1e-6 <= score <= hi + 1e-6:
            return Phenotype(code)
    if score > bins[-1][1]:
        return Phenotype(bins[-1][2])
    return Phenotype.INDETERMINATE
