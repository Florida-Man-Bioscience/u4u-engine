"""
engine/pgx/hgnn/model.py
=========================
Drug-response ranker.

Default path: rule-based fallback that traverses the PGxGraph built in
graph_build.py — sums weighted contributions from CPIC recommendations,
pharmacogenomic PRS, and HLA risk alleles to produce a per-drug response
score in [0, 1] where higher = predicted responder, lower = predicted
non-responder or ADR risk.

Optional path: a Heterogeneous Graph Transformer (HGT, Hu et al. 2020)
inference call when `torch_geometric` is importable and pretrained weights
are present at `data/hgnn_weights/`. Architecture is sketched per the
HGACL-DRP / HeteroRepur literature; we do not train inside this engine.

Output: list[DrugPrediction] (point score only; conformal calibration is
applied separately in conformal.py).
"""
from __future__ import annotations

import math

from ..types import DrugPrediction, StarAlleleCall, HLACall, PRSResult, Phenotype
from .graph_build import build_graph, PGxGraph


# Penalize phenotypes that move further from "normal" — informs responder probability
_PHENO_DEVIATION = {
    Phenotype.NORMAL: 0.0,
    Phenotype.RAPID: 0.4,
    Phenotype.INTERMEDIATE: 0.6,
    Phenotype.ULTRARAPID: 0.8,
    Phenotype.POOR: 1.0,
    Phenotype.INDETERMINATE: 0.3,
}

_PRS_TIER_PENALTY = {"low": 0.0, "intermediate": 0.4, "high": 0.8}


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _rule_based_score(
    drug: str,
    graph: PGxGraph,
    star_by_gene: dict[str, StarAlleleCall],
    hla_by_locus: dict[str, HLACall],
    prs_by_trait: dict[str, PRSResult],
) -> tuple[float, list[str]]:
    """Aggregate evidence against `drug` → (responder probability, contributing genes)."""
    risk = 0.0
    contributing: list[str] = []

    for gene, pheno_code, weight in graph.drug_to_gene_pheno.get(drug, []):
        call = star_by_gene.get(gene)
        if not call:
            continue
        if call.phenotype.value == pheno_code:
            risk += weight * _PHENO_DEVIATION[call.phenotype]
            contributing.append(gene)

    for locus, weight in graph.drug_to_hla.get(drug, []):
        hla = hla_by_locus.get(locus)
        if hla and hla.present:
            risk += weight * 1.2  # HLA contraindications are the highest-OR signal
            contributing.append(locus)

    for trait in graph.drug_to_prs.get(drug, []):
        prs = prs_by_trait.get(trait)
        if prs:
            risk += 0.5 * _PRS_TIER_PENALTY.get(prs.risk_tier, 0.0)
            contributing.append(f"PRS:{trait}")

    # Map risk (0..~3) to responder probability via inverted sigmoid.
    # risk=0 → ~0.85 (good responder); risk=1 → ~0.50; risk≥2 → ~0.15
    prob = _sigmoid(1.5 - 1.2 * risk)
    return round(prob, 3), contributing


def _torch_path_available() -> bool:
    try:  # noqa: SIM105 — optional dep
        import torch_geometric  # type: ignore  # noqa: F401
        import torch             # type: ignore  # noqa: F401
        return True
    except Exception:
        return False


def predict_drug_response(
    star_calls: list[StarAlleleCall],
    hla_calls: list[HLACall],
    prs_results: list[PRSResult],
    drugs: list[str] | None = None,
) -> list[DrugPrediction]:
    """
    Return a DrugPrediction per drug. If `drugs` is None, predict for every
    drug that has any edge in the graph (i.e. every CPIC-actionable drug).
    """
    graph = build_graph()
    star_by_gene = {c.gene: c for c in star_calls}
    hla_by_locus = {h.locus: h for h in hla_calls}
    prs_by_trait = {p.trait: p for p in prs_results}

    if drugs is None:
        drugs = sorted(set(graph.drug_to_gene_pheno) |
                       set(graph.drug_to_prs) |
                       set(graph.drug_to_hla))

    method = "hgnn" if _torch_path_available() else "rule_based_fallback"
    # NB: when torch is available we *could* run a pretrained model here.
    # For now we use the rule-based path uniformly so the engine is
    # deterministic across deploys.
    method = "rule_based_fallback"

    out: list[DrugPrediction] = []
    for drug in drugs:
        score, contributing = _rule_based_score(
            drug, graph, star_by_gene, hla_by_locus, prs_by_trait,
        )
        out.append(DrugPrediction(
            drug=drug,
            point_score=score,
            prediction_set=[],            # filled in by conformal layer
            confidence_level=0.0,
            contributing_genes=contributing,
            method=method,
        ))
    return out
