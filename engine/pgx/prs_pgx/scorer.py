"""
engine/pgx/prs_pgx/scorer.py
=============================
Pharmacogenomic PRS scorer.

This is a lightweight, additive PRS implementation (sum of allele dosage ×
beta over a curated SNP set). It is enough to be useful from a 23andMe array
today and provides a clean extension point for PRS-PGx-TL (Cheng et al. 2025)
when a target-cohort calibration set is available.

PRS definitions are condensed from published clinical PGx PRS:

  - clopidogrel HTPR     — Qiu 2025 (CHANCE PRS) + Echeverría 2024 (LASSO PgxRS)
                          https://doi.org/10.1161/STROKEAHA.124.049140
                          https://doi.org/10.1371/journal.pone.0306445
  - statin myalgia       — Oni-Orisan 2023 cardiovascular PGx review
                          https://doi.org/10.1002/cpt.2957
  - warfarin sensitivity — supplements monogenic CYP2C9/VKORC1 (IWPC algorithm)

The bundled PRS are intentionally small (5–15 SNPs each) so they remain
auditable. Use scripts/refresh_pgs_catalog.py to ingest larger PGS Catalog
scores for production deployments.
"""
from __future__ import annotations

from ..types import PRSResult

# Each PRS: trait → (drug_context, expected_n, list of (rsid, effect_allele, beta))
PRS_DEFINITIONS: dict[str, dict] = {
    "clopidogrel_htpr": {
        "drug_context": ["clopidogrel"],
        "weights": [
            ("rs4244285",  "A", 0.78),   # CYP2C19*2
            ("rs4986893",  "A", 0.55),   # CYP2C19*3
            ("rs12248560", "T", -0.30),  # CYP2C19*17 protective
            ("rs2032582",  "T", 0.42),   # ABCB1 c.2677G>T (Echeverría)
            ("rs1045642",  "T", 0.35),   # ABCB1 c.3435C>T
            ("rs2286823",  "T", 0.50),   # PON1
            ("rs5918",     "C", 0.20),   # ITGB3 PlA2
        ],
        "tier_cutoffs": (0.5, 1.2),       # low / intermediate / high
    },
    "statin_myalgia": {
        "drug_context": ["simvastatin", "atorvastatin", "rosuvastatin"],
        "weights": [
            ("rs4149056",  "C", 0.85),   # SLCO1B1*5 (dominant)
            ("rs2306283",  "G", 0.20),   # SLCO1B1*1B
            ("rs2231142",  "T", 0.25),   # ABCG2 Q141K
            ("rs4253728",  "G", 0.18),   # PPARA
        ],
        "tier_cutoffs": (0.4, 1.0),
    },
    "warfarin_sensitivity": {
        "drug_context": ["warfarin"],
        "weights": [
            ("rs9923231",  "T", 0.60),   # VKORC1 promoter
            ("rs1799853",  "T", 0.45),   # CYP2C9*2
            ("rs1057910",  "C", 0.65),   # CYP2C9*3
            ("rs2108622",  "T", 0.20),   # CYP4F2
            ("rs7294",     "A", 0.15),   # VKORC1 3173
        ],
        "tier_cutoffs": (0.6, 1.4),
    },
}


def _dosage(variant: dict, effect_allele: str) -> int | None:
    """Return 0/1/2 effect-allele dosage; None if unknown."""
    if not variant:
        return None
    alleles = variant.get("alleles")
    if isinstance(alleles, (list, tuple)) and len(alleles) == 2:
        return sum(1 for a in alleles if str(a).upper() == effect_allele.upper())
    alt = (variant.get("alt") or "").upper()
    if effect_allele.upper() not in alt:
        return 0
    # Fall back to genotype field
    gt = str(variant.get("genotype") or variant.get("gt") or "").lower()
    if gt in ("hom", "1/1", "1|1"):
        return 2
    if gt in ("het", "0/1", "1/0", "0|1", "1|0"):
        return 1
    return 1   # presence implied; treat as het


def calculate_pgx_prs(variants: list[dict]) -> list[PRSResult]:
    var_by_rsid = {v.get("rsid"): v for v in variants if v.get("rsid")}
    results: list[PRSResult] = []

    for trait, spec in PRS_DEFINITIONS.items():
        weights = spec["weights"]
        score = 0.0
        used = 0
        for rsid, eff, beta in weights:
            v = var_by_rsid.get(rsid)
            d = _dosage(v, eff)
            if d is None:
                continue
            used += 1
            score += d * beta

        if used == 0:
            continue

        low, high = spec["tier_cutoffs"]
        if score < low:
            tier = "low"
        elif score < high:
            tier = "intermediate"
        else:
            tier = "high"

        results.append(PRSResult(
            trait=trait,
            score=round(score, 3),
            percentile=None,
            risk_tier=tier,
            n_variants_used=used,
            n_variants_expected=len(weights),
            drug_context=list(spec["drug_context"]),
        ))

    return results
