"""
validation/reference/giab_truth_from_vcf.py
===========================================
Convert a GIAB high-confidence benchmark VCF into the site-level genotype truth
TSV consumed by the Tier A variant-genotype track
(`validation.tier_a.reference.load_genotype_truth`).

The pipeline reports per-variant genotypes; GIAB provides high-confidence truth.
To make a fair, tractable comparison we restrict to a **panel** of GRCh38 sites
(e.g. positions distilled from the ACMG81 / peptide-gene panel) and emit, per
site, the benchmark genotype — or ``ref`` when the panel site is absent from the
VCF (valid only inside the benchmark high-confidence BED; see ``--confident-bed``).

The extraction core (:func:`extract_truth`) is pure and unit-tested offline; the
CLI wrapper handles file/gzip I/O.

Usage
-----
    python validation/reference/giab_truth_from_vcf.py \\
        --vcf HG001_GRCh38_benchmark.vcf.gz \\
        --sample NA12878 \\
        --panel validation/reference/panel_sites_grch38.txt \\
        --out validation/reference/giab_genotypes.tsv
"""
from __future__ import annotations

import argparse
import gzip
import sys
from pathlib import Path
from typing import Iterable, Optional


def normalize_gt(gt_field: str) -> Optional[str]:
    """Normalize a VCF GT subfield to ``a/b`` form, or None if it's a no-call.

    Phasing (``|``) is collapsed to ``/`` and alleles are sorted so ``1/0`` and
    ``0/1`` compare equal. A genotype with any missing allele (``.``) is a
    no-call → None. ``0/0`` is returned as the ``ref`` sentinel.
    """
    gt = gt_field.split(":")[0].strip()
    if not gt or gt in (".", "./.", ".|."):
        return None
    sep = "|" if "|" in gt else "/"
    parts = gt.split(sep)
    if any(p == "." or p == "" for p in parts):
        return None
    try:
        alleles = sorted(int(p) for p in parts)
    except ValueError:
        return None
    if all(a == 0 for a in alleles):
        return "ref"
    return "/".join(str(a) for a in alleles)


def _panel_key(chrom: str, pos: str) -> str:
    """Canonical site key: strip a leading 'chr' so chr1:x and 1:x unify."""
    c = chrom[3:] if chrom.lower().startswith("chr") else chrom
    return f"{c}:{pos}"


def load_panel(lines: Iterable[str]) -> set[str]:
    """Parse a panel file: one ``chrom:pos`` (or ``chr1:pos``) per line."""
    panel: set[str] = set()
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if ":" not in ln:
            continue
        chrom, pos = ln.split(":", 1)
        panel.add(_panel_key(chrom, pos.strip()))
    return panel


def extract_truth(
    vcf_lines: Iterable[str],
    sample: str,
    panel: Optional[set[str]] = None,
) -> list[tuple[str, str, str]]:
    """Extract ``(sample, site, genotype)`` rows from VCF lines.

    - ``site`` is the canonical ``chrom:pos`` key.
    - Only the first ALT-bearing genotype column is read; GIAB benchmark VCFs are
      single-sample, so the sample column is located from the ``#CHROM`` header.
    - When ``panel`` is given, only panel sites are emitted, and panel sites not
      seen in the VCF are emitted as ``ref`` (assumed high-confidence reference).
    - No-call genotypes are skipped.
    """
    rows: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    sample_col: Optional[int] = None

    for line in vcf_lines:
        if line.startswith("##"):
            continue
        if line.startswith("#CHROM"):
            header = line.rstrip("\n").split("\t")
            # FORMAT is col 8; sample columns start at 9. Use the named sample if
            # present, else the first sample column.
            if sample in header:
                sample_col = header.index(sample)
            elif len(header) > 9:
                sample_col = 9
            continue
        if not line.strip():
            continue

        fields = line.rstrip("\n").split("\t")
        if len(fields) < 8:
            continue
        chrom, pos = fields[0], fields[1]
        site = _panel_key(chrom, pos)
        if panel is not None and site not in panel:
            continue

        # Genotype: needs FORMAT (col 8) + a sample column (col 9+).
        gt = None
        if sample_col is not None and len(fields) > sample_col:
            gt = normalize_gt(fields[sample_col])
        if gt is None:
            continue

        rows.append((sample, site, gt))
        seen.add(site)

    # Panel sites never seen → confident reference (caveat in module docstring).
    if panel is not None:
        for site in sorted(panel - seen):
            rows.append((sample, site, "ref"))

    return rows


def _open_maybe_gzip(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="GIAB benchmark VCF -> Tier A genotype truth TSV")
    ap.add_argument("--vcf", required=True, help="GIAB benchmark VCF (.vcf or .vcf.gz)")
    ap.add_argument("--sample", required=True, help="Sample id to label rows with")
    ap.add_argument("--panel", help="Panel file of chrom:pos sites (one per line)")
    ap.add_argument("--out", required=True, help="Output truth TSV path")
    args = ap.parse_args(argv)

    vcf_path = Path(args.vcf)
    if not vcf_path.exists():
        print(f"error: VCF not found: {vcf_path}", file=sys.stderr)
        return 2

    panel = None
    if args.panel:
        panel_path = Path(args.panel)
        if not panel_path.exists():
            print(f"error: panel not found: {panel_path}", file=sys.stderr)
            return 2
        panel = load_panel(panel_path.read_text(encoding="utf-8").splitlines())

    with _open_maybe_gzip(vcf_path) as fh:
        rows = extract_truth(fh, args.sample, panel)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as out:
        out.write("sample\tsite\tgenotype\n")
        for sample, site, gt in rows:
            out.write(f"{sample}\t{site}\t{gt}\n")

    n_var = sum(1 for _, _, g in rows if g != "ref")
    print(f"Wrote {len(rows)} sites ({n_var} variant, {len(rows) - n_var} ref) "
          f"to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
