"""Tests for SIFT/PolyPhen + protein-change extraction from VEP results."""
from engine.annotators.vep import select_insilico, select_protein_change


def test_prefers_mane_select_transcript():
    vep = {"transcript_consequences": [
        {"canonical": 1, "sift_prediction": "tolerated", "polyphen_prediction": "benign"},
        {"flags": ["mane_select"], "sift_prediction": "Deleterious",
         "polyphen_prediction": "Probably_Damaging"},
    ]}
    sift, polyphen = select_insilico(vep)
    assert sift == "deleterious"
    assert polyphen == "probably_damaging"


def test_falls_back_to_canonical():
    vep = {"transcript_consequences": [
        {"canonical": 1, "sift_prediction": "tolerated", "polyphen_prediction": "benign"},
    ]}
    assert select_insilico(vep) == ("tolerated", "benign")


def test_returns_none_when_absent():
    vep = {"transcript_consequences": [{"canonical": 1}]}
    assert select_insilico(vep) == (None, None)


def test_protein_change_extracted():
    vep = {"transcript_consequences": [
        {"flags": ["mane_select"], "gene_symbol": "BRCA1",
         "amino_acids": "R/W", "protein_start": 1699},
    ]}
    pc = select_protein_change(vep)
    assert pc == {"gene": "BRCA1", "protein_pos": 1699, "ref_aa": "R", "alt_aa": "W"}


def test_protein_change_none_for_synonymous():
    vep = {"transcript_consequences": [
        {"canonical": 1, "gene_symbol": "X", "amino_acids": "R", "protein_start": 5},
    ]}
    assert select_protein_change(vep) is None
