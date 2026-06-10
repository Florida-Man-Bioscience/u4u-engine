"""
engine/acmg/criteria.py
=======================
ACMG/AMP 2015 (Richards et al., Genet Med 2015) evidence codes and the rules
for combining them into a five-tier classification.

This module implements the *combining logic* only — the deterministic, well
specified part of the standard. Which evidence codes apply to a given variant
is decided by ``classifier.py`` (and, for clinical use, by a qualified human
reviewer). The combining rules below are a faithful encoding of the 2015
criteria; strength modifiers (ClinGen SVI) are supported by letting each code
carry an effective strength rather than its default.

Pathogenic strengths:  VERY_STRONG (PVS) > STRONG (PS) > MODERATE (PM) > SUPPORTING (PP)
Benign strengths:      STAND_ALONE (BA) , STRONG (BS) , SUPPORTING (BP)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Strength(str, Enum):
    # Pathogenic direction
    VERY_STRONG = "very_strong"   # PVS
    STRONG = "strong"             # PS
    MODERATE = "moderate"         # PM
    SUPPORTING = "supporting"     # PP
    # Benign direction
    STAND_ALONE = "stand_alone"   # BA
    BENIGN_STRONG = "benign_strong"        # BS
    BENIGN_SUPPORTING = "benign_supporting"  # BP


class Classification(str, Enum):
    PATHOGENIC = "Pathogenic"
    LIKELY_PATHOGENIC = "Likely pathogenic"
    UNCERTAIN = "Uncertain significance"
    LIKELY_BENIGN = "Likely benign"
    BENIGN = "Benign"


@dataclass(frozen=True)
class EvidenceCode:
    code: str                 # e.g. "PM2", "BA1"
    strength: Strength
    rationale: str

    @property
    def is_pathogenic(self) -> bool:
        return self.strength in (
            Strength.VERY_STRONG, Strength.STRONG, Strength.MODERATE, Strength.SUPPORTING,
        )

    @property
    def is_benign(self) -> bool:
        return not self.is_pathogenic

    def to_dict(self) -> dict:
        return {"code": self.code, "strength": self.strength.value, "rationale": self.rationale}


@dataclass(frozen=True)
class _Counts:
    pvs: int
    ps: int
    pm: int
    pp: int
    ba: int
    bs: int
    bp: int


def _count(codes: list[EvidenceCode]) -> _Counts:
    return _Counts(
        pvs=sum(c.strength == Strength.VERY_STRONG for c in codes),
        ps=sum(c.strength == Strength.STRONG for c in codes),
        pm=sum(c.strength == Strength.MODERATE for c in codes),
        pp=sum(c.strength == Strength.SUPPORTING for c in codes),
        ba=sum(c.strength == Strength.STAND_ALONE for c in codes),
        bs=sum(c.strength == Strength.BENIGN_STRONG for c in codes),
        bp=sum(c.strength == Strength.BENIGN_SUPPORTING for c in codes),
    )


def _meets_pathogenic(n: _Counts) -> bool:
    # (i) 1 PVS + (≥1 PS | ≥2 PM | 1 PM+1 PP | ≥2 PP)
    if n.pvs >= 1 and (n.ps >= 1 or n.pm >= 2 or (n.pm == 1 and n.pp >= 1) or n.pp >= 2):
        return True
    # (ii) ≥2 PS
    if n.ps >= 2:
        return True
    # (iii) 1 PS + (≥3 PM | 2 PM+≥2 PP | 1 PM+≥4 PP)
    if n.ps == 1 and (n.pm >= 3 or (n.pm == 2 and n.pp >= 2) or (n.pm == 1 and n.pp >= 4)):
        return True
    return False


def _meets_likely_pathogenic(n: _Counts) -> bool:
    # (i) 1 PVS + 1 PM
    if n.pvs == 1 and n.pm == 1:
        return True
    # (ii) 1 PS + 1-2 PM
    if n.ps == 1 and 1 <= n.pm <= 2:
        return True
    # (iii) 1 PS + ≥2 PP
    if n.ps == 1 and n.pp >= 2:
        return True
    # (iv) ≥3 PM
    if n.pm >= 3:
        return True
    # (v) 2 PM + ≥2 PP
    if n.pm == 2 and n.pp >= 2:
        return True
    # (vi) 1 PM + ≥4 PP
    if n.pm == 1 and n.pp >= 4:
        return True
    return False


def _meets_benign_standalone(n: _Counts) -> bool:
    return n.ba >= 1


def _meets_benign_strong(n: _Counts) -> bool:
    return n.bs >= 2


def _meets_likely_benign(n: _Counts) -> bool:
    # (i) 1 BS + 1 BP   (ii) ≥2 BP
    return (n.bs == 1 and n.bp >= 1) or n.bp >= 2


def combine(codes: list[EvidenceCode]) -> Classification:
    """
    Combine evidence codes into a five-tier classification per ACMG/AMP 2015.

    Contradictory evidence (both a pathogenic and a benign assertion are met)
    resolves to Uncertain significance, per the guideline's guidance that
    conflicting criteria be reported as VUS unless resolved by a curator.
    """
    n = _count(codes)

    path = _meets_pathogenic(n)
    likely_path = _meets_likely_pathogenic(n)
    benign = _meets_benign_standalone(n) or _meets_benign_strong(n)
    likely_benign = _meets_likely_benign(n)

    pathogenic_side = path or likely_path
    benign_side = benign or likely_benign

    if pathogenic_side and benign_side:
        return Classification.UNCERTAIN
    if path:
        return Classification.PATHOGENIC
    if likely_path:
        return Classification.LIKELY_PATHOGENIC
    if benign:
        return Classification.BENIGN
    if likely_benign:
        return Classification.LIKELY_BENIGN
    return Classification.UNCERTAIN
