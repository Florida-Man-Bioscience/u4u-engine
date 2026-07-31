# Regulatory dashboard per-peptide enrichment (Phase A) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** [`docs/superpowers/specs/2026-07-20-regulatory-peptide-enrichment-design.md`](../specs/2026-07-20-regulatory-peptide-enrichment-design.md) (merged to `main` via PR #118).

**Goal:** Ship Phase A only — PubMed link-out, cited mechanism text, hybrid
curated+FAERS adverse effects, and two popularity sparklines (PubMed
publications/year, Wikipedia pageviews) on each `/regulatory` peptide block,
plus the curation CLI and a pilot-curated set (BPC-157, Semaglutide,
CJC-1295). Phase B (Reddit anecdote feed) is **out of scope for this plan** —
see [Deferred: Phase B](#deferred-phase-b) at the end.

**Architecture:** Extends the existing curated-JSON + live-source + TTL-cache
pattern in `engine/regulatory/` unchanged. Two new source modules
(`pubmed.py`, `wikipedia.py`) follow the `_base.cached_fetch` contract used by
`clinicaltrials.py` / `federal_register.py`. `openfda.py` gains a FAERS
reaction breakdown (extended, not a new module, per the spec). The curated
data model (`data/regulatory/peptides.json`) gains four new per-peptide
fields, validated by a shared `engine/regulatory/curation.py` module used by
both `store.py` (defense-in-depth on every load) and the new curation CLI
`engine/regulatory/curate.py` (mirrors `engine/tracking/evidence_update.py`).
The frontend gets new types, a pure state-selection helper for the
adverse-effects 4-state logic (unit-tested with a newly-added `vitest`
devDependency, since the frontend has no test runner today), and new
`PeptideCard` sub-components.

**Tech Stack:** Python 3.12, `requests` + `tenacity` (already a dependency of
`engine/` via `pyproject.toml` — no new runtime dependency), `responses` for
HTTP mocking in tests, Next.js 15 / React 19 / TypeScript / `recharts`
(already a frontend dependency) for the sparklines, `vitest` (new, dev-only)
for the one pure-logic unit test the spec requires.

## Global constraints

- Dev shell only: every Python command runs as
  `nix develop --command python -m pytest ...`. **Never** run a bare
  `nix develop` (no `--command`) — it opens an interactive shell that hangs
  the session forever.
- The test suite mocks all external HTTP (`responses` library) — no live API
  keys or network calls in CI.
- New regulatory sources live in `engine/regulatory/sources/`, follow the
  `_base.cached_fetch` contract, and degrade to `{"status": "unavailable",
  "data": None}` on any failure rather than raising — a dead upstream must
  never break the page.
- **No new runtime dependency is needed for Phase A.** `requests>=2.31` and
  `tenacity>=8.2` are already installed via `engine/pyproject.toml` (and
  therefore already in the Dockerfile's stage-1 `pip install "engine/[vcf]"`
  — see `Dockerfile` lines ~19–20). `recharts` is already a frontend
  dependency. If any later task in this plan is implemented differently and
  ends up needing a new package, it **must** be added to the Dockerfile's
  hand-maintained pip list too (it does not read `requirements.txt`) — flag
  this explicitly if it comes up, don't silently skip it.
- The curation CLI mirrors `engine/tracking/evidence_update.py`
  (`list`/`show`/`set`/`remove`/`validate`) and **refuses to write an
  uncited `mechanism` or `adverse_effects` entry**.
- **Never conflate `None` and `[]`** for `adverse_effects`: `None` = not yet
  curated (nobody has looked); `[]` = curated, no adverse effects found in
  the reviewed literature. They render different text. Neither ever renders
  as "none reported" or implies safety.
- TDD throughout every task: write the failing test, run it and confirm the
  failure, write the minimal implementation, run it and confirm the pass,
  commit.

---

### Task 1: Curated data model — new fields + shared validation module

**Files:**
- Create: `engine/regulatory/curation.py`
- Modify: `engine/regulatory/store.py` (call validation from `load_peptides`)
- Modify: `data/regulatory/peptides.json` (add 4 new keys to all 26 entries;
  bump `schema_version` 2 → 3)
- Test: `tests/regulatory/test_curation.py`
- Modify: `tests/regulatory/test_store.py` (extend required-fields set)

**Interfaces:**
- Produces:
  - `class CurationError(ValueError)`
  - `validate_mechanism(raw: dict | None, *, slug: str) -> None` — raises
    `CurationError` if `raw` is not `None` and is missing a non-empty `text`
    or `citation`.
  - `validate_adverse_effects(raw: list | None, *, slug: str) -> None` —
    raises `CurationError` if `raw` is not `None` and any entry is missing a
    non-empty `effect` or `citation`.
  - `validate_peptide_curation(peptide: dict) -> None` — calls both of the
    above for one peptide dict.

- [ ] **Step 1: Write the failing test**

```python
# tests/regulatory/test_curation.py
"""Validation for the mechanism / adverse_effects curation fields."""

import pytest

from engine.regulatory.curation import (
    CurationError,
    validate_adverse_effects,
    validate_mechanism,
    validate_peptide_curation,
)


def test_none_mechanism_is_valid():
    validate_mechanism(None, slug="bpc-157")


def test_cited_mechanism_is_valid():
    validate_mechanism(
        {"text": "Stabilizes gastric pentadecapeptide activity.", "citation": "Sikiric et al. 2018, Curr Pharm Des, doi:10.2174/xxx"},
        slug="bpc-157",
    )


def test_mechanism_missing_citation_is_rejected():
    with pytest.raises(CurationError, match="citation"):
        validate_mechanism({"text": "Some mechanism."}, slug="bpc-157")


def test_mechanism_missing_text_is_rejected():
    with pytest.raises(CurationError, match="text"):
        validate_mechanism({"citation": "Smith 2020"}, slug="bpc-157")


def test_none_adverse_effects_is_valid():
    validate_adverse_effects(None, slug="bpc-157")


def test_empty_list_adverse_effects_is_valid():
    """[] means 'curated, none found' — must not be rejected as uncited."""
    validate_adverse_effects([], slug="bpc-157")


def test_adverse_effect_missing_citation_is_rejected():
    with pytest.raises(CurationError, match="citation"):
        validate_adverse_effects([{"effect": "Nausea"}], slug="semaglutide")


def test_adverse_effect_missing_effect_text_is_rejected():
    with pytest.raises(CurationError, match="effect"):
        validate_adverse_effects([{"citation": "Smith 2020"}], slug="semaglutide")


def test_validate_peptide_curation_checks_both_fields():
    with pytest.raises(CurationError):
        validate_peptide_curation({
            "slug": "cjc-1295",
            "mechanism": {"text": "x"},
            "adverse_effects": None,
        })
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/regulatory/test_curation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.regulatory.curation'`.

- [ ] **Step 3: Write minimal implementation**

```python
# engine/regulatory/curation.py
"""
engine/regulatory/curation.py
==============================
Validation for the curated ``mechanism`` / ``adverse_effects`` fields on a
peptide entry (``data/regulatory/peptides.json``).

Honesty contract, same shape as ``engine.tracking.evidence``: an entry is
only valid with a real citation string. ``None`` and ``[]`` are both valid
for ``adverse_effects`` and mean different things —
``None`` = not yet curated, ``[]`` = curated, none found. Neither is an
"uncited" state; only a *present* entry lacking a citation is rejected.

Shared by ``store.load_peptides`` (defense-in-depth on every read) and the
curation CLI ``engine.regulatory.curate`` (the write-time gate).
"""
from __future__ import annotations

from typing import Any


class CurationError(ValueError):
    """Raised when a curated mechanism/adverse_effects entry is malformed."""


def validate_mechanism(raw: dict[str, Any] | None, *, slug: str) -> None:
    if raw is None:
        return
    if not isinstance(raw, dict):
        raise CurationError(f"{slug}: mechanism must be an object or null")
    text = str(raw.get("text", "")).strip()
    citation = str(raw.get("citation", "")).strip()
    if not text:
        raise CurationError(f"{slug}: mechanism is missing its text")
    if not citation:
        raise CurationError(
            f"{slug}: mechanism is missing its citation (honesty contract — "
            f"no curated mechanism without a real, retrieved citation)"
        )


def validate_adverse_effects(raw: list[Any] | None, *, slug: str) -> None:
    if raw is None:
        return
    if not isinstance(raw, list):
        raise CurationError(f"{slug}: adverse_effects must be a list or null")
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise CurationError(f"{slug}: adverse_effects[{i}] must be an object")
        effect = str(entry.get("effect", "")).strip()
        citation = str(entry.get("citation", "")).strip()
        if not effect:
            raise CurationError(f"{slug}: adverse_effects[{i}] is missing its effect text")
        if not citation:
            raise CurationError(
                f"{slug}: adverse_effects[{i}] ({effect!r}) is missing its citation "
                f"(honesty contract — no curated adverse effect without a real, "
                f"retrieved citation)"
            )


def validate_peptide_curation(peptide: dict[str, Any]) -> None:
    slug = peptide.get("slug", "<unknown>")
    validate_mechanism(peptide.get("mechanism"), slug=slug)
    validate_adverse_effects(peptide.get("adverse_effects"), slug=slug)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `nix develop --command python -m pytest tests/regulatory/test_curation.py -v`
Expected: PASS.

- [ ] **Step 5: Wire validation into `store.load_peptides` and extend the JSON schema**

In `engine/regulatory/store.py`, import and call the validator so a hand-edited
JSON file that violates the honesty contract fails loudly at load time
instead of silently reaching the API:

```python
from .curation import validate_peptide_curation

@lru_cache(maxsize=1)
def load_peptides() -> dict:
    """Return the parsed peptides.json contents."""
    with open(_PEPTIDES_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    for p in data["peptides"]:
        validate_peptide_curation(p)
    return data
```

Then add the four new keys to every entry in `data/regulatory/peptides.json`
and bump `schema_version` from `2` to `3`. Do this with a small one-off
script (do not hand-edit 26 entries):

```python
# run once from the repo root, then delete
import json
path = "data/regulatory/peptides.json"
with open(path, encoding="utf-8") as fh:
    doc = json.load(fh)
doc["schema_version"] = 3
for p in doc["peptides"]:
    p.setdefault("pubmed_search_term", p["clinicaltrials_search_term"])
    p.setdefault("wikipedia_title", None)
    p.setdefault("mechanism", None)
    p.setdefault("adverse_effects", None)
with open(path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
```

`pubmed_search_term` defaults to the existing `clinicaltrials_search_term`
value (already a clean drug name per entry — see `bpc-157`'s
`"clinicaltrials_search_term": "BPC-157"`); revisit per-peptide only if a
search term collides with an unrelated PubMed topic during pilot curation.
`wikipedia_title` stays `null` for every peptide until a human confirms the
peptide actually has a Wikipedia article (many of these compounds don't).

`reddit_search_term` (Phase B) is **intentionally not added** in this task —
see [Deferred: Phase B](#deferred-phase-b).

- [ ] **Step 6: Update `test_store.py`'s required-fields set**

```python
# tests/regulatory/test_store.py — extend the `required` set in
# test_every_peptide_has_required_fields with:
        "pubmed_search_term",
        "wikipedia_title",
        "mechanism",
        "adverse_effects",
```

(Presence of the key is what's asserted, not non-null — `wikipedia_title` /
`mechanism` / `adverse_effects` are legitimately `null` for every
not-yet-curated peptide.)

Run: `nix develop --command python -m pytest tests/regulatory/ -v`
Expected: PASS (all regulatory tests, including the untouched pre-existing
ones — confirms the schema change didn't break anything downstream).

- [ ] **Step 7: Commit**

```bash
git add engine/regulatory/curation.py engine/regulatory/store.py \
        data/regulatory/peptides.json tests/regulatory/test_curation.py \
        tests/regulatory/test_store.py
git commit -m "feat(regulatory): add mechanism/adverse_effects/pubmed/wikipedia curation fields"
```

---

### Task 2: PubMed source module — publications per year

**Files:**
- Create: `engine/regulatory/sources/pubmed.py`
- Modify: `engine/regulatory/sources/__init__.py`
- Test: `tests/regulatory/test_sources.py` (extend)

**Interfaces:**
- Produces: `fetch_pubmed(search_term: str) -> dict` — same envelope as
  `fetch_trials`/`fetch_openfda`/`fetch_federal_register`
  (`{"data": ..., "fetched_at": ..., "status": ..., "source": "pubmed"}`).
  `data` shape: `{"search_term": str, "total": int, "years": [{"year": int,
  "count": int}, ...], "pubmed_url": str}`.

**Design notes:** NCBI's `esearch` has no per-year histogram endpoint, so
this loops one `esearch` call per year over a fixed window (last 8 years,
`retmax=0` so NCBI doesn't serialize any UIDs — only the count), mirroring
the existing `NCBI_API_KEY` handling and rate-limit sleep in
`engine/annotators/clinvar.py`.

- [ ] **Step 1: Write the failing test**

```python
# tests/regulatory/test_sources.py — append

from engine.regulatory.sources import fetch_pubmed

_PM_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"


@resp_lib.activate
def test_pubmed_aggregates_per_year_counts():
    for _ in range(8):
        resp_lib.add(
            resp_lib.GET, _PM_ESEARCH,
            json={"esearchresult": {"count": "3"}},
            status=200,
        )
    out = fetch_pubmed("BPC-157")
    assert out["status"] == "fresh"
    assert out["data"]["total"] == 24
    assert len(out["data"]["years"]) == 8
    assert all(y["count"] == 3 for y in out["data"]["years"])
    assert "pubmed.ncbi.nlm.nih.gov" in out["data"]["pubmed_url"]


@resp_lib.activate
def test_pubmed_empty_result_is_fresh_with_zero_counts():
    for _ in range(8):
        resp_lib.add(
            resp_lib.GET, _PM_ESEARCH,
            json={"esearchresult": {"count": "0"}},
            status=200,
        )
    out = fetch_pubmed("Some Obscure Peptide")
    assert out["status"] == "fresh"
    assert out["data"]["total"] == 0
    assert all(y["count"] == 0 for y in out["data"]["years"])


@resp_lib.activate
def test_pubmed_failure_returns_unavailable():
    for _ in range(3):
        resp_lib.add(resp_lib.GET, _PM_ESEARCH, json={}, status=500)
    out = fetch_pubmed("Ipamorelin")
    assert out["status"] == "unavailable"
    assert out["data"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/regulatory/test_sources.py -v -k pubmed`
Expected: FAIL — `ImportError: cannot import name 'fetch_pubmed'`.

- [ ] **Step 3: Write minimal implementation**

```python
# engine/regulatory/sources/pubmed.py
"""
PubMed (NCBI E-utilities) client — publication counts per year for a search
term, used for the "publications/year" popularity sparkline.

Sends NCBI_API_KEY when present (already configured for the ClinVar
annotator — see engine/annotators/clinvar.py — this reuses the same var).
No per-year histogram endpoint exists in esearch, so this issues one
retmax=0 esearch call per year over a fixed lookback window.
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from urllib.parse import quote_plus

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ._base import cached_fetch

_SOURCE = "pubmed"
_TTL = 60 * 60 * 24  # 24 hours
_TIMEOUT = 6
_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_YEARS_BACK = 8
_NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")
_SLEEP = 0.1 if _NCBI_API_KEY else 0.35


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _count_for_year(search_term: str, year: int) -> int:
    time.sleep(_SLEEP)
    params = {
        "db": "pubmed",
        "term": search_term,
        "datetype": "pdat",
        "mindate": str(year),
        "maxdate": str(year),
        "retmax": 0,
        "retmode": "json",
    }
    if _NCBI_API_KEY:
        params["api_key"] = _NCBI_API_KEY
    res = requests.get(_ESEARCH, params=params, timeout=_TIMEOUT)
    res.raise_for_status()
    return int(res.json().get("esearchresult", {}).get("count", 0))


def _fetch(search_term: str) -> dict:
    current_year = datetime.now().year
    years = list(range(current_year - _YEARS_BACK + 1, current_year + 1))
    counts = [{"year": y, "count": _count_for_year(search_term, y)} for y in years]
    return {
        "search_term": search_term,
        "total": sum(c["count"] for c in counts),
        "years": counts,
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/?term={quote_plus(search_term)}",
    }


def fetch_pubmed(search_term: str) -> dict:
    return cached_fetch(_SOURCE, search_term, _TTL, lambda: _fetch(search_term))
```

Update `engine/regulatory/sources/__init__.py`:

```python
"""Live regulatory source clients (Regulations.gov, ClinicalTrials.gov, openFDA, Federal Register, PubMed, Wikipedia)."""

from .clinicaltrials import fetch_trials
from .federal_register import fetch_federal_register
from .openfda import fetch_openfda
from .pubmed import fetch_pubmed
from .regulations_gov import fetch_docket_summary
from .wikipedia import fetch_wikipedia_pageviews

__all__ = [
    "fetch_docket_summary",
    "fetch_trials",
    "fetch_openfda",
    "fetch_federal_register",
    "fetch_pubmed",
    "fetch_wikipedia_pageviews",
]
```

(`fetch_wikipedia_pageviews` doesn't exist yet — Task 3 adds it. Importing it
here now means this step's test run will fail on the `wikipedia` import
until Task 3 lands; if running Task 2 in isolation, temporarily comment out
the `wikipedia` import/export line and finish wiring `__init__.py` at the end
of Task 3 instead.)

- [ ] **Step 4: Run test to verify it passes**

Run: `nix develop --command python -m pytest tests/regulatory/test_sources.py -v -k pubmed`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/regulatory/sources/pubmed.py engine/regulatory/sources/__init__.py \
        tests/regulatory/test_sources.py
git commit -m "feat(regulatory): add PubMed publications-per-year source"
```

---

### Task 3: Wikipedia source module — monthly pageviews

**Files:**
- Create: `engine/regulatory/sources/wikipedia.py`
- Modify: `engine/regulatory/sources/__init__.py` (finish the wiring started
  in Task 2)
- Test: `tests/regulatory/test_sources.py` (extend)

**Interfaces:**
- Produces: `fetch_wikipedia_pageviews(title: str) -> dict` — same envelope
  shape. `data`: `{"title": str, "months": [{"month": "YYYY-MM", "views":
  int}, ...], "total": int}`.
- Env var (new): `U4U_CONTACT_EMAIL` — used to build the descriptive
  `User-Agent` the Wikimedia Analytics API requires by policy. Falls back to
  a placeholder when unset (mirrors the existing
  `U4U_CLUSTER_AUTHENTIK_ISSUER` fallback-placeholder pattern) — the real
  contact address is one of the spec's open items (see
  [Deferred: Phase B](#deferred-phase-b) / open items below), not something
  to invent here.

- [ ] **Step 1: Write the failing test**

```python
# tests/regulatory/test_sources.py — append

from engine.regulatory.sources import fetch_wikipedia_pageviews

_WIKI_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"


@resp_lib.activate
def test_wikipedia_aggregates_monthly_views():
    resp_lib.add(
        resp_lib.GET,
        f"{_WIKI_BASE}/en.wikipedia/all-access/user/Semaglutide/monthly/20240101/20241231",
        json={"items": [
            {"timestamp": "2024010100", "views": 1000},
            {"timestamp": "2024020100", "views": 1500},
        ]},
        status=200,
        match_querystring=False,
    )
    out = fetch_wikipedia_pageviews("Semaglutide")
    assert out["status"] == "fresh"
    assert out["data"]["total"] == 2500
    assert out["data"]["months"][0] == {"month": "2024-01", "views": 1000}


@resp_lib.activate
def test_wikipedia_no_article_returns_empty_not_failure():
    resp_lib.add(
        resp_lib.GET,
        f"{_WIKI_BASE}/en.wikipedia/all-access/user/Obscure-Peptide-XYZ/monthly/20240101/20241231",
        json={"type": "https://mediawiki.org/wiki/HyperSwitch/errors/not_found"},
        status=404,
        match_querystring=False,
    )
    out = fetch_wikipedia_pageviews("Obscure-Peptide-XYZ")
    assert out["status"] == "fresh"
    assert out["data"]["total"] == 0
    assert out["data"]["months"] == []


@resp_lib.activate
def test_wikipedia_failure_returns_unavailable():
    for _ in range(3):
        resp_lib.add(
            resp_lib.GET,
            f"{_WIKI_BASE}/en.wikipedia/all-access/user/BPC-157/monthly/20240101/20241231",
            json={},
            status=500,
            match_querystring=False,
        )
    out = fetch_wikipedia_pageviews("BPC-157")
    assert out["status"] == "unavailable"
    assert out["data"] is None
```

Note: the exact date-range segment of the URL (`.../monthly/20240101/20241231`)
depends on "now" at test-run time. Rather than hardcode it, register the
mock with `responses.matchers` on path only, or (simpler, matching the
existing house style of not fighting the mock library) use
`resp_lib.add(..., url=re.compile(rf"{re.escape(_WIKI_BASE)}/en\.wikipedia/all-access/user/Semaglutide/monthly/\d+/\d+"))`.
Use the regex form for all three tests above instead of a literal f-string
URL so the test isn't clock-dependent.

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/regulatory/test_sources.py -v -k wikipedia`
Expected: FAIL — `ImportError: cannot import name 'fetch_wikipedia_pageviews'`.

- [ ] **Step 3: Write minimal implementation**

```python
# engine/regulatory/sources/wikipedia.py
"""
Wikimedia Analytics REST API client — monthly pageviews for an article
title, used as the closest free proxy for public/consumer interest (see the
spec's "Why not Google Trends" section — this is NOT search volume and must
never be labeled as such by the frontend).

No API key. Wikimedia policy requires a descriptive User-Agent
identifying the application and a contact point.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from urllib.parse import quote

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ._base import cached_fetch

_SOURCE = "wikipedia"
_TTL = 60 * 60 * 24  # 24 hours
_TIMEOUT = 6
_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
_MONTHS_BACK = 24


def _user_agent() -> str:
    contact = os.environ.get("U4U_CONTACT_EMAIL", "ops@flmanbiosci.net")
    return f"u4u-engine/regulatory-dashboard (https://flmanbiosci.net; {contact})"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _query(title: str, start: str, end: str) -> dict:
    url = f"{_BASE}/en.wikipedia/all-access/user/{quote(title, safe='')}/monthly/{start}/{end}"
    res = requests.get(url, headers={"User-Agent": _user_agent()}, timeout=_TIMEOUT)
    if res.status_code == 404:
        # No article for this title — a legitimate empty result, not a failure.
        return {"items": []}
    res.raise_for_status()
    return res.json()


def _fetch(title: str) -> dict:
    now = datetime.now()
    start = (now.replace(day=1) - timedelta(days=_MONTHS_BACK * 31)).strftime("%Y%m01")
    end = now.strftime("%Y%m%d")
    payload = _query(title, start, end)
    months = [
        {"month": f"{it['timestamp'][:4]}-{it['timestamp'][4:6]}", "views": it["views"]}
        for it in payload.get("items", []) or []
    ]
    return {
        "title": title,
        "months": months,
        "total": sum(m["views"] for m in months),
    }


def fetch_wikipedia_pageviews(title: str) -> dict:
    return cached_fetch(_SOURCE, title, _TTL, lambda: _fetch(title))
```

Now finish `engine/regulatory/sources/__init__.py` (uncomment/complete the
wiring from Task 2 — the version shown in Task 2's Step 3 is already the
final state, nothing further to change there).

- [ ] **Step 4: Run test to verify it passes**

Run: `nix develop --command python -m pytest tests/regulatory/test_sources.py -v -k wikipedia`
Expected: PASS. Then run the whole file to confirm Task 2 + Task 3 coexist:
`nix develop --command python -m pytest tests/regulatory/test_sources.py -v`

- [ ] **Step 5: Commit**

```bash
git add engine/regulatory/sources/wikipedia.py engine/regulatory/sources/__init__.py \
        tests/regulatory/test_sources.py
git commit -m "feat(regulatory): add Wikipedia monthly-pageviews source"
```

---

### Task 4: Extend `openfda.py` with a FAERS reaction breakdown

**Files:**
- Modify: `engine/regulatory/sources/openfda.py`
- Test: `tests/regulatory/test_sources.py` (extend)

**Interfaces:**
- `fetch_openfda(search_term)`'s `data` gains a new key
  `adverse_event_reactions: list[{"term": str, "count": int}] | None` — the
  top reported MedDRA reaction terms from FAERS. `None` specifically means
  "no FAERS surveillance found for this compound" (distinct from `[]`,
  which would mean "queried FAERS, zero reactions" — an edge case that in
  practice won't occur since a zero-result query 404s, handled below).
  Existing `adverse_events_total` is unchanged and remains the "is there any
  FAERS data at all" signal the frontend's state-4 check uses.

- [ ] **Step 1: Write the failing test**

```python
# tests/regulatory/test_sources.py — extend the openFDA section

@resp_lib.activate
def test_openfda_includes_reaction_breakdown():
    resp_lib.add(resp_lib.GET, _OF_ENF, json={}, status=404)
    resp_lib.add(
        resp_lib.GET, _OF_EVT,
        json={"meta": {"results": {"total": 42}}, "results": []},
        status=200,
    )
    resp_lib.add(
        resp_lib.GET, _OF_EVT,
        json={"results": [
            {"term": "NAUSEA", "count": 20},
            {"term": "HEADACHE", "count": 12},
        ]},
        status=200,
    )
    out = fetch_openfda("Semaglutide")
    assert out["data"]["adverse_events_total"] == 42
    assert out["data"]["adverse_event_reactions"] == [
        {"term": "NAUSEA", "count": 20},
        {"term": "HEADACHE", "count": 12},
    ]


@resp_lib.activate
def test_openfda_no_faers_data_is_none_not_empty_list():
    resp_lib.add(resp_lib.GET, _OF_ENF, json={}, status=404)
    resp_lib.add(resp_lib.GET, _OF_EVT, json={}, status=404)
    out = fetch_openfda("Very Obscure Peptide")
    assert out["data"]["adverse_events_total"] == 0
    assert out["data"]["adverse_event_reactions"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/regulatory/test_sources.py -v -k openfda`
Expected: FAIL — `KeyError: 'adverse_event_reactions'`.

- [ ] **Step 3: Write minimal implementation**

```python
# engine/regulatory/sources/openfda.py — replace the adverse-event block in _fetch()

    # Adverse-event signal — total count, plus (if any exist) the top
    # reported reaction terms via openFDA's count aggregation. None means
    # no FAERS surveillance was found; this is distinct from a curated
    # adverse_effects: [] ("reviewed, none found") — see engine/regulatory/curation.py.
    events_total = None
    reactions: list[dict] | None = None
    try:
        events_query = f'patient.drug.medicinalproduct:"{search_term}"'
        events = _query(_EVENT, _params(events_query, limit=1))
        events_total = ((events.get("meta") or {}).get("results") or {}).get("total", 0)
        if events_total:
            reaction_params = _params(events_query, limit=5)
            reaction_params["count"] = "patient.reaction.reactionmeddrapt.exact"
            reaction_payload = _query(_EVENT, reaction_params)
            reactions = [
                {"term": r["term"], "count": r["count"]}
                for r in reaction_payload.get("results", []) or []
            ]
    except Exception:
        events_total = None

    return {
        "search_term": search_term,
        "recalls_total": recalls_total,
        "recalls": recalls,
        "adverse_events_total": events_total,
        "adverse_event_reactions": reactions,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `nix develop --command python -m pytest tests/regulatory/test_sources.py -v -k openfda`
Expected: PASS. Then the full source test file:
`nix develop --command python -m pytest tests/regulatory/test_sources.py -v`

- [ ] **Step 5: Commit**

```bash
git add engine/regulatory/sources/openfda.py tests/regulatory/test_sources.py
git commit -m "feat(regulatory): add FAERS reaction breakdown to openfda source"
```

---

### Task 5: Wire PubMed + Wikipedia into the aggregator (with graceful skip)

**Files:**
- Modify: `engine/regulatory/aggregator.py`
- Test: `tests/regulatory/test_aggregator.py` (extend)

**Interfaces:**
- `build_dashboard_payload()`'s per-peptide `live` dict gains `"pubmed"`
  (always present) and `"wikipedia"` (present only when the peptide has a
  non-null `wikipedia_title` — omitted, not `unavailable`, otherwise, per
  the spec's "missing signal omits that sparkline" rule).

- [ ] **Step 1: Write the failing test**

```python
# tests/regulatory/test_aggregator.py — extend _stub_all_sources_ok() and add tests

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
    resp_lib.add(
        resp_lib.GET,
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        json={"esearchresult": {"count": "0"}},
        status=200,
    )


def test_payload_with_live_attaches_pubmed_for_every_peptide():
    with resp_lib.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        _stub_all_sources_ok()
        payload = build_dashboard_payload(include_live=True)
        assert len(rsps.calls) > 0
    for p in payload["peptides"]:
        assert "pubmed" in p["live"]
        assert p["live"]["pubmed"]["status"] in {"fresh", "stale", "unavailable"}


def test_wikipedia_omitted_when_no_title_curated():
    """Every peptide today has wikipedia_title: null (Task 1) — none should
    carry a 'wikipedia' key in `live` until a human curates a title."""
    with resp_lib.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        _stub_all_sources_ok()
        payload = build_dashboard_payload(include_live=True)
    for p in payload["peptides"]:
        assert "wikipedia" not in p["live"]


def test_wikipedia_present_when_title_curated(monkeypatch):
    """Simulate a curated wikipedia_title and confirm it's fetched."""
    from engine.regulatory import store as store_module

    orig_load = store_module.load_peptides

    def _patched():
        data = orig_load()
        data = {**data, "peptides": [
            {**p, "wikipedia_title": "Semaglutide"} if p["slug"] == "semaglutide" else p
            for p in data["peptides"]
        ]}
        return data

    monkeypatch.setattr(store_module, "load_peptides", _patched)
    monkeypatch.setattr(
        "engine.regulatory.aggregator.load_peptides", _patched
    )
    with resp_lib.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        _stub_all_sources_ok()
        resp_lib.add(
            resp_lib.GET,
            re.compile(r"https://wikimedia\.org/api/rest_v1/metrics/pageviews/per-article/.*"),
            json={"items": []},
            status=200,
        )
        payload = build_dashboard_payload(include_live=True)
    by_slug = {p["slug"]: p for p in payload["peptides"]}
    assert "wikipedia" in by_slug["semaglutide"]["live"]
```

Add `import re` at the top of `tests/regulatory/test_aggregator.py`.

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/regulatory/test_aggregator.py -v`
Expected: FAIL — `assert "pubmed" in p["live"]` (KeyError-shaped assertion
failure; `pubmed` isn't fetched yet).

- [ ] **Step 3: Write minimal implementation**

```python
# engine/regulatory/aggregator.py

from .sources import (
    fetch_docket_summary,
    fetch_federal_register,
    fetch_openfda,
    fetch_pubmed,
    fetch_trials,
    fetch_wikipedia_pageviews,
)

# term_key, fetch_fn, optional (skip entirely when the peptide's term_key value is falsy)
_SOURCE_FETCHERS: dict[str, tuple[str, Callable[[str], dict], bool]] = {
    "clinicaltrials": ("clinicaltrials_search_term", fetch_trials, False),
    "openfda": ("openfda_search_term", fetch_openfda, False),
    "federal_register": ("federal_register_search_term", fetch_federal_register, False),
    "pubmed": ("pubmed_search_term", fetch_pubmed, False),
    "wikipedia": ("wikipedia_title", fetch_wikipedia_pageviews, True),
}


def _fan_out_live(peptides: list[dict], max_workers: int) -> dict[str, dict[str, dict]]:
    """
    Run every (peptide × source) live fetch in a single executor.

    A nested per-peptide ThreadPoolExecutor would serialise across peptides
    (one batch of 3 in flight at a time). Flattening means the dashboard's
    cold-cache latency is roughly one upstream round-trip, not N of them.

    Optional sources (currently just Wikipedia) are skipped entirely — not
    submitted, not marked unavailable — when the peptide has no value for
    their term key, so the frontend can tell "no signal to show" apart from
    "tried and failed."
    """
    out: dict[str, dict[str, dict]] = {p["slug"]: {} for p in peptides}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures: dict = {}
        for p in peptides:
            for name, (term_key, fetch_fn, optional) in _SOURCE_FETCHERS.items():
                term = p.get(term_key)
                if optional and not term:
                    continue
                fut = ex.submit(fetch_fn, term)
                futures[fut] = (p["slug"], name)
        for fut in as_completed(futures):
            slug, name = futures[fut]
            try:
                out[slug][name] = fut.result()
            except Exception as exc:
                log.warning("source %s failed for %s: %s", name, slug, exc)
                out[slug][name] = {
                    "data": None,
                    "fetched_at": None,
                    "status": "unavailable",
                    "source": name,
                }
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `nix develop --command python -m pytest tests/regulatory/test_aggregator.py -v`
Expected: PASS. Then the full regulatory suite:
`nix develop --command python -m pytest tests/regulatory/ -v`

- [ ] **Step 5: Commit**

```bash
git add engine/regulatory/aggregator.py tests/regulatory/test_aggregator.py
git commit -m "feat(regulatory): fan out PubMed + optional Wikipedia in the aggregator"
```

---

### Task 6: Curation CLI `engine/regulatory/curate.py`

**Files:**
- Create: `engine/regulatory/curate.py`
- Test: `tests/regulatory/test_curate.py`

**Interfaces:**
- `python -m engine.regulatory.curate {list,show,set-mechanism,set-adverse-effect,remove-adverse-effect,clear-mechanism,validate} ...`
  operating on `data/regulatory/peptides.json` (`--out` overrides the path
  for tests, mirroring `evidence_update.py`'s `--out`).
- Refuses to write an uncited `mechanism` or `adverse_effects` entry
  (delegates to `engine.regulatory.curation.validate_*`).

**Design notes:** Unlike the biomarker evidence registry (one flat
`entries` dict), curation here targets one field on one existing peptide
inside an already-large `peptides` list, so the CLI is peptide-slug +
sub-resource shaped (`set-mechanism <slug>`, `set-adverse-effect <slug>`,
`remove-adverse-effect <slug> <effect-text>`, `clear-mechanism <slug>`)
rather than a single `set`/`remove` pair. `adverse_effects` starts as
`None`; the first `set-adverse-effect` call for a slug initializes it to
`[]` and appends — so curating "no adverse effects found" is
`clear-adverse-effects <slug>` (sets `[]` explicitly), distinct from never
having run any adverse-effect command at all (stays `None`).

- [ ] **Step 1: Write the failing test**

```python
# tests/regulatory/test_curate.py
"""Tests for the regulatory curation CLI (mirrors evidence_update tests)."""

import json

import pytest

from engine.regulatory import curate
from engine.regulatory.curation import CurationError


@pytest.fixture
def seeded_path(tmp_path):
    path = tmp_path / "peptides.json"
    path.write_text(json.dumps({
        "schema_version": 3,
        "last_curated": "2026-07-01",
        "categories": {"cat1": {"label": "x", "description": "x"}},
        "peptides": [
            {
                "slug": "bpc-157",
                "name": "BPC-157",
                "aliases": [],
                "category": "cat1",
                "pcac_wave": None,
                "approved_indications": [],
                "medspa_uses": [],
                "history": [],
                "clinicaltrials_search_term": "BPC-157",
                "openfda_search_term": "BPC-157",
                "federal_register_search_term": "BPC-157",
                "pubmed_search_term": "BPC-157",
                "wikipedia_title": None,
                "mechanism": None,
                "adverse_effects": None,
            },
        ],
    }))
    return str(path)


def test_set_mechanism_requires_citation(seeded_path):
    rc = curate.main([
        "--out", seeded_path, "set-mechanism", "bpc-157",
        "--text", "Some mechanism text.",
    ])
    assert rc != 0
    doc = json.loads(open(seeded_path).read())
    assert doc["peptides"][0]["mechanism"] is None


def test_set_mechanism_with_citation_succeeds(seeded_path):
    rc = curate.main([
        "--out", seeded_path, "set-mechanism", "bpc-157",
        "--text", "Some mechanism text.",
        "--citation", "Sikiric et al. 2018, doi:10.2174/xxx",
    ])
    assert rc == 0
    doc = json.loads(open(seeded_path).read())
    m = doc["peptides"][0]["mechanism"]
    assert m["text"] == "Some mechanism text."
    assert m["citation"] == "Sikiric et al. 2018, doi:10.2174/xxx"


def test_set_adverse_effect_requires_citation(seeded_path):
    rc = curate.main([
        "--out", seeded_path, "set-adverse-effect", "bpc-157",
        "--effect", "Injection site irritation",
    ])
    assert rc != 0
    doc = json.loads(open(seeded_path).read())
    assert doc["peptides"][0]["adverse_effects"] is None


def test_set_adverse_effect_with_citation_appends(seeded_path):
    rc = curate.main([
        "--out", seeded_path, "set-adverse-effect", "bpc-157",
        "--effect", "Injection site irritation",
        "--citation", "Case series, doi:10.1000/xyz",
    ])
    assert rc == 0
    doc = json.loads(open(seeded_path).read())
    effects = doc["peptides"][0]["adverse_effects"]
    assert len(effects) == 1
    assert effects[0]["effect"] == "Injection site irritation"


def test_clear_adverse_effects_sets_explicit_empty_list(seeded_path):
    """clear-adverse-effects records 'reviewed, none found' -- [] not None."""
    rc = curate.main(["--out", seeded_path, "clear-adverse-effects", "bpc-157"])
    assert rc == 0
    doc = json.loads(open(seeded_path).read())
    assert doc["peptides"][0]["adverse_effects"] == []


def test_unknown_slug_fails(seeded_path):
    rc = curate.main([
        "--out", seeded_path, "set-mechanism", "not-a-real-slug",
        "--text", "x", "--citation", "x",
    ])
    assert rc != 0


def test_validate_catches_malformed_registry(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({
        "schema_version": 3,
        "categories": {},
        "peptides": [
            {"slug": "x", "mechanism": {"text": "no citation"}, "adverse_effects": None},
        ],
    }))
    rc = curate.main(["--out", str(path), "validate"])
    assert rc != 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/regulatory/test_curate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.regulatory.curate'`.

- [ ] **Step 3: Write minimal implementation**

```python
# engine/regulatory/curate.py
"""
engine/regulatory/curate.py
============================
Curator CLI for the mechanism / adverse_effects fields on
data/regulatory/peptides.json. Mirrors engine/tracking/evidence_update.py:
a human who has actually read the cited paper records it here; the CLI
refuses to write an entry without a real citation string.

Subcommands
-----------
    list                          Show curation coverage per peptide.
    show <slug>                   Print one peptide's mechanism + adverse_effects.
    set-mechanism <slug>          Set the cited mechanism text (--text --citation).
    clear-mechanism <slug>        Revert mechanism to null (not yet curated).
    set-adverse-effect <slug>     Append one cited adverse effect (--effect --citation [--note]).
    remove-adverse-effect <slug> <effect>   Remove one adverse-effect entry by exact effect text.
    clear-adverse-effects <slug>  Set adverse_effects to [] -- "reviewed, none found".
    reset-adverse-effects <slug>  Revert adverse_effects to null (not yet curated).
    validate                      Load + validate every peptide's curation fields.

Only data/regulatory/peptides.json is touched; ``--out`` overrides the path
(tests use a tmp file).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .curation import CurationError, validate_peptide_curation

_DEFAULT_PATH = "data/regulatory/peptides.json"


def _load(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write(path: str, doc: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _find_peptide(doc: dict[str, Any], slug: str) -> dict[str, Any] | None:
    for p in doc.get("peptides", []):
        if p.get("slug") == slug:
            return p
    return None


def cmd_list(args: argparse.Namespace) -> int:
    doc = _load(args.out)
    print(f"{'SLUG':25} {'MECHANISM':10} {'ADVERSE EFFECTS':30}")
    print("-" * 68)
    for p in doc["peptides"]:
        mech = "cited" if p.get("mechanism") else "—"
        ae = p.get("adverse_effects")
        ae_state = "not yet curated" if ae is None else f"{len(ae)} cited" if ae else "none found (reviewed)"
        print(f"{p['slug']:25} {mech:10} {ae_state:30}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    doc = _load(args.out)
    p = _find_peptide(doc, args.slug)
    if p is None:
        print(f"no such peptide slug: {args.slug!r}", file=sys.stderr)
        return 1
    print(json.dumps({
        "slug": p["slug"],
        "mechanism": p.get("mechanism"),
        "adverse_effects": p.get("adverse_effects"),
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_set_mechanism(args: argparse.Namespace) -> int:
    doc = _load(args.out)
    p = _find_peptide(doc, args.slug)
    if p is None:
        print(f"no such peptide slug: {args.slug!r}", file=sys.stderr)
        return 1
    candidate = {"text": args.text, "citation": args.citation}
    try:
        validate_peptide_curation({**p, "mechanism": candidate})
    except CurationError as exc:
        print(f"rejected: {exc}", file=sys.stderr)
        return 1
    p["mechanism"] = candidate
    _write(args.out, doc)
    print(f"set mechanism for {args.slug!r}")
    return 0


def cmd_clear_mechanism(args: argparse.Namespace) -> int:
    doc = _load(args.out)
    p = _find_peptide(doc, args.slug)
    if p is None:
        print(f"no such peptide slug: {args.slug!r}", file=sys.stderr)
        return 1
    p["mechanism"] = None
    _write(args.out, doc)
    print(f"cleared mechanism for {args.slug!r} (now not yet curated)")
    return 0


def cmd_set_adverse_effect(args: argparse.Namespace) -> int:
    doc = _load(args.out)
    p = _find_peptide(doc, args.slug)
    if p is None:
        print(f"no such peptide slug: {args.slug!r}", file=sys.stderr)
        return 1
    entry = {"effect": args.effect, "citation": args.citation}
    if args.note:
        entry["note"] = args.note
    existing = list(p.get("adverse_effects") or [])
    candidate = existing + [entry]
    try:
        validate_peptide_curation({**p, "adverse_effects": candidate})
    except CurationError as exc:
        print(f"rejected: {exc}", file=sys.stderr)
        return 1
    p["adverse_effects"] = candidate
    _write(args.out, doc)
    print(f"added adverse effect {args.effect!r} for {args.slug!r}")
    return 0


def cmd_remove_adverse_effect(args: argparse.Namespace) -> int:
    doc = _load(args.out)
    p = _find_peptide(doc, args.slug)
    if p is None:
        print(f"no such peptide slug: {args.slug!r}", file=sys.stderr)
        return 1
    existing = p.get("adverse_effects") or []
    remaining = [e for e in existing if e.get("effect") != args.effect]
    if len(remaining) == len(existing):
        print(f"no adverse effect {args.effect!r} found for {args.slug!r}", file=sys.stderr)
        return 1
    p["adverse_effects"] = remaining
    _write(args.out, doc)
    print(f"removed adverse effect {args.effect!r} for {args.slug!r}")
    return 0


def cmd_clear_adverse_effects(args: argparse.Namespace) -> int:
    doc = _load(args.out)
    p = _find_peptide(doc, args.slug)
    if p is None:
        print(f"no such peptide slug: {args.slug!r}", file=sys.stderr)
        return 1
    p["adverse_effects"] = []
    _write(args.out, doc)
    print(f"set adverse_effects=[] for {args.slug!r} (reviewed, none found)")
    return 0


def cmd_reset_adverse_effects(args: argparse.Namespace) -> int:
    doc = _load(args.out)
    p = _find_peptide(doc, args.slug)
    if p is None:
        print(f"no such peptide slug: {args.slug!r}", file=sys.stderr)
        return 1
    p["adverse_effects"] = None
    _write(args.out, doc)
    print(f"reset adverse_effects for {args.slug!r} to null (not yet curated)")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    doc = _load(args.out)
    errors = []
    for p in doc.get("peptides", []):
        try:
            validate_peptide_curation(p)
        except CurationError as exc:
            errors.append(str(exc))
    if errors:
        for e in errors:
            print(f"INVALID: {e}", file=sys.stderr)
        return 1
    print(f"OK: {len(doc.get('peptides', []))} peptides validated in {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="curate", description="Curate regulatory peptide mechanism/adverse-effects data.")
    p.add_argument("--out", default=_DEFAULT_PATH)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list").set_defaults(func=cmd_list)

    sp = sub.add_parser("show"); sp.add_argument("slug"); sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("set-mechanism")
    sp.add_argument("slug")
    sp.add_argument("--text", required=True)
    sp.add_argument("--citation", required=True)
    sp.set_defaults(func=cmd_set_mechanism)

    sp = sub.add_parser("clear-mechanism"); sp.add_argument("slug"); sp.set_defaults(func=cmd_clear_mechanism)

    sp = sub.add_parser("set-adverse-effect")
    sp.add_argument("slug")
    sp.add_argument("--effect", required=True)
    sp.add_argument("--citation", required=True)
    sp.add_argument("--note", default=None)
    sp.set_defaults(func=cmd_set_adverse_effect)

    sp = sub.add_parser("remove-adverse-effect")
    sp.add_argument("slug")
    sp.add_argument("effect")
    sp.set_defaults(func=cmd_remove_adverse_effect)

    sp = sub.add_parser("clear-adverse-effects"); sp.add_argument("slug"); sp.set_defaults(func=cmd_clear_adverse_effects)
    sp = sub.add_parser("reset-adverse-effects"); sp.add_argument("slug"); sp.set_defaults(func=cmd_reset_adverse_effects)

    sub.add_parser("validate").set_defaults(func=cmd_validate)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `nix develop --command python -m pytest tests/regulatory/test_curate.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/regulatory/curate.py tests/regulatory/test_curate.py
git commit -m "feat(regulatory): add curation CLI for mechanism/adverse_effects"
```

---

### Task 7: Backend degrade-gracefully + honesty-contract regression tests

**Files:**
- Test: `tests/regulatory/test_aggregator.py` (extend)
- Test: `tests/regulatory/test_api.py` (create, if no such file exists yet —
  check first; extend if `tests/test_api.py` already covers `/regulatory/*`)

**Interfaces:** No new production code — this task is pure test coverage
closing out the spec's "Testing" section items that Tasks 1–6 didn't
already cover directly: the full-outage 200 response, and that the four
adverse-effects states are distinguishable in the raw payload (the
frontend-rendering assertion itself is Task 9/10's job, since that's where
the actual state → text mapping lives).

- [ ] **Step 1: Write the failing test**

```python
# tests/regulatory/test_aggregator.py — append

def test_all_sources_down_still_returns_curated_with_new_sources():
    """Extends the existing all-down test to cover pubmed/wikipedia too."""
    payload = build_dashboard_payload(include_live=True)
    assert len(payload["peptides"]) >= 22
    for p in payload["peptides"]:
        assert p["live"]["pubmed"]["status"] == "unavailable"
        assert p["live"]["pubmed"]["data"] is None
        # wikipedia is omitted (no curated title), not unavailable -- confirms
        # Task 5's optional-skip behavior holds even when every source is down.
        assert "wikipedia" not in p["live"]


def test_adverse_effects_none_vs_empty_list_survive_the_full_payload(monkeypatch):
    """Payload-level check that None and [] aren't coerced into each other
    anywhere between store.load_peptides and the aggregator's dict merge."""
    from engine.regulatory import store as store_module

    orig_load = store_module.load_peptides

    def _patched():
        data = orig_load()
        peptides = []
        for p in data["peptides"]:
            if p["slug"] == "bpc-157":
                p = {**p, "adverse_effects": [{"effect": "Injection site irritation", "citation": "x"}]}
            elif p["slug"] == "semaglutide":
                p = {**p, "adverse_effects": []}
            peptides.append(p)
        return {**data, "peptides": peptides}

    monkeypatch.setattr("engine.regulatory.aggregator.load_peptides", _patched)
    payload = build_dashboard_payload(include_live=False)
    by_slug = {p["slug"]: p for p in payload["peptides"]}
    assert by_slug["bpc-157"]["adverse_effects"] == [
        {"effect": "Injection site irritation", "citation": "x"}
    ]
    assert by_slug["semaglutide"]["adverse_effects"] == []
    # every other peptide is still genuinely uncurated (None), not silently []
    for slug, p in by_slug.items():
        if slug not in ("bpc-157", "semaglutide"):
            assert p["adverse_effects"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/regulatory/test_aggregator.py -v`
Expected: These two should already pass once Tasks 1–5 are in place (this
task adds coverage, not new behavior) — if either fails, it's telling you
Task 1's `.setdefault` seeding or Task 5's `_fan_out_live` broke the
None/[] distinction; fix there, not here.

- [ ] **Step 3: N/A — no implementation change if Step 2 passes**

If Step 2 genuinely fails, the fix belongs in `store.py` (Task 1) or
`aggregator.py` (Task 5) — do not special-case `None`/`[]` handling inside
the aggregator's dict-merge (`{**p, ...}` already passes both through
verbatim; a failure here means something upstream is calling
`.get("adverse_effects", [])` with a truthy default somewhere, which must
be changed to `.get("adverse_effects")`).

- [ ] **Step 4: Run test to verify it passes**

Run: `nix develop --command python -m pytest tests/regulatory/ -v`
Expected: PASS, full regulatory suite green.

- [ ] **Step 5: Commit**

```bash
git add tests/regulatory/test_aggregator.py
git commit -m "test(regulatory): cover full-outage degrade + None/[] honesty contract"
```

---

### Task 8: Frontend types

**Files:**
- Modify: `frontend/src/app/lib/types.ts`

**Interfaces:**
- Produces new exported interfaces `Mechanism`, `AdverseEffect`,
  `PubmedLiveData`, `WikipediaLiveData`; extends `RegulatoryPeptide` and the
  `PeptideLiveData` map type.

- [ ] **Step 1: N/A (types file, no runtime behavior to test — verified by
  the Task 10 type-check step)**

- [ ] **Step 2: Add the new types**

Find the existing `PeptideLiveData` interface (referenced by `PeptideCard.tsx`
as `peptide.live?.clinicaltrials` etc.) and extend it alongside
`RegulatoryPeptide`:

```typescript
// frontend/src/app/lib/types.ts

export interface Mechanism {
  text: string;
  citation: string;
}

export interface AdverseEffect {
  effect: string;
  citation: string;
  note?: string;
}

export interface PubmedLiveData {
  search_term: string;
  total: number;
  years: { year: number; count: number }[];
  pubmed_url: string;
}

export interface WikipediaLiveData {
  title: string;
  months: { month: string; views: number }[];
  total: number;
}

export interface FaersReaction {
  term: string;
  count: number;
}
```

Then extend the existing `openfda` live-data shape (find its interface —
likely `OpenFdaLiveData` or inline in `PeptideLiveData`) to add:

```typescript
  adverse_event_reactions: FaersReaction[] | null;
```

And extend `RegulatoryPeptide`:

```typescript
export interface RegulatoryPeptide {
  slug: string;
  name: string;
  aliases: string[];
  category: RegulatoryCategorySlug;
  pcac_wave: "july_2026" | "early_2027" | null;
  approved_indications: string[];
  medspa_uses: string[];
  history: RegulatoryHistoryEntry[];
  clinicaltrials_search_term: string;
  openfda_search_term: string;
  federal_register_search_term: string;
  pubmed_search_term: string;
  wikipedia_title: string | null;
  mechanism: Mechanism | null;
  adverse_effects: AdverseEffect[] | null;
  engine_covered: boolean;
  live: PeptideLiveData;
}
```

Find the `PeptideLiveData` type declaration (likely
`Partial<Record<"clinicaltrials" | "openfda" | "federal_register", LiveEnvelope<...>>>`
or similar — read it first) and add `pubmed?: LiveEnvelope<PubmedLiveData>`
and `wikipedia?: LiveEnvelope<WikipediaLiveData>` (optional, matching the
"omitted when no title" contract from Task 5).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/lib/types.ts
git commit -m "feat(frontend): add types for mechanism/adverse_effects/pubmed/wikipedia"
```

---

### Task 9: Frontend adverse-effects state helper (unit-tested)

**Files:**
- Create: `frontend/src/app/regulatory/lib/adverseEffects.ts`
- Create: `frontend/src/app/regulatory/lib/adverseEffects.test.ts`
- Modify: `frontend/package.json` (add `vitest` devDependency + `test` script)
- Create: `frontend/vitest.config.ts`

**Design notes:** The frontend has no test runner today (`package.json` has
no `test` script and no Jest/Vitest devDependency). The spec explicitly
requires an executable assertion that the four adverse-effects states never
render text implying safety — that can't be checked by eyeballing, so this
task extracts the state-selection logic into one pure, framework-free
function and adds the smallest possible test runner (`vitest`, zero
`jsdom`/React-rendering setup needed since the function takes/returns plain
data). This is a dev-only dependency; it's not part of `npm run build` and
doesn't touch the production frontend Docker image.

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/app/regulatory/lib/adverseEffects.test.ts
import { describe, expect, it } from "vitest";
import { describeAdverseEffects } from "./adverseEffects";
import type { AdverseEffect, FaersReaction } from "../../lib/types";

const SAFETY_IMPLYING = /none reported|no known side effects|no side effects/i;

describe("describeAdverseEffects", () => {
  it("state 1: curated entries present -> shows them", () => {
    const entries: AdverseEffect[] = [
      { effect: "Nausea", citation: "Smith 2020" },
    ];
    const r = describeAdverseEffects({ curated: entries, faersTotal: null, faersReactions: null });
    expect(r.state).toBe("curated");
    expect(r.curatedEntries).toEqual(entries);
    expect(r.headline).not.toMatch(SAFETY_IMPLYING);
  });

  it("state 2: adverse_effects is null -> not yet curated", () => {
    const r = describeAdverseEffects({ curated: null, faersTotal: null, faersReactions: null });
    expect(r.state).toBe("not_yet_curated");
    expect(r.headline).toMatch(/not yet curated/i);
    expect(r.headline).not.toMatch(SAFETY_IMPLYING);
  });

  it("state 3: adverse_effects is [] -> reviewed, none found (never 'none reported')", () => {
    const r = describeAdverseEffects({ curated: [], faersTotal: null, faersReactions: null });
    expect(r.state).toBe("reviewed_none_found");
    expect(r.headline).toMatch(/no adverse effects identified in the reviewed literature/i);
    expect(r.headline).not.toMatch(SAFETY_IMPLYING);
  });

  it("state 4: no FAERS surveillance -> says so explicitly, never implies safety", () => {
    const r = describeAdverseEffects({ curated: null, faersTotal: 0, faersReactions: null });
    expect(r.faersState).toBe("no_surveillance");
    expect(r.faersHeadline).toMatch(/no faers surveillance/i);
    expect(r.faersHeadline).not.toMatch(SAFETY_IMPLYING);
  });

  it("FAERS data present -> surfaces the reaction breakdown, still not a safety claim", () => {
    const reactions: FaersReaction[] = [{ term: "NAUSEA", count: 20 }];
    const r = describeAdverseEffects({ curated: null, faersTotal: 20, faersReactions: reactions });
    expect(r.faersState).toBe("has_reports");
    expect(r.faersReactions).toEqual(reactions);
    expect(r.faersHeadline).not.toMatch(SAFETY_IMPLYING);
  });

  it("no combination of inputs ever produces safety-implying text", () => {
    const combos = [
      { curated: null, faersTotal: null, faersReactions: null },
      { curated: [], faersTotal: 0, faersReactions: null },
      { curated: [], faersTotal: null, faersReactions: null },
      { curated: [{ effect: "X", citation: "Y" }], faersTotal: 0, faersReactions: null },
    ];
    for (const c of combos) {
      const r = describeAdverseEffects(c);
      expect(r.headline).not.toMatch(SAFETY_IMPLYING);
      expect(r.faersHeadline).not.toMatch(SAFETY_IMPLYING);
    }
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npx vitest run 2>&1 | head -40
```

Expected: FAIL — `vitest` isn't a dependency yet / `Cannot find module './adverseEffects'`.

- [ ] **Step 3: Add the vitest devDependency + config, write the minimal implementation**

`frontend/package.json` — add to `devDependencies` and `scripts`:

```json
    "vitest": "^3"
```

```json
    "test": "vitest run"
```

`frontend/vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
```

`frontend/src/app/regulatory/lib/adverseEffects.ts`:

```typescript
import type { AdverseEffect, FaersReaction } from "../../lib/types";

export type AdverseEffectsState = "curated" | "not_yet_curated" | "reviewed_none_found";
export type FaersState = "has_reports" | "no_surveillance";

export interface AdverseEffectsView {
  state: AdverseEffectsState;
  curatedEntries: AdverseEffect[];
  headline: string;
  faersState: FaersState;
  faersHeadline: string;
  faersReactions: FaersReaction[];
}

/**
 * Pure state-selection for the adverse-effects panel. Never returns text
 * implying safety -- absence of data means unmonitored, not safe. See
 * docs/superpowers/specs/2026-07-20-regulatory-peptide-enrichment-design.md
 * "Critical correctness constraint".
 */
export function describeAdverseEffects(input: {
  curated: AdverseEffect[] | null;
  faersTotal: number | null;
  faersReactions: FaersReaction[] | null;
}): AdverseEffectsView {
  const { curated, faersTotal, faersReactions } = input;

  let state: AdverseEffectsState;
  let headline: string;
  if (curated === null) {
    state = "not_yet_curated";
    headline = "Not yet curated";
  } else if (curated.length === 0) {
    state = "reviewed_none_found";
    headline = "No adverse effects identified in the reviewed literature";
  } else {
    state = "curated";
    headline = `${curated.length} cited adverse effect${curated.length === 1 ? "" : "s"}`;
  }

  const faersState: FaersState = faersTotal ? "has_reports" : "no_surveillance";
  const faersHeadline =
    faersState === "has_reports"
      ? `${faersTotal} FAERS report${faersTotal === 1 ? "" : "s"} on file`
      : "No FAERS surveillance found for this compound (unmonitored, not confirmed safe)";

  return {
    state,
    curatedEntries: curated ?? [],
    headline,
    faersState,
    faersHeadline,
    faersReactions: faersReactions ?? [],
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd frontend && npm install && npx vitest run
```

Expected: PASS, all 6 test cases.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts \
        frontend/src/app/regulatory/lib/adverseEffects.ts \
        frontend/src/app/regulatory/lib/adverseEffects.test.ts
git commit -m "feat(frontend): add adverse-effects 4-state helper with unit tests"
```

---

### Task 10: Frontend UI — mechanism, adverse effects, sparklines on `PeptideCard`

**Files:**
- Create: `frontend/src/app/regulatory/components/MechanismBlock.tsx`
- Create: `frontend/src/app/regulatory/components/AdverseEffectsBlock.tsx`
- Create: `frontend/src/app/regulatory/components/PopularitySparklines.tsx`
- Modify: `frontend/src/app/regulatory/components/PeptideCard.tsx`

**Interfaces:** Three new presentational components, wired into
`PeptideCard.tsx` below the existing `<dl>` stats grid and above the
"Regulatory history" `<details>` block.

- [ ] **Step 1: (No new unit-testable logic here — `describeAdverseEffects`
  is already tested in Task 9; this task is presentation only, verified by
  the build/type-check step and, if the dev server is reachable in this
  environment, a manual look at `/regulatory` per the repo's UI-change
  convention.)**

- [ ] **Step 2: Write `MechanismBlock.tsx`**

```tsx
// frontend/src/app/regulatory/components/MechanismBlock.tsx
import type { Mechanism } from "../../lib/types";

export function MechanismBlock({ mechanism }: { mechanism: Mechanism | null }) {
  if (!mechanism) return null; // hidden entirely when not curated -- never an empty heading

  return (
    <div className="text-xs text-zinc-400">
      <p className="mb-1 font-medium text-zinc-300">Mechanism</p>
      <p>{mechanism.text}</p>
      <p className="mt-1 text-[10px] text-zinc-500">{mechanism.citation}</p>
    </div>
  );
}
```

- [ ] **Step 3: Write `AdverseEffectsBlock.tsx`**

```tsx
// frontend/src/app/regulatory/components/AdverseEffectsBlock.tsx
import type { AdverseEffect, FaersReaction } from "../../lib/types";
import { describeAdverseEffects } from "../lib/adverseEffects";

export function AdverseEffectsBlock({
  curated,
  faersTotal,
  faersReactions,
}: {
  curated: AdverseEffect[] | null;
  faersTotal: number | null;
  faersReactions: FaersReaction[] | null;
}) {
  const view = describeAdverseEffects({ curated, faersTotal, faersReactions });

  return (
    <div className="text-xs text-zinc-400">
      <p className="mb-1 font-medium text-zinc-300">Adverse effects</p>

      {view.state === "curated" ? (
        <ul className="list-disc space-y-1 pl-4">
          {view.curatedEntries.map((e) => (
            <li key={e.effect}>
              {e.effect}
              {e.note ? <span className="text-zinc-500"> — {e.note}</span> : null}
              <span className="ml-1 text-[10px] text-zinc-500">({e.citation})</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="italic text-zinc-500">{view.headline}</p>
      )}

      <p className="mt-2 border-t border-zinc-800 pt-2 text-[11px]">
        {view.faersHeadline}
      </p>
      {view.faersState === "has_reports" && view.faersReactions.length > 0 && (
        <ul className="mt-1 space-y-0.5 pl-2 text-[10px] text-zinc-500">
          {view.faersReactions.map((r) => (
            <li key={r.term}>{r.term} · {r.count}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Write `PopularitySparklines.tsx`**

```tsx
// frontend/src/app/regulatory/components/PopularitySparklines.tsx
import { Line, LineChart, ResponsiveContainer } from "recharts";
import type { PubmedLiveData, WikipediaLiveData } from "../../lib/types";
import type { LiveEnvelope } from "../../lib/types";

function Sparkline({ data, dataKey }: { data: { value: number }[]; dataKey: string }) {
  if (data.length < 2) return <p className="text-[10px] text-zinc-500">Not enough data</p>;
  return (
    <ResponsiveContainer width="100%" height={32}>
      <LineChart data={data}>
        <Line type="monotone" dataKey={dataKey} stroke="#60a5fa" strokeWidth={1.5} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function PopularitySparklines({
  pubmed,
  wikipedia,
}: {
  pubmed: LiveEnvelope<PubmedLiveData> | undefined;
  wikipedia: LiveEnvelope<WikipediaLiveData> | undefined;
}) {
  if (!pubmed && !wikipedia) return null;

  return (
    <div className="grid grid-cols-2 gap-3 border-t border-zinc-800 pt-3">
      {pubmed?.data && (
        <div>
          <p className="text-[10px] text-zinc-500">Publications/year</p>
          <Sparkline data={pubmed.data.years.map((y) => ({ value: y.count }))} dataKey="value" />
        </div>
      )}
      {/* wikipedia is entirely absent (undefined) when the peptide has no
          curated wikipedia_title -- Task 5's aggregator skip -- so this
          branch simply doesn't render, never a broken/empty sparkline. */}
      {wikipedia?.data && (
        <div>
          <p className="text-[10px] text-zinc-500">Wikipedia pageviews</p>
          <Sparkline data={wikipedia.data.months.map((m) => ({ value: m.views }))} dataKey="value" />
        </div>
      )}
    </div>
  );
}
```

Confirm the exact exported name of the generic live-envelope type (it may
already exist, e.g. `LiveEnvelope<T>` or a per-source type per Task 8 —
read `frontend/src/app/lib/types.ts` after Task 8 lands and adjust the
import to match rather than introducing a duplicate type).

- [ ] **Step 5: Wire into `PeptideCard.tsx`**

```tsx
// frontend/src/app/regulatory/components/PeptideCard.tsx
// add imports:
import { MechanismBlock } from "./MechanismBlock";
import { AdverseEffectsBlock } from "./AdverseEffectsBlock";
import { PopularitySparklines } from "./PopularitySparklines";

// inside the component, after `const fr = peptide.live?.federal_register;`:
  const pubmed = peptide.live?.pubmed;
  const wikipedia = peptide.live?.wikipedia;
  const openfda = peptide.live?.openfda;

// after the closing </dl> of the existing stats grid, before the
// "Regulatory history" <details> block, insert:
      <MechanismBlock mechanism={peptide.mechanism} />

      <AdverseEffectsBlock
        curated={peptide.adverse_effects}
        faersTotal={openfda?.data?.adverse_events_total ?? null}
        faersReactions={openfda?.data?.adverse_event_reactions ?? null}
      />

      <PopularitySparklines pubmed={pubmed} wikipedia={wikipedia} />

      {peptide.pubmed_search_term && (
        <a
          href={`https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(peptide.pubmed_search_term)}`}
          target="_blank"
          rel="noreferrer"
          className="text-[11px] text-blue-400 hover:underline"
        >
          View on PubMed →
        </a>
      )}
```

- [ ] **Step 6: Build + type-check**

```bash
cd frontend && npm install && npx tsc --noEmit && npm run build
```

Expected: both pass with no type errors. If `openfda`'s live-data type
doesn't yet have `adverse_event_reactions` typed, go back and confirm Task
8's edit to that interface landed.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/regulatory/components/MechanismBlock.tsx \
        frontend/src/app/regulatory/components/AdverseEffectsBlock.tsx \
        frontend/src/app/regulatory/components/PopularitySparklines.tsx \
        frontend/src/app/regulatory/components/PeptideCard.tsx
git commit -m "feat(frontend): render mechanism, adverse effects, and popularity sparklines"
```

---

### Task 11 (blocking, non-engineering): Human pilot curation

This task is **not** implemented by an agentic worker. Do not write medical
content, mechanism text, or adverse-effect claims — the honesty contract
requires a human who has actually retrieved and read the source.

**What a human needs to do**, once Tasks 1–10 are merged:

1. For each of **BPC-157** (`bpc-157`), **Semaglutide** (`semaglutide`), and
   **CJC-1295** (`cjc-1295`):
   - Source 2–3 sentences of cited mechanism text from real, retrieved
     literature.
   - Source a curated adverse-effects list (or explicitly confirm none were
     found in the reviewed literature) with real citations.
   - Confirm whether each peptide has an actual Wikipedia article and, if
     so, its exact title (for `wikipedia_title`).
2. Run, per peptide:
   ```bash
   nix develop --command python -m engine.regulatory.curate set-mechanism <slug> \
     --text "<2-3 sentence mechanism>" --citation "<author, year, journal/DOI>"

   nix develop --command python -m engine.regulatory.curate set-adverse-effect <slug> \
     --effect "<effect>" --citation "<author, year, journal/DOI>" [--note "<context>"]
   # repeat set-adverse-effect for each effect found, OR:
   nix develop --command python -m engine.regulatory.curate clear-adverse-effects <slug>
   # if the literature review found none
   ```
   Then set `wikipedia_title` directly in `data/regulatory/peptides.json`
   for any of the three with a confirmed article (no CLI subcommand needed
   for this field — it isn't citation-gated).
3. Run `nix develop --command python -m engine.regulatory.curate validate`
   and commit the result.
4. Also supply the real `U4U_CONTACT_EMAIL` value (Task 3) as an
   External-Secrets-managed env var per `docs/server-management.md`'s
   convention, once the operations contact address is decided — this is
   the same open item the spec flags for the Wikimedia `User-Agent`.

---

## Deferred: Phase B

Reddit anecdote feed (`engine/regulatory/sources/reddit.py` + the quarantined
"Unverified anecdotal reports — not evidence" community panel) is **blocked**
on Hampton supplying Reddit API OAuth credentials (client id + secret) as a
Bitwarden secret. Not planned in detail here per the spec's phasing — when
those credentials exist, write a follow-up plan that:
- Adds `reddit_search_term: str | None` to the peptide schema (intentionally
  omitted in this plan's Task 1).
- Follows the same `_base.cached_fetch` + graceful-degrade contract as every
  other source in `engine/regulatory/sources/`.
- Gates the community panel behind a feature flag that defaults off when the
  Reddit credentials are absent, per the spec's error-handling table.
