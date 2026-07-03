"""
engine/tracking/biomarker_params.py
==================================
Per-biomarker effect parameters shared by the synthetic seeder and the
Bayesian prediction layer.

`Params.max_pct_change` is the asymptotic fractional change from baseline an
"average responder" is expected to show at the panel's documented timeframe.
For example, +0.55 means a healthy patient is expected to end up +55% above
baseline by the steady state; -0.05 means a 5% drop.

Sign carries the direction (positive = increase, negative = decrease).
Magnitude is the panel's documented effect size — sourced informally from
the biomarker panel literature; not a tight clinical claim.

Why this lives in its own module
--------------------------------
- seed.py uses it to simulate measurements
- analysis.predict_response uses it to scale the Bayesian prior to the
  right magnitude per biomarker
- pulling it into a shared module avoids a circular import (analysis ->
  seed) and makes the "panel ground truth" easy to update in one place
"""
from __future__ import annotations

from dataclasses import dataclass

from engine.peptides.biomarkers import BiomarkerMeasurement


@dataclass(frozen=True)
class Params:
    baseline: float           # rough physiologic baseline
    max_pct_change: float     # asymptotic effect at average responder × top dose
    noise_pct: float          # gaussian noise as fraction of current value
    tau_weeks: float          # time constant for the exponential approach


BIOMARKER_PARAMS: dict[str, Params] = {
    # GH axis (CJC-1295 / Ipamorelin / GHRP-2 / MGF)
    "Serum IGF-1":              Params(180.0, 0.55, 0.06, 3.0),
    "Serum IGFBP-3":            Params(4.0,   0.40, 0.06, 3.5),
    "GH peak":                  Params(2.0,   1.50, 0.20, 0.5),
    "GH AUC":                   Params(8.0,   1.30, 0.20, 0.5),
    "IGF-1 vs age-adjusted reference": Params(0.0, 0.30, 0.10, 4.0),
    "Lean body mass (DXA)":     Params(62.0,  0.05, 0.02, 8.0),
    "Body weight":              Params(78.0,  0.04, 0.015, 4.0),
    "Grip strength":            Params(38.0,  0.10, 0.05, 6.0),

    # Repair (BPC-157 / TB-500 / Thymosin Beta-4)
    "Serum VEGF":               Params(110.0, 0.45, 0.10, 2.0),
    "Plasma nitrite/nitrate (NOx)": Params(35.0, 0.50, 0.10, 1.5),
    "Pain VAS":                 Params(6.0,  -0.65, 0.10, 3.0),
    "Joint range of motion":    Params(110.0, 0.18, 0.05, 4.0),
    "Tendon thickness (ultrasound)": Params(4.5, 0.15, 0.08, 6.0),
    "Wound closure area":       Params(20.0,  3.50, 0.10, 2.0),
    "Dermal wound closure":     Params(15.0,  4.00, 0.10, 2.0),
    "Wound area (absolute)":    Params(1800.0, -0.80, 0.10, 3.0),
    "Wound area closure":       Params(15.0,  4.00, 0.10, 2.5),

    # Metabolic (MOTS-c / AOD-9604)
    "HOMA-IR":                  Params(3.4,  -0.45, 0.10, 4.0),
    "Fasting glucose":          Params(102.0, -0.10, 0.04, 4.0),
    "HbA1c":                    Params(5.9,  -0.05, 0.02, 12.0),
    "VO2max":                   Params(34.0,  0.12, 0.06, 6.0),
    "% body fat (DXA)":         Params(30.0, -0.12, 0.04, 8.0),
    "Waist circumference":      Params(96.0, -0.05, 0.02, 8.0),
    "Serum leptin":             Params(18.0, -0.30, 0.10, 6.0),

    # GLP-1 / incretin class (Semaglutide / Tirzepatide / Liraglutide).
    # Class-qualified marker names carry GLP-1-magnitude effects so they do NOT
    # overwrite the much smaller generic "Body weight" / "HbA1c" markers above
    # (which are tuned for AOD-9604 / MOTS-c). Magnitudes are a class-level
    # approximation across the three agents (e.g. weight loss ranges ~8% for
    # liraglutide to ~21% for tirzepatide; ~13% is a representative class mean).
    "Body weight (GLP-1 RA)":        Params(95.0, -0.13, 0.02, 8.0),
    "Waist circumference (GLP-1 RA)": Params(110.0, -0.09, 0.02, 8.0),
    "HbA1c (GLP-1 RA)":              Params(7.8,  -0.18, 0.02, 12.0),
    "HOMA-IR (GLP-1 RA)":            Params(4.0,  -0.40, 0.08, 6.0),
    "Fasting plasma glucose":        Params(160.0, -0.22, 0.05, 6.0),
    "Serum lipase":                  Params(30.0,  0.0,  0.10, 4.0),
    "Resting heart rate":            Params(72.0,  0.04, 0.03, 4.0),

    # Skin (GHK-Cu)
    "Wrinkle depth (imaging)":  Params(40.0, -0.25, 0.06, 6.0),
    "Skin thickness (ultrasound)": Params(1.4, 0.15, 0.05, 6.0),
    "Hair density (trichoscopy)": Params(180.0, 0.20, 0.06, 12.0),

    # Immune (Thymosin Alpha-1)
    "CD4/CD8 ratio":            Params(0.9, 0.60, 0.10, 4.0),
    "Absolute CD4+ T-lymphocyte count": Params(380.0, 0.55, 0.08, 4.0),

    # Inflammation cytokines
    "Serum IL-6":               Params(5.5, -0.45, 0.15, 3.0),
    "Serum TNF-alpha":          Params(7.0, -0.40, 0.15, 3.0),
    "hs-CRP":                   Params(3.2, -0.40, 0.15, 4.0),
    "Serum hs-CRP":             Params(3.2, -0.40, 0.15, 4.0),

    # Patient-reported scales
    "Hamilton Anxiety (HAM-A)": Params(22.0, -0.45, 0.10, 3.0),
    "GAD-7 score":              Params(13.0, -0.45, 0.10, 3.0),
    "MoCA":                     Params(24.0,  0.12, 0.04, 12.0),
    "MoCA score":               Params(24.0,  0.12, 0.04, 12.0),
    "NIHSS":                    Params(8.0,  -0.50, 0.10, 4.0),
    "Pittsburgh Sleep Quality Index (PSQI)": Params(11.0, -0.50, 0.10, 4.0),
    "OSDI ocular symptom score": Params(28.0, -0.45, 0.10, 4.0),
    "IIEF-5":                   Params(15.0, 0.40, 0.08, 4.0),

    # Safety markers (mostly flat)
    "ALT":                      Params(28.0, 0.0,  0.10, 4.0),
    "Serum creatinine":         Params(0.95, 0.0,  0.06, 4.0),
    "CBC with differential":    Params(7.0,  0.0,  0.08, 4.0),
    "Serum copper":             Params(95.0, 0.0,  0.05, 4.0),
    "Ceruloplasmin":            Params(28.0, 0.0,  0.05, 4.0),
    "Serum lactate":            Params(1.6,  0.0,  0.08, 4.0),
    "PSA":                      Params(1.1,  0.0,  0.10, 8.0),
    "Blood pressure":           Params(124.0, 0.0, 0.04, 4.0),
    "Blood pressure / heart rate": Params(124.0, 0.0, 0.04, 4.0),

    # Selectivity (flat by design)
    "Serum cortisol":           Params(14.0, 0.0,  0.08, 4.0),
    "Serum prolactin":          Params(8.0,  0.0,  0.10, 4.0),
    "WADA hGH isoform immunoassay": Params(1.0, 0.0, 0.02, 4.0),
}


# Default magnitude assumed when no explicit Params row is available.
# Sign is taken from the panel's direction field.
_DIRECTION_DEFAULT_MAGNITUDE: dict[str, float] = {
    "increase":  0.25,
    "decrease": -0.25,
    "biphasic":  0.15,
    "no_change": 0.0,
    "variable":  0.20,
}


def params_for(b: BiomarkerMeasurement | None,
               biomarker_name: str | None = None) -> Params:
    """Return the seeder/analysis Params for one biomarker.

    Priority: explicit name lookup -> panel-direction fallback -> generic.
    """
    name = (biomarker_name or (b.name if b else "")).strip()
    if name in BIOMARKER_PARAMS:
        return BIOMARKER_PARAMS[name]
    if b is not None:
        mag = _DIRECTION_DEFAULT_MAGNITUDE.get(b.direction, 0.20)
        return Params(baseline=100.0, max_pct_change=mag, noise_pct=0.10, tau_weeks=4.0)
    return Params(baseline=100.0, max_pct_change=0.20, noise_pct=0.10, tau_weeks=4.0)


def expected_pct_change(b: BiomarkerMeasurement | None,
                        biomarker_name: str | None = None) -> float:
    """The asymptotic fractional change an average responder is expected to
    show on this biomarker (sign included). Used as the per-biomarker scale
    for the Bayesian prior.

    If the panel marker tells us the direction explicitly, we honour it
    here so the seeder and the analyzer agree on sign — otherwise a row
    like Body weight (+0.04 in BIOMARKER_PARAMS) would predict weight gain
    on AOD-9604 even though the panel direction is `decrease`.
    """
    mag = params_for(b, biomarker_name).max_pct_change
    if b is not None:
        if b.direction == "decrease" and mag > 0:
            mag = -abs(mag)
        elif b.direction == "increase" and mag < 0:
            mag = abs(mag)
        elif b.direction == "no_change":
            mag = 0.0
    return mag
