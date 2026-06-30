"""
Offline unit tests for the Tier A concordance metrics.

These exercise the pure math in ``validation.tier_a.metrics`` and the TSV
loaders in ``validation.tier_a.reference`` — no pipeline, no network. This is
where the correctness of the validation evidence is pinned.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from validation.tier_a.metrics import (
    REF,
    compare_categorical,
    compare_genotypes,
)
from validation.tier_a.reference import (
    load_genotype_truth,
    load_pgx_reference,
)

# ── categorical concordance ────────────────────────────────────────────────

def test_categorical_all_concordant():
    expected = {("S1", "CYP2C19"): "*1/*2", ("S1", "CYP2D6"): "*1/*1"}
    observed = dict(expected)
    r = compare_categorical(observed, expected, case_sensitive=True)
    assert r.n_compared == 2
    assert r.n_concordant == 2
    assert r.concordance_rate == 1.0
    assert r.discordances == []


def test_categorical_counts_discordance_and_per_key():
    expected = {("S1", "CYP2D6"): "*1/*1", ("S2", "CYP2D6"): "*3/*4"}
    observed = {("S1", "CYP2D6"): "*1/*1", ("S2", "CYP2D6"): "*1/*4"}
    r = compare_categorical(observed, expected, case_sensitive=True)
    assert r.n_compared == 2
    assert r.n_concordant == 1
    assert r.concordance_rate == 0.5
    assert r.by_key["CYP2D6"] == (1, 2)
    assert len(r.discordances) == 1
    d = r.discordances[0]
    assert (d.sample, d.expected, d.observed) == ("S2", "*3/*4", "*1/*4")


def test_categorical_missing_observed_is_skipped_not_wrong():
    # pipeline made no call for S1 — must be skipped, not scored as discordant
    expected = {("S1", "CYP2D6"): "*1/*1"}
    observed: dict = {}
    r = compare_categorical(observed, expected)
    assert r.n_compared == 0
    assert r.n_skipped_missing == 1
    assert r.concordance_rate is None  # undefined, not 0.0


def test_categorical_case_insensitive_phenotype():
    expected = {("S1", "CYP2C19"): "PM"}
    observed = {("S1", "CYP2C19"): "pm"}
    r = compare_categorical(observed, expected, case_sensitive=False)
    assert r.concordance_rate == 1.0


def test_categorical_empty_rate_is_none():
    r = compare_categorical({}, {})
    assert r.concordance_rate is None


# ── genotype confusion matrix ──────────────────────────────────────────────

def test_genotype_perfect_detection():
    expected = {"rs1": "0/1", "rs2": "1/1", "rs3": REF}
    observed = {"rs1": "0/1", "rs2": "1/1", "rs3": REF}
    cm = compare_genotypes(observed, expected)
    assert (cm.tp, cm.fp, cm.fn, cm.tn) == (2, 0, 0, 1)
    assert cm.sensitivity == 1.0
    assert cm.specificity == 1.0
    assert cm.precision == 1.0
    assert cm.genotype_concordance == 1.0


def test_genotype_false_negative_missing_call():
    expected = {"rs1": "0/1"}
    observed: dict = {}  # site absent → treated as ref → a miss
    cm = compare_genotypes(observed, expected)
    assert (cm.tp, cm.fn) == (0, 1)
    assert cm.sensitivity == 0.0


def test_genotype_false_positive():
    expected = {"rs1": REF}
    observed = {"rs1": "0/1"}
    cm = compare_genotypes(observed, expected)
    assert (cm.fp, cm.tn) == (1, 0)
    assert cm.precision == 0.0
    assert cm.specificity == 0.0


def test_genotype_detected_but_miscalled_zygosity():
    # variant truly present and detected, but het vs hom-alt disagree
    expected = {"rs1": "0/1"}
    observed = {"rs1": "1/1"}
    cm = compare_genotypes(observed, expected)
    assert cm.tp == 1                  # still a true detection
    assert cm.genotype_mismatch == 1
    assert cm.sensitivity == 1.0
    assert cm.genotype_concordance == 0.0  # but wrong genotype


def test_genotype_empty_rates_are_none():
    cm = compare_genotypes({}, {})
    assert cm.sensitivity is None
    assert cm.specificity is None
    assert cm.precision is None
    assert cm.f1 is None


# ── reference loaders ──────────────────────────────────────────────────────

def test_load_pgx_reference_seed():
    seed = Path("validation/reference/getrm_pgx_seed.tsv")
    calls = load_pgx_reference(seed)
    assert len(calls) >= 4
    na12878 = [c for c in calls if c.sample == "NA12878"]
    genes = {c.gene for c in na12878}
    assert {"CYP2C19", "CYP2D6"} <= genes


def test_load_pgx_reference_skips_comments_and_blank(tmp_path):
    f = tmp_path / "ref.tsv"
    f.write_text(
        "# a comment\n"
        "sample\tgene\tdiplotype\tphenotype\tsource\n"
        "S1\tCYP2D6\t*1/*1\tNM\ttest\n",
        encoding="utf-8",
    )
    calls = load_pgx_reference(f)
    assert len(calls) == 1
    assert calls[0].phenotype == "NM"


def test_load_genotype_truth(tmp_path):
    f = tmp_path / "gt.tsv"
    f.write_text(
        "sample\tsite\tgenotype\n"
        "S1\trs4244285\t0/1\n"
        "S1\trs1\tref\n",
        encoding="utf-8",
    )
    truths = load_genotype_truth(f)
    assert len(truths) == 2
    assert truths[0].site == "rs4244285"


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_pgx_reference(tmp_path / "nope.tsv")
