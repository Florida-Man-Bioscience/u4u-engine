"""
engine/pgx/star_alleles/allele_definitions.py
==============================================
Hand-curated, rsID-keyed star-allele definitions for the most actionable PGx
genes. This is the array/VCF path — it uses tag SNPs that are reliable on
consumer arrays. Complex SV alleles (CYP2D6 *5/*36 hybrids, CYP2B6 SVs) are
flagged but NOT called from arrays — they require the BAM path.

Allele functions follow CPIC's allele functionality assignments.

Sources:
  - PharmVar 6.x allele definitions
  - CPIC Allele Functionality Tables (publicly available CSV)
  - 23andMe/AncestryDNA chip content for tag-SNP availability

A defining variant set is matched if ALL listed rsIDs are present with the
specified genotype call. Default reference allele = *1.
"""
from __future__ import annotations

# Activity score per haplotype (CPIC standard scale 0.0 - 1.5 per allele;
# values for non-CYP genes use enzyme function: 0=no, 0.5=decreased, 1=normal, 1.5=increased)
ALLELE_FUNCTIONS: dict[str, dict[str, float]] = {
    "CYP2C19": {
        "*1": 1.0,    # normal
        "*2": 0.0,    # no function
        "*3": 0.0,    # no function
        "*17": 1.5,   # increased
        "*4": 0.0,
        "*8": 0.0,
    },
    "CYP2C9": {
        "*1": 1.0,
        "*2": 0.5,
        "*3": 0.0,
        "*5": 0.0,
        "*6": 0.0,
        "*8": 0.5,
        "*11": 0.5,
    },
    "CYP2D6": {
        "*1": 1.0,
        "*2": 1.0,
        "*3": 0.0,
        "*4": 0.0,
        "*6": 0.0,
        "*10": 0.25,  # decreased per 2024 update
        "*17": 0.5,
        "*41": 0.25,  # decreased per 2024 update
    },
    "TPMT": {
        "*1": 1.0,
        "*2": 0.0,
        "*3A": 0.0,
        "*3B": 0.0,
        "*3C": 0.0,
    },
    "DPYD": {
        # DPYD uses activity-score scale 0/0.5/1 per CPIC
        "Reference": 1.0,
        "c.1905+1G>A": 0.0,   # *2A
        "c.1679T>G": 0.0,     # *13
        "c.2846A>T": 0.5,
        "c.1236G>A": 0.5,     # HapB3
    },
    "SLCO1B1": {
        # CPIC uses function categories — mapped to numeric for uniformity
        "*1": 1.0,
        "*5": 0.0,            # poor function (rs4149056 C/C)
        "*15": 0.0,
        "*17": 0.0,
    },
    "VKORC1": {
        # VKORC1 is haploinsufficient; we report the rs9923231 allele directly.
        "G": 1.0,
        "A": 0.5,
    },
    "UGT1A1": {
        "*1": 1.0,
        "*28": 0.5,           # TA7
        "*6": 0.0,
        "*37": 0.0,
    },
    "NUDT15": {
        "*1": 1.0,
        "*3": 0.0,
        "*2": 0.0,
    },
}


# Each entry: gene → list of (allele_name, {rsid: required_genotype_letter})
# Genotype letters use the ALT allele (variant). A homozygous call requires
# both copies; heterozygous requires one copy.
#
# Defining-variant approach: an allele is called if ALL its defining variants
# are present on the same haplotype (we approximate without phasing by checking
# zygosity — see array_caller.py).
DEFINING_VARIANTS: dict[str, list[tuple[str, dict[str, str]]]] = {
    "CYP2C19": [
        ("*2",  {"rs4244285": "A"}),
        ("*3",  {"rs4986893": "A"}),
        ("*17", {"rs12248560": "T"}),
        ("*4",  {"rs28399504": "G"}),
        ("*8",  {"rs41291556": "C"}),
    ],
    "CYP2C9": [
        ("*2",  {"rs1799853": "T"}),
        ("*3",  {"rs1057910": "C"}),
        ("*5",  {"rs28371686": "C"}),
        ("*8",  {"rs7900194": "A"}),
        ("*11", {"rs28371685": "T"}),
    ],
    # CYP2D6 from arrays is intrinsically incomplete (no CNV / *5 deletion / hybrids).
    # We call the simple SNP alleles and mark evidence_tier="tentative-no-sv".
    "CYP2D6": [
        ("*4",  {"rs3892097": "A"}),
        ("*10", {"rs1065852": "A"}),
        ("*17", {"rs28371706": "T"}),
        ("*41", {"rs28371725": "A"}),
        ("*3",  {"rs35742686": "del"}),
        ("*6",  {"rs5030655": "del"}),
    ],
    "TPMT": [
        ("*2",  {"rs1800462": "C"}),
        ("*3C", {"rs1142345": "C"}),
        ("*3B", {"rs1800460": "T"}),
        # *3A = *3B + *3C; resolved in array_caller via co-occurrence
    ],
    "DPYD": [
        ("c.1905+1G>A", {"rs3918290": "T"}),
        ("c.1679T>G",   {"rs55886062": "G"}),
        ("c.2846A>T",   {"rs67376798": "T"}),
        ("c.1236G>A",   {"rs56038477": "A"}),
    ],
    "SLCO1B1": [
        ("*5",  {"rs4149056": "C"}),
    ],
    "VKORC1": [
        # Special: report the rs9923231 allele directly (used by warfarin algorithms)
        ("rs9923231", {"rs9923231": "T"}),
    ],
    "UGT1A1": [
        ("*28", {"rs8175347": "TA7"}),     # TA repeat — may be reported as rs3064744
        ("*6",  {"rs4148323": "A"}),
        ("*37", {"rs8175347": "TA8"}),
    ],
    "NUDT15": [
        ("*3",  {"rs116855232": "T"}),
        ("*2",  {"rs746071566": "A"}),
    ],
}


# Phenotype mapping from total activity score (CPIC standard)
# Per-gene because the bins differ.
PHENOTYPE_BINS: dict[str, list[tuple[float, float, str]]] = {
    # (min_inclusive, max_inclusive, phenotype_code)
    "CYP2C19": [
        (0.0, 0.0, "PM"),
        (0.5, 1.0, "IM"),
        (1.5, 2.0, "NM"),
        (2.5, 2.5, "RM"),
        (3.0, 3.5, "UM"),
    ],
    "CYP2C9": [
        (0.0, 0.5, "PM"),
        (1.0, 1.5, "IM"),
        (2.0, 2.0, "NM"),
        (2.5, 3.0, "RM"),
    ],
    "CYP2D6": [
        (0.0, 0.0, "PM"),
        (0.25, 1.0, "IM"),
        (1.25, 2.25, "NM"),
        (2.5, 6.0, "UM"),
    ],
    "TPMT": [
        (0.0, 0.0, "PM"),
        (0.5, 1.0, "IM"),
        (2.0, 2.0, "NM"),
    ],
    "DPYD": [
        (0.0, 0.5, "PM"),
        (1.0, 1.5, "IM"),
        (2.0, 2.0, "NM"),
    ],
    "SLCO1B1": [
        (0.0, 0.0, "PM"),
        (0.5, 1.0, "IM"),
        (2.0, 2.0, "NM"),
    ],
    "UGT1A1": [
        (0.0, 0.0, "PM"),
        (0.5, 1.5, "IM"),
        (2.0, 2.0, "NM"),
    ],
    "NUDT15": [
        (0.0, 0.0, "PM"),
        (0.5, 1.0, "IM"),
        (2.0, 2.0, "NM"),
    ],
}


# Genes for which array-based calls are inherently limited (no SV/CNV support).
ARRAY_LIMITED_GENES: set[str] = {"CYP2D6", "CYP2B6", "CYP2A6", "GSTM1"}
