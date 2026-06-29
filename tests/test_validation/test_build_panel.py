"""
Offline tests for the panel-site distillation tool
(``validation/reference/build_panel.py``).

The resolution core is exercised with a stub ``resolve_fn`` so no network or
rsID cache is touched. These lock the parts that matter for a trustworthy panel:
correct rsID parsing (inline comments), de-duplication of multi-allele sites,
the honesty contract (unresolved rsIDs reported), genomic sort order, and the
BED coverage report (which never fabricates sites).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# build_panel.py lives under validation/reference/ (not an importable package).
# It must be registered in sys.modules before exec so its @dataclass can resolve
# its (PEP-563 string) annotations when loaded by path.
_spec = importlib.util.spec_from_file_location(
    "build_panel", Path("validation/reference/build_panel.py")
)
bp = importlib.util.module_from_spec(_spec)
sys.modules["build_panel"] = bp
_spec.loader.exec_module(bp)


# ── rsID parsing ────────────────────────────────────────────────────────────

def test_parse_rsid_list_strips_inline_comments_and_dedups():
    lines = [
        "# header comment",
        "rs80357906      # 185delAG — Ashkenazi founder",
        "rs80357382",
        "",
        "rs80357906",          # duplicate → dropped
        "not_an_rsid 123",     # non-rs token → skipped
        "  rs28897696  ",
    ]
    assert bp.parse_rsid_list(lines) == ["rs80357906", "rs80357382", "rs28897696"]


# ── distillation core ───────────────────────────────────────────────────────

def _fake_resolver(mapping):
    """Build a resolve_fn that returns coordinate dicts from {rsid: [(chrom,pos,alt)]}."""
    def resolve(rsids):
        out = []
        for r in rsids:
            for chrom, pos, alt in mapping.get(r, []):
                out.append({"rsid": r, "chrom": chrom, "pos": pos, "alt": alt})
        return out
    return resolve


def test_distill_collapses_multiallele_to_one_site():
    # rs1 has two alt alleles at the same position → one panel site.
    resolve = _fake_resolver({"rs1": [("7", 100, "A"), ("7", 100, "G")]})
    res = bp.distill_panel(["rs1"], resolve)
    assert res.sites == ["7:100"]
    assert res.resolved_rsids == ["rs1"]
    assert res.unresolved_rsids == []


def test_distill_reports_unresolved_rsids():
    resolve = _fake_resolver({"rs1": [("1", 50, "T")]})  # rs2 resolves to nothing
    res = bp.distill_panel(["rs1", "rs2"], resolve)
    assert res.sites == ["1:50"]
    assert res.resolved_rsids == ["rs1"]
    assert res.unresolved_rsids == ["rs2"]
    assert res.resolution_rate == 0.5


def test_distill_drops_rows_without_coordinates():
    def resolve(_):
        return [{"rsid": "rs1", "chrom": "1", "pos": None},   # no pos → dropped
                {"rsid": "rs1", "chrom": "1", "pos": 200}]
    res = bp.distill_panel(["rs1"], resolve)
    assert res.sites == ["1:200"]


def test_distill_sorts_sites_genomically():
    resolve = _fake_resolver({
        "rsX": [("X", 5, "A")],
        "rs10": [("10", 999, "A")],
        "rs2": [("2", 1, "A")],
        "rsMT": [("MT", 7, "A")],
    })
    res = bp.distill_panel(["rsX", "rs10", "rs2", "rsMT"], resolve)
    # chr 2 < 10 < X < MT, numerically not lexically.
    assert res.sites == ["2:1", "10:999", "X:5", "MT:7"]


def test_distill_canonicalizes_chr_prefix():
    resolve = _fake_resolver({"rs1": [("chr7", 100, "A")]})
    res = bp.distill_panel(["rs1"], resolve)
    assert res.sites == ["7:100"]      # 'chr' stripped to match the genotype track


def test_canonical_site_matches_runner_implementation():
    """The inlined _canonical_site must not drift from the runner's, or the
    panel's site keys would stop matching the genotype track's lookup."""
    from validation.tier_a.run import canonical_site
    for s in ("chr1:100", "1:100", "X:5", "rs429358", "chrMT:7", "22:999"):
        assert bp._canonical_site(s) == canonical_site(s)


# ── BED coverage report ─────────────────────────────────────────────────────

_BED = [
    "7\t94389820\t94436227\tCOL1A2",
    "5\t1248147\t1300085\tTERT",
]


def test_parse_bed():
    regions = bp.parse_bed(_BED)
    assert ("7", 94389820, 94436227, "COL1A2") in regions
    assert len(regions) == 2


def test_bed_coverage_counts_and_flags_uncovered():
    regions = bp.parse_bed(_BED)
    sites = ["7:94400000", "5:2000000"]   # one inside COL1A2, one outside TERT
    per_gene, uncovered = bp.bed_coverage(sites, regions)
    assert per_gene["COL1A2"] == 1
    assert per_gene["TERT"] == 0
    assert uncovered == ["TERT"]


def test_bed_coverage_is_half_open_1based():
    regions = bp.parse_bed(["1\t100\t200\tGENE"])
    # start is exclusive for a 1-based pos (start < p <= end): 100 out, 101 in, 200 in, 201 out
    per_gene, _ = bp.bed_coverage(["1:100", "1:101", "1:200", "1:201"], regions)
    assert per_gene["GENE"] == 2


# ── rendering ────────────────────────────────────────────────────────────────

def test_render_panel_file_roundtrips_through_giab_loader():
    """The panel file the tool writes must parse back via the converter's loader."""
    resolve = _fake_resolver({"rs1": [("1", 100, "A")], "rs2": [("2", 200, "A")]})
    res = bp.distill_panel(["rs1", "rs2"], resolve)
    body = bp.render_panel_file(res, ["data/acmg81_rsids.txt"])
    assert body.splitlines()[0].startswith("#")        # provenance header is a comment

    # Load it with the GIAB converter's panel parser (the real consumer).
    _gspec = importlib.util.spec_from_file_location(
        "giab_truth_from_vcf", Path("validation/reference/giab_truth_from_vcf.py")
    )
    giab = importlib.util.module_from_spec(_gspec)
    _gspec.loader.exec_module(giab)
    panel = giab.load_panel(body.splitlines())
    assert panel == {"1:100", "2:200"}                 # comments skipped, sites kept
