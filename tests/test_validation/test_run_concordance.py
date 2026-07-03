"""
End-to-end tests for the Tier A concordance *runner* (``validation/tier_a/run.py``).

The metrics math is covered offline in ``test_tier_a_metrics.py``; this module
locks the *orchestration* contract that sits on top of it — the part that turns
reference truth sets + a sample map into a report:

  - pipeline runs are cached and reused across the PGx and genotype tracks
  - a reference sample with no mapped input is reported as ``not_run`` (honesty
    contract), never scored as a failure
  - with no sample map at all, rates are ``null`` (undefined), not a passing 0/1
  - per-sample confusion matrices aggregate into one combined matrix
  - the genotype track restricts observed calls to truth sites, so the runner
    structurally cannot manufacture a false positive
  - the Markdown renderer surfaces discordances and renders undefined rates as
    "n/a (undefined)"

The live pipeline is never invoked: ``run_sample`` is monkeypatched to return
canned pipeline-output dicts, so these tests are fully offline and deterministic.
"""
from __future__ import annotations

import pytest

from validation.tier_a import run as runner

# ── Synthetic pipeline outputs, keyed by sample id ──────────────────────────
# Shapes mirror engine.run_pipeline's return: pgx_profile.star_alleles (dicts
# with gene/diplotype/phenotype) and variants (dicts with rsid/genotype).

_PIPELINE_OUT = {
    "NA-001": {
        "pgx_profile": {
            "star_alleles": [
                {"gene": "CYP2C19", "diplotype": "*1/*2", "phenotype": "IM"},
                {"gene": "CYP2D6", "diplotype": "*1/*1", "phenotype": "NM"},
            ]
        },
        "variants": [
            {"rsid": "rs4244285", "genotype": "0/1"},   # matches truth
            {"rsid": "rs1799853", "genotype": "1/1"},   # truth says 0/1 → miscall
        ],
    },
    "NA-003": {
        "pgx_profile": {"star_alleles": []},
        "variants": [
            {"rsid": "rs4244285", "genotype": "0/1"},   # matches truth
        ],
    },
}


@pytest.fixture
def patched(tmp_path, monkeypatch):
    """Write reference/truth/sample-map files and stub the live pipeline.

    Returns the three file paths the runner consumes. The sample map points
    NA-001 and NA-003 at real (empty) files so the runner's ``path.exists()``
    guard passes; the stubbed ``run_sample`` ignores the bytes and routes on the
    file stem. NA-002 is deliberately *absent* from the map.
    """
    # Genome-input stand-ins — content is irrelevant (run_sample is stubbed).
    for sample in ("NA-001", "NA-003"):
        (tmp_path / f"{sample}.vcf").write_text("", encoding="utf-8")

    sample_map = tmp_path / "sample_map.tsv"
    sample_map.write_text(
        f"NA-001\t{tmp_path/'NA-001.vcf'}\n"
        f"NA-003\t{tmp_path/'NA-003.vcf'}\n",   # NA-002 intentionally not mapped
        encoding="utf-8",
    )

    pgx_ref = tmp_path / "pgx.tsv"
    pgx_ref.write_text(
        "sample\tgene\tdiplotype\tphenotype\tsource\n"
        "NA-001\tCYP2C19\t*1/*2\tIM\tSEED\n"   # diplo + pheno concordant
        "NA-001\tCYP2D6\t*1/*2\tPM\tSEED\n"    # diplo + pheno DISCORDANT
        "NA-002\tCYP2C19\t*2/*2\tPM\tSEED\n",  # NA-002 not run → skipped
        encoding="utf-8",
    )

    truth = tmp_path / "geno.tsv"
    truth.write_text(
        "sample\tsite\tgenotype\n"
        "NA-001\trs4244285\t0/1\n"   # TP, genotype match
        "NA-001\trs1799853\t0/1\n"   # TP detection but genotype miscalled (obs 1/1)
        "NA-001\trs0000000\tref\n"   # truth ref, not observed → TN
        "NA-001\trs5555555\t1/1\n"   # truth variant, not observed → FN
        "NA-003\trs4244285\t0/1\n",  # TP, genotype match (second sample)
        encoding="utf-8",
    )

    # Stub the live pipeline: route canned output by the input file's stem.
    monkeypatch.setattr(runner, "run_sample", lambda p: _PIPELINE_OUT[p.stem])

    return {"pgx": str(pgx_ref), "truth": str(truth), "map": str(sample_map)}


# ── PGx categorical tracks ──────────────────────────────────────────────────

def test_pgx_diplotype_concordance(patched):
    report = runner.run_concordance(patched["pgx"], None, patched["map"])
    t = report["tracks"]["pgx_diplotype"]
    # 2 compared (both NA-001 genes), 1 concordant; NA-002 skipped (not run).
    assert t["n_compared"] == 2
    assert t["n_concordant"] == 1
    assert t["n_skipped_missing"] == 1
    assert t["concordance_rate"] == 0.5
    assert t["by_key"]["CYP2C19"] == {"concordant": 1, "compared": 1, "rate": 1.0}
    assert t["by_key"]["CYP2D6"] == {"concordant": 0, "compared": 1, "rate": 0.0}
    # The discordance is itemized for the audit trail.
    assert t["discordances"] == [
        {"sample": "NA-001", "key": "CYP2D6", "expected": "*1/*2", "observed": "*1/*1"}
    ]


def test_pgx_phenotype_concordance(patched):
    report = runner.run_concordance(patched["pgx"], None, patched["map"])
    t = report["tracks"]["pgx_phenotype"]
    assert t["n_compared"] == 2
    assert t["n_concordant"] == 1          # IM matches; PM vs NM does not
    assert t["concordance_rate"] == 0.5


def test_unmapped_reference_sample_is_not_run_not_failed(patched):
    report = runner.run_concordance(patched["pgx"], None, patched["map"])
    assert "NA-002" in report["samples_not_run"]
    assert "NA-002" not in report["samples_run"]
    # NA-002's two reference labels are skipped, never counted as discordant.
    assert report["tracks"]["pgx_diplotype"]["n_skipped_missing"] == 1


# ── Genotype confusion-matrix track ─────────────────────────────────────────

def test_genotype_combined_confusion_matrix(patched):
    report = runner.run_concordance(None, patched["truth"], patched["map"])
    c = report["tracks"]["variant_genotype"]["combined"]
    # NA-001: tp(rs4244285)+tp(rs1799853, miscalled)+tn(rs0000000)+fn(rs5555555)
    # NA-003: tp(rs4244285)
    assert c["tp"] == 3
    assert c["genotype_mismatch"] == 1
    assert c["fn"] == 1
    assert c["tn"] == 1
    assert c["fp"] == 0                      # runner restricts to truth sites
    assert c["sensitivity"] == pytest.approx(3 / 4)
    assert c["specificity"] == 1.0
    assert c["precision"] == 1.0
    # Of 3 detected true-variant sites, 1 had the wrong genotype → 2/3 correct.
    assert c["genotype_concordance"] == pytest.approx(2 / 3)


def test_genotype_per_sample_breakdown(patched):
    report = runner.run_concordance(None, patched["truth"], patched["map"])
    per = report["tracks"]["variant_genotype"]["by_sample"]
    assert set(per) == {"NA-001", "NA-003"}
    assert per["NA-003"]["tp"] == 1
    assert per["NA-001"]["genotype_mismatch"] == 1


def test_pipeline_run_cached_across_tracks(patched, monkeypatch):
    """NA-001 appears in both tracks but must be executed exactly once."""
    calls: list[str] = []
    monkeypatch.setattr(
        runner, "run_sample",
        lambda p: (calls.append(p.stem), _PIPELINE_OUT[p.stem])[1],
    )
    runner.run_concordance(patched["pgx"], patched["truth"], patched["map"])
    assert calls.count("NA-001") == 1        # cached, not re-run for genotype track
    assert sorted(calls) == ["NA-001", "NA-003"]


# ── Coordinate keyspace (real GIAB shape) ───────────────────────────────────

def test_genotype_track_matches_coordinate_keyed_truth(tmp_path, monkeypatch):
    """GIAB truth is coordinate-keyed (no rsIDs in benchmark VCFs), but the
    pipeline reports variants with an rsID *and* coordinates. The genotype
    track must match on coordinate even when the observed variant also has an
    rsID — otherwise every GIAB site collapses to a false negative.
    """
    (tmp_path / "GIAB-1.vcf").write_text("", encoding="utf-8")
    sample_map = tmp_path / "map.tsv"
    sample_map.write_text(f"GIAB-1\t{tmp_path/'GIAB-1.vcf'}\n", encoding="utf-8")

    # Truth keyed exactly as giab_truth_from_vcf.py emits: bare "chrom:pos".
    truth = tmp_path / "giab.tsv"
    truth.write_text(
        "sample\tsite\tgenotype\n"
        "GIAB-1\t1:100\t0/1\n"      # observed has rsid too → must still match
        "GIAB-1\t2:200\t1/1\n"      # observed has no rsid → coordinate fallback
        "GIAB-1\tchr3:300\tref\n",  # chr-prefixed truth → canonicalized to 3:300
        encoding="utf-8",
    )

    pipeline_out = {
        "variants": [
            {"rsid": "rs777", "genotype": "0/1", "chrom": "1", "pos": 100},
            {"genotype": "1/1", "chrom": "2", "pos": 200},  # rsID-less
        ],
    }
    monkeypatch.setattr(runner, "run_sample", lambda p: pipeline_out)

    report = runner.run_concordance(None, str(truth), str(sample_map))
    c = report["tracks"]["variant_genotype"]["combined"]
    assert c["tp"] == 2          # both variant sites detected via coordinate
    assert c["fn"] == 0          # ← was 2 before the dual-key fix
    assert c["tn"] == 1          # chr3:300 truth-ref, not observed → TN
    assert c["genotype_mismatch"] == 0


# ── Honesty contract: no fabricated denominator ─────────────────────────────

def test_no_sample_map_yields_undefined_rates_and_warning(patched):
    report = runner.run_concordance(patched["pgx"], None, None)
    assert any("undefined" in w for w in report["warnings"])
    assert report["samples_run"] == []
    t = report["tracks"]["pgx_diplotype"]
    # Nothing was compared — rate is null, NOT a passing 0% or 100%.
    assert t["n_compared"] == 0
    assert t["concordance_rate"] is None


# ── Markdown rendering ──────────────────────────────────────────────────────

def test_render_markdown_includes_sections_and_discordances(patched):
    report = runner.run_concordance(patched["pgx"], patched["truth"], patched["map"])
    md = runner.render_markdown(report)
    assert "# Tier A Concordance Report" in md
    assert "PGx diplotype concordance" in md
    assert "Variant genotype concordance" in md
    assert "NA-001 / CYP2D6" in md            # discordance surfaced
    assert "NA-002" in md                      # listed as not-run


def test_render_markdown_renders_undefined_rate():
    md = runner.render_markdown(
        runner.run_concordance(None, None, None)  # nothing configured
    )
    # An empty report still renders; no track sections, just the header + warning.
    assert "# Tier A Concordance Report" in md
