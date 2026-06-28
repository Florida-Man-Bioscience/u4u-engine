"""
Offline tests for the GIAB benchmark VCF -> genotype-truth converter.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

# The converter lives under validation/reference/ (not an importable package),
# so load it by path.
_spec = importlib.util.spec_from_file_location(
    "giab_truth_from_vcf",
    Path("validation/reference/giab_truth_from_vcf.py"),
)
giab = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(giab)


# ── normalize_gt ────────────────────────────────────────────────────────────

def test_normalize_gt_het_sorted():
    assert giab.normalize_gt("1/0") == "0/1"
    assert giab.normalize_gt("0/1") == "0/1"


def test_normalize_gt_phased_collapsed():
    assert giab.normalize_gt("1|0") == "0/1"


def test_normalize_gt_homalt():
    assert giab.normalize_gt("1/1") == "1/1"


def test_normalize_gt_homref_is_ref_sentinel():
    assert giab.normalize_gt("0/0") == "ref"


def test_normalize_gt_nocall_is_none():
    assert giab.normalize_gt("./.") is None
    assert giab.normalize_gt(".|.") is None
    assert giab.normalize_gt("./1") is None


def test_normalize_gt_strips_format_suffix():
    # GT is the first colon-delimited subfield
    assert giab.normalize_gt("0/1:35,40:75") == "0/1"


# ── panel parsing + key canonicalization ────────────────────────────────────

def test_load_panel_unifies_chr_prefix():
    panel = giab.load_panel(["chr1:100", "2:200", "# comment", ""])
    assert panel == {"1:100", "2:200"}


# ── extract_truth ───────────────────────────────────────────────────────────

_VCF = """\
##fileformat=VCFv4.2
##contig=<ID=chr1,length=248956422>
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tNA12878
chr1\t100\t.\tA\tG\t50\tPASS\t.\tGT\t0/1
chr1\t200\t.\tC\tT\t50\tPASS\t.\tGT\t1/1
chr1\t300\t.\tG\tA\t50\tPASS\t.\tGT\t0/0
chr1\t400\t.\tT\tC\t50\tPASS\t.\tGT\t./.
"""


def test_extract_truth_no_panel_skips_nocall_keeps_rest():
    rows = giab.extract_truth(_VCF.splitlines(), "NA12878")
    by_site = {site: gt for _, site, gt in rows}
    assert by_site["1:100"] == "0/1"
    assert by_site["1:200"] == "1/1"
    assert by_site["1:300"] == "ref"   # 0/0 recorded as ref
    assert "1:400" not in by_site      # no-call skipped


def test_extract_truth_with_panel_emits_ref_for_absent_sites():
    panel = {"1:100", "1:999"}  # 999 not in the VCF
    rows = giab.extract_truth(_VCF.splitlines(), "NA12878", panel)
    by_site = {site: gt for _, site, gt in rows}
    assert by_site["1:100"] == "0/1"
    assert by_site["1:999"] == "ref"   # absent panel site -> confident ref
    assert "1:200" not in by_site      # outside panel, excluded


def test_extract_truth_labels_sample():
    rows = giab.extract_truth(_VCF.splitlines(), "MYSAMPLE")
    assert all(s == "MYSAMPLE" for s, _, _ in rows)


def test_extract_truth_roundtrips_into_loader(tmp_path):
    """The converter output must load cleanly via the harness loader."""
    rows = giab.extract_truth(_VCF.splitlines(), "NA12878")
    out = tmp_path / "giab_genotypes.tsv"
    out.write_text(
        "sample\tsite\tgenotype\n"
        + "\n".join(f"{s}\t{site}\t{gt}" for s, site, gt in rows) + "\n",
        encoding="utf-8",
    )
    from validation.tier_a.reference import load_genotype_truth
    truths = load_genotype_truth(out)
    assert {t.site for t in truths} == {"1:100", "1:200", "1:300"}
