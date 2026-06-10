"""
engine/liftover.py
==================
Optional GRCh37 → GRCh38 coordinate liftover.

By default the engine *rejects* non-GRCh38 coordinate files (see
``genome_build.py``) because mis-mapped coordinates are a patient-safety
hazard. When liftover is explicitly enabled and a chain is available, GRCh37
coordinate variants can instead be lifted to GRCh38 and processed.

Liftover is itself an analytical step that must be validated before clinical
use; it is opt-in and off by default.

Configuration
-------------
    ENABLE_LIFTOVER          "1"/"true" to enable (default: off)
    LIFTOVER_CHAIN_37_TO_38  path to a local hg19→hg38 chain file (optional;
                             when absent, pyliftover fetches the UCSC chain,
                             which requires network access on first use)

Public interface
----------------
    liftover_available(from_build="GRCh37") -> bool
    lift_variants_to_grch38(variants) -> tuple[list[dict], list[dict]]
    lift_coordinate_variants(variants, convert) -> tuple[list[dict], list[dict]]
"""

from __future__ import annotations

import logging
import os
from typing import Callable, Optional

log = logging.getLogger(__name__)

ENABLE_LIFTOVER = os.getenv("ENABLE_LIFTOVER", "").lower() in ("1", "true", "yes", "on")
LIFTOVER_CHAIN_37_TO_38 = os.getenv("LIFTOVER_CHAIN_37_TO_38", "").strip()

_lifter_cache: dict[str, object] = {}


def _get_lifter():
    """Lazily construct a pyliftover hg19→hg38 lifter, or return None."""
    if "37_38" in _lifter_cache:
        return _lifter_cache["37_38"]
    lifter = None
    try:
        from pyliftover import LiftOver  # type: ignore
        if LIFTOVER_CHAIN_37_TO_38 and os.path.exists(LIFTOVER_CHAIN_37_TO_38):
            lifter = LiftOver(LIFTOVER_CHAIN_37_TO_38)
        else:
            lifter = LiftOver("hg19", "hg38")
    except Exception as e:  # pyliftover missing or chain unavailable
        log.warning("liftover unavailable: %s", e)
        lifter = None
    _lifter_cache["37_38"] = lifter
    return lifter


def liftover_available(from_build: str = "GRCh37") -> bool:
    """True only when liftover is enabled and a lifter for this build exists."""
    if not ENABLE_LIFTOVER or from_build != "GRCh37":
        return False
    return _get_lifter() is not None


def _make_convert(lifter) -> Callable[[str, int], Optional[tuple[str, int]]]:
    """
    Wrap a pyliftover lifter as ``convert(chrom, pos1based) -> (chrom, pos1based)``.

    pyliftover uses 'chr'-prefixed names and 0-based coordinates; the engine
    uses bare chromosome names and 1-based positions.
    """
    def convert(chrom: str, pos: int) -> Optional[tuple[str, int]]:
        query_chrom = chrom if str(chrom).startswith("chr") else f"chr{chrom}"
        res = lifter.convert_coordinate(query_chrom, int(pos) - 1)
        if not res:
            return None
        new_chrom, new_pos0 = res[0][0], res[0][1]
        return str(new_chrom).replace("chr", ""), int(new_pos0) + 1
    return convert


def lift_coordinate_variants(
    variants: list[dict],
    convert: Callable[[str, int], Optional[tuple[str, int]]],
) -> tuple[list[dict], list[dict]]:
    """
    Lift coordinate variants using a ``convert`` callable (dependency-injected
    so this is testable without pyliftover).

    rsid_only variants are passed through unchanged — their coordinates are
    re-resolved on GRCh38 from the rsID downstream. Coordinate variants that
    fail to map are collected in ``unmapped`` and excluded from results so they
    are never annotated on the wrong build.

    Returns ``(lifted, unmapped)``.
    """
    lifted: list[dict] = []
    unmapped: list[dict] = []
    for v in variants:
        if v.get("variant_type") != "coordinate" or not v.get("chrom") or not v.get("pos"):
            lifted.append(v)
            continue
        res = convert(v["chrom"], v["pos"])
        if not res:
            unmapped.append(v)
            continue
        nv = dict(v)
        nv["chrom"], nv["pos"] = res[0], res[1]
        lifted.append(nv)
    return lifted, unmapped


def lift_variants_to_grch38(variants: list[dict]) -> tuple[list[dict], list[dict]]:
    """Lift GRCh37 coordinate variants to GRCh38. Returns ``(lifted, unmapped)``."""
    lifter = _get_lifter()
    if lifter is None:
        raise RuntimeError("liftover requested but no lifter is available")
    return lift_coordinate_variants(variants, _make_convert(lifter))
