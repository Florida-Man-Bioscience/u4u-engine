"""
ClinicalTrials.gov v2 client — active and total trial counts per peptide.

No auth required.
"""

from __future__ import annotations

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ._base import cached_fetch

_SOURCE = "clinicaltrials"
_TTL = 60 * 60 * 24  # 24 hours
_TIMEOUT = 10
_BASE = "https://clinicaltrials.gov/api/v2/studies"

# Phases that count as "active" (recruiting or otherwise enrolling).
_ACTIVE_STATUSES = {"RECRUITING", "ENROLLING_BY_INVITATION", "ACTIVE_NOT_RECRUITING"}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _query(search_term: str) -> dict:
    res = requests.get(
        _BASE,
        params={
            "query.term": search_term,
            "pageSize": 25,
            "fields": "NCTId,BriefTitle,OverallStatus,Phase,StartDate",
        },
        timeout=_TIMEOUT,
    )
    res.raise_for_status()
    return res.json()


def _fetch(search_term: str) -> dict:
    payload = _query(search_term)
    studies = payload.get("studies", []) or []
    total = payload.get("totalCount", len(studies))
    active = 0
    latest_phase = None
    latest = []
    for s in studies:
        protocol = s.get("protocolSection") or {}
        status_module = protocol.get("statusModule") or {}
        design_module = protocol.get("designModule") or {}
        ident = protocol.get("identificationModule") or {}
        status = status_module.get("overallStatus")
        phases = design_module.get("phases") or []
        if status in _ACTIVE_STATUSES:
            active += 1
        if phases and not latest_phase:
            latest_phase = phases[-1]
        nct = ident.get("nctId")
        if nct and len(latest) < 5:
            latest.append({
                "nct_id": nct,
                "title": ident.get("briefTitle"),
                "status": status,
                "phase": phases[-1] if phases else None,
                "url": f"https://clinicaltrials.gov/study/{nct}",
            })
    return {
        "search_term": search_term,
        "total_trials": total,
        "active_trials": active,
        "latest_phase": latest_phase,
        "recent_studies": latest,
    }


def fetch_trials(search_term: str) -> dict:
    return cached_fetch(_SOURCE, search_term, _TTL, lambda: _fetch(search_term))
