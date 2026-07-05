# PeptidIQ — File Map & Module Reference

Generated: April 2026 · **Regenerated: July 2026** (full-tree sync)
Author: Claude (Anthropic) on behalf of Florida Man Biosciences

This document maps the engine and database source tree and explains each module's
purpose, dependencies, and integration points. The April 2026 edition covered only
the original V3 sprint (KEGG mapper + AR CAG caller + the peptide condition library);
it has been regenerated to reflect everything shipped since — the HBRI tracking model,
HealthKit ingestion, the PGx subsystem, ACMG/AMP assembly, the regulatory module, app
user accounts, and the Postgres migration.

Every path below was enumerated from the working tree (`find engine db -type f -name
'*.py'`, `ls db/migrations/`) and each one-line summary is taken from the module's own
docstring. If a path here does not exist, that is a bug in this document — file it.

---

## Directory Tree

```
u4u-engine/
│
├── api.py                                  FastAPI app: /analyze job queue + all mounted routers
├── db/
│   ├── pool.py                             Shared psycopg2 pool + sqlite3-compatible _ConnWrapper
│   ├── migrate.py                          Runs db/migrations/00N_*.sql in order at startup (schema_migrations)
│   ├── schema.sql                          Legacy standalone SQLite schema (superseded by migrations)
│   ├── migrations/
│   │   ├── 001_initial_schema.sql          Jobs, per-variant results, condition library, pipeline output
│   │   ├── 002_caches_and_tracking.sql     Annotation cache, rsID cache, longitudinal biomarker tracking
│   │   ├── 003_peptide_condition_library.sql  Peptide condition-library tables + indexes + triggers
│   │   ├── 004_users.sql                   App user accounts (engine operators)
│   │   ├── 005_ownership_fks.sql           Wires app-user ownership into domain tables
│   │   ├── 006_regulatory_cache.sql        TTL cache for live regulatory sources
│   │   ├── 007_cache_ttl.sql               Adds fetched_at to annotation_cache / rsid_cache
│   │   ├── 008_healthkit.sql               HealthKit ingestion tables (healthkit_*)
│   │   ├── 009_healthkit_device_tokens.sql Interim per-device bearer tokens for HealthKit
│   │   ├── 010_healthkit_subject_map.sql   Subject↔patient identity bridge (healthkit_subject_map)
│   │   └── 011_patient_enrichment.sql      Per-patient pipeline enrichment (PRS / BPC-157 responder inputs)
│   ├── models/
│   │   └── peptide_models.py               SQLAlchemy 2.0 ORM for the peptide condition-library tables
│   └── seeds/
│       └── peptide_seed_data.sql           Seed rows for peptide_condition_library
│
├── data/
│   ├── acmg81_rsids.txt                    ACMG SF rsID whitelist
│   ├── biomarker_evidence.json             Citation-anchored per-biomarker evidence registry
│   ├── condition_library_for_sasank.xlsx   Condition library spreadsheet
│   ├── peptide_genes.bed                   Peptide gene BED intervals
│   ├── peptidiq_engine_schema.json         JSON Schema (2020-12) for scoring engine I/O
│   ├── acmg/                               ACMG reference data
│   └── regulatory/                         Curated regulatory *.json (peptide FDA status)
│
├── engine/                                 Pure-Python analysis library (no web framework at the core)
│   ├── __init__.py                         run_pipeline() entry point
│   ├── pipeline.py                         Orchestrates the full variant analysis pipeline (returns a dict)
│   ├── parsers.py                          VCF / 23andMe / rsID-list parsers
│   ├── validators.py                       Input validation for all data entering the engine
│   ├── quality_filter.py                   Genotype quality filter
│   ├── deduplicator.py                     Removes duplicate variants before annotation
│   ├── filters.py                          rsID whitelist loading (ACMG81, PGx, carrier, traits)
│   ├── rsid_resolver.py                    rsID → genomic coordinate resolution (Ensembl REST + cache)
│   ├── genome_build.py                     Reference-build detection and gating
│   ├── liftover.py                         Optional GRCh37 → GRCh38 liftover
│   ├── scoring.py                          Scores and tiers an annotated variant
│   ├── summary.py                          Plain-English consumer summaries
│   ├── dossier_generator.py               Self-contained HTML dossier reports per peptide
│   ├── annotation_cache.py                Universal SQLite cache for annotation results
│   ├── tenacity.py                        Vendored retry helper (exponential backoff)
│   ├── _vendor/                            Vendored third-party helpers
│   │
│   ├── annotators/                        Per-variant external-source annotators (shared cache)
│   │   ├── cache.py                        Shared cache for all annotator results (SQLite or Postgres)
│   │   ├── vep.py                          Ensembl VEP consequences
│   │   ├── clinvar.py                      ClinVar clinical significance
│   │   ├── gnomad.py                       gnomAD population allele frequencies
│   │   ├── myvariant.py                    MyVariant.info fallback annotator
│   │   ├── uniprot.py                      UniProt protein function / domain / localization
│   │   ├── pharmgkb.py                     PharmGKB drug–gene interactions
│   │   ├── gwas_catalog.py                 NHGRI-EBI GWAS Catalog trait associations
│   │   ├── kegg_mapper.py                  KEGG pathway mapping (offline-first, optional API)
│   │   ├── receptor_mapper.py              Receptor expression + isoform prediction
│   │   ├── prs_calculator.py               Polygenic risk scores for complex traits
│   │   ├── bpc157_predictor.py             BPC-157 response-likelihood prediction
│   │   └── peptide_mapper.py               Peptide therapeutic-efficacy candidate coverage
│   │
│   ├── repeat_callers/
│   │   └── expansion_hunter.py             AR CAG STR caller (wraps ExpansionHunter binary)
│   │
│   ├── peptides/
│   │   ├── biomarkers.py                   Curated peptide → off-label-use → biomarker mapping
│   │   └── measurements.py                 Structured per-peptide biomarker measurement records
│   │
│   ├── tracking/                          HBRI biomarker tracking subsystem (see Module Reference)
│   │   ├── api.py                          FastAPI router (/tracking/*)
│   │   ├── db.py                           Postgres-or-SQLite connection helper
│   │   ├── service.py                      CRUD for patients / treatments / measurements
│   │   ├── models.py                       Tracking-domain dataclasses
│   │   ├── bayes.py                        Normal-Normal conjugate Bayesian update
│   │   ├── analysis.py                     Cohort analysis + predict_response (emits responder_features)
│   │   ├── pooling.py                      Empirical-Bayes hierarchical prior + BLUE combine_priors
│   │   ├── responder_index.py             HBRI responder index η = 1 + Δ·tanh(βᵀx)
│   │   ├── genetics.py                     Synthetic profile + peptide-response prior derivation
│   │   ├── profile_from_job.py            Build a real-data GeneticProfile from an /analyze job
│   │   ├── pharmgkb_catalog.py            Evidence-based variant catalog for the real-data path
│   │   ├── biomarker_params.py            Per-biomarker effect parameters
│   │   ├── evidence.py                    Research-backed, citation-anchored evidence registry
│   │   ├── evidence_update.py             Curator CLI for the evidence registry
│   │   ├── seed.py                        Synthetic tracking-data generator
│   │   ├── healthkit_bridge.py            Maps HealthKit proxy samples onto panel biomarkers
│   │   ├── healthkit_identity.py          Subject_id ↔ patient_id identity bridge
│   │   ├── dose_response.py               Saturating dose-response multiplier — GATED design stub
│   │   ├── cross_biomarker.py             Cross-biomarker residual covariance — GATED design stub
│   │   └── feature_adapters/             Auto-discovering responder-feature registry (@register_adapter)
│   │       ├── genetics_adapter.py        Anchored reference feature (summed genetic weight w)
│   │       ├── prs_adapter.py             Systemic-inflammation PRS responder feature
│   │       ├── bpc157_adapter.py          BPC-157 composite responder feature
│   │       ├── covariates_adapter.py      Demographic effect-modifier features (sex, age, weight)
│   │       └── healthkit_behavior_adapter.py  HealthKit behavioural-covariate feature
│   │
│   ├── healthkit/                         HealthKit ingestion from the peptodyssey iOS app
│   │   ├── api.py                          FastAPI router (/healthkit/samples POST + GET)
│   │   ├── auth.py                         Interim per-device bearer-token auth (fail-closed in prod)
│   │   ├── db.py                           Postgres-or-SQLite connection helper
│   │   ├── schemas.py                      Pydantic ingestion request/response bodies
│   │   └── service.py                      Idempotent upsert-by-uuid ingest + read
│   │
│   ├── users/                             App user accounts (engine operators)
│   │   ├── api.py                          FastAPI router (/users, /users/me)
│   │   ├── db.py                           Postgres-or-SQLite connection helper
│   │   ├── service.py                      CRUD + upsert-from-Authentik-headers
│   │   ├── deps.py                         FastAPI deps resolving the Authentik subject to a users row
│   │   └── models.py                       users-row dataclass
│   │
│   ├── pgx/                               Pharmacogenomics subsystem (shipped)
│   │   ├── orchestrator.py                 Top-level pgx_stage() the pipeline calls
│   │   ├── types.py                        PGx dataclasses
│   │   ├── star_alleles/
│   │   │   ├── detect_input.py             Choose the star-allele caller path
│   │   │   ├── array_caller.py             CPIC-style named-allele matcher (VCF / 23andMe)
│   │   │   ├── bam_caller.py               Optional short-read BAM caller (Aldy 4 / PyPGx / Cyrius)
│   │   │   ├── lr_caller.py                Optional long-read (ONT / PacBio HiFi) caller
│   │   │   ├── hla_caller.py               Tag-SNP HLA risk-allele detection
│   │   │   └── allele_definitions.py       Curated rsID-keyed star-allele definitions
│   │   ├── cpic/
│   │   │   ├── phenoconversion.py          Drug–Drug–Gene Interaction phenoconversion
│   │   │   ├── phenotype.py                Activity score → CPIC phenotype
│   │   │   └── recommendations.py          CPIC drug-recommendation generator
│   │   ├── prs_pgx/
│   │   │   └── scorer.py                   Pharmacogenomic PRS scorer
│   │   └── hgnn/
│   │       ├── graph_build.py              Heterogeneous PGx knowledge graph
│   │       ├── model.py                    Drug-response ranker
│   │       └── conformal.py               Split Mondrian conformal prediction sets
│   │
│   ├── acmg/                              ACMG/AMP (2015) evidence-assembly aid
│   │   ├── classifier.py                   Assemble evidence codes → five-tier classification
│   │   ├── criteria.py                     ACMG/AMP evidence codes + combination rules
│   │   ├── aggregate.py                    Result-level summary + discordance list
│   │   └── signoff.py                      Clinician/laboratory sign-out workflow
│   │
│   └── regulatory/                        FDA peptide regulatory status + live sources
│       ├── aggregator.py                   Merge curated JSON with live source results
│       ├── store.py                        Load curated regulatory JSON; canonical peptide list
│       ├── cache.py                        TTL cache for live source results (Postgres or SQLite)
│       └── sources/
│           ├── clinicaltrials.py           ClinicalTrials.gov v2 trial counts per peptide
│           ├── openfda.py                  openFDA recalls + adverse-event counts
│           ├── federal_register.py         Federal Register notices per peptide
│           ├── regulations_gov.py          Regulations.gov v4 comment counts (FDA docket)
│           └── _base.py                    Shared source-client base
│
└── docs/
    ├── peptidiq-v3-file-map.md            This file
    ├── models/peptide-response-model.md   Authoritative HBRI model spec
    ├── healthkit-storage.md               HealthKit schema + storage design
    ├── architecture.md                    System architecture
    └── … (see docs/ for the full set)
```

---

## Module Reference

### `db/pool.py`

**What it is:** the single shared psycopg2 connection pool (max 25 connections) used by
every Postgres code path. It exposes a `_ConnWrapper` that adds a sqlite3-compatible
`conn.execute()` shortcut so the same service code runs against Postgres or SQLite.

**Selection rule:** Postgres is used whenever `DATABASE_URL` is set; otherwise the module's
callers fall back to SQLite (local dev / tests). See `engine/tracking/db.py`,
`engine/healthkit/db.py`, and `engine/users/db.py` for the per-subsystem `get_conn()` helpers
that consume this pool.

---

### `db/migrate.py`

**What it is:** the migration runner. At application startup it applies every
`db/migrations/00N_*.sql` file in numeric order and records applied versions in a
`schema_migrations` table so each migration runs exactly once.

**Migrations 001–011 (current):**

| # | File | Adds |
|---|------|------|
| 001 | `001_initial_schema.sql` | Jobs, per-variant results, condition library, pipeline output |
| 002 | `002_caches_and_tracking.sql` | Annotation cache, rsID resolver cache, longitudinal biomarker tracking |
| 003 | `003_peptide_condition_library.sql` | Peptide condition-library tables + indexes + triggers |
| 004 | `004_users.sql` | App user accounts (engine operators) |
| 005 | `005_ownership_fks.sql` | App-user ownership foreign keys on domain tables |
| 006 | `006_regulatory_cache.sql` | TTL cache for live regulatory sources |
| 007 | `007_cache_ttl.sql` | `fetched_at` on `annotation_cache` / `rsid_cache` |
| 008 | `008_healthkit.sql` | HealthKit ingestion tables (`healthkit_*`) |
| 009 | `009_healthkit_device_tokens.sql` | Interim per-device bearer tokens for HealthKit |
| 010 | `010_healthkit_subject_map.sql` | De-identified subject_id ↔ patient_id bridge |
| 011 | `011_patient_enrichment.sql` | Per-patient pipeline enrichment (PRS / BPC-157 responder inputs) |

**Run:** applied automatically at startup; no manual `psql -f` needed against a live deploy.

---

### `engine/tracking/` — HBRI biomarker tracking

The tracking subsystem implements the **Hierarchical Bayesian Responder Index (HBRI)**.
The authoritative model spec is [`docs/models/peptide-response-model.md`](models/peptide-response-model.md);
this section is only a file map of the implementation.

**Core prediction path:**

- **`responder_index.py`** — the responder index. A patient's response magnitude is
  `η = 1 + Δ·tanh(βᵀx)` with `Δ = R_DELTA_SCALE = 0.72`, generalising the legacy scalar
  `1 + Δ·tanh(w)` into a regularised multi-feature index. `x` is the stacked feature vector
  produced by the feature-adapter registry.
- **`feature_adapters/`** — an auto-discovering registry: every submodule is imported on
  package load so adapters decorated with `@register_adapter` self-register. Shipped adapters:
  - `genetics_adapter.py` — the anchored reference feature (summed genetic weight `w`); the
    index reduces **exactly** to the legacy genetics-only model when it is the only feature.
  - `prs_adapter.py` — signed, standardised systemic-inflammation PRS feature.
  - `bpc157_adapter.py` — composite BPC-157 responder feature wrapping the offline predictor.
  - `covariates_adapter.py` — demographic effect modifiers (sex, birth year, weight).
  - `healthkit_behavior_adapter.py` — HealthKit **behavioural-covariate** feature (kept
    disjoint from HealthKit-as-biomarker-observation, per model spec §4).
- **`pooling.py`** — empirical-Bayes hierarchical prior for a `(peptide, biomarker)` cell.
  `combine_priors()` performs **correlation-aware BLUE fusion** (takes an assumed error
  correlation ρ to avoid double-counting), replacing the older fused-precision cap.
- **`bayes.py`** — Normal-Normal conjugate update of the latent response θ.
- **`analysis.py`** — cohort trajectories + `predict_response`; the prediction output now
  includes a **`responder_features`** list (each feature's contribution to η).

**Data + evidence:** `biomarker_params.py` (effect magnitudes), `evidence.py` +
`evidence_update.py` (citation-anchored, grade-tagged registry over
`data/biomarker_evidence.json`), `pharmgkb_catalog.py` and `profile_from_job.py` (real-data
`GeneticProfile` path), `seed.py` (synthetic demo data), `genetics.py` (synthetic profiles).

**HealthKit seam:** `healthkit_identity.py` (subject↔patient bridge, backed by migration 010)
and `healthkit_bridge.py` (proxy samples → panel-biomarker observations).

**Gated design stubs (not wired into any live prediction):** `dose_response.py` (saturating
dose-response multiplier) and `cross_biomarker.py` (cross-biomarker residual covariance).

**Plumbing:** `api.py` (router at `/tracking/*`), `db.py`, `service.py`, `models.py`.

---

### `engine/healthkit/` — HealthKit ingestion

Receives batches of Apple HealthKit samples from the peptodyssey iOS app and stores them in
the de-identified `healthkit_*` tables. Design: [`docs/healthkit-storage.md`](healthkit-storage.md).

- **`api.py`** — router mounted at `/healthkit`: `POST /healthkit/samples` (ingest) and
  `GET /healthkit/samples` (read).
- **`auth.py`** — interim per-device bearer-token auth. **Fail-closed in production**
  (enforced when `DATABASE_URL` is set) and open in local dev, so the write endpoint is not
  an open door. Device tokens live in the table from migration 009.
- **`service.py`** — ingest + read, database-agnostic (Postgres via `db/pool.py`, SQLite
  fallback). Idempotent: samples upsert by UUID with `ON CONFLICT DO NOTHING`, so re-syncs and
  `HKAnchoredObjectQuery` replays are safe.
- **`schemas.py`** — Pydantic bodies (`class` aliased, ISO-8601 datetimes).
- **`db.py`** — same Postgres-or-SQLite switch as the other subsystems.

The de-identified `subject_id` is bridged to a tracking `patient_id` via
`engine/tracking/healthkit_identity.py` and `healthkit_subject_map` (migration 010).

---

### `engine/users/` — app user accounts

App-user (engine operator) accounts. Assumes an **Authentik** forward-auth proxy in front:
every request that reaches the API already carries a trusted subject header.

- **`api.py`** — router at `/users` (`GET /users`, `GET /users/me`).
- **`deps.py`** — FastAPI dependencies resolving the Authentik subject to a local `users` row.
- **`service.py`** — CRUD + upsert-from-headers. **`db.py`**, **`models.py`** as elsewhere.

Backed by migration 004 (`users`) and migration 005 (ownership FKs on domain tables).

---

### `engine/pgx/` — pharmacogenomics (shipped)

Star-allele calling, CPIC phenotype/recommendation engine, DDGI phenoconversion,
pharmacogenomic PRS, and a heterogeneous-graph drug-response ranker with conformal
prediction sets. Entry point: `orchestrator.pgx_stage(variants, medications=None,
bam_path=None, confidence=0.90)`, called by the main pipeline.

- **`star_alleles/`** — `detect_input.py` picks the caller path; `array_caller.py`
  (VCF / 23andMe), optional `bam_caller.py` (Aldy 4 / PyPGx / Cyrius), `lr_caller.py`
  (ONT / PacBio HiFi), `hla_caller.py` (tag-SNP HLA), `allele_definitions.py` (curated defs).
- **`cpic/`** — `phenotype.py` (activity score → phenotype), `phenoconversion.py` (DDGI),
  `recommendations.py` (CPIC drug recommendations).
- **`prs_pgx/scorer.py`** — pharmacogenomic PRS.
- **`hgnn/`** — `graph_build.py` (knowledge graph), `model.py` (ranker), `conformal.py`
  (split Mondrian conformal prediction sets). Calibration is gated by
  `PGX_CONFORMAL_CALIBRATION`; without it predictions are marked `uncalibrated`.

---

### `engine/acmg/` — ACMG/AMP evidence assembly

Assembles the subset of ACMG/AMP (2015) evidence codes the engine can support from existing
annotations. It is an **evidence-assembly aid, not a final clinical determination**.

- **`criteria.py`** — evidence codes + combination rules → five-tier classification.
- **`classifier.py`** — `classify_acmg(variant, config)` assembles + combines.
- **`aggregate.py`** — result-level summary, notably the **discordance** list.
- **`signoff.py`** — required qualified-human sign-out
  (`POST /jobs/{job_id}/variants/{variant_id}/acmg-signoff`).

---

### `engine/regulatory/` — FDA peptide regulatory status

Curated peptide FDA status merged with live sources; served at `/regulatory/peptides` and
`/regulatory/events`. Live-source failures degrade gracefully.

- **`store.py`** — loads curated `data/regulatory/*.json`; canonical peptide list.
- **`aggregator.py`** — merges curated + live into the served payload.
- **`cache.py`** — TTL cache (Postgres via migration 006, or SQLite).
- **`sources/`** — `clinicaltrials.py`, `openfda.py`, `federal_register.py`,
  `regulations_gov.py` (+ shared `_base.py`).

---

### `data/peptidiq_engine_schema.json`

JSON Schema (draft 2020-12) formally specifying the input/output contract for the scoring
engine: an `input_layer`, an `evidence_layer` with `const`-pinned weights, an engine-written
`outcome_layer`, and a `logic_flow` referencing the pipeline step sequence.

---

### `db/migrations/003_peptide_condition_library.sql`, `db/models/peptide_models.py`, `db/seeds/peptide_seed_data.sql`

The original V3 peptide condition library. Migration 003 creates
`peptide_condition_library` and `peptide_trade_offs` (partial / GIN / composite indexes;
`set_updated_at()` triggers). `peptide_models.py` is the SQLAlchemy 2.0 ORM
(`Mapped[]` annotations, `AsyncSession`) with helpers `get_peptide_responses`,
`get_trade_off`, `get_contraindicated_peptides`. `peptide_seed_data.sql` seeds the library.

---

### `engine/repeat_callers/expansion_hunter.py`

Python wrapper around Illumina's ExpansionHunter binary for calling the AR CAG short tandem
repeat from BAM/CRAM. Entry point `call_ar_cag_repeat(bam_path, sex, ancestry)`; ancestry
reference means and shorter-CAG-⇒-higher-sensitivity tiers as before. `parse_eh_output()`
can extract counts from existing ExpansionHunter VCF/JSON without rerunning the binary.
Requires the ExpansionHunter binary on `PATH` and an hg38 reference FASTA for live calling.

---

### `engine/annotators/kegg_mapper.py`

Maps variant gene symbols to eight priority KEGG signaling pathways with plain-English
implication text. Entry points `map_variants_to_pathways(genes)` and
`generate_pathway_summary(hits)`. Offline-first (gene membership hardcoded); pass
`use_api=True` with a `KEGGCache` to optionally refresh from rest.kegg.jp.

---

## Integration Notes

### Database setup

Migrations are applied automatically by `db/migrate.py` at application startup (tracked in
`schema_migrations`). Postgres is used when `DATABASE_URL` is set; otherwise subsystems fall
back to SQLite for local dev and tests. There is no manual `psql -f` step in a live deploy.

### Routers mounted in `api.py`

`api.py` wraps `run_pipeline()` in an async job queue (`POST /analyze` → poll
`GET /jobs/{job_id}`) and mounts: `/tracking/*` (`engine/tracking/api.py`), `/healthkit/*`
(`engine/healthkit/api.py`), `/users` (`engine/users/api.py`), `/regulatory/*`, and the ACMG
sign-off endpoint. Jobs persist to Postgres when `DATABASE_URL` is set (in-memory fallback
otherwise); the old `JOB_STORE_KEY`/Fernet on-disk job store is deprecated and unused.

### `run_pipeline()` return shape

`run_pipeline(file_bytes, filename, filters=[...])` returns a **dict** — keys `variants`,
`pathway_summary`, `receptor_genetics`, `prs_profile`, `ar_cag_repeat`,
`peptide_recommendations`, `pgx_profile`, `dossiers`, `acmg_summary`, `analysis_status` —
not a list of dicts.

---

## Footnotes

[^jsonschema]: **JSON Schema (draft 2020-12)** — a versioned standard for describing and validating JSON structure; the `const` keyword pins a value so the evidence weights can never drift.
[^migration]: **Migration** — a versioned, ordered SQL script that incrementally changes a database schema; running migrations in sequence brings any database to the current structure.
[^blue]: **BLUE (Best Linear Unbiased Estimator)** — the minimum-variance unbiased linear combination of several noisy estimates; `pooling.combine_priors` uses a correlation-aware BLUE so correlated sources are not double-counted.
[^conjugate]: **Conjugate prior (Normal-Normal)** — when prior and likelihood are both Normal, the posterior is Normal too, so the Bayesian update is a closed-form weighted average rather than a numerical integration.
[^conformal]: **Conformal prediction** — a distribution-free method that turns a point predictor into calibrated prediction *sets* with a guaranteed coverage rate; "Mondrian" conditions that guarantee within groups.
[^ddgi]: **DDGI (Drug–Drug–Gene Interaction) / phenoconversion** — a co-prescribed inhibitor/inducer can shift a patient's *genotype-predicted* metabolizer phenotype to a different *observed* one; phenoconversion adjusts for it.
[^orm]: **ORM (Object-Relational Mapper)** — SQLAlchemy maps tables to Python classes so rows are manipulated as objects rather than raw SQL.
[^str]: **STR (Short Tandem Repeat)** — a short DNA motif repeated in a row; the repeat count can be clinically meaningful (e.g. the AR CAG repeat).
[^bam]: **BAM / CRAM** — compressed binary formats storing aligned sequencing reads; repeat calling needs the raw reads, not just a variant list.
[^hg38]: **hg38 (GRCh38)** — the current human reference genome assembly; coordinates are positions within it.
[^kegg]: **KEGG (Kyoto Encyclopedia of Genes and Genomes)** — a public database of biological pathways.
[^authentik]: **Authentik** — the identity provider running as a forward-auth proxy in the deployment; it authenticates requests and passes a trusted subject header the `engine/users` layer maps to a local account.
