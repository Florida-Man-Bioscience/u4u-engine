"""
validation/tier_a/reference.py
==============================
Loaders for Tier A reference truth sets.

Tier A validates the pipeline against materials that are **not human subjects**
(45 CFR 46.102(e)): cell-line reference materials and de-identified public
benchmark data. This module reads those truth sets into simple dataclasses the
runner can compare pipeline output against.

Supported reference formats
---------------------------
1. **GeT-RM PGx consensus diplotypes** (TSV) — the CDC/GeT-RM consensus
   star-allele diplotypes for Coriell cell lines (CYP2D6, CYP2C19, …). One row
   per (sample, gene). See ``validation/reference/getrm_pgx_seed.tsv`` for the
   schema and a small seed set.

2. **Variant genotype truth** (TSV) — expected genotypes at specific sites for a
   reference sample (e.g. a tractable rsID-level subset distilled from a GIAB
   benchmark VCF). One row per (sample, site).

The full GA4GH/hap.py comparison of a complete GIAB benchmark VCF is a separate,
heavier integration (an external tool, not a parser) and is intentionally out of
scope for this scaffold; see the README. This loader covers the site-level
subset that is directly comparable to the pipeline's per-variant output.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class PGxReferenceCall:
    """One GeT-RM consensus diplotype for a (sample, gene)."""
    sample: str
    gene: str
    diplotype: str               # e.g. "*1/*2"
    phenotype: Optional[str]     # consensus phenotype label if provided (e.g. "IM")
    source: str                  # provenance, e.g. "GeT-RM 2016"


@dataclass(frozen=True)
class GenotypeTruth:
    """One expected genotype at a site for a sample."""
    sample: str
    site: str                    # rsID (e.g. "rs4244285") or "chrom:pos"
    genotype: str                # normalized genotype, e.g. "0/1", "1/1", or "ref"


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        # Skip comment lines beginning with '#'
        rows = [ln for ln in fh if not ln.lstrip().startswith("#")]
    reader = csv.DictReader(rows, delimiter="\t")
    return [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in reader]


def load_pgx_reference(path: str | Path) -> list[PGxReferenceCall]:
    """Load GeT-RM-format PGx consensus diplotypes.

    Required columns: ``sample``, ``gene``, ``diplotype``.
    Optional columns: ``phenotype``, ``source``.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"PGx reference file not found: {p}")

    calls: list[PGxReferenceCall] = []
    for row in _read_tsv(p):
        if not row.get("sample") or not row.get("gene") or not row.get("diplotype"):
            continue
        calls.append(
            PGxReferenceCall(
                sample=row["sample"],
                gene=row["gene"],
                diplotype=row["diplotype"],
                phenotype=row.get("phenotype") or None,
                source=row.get("source") or "unspecified",
            )
        )
    return calls


def load_genotype_truth(path: str | Path) -> list[GenotypeTruth]:
    """Load a variant genotype truth set.

    Required columns: ``sample``, ``site``, ``genotype``.
    ``site`` is an rsID or ``chrom:pos``; ``genotype`` is ``0/1``/``1/1``/``ref``.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Genotype truth file not found: {p}")

    truths: list[GenotypeTruth] = []
    for row in _read_tsv(p):
        if not row.get("sample") or not row.get("site") or not row.get("genotype"):
            continue
        truths.append(
            GenotypeTruth(
                sample=row["sample"],
                site=row["site"],
                genotype=row["genotype"],
            )
        )
    return truths
