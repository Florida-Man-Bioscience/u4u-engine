"""
engine/annotators/peptide_mapper.py
====================================
Predicts therapeutic efficacy of various peptides based on patient genetics.

Public interface
----------------
    map_peptide_coverage(variants: list[dict]) -> dict
    generate_peptide_summary(mapping: dict) -> str
"""

from __future__ import annotations
from typing import Optional

from .bpc157_predictor import BPC157_PATHWAY_GENES

# Build BPC-157 standalone gene set from the predictor's pathway definitions
_BPC157_ALL_GENES = set()
for _pw in BPC157_PATHWAY_GENES.values():
    _BPC157_ALL_GENES |= _pw["genes"]

PEPTIDE_GENE_MAP: dict[str, dict] = {
    "BPC-157": {
        "genes": _BPC157_ALL_GENES,
        "rationale": (
            "Full BPC-157 response prediction across all relevant pathways: "
            "NO/eNOS, VEGF/angiogenesis, inflammatory cytokines, GH/IGF-1, "
            "collagen/tissue repair, antioxidant/HO-1, gut barrier, and "
            "dopamine/serotonin modulation."
        ),
        "effect_type": "compensatory",
        "refs": ["[1-9]"],
        "category": "multi_pathway",
        "category_display": "Multi-Pathway Regenerative",
    },
    "GHK-Cu + BPC-157 + TB-500": {
        "genes": {"COL1A1", "COL1A2", "SMYD3"},
        "rationale": "Predict ECM repair capacity and collagen synthetic response.",
        "effect_type": "compensatory",
        "refs": ["[1-3]"],
        "category": "tissue_repair",
        "category_display": "Tissue Repair / Collagen Synthesis",
    },
    "CJC-1295 + Ipamorelin": {
        "genes": {"GHSR"},
        "rationale": "Identify loss-of-function receptor variants that blunt GH secretagogue response.",
        "effect_type": "receptor",
        "refs": ["[4-7]"],
        "category": "growth_hormone",
        "category_display": "Growth Hormone Secretagogue",
    },
    "BPC-157 + TB-500": {
        "genes": {"NOS3"},
        "rationale": "Predict NO-dependent angiogenic and healing response.",
        "effect_type": "compensatory",
        "refs": ["[8-9]"],
        "category": "angiogenesis",
        "category_display": "Angiogenesis / Healing",
    },
    "AOD-9604": {
        "genes": {"ADRB3"},
        "rationale": "Predict lipolytic response; Trp64Arg variant impairs β3-AR function.",
        "effect_type": "receptor",
        "refs": ["[10]"],
        "category": "weight_management",
        "category_display": "Weight Management / Lipolysis",
    },
    "MOTS-c": {
        "genes": {"MT-RNR1"},
        "rationale": "K14Q substitution in MOTS-c peptide reduces insulin-sensitizing activity (males).",
        "effect_type": "receptor",
        "refs": ["[11]"],
        "category": "metabolic",
        "category_display": "Metabolic / Insulin Sensitization",
    },
    "Epithalon": {
        "genes": {"TERT"},
        "rationale": "Stratify telomerase activation benefit vs. cancer risk (VNTR2-1, rs2736100).",
        "effect_type": "caution",
        "refs": ["[12-14]"],
        "category": "longevity",
        "category_display": "Longevity / Telomere Maintenance",
    },
    "Thymosin Alpha-1": {
        "genes": {"TLR2", "TLR4", "TLR9"},
        "rationale": "Predict immunomodulatory response via TLR-dependent DC activation.",
        "effect_type": "receptor",
        "refs": ["[15-17]"],
        "category": "immune",
        "category_display": "Immune Modulation",
    },
    "Matrixyl": {
        "genes": {"COL1A1", "IRF4"},
        "rationale": "Predict collagen synthesis upregulation capacity.",
        "effect_type": "compensatory",
        "refs": ["[2-3, 18]"],
        "category": "skin",
        "category_display": "Skin / Anti-Aging",
    },
    "Argireline": {
        "genes": {"SNAP25"},
        "rationale": "Predict SNARE-complex modulation efficacy (parallels BoNT-A pharmacogenomics).",
        "effect_type": "receptor",
        "refs": ["[19-20]"],
        "category": "skin",
        "category_display": "Skin / Neuromodulation",
    },
    "SNAP-8": {
        "genes": {"SNAP25", "SV2C"},
        "rationale": "Predict neuromodulatory efficacy and duration.",
        "effect_type": "receptor",
        "refs": ["[19, 21]"],
        "category": "skin",
        "category_display": "Skin / Neuromodulation",
    },
}

def _determine_efficacy(effect_type: str, found_count: int) -> tuple[str, str]:
    if found_count == 0:
        return ("Baseline", "No relevant variants detected. Expected baseline efficacy.")

    if effect_type == "compensatory":
        return ("Strong Fit", "Variants detected in target pathways. This therapeutic strongly compensates for these genetic deficits.")
    elif effect_type == "receptor":
        return ("Altered / Reduced", "Variants in targeted receptors detected. This may blunt or alter the therapeutic efficacy.")
    elif effect_type == "caution":
        return ("Caution", "Variants detected that require clinical screening (e.g. oncology risk) before initiating therapy.")

    return ("Unknown", "Variants detected with unknown net effect.")


def _collect_relevant_variants(variants: list[dict], target_genes_upper: set[str]) -> list[dict]:
    """Filter variant list to those whose genes overlap the target gene set."""
    relevant = []
    for v in variants:
        genes = v.get("genes", [])
        if isinstance(genes, str):
            genes = [genes]
        v_genes_upper = {g.upper() for g in genes if g}
        if v_genes_upper & target_genes_upper:
            relevant.append(v)
    return relevant


def map_peptide_coverage(variants: list[dict]) -> dict:
    patient_genes: set[str] = set()
    for v in variants:
        genes = v.get("genes", [])
        if isinstance(genes, str):
            genes = [genes]
        for g in genes:
            if g:
                patient_genes.add(g.upper())

    recommendations = []
    for peptide_name, info in PEPTIDE_GENE_MAP.items():
        target_genes = info["genes"]
        target_upper = {g.upper() for g in target_genes}
        genes_found = sorted(patient_genes & target_upper)
        coverage = len(genes_found) / max(len(target_genes), 1)

        predicted_tier, prediction_desc = _determine_efficacy(info["effect_type"], len(genes_found))

        # Attach the actual variant objects relevant to this peptide
        relevant_variants = _collect_relevant_variants(variants, target_upper)

        recommendations.append({
            "peptide_name": peptide_name,
            "genes_for_genotyping": sorted(target_genes),
            "genes_found": genes_found,
            "genes_missing": sorted(target_upper - patient_genes),
            "coverage": round(coverage, 2),
            "predicted_tier": predicted_tier,
            "prediction_description": prediction_desc,
            "rationale": info["rationale"],
            "references": info["refs"],
            "category": info["category"],
            "category_display": info["category_display"],
            "relevant_variants": relevant_variants,
        })

    # Sort: those with variants first, then alphabetically
    recommendations.sort(key=lambda r: (0 if len(r["genes_found"]) > 0 else 1, r["peptide_name"]))

    peptides_with_variants = sum(1 for r in recommendations if len(r["genes_found"]) > 0)
    summary_text = generate_peptide_summary(recommendations)

    return {
        "recommendations": recommendations,
        "summary_text": summary_text,
        "genes_found_total": sorted(patient_genes),
        "peptides_with_coverage": peptides_with_variants,
    }

def generate_peptide_summary(recommendations: list[dict]) -> str:
    if not recommendations:
        return "No peptide therapy candidates were evaluated."

    with_variants = [r for r in recommendations if len(r["genes_found"]) > 0]

    if not with_variants:
        return "No modifying variants were detected in any of the targeted peptide pathways. All evaluated peptides are predicted to have standard baseline efficacy."

    fits = [r["peptide_name"] for r in with_variants if r["predicted_tier"] == "Strong Fit"]
    altered = [r["peptide_name"] for r in with_variants if r["predicted_tier"] == "Altered / Reduced"]
    caution = [r["peptide_name"] for r in with_variants if r["predicted_tier"] == "Caution"]

    parts = [f"Variants detected alter the predicted efficacy of {len(with_variants)} peptide(s)."]
    if fits:
        parts.append(f"Strong therapeutic fits found due to identified deficits for: {', '.join(fits)}.")
    if altered:
        parts.append(f"Potential receptor modifications or reduced efficacy predicted for: {', '.join(altered)}.")
    if caution:
        parts.append(f"Clinical caution or lab screening recommended for: {', '.join(caution)}.")

    return " ".join(parts)
