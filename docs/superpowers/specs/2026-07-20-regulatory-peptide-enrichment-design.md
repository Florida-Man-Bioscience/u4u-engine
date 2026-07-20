# Regulatory dashboard — per-peptide enrichment

**Status:** Design approved 2026-07-20. Ready for implementation planning.
**Scope:** Enrich each peptide block on `/regulatory` with a PubMed link, a brief
cited mechanism, side-effects / adverse events, two popularity sparklines, and a
quarantined community-anecdote panel.

## Background

`/regulatory` already serves 26 curated peptides (`GET /regulatory/peptides`).
Each entry carries `slug`, `name`, `aliases`, `category`, `pcac_wave`,
`approved_indications`, `medspa_uses`, `history`, plus per-source search terms
(`clinicaltrials_search_term`, `openfda_search_term`,
`federal_register_search_term`). Live sources live in
`engine/regulatory/sources/` behind a common `_base.py`, are cached with a TTL
(`engine/regulatory/cache.py`), and **degrade gracefully** — a dead upstream
never breaks the page. This work extends those existing patterns rather than
introducing new ones.

This dashboard is clinician-facing and tied to the IRB study, so provenance and
the difference between *evidence* and *anecdote* are first-class design
concerns, not polish.

## Decisions (locked)

| Question | Choice |
|---|---|
| Popularity chart source | **Both** free signals: PubMed publications/year + Wikipedia pageviews |
| Adverse events source | **Hybrid**: curated + cited baseline, plus live openFDA FAERS where it genuinely exists, labeled by source |
| Curation strategy | **Ship structure + tooling, curate a pilot set**; everything else shows an explicit "not yet curated" state |
| Forum posts | **Quarantined anecdote feed** — visually distinct, explicitly labeled "unverified, not evidence" |

### Why not Google Trends

There is no free, dependable Google Trends access. The official Trends API has
been **alpha and allowlisted since July 2025** (application + Google Cloud auth
required). `pytrends` is an unofficial scraper that breaks on markup changes,
is rate-limited/IP-blocked from datacenter ranges, and violates ToS — unsuitable
for server-side use in the cluster. Paid providers (SerpApi, DataForSEO, Apify,
Glimpse) work but need budget and a key.

We therefore plot two **free, official, keyless-or-already-keyed** signals:
- **PubMed publications per year** (NCBI E-utilities; `NCBI_API_KEY` already
  configured) — research momentum.
- **Wikipedia monthly pageviews** (Wikimedia Analytics API; no key, ~100 req/s
  anonymous) — the closest free proxy for public/consumer interest.

Neither *is* Google search volume; the UI must label them for what they are.

## Components

### 1. Curated data model

Extend each curated peptide entry with:

- `pubmed_search_term: str` — drives both the PubMed link and the publications
  sparkline (mirrors the existing `*_search_term` fields).
- `wikipedia_title: str | None` — article title for pageviews; `None` when the
  peptide has no article.
- `reddit_search_term: str | None` — for the anecdote feed (Phase B).
- `mechanism: {text: str, citation: str} | None` — 2–3 sentences.
- `adverse_effects: [{effect: str, citation: str, note?: str}] | None`

`mechanism` and every `adverse_effects` entry **require a real citation**. An
uncited entry is invalid and must be rejected by the curation CLI.

**`None` and `[]` mean different things and must never be conflated:**
- `adverse_effects: None` → *not yet curated*. Nobody has looked.
- `adverse_effects: []` → *curated, and no adverse effects were identified in
  the cited literature*. This still must not render as "none reported" or imply
  safety; it renders as "No adverse effects identified in the reviewed
  literature", which says what was actually done.

### 2. New source modules (`engine/regulatory/sources/`)

Each follows the existing `_base.py` contract, is cached via the regulatory
cache TTL, and degrades to "unavailable" rather than raising:

- `pubmed.py` — publication counts per year for a search term (E-utilities
  `esearch` with date facets). Sends `NCBI_API_KEY` when present.
- `wikipedia.py` — monthly pageviews for an article title (Wikimedia Analytics
  API). Must send a descriptive `User-Agent` per Wikimedia policy.
- FAERS adverse events — extend the existing `openfda.py` rather than adding a
  new module, since openFDA is already integrated there.
- `reddit.py` — **Phase B**, recent posts for a search term via the official
  Reddit API (OAuth).

### 3. Curation CLI

`python -m engine.regulatory.curate`, mirroring
`engine/tracking/evidence_update.py` (`list` / `show` / `set` / `remove` /
`validate`). It **refuses to write an uncited `mechanism` or
`adverse_effects` entry**, exactly as the biomarker evidence CLI does.

Pilot curation set: **BPC-157, Semaglutide, CJC-1295**.

### 4. UI — per peptide block

- **PubMed** — link-out built from `pubmed_search_term`.
- **Mechanism** — the curated text with its citation; hidden entirely when not
  curated (never an empty heading).
- **Adverse effects** — curated cited entries first, then FAERS reports labeled
  as such. Four distinct states, which must not be conflated:
  1. curated entries exist → show them;
  2. `adverse_effects` is `None` → "Not yet curated";
  3. `adverse_effects` is `[]` → "No adverse effects identified in the reviewed
     literature";
  4. no FAERS surveillance for this compound → say so explicitly.
  **Never render anything that reads as "no known side effects."** Absence of
  reports means the compound is unmonitored, not safe.
- **Popularity** — two small sparklines, each labeled with its actual meaning
  ("Publications/year", "Wikipedia pageviews"), never labeled "Google Trends".
  A missing signal (e.g. no `wikipedia_title`) omits that sparkline.
- **Community** — a visually distinct panel headed **"Unverified anecdotal
  reports — not evidence"**, placed away from the adverse-effects block, behind
  a feature flag (Phase B).

## Data flow

```
curated JSON ──┐
               ├─► aggregator ──► regulatory cache (TTL) ──► GET /regulatory/peptides ──► UI block
live sources ──┘   (pubmed, wikipedia, openfda/FAERS, reddit*)      *Phase B, flagged
```

## Error handling

| Situation | Behavior |
|---|---|
| Live source errors / times out | Cached value if present, else that section is omitted; page still renders |
| No `wikipedia_title` for a peptide | Omit the pageviews sparkline |
| No FAERS data for a compound | Explicit "no FAERS surveillance" state — never "none reported" |
| Not yet curated | Explicit "Not yet curated" state |
| Reddit creds absent | Feature flag off; community panel not rendered |

## Testing

- Source modules: mocked HTTP (the suite already mocks all external HTTP), one
  test per source for success, empty-result, and upstream-failure paths.
- Curation CLI: rejects an uncited `mechanism`/`adverse_effects` entry; accepts
  a cited one; `validate` catches a malformed entry.
- Graceful degradation: with every live source failing, `GET /regulatory/peptides`
  still returns 200 with curated content intact.
- The four adverse-effects states each render distinctly; assert none of them
  produces text implying safety (no "none reported").
- Frontend build/type-check passes.

## Phasing

- **Phase A (buildable now, no new secrets):** data model, `pubmed.py`,
  `wikipedia.py`, FAERS via `openfda.py`, curation CLI, pilot curation, UI for
  PubMed link / mechanism / adverse effects / sparklines.
- **Phase B (blocked on Hampton):** `reddit.py` + the community panel, gated by
  a feature flag so Phase A can ship without it.

## External dependencies / open items

- **Hampton:** Reddit API OAuth credentials (client id + secret) as a Bitwarden
  secret referenced by UUID, for Phase B.
- Wikimedia policy requires a descriptive `User-Agent`; use
  `u4u-engine/<version> (https://flmanbiosci.net; contact <ops-email>)` — the
  contact address is the one open item here.
- Pilot curation content (BPC-157, Semaglutide, CJC-1295) must be sourced from
  real literature with real citations before merge — no invented claims.

## Out of scope

- Full curation of all 26 peptides (tooling ships; content follows incrementally).
- Google Trends data of any kind (see rationale above).
- Scraping non-Reddit forums (no API; fragile and ToS-hostile).
