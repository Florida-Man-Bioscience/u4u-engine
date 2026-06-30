"""GLP-1 / incretin class integration into the tracking engine.

Covers the three things that make GLP-1 a first-class, evidence-backed peptide
in the prediction pipeline:

  1. The GLP-1 panels expose class-qualified biomarker names so their large
     effects bind to GLP-1-tuned magnitudes and grade-A evidence.
  2. That evidence binds through derive_prior (grade A, tight relative_sd).
  3. It does NOT bleed into the generic metabolic markers shared by the much
     weaker peptides (AOD-9604, MOTS-c).
"""
import random

import pytest

from engine.peptides import get_biomarker_panel
from engine.tracking import evidence
from engine.tracking.biomarker_params import BIOMARKER_PARAMS
from engine.tracking.genetics import derive_prior, generate_synthetic_profile

GLP1_PEPTIDES = ["Semaglutide", "Tirzepatide", "Liraglutide"]
QUALIFIED = "Body weight (GLP-1 RA)"


@pytest.mark.parametrize("peptide", GLP1_PEPTIDES)
def test_glp1_panels_use_class_qualified_markers(peptide):
    panel = get_biomarker_panel(peptide)
    assert panel is not None
    names = {m.name for m in panel.measurements}
    # Class-qualified (so they bind to GLP-1 magnitudes / evidence)…
    assert "Body weight (GLP-1 RA)" in names
    assert "HbA1c (GLP-1 RA)" in names
    # …and the GLP-1-exclusive markers kept their plain names.
    assert "Fasting plasma glucose" in names
    assert "Resting heart rate" in names
    # The generic shared markers must NOT appear under their bare names here.
    assert "Body weight" not in names
    assert "HbA1c" not in names


def test_glp1_biomarker_params_have_class_magnitudes():
    # Weight loss far exceeds the generic AOD-9604 "Body weight" (-0.04).
    assert BIOMARKER_PARAMS["Body weight (GLP-1 RA)"].max_pct_change == pytest.approx(-0.13)
    # Generic "Body weight" stores a small magnitude (+0.04; its sign is applied
    # from the panel direction at use-time) — far smaller than the GLP-1 value.
    assert abs(BIOMARKER_PARAMS["Body weight"].max_pct_change) == pytest.approx(0.04)
    assert BIOMARKER_PARAMS["HbA1c (GLP-1 RA)"].max_pct_change == pytest.approx(-0.18)
    # GLP-1-exclusive markers are present so they aren't generic fallbacks.
    for k in ("Fasting plasma glucose", "Serum lipase", "Resting heart rate"):
        assert k in BIOMARKER_PARAMS


def test_glp1_evidence_is_grade_a():
    ev = evidence.evidence_for("Body weight (GLP-1 RA)")
    assert ev is not None and ev.grade == "A"
    assert ev.relative_sd == pytest.approx(0.10)
    assert ev.citations  # >= 1 verified citation
    hba1c = evidence.evidence_for("HbA1c (GLP-1 RA)")
    assert hba1c is not None and hba1c.grade == "A"


def test_glp1_grade_a_binds_through_derive_prior():
    profile = generate_synthetic_profile(random.Random(7))
    prior = derive_prior(
        profile, "Semaglutide", expected_pct=-0.13, biomarker_name="Body weight (GLP-1 RA)"
    )
    assert prior.evidence_grade == "A"
    assert prior.panel_rel_sd == pytest.approx(0.10)


def test_glp1_evidence_does_not_bleed_into_generic_markers():
    # The grade-A GLP-1 entries are keyed to class-qualified names, so the
    # generic markers used by AOD-9604 / MOTS-c remain uncited and unchanged.
    assert evidence.evidence_for("Body weight") is None
    assert evidence.evidence_for("HbA1c") is None
    profile = generate_synthetic_profile(random.Random(7))
    aod = derive_prior(
        profile, "AOD-9604", expected_pct=-0.04, biomarker_name="Body weight"
    )
    assert aod.evidence_grade is None
