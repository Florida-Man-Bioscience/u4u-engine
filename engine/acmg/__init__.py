"""
engine/acmg
===========
ACMG/AMP (2015) variant-classification support.

`classify_acmg(variant, config)` assembles the subset of ACMG/AMP evidence
codes derivable from the engine's annotations and combines them into a
five-tier classification. It is an evidence-assembly aid that ALWAYS requires
qualified human sign-out — it is not a final clinical classification. See
`classifier.py` for the scope and caveats.
"""

from .criteria import Classification, EvidenceCode, Strength, combine
from .classifier import AcmgConfig, assign_codes, classify_acmg

__all__ = [
    "Classification",
    "EvidenceCode",
    "Strength",
    "combine",
    "AcmgConfig",
    "assign_codes",
    "classify_acmg",
]
