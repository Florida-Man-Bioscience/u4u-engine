"""
engine/pgx/cpic/phenoconversion.py
====================================
Drug–Drug–Gene Interaction (DDGI) phenoconversion engine.

Applies the standard CPIC / All-of-Us-2025 model:
    effective_activity = inhibitor_factor × genotypic_activity
where strong inhibitor → 0, moderate → 0.5, weak/none → 1.0.

Reference: Nahid et al. *JAMA Network Open* 2025;8(7) — All of Us cohort
study tying phenoconversion to ED visits among opioid-treated patients
(https://doi.org/10.1001/jamanetworkopen.2025.23543).

Inhibitor table is condensed from the FDA Drug Development Drug Interactions
substrate/inhibitor tables. Drug name matching is case-insensitive and uses
generic stems; brand names should be normalized before lookup.
"""
from __future__ import annotations

from ..types import Phenotype, StarAlleleCall
from .phenotype import score_to_phenotype

# Inhibitor strength: 1.0 = no effect, 0.5 = moderate, 0.0 = strong
CYP_INHIBITORS: dict[str, dict[str, float]] = {
    "CYP2D6": {
        "paroxetine": 0.0,
        "fluoxetine": 0.0,
        "bupropion": 0.0,
        "quinidine": 0.0,
        "terbinafine": 0.0,
        "duloxetine": 0.5,
        "sertraline": 0.5,
        "cinacalcet": 0.5,
        "mirabegron": 0.5,
        "amiodarone": 0.5,
    },
    "CYP2C19": {
        "fluconazole": 0.0,
        "fluvoxamine": 0.0,
        "ticlopidine": 0.0,
        "omeprazole": 0.5,
        "esomeprazole": 0.5,
        "voriconazole": 0.0,
    },
    "CYP2C9": {
        "fluconazole": 0.0,
        "amiodarone": 0.5,
        "miconazole": 0.5,
    },
    "CYP3A5": {
        "ketoconazole": 0.0,
        "itraconazole": 0.0,
        "clarithromycin": 0.0,
        "ritonavir": 0.0,
        "diltiazem": 0.5,
        "verapamil": 0.5,
        "erythromycin": 0.5,
    },
}


def _normalize_drug(name: str) -> str:
    return name.strip().lower().split()[0] if name else ""


def apply_phenoconversion(
    star_calls: list[StarAlleleCall],
    medications: list[str] | None,
) -> tuple[list[StarAlleleCall], list[str]]:
    """
    Return (adjusted_calls, notes).

    Each call in `adjusted_calls` carries the *phenotypic* phenotype after
    accounting for any inhibitors among `medications`. The original
    genotypic call is preserved in `raw_calls["_genotypic_phenotype"]`.
    """
    if not medications:
        return list(star_calls), []

    norm_meds = [_normalize_drug(m) for m in medications if m]
    notes: list[str] = []
    adjusted: list[StarAlleleCall] = []

    for call in star_calls:
        table = CYP_INHIBITORS.get(call.gene)
        if not table or call.activity_score is None:
            adjusted.append(call)
            continue

        # Take the strongest inhibitor present in the medication list.
        strongest_factor = 1.0
        hit_drug: str | None = None
        for med in norm_meds:
            factor = table.get(med)
            if factor is not None and factor < strongest_factor:
                strongest_factor = factor
                hit_drug = med

        if strongest_factor == 1.0:
            adjusted.append(call)
            continue

        new_score = call.activity_score * strongest_factor
        new_pheno = score_to_phenotype(call.gene, new_score)
        if new_pheno == call.phenotype:
            adjusted.append(call)
            continue

        # Carry over with phenoconversion
        new_raw = dict(call.raw_calls)
        new_raw["_genotypic_phenotype"] = call.phenotype.value
        new_raw["_inhibitor"] = hit_drug or "unknown"
        new_raw["_inhibitor_factor"] = str(strongest_factor)

        adjusted.append(StarAlleleCall(
            gene=call.gene,
            diplotype=call.diplotype,
            activity_score=round(new_score, 3),
            phenotype=new_pheno,
            callers_agreed=call.callers_agreed,
            confidence=max(0.5, call.confidence - 0.1),
            evidence_tier=call.evidence_tier,
            raw_calls=new_raw,
        ))
        notes.append(
            f"{call.gene}: phenoconverted from {call.phenotype.value} to "
            f"{new_pheno.value} due to {hit_drug} "
            f"(inhibitor factor {strongest_factor})."
        )

    return adjusted, notes
