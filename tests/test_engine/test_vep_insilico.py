"""Tests for SIFT/PolyPhen extraction from VEP results (select_insilico)."""
from engine.annotators.vep import select_insilico


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
