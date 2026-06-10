"""
engine/acmg/aggregate.py
========================
Result-level summary of the per-variant ACMG/AMP evidence assembly.

The most useful safety output here is a list of **discordances** between the
automated ACMG classification and the ClinVar classification: those are exactly
the variants a curator should review first (e.g. ClinVar says Pathogenic but the
automated evidence lands at Benign/VUS, or vice versa).

Public interface
----------------
    summarize_acmg(variants: list[dict]) -> dict
"""

from __future__ import annotations

_PATH = {"pathogenic", "likely pathogenic"}
_BENIGN = {"benign", "likely benign"}
_VUS = {"uncertain significance", "uncertain", "vus"}


def _direction(label: str | None) -> str:
    """Map a classification string to 'pathogenic' | 'benign' | 'vus' | 'unknown'."""
    if not label:
        return "unknown"
    s = label.strip().lower()
    if any(k in s for k in _PATH):
        return "pathogenic"
    if any(k in s for k in _BENIGN):
        return "benign"
    if any(k in s for k in _VUS):
        return "vus"
    return "unknown"


def summarize_acmg(variants: list[dict]) -> dict:
    """
    Aggregate per-variant ACMG results into counts + ClinVar discordances.

    Discordance severity:
      - "opposing": ACMG and ClinVar give opposite definite directions
        (pathogenic vs benign) — highest curator priority.
      - "clinvar_only": ClinVar has a definite direction but ACMG is VUS.
      - "acmg_only": ACMG has a definite direction but ClinVar is VUS/absent.
    """
    counts: dict[str, int] = {}
    discordances: list[dict] = []
    n_with_acmg = 0

    for v in variants:
        acmg = v.get("acmg")
        if not acmg:
            continue
        n_with_acmg += 1
        classification = acmg.get("classification", "Uncertain significance")
        counts[classification] = counts.get(classification, 0) + 1

        acmg_dir = _direction(classification)
        clinvar_label = acmg.get("clinvar_comparison")
        clinvar_dir = _direction(clinvar_label)

        severity = None
        if {acmg_dir, clinvar_dir} == {"pathogenic", "benign"}:
            severity = "opposing"
        elif clinvar_dir in ("pathogenic", "benign") and acmg_dir == "vus":
            severity = "clinvar_only"
        elif acmg_dir in ("pathogenic", "benign") and clinvar_dir in ("vus", "unknown"):
            severity = "acmg_only"

        if severity:
            discordances.append({
                "variant_id": v.get("variant_id") or v.get("rsid") or v.get("location"),
                "acmg": classification,
                "clinvar": clinvar_label,
                "severity": severity,
            })

    return {
        "counts": counts,
        "variants_classified": n_with_acmg,
        "requires_review": n_with_acmg,   # every automated call needs sign-out
        "clinvar_discordances": discordances,
        "disclaimer": (
            "Automated ACMG/AMP evidence assembly. Discordances with ClinVar and "
            "all classifications require review and sign-out by a qualified "
            "laboratory professional before clinical use."
        ),
    }
