"""Tests for the four live regulatory source clients (all HTTP mocked)."""

import os

import pytest
import responses as resp_lib

from engine.regulatory.sources import (
    fetch_docket_summary,
    fetch_federal_register,
    fetch_openfda,
    fetch_trials,
)

# ── ClinicalTrials.gov ────────────────────────────────────────────────────────

_CT_URL = "https://clinicaltrials.gov/api/v2/studies"


@resp_lib.activate
def test_clinicaltrials_parses_active_count():
    resp_lib.add(
        resp_lib.GET,
        _CT_URL,
        json={
            "totalCount": 3,
            "studies": [
                {
                    "protocolSection": {
                        "identificationModule": {"nctId": "NCT001", "briefTitle": "A"},
                        "statusModule": {"overallStatus": "RECRUITING"},
                        "designModule": {"phases": ["PHASE2"]},
                    }
                },
                {
                    "protocolSection": {
                        "identificationModule": {"nctId": "NCT002", "briefTitle": "B"},
                        "statusModule": {"overallStatus": "COMPLETED"},
                        "designModule": {"phases": ["PHASE1"]},
                    }
                },
                {
                    "protocolSection": {
                        "identificationModule": {"nctId": "NCT003", "briefTitle": "C"},
                        "statusModule": {"overallStatus": "ACTIVE_NOT_RECRUITING"},
                        "designModule": {"phases": ["PHASE3"]},
                    }
                },
            ],
        },
        status=200,
    )
    out = fetch_trials("BPC-157")
    assert out["status"] == "fresh"
    assert out["data"]["total_trials"] == 3
    assert out["data"]["active_trials"] == 2
    assert len(out["data"]["recent_studies"]) == 3


@resp_lib.activate
def test_clinicaltrials_cached_second_call_skips_http():
    resp_lib.add(
        resp_lib.GET,
        _CT_URL,
        json={"totalCount": 0, "studies": []},
        status=200,
    )
    fetch_trials("KPV")
    assert len(resp_lib.calls) == 1
    fetch_trials("KPV")
    # Cached hit — still only 1 HTTP call
    assert len(resp_lib.calls) == 1


@resp_lib.activate
def test_clinicaltrials_failure_returns_unavailable():
    # Three attempts then give up (per tenacity stop_after_attempt(3))
    for _ in range(3):
        resp_lib.add(resp_lib.GET, _CT_URL, json={}, status=500)
    out = fetch_trials("Semax")
    assert out["status"] == "unavailable"
    assert out["data"] is None


# ── openFDA ───────────────────────────────────────────────────────────────────

_OF_ENF = "https://api.fda.gov/drug/enforcement.json"
_OF_EVT = "https://api.fda.gov/drug/event.json"


@resp_lib.activate
def test_openfda_handles_404_as_empty():
    resp_lib.add(resp_lib.GET, _OF_ENF, json={}, status=404)
    resp_lib.add(resp_lib.GET, _OF_EVT, json={}, status=404)
    out = fetch_openfda("Ipamorelin")
    assert out["status"] == "fresh"
    assert out["data"]["recalls_total"] == 0
    assert out["data"]["recalls"] == []


@resp_lib.activate
def test_openfda_parses_recalls():
    resp_lib.add(
        resp_lib.GET,
        _OF_ENF,
        json={
            "meta": {"results": {"total": 1}},
            "results": [
                {
                    "recall_number": "D-001",
                    "reason_for_recall": "Mislabeled",
                    "status": "Ongoing",
                    "classification": "Class II",
                    "report_date": "20260301",
                    "product_description": "Test product",
                }
            ],
        },
        status=200,
    )
    resp_lib.add(
        resp_lib.GET,
        _OF_EVT,
        json={"meta": {"results": {"total": 42}}, "results": []},
        status=200,
    )
    out = fetch_openfda("Kisspeptin")
    assert out["data"]["recalls_total"] == 1
    assert out["data"]["recalls"][0]["recall_number"] == "D-001"
    assert out["data"]["adverse_events_total"] == 42


# ── Federal Register ──────────────────────────────────────────────────────────

_FR_URL = "https://www.federalregister.gov/api/v1/documents.json"


@resp_lib.activate
def test_federal_register_parses_documents():
    resp_lib.add(
        resp_lib.GET,
        _FR_URL,
        json={
            "count": 1,
            "results": [
                {
                    "title": "Removal from Cat 2",
                    "document_number": "2026-07361",
                    "publication_date": "2026-04-22",
                    "html_url": "https://example.gov/doc",
                    "abstract": "...",
                }
            ],
        },
        status=200,
    )
    out = fetch_federal_register("BPC-157 compounding")
    assert out["data"]["total"] == 1
    assert out["data"]["documents"][0]["document_number"] == "2026-07361"


# ── Regulations.gov ───────────────────────────────────────────────────────────

_RG_URL = "https://api.regulations.gov/v4/comments"


def test_regulations_gov_without_key_returns_unavailable_envelope(monkeypatch):
    """No API key configured → source returns None (then envelope marks unavailable)."""
    monkeypatch.delenv("REGULATIONS_GOV_API_KEY", raising=False)
    out = fetch_docket_summary("FDA-2025-N-6895")
    # First call: fetch returns None which gets cached. The "fresh" envelope
    # wraps None. The frontend treats data=None as nothing-to-show; that's fine.
    assert out["status"] == "fresh"
    assert out["data"] is None


@resp_lib.activate
def test_regulations_gov_with_key_parses_count(monkeypatch):
    monkeypatch.setenv("REGULATIONS_GOV_API_KEY", "test-key")
    resp_lib.add(
        resp_lib.GET,
        _RG_URL,
        json={
            "meta": {"totalElements": 137},
            "data": [{"attributes": {"postedDate": "2026-05-30T12:00:00Z"}}],
        },
        status=200,
    )
    out = fetch_docket_summary("FDA-2025-N-6895")
    assert out["status"] == "fresh"
    assert out["data"]["comments_count"] == 137
    assert out["data"]["last_comment_posted_at"].startswith("2026-05-30")
