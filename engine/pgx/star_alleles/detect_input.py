"""
engine/pgx/star_alleles/detect_input.py
========================================
Decide which star-allele caller path to take based on inputs available.
"""
from __future__ import annotations

import os


def detect_input_type(bam_path: str | None = None) -> str:
    """
    Return one of:
      "array"   — variants only (VCF, 23andMe, rsID list)
      "bam_sr"  — short-read BAM available
      "bam_lr"  — long-read BAM available (filename hint: .ont. or .pacbio.)
    """
    if not bam_path:
        return "array"
    if not os.path.exists(bam_path):
        return "array"
    name = os.path.basename(bam_path).lower()
    if ".ont." in name or ".pacbio." in name or ".lr." in name or "longread" in name:
        return "bam_lr"
    return "bam_sr"
