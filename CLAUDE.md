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

The engine is a pure Python library — no web framework, no database. Entry point:

```python
from engine import run_pipeline
result = run_pipeline(file_bytes, filename, filters=[...])
```

`engine/pipeline.py` orchestrates 10 steps: validate → parse → quality filter → whitelist filter → rsID resolution → deduplicate → annotate (parallel, 8 threads) → score → summarize → sort. Returns a rich `dict` with keys: `variants`, `pathway_summary`, `receptor_genetics`, `prs_profile`, `ar_cag_repeat`, `peptide_recommendations`, `pgx_profile`, `dossiers`, `acmg_summary`, `analysis_status`.

**Annotators** (`engine/annotators/`): VEP, ClinVar, gnomAD, MyVariant.info (fallback), UniProt, PharmGKB, GWAS Catalog. All share a SQLite cache at `data/annotation_cache.db` via `engine/annotators/cache.py`. Cache is keyed `(source, lookup_key)` and caches both results and `None` (no-data-found).

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

**Biomarker tracking** (`engine/tracking/`): SQLite-backed longitudinal biomarker tracking with Bayesian posterior updates. REST API mounted at `/tracking/...` via `engine/tracking/api.py`. `analysis.predict_response` combines a genetics-derived prior (`genetics.derive_prior`), leave-one-out cohort pooling (`pooling.py`), and the measurement likelihood into a posterior with 95% credible intervals plus a predictive curve (`bayes.py`, Normal–Normal conjugate). Per-biomarker effect magnitudes live in `biomarker_params.py`.

- **Research-backed evidence registry** (`engine/tracking/evidence.py` + `data/biomarker_evidence.json`): citation-anchored, grade-tagged (A–D) per-biomarker effect entries. The grade sets the prior's `relative_sd` (tighter for well-evidenced markers; flat `PANEL_REL_SD` fallback for uncited markers — most of the panel). Honesty contract: an entry requires ≥1 retrieved citation (real DOI). Curate via the CLI `python -m engine.tracking.evidence_update` (`set`/`show`/`validate`; refuses an uncited entry). Entries are keyed by the exact `BIOMARKER_PARAMS` / panel measurement name, which is also what binds at prediction time.
- **GLP-1 / incretin class** (Semaglutide / Tirzepatide / Liraglutide) are first-class, grade-A evidence-backed peptides. Their flagship endpoints use **class-qualified marker names** (`"Body weight (GLP-1 RA)"`, `"HbA1c (GLP-1 RA)"`, …) so their large, well-evidenced effects do not bleed onto the much smaller generic `"Body weight"` / `"HbA1c"` markers shared by weaker peptides (AOD-9604, MOTS-c).
- The generative model is documented in-app at `/tracking/model` (inline-SVG data flow + the formalization mirroring `bayes.py`).

### The API (`api.py`)

FastAPI wrapper around `run_pipeline()`. Async job queue pattern: `POST /analyze` returns a `job_id` immediately; client polls `GET /jobs/{job_id}`. Pipeline runs in a `ThreadPoolExecutor` (blocking IO). Job results are kept in-memory and optionally persisted to disk encrypted with a Fernet key (`JOB_STORE_KEY`). Without a key, disk persistence is disabled — results are lost on restart.

### The Frontend (`frontend/`)

Next.js 15 app router. Key routes:
- `/` — genome file upload form
- `/jobs/[id]` — progress polling page
- `/jobs/[id]/results` — variant results display
- `/regulatory` — FDA peptide regulatory dashboard (SSR)
- `/tracking` — longitudinal biomarker tracking UI

API calls go through `frontend/src/app/lib/api.ts` and `authFetch.ts`.

## Caching Architecture

Two independent SQLite caches:
1. `data/annotation_cache.db` — all 7 annotators (shared, `engine/annotators/cache.py`)
2. `data/rsid_cache.db` — rsID → coordinate resolution (`engine/rsid_resolver.py`)

`tests/conftest.py` has an autouse fixture that clears the annotation cache between tests. The rsID cache is not cleared between tests.

## Key Environment Variables

| Variable | Purpose |
|---|---|
| `NCBI_API_KEY` | Raises ClinVar rate limit 3→10 req/s |
| `JOB_STORE_KEY` | Fernet key for encrypted job persistence. Without it, results stay in memory only |
| `FILTERS` | Comma-separated rsID filter filenames (default: `acmg81_rsids.txt`) |
| `DATA_DIR` | Path to filter files directory (default: `data`) |
| `ENABLE_LIFTOVER` | Set to `1` to accept GRCh37 files via pyliftover (requires optional dep) |
| `PGX_CONFORMAL_CALIBRATION` | Path to validated PGx calibration set; without it, predictions are `uncalibrated` |

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
