"""
engine/pgx/types.py
====================
Dataclasses for the pharmacogenomics subsystem.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class Phenotype(str, Enum):
    POOR = "PM"
    INTERMEDIATE = "IM"
    NORMAL = "NM"
    RAPID = "RM"
    ULTRARAPID = "UM"
    INDETERMINATE = "IND"


@dataclass
class StarAlleleCall:
    gene: str
    diplotype: str                       # e.g. "*1/*2"
    activity_score: float | None
    phenotype: Phenotype
    callers_agreed: list[str]            # e.g. ["array_named_allele"] or ["aldy","pypgx"]
    confidence: float                    # 0..1
    evidence_tier: str                   # "definitive" | "tentative-no-sv" | "single-tool"
    raw_calls: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["phenotype"] = self.phenotype.value
        return d


@dataclass
class HLACall:
    locus: str                           # "HLA-B*57:01"
    present: bool
    method: str                          # "tag_snp" | "hla_la"
    tag_rsid: str | None
    risk_drugs: list[str]                # drugs contraindicated when present

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DrugRecommendation:
    drug: str
    gene: str
    phenotype: Phenotype
    recommendation: str                  # e.g. "Avoid codeine; use morphine"
    classification: str                  # "strong" | "moderate" | "optional"
    cpic_guideline_id: str | None
    source: str                          # "CPIC" | "DPWG" | "FDA"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["phenotype"] = self.phenotype.value
        return d


@dataclass
class DrugPrediction:
    """HGNN/rule-based drug response prediction with conformal prediction set."""
    drug: str
    point_score: float                   # 0..1 raw model output (responder probability)
    prediction_set: list[str]            # {"respond","non_respond"}, ["indeterminate"], or ["uncalibrated"]
    confidence_level: float | None       # 0.90 for 90% coverage; None when uncalibrated (no guarantee)
    contributing_genes: list[str]
    method: str                          # "hgnn" | "rule_based_fallback"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PRSResult:
    trait: str                           # e.g. "clopidogrel_htpr"
    score: float                         # raw weighted sum
    percentile: float | None             # vs reference population, if available
    risk_tier: str                       # "low" | "intermediate" | "high"
    n_variants_used: int
    n_variants_expected: int
    drug_context: list[str]              # drugs this PRS informs

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PGxProfile:
    star_alleles: list[StarAlleleCall] = field(default_factory=list)
    hla_calls: list[HLACall] = field(default_factory=list)
    recommendations: list[DrugRecommendation] = field(default_factory=list)
    prs_results: list[PRSResult] = field(default_factory=list)
    drug_predictions: list[DrugPrediction] = field(default_factory=list)
    phenoconversion_notes: list[str] = field(default_factory=list)
    input_path: str = "array"            # "array" | "bam_sr" | "bam_lr"
    summary_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "star_alleles": [s.to_dict() for s in self.star_alleles],
            "hla_calls": [h.to_dict() for h in self.hla_calls],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "prs_results": [p.to_dict() for p in self.prs_results],
            "drug_predictions": [d.to_dict() for d in self.drug_predictions],
            "phenoconversion_notes": list(self.phenoconversion_notes),
            "input_path": self.input_path,
            "summary_text": self.summary_text,
        }
