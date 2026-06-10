"""
engine/tracking/seed.py
======================
Synthetic biomarker tracking data generator.

Used by:
- scripts/seed_tracking_data.py (CLI wrapper) — entrypoint + ad-hoc seeding.
- engine/tracking/api.py POST /tracking/seed — UI "Load demo data" button.

Each treatment generates measurements following:
  - a per-biomarker baseline (physiologic anchor) with mild jitter
  - exponential approach to a per-patient target value
  - dose-proportional effect with diminishing returns
  - Gaussian noise
  - direction-aware sign flipping so the trend matches the panel's
    expected_direction

Trends are intentionally simple — the goal is recognisable shapes in the
charts and a clean dose-response signal, not clinical accuracy.
"""
from __future__ import annotations

import math
import random
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

from engine.peptides import get_biomarker_panel
from engine.peptides.biomarkers import BiomarkerMeasurement

from . import service
from .genetics import (
    generate_synthetic_profile,
    responder_strength_from_profile,
)


# ── Baselines + effect knobs ────────────────────────────────────────────────

@dataclass(frozen=True)
class Params:
    baseline: float           # rough physiologic baseline
    max_pct_change: float     # asymptotic effect at max dose ("hot" responder)
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


def _baseline_for(b: BiomarkerMeasurement) -> Params:
    """Look up explicit params, or pick a sane default by direction."""
    if b.name in BIOMARKER_PARAMS:
        return BIOMARKER_PARAMS[b.name]
    direction_default = {
        "increase":   Params(100.0,  0.30, 0.10, 4.0),
        "decrease":   Params(100.0, -0.25, 0.10, 4.0),
        "biphasic":   Params(100.0,  0.20, 0.10, 4.0),
        "no_change":  Params(100.0,  0.00, 0.10, 4.0),
        "variable":   Params(100.0,  0.15, 0.15, 4.0),
    }
    return direction_default.get(b.direction, Params(100.0, 0.20, 0.10, 4.0))


# ── Treatment scenarios ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Scenario:
    peptide: str
    doses: tuple[float, ...]
    dose_unit: str
    schedule: str
    route: str
    sample_weeks: tuple[float, ...] = (0.0, 2.0, 4.0, 8.0, 12.0, 20.0)


SCENARIOS: list[Scenario] = [
    Scenario("CJC-1295",        (1.0, 2.0, 4.0),   "mg",  "weekly", "SC"),
    Scenario("BPC-157",         (250.0, 500.0),    "mcg", "BID",    "SC",
             sample_weeks=(0.0, 1.0, 2.0, 4.0, 8.0, 12.0)),
    Scenario("MOTS-c",          (10.0, 15.0, 20.0), "mg", "weekly", "SC",
             sample_weeks=(0.0, 4.0, 8.0, 12.0, 24.0)),
    Scenario("GHK-Cu",          (3.0,),            "%",   "topical daily", "topical",
             sample_weeks=(0.0, 4.0, 8.0, 12.0, 16.0)),
    Scenario("Thymosin Alpha-1", (1.6, 3.2),       "mg",  "2x/week", "SC",
             sample_weeks=(0.0, 2.0, 4.0, 8.0, 12.0)),
    Scenario("AOD-9604",        (0.3, 0.5),        "mg",  "daily",  "SC",
             sample_weeks=(0.0, 4.0, 8.0, 16.0, 24.0)),
]


# ── Trajectory math ─────────────────────────────────────────────────────────

def _dose_factor(dose: float, doses: tuple[float, ...]) -> float:
    """Scale ~0.45..1.2 across the dose range, diminishing returns."""
    if not doses:
        return 1.0
    lo, hi = min(doses), max(doses)
    if hi == lo:
        return 1.0
    z = (dose - lo) / (hi - lo)
    return 0.45 + 0.75 * math.sqrt(z)


def _generate_value(
    *,
    params: Params,
    weeks_since_start: float,
    responder_strength: float,
    dose_factor: float,
    rng: random.Random,
) -> float:
    target_pct = params.max_pct_change * responder_strength * dose_factor
    approach = 1 - math.exp(-max(weeks_since_start, 0) / params.tau_weeks)
    expected = params.baseline * (1 + target_pct * approach)
    noise = rng.gauss(0, abs(expected) * params.noise_pct)
    return max(expected + noise, 0.0) if params.baseline >= 0 else expected + noise


PATIENT_DEMOGRAPHICS = [
    ("M", 1976), ("F", 1981), ("M", 1988), ("F", 1972), ("M", 1995),
    ("F", 1990), ("M", 1968), ("F", 1985), ("M", 1979), ("F", 1992),
    ("M", 1984), ("F", 1977),
]


# ── Public entry points ─────────────────────────────────────────────────────

def seed(
    conn: sqlite3.Connection,
    *,
    rng: random.Random | None = None,
    n_patients: int = 12,
    today: datetime | None = None,
    force: bool = False,
) -> dict[str, int]:
    """Populate the tracking DB with synthetic data.

    Idempotent: if patients already exist and ``force`` is False, returns
    ``{"skipped": <existing_count>, ...}`` without touching the DB.

    With ``force=True``, all existing patients (and their cascade-deleted
    treatments + measurements) are removed before reseeding.
    """
    rng = rng or random.Random(42)
    today = today or datetime.now()
    stats = {"patients": 0, "treatments": 0, "measurements": 0, "skipped": 0}

    existing = conn.execute("SELECT COUNT(*) AS n FROM patients").fetchone()["n"]
    if existing and not force:
        stats["skipped"] = existing
        return stats
    if existing and force:
        # FK cascade removes treatments + measurements.
        conn.execute("DELETE FROM patients")
        conn.commit()

    patients = []
    profiles: dict[str, "GeneticProfile"] = {}  # noqa: F821 — forward use only
    for i in range(n_patients):
        sex, byr = PATIENT_DEMOGRAPHICS[i % len(PATIENT_DEMOGRAPHICS)]
        if i >= len(PATIENT_DEMOGRAPHICS):
            byr += rng.randint(-3, 3)
        p = service.create_patient(
            conn,
            # "DEMO-" prefix makes synthetic data unmistakable so it can never
            # be confused with a real patient in any list or report.
            label=f"DEMO-{i + 1:03d}",
            sex=sex,
            birth_year=byr,
            notes=f"DEMO / synthetic patient #{i + 1} — not a real patient",
        )
        patients.append(p)
        stats["patients"] += 1

        # Each patient gets a synthetic genetic profile. The aggregate
        # variant weight for a peptide drives their responder_strength on
        # that peptide — so the Bayesian prior derived from genetics will
        # genuinely predict the observed response.
        profile = generate_synthetic_profile(rng)
        profiles[p.id] = profile
        service.set_genetic_profile(conn, p.id, profile.to_json(),
                                    source="synthetic")

    for p in patients:
        n_treatments = 1 if rng.random() < 0.55 else 2
        chosen = rng.sample(SCENARIOS, k=min(n_treatments, len(SCENARIOS)))
        for k, scenario in enumerate(chosen):
            dose = rng.choice(scenario.doses)
            days_ago = rng.randint(60, 180) - 14 * k
            start_dt = today - timedelta(days=days_ago)
            treatment = service.create_treatment(
                conn,
                patient_id=p.id,
                peptide_name=scenario.peptide,
                start_date=start_dt.date().isoformat(),
                dose=dose,
                dose_unit=scenario.dose_unit,
                schedule=scenario.schedule,
                route=scenario.route,
            )
            stats["treatments"] += 1

            panel = get_biomarker_panel(scenario.peptide)
            if panel is None:
                continue

            # Per-peptide responder strength: derived from the patient's
            # genetic profile (so the priors are predictive), with a small
            # random jitter to reflect non-genetic variance.
            profile = profiles[p.id]
            genetic_strength = responder_strength_from_profile(profile, scenario.peptide)
            responder = max(0.0, genetic_strength * rng.gauss(1.0, 0.18))
            dose_f = _dose_factor(dose, scenario.doses)
            n_markers = min(len(panel.measurements), rng.randint(4, 6))
            markers = rng.sample(list(panel.measurements), k=n_markers)

            for marker in markers:
                params = _baseline_for(marker)
                if marker.direction == "decrease" and params.max_pct_change > 0:
                    params = Params(params.baseline, -abs(params.max_pct_change),
                                    params.noise_pct, params.tau_weeks)
                elif marker.direction == "no_change":
                    params = Params(params.baseline, 0.0, params.noise_pct,
                                    params.tau_weeks)
                jitter = 1 + rng.uniform(-0.10, 0.10)
                params = Params(params.baseline * jitter,
                                params.max_pct_change,
                                params.noise_pct,
                                params.tau_weeks)

                for w in scenario.sample_weeks:
                    elapsed_weeks = (today - start_dt).days / 7
                    if w > elapsed_weeks + 0.5:
                        continue
                    measured_at = (start_dt + timedelta(weeks=w)).date().isoformat()
                    val = _generate_value(
                        params=params,
                        weeks_since_start=w,
                        responder_strength=responder,
                        dose_factor=dose_f,
                        rng=rng,
                    )
                    service.create_measurement(
                        conn,
                        patient_id=p.id,
                        treatment_id=treatment.id,
                        biomarker_name=marker.name,
                        modality=marker.modality,
                        value=round(val, 3),
                        unit=marker.unit or None,
                        measured_at=measured_at,
                    )
                    stats["measurements"] += 1

    return stats
