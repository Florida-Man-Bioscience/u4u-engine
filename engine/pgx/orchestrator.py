"""
engine/pgx/orchestrator.py
============================
Top-level entry point that the main pipeline calls.

    pgx_stage(variants, medications=None, bam_path=None, confidence=0.90)
        → PGxProfile

Composes the four PGx phases:

    1. star-allele calls (array / BAM short-read / BAM long-read)
    2. HLA tag-SNP calls
    3. CPIC phenoconversion (DDGI) given current medications
    4. CPIC drug recommendations
    5. Pharmacogenomic PRS
    6. HGNN/rule-based drug-response prediction with Mondrian conformal sets
"""
from __future__ import annotations

from .types import PGxProfile, Phenotype
from .star_alleles import (
    call_star_alleles_from_variants,
    call_hla_from_variants,
    detect_input_type,
)
from .star_alleles.bam_caller import call_star_alleles_from_bam
from .star_alleles.lr_caller import call_star_alleles_from_long_read
from .cpic import (
    apply_phenoconversion,
    generate_recommendations,
)
from .cpic.phenotype import diplotype_to_phenotype, activity_score
from .prs_pgx import calculate_pgx_prs
from .hgnn import predict_drug_response, calibrate_conformal_set


def _enrich_bam_calls_with_phenotype(calls):
    """BAM/LR callers don't compute phenotype themselves; fill it in."""
    for c in calls:
        if c.activity_score is None:
            score = activity_score(c.gene, c.diplotype)
            if score is not None:
                c.activity_score = round(score, 3)
        if c.phenotype == Phenotype.INDETERMINATE:
            c.phenotype = diplotype_to_phenotype(c.gene, c.diplotype)
    return calls


def _merge_calls(array_calls, bam_calls):
    """BAM calls take precedence over array calls when they cover the same gene."""
    by_gene = {c.gene: c for c in array_calls}
    for c in bam_calls:
        by_gene[c.gene] = c          # overwrite
    return list(by_gene.values())


def _summarize(profile: PGxProfile) -> str:
    parts: list[str] = []
    n_recs = len(profile.recommendations)
    n_actionable = sum(1 for c in profile.star_alleles if c.phenotype not in (
        Phenotype.NORMAL, Phenotype.INDETERMINATE,
    ))
    n_hla = sum(1 for h in profile.hla_calls if h.present)

    if n_actionable:
        parts.append(f"{n_actionable} actionable pharmacogene phenotype(s) detected")
    if n_hla:
        parts.append(f"{n_hla} HLA risk allele(s) present")
    if profile.phenoconversion_notes:
        parts.append(f"{len(profile.phenoconversion_notes)} phenoconversion event(s)")
    if n_recs:
        parts.append(f"{n_recs} drug-specific recommendation(s)")
    if not parts:
        return "No actionable pharmacogenomic findings."
    return "; ".join(parts) + "."


def pgx_stage(
    variants: list[dict],
    medications: list[str] | None = None,
    bam_path: str | None = None,
    confidence: float = 0.90,
) -> PGxProfile:
    """
    Run the full pharmacogenomics stage and return a populated PGxProfile.
    """
    input_path = detect_input_type(bam_path)

    # 1. Star alleles
    array_calls = call_star_alleles_from_variants(variants)
    bam_calls = []
    if input_path == "bam_sr":
        bam_calls = _enrich_bam_calls_with_phenotype(
            call_star_alleles_from_bam(bam_path or "")
        )
    elif input_path == "bam_lr":
        bam_calls = _enrich_bam_calls_with_phenotype(
            call_star_alleles_from_long_read(bam_path or "")
        )
    star_calls = _merge_calls(array_calls, bam_calls)

    # 2. HLA
    hla_calls = call_hla_from_variants(variants)

    # 3. Phenoconversion (DDGI)
    star_calls, pheno_notes = apply_phenoconversion(star_calls, medications)

    # 4. CPIC drug recommendations
    recommendations = generate_recommendations(star_calls, hla_calls)

    # 5. Pharmacogenomic PRS
    prs_results = calculate_pgx_prs(variants)

    # 6. HGNN/rule-based drug-response prediction + Mondrian conformal calibration
    raw_predictions = predict_drug_response(star_calls, hla_calls, prs_results)
    drug_predictions = calibrate_conformal_set(raw_predictions, confidence=confidence)

    profile = PGxProfile(
        star_alleles=star_calls,
        hla_calls=hla_calls,
        recommendations=recommendations,
        prs_results=prs_results,
        drug_predictions=drug_predictions,
        phenoconversion_notes=pheno_notes,
        input_path=input_path,
    )
    profile.summary_text = _summarize(profile)
    return profile
