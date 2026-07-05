"""
engine/tracking/healthkit_bridge.py
===================================
Map de-identified HealthKit *proxy* samples onto panel biomarkers so they feed
the existing Bayesian likelihood as extra observations of θ.

Role (per ``docs/models/peptide-response-model.md`` §4)
------------------------------------------------------
HealthKit signals split by role. This module handles **proxy observations**
only: HealthKit quantities that *are* a tracked biomarker (body mass → weight,
resting heart rate → resting HR). They enter as additional likelihood
observations ``y_i`` on θ — they update the posterior, they do **not** touch the
prior. Behavioural covariates (sleep, activity) that modulate *responsiveness*
are a separate role (feature adapters on the prior) and are out of scope here.

Honesty contract
----------------
Wearable proxies are noisier observations, not ground truth:

* **Daily-median aggregation.** Raw HealthKit streams are autocorrelated
  (many samples per day, minutes apart) and would inflate precision if each
  were treated as an independent observation of θ. We collapse each proxy type
  to one value per calendar day (median) before emitting observations.
* **Wearable-grade noise.** Emitted observations carry a per-observation noise
  *scale* > 1 (``WEARABLE_NOISE_SCALE``) so the joint fit down-weights them
  relative to clinical labs. They inform but do not swamp lab measurements.
* **Correct unit conversion.** Body mass is normalised to kilograms from
  whatever unit the sample carries (kg / g / lb / oz / st); an unrecognised
  unit is skipped rather than guessed.

Design is table-driven (``PROXY_MAP``): only HealthKit types with a clear panel
counterpart are included, and more can be added by extending the table.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import UTC, datetime

from engine.peptides import get_biomarker_panel

from .healthkit_identity import resolve_subject_id

# Wearable observations are treated as this many times noisier (in σ) than a
# clinical lab of the same biomarker. A scale of 2.5 means a single wearable
# day-median carries ~1/6 (1/2.5²) of the information of one clinical value —
# enough to inform the posterior, not enough to swamp a lab draw. The joint
# fit consumes this as a per-observation weight ``w_i = 1/scale²``.
WEARABLE_NOISE_SCALE = 2.5

_GLP1_SUFFIX = "(GLP-1 RA)"

# Mass-unit → kilograms. HealthKit reports body mass in one of these units
# depending on the user's locale / source device.
_MASS_TO_KG: dict[str, float] = {
    "kg": 1.0,
    "g": 0.001,
    "lb": 0.45359237,
    "lbs": 0.45359237,
    "oz": 0.028349523125,
    "st": 6.35029318,
}


@dataclass(frozen=True)
class ProxyType:
    """One HealthKit proxy → panel-biomarker mapping.

    ``base_name`` is the generic panel marker; ``glp1_name`` (when set) is the
    class-qualified marker used for GLP-1 receptor agonists so a GLP-1 proxy
    does not bleed onto the much smaller generic marker. ``kind`` selects the
    unit-conversion path. ``noise_scale`` is the wearable noise multiplier.
    """
    hk_type: str
    base_name: str
    kind: str                       # 'mass' | 'rate'
    glp1_name: str | None = None
    noise_scale: float = WEARABLE_NOISE_SCALE


# Only types with a clear, direct panel counterpart. Extend deliberately.
PROXY_MAP: dict[str, ProxyType] = {
    "HKQuantityTypeIdentifierBodyMass": ProxyType(
        hk_type="HKQuantityTypeIdentifierBodyMass",
        base_name="Body weight",
        kind="mass",
        glp1_name=f"Body weight {_GLP1_SUFFIX}",
    ),
    "HKQuantityTypeIdentifierRestingHeartRate": ProxyType(
        hk_type="HKQuantityTypeIdentifierRestingHeartRate",
        base_name="Resting heart rate",
        kind="rate",
    ),
}


@dataclass(frozen=True)
class ProxyBinding:
    """A resolved proxy for one (peptide, biomarker): which HealthKit type to
    read and the noise scale its observations carry."""
    proxy: ProxyType
    biomarker_name: str             # the panel name the observations bind to
    noise_scale: float


# ── Helpers ─────────────────────────────────────────────────────────────────

def _parse_dt(value: str | None) -> datetime | None:
    """Accept 'YYYY-MM-DD' or an ISO-8601 datetime (with optional trailing Z)."""
    if not value:
        return None
    try:
        if "T" in value:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _as_utc_naive(dt: datetime) -> datetime:
    """Represent an aware datetime as its UTC wall-clock, tz stripped; a naive
    datetime is assumed to already be UTC. Lets us subtract mixed inputs
    without silently discarding a real offset."""
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def _weeks_between(start: str | None, end: str | None) -> float | None:
    a, b = _parse_dt(start), _parse_dt(end)
    if a is None or b is None:
        return None
    # Normalise both to UTC-naive so the delta is a true elapsed time even when
    # one side is naive (e.g. a 'YYYY-MM-DD' treatment start) and the other
    # carries an offset — converting to UTC rather than dropping the offset.
    return (_as_utc_naive(b) - _as_utc_naive(a)).total_seconds() / (7 * 86400)


def _is_glp1(peptide_name: str) -> bool:
    """A peptide is GLP-1-class iff its panel carries a class-qualified
    '(GLP-1 RA)' marker. Data-driven so it stays correct as the panel grows."""
    panel = get_biomarker_panel(peptide_name)
    if panel is None:
        return False
    return any(m.name.strip().endswith(_GLP1_SUFFIX) for m in panel.measurements)


def _canonical_value(value, unit, kind: str) -> float | None:
    """Convert a raw sample value to the biomarker's canonical unit.

    mass → kilograms (via the sample's unit); rate → bpm (unit-agnostic).
    Returns None for a missing value or an unrecognised mass unit (we skip
    rather than guess)."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if kind == "mass":
        u = (unit or "").strip().lower()
        factor = _MASS_TO_KG.get(u)
        if factor is None:
            return None
        return v * factor
    # rate: value is already bpm; HealthKit reports 'count/min'.
    return v


def resolve_proxy(peptide_name: str, biomarker_name: str) -> ProxyBinding | None:
    """Return the proxy binding for a (peptide, biomarker) pair, or None.

    A proxy binds only when the *requested* biomarker equals the panel marker
    the proxy resolves to for this peptide. For a GLP-1 peptide, body mass
    resolves to the class-qualified 'Body weight (GLP-1 RA)'; otherwise to the
    generic 'Body weight'. This is a pure, cheap lookup (no DB access) so
    callers can gate on it before touching the HealthKit store.
    """
    target = biomarker_name.strip().lower()
    glp1 = _is_glp1(peptide_name)
    for proxy in PROXY_MAP.values():
        name = proxy.glp1_name if (proxy.glp1_name and glp1) else proxy.base_name
        if name.strip().lower() == target:
            return ProxyBinding(
                proxy=proxy, biomarker_name=name, noise_scale=proxy.noise_scale
            )
    return None


def _collect(hk_conn, binding: ProxyBinding, patient_id: str,
             treatment_start: str) -> list[tuple[float, float]]:
    """Pull the proxy samples for the patient's subject, convert units, and
    collapse to one daily-median observation per calendar day."""
    from engine.healthkit.service import read_samples

    subject_id = resolve_subject_id(hk_conn, patient_id)
    if subject_id is None:
        return []

    # Only samples on/after treatment start can inform θ, so filter DB-side
    # (``since`` pushes ``start_time >= ?`` into SQL) rather than loading the
    # subject's entire proxy history and discarding pre-treatment rows here.
    rows = read_samples(
        hk_conn,
        subject_id=subject_id,
        type_identifier=binding.proxy.hk_type,
        since=treatment_start,
        limit=1_000_000,
    )

    # Bucket converted (week, value) pairs by UTC calendar day, then take the
    # per-day median of both. Keying on the UTC date (not the raw offset date)
    # keeps the bucket consistent with the UTC instant _weeks_between uses, so
    # a sample near local midnight can't land in the wrong day.
    per_day: dict[str, list[tuple[float, float]]] = {}
    for r in rows:
        val = _canonical_value(r.get("value"), r.get("unit"), binding.proxy.kind)
        if val is None:
            continue
        start = r.get("start_time")
        weeks = _weeks_between(treatment_start, start)
        if weeks is None or weeks < 0:
            continue
        parsed = _parse_dt(start)
        if parsed is None:
            continue
        day = _as_utc_naive(parsed).date().isoformat()
        per_day.setdefault(day, []).append((weeks, val))

    obs = [
        (statistics.median([w for w, _ in items]),
         statistics.median([v for _, v in items]))
        for items in per_day.values()
    ]
    obs.sort()
    return obs


def healthkit_observations(
    conn,
    patient_id: str,
    peptide_name: str,
    biomarker_name: str,
    treatment_start: str,
    *,
    hk_conn=None,
) -> list[tuple[float, float]]:
    """Proxy observations for one (patient, peptide, biomarker), in the same
    ``(weeks_since_start, value)`` shape ``predict_response`` already uses.

    Returns ``[]`` (gracefully) when:
      * the biomarker has no proxy counterpart for this peptide,
      * the patient has no linked HealthKit subject, or
      * the subject has no usable proxy samples.

    ``conn`` is the *tracking* connection. The HealthKit store is a separate
    database in dev/tests (SQLite files) but the same physical database in
    Postgres. We therefore read via, in order: an explicitly injected
    ``hk_conn`` (tests), the tracking connection itself when it is Postgres
    (shared DB), or a freshly opened HealthKit connection (SQLite fallback).
    """
    binding = resolve_proxy(peptide_name, biomarker_name)
    if binding is None:
        return []

    if hk_conn is not None:
        return _collect(hk_conn, binding, patient_id, treatment_start)
    if getattr(conn, "_is_pg", False):
        return _collect(conn, binding, patient_id, treatment_start)
    from engine.healthkit.db import get_conn as hk_get_conn
    with hk_get_conn() as c:
        return _collect(c, binding, patient_id, treatment_start)
