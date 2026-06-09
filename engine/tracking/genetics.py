"""
engine/tracking/genetics.py
==========================
Synthetic genetic profile generation + peptide-response prior derivation.

The catalog (VARIANT_CATALOG) lists ~25 SNPs with known pharmacogenomically
relevant roles, each annotated with:
  - effect_allele frequency (rough population estimate)
  - per-peptide effect weights (positive = boosts response, negative = drags it)
  - per-genotype effect multiplier (additive over allele dosage)

A "genetic profile" for a patient is a list of GeneticVariant records — one
per catalog SNP — with the sampled genotype and the precomputed peptide
effect contribution.

Aggregating those contributions yields a per-peptide responder score, which
the Bayesian module turns into a prior on the patient's expected % change
from baseline at the panel's expected timeframe.

This is *synthetic* test data — the effect weights are stylised, not pulled
from any GWAS. Real-world deployment would replace VARIANT_CATALOG with a
curated table sourced from PharmGKB / ClinVar.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Literal

Genotype = Literal["hom_ref", "het", "hom_alt"]


@dataclass(frozen=True)
class CatalogEntry:
    """One SNP in the curated catalog."""
    rsid: str
    gene: str
    chromosome: str
    effect_allele: str
    other_allele: str
    eaf: float                                      # effect allele frequency (population avg)
    peptide_effects: dict[str, float]               # peptide_name → effect weight per effect allele
    description: str

    def dosage_for(self, genotype: Genotype) -> int:
        return {"hom_ref": 0, "het": 1, "hom_alt": 2}[genotype]


@dataclass
class GeneticVariant:
    """A patient's genotype at one catalog SNP, with derived effects baked in."""
    rsid: str
    gene: str
    chromosome: str
    genotype: Genotype
    effect_allele: str
    other_allele: str
    dosage: int                                     # 0, 1, or 2 effect alleles
    peptide_effects: dict[str, float]               # already multiplied by dosage
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GeneticProfile:
    """A complete patient profile across the catalog SNPs."""
    variants: list[GeneticVariant] = field(default_factory=list)
    generated_at: str = ""
    source: str = "synthetic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "variants": [v.to_dict() for v in self.variants],
            "generated_at": self.generated_at,
            "source": self.source,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, raw: str) -> "GeneticProfile":
        d = json.loads(raw)
        variants = [
            GeneticVariant(
                rsid=v["rsid"],
                gene=v["gene"],
                chromosome=v["chromosome"],
                genotype=v["genotype"],
                effect_allele=v["effect_allele"],
                other_allele=v["other_allele"],
                dosage=v["dosage"],
                peptide_effects=v.get("peptide_effects", {}),
                description=v.get("description", ""),
            )
            for v in d.get("variants", [])
        ]
        return cls(
            variants=variants,
            generated_at=d.get("generated_at", ""),
            source=d.get("source", "synthetic"),
        )

    def peptide_effect_summary(self, peptide_name: str) -> dict[str, Any]:
        """Aggregate variant contributions for one peptide."""
        contribs = [
            (v, v.peptide_effects.get(peptide_name, 0.0))
            for v in self.variants
        ]
        contribs = [(v, w) for v, w in contribs if w != 0.0]
        total = sum(w for _, w in contribs)
        return {
            "peptide": peptide_name,
            "total_weight": total,
            "n_relevant_variants": len(contribs),
            "contributing_variants": [
                {
                    "rsid": v.rsid,
                    "gene": v.gene,
                    "genotype": v.genotype,
                    "weight": round(w, 4),
                    "description": v.description,
                }
                for v, w in sorted(contribs, key=lambda kw: abs(kw[1]), reverse=True)
            ],
        }


# ── Curated SNP catalog ─────────────────────────────────────────────────────
# Effect weights are stylised. Positive = boosts response to that peptide,
# negative = drags it down. Weights are "per effect allele"; dosage scales.

VARIANT_CATALOG: list[CatalogEntry] = [
    # NOS3 — endothelial nitric oxide, central to BPC-157 / TB-500 vascular repair
    CatalogEntry("rs1799983", "NOS3", "7", "T", "G", 0.35,
        {"BPC-157": 0.18, "TB-500": 0.12, "Thymosin Beta-4": 0.10, "GHK-Cu": 0.05},
        "NOS3 G894T — reduced eNOS activity; lower NO; dampens vascular repair"),
    CatalogEntry("rs2070744", "NOS3", "7", "C", "T", 0.40,
        {"BPC-157": 0.15, "TB-500": 0.10, "MOTS-c": 0.06},
        "NOS3 -786T>C — promoter variant; affects eNOS expression"),

    # VEGFA — angiogenesis, repair peptides
    CatalogEntry("rs3025039", "VEGFA", "6", "T", "C", 0.16,
        {"BPC-157": 0.20, "TB-500": 0.18, "Thymosin Beta-4": 0.15, "GHK-Cu": 0.08},
        "VEGFA +936C>T — reduced VEGF expression; weaker angiogenic response"),
    CatalogEntry("rs699947", "VEGFA", "6", "A", "C", 0.50,
        {"BPC-157": 0.12, "TB-500": 0.10, "Thymosin Beta-4": 0.10},
        "VEGFA -2578C>A — promoter; A allele higher VEGF"),

    # COL1A1 — collagen synthesis, GHK-Cu / wound healing
    CatalogEntry("rs1800012", "COL1A1", "17", "T", "G", 0.18,
        {"GHK-Cu": 0.22, "BPC-157": 0.08, "TB-500": 0.10},
        "COL1A1 Sp1 binding site polymorphism — altered collagen ratio"),
    CatalogEntry("rs1107946", "COL1A1", "17", "A", "C", 0.20,
        {"GHK-Cu": 0.15, "TB-500": 0.08},
        "COL1A1 promoter — affects type I collagen expression"),

    # MMP — matrix remodeling
    CatalogEntry("rs1799750", "MMP1", "11", "G", "GG", 0.49,
        {"GHK-Cu": -0.10, "TB-500": 0.08, "BPC-157": 0.06},
        "MMP1 -1607 1G/2G — 2G higher transcription; faster ECM turnover"),

    # IL6 — inflammation axis
    CatalogEntry("rs1800795", "IL6", "7", "C", "G", 0.42,
        {"BPC-157": 0.14, "KPV": 0.20, "Thymosin Alpha-1": 0.12,
         "LL-37": 0.10, "Selank": 0.06},
        "IL6 -174G>C — C allele lower IL-6; better anti-inflammatory response"),

    # TNF — TNF-α inflammation
    CatalogEntry("rs1800629", "TNF", "6", "A", "G", 0.18,
        {"BPC-157": -0.10, "KPV": -0.12, "Thymosin Alpha-1": -0.08},
        "TNF -308G>A — A allele higher TNF-α; harder to suppress inflammation"),

    # IL10 — anti-inflammatory
    CatalogEntry("rs1800896", "IL10", "1", "G", "A", 0.45,
        {"KPV": 0.15, "Thymosin Alpha-1": 0.10, "BPC-157": 0.08},
        "IL10 -1082G>A — G allele higher IL-10; stronger anti-inflammatory tone"),

    # MTHFR — methylation; broad relevance
    CatalogEntry("rs1801133", "MTHFR", "1", "T", "C", 0.30,
        {"BPC-157": -0.05, "Epitalon": -0.08, "Selank": -0.05, "Semax": -0.05},
        "MTHFR C677T — reduced enzyme activity; methylation drag"),

    # IGF axis — GH peptides
    CatalogEntry("rs2854744", "IGFBP3", "7", "A", "C", 0.45,
        {"CJC-1295": 0.18, "Ipamorelin": 0.16, "GHRP-2": 0.12, "MGF": 0.10},
        "IGFBP3 -202A>C — affects IGFBP-3 levels; modulates IGF-1 bioavailability"),
    CatalogEntry("rs6214", "IGF1", "12", "T", "C", 0.42,
        {"CJC-1295": 0.20, "Ipamorelin": 0.18, "GHRP-2": 0.14, "MGF": 0.16},
        "IGF1 — affects circulating IGF-1; stronger GH-axis response"),
    CatalogEntry("rs6220", "IGF1", "12", "G", "A", 0.36,
        {"CJC-1295": 0.10, "Ipamorelin": 0.08, "MGF": 0.10},
        "IGF1 3'UTR — modulates IGF-1 stability"),
    CatalogEntry("rs6184", "GHR", "5", "G", "A", 0.22,
        {"CJC-1295": 0.15, "Ipamorelin": 0.15, "GHRP-2": 0.18, "AOD-9604": 0.05},
        "GHR exon 3 deletion proxy — GH receptor sensitivity"),

    # Metabolic / insulin axis
    CatalogEntry("rs1801282", "PPARG", "3", "G", "C", 0.12,
        {"MOTS-c": 0.22, "AOD-9604": 0.18},
        "PPARG Pro12Ala — Ala allele improved insulin sensitivity"),
    CatalogEntry("rs7903146", "TCF7L2", "10", "T", "C", 0.28,
        {"MOTS-c": -0.18, "AOD-9604": -0.12},
        "TCF7L2 T2D risk allele — impaired glucose homeostasis"),
    CatalogEntry("rs9939609", "FTO", "16", "A", "T", 0.40,
        {"AOD-9604": -0.18, "MOTS-c": -0.10},
        "FTO obesity risk allele — harder fat loss"),
    CatalogEntry("rs17782313", "MC4R", "18", "C", "T", 0.21,
        {"Melanotan II": 0.18, "AOD-9604": -0.10},
        "MC4R near-gene — melanocortin pathway"),

    # Vitamin D / LL-37
    CatalogEntry("rs2228570", "VDR", "12", "C", "T", 0.45,
        {"LL-37": 0.20, "Thymosin Alpha-1": 0.08},
        "VDR FokI — vitamin D receptor activity; cathelicidin induction"),

    # Neuro / cognitive peptides
    CatalogEntry("rs6265", "BDNF", "11", "T", "C", 0.20,
        {"Semax": 0.22, "Selank": 0.18, "Dihexa": 0.20, "DSIP": 0.08},
        "BDNF Val66Met — reduced activity-dependent BDNF secretion"),
    CatalogEntry("rs1800497", "ANKK1", "11", "A", "G", 0.30,
        {"Semax": 0.10, "Selank": 0.12, "DSIP": 0.08},
        "ANKK1/DRD2 TaqIA — dopamine receptor density"),

    # Immune / TLR
    CatalogEntry("rs5743836", "TLR9", "3", "C", "T", 0.18,
        {"Thymosin Alpha-1": 0.20, "LL-37": 0.08},
        "TLR9 -1237T>C — TLR9 expression; key for thymosin α-1 mechanism"),

    # Reproductive
    CatalogEntry("rs10835638", "FSHB", "11", "T", "G", 0.16,
        {"Kisspeptin": 0.18},
        "FSHB promoter — FSH levels and gonadotropin response"),

    # Sleep / circadian
    CatalogEntry("rs1801260", "CLOCK", "4", "G", "A", 0.30,
        {"DSIP": 0.18, "Epitalon": 0.20, "Selank": 0.05},
        "CLOCK 3111T>C — circadian preference and sleep architecture"),

    # Oxidative stress (broad)
    CatalogEntry("rs4880", "SOD2", "6", "C", "T", 0.50,
        {"Epitalon": 0.12, "MOTS-c": 0.08, "BPC-157": 0.05, "GHK-Cu": 0.06},
        "SOD2 Ala16Val — mitochondrial superoxide dismutase activity"),
]


# ── Profile generation ──────────────────────────────────────────────────────

def _sample_genotype(rng: random.Random, eaf: float) -> Genotype:
    """Sample under Hardy-Weinberg equilibrium given effect allele frequency."""
    p = eaf
    q = 1 - p
    r = rng.random()
    # hom_alt prob = p², het prob = 2pq, hom_ref prob = q²
    if r < p * p:
        return "hom_alt"
    if r < p * p + 2 * p * q:
        return "het"
    return "hom_ref"


def generate_synthetic_profile(
    rng: random.Random,
    *,
    catalog: Iterable[CatalogEntry] | None = None,
    source: str = "synthetic",
) -> GeneticProfile:
    """Sample a genotype at every catalog SNP and bake the peptide effects."""
    entries = list(catalog) if catalog is not None else VARIANT_CATALOG
    variants: list[GeneticVariant] = []
    for entry in entries:
        gt = _sample_genotype(rng, entry.eaf)
        dosage = entry.dosage_for(gt)
        scaled = {pep: round(w * dosage, 4) for pep, w in entry.peptide_effects.items()}
        variants.append(GeneticVariant(
            rsid=entry.rsid,
            gene=entry.gene,
            chromosome=entry.chromosome,
            genotype=gt,
            effect_allele=entry.effect_allele,
            other_allele=entry.other_allele,
            dosage=dosage,
            peptide_effects=scaled,
            description=entry.description,
        ))
    return GeneticProfile(
        variants=variants,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        source=source,
    )


# ── Prior derivation ────────────────────────────────────────────────────────

# Maps the dimensionless aggregate weight from a profile into a prior mean
# on percent-change (as a fraction, e.g. 0.30 = +30%). The squashing keeps
# extreme genetic profiles from claiming silly effect sizes.

PRIOR_SCALE = 0.4      # how much aggregate weight maps to fraction change
PRIOR_BASE_SD = 0.18   # baseline uncertainty when no relevant variants
PRIOR_INFO_SD = 0.04   # per-relevant-variant reduction (additive precision)


@dataclass(frozen=True)
class GeneticPrior:
    """Prior on the patient's percent-change response to a peptide."""
    peptide: str
    mean_pct_change: float          # e.g. 0.30 = +30%
    sd_pct_change: float            # 1σ on the prior
    n_relevant_variants: int
    aggregate_weight: float         # raw weight before squashing

    def to_dict(self) -> dict[str, Any]:
        return {
            "peptide": self.peptide,
            "mean_pct_change": round(self.mean_pct_change, 4),
            "sd_pct_change": round(self.sd_pct_change, 4),
            "n_relevant_variants": self.n_relevant_variants,
            "aggregate_weight": round(self.aggregate_weight, 4),
        }


def derive_prior(profile: GeneticProfile, peptide_name: str) -> GeneticPrior:
    """Aggregate variant weights and squash into a Normal prior on % change.

    Uses a tanh squash so total weights ~ |x|>>1 saturate.
    Variance shrinks with more relevant variants (more information).
    """
    summary = profile.peptide_effect_summary(peptide_name)
    n = summary["n_relevant_variants"]
    w = summary["total_weight"]
    mean = PRIOR_SCALE * math.tanh(w)
    # Precision adds per-variant; floor SD at PRIOR_INFO_SD.
    sd = max(PRIOR_INFO_SD,
             PRIOR_BASE_SD / math.sqrt(1 + 0.5 * n))
    return GeneticPrior(
        peptide=peptide_name,
        mean_pct_change=mean,
        sd_pct_change=sd,
        n_relevant_variants=n,
        aggregate_weight=w,
    )


def responder_strength_from_profile(profile: GeneticProfile, peptide_name: str) -> float:
    """Convert prior mean into the responder-strength scalar used by the
    measurement seeder. Centered at 1.0 (= average responder)."""
    prior = derive_prior(profile, peptide_name)
    return max(0.0, 1.0 + 1.8 * prior.mean_pct_change)
