"""
engine/pgx/cpic/recommendations.py
====================================
CPIC drug-recommendation generator.

The table is a curated subset of CPIC Level-A guidelines covering the
highest-impact gene-drug pairs. Each entry maps (gene, phenotype) → action.

For full coverage in production, run scripts/refresh_cpic.py to mirror the
public CPIC API into data/cpic_snapshot.db and replace REC_TABLE with a
SQLite lookup.

References:
  - Caudle et al. 2025, CPT 118(6) — global CPIC adoption review
  - Manson et al. 2024, EJHG 32(8) — DPWG antiepileptic guideline
"""
from __future__ import annotations

from ..types import DrugRecommendation, HLACall, Phenotype, StarAlleleCall

# (gene, phenotype) → list of (drug, classification, recommendation, guideline_id)
REC_TABLE: dict[tuple[str, Phenotype], list[tuple[str, str, str, str]]] = {
    # CYP2C19 — clopidogrel, voriconazole, PPIs, SSRIs
    ("CYP2C19", Phenotype.POOR): [
        ("clopidogrel", "strong",
         "Avoid clopidogrel: consider prasugrel or ticagrelor.", "CPIC-CYP2C19-clopidogrel-2022"),
        ("voriconazole", "strong",
         "Avoid voriconazole or use therapeutic drug monitoring.", "CPIC-CYP2C19-voriconazole-2017"),
        ("citalopram", "moderate",
         "Consider 50% dose reduction; or use SSRI not metabolized by CYP2C19.", "CPIC-CYP2C19-SSRI-2023"),
    ],
    ("CYP2C19", Phenotype.INTERMEDIATE): [
        ("clopidogrel", "moderate",
         "Consider prasugrel or ticagrelor.", "CPIC-CYP2C19-clopidogrel-2022"),
        ("voriconazole", "moderate",
         "Therapeutic drug monitoring recommended.", "CPIC-CYP2C19-voriconazole-2017"),
    ],
    ("CYP2C19", Phenotype.ULTRARAPID): [
        ("voriconazole", "strong",
         "Avoid voriconazole; use isavuconazole or posaconazole.", "CPIC-CYP2C19-voriconazole-2017"),
        ("escitalopram", "moderate",
         "Consider alternative or therapeutic monitoring.", "CPIC-CYP2C19-SSRI-2023"),
    ],

    # CYP2D6 — opioids, SSRIs/SNRIs, tamoxifen, antipsychotics
    ("CYP2D6", Phenotype.POOR): [
        ("codeine",   "strong", "Avoid codeine; analgesia will be inadequate.", "CPIC-CYP2D6-opioids-2021"),
        ("tramadol",  "strong", "Avoid tramadol; analgesia will be inadequate.", "CPIC-CYP2D6-opioids-2021"),
        ("hydrocodone","moderate","Consider alternative non-CYP2D6 opioid.",   "CPIC-CYP2D6-opioids-2021"),
        ("tamoxifen", "strong", "Use aromatase inhibitor if postmenopausal.",   "CPIC-CYP2D6-tamoxifen-2018"),
        ("paroxetine","moderate","Consider 50% dose reduction or alternative.", "CPIC-CYP2D6-SSRI-2023"),
        ("nortriptyline","strong","Use 50% lower starting dose.",              "CPIC-CYP2D6-TCA-2016"),
    ],
    ("CYP2D6", Phenotype.INTERMEDIATE): [
        ("codeine",   "moderate","Use lowest effective codeine dose; monitor.", "CPIC-CYP2D6-opioids-2021"),
        ("tramadol",  "moderate","Monitor analgesic response carefully.",       "CPIC-CYP2D6-opioids-2021"),
        ("tamoxifen", "moderate","Consider aromatase inhibitor.",               "CPIC-CYP2D6-tamoxifen-2018"),
    ],
    ("CYP2D6", Phenotype.ULTRARAPID): [
        ("codeine",   "strong", "Avoid codeine: severe toxicity risk.",        "CPIC-CYP2D6-opioids-2021"),
        ("tramadol",  "strong", "Avoid tramadol: severe toxicity risk.",       "CPIC-CYP2D6-opioids-2021"),
        ("nortriptyline","strong","Avoid TCA or use alternative.",             "CPIC-CYP2D6-TCA-2016"),
    ],

    # CYP2C9 — warfarin, NSAIDs, phenytoin
    ("CYP2C9", Phenotype.POOR): [
        ("warfarin", "strong",
         "Use CYP2C9-aware dosing algorithm (IWPC) — typically 50% reduction.", "CPIC-CYP2C9-warfarin-2017"),
        ("phenytoin","strong",
         "Reduce initial dose 25–50%; therapeutic monitoring required.",        "CPIC-CYP2C9-phenytoin-2020"),
        ("celecoxib","moderate","Consider 25–50% dose reduction.",              "CPIC-CYP2C9-NSAID-2020"),
    ],
    ("CYP2C9", Phenotype.INTERMEDIATE): [
        ("warfarin", "moderate","Use CYP2C9-aware dosing algorithm.",          "CPIC-CYP2C9-warfarin-2017"),
        ("phenytoin","moderate","Consider 25% reduction; monitor.",            "CPIC-CYP2C9-phenytoin-2020"),
    ],

    # TPMT / NUDT15 — thiopurines
    ("TPMT", Phenotype.POOR): [
        ("azathioprine",   "strong", "Avoid azathioprine or use 90% reduced dose.",  "CPIC-TPMT-thiopurines-2018"),
        ("mercaptopurine", "strong", "Avoid mercaptopurine or use 90% reduction.",   "CPIC-TPMT-thiopurines-2018"),
        ("thioguanine",    "strong", "Reduce thioguanine dose 50–80%.",              "CPIC-TPMT-thiopurines-2018"),
    ],
    ("TPMT", Phenotype.INTERMEDIATE): [
        ("azathioprine",   "moderate", "Reduce dose 30–80%; monitor counts.",        "CPIC-TPMT-thiopurines-2018"),
        ("mercaptopurine", "moderate", "Reduce dose 30–80%; monitor counts.",        "CPIC-TPMT-thiopurines-2018"),
    ],
    ("NUDT15", Phenotype.POOR): [
        ("mercaptopurine", "strong", "Use 90% reduced dose or avoid.",                "CPIC-NUDT15-thiopurines-2018"),
    ],
    ("NUDT15", Phenotype.INTERMEDIATE): [
        ("mercaptopurine", "moderate","Reduce dose 30–80%; monitor counts.",          "CPIC-NUDT15-thiopurines-2018"),
    ],

    # DPYD — fluoropyrimidines (fluorouracil, capecitabine)
    ("DPYD", Phenotype.POOR): [
        ("fluorouracil","strong","Avoid fluoropyrimidines or use ≤25% dose.",        "CPIC-DPYD-fluoropyrimidines-2024"),
        ("capecitabine","strong","Avoid or use 25% dose.",                            "CPIC-DPYD-fluoropyrimidines-2024"),
    ],
    ("DPYD", Phenotype.INTERMEDIATE): [
        ("fluorouracil","strong","Reduce starting dose 50%; titrate.",                "CPIC-DPYD-fluoropyrimidines-2024"),
        ("capecitabine","strong","Reduce starting dose 50%.",                         "CPIC-DPYD-fluoropyrimidines-2024"),
    ],

    # SLCO1B1 — simvastatin myopathy
    ("SLCO1B1", Phenotype.POOR): [
        ("simvastatin","strong","Avoid simvastatin >20 mg; consider alternative.",    "CPIC-SLCO1B1-statins-2022"),
        ("atorvastatin","moderate","Limit to 40 mg if used.",                          "CPIC-SLCO1B1-statins-2022"),
    ],
    ("SLCO1B1", Phenotype.INTERMEDIATE): [
        ("simvastatin","moderate","Prefer alternative statin or limit dose.",          "CPIC-SLCO1B1-statins-2022"),
    ],

    # UGT1A1 — atazanavir, irinotecan
    ("UGT1A1", Phenotype.POOR): [
        ("atazanavir","moderate","Consider alternative ARV regimen.",                 "CPIC-UGT1A1-atazanavir-2015"),
        ("irinotecan","moderate","Reduce starting dose; monitor for neutropenia.",    "FDA-UGT1A1-irinotecan"),
    ],
}


# HLA → drug contraindications (highest-OR / most preventable type-B ADRs)
HLA_DRUG_RULES: dict[str, list[tuple[str, str, str]]] = {
    "HLA-B*57:01": [
        ("abacavir",       "strong", "Avoid abacavir: hypersensitivity syndrome risk."),
        ("flucloxacillin", "moderate","Heightened DILI risk; monitor LFTs."),
    ],
    "HLA-B*15:02": [
        ("carbamazepine",  "strong", "Avoid carbamazepine: SJS/TEN risk."),
        ("oxcarbazepine",  "strong", "Avoid oxcarbazepine: SJS/TEN risk."),
        ("phenytoin",      "moderate","Avoid or use with caution."),
        ("lamotrigine",    "moderate","Caution; monitor for rash."),
    ],
    "HLA-B*58:01": [
        ("allopurinol",    "strong", "Avoid allopurinol: SJS/TEN/DRESS risk."),
    ],
    "HLA-A*31:01": [
        ("carbamazepine",  "moderate","Avoid: DRESS risk."),
    ],
    "HLA-B*13:01": [
        ("dapsone",        "strong", "Avoid dapsone: severe cutaneous reaction risk."),
    ],
}


def generate_recommendations(
    star_calls: list[StarAlleleCall],
    hla_calls: list[HLACall],
) -> list[DrugRecommendation]:
    out: list[DrugRecommendation] = []

    for call in star_calls:
        key = (call.gene, call.phenotype)
        entries = REC_TABLE.get(key)
        if not entries:
            continue
        for drug, classification, text, gid in entries:
            out.append(DrugRecommendation(
                drug=drug,
                gene=call.gene,
                phenotype=call.phenotype,
                recommendation=text,
                classification=classification,
                cpic_guideline_id=gid,
                source="CPIC",
            ))

    for hla in hla_calls:
        if not hla.present:
            continue
        for drug, classification, text in HLA_DRUG_RULES.get(hla.locus, []):
            out.append(DrugRecommendation(
                drug=drug,
                gene=hla.locus,
                phenotype=Phenotype.INDETERMINATE,
                recommendation=text,
                classification=classification,
                cpic_guideline_id=f"CPIC-{hla.locus}-{drug}",
                source="CPIC",
            ))

    return out
