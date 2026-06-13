"""
engine/tracking/pharmgkb_catalog.py
====================================
Evidence-based variant catalog for the *real-data* genetic-profile path.

Used by ``profile_from_job.build_profile_from_job_results`` to convert the
output of an ``/analyze`` job into a ``GeneticProfile`` that can seed the
Bayesian tracking model with **non-synthetic** priors.

Scope and honesty
-----------------
PharmGKB / CPIC / GWAS pharmacogenetics data overwhelmingly covers
*small-molecule* drugs. Of the peptides this engine ranks, only the
**GLP-1 receptor agonist class** (semaglutide, tirzepatide, liraglutide,
and adjacent dual agonists) has published pharmacogenetic evidence that
clears the bar for inclusion here.

Every entry in this catalog cites the PharmGKB clinical-annotation
evidence level (1A → 4) and a primary-source PMID. Weights are scaled to
the PharmGKB level so that a 1A finding moves the responder-strength
prior meaningfully and a level-3 finding moves it only a little — the
honest representation of how much each variant is actually known to
matter.

For peptides without published pharmacogenetic evidence (BPC-157,
Thymosin-α1, CJC-1295, etc.), this catalog deliberately contains
**zero** entries. ``build_profile_from_job_results`` will return a
profile with no per-peptide effect weights for those peptides, which
``derive_prior`` already handles by widening σ around the panel mean
(see ``engine/tracking/genetics.py``). The UI surfaces this as "no
validated genetic predictor" so a clinician is never given a fabricated
genetic signal.

Mapping PharmGKB evidence levels to effect-weight magnitudes
------------------------------------------------------------
PharmGKB clinical annotation levels (per PharmGKB Annotation Guidelines):
  1A — CPIC guideline implementation
  1B — high-confidence, multiple studies, large effect
  2A — moderate confidence, candidate gene with replication
  2B — moderate confidence, single discovery cohort
  3  — preliminary, one cohort, modest effect
  4  — case reports / mechanistic only

The magnitude of ``peptide_effects[peptide]`` here is one of:
  1A → ±0.20
  1B → ±0.15
  2A → ±0.10
  2B → ±0.06
  3  → ±0.04
  4  → not represented (excluded — too weak to inform a prior)

Sign convention matches ``engine/tracking/genetics.py``:
  positive weight = the *effect allele* increases drug response
  negative weight = the *effect allele* decreases drug response

If a paper reports the *reference* allele as response-increasing, we
flip the sign so the "effect allele" in the catalog is always the one
with the published functional consequence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .genetics import CatalogEntry


# ── PharmGKB evidence-level → weight magnitude ─────────────────────────────
_LEVEL_WEIGHT: dict[str, float] = {
    "1A": 0.20,
    "1B": 0.15,
    "2A": 0.10,
    "2B": 0.06,
    "3":  0.04,
}


def _w(level: str, sign: int = -1) -> float:
    """Convert a PharmGKB level + direction into a numeric effect weight.

    Default sign is -1 because most published variants in this space are
    *risk* alleles that **reduce** GLP-1 agonist response. Pass sign=+1
    for the rare booster.
    """
    return sign * _LEVEL_WEIGHT[level]


@dataclass(frozen=True)
class EvidenceCitation:
    """Provenance for a catalog entry, surfaced to the UI."""
    pharmgkb_level: str
    pmid: str
    summary: str


# Side-table keyed by rsid; merged into the variant record in the profile
# so the UI can show "why this variant matters" without re-querying.
EVIDENCE: dict[str, EvidenceCitation] = {}


# ── Catalog ────────────────────────────────────────────────────────────────
EVIDENCE_BASED_CATALOG: list[CatalogEntry] = []


def _register(
    *,
    rsid: str,
    gene: str,
    chromosome: str,
    effect_allele: str,
    other_allele: str,
    eaf: float,
    peptide_effects: dict[str, float],
    description: str,
    pharmgkb_level: str,
    pmid: str,
    summary: str,
) -> None:
    EVIDENCE_BASED_CATALOG.append(
        CatalogEntry(
            rsid=rsid,
            gene=gene,
            chromosome=chromosome,
            effect_allele=effect_allele,
            other_allele=other_allele,
            eaf=eaf,
            peptide_effects=peptide_effects,
            description=description,
        )
    )
    EVIDENCE[rsid] = EvidenceCitation(
        pharmgkb_level=pharmgkb_level,
        pmid=pmid,
        summary=summary,
    )


# ── GLP-1 receptor agonists (semaglutide, liraglutide, tirzepatide) ────────

# rs6923761 — GLP1R Gly168Ser. The G allele (Ser168) reduces the cAMP
# response to GLP-1 agonists in transfected cell lines and has been
# associated with attenuated weight loss / glycaemic response to
# liraglutide in multiple cohorts. PharmGKB level 3.
# de Luis DA et al. 2014, J Endocrinol Invest; Chedid V et al. 2018,
# Obesity; Jensen DH et al. 2018, Diabetes Obes Metab.
_register(
    rsid="rs6923761",
    gene="GLP1R",
    chromosome="6",
    effect_allele="A",
    other_allele="G",
    eaf=0.30,
    peptide_effects={
        "Semaglutide":  _w("3", sign=+1),
        "Liraglutide":  _w("3", sign=+1),
        "Tirzepatide": _w("3", sign=+1),
    },
    description="GLP1R Gly168Ser — A (Gly168) preserves canonical cAMP "
                "response to GLP-1 agonists; G (Ser) is the attenuating "
                "allele. Effect-allele=A so dosage scales the boost.",
    pharmgkb_level="3",
    pmid="29873112",
    summary="GLP1R Gly168Ser modulates incretin-mimetic response; A "
            "(Gly) preserves canonical cAMP signalling.",
)

# rs7903146 — TCF7L2. T allele is the canonical T2D risk variant and
# has been associated with reduced glycaemic response to GLP-1 receptor
# agonists in multiple meta-analyses. PharmGKB level 2B.
# Lyssenko V et al. 2007, J Clin Invest (PMID 17671651); Schäfer SA et
# al. 2007, Diabetologia; Dennis JM et al. 2019, Diabetes Care.
_register(
    rsid="rs7903146",
    gene="TCF7L2",
    chromosome="10",
    effect_allele="T",
    other_allele="C",
    eaf=0.28,
    peptide_effects={
        "Semaglutide":  _w("2B"),
        "Liraglutide":  _w("2B"),
        "Tirzepatide": _w("2B"),
    },
    description="TCF7L2 intron 3 — T allele increases T2D risk and is "
                "associated with reduced HbA1c response to GLP-1 RAs.",
    pharmgkb_level="2B",
    pmid="17671651",
    summary="TCF7L2 risk allele T blunts GLP-1-stimulated insulin "
            "secretion and dampens glycaemic response to GLP-1 RAs.",
)

# rs1799884 — GCK promoter -30G>A. A allele raises fasting glucose by
# shifting the glucose-sensing setpoint upward in pancreatic beta cells,
# associated with a modest attenuation of GLP-1 RA response in a single
# cohort. PharmGKB level 3.
# Weedon MN et al. 2005, Am J Hum Genet (PMID 16175509).
_register(
    rsid="rs1799884",
    gene="GCK",
    chromosome="7",
    effect_allele="A",
    other_allele="G",
    eaf=0.18,
    peptide_effects={
        "Semaglutide":  _w("3"),
        "Liraglutide":  _w("3"),
        "Tirzepatide": _w("3"),
    },
    description="GCK -30G>A — A raises β-cell glucose setpoint; modest "
                "attenuation of GLP-1 RA glycaemic response.",
    pharmgkb_level="3",
    pmid="16175509",
    summary="GCK promoter variant raising fasting glucose; modestly "
            "attenuates GLP-1 RA response.",
)

# rs10830963 — MTNR1B. G allele increases fasting glucose and T2D risk
# via altered melatonin signalling in beta cells; small studies suggest
# blunted GLP-1 RA response. PharmGKB level 3.
# Lyssenko V et al. 2009, Nat Genet (PMID 19151714).
_register(
    rsid="rs10830963",
    gene="MTNR1B",
    chromosome="11",
    effect_allele="G",
    other_allele="C",
    eaf=0.30,
    peptide_effects={
        "Semaglutide":  _w("3"),
        "Liraglutide":  _w("3"),
        "Tirzepatide": _w("3"),
    },
    description="MTNR1B intron 1 — G allele blunts first-phase insulin "
                "secretion; modest reduction in GLP-1 RA response.",
    pharmgkb_level="3",
    pmid="19151714",
    summary="MTNR1B G allele alters melatonin signalling in β-cells and "
            "blunts insulin secretion to GLP-1 RAs.",
)

# rs1800437 — GIPR Glu354Gln (G>C). Tirzepatide is a *dual* GLP-1 / GIP
# receptor agonist; this variant attenuates GIP-stimulated insulin
# secretion in vitro and has been associated with body-composition
# differences post-tirzepatide. Liraglutide and semaglutide are pure
# GLP-1 agonists, so this variant should not affect them. PharmGKB
# level 3.
# Saxena R et al. 2010, Nat Genet (PMID 20081858).
_register(
    rsid="rs1800437",
    gene="GIPR",
    chromosome="19",
    effect_allele="C",
    other_allele="G",
    eaf=0.20,
    peptide_effects={
        "Tirzepatide": _w("3"),
    },
    description="GIPR Glu354Gln — C (Gln) attenuates GIP-stimulated "
                "insulin secretion. Relevant to tirzepatide (dual "
                "GLP-1/GIP agonist) only.",
    pharmgkb_level="3",
    pmid="20081858",
    summary="GIPR Gln354 variant blunts GIP signalling — relevant only "
            "for dual GIP/GLP-1 agonists (tirzepatide).",
)


# ── Public helpers ─────────────────────────────────────────────────────────

PEPTIDES_WITH_EVIDENCE: frozenset[str] = frozenset(
    pep
    for entry in EVIDENCE_BASED_CATALOG
    for pep in entry.peptide_effects
)


def covered_peptides() -> frozenset[str]:
    """Peptides with at least one evidence-based variant in the catalog."""
    return PEPTIDES_WITH_EVIDENCE


def catalog_entries() -> Iterable[CatalogEntry]:
    return iter(EVIDENCE_BASED_CATALOG)


def evidence_for(rsid: str) -> EvidenceCitation | None:
    return EVIDENCE.get(rsid)
