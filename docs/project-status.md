# Project Status

> **Note (2026-07):** this file has been reconciled with shipped reality. The
> MVP has been superseded — the frontend is built and deployed, Postgres is
> wired, and pharmacogenomics / research tracking / PRS have all shipped. See
> **[Now shipped — previously listed as missing](#now-shipped--previously-listed-as-missing)**.

---

## MVP scope (historical)

The original 4-week MVP was: VCF upload → annotation engine → interactive
dashboard, no genome storage, email capture for future research updates. That
scope shipped and the product has since grown well past it (PGx, tracking, PRS,
HealthKit, a deployed Next.js frontend).

---

## What works

- Parses VCF / `.vcf.gz` (primary), 23andMe `.txt`, CSV, rsID lists
- 10-step pipeline (`engine/pipeline.py`): validate → parse → quality filter → whitelist → rsID resolution → deduplicate → annotate → score → summarize → sort. `run_pipeline()` returns a rich **`dict`** (keys: `variants`, `pathway_summary`, `receptor_genetics`, `prs_profile`, `ar_cag_repeat`, `peptide_recommendations`, `pgx_profile`, `dossiers`, `acmg_summary`, `analysis_status`)
- Annotates against ClinVar, gnomAD, Ensembl VEP[^vep], MyVariant.info (fallback), UniProt, PharmGKB, GWAS Catalog (retry + fallback)
- Returns plain-English headline, consequence, rarity, action hint per variant
- FastAPI job queue (`api.py`) — `POST /analyze` → 202 + `job_id`, `GET /jobs/:id` for polling. Jobs persist to **Postgres when `DATABASE_URL` is set**; in-memory fallback otherwise. (The old `JOB_STORE_KEY`/Fernet on-disk job store is **deprecated and unused** — `api.py` emits a deprecation warning if the var is set.)
- **Postgres backing** for annotation cache, rsID cache, tracking, jobs, and HealthKit — via `db/pool.py` when `DATABASE_URL` is set, with SQLite fallback for local dev/tests. Schema is applied by `db/migrate.py` (`run_migrations`, called at startup), which runs `db/migrations/00N_*.sql` files `001`–`011` and tracks them in a `schema_migrations` table.
- Deployed to a self-hosted RKE2 Kubernetes cluster, public at **`flmanbiosci.net`** (GitOps via Flux)
- CI on push via GitHub Actions (Python 3.11 and 3.12)

### PeptidIQ V3[^peptidiq] — Peptide Response Interpretation Engine ✅

Added April 2026. Extends the genomics pipeline into a clinically actionable peptide and hormone response system.

**Peptide Condition Library** (`db/migrations/003_peptide_condition_library.sql`, `db/models/peptide_models.py`, `db/seeds/peptide_seed_data.sql`)
- Two new Postgres tables: `peptide_condition_library` and `peptide_trade_offs`
- SQLAlchemy 2.0 ORM[^orm] models with async[^async] helpers (`get_peptide_responses`, `get_trade_off`, `get_contraindicated_peptides`)
- 12 seeded rows covering AR, ESR1, ESR2, OXTR, MC4R, GLP1R, RET, TP53, BRCA1[^peptidegenes] with clinically detailed genotype–peptide response data
- JSON Schema 2020-12[^jsonschema] for scoring engine input/output format (`data/peptidiq_engine_schema.json`)

**ExpansionHunter[^expansionhunter] STR[^str] Calling** (`engine/repeat_callers/expansion_hunter.py`)
- Wraps Illumina ExpansionHunter binary to call AR CAG repeat[^arcag] directly from BAM/CRAM[^bam] files
- Clinical interpretation with 6 sensitivity tiers (VERY_LOW_PATHOLOGIC → VERY_HIGH) and severity flags
- Ancestry-adjusted[^ancestry] reference ranges (African, Caucasian, Hispanic, Asian)
- Graceful degradation: operates from VCF-only when no BAM is available
- 58 unit tests — all passing (`tests/test_engine/test_expansion_hunter.py`)

**KEGG Pathway Mapper**[^kegg] (`engine/annotators/kegg_mapper.py`)
- Maps patient variant gene symbols to 8 priority KEGG pathways: Estrogen signalling, GnRH signalling, Serotonergic synapse, MAPK, PI3K-AKT, Adipocytokine, Melanocortin/MC4R, Steroid hormone biosynthesis[^pathways]
- Fully offline via hardcoded gene membership; optional KEGG REST API refresh with SQLite caching
- Per-gene clinical implication generation (~50 curated gene–pathway notes)
- Cross-pathway combination notes for 7 clinically relevant co-hit[^cohit] pairs
- 53 unit tests — all passing (`tests/test_engine/test_kegg_mapper.py`)

**Predictive Logic Architecture** — spec documented in Notion[^notion] (Predictive Logic Architecture page); 4-layer scoring engine (Input → Evidence [35/25/20/20 weights] → Outcome → Logic Flow).

**Biomarker Tracking — HBRI unified peptide-effect model** (`engine/tracking/`) ✅

The tracking subsystem has been upgraded from the original scalar Normal–Normal
model to the **Hierarchical Bayesian Responder Index (HBRI)**. The authoritative
spec is [`docs/models/peptide-response-model.md`](models/peptide-response-model.md).

- **Responder index** (`responder_index.py`): `η = 1 + Δ·tanh(βᵀx)` with `Δ = R_DELTA_SCALE = 0.72`, a bounded per-patient/per-biomarker multiplier over the linear feature score `βᵀx`.
- **Auto-discovering feature-adapter registry** (`engine/tracking/feature_adapters/`): each `*_adapter.py` self-registers via `@register_adapter` on package load — genetics, PRS, BPC-157, demographic covariates, and HealthKit behaviour adapters ship. Dropping a new adapter file requires no edit to any shared file.
- **Correlation-aware BLUE fusion** (`pooling.combine_priors`): a best-linear-unbiased-estimator fusion of the genetics-derived prior and leave-one-out cohort pooling under an assumed error correlation `ρ`, replacing the previous fused-precision cap and fixing double-counting.
- **Pipeline enrichment wiring** (`patient_enrichment`, migration `011`): pipeline-derived enrichment feeds the responder context.
- **Prediction output** now includes a `responder_features` field (per-feature contributions) alongside the posterior with 95% credible intervals and forward predictive curve. Bayesian conjugate math still lives in `bayes.py`.
- **Gated design stubs**: `dose_response.py` (saturating dose→multiplier) and `cross_biomarker.py` (cross-biomarker covariance) ship gated/off by default.
- REST API mounted at `/tracking/*`; the generative model is documented in-app at `/tracking/model`.

- **Research-backed evidence registry** (`engine/tracking/evidence.py` + `data/biomarker_evidence.json`): citation-anchored, grade-tagged (A–D) per-biomarker effect entries. The evidence grade sets the prior's `relative_sd` — tighter for well-evidenced markers, flat `PANEL_REL_SD` fallback for the (still majority) uncited markers. Honesty contract: an entry requires ≥1 real, retrieved citation (DOI); curate via `python -m engine.tracking.evidence_update`.
- **GLP-1 / incretin class** (Semaglutide, Tirzepatide, Liraglutide) integrated as first-class, grade-A evidence-backed peptides, with class-qualified marker names (e.g. `Body weight (GLP-1 RA)`) so their large, well-evidenced effects do not bleed onto the smaller generic markers shared by weaker peptides (AOD-9604, MOTS-c).

**HealthKit ingestion** (`engine/healthkit/`) ✅
- iOS app (`peptodyssey`) syncs de-identified HealthKit samples to `POST`/`GET /healthkit/samples` (router mounted in `api.py`).
- **Device-token auth** (`engine/healthkit/auth.py`), **fail-closed when `DATABASE_URL` is set** (migration `009` device tokens).
- **Subject ↔ patient bridge** (`healthkit_subject_map`, migration `010`; `engine/tracking/healthkit_identity.py` + `healthkit_bridge.py`) links opaque HealthKit subjects to tracking patients, feeding the HealthKit behaviour feature adapter.

**Pharmacogenomics (PGx)** (`engine/pgx/`) ✅
- Orchestrated by `pgx/orchestrator.py`: star-allele calls → HLA tag-SNP calls → CPIC phenoconversion → drug recommendations + PRS + HGNN conformal prediction sets. Served at `GET /jobs/{id}/pgx` and `GET /jobs/{id}/drug/{drug}`; the frontend results view defaults to the **`pgx`** tab.

**Polygenic Risk Scores (PRS)** (`engine/annotators/prs_calculator.py`) ✅
- PRS profiles are computed in-pipeline (`prs_profile` output key) and also surface as a tracking responder feature (`engine/tracking/feature_adapters/prs_adapter.py`).

**ACMG/AMP classification** (`engine/acmg/`) — evidence-assembly aid requiring qualified human sign-out via `POST /jobs/{id}/variants/{variant_id}/acmg-signoff`.

**Regulatory module** (`engine/regulatory/`) — curated peptide FDA status merged with live sources; served at `/regulatory/peptides` and `/regulatory/events` (migration `006` cache).

**Users / auth** (`engine/users/`) — `/users` router (`/users/me`, `/users`) mounted in `api.py` (migration `004` users, `005` ownership FKs).

---

## Repo

```
engine/
  annotators/       ClinVar, gnomAD, VEP, MyVariant, UniProt, PharmGKB,
                    GWAS Catalog, kegg_mapper, receptor_mapper,
                    prs_calculator, bpc157_predictor, peptide_mapper
  repeat_callers/   ExpansionHunter STR caller (AR CAG repeat)
  peptides/         peptide biomarker + measurement catalogs
  tracking/         HBRI tracking: responder_index.py, bayes.py, pooling.py
                    (BLUE fusion), analysis.py, evidence registry,
                    healthkit_identity.py / healthkit_bridge.py,
                    dose_response.py + cross_biomarker.py (gated stubs),
                    feature_adapters/ (auto-discovering adapter registry)
  healthkit/        HealthKit ingestion: api.py, auth.py (device token),
                    service.py, db.py, schemas.py
  pgx/              pharmacogenomics: orchestrator.py, star_alleles/, cpic/,
                    hgnn/, prs_pgx/
  acmg/             ACMG/AMP classifier + human sign-off
  regulatory/       curated + live FDA peptide status (aggregator, sources/)
  users/            users/auth router + service
  pipeline.py       run_pipeline() entry point (returns a dict)
  scoring.py        scoring + tier logic
  summary.py        plain-English text generation
api.py              FastAPI app: analyze/jobs + /tracking, /healthkit, /users,
                    /regulatory routers + ACMG sign-off; startup runs migrations
db/
  pool.py           shared psycopg2 pool + sqlite3-compatible conn wrapper
  migrate.py        run_migrations() — applies 00N_*.sql, tracks schema_migrations
  schema.sql        base Postgres schema
  migrations/       001 initial · 002 caches+tracking · 003 peptide condition
                    library · 004 users · 005 ownership FKs · 006 regulatory
                    cache · 007 cache TTL · 008 healthkit · 009 healthkit device
                    tokens · 010 healthkit subject map · 011 patient enrichment
  models/           SQLAlchemy ORM models (peptide_models.py)
  seeds/            seed data SQL (peptide_seed_data.sql)
data/
  acmg81_rsids.txt
  biomarker_evidence.json          ← citation-anchored evidence registry
  peptidiq_engine_schema.json      ← JSON Schema 2020-12 for scoring engine I/O
frontend/           Next.js 15 app (built + deployed): /, /jobs/[id],
                    /jobs/[id]/results (peptides|pgx|variants tabs, pgx default),
                    /tracking, /tracking/cohort, /regulatory, /study
tests/              all unit + integration tests
docs/               documentation (this file, architecture, roadmap, etc.)
.github/            CI, issue templates, PR template
```

---

## Now shipped — previously listed as missing

The earlier "What doesn't exist" table is obsolete. The items below have all shipped:

| Area | Then | Now |
|------|------|-----|
| Docker build + K8s deployment | Not deployed | **Deployed** to self-hosted RKE2, public at `flmanbiosci.net` (Docker + Flux GitOps) |
| Postgres instance running | Schema exists — not wired | **Wired** via `db/pool.py`; `db/migrate.py` applies migrations `001`–`011` at startup |
| Frontend | Not built | **Built + deployed** — Next.js 15 app (`frontend/`); routes `/`, `/jobs/[id]`, `/jobs/[id]/results`, `/tracking`, `/tracking/cohort`, `/regulatory`, `/study` |
| Domain + DNS | Not registered | **Live** at `flmanbiosci.net` |
| FastAPI endpoints for peptide response | Not yet wired | **Live** — `/tracking/*` router mounted in `api.py`; also `/healthkit/*`, `/users`, `/regulatory/*` |

### Genuinely open / environment-dependent

| Area | Status |
|------|--------|
| Condition library content | <!-- NEEDS REVIEW: confirm current ACMG SF row coverage against seeded data --> ACMG SF coverage still being expanded |
| Security audit | <!-- NEEDS REVIEW: confirm current status --> Plan in `U4U_Cybersecurity_Execution_Plan.docx`; HealthKit uses device-token auth (fail-closed with `DATABASE_URL`) |
| ExpansionHunter binary + reference FASTA[^fasta] | Optional runtime dep — must be installed in the deployment environment; pipeline degrades to VCF-only without it |

---

## UI

The Next.js 15 frontend is built and deployed (see [`docs/frontend.md`](frontend.md)).
It has grown past the original three-screen MVP (Upload → Processing → Results)
into a multi-surface app: genome upload (`/`), job progress (`/jobs/[id]`),
results with `peptides | pgx | variants` tabs (`pgx` default), longitudinal
tracking (`/tracking`, `/tracking/cohort`), the FDA regulatory dashboard
(`/regulatory`), and the study surface (`/study`).

The variant results view still renders a **prioritized findings report** —
expandable rows with a colored left border (tier color), grouped into "Needs
Attention" (critical + high) and "For Your Records" (medium + low + carrier).

**Tier visual treatment:**

| `tier` | Border | Emoji |
|--------|--------|-------|
| critical | red | 🔴 |
| high | orange | 🟠 |
| medium | yellow | 🟡 |
| low | green | 🟢 |
| carrier | blue | 🔵 |

**Error states:**

| State | Behavior |
|-------|----------|
| File too large / unsupported format | Inline error before submit |
| Invalid VCF header | Error screen after submit |
| All variants filtered | Results page with explanation |
| Zero ACMG findings | Message, not blank |
| Network error | Error screen with retry |
| Partial results | Show succeeded, note how many failed |

---

## Beyond the original V1 — now shipped

Most items once deferred past V1 have shipped:

- **Pharmacogenomics** — `engine/pgx/` (star alleles, CPIC phenoconversion, drug recs, HGNN conformal sets); results `pgx` tab.
- **Research / biomarker tracking** — `engine/tracking/` (HBRI model, `/tracking/*` API, `/tracking` + `/tracking/cohort` UI).
- **PRS[^prs]** — `engine/annotators/prs_calculator.py` (`prs_profile` output) + tracking `prs_adapter`.
- **User accounts / auth** — `engine/users/` (`/users` router; migrations `004`/`005`).
- **Saved results** — jobs persist to Postgres when `DATABASE_URL` is set.
- **Mobile** — the `peptodyssey` iOS app syncs HealthKit into `engine/healthkit/`.

Still genuinely future: email delivery and a public API for external developers.
<!-- NEEDS REVIEW: confirm email-delivery and external-developer-API status. -->

---

---

## Footnotes

[^vep]: **Ensembl VEP (Variant Effect Predictor)** — Ensembl's tool/API that annotates variants with predicted molecular consequences and affected genes.
[^peptidiq]: **PeptidIQ V3** — the project's peptide-response interpretation layer (version 3), extending the genomics pipeline to predict how a person's genotype affects their response to peptide/hormone therapies.
[^orm]: **ORM (Object-Relational Mapper)** — a library (here SQLAlchemy 2.0) that maps database tables to Python objects, so queries are written in Python instead of raw SQL.
[^async]: **async helpers** — non-blocking functions (Python `async`/`await`) that let the server handle other work while waiting on database I/O.
[^peptidegenes]: **AR, ESR1, ESR2, OXTR, MC4R, GLP1R, RET, TP53, BRCA1** — genes seeded in the peptide library: androgen receptor (AR), estrogen receptors α/β (ESR1/ESR2), oxytocin receptor (OXTR), melanocortin-4 receptor (MC4R), GLP-1 receptor (GLP1R), the RET proto-oncogene, and the tumor-suppressors TP53/BRCA1.
[^jsonschema]: **JSON Schema 2020-12** — a versioned standard (draft 2020-12) for formally describing and validating the structure of JSON documents; used to lock the scoring engine's input/output format.
[^expansionhunter]: **ExpansionHunter** — an Illumina open-source tool that estimates the size of short tandem repeat expansions directly from aligned sequencing reads.
[^str]: **STR (Short Tandem Repeat)** — a stretch of DNA where a short motif repeats many times (e.g. `CAG CAG CAG…`); the number of repeats can be disease-relevant.
[^arcag]: **AR CAG repeat** — the polyglutamine (CAG)ₙ repeat in the androgen receptor (AR) gene; its length modulates receptor activity and is clinically significant (e.g. in spinal-bulbar muscular atrophy and androgen sensitivity).
[^bam]: **BAM / CRAM** — compressed binary formats for aligned sequencing reads. BAM is the classic format; CRAM is a more compressed, reference-based successor. Repeat calling needs the actual reads, not just a variant list.
[^ancestry]: **Ancestry-adjusted reference ranges** — "normal" repeat-length distributions differ by genetic ancestry, so the interpretation thresholds are calibrated per population group to avoid mis-flagging.
[^kegg]: **KEGG (Kyoto Encyclopedia of Genes and Genomes)** — a public database of biological pathways; a "pathway" is a known network of interacting genes/proteins carrying out a cellular process.
[^pathways]: **The 8 pathways** — biological signalling/metabolic networks: estrogen signalling, GnRH (gonadotropin-releasing hormone) signalling, serotonergic synapse (serotonin neurotransmission), MAPK and PI3K-AKT (core cell-growth cascades), adipocytokine (fat-tissue signalling), melanocortin/MC4R (appetite/energy), and steroid-hormone biosynthesis.
[^cohit]: **Co-hit** — when a patient carries variants in two genes that fall in related pathways at once; such combinations can carry extra clinical meaning beyond either gene alone.
[^notion]: **Notion** — a collaborative documentation/wiki app where the predictive-logic spec is maintained.
[^fasta]: **FASTA** — a plain-text format for reference DNA/protein sequences; ExpansionHunter needs the reference genome FASTA to interpret read alignments.
[^prs]: **PRS (Polygenic Risk Score)** — a single score aggregating the small effects of many variants to estimate genetic predisposition to a trait or disease.

Roadmap: `docs/roadmap.md`
