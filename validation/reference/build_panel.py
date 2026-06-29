"""
validation/reference/build_panel.py
===================================
Distill a GRCh38 ``chrom:pos`` panel from rsID filter lists (e.g. the ACMG81
secondary-findings set) for use as the ``--panel`` input to
``giab_truth_from_vcf.py``.

Why a panel
-----------
The GIAB genotype-truth comparison needs to be restricted to a tractable set of
sites aligned to what the pipeline actually evaluates — otherwise the confusion
matrix is dominated by millions of irrelevant reference positions. The natural
panel is the set of discrete, clinically-relevant sites the pipeline filters on:
the ACMG81 rsIDs, resolved to GRCh38 coordinates via the engine's rsID resolver.

Honesty contract
----------------
- rsIDs that fail to resolve are **reported, never silently dropped** — a panel
  that quietly omits sites would understate the truth-set denominator.
- Gene *ranges* (``data/peptide_genes.bed``) are intervals, not discrete variant
  sites, and cannot be enumerated into panel positions without a variant list.
  So ``--bed`` is used **only as a coverage report** (which resolved sites fall
  in which peptide gene, and which peptide genes have *zero* panel coverage),
  never to fabricate sites. To add peptide-gene sites to the panel, supply an
  rsID list for those genes' variants via another ``--rsids`` file.

The resolution core (:func:`distill_panel`) is pure — it takes a ``resolve_fn``
callable — so it is unit-tested offline. The CLI wires in the real, cache-backed
``engine.rsid_resolver.resolve_rsids`` (which calls Ensembl on a cache miss; run
it against a warmed ``data/rsid_cache.db`` for reproducibility).

Usage
-----
    nix develop --command python validation/reference/build_panel.py \\
        --rsids data/acmg81_rsids.txt \\
        --bed   data/peptide_genes.bed \\
        --out   validation/reference/panel_sites_grch38.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional

# Allow running as a path script (``python validation/reference/build_panel.py``):
# a path-run script puts its own dir on sys.path, not the repo root, so the lazy
# ``import engine`` in main() would fail. Put the repo root first.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_RSID_RE = re.compile(r"^rs\d+$")


def _canonical_site(site: str) -> str:
    """Canonical site key: bare ``chrom:pos``, stripping a leading ``chr``.

    Kept byte-identical to ``validation.tier_a.run.canonical_site`` so the
    panel's site keys match exactly what the genotype track compares against.
    Inlined (rather than imported) so this stays a self-contained script
    runnable as ``python validation/reference/build_panel.py``.
    """
    s = site.strip()
    if ":" not in s:
        return s
    chrom, _, pos = s.partition(":")
    chrom = chrom[3:] if chrom.lower().startswith("chr") else chrom
    return f"{chrom}:{pos}"


# ──────────────────────────────────────────────────────────────────────────
# Parsing
# ──────────────────────────────────────────────────────────────────────────

def parse_rsid_list(lines: Iterable[str]) -> list[str]:
    """Parse an rsID list file into a de-duplicated, order-preserving list.

    Takes the first whitespace-delimited token on each line so inline comments
    (``rs80357906   # 185delAG``) are handled. Blank lines and full-line
    comments are skipped. NB: this is deliberately *not* ``filters.load_filter_set``,
    which keeps the whole stripped line (comment included) — fine for set
    membership against clean rsIDs, but it would feed comment text to the
    resolver here.
    """
    out: list[str] = []
    seen: set[str] = set()
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        token = ln.split()[0]
        if _RSID_RE.match(token) and token not in seen:
            seen.add(token)
            out.append(token)
    return out


def parse_bed(lines: Iterable[str]) -> list[tuple[str, int, int, Optional[str]]]:
    """Parse a BED file into ``(chrom, start, end, gene)`` tuples (chrom bare)."""
    regions: list[tuple[str, int, int, Optional[str]]] = []
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.startswith("track"):
            continue
        parts = ln.split()
        if len(parts) < 3:
            continue
        chrom = parts[0][3:] if parts[0].lower().startswith("chr") else parts[0]
        try:
            start, end = int(parts[1]), int(parts[2])
        except ValueError:
            continue
        gene = parts[3] if len(parts) >= 4 else None
        regions.append((chrom, start, end, gene))
    return regions


# ──────────────────────────────────────────────────────────────────────────
# Sorting
# ──────────────────────────────────────────────────────────────────────────

def _chrom_sort_key(chrom: str) -> tuple[int, int, str]:
    c = chrom.upper()
    if c.isdigit():
        return (0, int(c), "")
    special = {"X": 23, "Y": 24, "MT": 25, "M": 25}
    if c in special:
        return (0, special[c], "")
    return (1, 0, c)


def _site_sort_key(site: str) -> tuple[tuple[int, int, str], int]:
    chrom, _, pos = site.partition(":")
    try:
        p = int(pos)
    except ValueError:
        p = 0
    return (_chrom_sort_key(chrom), p)


# ──────────────────────────────────────────────────────────────────────────
# Distillation
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class PanelResult:
    sites: list[str]                                  # sorted unique "chrom:pos"
    resolved_rsids: list[str]
    unresolved_rsids: list[str]
    sites_by_rsid: dict[str, list[str]] = field(default_factory=dict)

    @property
    def resolution_rate(self) -> Optional[float]:
        total = len(self.resolved_rsids) + len(self.unresolved_rsids)
        return (len(self.resolved_rsids) / total) if total else None

    def to_dict(self) -> dict:
        return {
            "n_sites": len(self.sites),
            "n_rsids_resolved": len(self.resolved_rsids),
            "n_rsids_unresolved": len(self.unresolved_rsids),
            "resolution_rate": self.resolution_rate,
            "unresolved_rsids": self.unresolved_rsids,
            "sites": self.sites,
        }


def distill_panel(
    rsids: list[str],
    resolve_fn: Callable[[list[str]], list[dict]],
) -> PanelResult:
    """Resolve rsIDs to GRCh38 panel sites.

    ``resolve_fn`` takes a list of rsIDs and returns coordinate variant dicts
    (the shape of ``engine.rsid_resolver.resolve_rsids``: each dict carries
    ``rsid``/``chrom``/``pos``). Multiple alt alleles for one rsID collapse to a
    single site. An rsID that yields no usable coordinate is reported as
    unresolved.
    """
    variants = resolve_fn(rsids) or []
    sites_by_rsid: dict[str, set[str]] = {}
    for v in variants:
        rsid, chrom, pos = v.get("rsid"), v.get("chrom"), v.get("pos")
        if not rsid or not chrom or pos is None:
            continue
        sites_by_rsid.setdefault(rsid, set()).add(_canonical_site(f"{chrom}:{pos}"))

    resolved = [r for r in rsids if r in sites_by_rsid]
    unresolved = [r for r in rsids if r not in sites_by_rsid]
    all_sites = sorted(
        {s for ss in sites_by_rsid.values() for s in ss}, key=_site_sort_key
    )
    return PanelResult(
        sites=all_sites,
        resolved_rsids=resolved,
        unresolved_rsids=unresolved,
        sites_by_rsid={k: sorted(v, key=_site_sort_key) for k, v in sites_by_rsid.items()},
    )


def bed_coverage(
    sites: list[str],
    regions: list[tuple[str, int, int, Optional[str]]],
) -> tuple[dict[str, int], list[str]]:
    """Count how many panel sites fall in each BED gene region.

    A 1-based site position ``p`` is in a 0-based half-open BED interval
    ``[start, end)`` iff ``start < p <= end``. Returns ``(per_gene_counts,
    genes_with_zero_sites)`` — the latter is the honest "your panel does not
    cover these genes" list.
    """
    parsed: list[tuple[str, int]] = []
    for s in sites:
        chrom, _, pos = s.partition(":")
        try:
            parsed.append((chrom, int(pos)))
        except ValueError:
            continue

    per_gene: dict[str, int] = {}
    for chrom, start, end, gene in regions:
        name = gene or f"{chrom}:{start}-{end}"
        hits = sum(1 for c, p in parsed if c == chrom and start < p <= end)
        per_gene[name] = per_gene.get(name, 0) + hits

    uncovered = sorted(g for g, n in per_gene.items() if n == 0)
    return per_gene, uncovered


# ──────────────────────────────────────────────────────────────────────────
# Rendering
# ──────────────────────────────────────────────────────────────────────────

def render_panel_file(result: PanelResult, sources: list[str]) -> str:
    """The panel file body: a provenance header (comments) + one site per line.

    ``giab_truth_from_vcf.py``'s ``load_panel`` skips ``#`` lines, so the header
    is safe to keep inline with the data.
    """
    lines = [
        "# GRCh38 panel sites — generated by validation/reference/build_panel.py",
        f"# Source rsID lists: {', '.join(sources)}",
        f"# {len(result.sites)} sites from {len(result.resolved_rsids)} resolved "
        f"rsIDs ({len(result.unresolved_rsids)} unresolved).",
        "# Format: <chrom>:<pos> (1-based, GRCh38, bare chromosome).",
    ]
    lines += result.sites
    return "\n".join(lines) + "\n"


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Distill a GRCh38 chrom:pos panel from rsID lists")
    ap.add_argument("--rsids", action="append", default=None,
                    help="rsID list file (repeatable). Default: data/acmg81_rsids.txt")
    ap.add_argument("--bed", help="Optional BED for a gene-coverage report (e.g. data/peptide_genes.bed)")
    ap.add_argument("--out", default="validation/reference/panel_sites_grch38.txt",
                    help="Output panel file")
    ap.add_argument("--report", help="Optional JSON report path (resolution + coverage)")
    args = ap.parse_args(argv)

    rsid_files = args.rsids or ["data/acmg81_rsids.txt"]

    rsids: list[str] = []
    seen: set[str] = set()
    for fp in rsid_files:
        p = Path(fp)
        if not p.exists():
            print(f"error: rsID list not found: {p}", file=sys.stderr)
            return 2
        for r in parse_rsid_list(p.read_text(encoding="utf-8").splitlines()):
            if r not in seen:
                seen.add(r)
                rsids.append(r)

    if not rsids:
        print("error: no rsIDs parsed from the input list(s)", file=sys.stderr)
        return 2

    print(f"Resolving {len(rsids)} rsIDs to GRCh38 coordinates "
          f"(cache: data/rsid_cache.db; cache misses hit Ensembl)…")
    from engine.rsid_resolver import resolve_rsids  # lazy: engine import

    result = distill_panel(rsids, resolve_rsids)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_panel_file(result, rsid_files), encoding="utf-8")

    print(f"\nWrote {len(result.sites)} panel sites to {out_path}")
    print(f"  resolved:   {len(result.resolved_rsids)} rsIDs")
    print(f"  unresolved: {len(result.unresolved_rsids)} rsIDs"
          + (f" — {', '.join(result.unresolved_rsids[:10])}"
             + ("…" if len(result.unresolved_rsids) > 10 else "")
             if result.unresolved_rsids else ""))

    report: dict = {"panel": result.to_dict(), "sources": rsid_files}

    if args.bed:
        bed_path = Path(args.bed)
        if not bed_path.exists():
            print(f"error: BED not found: {bed_path}", file=sys.stderr)
            return 2
        regions = parse_bed(bed_path.read_text(encoding="utf-8").splitlines())
        per_gene, uncovered = bed_coverage(result.sites, regions)
        report["bed_coverage"] = {"per_gene": per_gene, "genes_without_coverage": uncovered}
        covered = {g: n for g, n in per_gene.items() if n}
        print(f"\nBED coverage ({bed_path.name}):")
        if covered:
            for g, n in sorted(covered.items()):
                print(f"  {g}: {n} site(s)")
        else:
            print("  (no panel sites fall in any BED region)")
        if uncovered:
            print(f"  ⚠️  {len(uncovered)} gene(s) with NO panel coverage: "
                  f"{', '.join(uncovered)}")
            print("      (gene ranges are not enumerable into sites — supply an "
                  "rsID list for these genes' variants to include them.)")

    if args.report:
        rp = Path(args.report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nWrote report to {rp}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
