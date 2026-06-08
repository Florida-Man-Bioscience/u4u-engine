"""Aggregator merges curated data with live sources and tolerates failures."""

import responses as resp_lib

from engine.regulatory.aggregator import (
    build_dashboard_payload,
    build_events_payload,
)


def _stub_all_sources_ok():
    resp_lib.add(
        resp_lib.GET,
        "https://clinicaltrials.gov/api/v2/studies",
        json={"totalCount": 0, "studies": []},
        status=200,
    )
    resp_lib.add(
        resp_lib.GET,
        "https://api.fda.gov/drug/enforcement.json",
        json={},
        status=404,
    )
    resp_lib.add(
        resp_lib.GET,
        "https://api.fda.gov/drug/event.json",
        json={},
        status=404,
    )
    resp_lib.add(
        resp_lib.GET,
        "https://www.federalregister.gov/api/v1/documents.json",
        json={"count": 0, "results": []},
        status=200,
    )


def test_payload_without_live_skips_network():
    """include_live=False should never make HTTP calls."""
    with resp_lib.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        payload = build_dashboard_payload(include_live=False)
        assert len(rsps.calls) == 0
    assert len(payload["peptides"]) >= 22
    assert "categories" in payload
    assert payload["stats"]["total_peptides"] == len(payload["peptides"])


@resp_lib.activate
def test_payload_with_live_attaches_envelopes():
    resp_lib.add_passthru("http://does-not-exist")
    _stub_all_sources_ok()
    payload = build_dashboard_payload(include_live=True)
    sample = payload["peptides"][0]
    assert "live" in sample
    for src in ("clinicaltrials", "openfda", "federal_register"):
        assert src in sample["live"]
        assert sample["live"][src]["status"] in {"fresh", "stale", "unavailable"}


@resp_lib.activate
def test_all_sources_down_still_returns_curated():
    """When every live call fails, the curated layer must still render."""
    # No mocks registered → every HTTP call raises ConnectionError → unavailable
    payload = build_dashboard_payload(include_live=True)
    assert len(payload["peptides"]) >= 22
    for p in payload["peptides"]:
        for src in ("clinicaltrials", "openfda", "federal_register"):
            assert p["live"][src]["status"] == "unavailable"
            assert p["live"][src]["data"] is None


def test_engine_covered_flag_set_on_overlap_peptides():
    payload = build_dashboard_payload(include_live=False)
    by_slug = {p["slug"]: p for p in payload["peptides"]}
    assert by_slug["bpc-157"]["engine_covered"] is True
    assert by_slug["ipamorelin"]["engine_covered"] is True
    # Cosmetic peptide that is in PEPTIDE_GENE_MAP but only as engine extra
    assert by_slug["matrixyl"]["engine_covered"] is True
    # Pure dashboard peptide with no engine entry
    assert by_slug["kisspeptin-10"]["engine_covered"] is False


def test_events_payload_includes_curated_events_and_sources(monkeypatch):
    monkeypatch.delenv("REGULATIONS_GOV_API_KEY", raising=False)
    payload = build_events_payload(include_live=False)
    assert len(payload["events"]) >= 10
    assert len(payload["official_sources"]) >= 5
    assert payload["regulations_gov_docket_id"] == "FDA-2025-N-6895"
    assert payload["docket_live"] is None
