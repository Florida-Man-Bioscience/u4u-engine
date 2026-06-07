"""
engine/pgx/star_alleles/hla_caller.py
======================================
Tag-SNP based HLA risk-allele detection. Reliable for the CPIC-actionable
set; for full 4-digit typing a BAM-path caller (HLA-LA / OptiType) would
be required.

Tag SNPs are well-documented in the literature; references include:
  - HLA-B*57:01 ↔ rs2395029 (G allele)        — abacavir (Mallal 2008)
  - HLA-B*15:02 ↔ rs10484555 (T allele)       — carbamazepine SJS/TEN (East Asian)
  - HLA-B*58:01 ↔ rs9263726 (T allele)        — allopurinol SJS
  - HLA-A*31:01 ↔ rs1061235 (A allele)        — carbamazepine DRESS
  - HLA-B*13:01 ↔ rs9469003 (C allele)        — dapsone hypersensitivity
  - CYP2C9*3 + HLA-B*15:02 ↔ phenytoin risk (DPWG 2024)
"""
from __future__ import annotations

from ..types import HLACall

# (locus, tag_rsid, risk_allele_letter, risk_drugs)
HLA_TAG_SNPS: list[tuple[str, str, str, list[str]]] = [
    ("HLA-B*57:01", "rs2395029",  "G", ["abacavir", "flucloxacillin"]),
    ("HLA-B*15:02", "rs10484555", "T", ["carbamazepine", "oxcarbazepine", "phenytoin", "lamotrigine"]),
    ("HLA-B*58:01", "rs9263726",  "T", ["allopurinol"]),
    ("HLA-A*31:01", "rs1061235",  "A", ["carbamazepine"]),
    ("HLA-B*13:01", "rs9469003",  "C", ["dapsone"]),
]


def _has_alt(variant: dict, required: str) -> bool:
    alt = (variant.get("alt") or "").upper()
    if alt == required.upper():
        return True
    # Be permissive when caller reports the ALT as a longer field
    return required.upper() in alt


def call_hla_from_variants(variants: list[dict]) -> list[HLACall]:
    var_by_rsid = {v.get("rsid"): v for v in variants if v.get("rsid")}
    out: list[HLACall] = []
    for locus, tag, allele, drugs in HLA_TAG_SNPS:
        v = var_by_rsid.get(tag)
        present = bool(v and _has_alt(v, allele))
        out.append(HLACall(
            locus=locus,
            present=present,
            method="tag_snp",
            tag_rsid=tag,
            risk_drugs=list(drugs),
        ))
    return out
