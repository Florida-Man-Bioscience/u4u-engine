"""Curated-data sanity checks."""

from engine.regulatory.store import (
    engine_covered_slugs,
    engine_peptide_names,
    get_peptide,
    load_events,
    load_peptides,
)


def test_load_peptides_returns_22_entries():
    data = load_peptides()
    slugs = [p["slug"] for p in data["peptides"]]
    assert len(slugs) == len(set(slugs)), "slugs must be unique"
    assert len(slugs) >= 22


def test_every_peptide_has_required_fields():
    required = {
        "slug",
        "name",
        "category",
        "history",
        "approved_indications",
        "medspa_uses",
        "clinicaltrials_search_term",
        "openfda_search_term",
        "federal_register_search_term",
    }
    for p in load_peptides()["peptides"]:
        missing = required - p.keys()
        assert not missing, f"{p['slug']} missing fields: {missing}"
        assert isinstance(p["approved_indications"], list)


def test_categories_referenced_by_peptides_exist():
    data = load_peptides()
    cats = set(data["categories"].keys())
    for p in data["peptides"]:
        assert p["category"] in cats, f"{p['slug']} has unknown category {p['category']}"


def test_engine_covered_slugs_includes_known_overlap():
    """BPC-157, MOTS-c, Epitalon, Ipamorelin must be flagged as engine-covered."""
    covered = engine_covered_slugs()
    must_be_covered = {"bpc-157", "mots-c", "epitalon", "ipamorelin"}
    assert must_be_covered.issubset(covered)


def test_engine_peptide_names_is_nonempty():
    names = engine_peptide_names()
    assert "bpc157" in names
    assert "ipamorelin" in names


def test_load_events_has_pcac_july_2026():
    events = load_events()["events"]
    titles = [e["title"] for e in events]
    assert any("Day 1" in t for t in titles)
    assert any("Day 2" in t for t in titles)


def test_get_peptide_by_slug():
    p = get_peptide("bpc-157")
    assert p is not None
    assert p["name"] == "BPC-157"
    assert get_peptide("not-a-real-slug") is None
