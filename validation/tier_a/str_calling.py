"""
validation/tier_a/str_calling.py
================================
Tier A — AR CAG short-tandem-repeat (STR) calling validation.

Validates `engine.repeat_callers.expansion_hunter`, which calls the Androgen
Receptor (AR) CAG repeat. Two deterministic, no-binary sub-tracks run now; the
full instrument-in-the-loop concordance is a documented hook (see below).

Sub-tracks
----------
1. **EH output parsing concordance** (analytical). Feeds synthetic-but-realistic
   ExpansionHunter VCF+JSON output with a *known* repeat count through
   :func:`parse_eh_output` and checks the parsed count matches. This answers
   "does the pipeline read the instrument's output correctly" without needing
   the binary, a BAM, or a reference FASTA.

2. **Interpretation boundary verification** (software *verification*, not clinical
   validation). Runs :func:`interpret_cag_repeat` across the documented
   breakpoints and checks the sensitivity tier is assigned without off-by-one
   errors at each boundary.

   ⚠️ **Scope honesty:** the master plan (§5.2.7) flags the CAG breakpoints and
   ancestry reference means as *hand-curated and needing clinical-evidence
   backing*. This sub-track verifies only that the code implements its **own
   documented spec** correctly — it makes **no claim** that the thresholds
   themselves are clinically correct. That is clinical validation (Tier C),
   out of scope here.

Not run here (documented hook)
------------------------------
End-to-end concordance — running the real ExpansionHunter binary on reference
BAMs aligned to hg38 and comparing called CAG lengths to an orthogonal truth set
(e.g. capillary-electrophoresis-sized Coriell samples) — requires the binary, a
reference FASTA, and STR reference materials. This is the STR analogue of the
hap.py hook in the genotype track. :func:`environment_status` reports whether the
binary/reference are even present so a runner can say *why* it was skipped.
"""
from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from engine.repeat_callers.expansion_hunter import (
    DEFAULT_REFERENCE_FASTA,
    EXPANSION_HUNTER_BIN,
    interpret_cag_repeat,
    parse_eh_output,
)

from .metrics import compare_categorical


# ──────────────────────────────────────────────────────────────────────────
# Sub-track 1 — EH output parsing concordance
# ──────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EHOutputFixture:
    """A synthetic ExpansionHunter output with a known true repeat count."""
    id: str
    repcn_vcf: Optional[str]          # REPCN INFO value, e.g. "22" or "19/22"; None to omit
    json_repeat_size: Optional[int]   # JSON RepeatSize; None to omit
    expected_repeat_count: int        # what parse_eh_output should return


# REPCN diploid "19/22" → parser takes the shorter (more active) allele = 19.
# JSON RepeatSize, when present, is authoritative and overrides the VCF count.
EH_FIXTURES: list[EHOutputFixture] = [
    EHOutputFixture("json_authoritative_22", None, 22, 22),
    EHOutputFixture("json_authoritative_36", None, 36, 36),
    EHOutputFixture("vcf_haploid_19", "19", None, 19),
    EHOutputFixture("vcf_diploid_min_19", "19/22", None, 19),
    EHOutputFixture("json_overrides_vcf", "30/30", 22, 22),
]


def _write_eh_outputs(dir_: Path, fx: EHOutputFixture) -> tuple[Path, Path]:
    """Write a synthetic EH .vcf and .json for a fixture; return their paths."""
    vcf_lines = [
        "##fileformat=VCFv4.1",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE",
    ]
    if fx.repcn_vcf is not None:
        info = f"END=67545385;REF=22;RL=210;RU=CAG;REPCN={fx.repcn_vcf}"
        vcf_lines.append(
            f"chrX\t67545316\tAR\t.\t<STR{fx.repcn_vcf.split('/')[0]}>\t.\tPASS\t{info}"
            f"\tGT\t1/1"
        )
    vcf_path = dir_ / f"{fx.id}.vcf"
    vcf_path.write_text("\n".join(vcf_lines) + "\n", encoding="utf-8")

    ar_variant: dict[str, Any] = {
        "ReferenceRegion": "chrX:67545316-67545385",
        "RepeatSizeConfidenceInterval": {"Low": 1, "High": 1},
        "ReadSupport": {"SpanningReads": 20, "FlankingReads": 4, "InrepeatReads": 0},
    }
    if fx.json_repeat_size is not None:
        ar_variant["RepeatSize"] = fx.json_repeat_size
        ar_variant["RepeatSizeConfidenceInterval"] = {
            "Low": fx.json_repeat_size, "High": fx.json_repeat_size,
        }
    json_obj = {"LocusResults": {"AR": {"AlleleCount": 2, "Variants": {"AR": ar_variant}}}}
    json_path = dir_ / f"{fx.id}.json"
    json_path.write_text(json.dumps(json_obj), encoding="utf-8")
    return vcf_path, json_path


def run_parser_concordance(
    fixtures: list[EHOutputFixture] = EH_FIXTURES,
) -> dict[str, Any]:
    """Parse each synthetic EH output and compare the count to ground truth."""
    observed: dict[tuple[str, str], Optional[str]] = {}
    expected: dict[tuple[str, str], Optional[str]] = {}
    details: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="str_val_") as td:
        d = Path(td)
        for fx in fixtures:
            vcf_path, json_path = _write_eh_outputs(d, fx)
            parsed = parse_eh_output(vcf_path, json_path)
            got = parsed.get("repeat_count")
            observed[(fx.id, "repeat_count")] = None if got is None else str(got)
            expected[(fx.id, "repeat_count")] = str(fx.expected_repeat_count)
            details.append({
                "id": fx.id,
                "expected": fx.expected_repeat_count,
                "parsed": got,
                "ok": got == fx.expected_repeat_count,
            })

    conc = compare_categorical(observed, expected, case_sensitive=True)
    return {"concordance": conc.to_dict(), "details": details}


# ──────────────────────────────────────────────────────────────────────────
# Sub-track 2 — interpretation boundary verification
# ──────────────────────────────────────────────────────────────────────────

# (repeat_count, expected sensitivity_level) at and around each documented
# breakpoint: <18 VERY_HIGH, <23 HIGH, <27 NORMAL, <32 REDUCED, <36 LOW,
# >=36 VERY_LOW_PATHOLOGIC.
BOUNDARY_CASES: list[tuple[int, str]] = [
    (10, "VERY_HIGH"),
    (17, "VERY_HIGH"),
    (18, "HIGH"),
    (22, "HIGH"),
    (23, "NORMAL"),
    (26, "NORMAL"),
    (27, "REDUCED"),
    (31, "REDUCED"),
    (32, "LOW"),
    (35, "LOW"),
    (36, "VERY_LOW_PATHOLOGIC"),
    (45, "VERY_LOW_PATHOLOGIC"),
]


def run_interpretation_verification(
    cases: list[tuple[int, str]] = BOUNDARY_CASES,
) -> dict[str, Any]:
    """Check the sensitivity-tier classifier against its documented breakpoints."""
    observed: dict[tuple[str, str], Optional[str]] = {}
    expected: dict[tuple[str, str], Optional[str]] = {}
    details: list[dict[str, Any]] = []

    for count, exp_level in cases:
        got = interpret_cag_repeat(count, sex="female", ancestry="unknown")
        level = got["sensitivity_level"]
        key = (f"cag_{count}", "level")
        observed[key] = level
        expected[key] = exp_level
        details.append({
            "repeat_count": count,
            "expected_level": exp_level,
            "actual_level": level,
            "ok": level == exp_level,
        })

    conc = compare_categorical(observed, expected, case_sensitive=True)
    return {"concordance": conc.to_dict(), "details": details}


# ──────────────────────────────────────────────────────────────────────────
# Environment status for the end-to-end hook
# ──────────────────────────────────────────────────────────────────────────

def environment_status() -> dict[str, Any]:
    """Report whether the EH binary + reference FASTA are present.

    The end-to-end concordance track cannot run without these; this lets a
    runner state *why* it was skipped instead of silently omitting it.
    """
    import shutil

    eh = shutil.which("ExpansionHunter") or EXPANSION_HUNTER_BIN
    eh_present = Path(eh).exists()
    ref_present = Path(DEFAULT_REFERENCE_FASTA).exists()
    return {
        "expansion_hunter_present": eh_present,
        "reference_fasta_present": ref_present,
        "end_to_end_runnable": eh_present and ref_present,
        "note": (
            "End-to-end STR concordance (binary + BAM + reference + STR truth "
            "set) is not run by this harness; supply reference materials and "
            "wire it in as a follow-up (see module docstring)."
        ),
    }


# ──────────────────────────────────────────────────────────────────────────
# Orchestration + reporting
# ──────────────────────────────────────────────────────────────────────────

def run_str_validation() -> dict[str, Any]:
    return {
        "track": "ar_cag_str_calling",
        "parser_concordance": run_parser_concordance(),
        "interpretation_verification": run_interpretation_verification(),
        "environment": environment_status(),
    }


def render_markdown(report: dict[str, Any]) -> str:
    def pct(x: Optional[float]) -> str:
        return "n/a" if x is None else f"{x * 100:.1f}%"

    parser = report["parser_concordance"]["concordance"]
    interp = report["interpretation_verification"]["concordance"]
    env = report["environment"]

    lines = [
        "# Tier A — AR CAG STR Calling Validation",
        "",
        "## 1. EH output parsing concordance (analytical)",
        f"- Concordant: {parser['n_concordant']} / {parser['n_compared']} "
        f"→ **{pct(parser['concordance_rate'])}**",
    ]
    for d in report["parser_concordance"]["details"]:
        mark = "✅" if d["ok"] else "❌"
        lines.append(f"  - {mark} {d['id']}: expected {d['expected']}, "
                     f"parsed {d['parsed']}")

    lines += [
        "",
        "## 2. Interpretation boundary verification (implementation, NOT clinical)",
        "> Verifies the tier classifier implements its documented breakpoints "
        "without off-by-one errors. Makes **no claim** the thresholds are "
        "clinically correct (master plan §5.2.7 — that is Tier C).",
        f"- Correct: {interp['n_concordant']} / {interp['n_compared']} "
        f"→ **{pct(interp['concordance_rate'])}**",
    ]
    for d in report["interpretation_verification"]["details"]:
        mark = "✅" if d["ok"] else "❌"
        lines.append(f"  - {mark} CAG={d['repeat_count']}: "
                     f"{d['expected_level']} → {d['actual_level']}")

    lines += [
        "",
        "## 3. End-to-end concordance (not run)",
        f"- ExpansionHunter binary present: {env['expansion_hunter_present']}",
        f"- Reference FASTA present: {env['reference_fasta_present']}",
        f"- {env['note']}",
        "",
    ]
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Tier A AR CAG STR calling validation")
    ap.add_argument("--out-dir", default="validation/reports")
    args = ap.parse_args(argv)

    report = run_str_validation()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tier_a_str_calling.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    md = render_markdown(report)
    (out_dir / "tier_a_str_calling.md").write_text(md, encoding="utf-8")
    print(md)

    # Non-zero if either deterministic sub-track has a failure (CI gate).
    parser_rate = report["parser_concordance"]["concordance"]["concordance_rate"]
    interp_rate = report["interpretation_verification"]["concordance"]["concordance_rate"]
    ok = (parser_rate == 1.0) and (interp_rate == 1.0)
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
