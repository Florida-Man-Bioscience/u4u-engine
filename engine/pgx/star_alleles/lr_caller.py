"""
engine/pgx/star_alleles/lr_caller.py
=====================================
Optional long-read (ONT / PacBio HiFi) star-allele caller. PyPGx ≥ 0.20
supports a long-read mode that produces phased diplotypes directly; this
is currently the gold-standard input path for CYP2D6 and HLA.

This module is a thin wrapper that delegates to PyPGx when present and
returns [] otherwise.
"""
from __future__ import annotations

import logging
import shutil
import subprocess

from ..types import Phenotype, StarAlleleCall

log = logging.getLogger(__name__)

LR_GENES = [
    "CYP2D6", "CYP2C19", "CYP2C9", "CYP2B6", "CYP3A5",
    "DPYD", "TPMT", "UGT1A1", "NUDT15", "SLCO1B1",
]


def call_star_alleles_from_long_read(bam_path: str) -> list[StarAlleleCall]:
    if not bam_path or not shutil.which("pypgx"):
        return []
    out: list[StarAlleleCall] = []
    for gene in LR_GENES:
        try:
            proc = subprocess.run(
                ["pypgx", "run-ngs-pipeline", "--gene", gene,
                 "--input-bam", bam_path, "--assembly", "GRCh38",
                 "--long-read"],
                capture_output=True, text=True, timeout=300,
            )
            if proc.returncode != 0:
                continue
            lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
            if not lines:
                continue
            out.append(StarAlleleCall(
                gene=gene,
                diplotype=lines[-1],
                activity_score=None,
                phenotype=Phenotype.INDETERMINATE,
                callers_agreed=["pypgx_lr"],
                confidence=0.95,  # phased long-read is the highest-quality call
                evidence_tier="definitive",
            ))
        except (subprocess.TimeoutExpired, OSError) as e:
            log.debug("pypgx LR failed for %s: %s", gene, e)
            continue
    return out
