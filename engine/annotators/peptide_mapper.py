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

from ..peptides import get_biomarker_panel
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
    "Semaglutide": {
        "genes": {"GLP1R", "TCF7L2"},
        "rationale": (
            "Predict GLP-1 receptor agonist weight-loss and glycemic response. "
            "GLP1R coding variants (e.g. Ala316Thr, rs10305420) reduce receptor "
            "expression / cAMP coupling, and the TCF7L2 rs7903146 T allele is "
            "associated with attenuated incretin response."
        ),
        "effect_type": "receptor",
        "refs": ["[22-23]"],
        "category": "glp1",
        "category_display": "GLP-1 / Incretin (Weight & Metabolic)",
    },
    "Tirzepatide": {
        "genes": {"GLP1R", "GIPR", "TCF7L2"},
        "rationale": (
            "Predict dual GIP/GLP-1 receptor agonist response. GIPR variants "
            "(e.g. Glu354Gln, rs1800437) and GLP1R coding variants modify "
            "incretin signaling; TCF7L2 rs7903146 further stratifies glycemic "
            "and body-composition response."
        ),
        "effect_type": "receptor",
        "refs": ["[22-24]"],
        "category": "glp1",
        "category_display": "GLP-1 / Incretin (Weight & Metabolic)",
    },
    "Liraglutide": {
        "genes": {"GLP1R", "TCF7L2"},
        "rationale": (
            "Predict daily GLP-1 receptor agonist response. GLP1R loss-of-function "
            "variants blunt cAMP coupling and the TCF7L2 rs7903146 T allele is "
            "associated with reduced incretin-mediated insulin secretion."
        ),
        "effect_type": "receptor",
        "refs": ["[22, 25]"],
        "category": "glp1",
        "category_display": "GLP-1 / Incretin (Weight & Metabolic)",
    },
}

# ── Regulatory gating ───────────────────────────────────────────────────────
# None of the peptides modeled here are FDA-approved for the indications in
# question; they are investigational / off-label / compounded. A genetic
# pathway match is a mechanistic observation, NOT evidence that the therapy
# will benefit a patient — so patient-facing "efficacy" claims must be gated.
# Populate FDA_APPROVED_PEPTIDES only with peptides approved for the modeled use.
FDA_APPROVED_PEPTIDES: set[str] = set()

_INVESTIGATIONAL_DISCLAIMER = (
    "This peptide is investigational and not FDA-approved for this use. A match "
    "between your genetics and this peptide's target pathways is a mechanistic "
    "observation only — it is NOT a prediction that the therapy will work for "
    "you. No validated genetic predictor of response to this peptide exists, and "
    "human efficacy/safety evidence is limited. Discuss with a qualified clinician."
)


def _is_investigational(peptide_name: str) -> bool:
    return peptide_name not in FDA_APPROVED_PEPTIDES


def _pathway_match_label(tier: str) -> str:
    """
    Translate an internal efficacy tier into a neutral, non-predictive
    'pathway match' descriptor for investigational compounds, so the
    patient-facing output never asserts efficacy that has not been established.
    """
    mapping = {
        "Strong Fit": "Target-pathway variants present (strong overlap)",
        "Possible Fit": "Target-pathway variant(s) of uncertain significance present",
        "Likely Reduced": "Receptor-gene variant present (may affect response)",
        "Possibly Altered": "Receptor-gene variant of uncertain significance present",
        "Caution": "Safety-relevant variant present — clinical screening indicated",
        "Review Recommended": "Variant of uncertain significance in a safety-relevant gene",
        "Review Needed": "Variant(s) present with unclear net effect",
        "Baseline": "No relevant target-gene variants detected",
    }
    return mapping.get(tier, "Target-gene variant(s) present")


def _classify_variants(relevant_variants: list[dict]) -> dict:
    """Classify relevant variants by clinical significance."""
    pathogenic = []
    benign = []
    vus = []
    unknown = []

    for v in relevant_variants:
        cv = (v.get("clinvar") or "").lower()
        if "pathogenic" in cv and "benign" not in cv:
            pathogenic.append(v)
        elif "benign" in cv:
            benign.append(v)
        elif "uncertain" in cv or "vus" in cv:
            vus.append(v)
        else:
            unknown.append(v)

    return {
        "pathogenic": pathogenic,
        "benign": benign,
        "vus": vus,
        "unknown": unknown,
    }


def _determine_efficacy(
    effect_type: str,
    relevant_variants: list[dict],
) -> tuple[str, str, list[str]]:
    """
    Determine predicted efficacy tier based on effect type AND the clinical
    significance of matched variants. Returns (tier, description, reasons).
    """
    if not relevant_variants:
        return (
            "Baseline",
            "No variants detected in this peptide's target genes. Standard baseline efficacy expected.",
            ["No target-gene variants found in your genome"],
        )

    classified = _classify_variants(relevant_variants)
    has_pathogenic = len(classified["pathogenic"]) > 0
    has_vus = len(classified["vus"]) > 0
    has_unknown = len(classified["unknown"]) > 0
    all_benign = all(
        (v.get("clinvar") or "").lower().find("benign") >= 0
        for v in relevant_variants
        if v.get("clinvar")
    ) and any(v.get("clinvar") for v in relevant_variants)

    reasons = []

    # If all matched variants are benign, this is effectively baseline
    if all_benign:
        for v in relevant_variants:
            reasons.append(
                f"{v.get('rsid') or v.get('variant_id')} in {', '.join(v.get('genes', []))} — "
                f"classified benign, no expected impact"
            )
        return (
            "Baseline",
            "Variants detected in target genes but all classified as benign. Standard baseline efficacy expected.",
            reasons,
        )

    # Build reasons from each variant
    for v in relevant_variants:
        vid = v.get("rsid") or v.get("variant_id")
        genes = ", ".join(v.get("genes", []))
        cv = v.get("clinvar") or "no ClinVar classification"
        csq = v.get("consequence_plain") or v.get("consequence") or "unknown consequence"
        reasons.append(f"{vid} in {genes} — {cv} ({csq})")

    if effect_type == "compensatory":
        if has_pathogenic:
            return (
                "Strong Fit",
                "Pathogenic variant(s) detected in target pathways. "
                "This therapeutic is designed to compensate for these genetic deficits.",
                reasons,
            )
        if has_vus or has_unknown:
            return (
                "Possible Fit",
                "Variant(s) of uncertain significance detected in target pathways. "
                "This therapeutic may compensate, but clinical impact is unclear.",
                reasons,
            )

    elif effect_type == "receptor":
        if has_pathogenic:
            return (
                "Likely Reduced",
                "Pathogenic variant(s) in targeted receptor gene(s). "
                "This is likely to reduce or alter therapeutic efficacy.",
                reasons,
            )
        if has_vus or has_unknown:
            return (
                "Possibly Altered",
                "Variant(s) of uncertain significance in receptor gene(s). "
                "Efficacy may be altered but clinical impact is unclear.",
                reasons,
            )

    elif effect_type == "caution":
        if has_pathogenic:
            return (
                "Caution",
                "Pathogenic variant(s) detected that require clinical screening "
                "(e.g. oncology risk) before initiating therapy.",
                reasons,
            )
        if has_vus or has_unknown:
            return (
                "Review Recommended",
                "Variant(s) of uncertain significance detected in safety-relevant gene(s). "
                "Clinical review is recommended before initiating therapy.",
                reasons,
            )

    return (
        "Review Needed",
        "Variant(s) detected in target genes with unclear net effect on this therapy.",
        reasons,
    )


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

        # Attach the actual variant objects relevant to this peptide
        relevant_variants = _collect_relevant_variants(variants, target_upper)

        predicted_tier, prediction_desc, tier_reasons = _determine_efficacy(
            info["effect_type"], relevant_variants,
        )

        panel = get_biomarker_panel(peptide_name)
        investigational = _is_investigational(peptide_name)
        recommendations.append({
            "peptide_name": peptide_name,
            "genes_for_genotyping": sorted(target_genes),
            "genes_found": genes_found,
            "genes_missing": sorted(target_upper - patient_genes),
            "coverage": round(coverage, 2),
            "predicted_tier": predicted_tier,
            "prediction_description": prediction_desc,
            "tier_reasons": tier_reasons,
            "rationale": info["rationale"],
            "references": info["refs"],
            "category": info["category"],
            "category_display": info["category_display"],
            "relevant_variants": relevant_variants,
            "biomarker_panel": panel.to_dict() if panel else None,
            # Regulatory gating — patient-facing efficacy claims are only
            # permitted for FDA-approved peptides; everything else is presented
            # as a non-predictive pathway observation with a disclaimer.
            "investigational": investigational,
            "regulatory_status": (
                "Investigational — not FDA-approved for this use"
                if investigational else "FDA-approved"
            ),
            "efficacy_claim_allowed": not investigational,
            "pathway_match_label": _pathway_match_label(predicted_tier),
            "efficacy_disclaimer": _INVESTIGATIONAL_DISCLAIMER if investigational else "",
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
