"""Tests for the research-update evidence registry (engine/tracking/evidence.py)
and its curator CLI (engine/tracking/evidence_update.py)."""
from __future__ import annotations

import json

import pytest

from engine.tracking import evidence, evidence_update
from engine.tracking.evidence import EvidenceError
from engine.tracking.genetics import derive_prior, generate_synthetic_profile, PANEL_REL_SD


# ── The shipped registry loads and is internally honest ─────────────────────

def test_shipped_registry_loads_and_validates():
    evidence.reset_cache()
    reg = evidence.load_evidence()  # default data/biomarker_evidence.json
    assert reg, "shipped registry should have at least the seeded markers"
    for marker, ev in reg.items():
        # Honesty contract: every entry carries >=1 real citation with a DOI.
        assert ev.citations, f"{marker} has no citations"
        for c in ev.citations:
            assert c.doi, f"{marker} citation missing DOI"
            assert c.to_dict()["url"] == f"https://doi.org/{c.doi}"
        assert ev.grade in {"A", "B", "C", "D"}
        assert 0.0 < ev.relative_sd <= 1.0


def test_igf1_is_evidence_backed_and_tighter_than_default():
    evidence.reset_cache()
    igf = evidence.evidence_for("Serum IGF-1")
    assert igf is not None
    assert igf.grade == "B"
    # Human-RCT-backed → tighter than the flat uncited default.
    assert igf.relative_sd < PANEL_REL_SD
    assert any("nejm" in c.doi.lower() or "10.1056" in c.doi for c in igf.citations)


def test_preclinical_marker_is_wider_than_default():
    evidence.reset_cache()
    vegf = evidence.evidence_for("Serum VEGF")
    assert vegf is not None
    assert vegf.grade == "D"
    # Preclinical-only → honestly wider than the default.
    assert vegf.relative_sd > PANEL_REL_SD


def test_uncited_marker_returns_none():
    evidence.reset_cache()
    # Body weight is in BIOMARKER_PARAMS but deliberately uncited.
    assert evidence.evidence_for("Body weight") is None
    assert evidence.relative_sd_for("Body weight") is None


# ── Wiring into the prior ───────────────────────────────────────────────────

def test_derive_prior_uses_evidence_sd_for_cited_marker():
    profile = generate_synthetic_profile_seeded()
    igf = derive_prior(profile, "CJC-1295", expected_pct=0.55, biomarker_name="Serum IGF-1")
    assert igf.evidence_grade == "B"
    assert igf.panel_rel_sd == pytest.approx(0.15)


def test_derive_prior_falls_back_to_panel_rel_sd_for_uncited():
    profile = generate_synthetic_profile_seeded()
    bw = derive_prior(profile, "AOD-9604", expected_pct=-0.04, biomarker_name="Body weight")
    assert bw.evidence_grade is None
    assert bw.panel_rel_sd == pytest.approx(PANEL_REL_SD)


def generate_synthetic_profile_seeded():
    import random
    return generate_synthetic_profile(random.Random(11))


# ── Validation rejects malformed entries ────────────────────────────────────

def _write(tmp_path, entries):
    p = tmp_path / "ev.json"
    p.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    evidence.reset_cache()
    return p


def test_validation_rejects_bad_grade(tmp_path):
    p = _write(tmp_path, {"X": {"max_pct_change": 0.5, "grade": "Z",
                                "last_reviewed": "2026-01-01",
                                "citations": [{"doi": "10.1/x", "year": 2020}]}})
    with pytest.raises(EvidenceError):
        evidence.load_evidence(p)


def test_validation_rejects_missing_citation(tmp_path):
    p = _write(tmp_path, {"X": {"max_pct_change": 0.5, "grade": "B",
                                "last_reviewed": "2026-01-01", "citations": []}})
    with pytest.raises(EvidenceError):
        evidence.load_evidence(p)


def test_validation_rejects_out_of_range_sd(tmp_path):
    p = _write(tmp_path, {"X": {"max_pct_change": 0.5, "grade": "B",
                                "relative_sd": 1.5, "last_reviewed": "2026-01-01",
                                "citations": [{"doi": "10.1/x", "year": 2020}]}})
    with pytest.raises(EvidenceError):
        evidence.load_evidence(p)


def test_validation_rejects_bad_date(tmp_path):
    p = _write(tmp_path, {"X": {"max_pct_change": 0.5, "grade": "B",
                                "last_reviewed": "not-a-date",
                                "citations": [{"doi": "10.1/x", "year": 2020}]}})
    with pytest.raises(EvidenceError):
        evidence.load_evidence(p)


def test_grade_default_sd_applied_when_omitted(tmp_path):
    p = _write(tmp_path, {"X": {"max_pct_change": 0.5, "grade": "A",
                                "last_reviewed": "2026-01-01",
                                "citations": [{"doi": "10.1/x", "year": 2020}]}})
    reg = evidence.load_evidence(p)
    assert reg["X"].relative_sd == pytest.approx(0.10)  # grade-A default


# ── Curator CLI round-trip ──────────────────────────────────────────────────

def test_cli_set_then_load_roundtrip(tmp_path):
    out = tmp_path / "reg.json"
    rc = evidence_update.main([
        "--out", str(out), "set", "Serum IL-6",
        "--max-pct-change", "-0.45", "--grade", "C",
        "--reviewed", "2026-06-29",
        "--peptides", "Thymosin-Alpha-1",
        "--rationale", "test entry",
        "--citation", "doi=10.9999/test", "title=Test", "authors=Doe",
        "year=2021", "journal=J", "design=RCT", "evidence=human",
    ])
    assert rc == 0
    evidence.reset_cache()
    reg = evidence.load_evidence(out)
    assert "Serum IL-6" in reg
    e = reg["Serum IL-6"]
    assert e.grade == "C"
    assert e.relative_sd == pytest.approx(0.22)  # grade-C default
    assert e.citations[0].doi == "10.9999/test"


def test_cli_set_requires_citation(tmp_path):
    out = tmp_path / "reg.json"
    with pytest.raises(SystemExit):
        evidence_update.main([
            "--out", str(out), "set", "X",
            "--max-pct-change", "0.1", "--grade", "B", "--reviewed", "2026-01-01",
        ])


def test_cli_remove(tmp_path):
    out = tmp_path / "reg.json"
    evidence_update.main([
        "--out", str(out), "set", "X", "--max-pct-change", "0.1", "--grade", "B",
        "--reviewed", "2026-01-01",
        "--citation", "doi=10.1/x", "year=2020",
    ])
    rc = evidence_update.main(["--out", str(out), "remove", "X"])
    assert rc == 0
    evidence.reset_cache()
    assert "X" not in evidence.load_evidence(out)


def test_cli_validate_ok_on_shipped(capsys):
    rc = evidence_update.main(["validate"])
    assert rc == 0
