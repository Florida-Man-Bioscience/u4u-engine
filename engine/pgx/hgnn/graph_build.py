"""
engine/pgx/hgnn/graph_build.py
================================
Lightweight heterogeneous knowledge graph over the engine's curated PGx
data: genes ↔ phenotypes ↔ drugs ↔ pathways ↔ ADRs. This is the structural
substrate that a graph neural network (HGT / RGCN) would consume; in our
default rule-based fallback, the graph is traversed directly to score
drugs against a patient profile.

For production, replace the seed nodes/edges below with an ingestion of
PrimeKG / Hetionet / SPOKE.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..cpic.recommendations import REC_TABLE, HLA_DRUG_RULES
from ..prs_pgx.scorer import PRS_DEFINITIONS


@dataclass
class PGxGraph:
    # Adjacency: drug → set of (gene, phenotype) keys with rec_severity weight
    drug_to_gene_pheno: dict[str, list[tuple[str, str, float]]] = field(default_factory=dict)
    # Drug → contributing PRS traits (and beta sum)
    drug_to_prs: dict[str, list[str]] = field(default_factory=dict)
    # Drug → HLA contraindications (locus, severity)
    drug_to_hla: dict[str, list[tuple[str, float]]] = field(default_factory=dict)


_SEVERITY = {"strong": 1.0, "moderate": 0.6, "optional": 0.3}


def build_graph() -> PGxGraph:
    g = PGxGraph()

    # Gene/phenotype → drug edges from CPIC recommendation table
    for (gene, phenotype), entries in REC_TABLE.items():
        for drug, classification, _, _ in entries:
            w = _SEVERITY.get(classification, 0.5)
            g.drug_to_gene_pheno.setdefault(drug, []).append((gene, phenotype.value, w))

    # PRS → drug edges
    for trait, spec in PRS_DEFINITIONS.items():
        for drug in spec["drug_context"]:
            g.drug_to_prs.setdefault(drug, []).append(trait)

    # HLA → drug edges
    for locus, rules in HLA_DRUG_RULES.items():
        for drug, classification, _ in rules:
            w = _SEVERITY.get(classification, 0.5)
            g.drug_to_hla.setdefault(drug, []).append((locus, w))

    return g
