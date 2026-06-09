#!/usr/bin/env python3
"""
scripts/seed_tracking_data.py
=============================
Populate the biomarker tracking DB with synthetic patients, treatments, and
longitudinal measurements so the UI and cohort analysis have something to
render.

Usage:
    nix develop --command python scripts/seed_tracking_data.py
    nix develop --command python scripts/seed_tracking_data.py --reset
    nix develop --command python scripts/seed_tracking_data.py --db /tmp/x.db --seed 7

Each treatment is generated with:
  - a baseline value for the biomarker (physiologic anchor)
  - an exponential approach to a per-patient target ("responder spectrum")
  - Gaussian measurement noise
  - dose-proportional effect amplification (with diminishing returns)

The shape is intentionally simple — the goal is recognisable trends in the
charts and a dose-response signal in the cohort view, not clinical accuracy.
"""
from __future__ import annotations

import argparse
import math
import os
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.tracking import db, get_conn, service  # noqa: E402
from engine.peptides import get_biomarker_panel  # noqa: E402
from engine.peptides.biomarkers import BiomarkerMeasurement  # noqa: E402


# ── Baselines + effect knobs ────────────────────────────────────────────────
# Keys are biomarker names exactly as they appear in
# engine/peptides/measurements.py. Anything not listed gets a generic default
# in _baseline_for() so seeding never crashes when a panel evolves.

@dataclass(frozen=True)
class Params:
    baseline: float           # rough physiologic baseline
    max_pct_change: float     # asymptotic effect at max dose ("hot" responder)
    noise_pct: float          # gaussian noise as fraction of current value
    tau_weeks: float          # time constant for the exponential approach

BIOMARKER_PARAMS: dict[str, Params] = {
    # CJC-1295 / Ipamorelin / GHRP-2 / MGF — GH axis
    "Serum IGF-1":              Params(180.0, 0.55, 0.06, 3.0),
    "Serum IGFBP-3":            Params(4.0,   0.40, 0.06, 3.5),
    "GH peak":                  Params(2.0,   1.50, 0.20, 0.5),
    "GH AUC":                   Params(8.0,   1.30, 0.20, 0.5),
    "IGF-1 vs age-adjusted reference": Params(0.0, 0.30, 0.10, 4.0),
    "Lean body mass (DXA)":     Params(62.0,  0.05, 0.02, 8.0),
    "Body weight":              Params(78.0,  0.04, 0.015, 4.0),
    "Grip strength":            Params(38.0,  0.10, 0.05, 6.0),

    # BPC-157 / TB-500 / Thymosin Beta-4 — repair
    "Serum VEGF":               Params(110.0, 0.45, 0.10, 2.0),
    "Plasma nitrite/nitrate (NOx)": Params(35.0, 0.50, 0.10, 1.5),
    "Pain VAS":                 Params(6.0,  -0.65, 0.10, 3.0),     # negative → decrease
    "Joint range of motion":    Params(110.0, 0.18, 0.05, 4.0),
    "Tendon thickness (ultrasound)": Params(4.5, 0.15, 0.08, 6.0),
    "Wound closure area":       Params(20.0,  3.50, 0.10, 2.0),     # % closure rises rapidly
    "Dermal wound closure":     Params(15.0,  4.00, 0.10, 2.0),
    "Wound area (absolute)":    Params(1800.0, -0.80, 0.10, 3.0),
    "Wound area closure":       Params(15.0,  4.00, 0.10, 2.5),

    # MOTS-c / AOD-9604 — metabolic
    "HOMA-IR":                  Params(3.4,  -0.45, 0.10, 4.0),
    "Fasting glucose":          Params(102.0, -0.10, 0.04, 4.0),
    "HbA1c":                    Params(5.9,  -0.05, 0.02, 12.0),
    "VO2max":                   Params(34.0,  0.12, 0.06, 6.0),
    "% body fat (DXA)":         Params(30.0, -0.12, 0.04, 8.0),
    "Waist circumference":      Params(96.0, -0.05, 0.02, 8.0),
    "Serum leptin":             Params(18.0, -0.30, 0.10, 6.0),

    # GHK-Cu — skin
    "Wrinkle depth (imaging)":  Params(40.0, -0.25, 0.06, 6.0),
    "Skin thickness (ultrasound)": Params(1.4, 0.15, 0.05, 6.0),
    "Hair density (trichoscopy)": Params(180.0, 0.20, 0.06, 12.0),

    # Thymosin Alpha-1 — immune
    "CD4/CD8 ratio":            Params(0.9, 0.60, 0.10, 4.0),
    "Absolute CD4+ T-lymphocyte count": Params(380.0, 0.55, 0.08, 4.0),

    # Inflammation cytokines (most peptides)
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

    # Selectivity markers
    "Serum cortisol":           Params(14.0, 0.0,  0.08, 4.0),   # flat for ipamorelin selectivity
    "Serum prolactin":          Params(8.0,  0.0,  0.10, 4.0),
    "WADA hGH isoform immunoassay": Params(1.0, 0.0, 0.02, 4.0),
}


def _baseline_for(b: BiomarkerMeasurement) -> Params:
    """Look up explicit params, or pick a sane default by direction."""
    if b.name in BIOMARKER_PARAMS:
        return BIOMARKER_PARAMS[b.name]
    # Default by expected direction so the trends still go the right way.
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
    """One canonical treatment to assign to several patients."""
    peptide: str
    doses: tuple[float, ...]      # different patients get different doses
    dose_unit: str
    schedule: str
    route: str
    # which biomarkers from the panel to sample, and on what week schedule
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
    """Scale 0.4..1.2 across the dose range, with diminishing returns."""
    if not doses:
        return 1.0
    lo, hi = min(doses), max(doses)
    if hi == lo:
        return 1.0
    z = (dose - lo) / (hi - lo)              # 0..1
    return 0.45 + 0.75 * math.sqrt(z)        # diminishing returns


def _generate_value(
    *,
    params: Params,
    weeks_since_start: float,
    responder_strength: float,   # 0..1.4 per-patient multiplier
    dose_factor: float,
    rng: random.Random,
) -> float:
    """Exponential approach: baseline → baseline*(1 + effect*responder*dose)."""
    target_pct = params.max_pct_change * responder_strength * dose_factor
    approach = 1 - math.exp(-max(weeks_since_start, 0) / params.tau_weeks)
    expected = params.baseline * (1 + target_pct * approach)
    noise = rng.gauss(0, abs(expected) * params.noise_pct)
    return max(expected + noise, 0.0) if params.baseline >= 0 else expected + noise


# ── Seeding ────────────────────────────────────────────────────────────────

PATIENT_DEMOGRAPHICS = [
    ("M", 1976), ("F", 1981), ("M", 1988), ("F", 1972), ("M", 1995),
    ("F", 1990), ("M", 1968), ("F", 1985), ("M", 1979), ("F", 1992),
    ("M", 1984), ("F", 1977),
]


def seed(conn, *, rng: random.Random, n_patients: int = 12,
         today: datetime | None = None,
         force: bool = False) -> dict[str, int]:
    today = today or datetime.now()
    stats = {"patients": 0, "treatments": 0, "measurements": 0, "skipped": 0}

    # Idempotency: skip if the DB already has patients. Lets the same script
    # run on every container start without wiping existing data.
    existing = conn.execute("SELECT COUNT(*) AS n FROM patients").fetchone()["n"]
    if existing and not force:
        stats["skipped"] = existing
        return stats
    if existing and force:
        # FK cascade clears treatments + measurements when patients are removed.
        conn.execute("DELETE FROM patients")
        conn.commit()

    patients = []
    for i in range(n_patients):
        sex, byr = PATIENT_DEMOGRAPHICS[i % len(PATIENT_DEMOGRAPHICS)]
        # Slight jitter so the first 12 aren't always identical demographics
        if i >= len(PATIENT_DEMOGRAPHICS):
            byr += rng.randint(-3, 3)
        p = service.create_patient(
            conn,
            label=f"P-{i + 1:03d}",
            sex=sex,
            birth_year=byr,
            notes=f"Synthetic patient #{i + 1}",
        )
        patients.append(p)
        stats["patients"] += 1

    # Round-robin assign 1-2 scenarios per patient, with varied start dates.
    for idx, p in enumerate(patients):
        n_treatments = 1 if rng.random() < 0.55 else 2
        chosen = rng.sample(SCENARIOS, k=min(n_treatments, len(SCENARIOS)))
        for k, scenario in enumerate(chosen):
            dose = rng.choice(scenario.doses)
            # Stagger start dates over the past ~6 months
            days_ago = rng.randint(60, 180) - 14 * k
            start_dt = today - timedelta(days=days_ago)
            start_iso = start_dt.date().isoformat()
            treatment = service.create_treatment(
                conn,
                patient_id=p.id,
                peptide_name=scenario.peptide,
                start_date=start_iso,
                dose=dose,
                dose_unit=scenario.dose_unit,
                schedule=scenario.schedule,
                route=scenario.route,
            )
            stats["treatments"] += 1

            panel = get_biomarker_panel(scenario.peptide)
            if panel is None:
                continue

            # Per-patient responder strength: a fat-tailed split so some
            # patients respond strongly, some weakly, a few not at all.
            responder = max(0.0, rng.gauss(0.85, 0.35))
            dose_f = _dose_factor(dose, scenario.doses)

            # Sample a subset of the panel — every patient gets 4-6 biomarkers
            # so the per-patient detail page has multiple charts.
            n_markers = min(len(panel.measurements), rng.randint(4, 6))
            markers = rng.sample(list(panel.measurements), k=n_markers)

            for marker in markers:
                params = _baseline_for(marker)
                # Direction-aware sign: if expected direction is "decrease"
                # but the params have a positive max_pct_change, flip the sign.
                if marker.direction == "decrease" and params.max_pct_change > 0:
                    params = Params(params.baseline, -abs(params.max_pct_change),
                                    params.noise_pct, params.tau_weeks)
                elif marker.direction == "no_change":
                    params = Params(params.baseline, 0.0, params.noise_pct,
                                    params.tau_weeks)

                # Per-marker baseline jitter so patients aren't identical
                jitter = 1 + rng.uniform(-0.10, 0.10)
                params = Params(params.baseline * jitter,
                                params.max_pct_change,
                                params.noise_pct,
                                params.tau_weeks)

                for w in scenario.sample_weeks:
                    # Skip future timepoints (treatment hasn't been running that long)
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


# ── CLI ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=None,
                        help="Path to tracking DB (default: data/biomarker_tracking.db)")
    parser.add_argument("--reset", action="store_true",
                        help="Delete the existing DB file before seeding.")
    parser.add_argument("--seed", type=int, default=42,
                        help="RNG seed for reproducible data.")
    parser.add_argument("--patients", type=int, default=12,
                        help="Number of patients to create (default 12).")
    parser.add_argument("--force", action="store_true",
                        help="Seed even if patients already exist (default: skip).")
    args = parser.parse_args()

    target = Path(args.db or os.getenv("TRACKING_DB_PATH")
                  or "data/biomarker_tracking.db")

    if args.reset and target.exists():
        target.unlink()
        for suffix in ("-shm", "-wal"):
            sidecar = target.with_name(target.name + suffix)
            if sidecar.exists():
                sidecar.unlink()
        print(f"removed existing {target}")

    db.reset_initialized()
    conn = get_conn(str(target))
    rng = random.Random(args.seed)
    stats = seed(conn, rng=rng, n_patients=args.patients, force=args.force)
    conn.close()

    if stats["skipped"]:
        print(f"tracking DB already has {stats['skipped']} patient(s) — "
              f"skipping seed ({target}). Pass --force to override.")
    else:
        print(f"seeded {stats['patients']} patients, "
              f"{stats['treatments']} treatments, "
              f"{stats['measurements']} measurements → {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
