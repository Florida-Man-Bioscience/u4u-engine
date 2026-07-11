# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This is a NixOS project. Always use `nix develop` to get the correct Python 3.12 environment — never the system Python or `.venv`.

```bash
# Enter the dev shell
nix develop

# Run all tests
nix develop --command python -m pytest tests/ -v

# Run a single test file
nix develop --command python -m pytest tests/test_engine/test_annotators.py -v

# Run a single test by name
nix develop --command python -m pytest tests/ -v -k "test_clinvar_fetch"

# Run the Postgres smoke tests (off by default — boots an ephemeral PG
# via initdb + pg_ctl and exercises the DATABASE_URL code paths)
PG_TESTS=1 nix develop --command python -m pytest tests/test_postgres_smoke.py -v
```

The `.venv/` in the repo root is a leftover from earlier development — don't use it.

## Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev          # dev server on :3000
npm run build        # production build
```

The frontend expects the backend at `NEXT_PUBLIC_API_BASE` (default: `http://localhost:8000`).

## Backend API (FastAPI)

```bash
# Local (requires pip-installed deps: fastapi, uvicorn, python-multipart, cryptography, bcrypt)
uvicorn api:app --reload

# Or via Docker
docker compose up --build
```

Health check: `GET /health` → `{"status":"ok","jobs_running":0,"jobs_pending":0}`

## Architecture

### The Engine (`engine/`)

The core analysis pipeline (`run_pipeline`) is a pure Python library — no web
framework, no database. Some newer subsystems under `engine/` are **not** pure,
however: `engine/tracking/` and `engine/healthkit/` each ship their own FastAPI
router (`api.py`) and database access layer (`db.py`), and `engine/users/`
likewise. Entry point for the core pipeline:

```python
from engine import run_pipeline
result = run_pipeline(file_bytes, filename, filters=[...])
```

`engine/pipeline.py` orchestrates 10 steps: validate → parse → quality filter → whitelist filter → rsID resolution → deduplicate → annotate (parallel, 8 threads) → score → summarize → sort. Returns a rich `dict` with keys: `variants`, `pathway_summary`, `receptor_genetics`, `prs_profile`, `ar_cag_repeat`, `peptide_recommendations`, `pgx_profile`, `dossiers`, `acmg_summary`, `analysis_status`.

**Annotators** (`engine/annotators/`): VEP, ClinVar, gnomAD, MyVariant.info (fallback), UniProt, PharmGKB, GWAS Catalog. All share one annotation cache via `engine/annotators/cache.py` — Postgres when `DATABASE_URL` is set, otherwise a local SQLite file at `data/annotation_cache.db` (dev/tests). Cache is keyed `(source, lookup_key)` and caches both results and `None` (no-data-found).

**V3 enrichment modules** run after per-variant annotation:
- `engine/annotators/kegg_mapper.py` — KEGG pathway mapping
- `engine/annotators/receptor_mapper.py` — receptor expression + isoform prediction  
- `engine/annotators/prs_calculator.py` — polygenic risk scores
- `engine/annotators/bpc157_predictor.py` — BPC-157 peptide response prediction
- `engine/annotators/peptide_mapper.py` — peptide therapy candidate coverage
- `engine/repeat_callers/expansion_hunter.py` — AR CAG repeat calling (optional, requires BAM)

**PGx pipeline** (`engine/pgx/`): orchestrated by `pgx/orchestrator.py`. Four phases: star-allele calls (array/BAM/long-read) → HLA tag-SNP calls → CPIC phenoconversion → drug recommendations + PRS + HGNN conformal prediction sets.

**ACMG/AMP classification** (`engine/acmg/`): evidence assembly aid (not a final clinical determination). Requires qualified human sign-out via `POST /jobs/{job_id}/variants/{variant_id}/acmg-signoff`.

**Regulatory module** (`engine/regulatory/`): curated peptide FDA status merged with live sources (ClinicalTrials.gov, openFDA, Federal Register). Served at `/regulatory/peptides` and `/regulatory/events`. Live source failures degrade gracefully.

**Biomarker tracking** (`engine/tracking/`): longitudinal biomarker tracking with Bayesian posterior updates, backed by Postgres when `DATABASE_URL` is set (SQLite fallback for dev/tests). REST API mounted at `/tracking/...` via `engine/tracking/api.py`. Authoritative model spec: [`docs/models/peptide-response-model.md`](docs/models/peptide-response-model.md).

`analysis.predict_response` fits baseline `b` and the plateau fractional-change θ jointly, then does a Normal–Normal conjugate update (`bayes.py`) against a prior whose mean is `η · expected_pct_k`, producing a posterior with 95% credible intervals plus a predictive curve. The prior mean is scaled by the **Hierarchical Bayesian Responder Index (HBRI)** responder index η = 1 + Δ·tanh(βᵀx), Δ = `R_DELTA_SCALE` = 0.72 (`responder_index.py`):

- **Feature-adapter registry** (`engine/tracking/feature_adapters/`): the feature vector `x` is assembled from adapters that self-register via `@register_adapter` and are auto-discovered with `pkgutil` at import. Shipped adapters: genetics, prs, bpc157, covariates, healthkit_behavior. The **genetics** feature is the anchored reference (`β_g = 1`, passed through un-shrunk), so with genetics alone every number is identical to the pre-HBRI scalar model. Non-genetic coefficients carry a ridge prior and currently default to 0.
- **Correlation-aware BLUE fusion** (`pooling.combine_priors`): the genetics-derived prior and the leave-one-out cohort prior (`pooling.py`) are fused as the minimum-variance unbiased estimate under an assumed error correlation ρ, correcting the genetics×cohort double-counting the old fused-precision cap ignored.
- **Patient enrichment** (`patient_enrichment` table, migration `011`): per-patient covariates/PRS/genetics captured via `POST /tracking/patients/from-job/{job_id}` and threaded into the adapters at prediction time (`service.get_patient_enrichment`).
- The prediction output includes a `responder_features` field (the per-feature β·value breakdown behind η).
- **Gated design stubs** — `dose_response.py` (saturating dose–response multiplier) and `cross_biomarker.py` (cross-biomarker residual covariance) are Phase-1 design-only stubs, inert and gated OFF behind a module constant (deliberately no env-var toggle, not wired into any live prediction path).

Per-biomarker effect magnitudes live in `biomarker_params.py`.

- **Research-backed evidence registry** (`engine/tracking/evidence.py` + `data/biomarker_evidence.json`): citation-anchored, grade-tagged (A–D) per-biomarker effect entries. The grade sets the prior's `relative_sd` (tighter for well-evidenced markers; flat `PANEL_REL_SD` fallback for uncited markers — most of the panel). Honesty contract: an entry requires ≥1 retrieved citation (real DOI). Curate via the CLI `python -m engine.tracking.evidence_update` (`set`/`show`/`validate`; refuses an uncited entry). Entries are keyed by the exact `BIOMARKER_PARAMS` / panel measurement name, which is also what binds at prediction time.
- **GLP-1 / incretin class** (Semaglutide / Tirzepatide / Liraglutide) are first-class, grade-A evidence-backed peptides. Their flagship endpoints use **class-qualified marker names** (`"Body weight (GLP-1 RA)"`, `"HbA1c (GLP-1 RA)"`, …) so their large, well-evidenced effects do not bleed onto the much smaller generic `"Body weight"` / `"HbA1c"` markers shared by weaker peptides (AOD-9604, MOTS-c).
- The generative model is documented in-app at `/tracking/model` (inline-SVG data flow + the formalization mirroring `bayes.py`).

**HealthKit ingestion** (`engine/healthkit/`): receives de-identified HealthKit samples from the peptodyssey iOS app. Router mounted at `/healthkit/*` (`engine/healthkit/api.py`): `POST /healthkit/samples` (idempotent batch upload, insert-only by sample uuid) and `GET /healthkit/samples` (read back a subject's samples). Auth is a per-device bearer token (`engine/healthkit/auth.py`), **fail-closed in prod**: when `DATABASE_URL` is set a valid token is always required; only the local SQLite dev/test fallback is open, and even that closes with `HEALTHKIT_REQUIRE_TOKEN=1`. A de-identified `subject_id` bridges to a tracking `patient_id` via the `healthkit_subject_map` table (migration `010`, `engine/tracking/healthkit_identity.py`), letting HealthKit-derived behavior feed the `healthkit_behavior` feature adapter. Storage is Postgres when `DATABASE_URL` is set (SQLite fallback otherwise).

**Users / auth** (`engine/users/`): authentication router mounted at `/users` (`engine/users/api.py`, e.g. `GET /users/me`). Backed by the `users` table (migration `004`).

### The API (`api.py`)

FastAPI wrapper around `run_pipeline()`. Async job queue pattern: `POST /analyze` returns a `job_id` immediately; client polls `GET /jobs/{job_id}`. Pipeline runs in a `ThreadPoolExecutor` (blocking IO). Jobs persist to **Postgres** when `DATABASE_URL` is set (loaded back into memory on startup); without it, jobs live only in the in-memory `_jobs` dict and are lost on restart (intentional for dev). The old `JOB_STORE_KEY` Fernet-encrypted on-disk snapshot is **deprecated and no longer used** — setting the var only logs a warning.

Besides `/analyze` and `/jobs/*`, `api.py` mounts routers for `/tracking/*`, `/healthkit/*`, `/users` (auth), `/regulatory/*`, and the ACMG sign-off endpoint. On startup it runs `_run_db_migrations()` (see [Database](#database-and-migrations) below).

### The Frontend (`frontend/`)

Next.js 15 app router (shipped, deployed at `flmanbiosci.net`). Key routes:
- `/` — genome file upload form
- `/jobs/[id]` — progress polling page
- `/jobs/[id]/results` — results display, tabbed `peptides | pgx | variants` (`pgx` default)
- `/tracking` and `/tracking/cohort` — longitudinal biomarker tracking UI
- `/regulatory` — FDA peptide regulatory dashboard (SSR)
- `/study` — study/enrollment surface

API calls go through `frontend/src/app/lib/api.ts` and `authFetch.ts`.

## Database and migrations

Storage is **Postgres when `DATABASE_URL` is set, SQLite fallback otherwise** (local dev / tests). This applies uniformly to every store: the annotation cache, the rsID cache, biomarker tracking, the job store, HealthKit samples, and users. All Postgres access goes through the shared psycopg2 pool in `db/pool.py` (`_ConnWrapper` adds a sqlite3-compatible `conn.execute()` so service code runs unchanged against either backend).

Schema is managed by migrations. On API startup `db/migrate.py::run_migrations` applies any pending `db/migrations/00N_*.sql` files in order; applied filenames are recorded in a `schema_migrations` table so re-running is idempotent (no-op when `DATABASE_URL` is absent). Current migrations `001`–`011` cover the initial schema, caches + tracking, the peptide/condition library, users, ownership FKs, the regulatory cache, cache TTL, HealthKit tables + device tokens + subject map, and `patient_enrichment`.

In the SQLite fallback path, the annotation cache lives at `data/annotation_cache.db` and the rsID cache at `data/rsid_cache.db`. `tests/conftest.py` has an autouse fixture that clears the annotation cache between tests; the rsID cache is not cleared between tests. To exercise the Postgres code paths locally, run the smoke tests: `PG_TESTS=1 nix develop --command python -m pytest tests/test_postgres_smoke.py -v`.

## Key Environment Variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres DSN. When set, all stores (annotation/rsID caches, tracking, jobs, HealthKit, users) use Postgres and `db/migrate.py` runs pending migrations at startup. Absent → SQLite fallback (local dev / tests) |
| `NCBI_API_KEY` | Raises ClinVar rate limit 3→10 req/s |
| `FILTERS` | Comma-separated rsID filter filenames (default: `acmg81_rsids.txt`) |
| `DATA_DIR` | Path to filter files directory (default: `data`) |
| `ENABLE_LIFTOVER` | Set to `1` to accept GRCh37 files via pyliftover (requires optional dep) |
| `PGX_CONFORMAL_CALIBRATION` | Path to validated PGx calibration set; without it, predictions are `uncalibrated` |
| `HEALTHKIT_REQUIRE_TOKEN` | Set to `1` to require a device bearer token for HealthKit ingestion even in the local SQLite dev path (already required whenever `DATABASE_URL` is set) |
| `U4U_OIDC_ISSUER` | End-user OIDC issuer URL for validating `Authorization: Bearer` access tokens (`engine/users/`) |
| `U4U_OIDC_AUDIENCE` | Expected `aud` claim for end-user OIDC access tokens |
| `U4U_OIDC_JWKS_URL` | JWKS endpoint used to verify end-user OIDC access token signatures |
| `U4U_CLUSTER_AUTHENTIK_ISSUER` | Issuer URL for the **cluster-admin** Authentik (the forward-auth proxy in front of the app, stamping trusted `X-Authentik-*` headers). Used to tag `issuer` on users upserted from those headers, so that population's `(issuer, sub)` keys stay distinct from end-user OIDC subs (`U4U_OIDC_ISSUER`). Falls back to a placeholder literal when unset (local dev/tests) — unrelated to end-user Bearer token validation |

`U4U_OIDC_ISSUER` / `U4U_OIDC_AUDIENCE` / `U4U_OIDC_JWKS_URL` gate the API's auth mode as a set: unless all three are set, the API runs in **dev-bypass** — every request resolves to a single fixed dev user, no real authentication. When all three are set, a missing or invalid `Authorization: Bearer` token on a protected endpoint gets a `401`; a JWKS endpoint that's unreachable at validation time gets a `503` (fail-closed) rather than silently falling back to anonymous.

> **Deprecated:** `JOB_STORE_KEY` (old Fernet on-disk job snapshot) is no longer used — jobs persist to Postgres when `DATABASE_URL` is set. Setting it only logs a warning.

## CI

Tests run on both Python 3.11 and 3.12 via `ubuntu-latest` GitHub Actions. Docker build/push workflows run on `self-hosted` runners. Test runs mock all external HTTP — no live API keys needed for the test suite to pass.

## Deployment (IAC)

The infrastructure lives in `../iac` (the [`hwcopeland/iac`](https://github.com/hwcopeland/iac) repo). u4u-engine deploys to a self-hosted RKE2 Kubernetes cluster. **Full ops runbook + deployment troubleshooting: [`docs/server-management.md`](docs/server-management.md).**

- **Namespace**: `theswamp` — manifests at `../iac/rke2/tooling/flux/theswamp/`
- **Public URL**: `https://flmanbiosci.net` — `/api/v1/*` → backend API (prefix rewritten to `/`), `/*` → frontend
- **Container registry**: `zot.hwcopeland.net/florida-man-bioscience/` (internal Zot)
- **GitOps**: Flux image automation watches the registry and auto-updates the SHA pins in `deployment.yaml` / `deployment-frontend.yaml`. The `# {"$imagepolicy": ...}` comments in those files are Flux markers — do not remove or reformat them.
- **Secrets**: External Secrets Operator pulling from Bitwarden (`bitwarden-cli` in `external-secrets` namespace)
- **Gateway**: Cilium Gateway API (`hwcopeland-gateway` in `kube-system`)

Deploying a change: push to `main` → CI builds and pushes new image to Zot → Flux detects the new digest, commits the updated SHA pin to `iac`, and rolls out the new pod automatically. No manual `kubectl` apply needed for normal releases.
