"""
validation/tier_a/run.py
========================
Tier A concordance runner.

Wires reference samples through ``engine.run_pipeline`` and scores the output
against the loaded truth sets using the pure functions in ``metrics.py``. Emits
a JSON evidence report and a human-readable Markdown summary.

This is **validation tooling, not a unit test**: it invokes the live pipeline,
which (for coordinate variants) calls external annotation APIs. Run it against a
warmed annotation cache or a pinned knowledge-base snapshot for reproducible
numbers — see the README. The metrics math itself is covered by offline unit
tests in ``tests/test_validation/``.

Honesty contract: this runner never fabricates a denominator. If a reference
file or a sample input is missing, it says so and the corresponding rate is
reported as ``null`` (undefined), not as a passing score.

Usage
-----
    nix develop --command python -m validation.tier_a.run \\
        --pgx-reference validation/reference/getrm_pgx_seed.tsv \\
        --sample-map    validation/reference/sample_inputs.tsv \\
        --out-dir       validation/reports

Where ``--sample-map`` is a TSV of ``sample<TAB>path`` pointing each reference
sample id to its genome input file (VCF / array export). Samples present in the
reference but absent from the map are reported as ``not_run`` (not as failures).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .metrics import (
    REF,
    compare_categorical,
    compare_genotypes,
)
from .reference import (
    GenotypeTruth,
    PGxReferenceCall,
    load_genotype_truth,
    load_pgx_reference,
)


# ──────────────────────────────────────────────────────────────────────────
# Sample input map
# ──────────────────────────────────────────────────────────────────────────

def load_sample_map(path: str | Path) -> dict[str, Path]:
    """Load a ``sample<TAB>path`` TSV mapping sample ids to genome input files."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Sample map not found: {p}")
    mapping: dict[str, Path] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        mapping[parts[0].strip()] = Path(parts[1].strip())
    return mapping


# ──────────────────────────────────────────────────────────────────────────
# Pipeline invocation + output extraction
# ──────────────────────────────────────────────────────────────────────────

def run_sample(input_path: Path) -> dict:
    """Run a single reference sample through the pipeline.

    Imported lazily so that `--help`, unit tests, and report-only runs do not
    require the full engine dependency tree.
    """
    from engine import run_pipeline  # lazy import

    data = input_path.read_bytes()
    # Tier A measures raw analytical accuracy, so we deliberately do NOT apply
    # the production ACMG81/peptide panel filters — they would hide most truth
    # sites. filters=[] processes all variants.
    return run_pipeline(data, input_path.name, filters=[])


def extract_observed_diplotypes(
    sample: str, pipeline_out: dict
) -> dict[tuple[str, str], Optional[str]]:
    """Map a pipeline result to ``{(sample, gene): diplotype}``."""
    pgx = pipeline_out.get("pgx_profile") or {}
    observed: dict[tuple[str, str], Optional[str]] = {}
    for call in pgx.get("star_alleles", []) or []:
        gene = call.get("gene")
        if gene:
            observed[(sample, gene)] = call.get("diplotype")
    return observed


def extract_observed_phenotypes(
    sample: str, pipeline_out: dict
) -> dict[tuple[str, str], Optional[str]]:
    """Map a pipeline result to ``{(sample, gene): phenotype}`` (e.g. "PM")."""
    pgx = pipeline_out.get("pgx_profile") or {}
    observed: dict[tuple[str, str], Optional[str]] = {}
    for call in pgx.get("star_alleles", []) or []:
        gene = call.get("gene")
        if gene:
            observed[(sample, gene)] = call.get("phenotype")
    return observed


def canonical_site(site: str) -> str:
    """Canonical site key: bare ``chrom:pos`` for coordinates, rsID unchanged.

    Strips a leading ``chr`` so ``chr1:100`` and ``1:100`` unify (the engine and
    the GIAB converter both emit bare chromosomes, but truth files may not).
    Keys without a ``:`` (rsIDs) pass through untouched.
    """
    s = site.strip()
    if ":" not in s:
        return s
    chrom, _, pos = s.partition(":")
    chrom = chrom[3:] if chrom.lower().startswith("chr") else chrom
    return f"{chrom}:{pos}"


def extract_observed_genotypes(pipeline_out: dict) -> dict[str, str]:
    """Map a pipeline result to ``{site: genotype}``, indexed under BOTH the
    rsID and the canonical ``chrom:pos`` so a truth set keyed either way matches.

    This matters for real data: GIAB benchmark VCFs carry no rsIDs, so
    GIAB-derived truth is coordinate-keyed, while GeT-RM / hand-curated truth is
    often rsID-keyed. The pipeline reports both an rsID and coordinates per
    variant, so registering the genotype under each available key lets the
    genotype track compare against either keyspace. (Keying by rsID alone — the
    previous behaviour — silently turned every coordinate-keyed truth site into
    a false negative.) Only variants the pipeline actually reported appear here;
    absence of a site is interpreted as a no-call (reference) by
    :func:`compare_genotypes`.
    """
    observed: dict[str, str] = {}
    for v in pipeline_out.get("variants", []) or []:
        gt = v.get("genotype")
        if not gt:
            continue
        rsid = v.get("rsid")
        if rsid:
            observed[rsid] = gt
        if v.get("chrom") and v.get("pos") is not None:
            observed[canonical_site(f"{v['chrom']}:{v['pos']}")] = gt
    return observed


# ──────────────────────────────────────────────────────────────────────────
# Orchestration
# ──────────────────────────────────────────────────────────────────────────

def run_concordance(
    pgx_reference: Optional[str],
    genotype_truth: Optional[str],
    sample_map: Optional[str],
) -> dict:
    """Execute the configured concordance tracks and return a report dict."""
    report: dict = {
        "tracks": {},
        "samples_run": [],
        "samples_not_run": [],
        "warnings": [],
    }

    samples = load_sample_map(sample_map) if sample_map else {}
    if not samples:
        report["warnings"].append(
            "No sample input map provided — pipeline was not run; "
            "nothing could be compared. All rates are undefined (null)."
        )

    # Cache pipeline runs so both PGx and genotype tracks reuse one execution.
    pipeline_cache: dict[str, dict] = {}

    def _ensure_run(sample: str) -> Optional[dict]:
        if sample in pipeline_cache:
            return pipeline_cache[sample]
        path = samples.get(sample)
        if path is None or not path.exists():
            if sample not in report["samples_not_run"]:
                report["samples_not_run"].append(sample)
            return None
        out = run_sample(path)
        pipeline_cache[sample] = out
        if sample not in report["samples_run"]:
            report["samples_run"].append(sample)
        return out

    # ── PGx diplotype + phenotype track ────────────────────────────────────
    if pgx_reference:
        ref_calls: list[PGxReferenceCall] = load_pgx_reference(pgx_reference)
        exp_diplo = {(c.sample, c.gene): c.diplotype for c in ref_calls}
        exp_pheno = {
            (c.sample, c.gene): c.phenotype for c in ref_calls if c.phenotype
        }

        obs_diplo: dict[tuple[str, str], Optional[str]] = {}
        obs_pheno: dict[tuple[str, str], Optional[str]] = {}
        for sample in sorted({c.sample for c in ref_calls}):
            out = _ensure_run(sample)
            if out is None:
                continue
            obs_diplo.update(extract_observed_diplotypes(sample, out))
            obs_pheno.update(extract_observed_phenotypes(sample, out))

        report["tracks"]["pgx_diplotype"] = compare_categorical(
            obs_diplo, exp_diplo, case_sensitive=True
        ).to_dict()
        report["tracks"]["pgx_phenotype"] = compare_categorical(
            obs_pheno, exp_pheno, case_sensitive=False
        ).to_dict()

    # ── Variant genotype track ─────────────────────────────────────────────
    if genotype_truth:
        truths: list[GenotypeTruth] = load_genotype_truth(genotype_truth)
        # group by sample so each sample's confusion matrix uses its own sites
        by_sample: dict[str, dict[str, str]] = {}
        for t in truths:
            by_sample.setdefault(t.sample, {})[t.site] = t.genotype

        from .metrics import ConfusionMatrix  # local import to keep top clean

        combined = ConfusionMatrix()
        per_sample: dict[str, dict] = {}
        for sample, exp_sites in sorted(by_sample.items()):
            out = _ensure_run(sample)
            if out is None:
                continue
            obs = extract_observed_genotypes(out)
            # restrict observed to the truth-set sites for a fair confusion
            # matrix. Look up each truth site via its canonical key so a
            # coordinate-keyed (GIAB) or rsID-keyed truth set both resolve
            # against the dual-keyed observed map.
            obs_restricted = {s: obs.get(canonical_site(s), REF) for s in exp_sites}
            cm = compare_genotypes(obs_restricted, exp_sites)
            per_sample[sample] = cm.to_dict()
            for fld in ("tp", "fp", "fn", "tn", "genotype_mismatch"):
                setattr(combined, fld, getattr(combined, fld) + getattr(cm, fld))

        report["tracks"]["variant_genotype"] = {
            "combined": combined.to_dict(),
            "by_sample": per_sample,
        }

    return report


# ──────────────────────────────────────────────────────────────────────────
# Reporting
# ──────────────────────────────────────────────────────────────────────────

def _fmt_rate(rate: Optional[float]) -> str:
    return "n/a (undefined)" if rate is None else f"{rate * 100:.1f}%"


def render_markdown(report: dict) -> str:
    lines: list[str] = ["# Tier A Concordance Report", ""]

    lines.append(f"- Samples run: {len(report['samples_run'])} "
                 f"({', '.join(report['samples_run']) or 'none'})")
    if report["samples_not_run"]:
        lines.append(f"- Samples NOT run (no input mapped): "
                     f"{', '.join(report['samples_not_run'])}")
    for w in report.get("warnings", []):
        lines.append(f"- ⚠️ {w}")
    lines.append("")

    tracks = report.get("tracks", {})

    for name, label in (
        ("pgx_diplotype", "PGx diplotype concordance (GeT-RM)"),
        ("pgx_phenotype", "PGx phenotype concordance (GeT-RM)"),
    ):
        t = tracks.get(name)
        if not t:
            continue
        lines += [f"## {label}", ""]
        lines.append(f"- Compared: {t['n_compared']}  ·  "
                     f"Concordant: {t['n_concordant']}  ·  "
                     f"Skipped (no call): {t['n_skipped_missing']}")
        lines.append(f"- **Concordance: {_fmt_rate(t['concordance_rate'])}**")
        if t["by_key"]:
            lines += ["", "| Gene | Concordant / Compared | Rate |", "|---|---|---|"]
            for gene, k in t["by_key"].items():
                lines.append(f"| {gene} | {k['concordant']} / {k['compared']} "
                             f"| {_fmt_rate(k['rate'])} |")
        if t["discordances"]:
            lines += ["", "Discordances:", ""]
            for d in t["discordances"]:
                lines.append(f"- {d['sample']} / {d['key']}: "
                             f"expected `{d['expected']}`, observed `{d['observed']}`")
        lines.append("")

    vg = tracks.get("variant_genotype")
    if vg:
        c = vg["combined"]
        lines += ["## Variant genotype concordance (GIAB subset)", ""]
        lines.append(f"- TP {c['tp']} · FP {c['fp']} · FN {c['fn']} · TN {c['tn']} "
                     f"· genotype-mismatch {c['genotype_mismatch']}")
        lines.append(f"- Sensitivity {_fmt_rate(c['sensitivity'])} · "
                     f"Specificity {_fmt_rate(c['specificity'])} · "
                     f"Precision {_fmt_rate(c['precision'])} · "
                     f"F1 {_fmt_rate(c['f1'])}")
        lines.append(f"- Genotype concordance (of detected sites): "
                     f"{_fmt_rate(c['genotype_concordance'])}")
        lines.append("")

    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Tier A analytical concordance runner")
    ap.add_argument("--pgx-reference", help="GeT-RM PGx diplotype TSV")
    ap.add_argument("--genotype-truth", help="Variant genotype truth TSV")
    ap.add_argument("--sample-map", help="TSV of sample<TAB>genome-input-path")
    ap.add_argument("--out-dir", default="validation/reports",
                    help="Directory for JSON + Markdown reports")
    args = ap.parse_args(argv)

    if not args.pgx_reference and not args.genotype_truth:
        ap.error("provide at least one of --pgx-reference / --genotype-truth")

    report = run_concordance(
        pgx_reference=args.pgx_reference,
        genotype_truth=args.genotype_truth,
        sample_map=args.sample_map,
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tier_a_concordance.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    md = render_markdown(report)
    (out_dir / "tier_a_concordance.md").write_text(md, encoding="utf-8")

    print(md)
    print(f"\nWrote {out_dir/'tier_a_concordance.json'} and "
          f"{out_dir/'tier_a_concordance.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
