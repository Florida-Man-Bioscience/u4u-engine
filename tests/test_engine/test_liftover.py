"""
Tests for engine/liftover.py and the build-handling policy.
"""
from engine.genome_build import detect_build, plan_build_handling
from engine.liftover import lift_coordinate_variants


def _coord(chrom, pos, vtype="coordinate", rsid=None):
    return {"chrom": chrom, "pos": pos, "ref": "A", "alt": "T",
            "rsid": rsid, "variant_type": vtype}


def test_lift_shifts_coordinate_variants():
    def convert(chrom, pos):
        return (chrom, pos + 1000)  # deterministic fake lift

    variants = [_coord("1", 100), _coord("X", 5000)]
    lifted, unmapped = lift_coordinate_variants(variants, convert)
    assert not unmapped
    assert lifted[0]["pos"] == 1100
    assert lifted[1]["pos"] == 6000


def test_lift_passes_through_rsid_only():
    def convert(chrom, pos):
        raise AssertionError("rsid_only variants should not be converted")

    variants = [_coord(None, None, vtype="rsid_only", rsid="rs1")]
    lifted, unmapped = lift_coordinate_variants(variants, convert)
    assert not unmapped
    assert lifted[0]["variant_type"] == "rsid_only"


def test_lift_collects_unmapped():
    def convert(chrom, pos):
        return None  # nothing maps

    variants = [_coord("1", 100)]
    lifted, unmapped = lift_coordinate_variants(variants, convert)
    assert lifted == []
    assert len(unmapped) == 1


_VCF37 = (
    b"##fileformat=VCFv4.2\n##reference=hg19\n"
    b"##contig=<ID=1,length=249250621>\n#CHROM\tPOS\tID\tREF\tALT\n"
)
_VCF38 = (
    b"##fileformat=VCFv4.2\n##reference=GRCh38\n"
    b"##contig=<ID=1,length=248956422>\n#CHROM\tPOS\tID\tREF\tALT\n"
)


def test_plan_grch37_liftover_when_available():
    d = detect_build(_VCF37, "x.vcf")
    plan = plan_build_handling(d, "x.vcf", liftover_available=True)
    assert plan["action"] == "liftover"
    assert plan["from_build"] == "GRCh37"


def test_plan_grch37_reject_when_liftover_unavailable():
    d = detect_build(_VCF37, "x.vcf")
    plan = plan_build_handling(d, "x.vcf", liftover_available=False)
    assert plan["action"] == "reject"
    assert "GRCh38" in plan["message"]


def test_plan_grch38_proceeds():
    d = detect_build(_VCF38, "x.vcf")
    plan = plan_build_handling(d, "x.vcf", liftover_available=True)
    assert plan["action"] == "proceed"
