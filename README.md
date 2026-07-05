# u4u-engine

[![tests](https://github.com/Florida-Man-Bioscience/u4u-engine/actions/workflows/test.yml/badge.svg)](https://github.com/Florida-Man-Bioscience/u4u-engine/actions/workflows/test.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Genomics-to-peptide-therapy analysis engine for the U4U platform.

Takes a raw genome file, runs it through a 10-step annotation pipeline, and returns a
rich result covering scored/prioritized variants, KEGG pathway hits, receptor genetics,
polygenic risk scores, pharmacogenomics (PGx), ACMG/AMP evidence assembly, and peptide
therapy recommendations — each with plain-English summaries. The engine is a pure Python
library with no web-framework dependency: import it wherever and call `run_pipeline()`.
A FastAPI wrapper (`api.py`) and Next.js frontend (`frontend/`) ship alongside it.

---

## Documentation

Engine, clinical, and infrastructure docs live in [`docs/`](docs/):

| Document | What it covers |
|----------|----------------|
| [`docs/architecture.md`](docs/architecture.md) | System architecture — engine, API, frontend, data flow |
| [`docs/pipeline.md`](docs/pipeline.md) | The 10 pipeline steps in detail |
| [`docs/interpretation.md`](docs/interpretation.md) | Finding tiers, VUS policy, condition library schema |
| [`docs/integrations.md`](docs/integrations.md) | External APIs, rate limits, what user data leaves the system |
| [`docs/api.md`](docs/api.md) | U4U Engine + `/tracking` REST API reference |
| [`docs/deploy.md`](docs/deploy.md) | Deploying the engine standalone (single-host) |
| [`docs/server-management.md`](docs/server-management.md) | Production ops runbook (hwcopeland RKE2/Flux cluster) |
| [`docs/clinical-validation-plan.md`](docs/clinical-validation-plan.md) | Clinical validation master plan |
| [`docs/roadmap.md`](docs/roadmap.md) · [`docs/project-status.md`](docs/project-status.md) | Where the project is headed and where it stands |

---

## Install

```bash
# From the repo root
pip install -e ./engine

# With VCF support (Linux/Mac only — pysam requires a C compiler)
pip install -e "./engine[vcf]"

# Enable git hooks (auto-increments version on each commit)
git config core.hooksPath scripts
```

**Required dependencies:** `requests>=2.31`, `tenacity>=8.2`

---

## NixOS / Nix Development

A `flake.nix` is provided for reproducible development on NixOS or any system with [Nix](https://nixos.org/) installed.

### Enter the dev shell

```bash
# From the repo root
nix develop
```

This gives you Python 3.12 with `pytest`, `responses`, `requests`, `tenacity`, and Node.js 20 — everything needed to run the engine tests and build the frontend.

### Run tests inside the Nix shell

```bash
# Already inside `nix develop`:
python -m pytest tests/ -v

# Or as a one-liner without entering the shell:
nix develop --command bash -c "python -m pytest tests/ -v"
```

### Run the engine

```bash
nix develop --command python -c "
from engine import run_pipeline
# ... your pipeline code
"
```

> **Note:** The Nix shell provides test and engine dependencies only. For production
> deployment (FastAPI/uvicorn, Celery, database drivers), use Docker or `pip install`
> as described above.

---

## Quick Start

`run_pipeline()` returns a **dict**, not a list. The scored variants live under the
`"variants"` key; the other keys carry the enrichment layers (pathways, PGx, ACMG, etc.).

```python
from engine import run_pipeline

with open("my_file.vcf", "rb") as f:
    result = run_pipeline(f.read(), "my_file.vcf")

for v in result["variants"]:
    print(v["tier"], v["genes"], v["headline"])

print(result["pathway_summary"]["summary_text"])
print(result["pgx_profile"]["summary_text"])
```

### Top-level result keys

| Key | Contents |
|-----|----------|
| `variants` | Scored, sorted list of annotated variants (fields below) |
| `analysis_status` | Counts + per-variant annotation failures; `complete` flag |
| `genome_build` | Detected/assumed build (GRCh38; or liftover metadata) |
| `pathway_summary` | KEGG pathway hits + plain-English summary |
| `receptor_genetics` | Receptor expression + isoform predictions |
| `prs_profile` | Polygenic risk scores |
| `ar_cag_repeat` | AR CAG repeat call (only when a BAM is supplied; else `None`) |
| `peptide_recommendations` | Peptide therapy candidate coverage (incl. BPC-157 detail) |
| `pgx_profile` | Star-allele/HLA calls, CPIC phenoconversion, drug recommendations |
| `acmg_summary` | ACMG/AMP evidence-assembly rollup (requires human sign-out) |

---

## Beyond variant annotation

The engine is more than a variant annotator. After per-variant annotation, several
enrichment subsystems run (see [`docs/architecture.md`](docs/architecture.md)):

- **V3 enrichment** — KEGG pathway mapping, receptor expression + isoform prediction,
  polygenic risk scores, BPC-157 response prediction, and peptide-therapy candidate
  coverage (`engine/annotators/`).
- **PGx pipeline** (`engine/pgx/`) — star-allele calls (array/BAM/long-read) → HLA
  tag-SNP calls → CPIC phenoconversion → drug recommendations + conformal prediction
  sets. Predictions are `uncalibrated` unless `PGX_CONFORMAL_CALIBRATION` points at a
  validated calibration set.
- **ACMG/AMP classification** (`engine/acmg/`) — an evidence-assembly *aid*, not a final
  clinical determination. Requires qualified human sign-out.
- **Regulatory module** (`engine/regulatory/`) — curated peptide FDA status merged with
  live sources (ClinicalTrials.gov, openFDA, Federal Register); live-source failures
  degrade gracefully.
- **Biomarker tracking** (`engine/tracking/`) — SQLite/Postgres-backed longitudinal
  tracking built on the **Hierarchical Bayesian Responder Index (HBRI)**: a responder
  index `η = 1 + Δ·tanh(βᵀx)` shapes the prior from an auto-discovering
  feature-adapter registry (`engine/tracking/feature_adapters/`: genetics, PRS,
  BPC-157, covariates, HealthKit behavior). Priors, leave-one-out cohort pooling, and
  the measurement likelihood are combined with a correlation-aware **BLUE fusion**
  (`pooling.combine_priors`); the prediction output carries a `responder_features`
  breakdown. Effect sizes are citation-anchored and grade-tagged in a research-backed
  evidence registry. Authoritative spec:
  [`docs/models/peptide-response-model.md`](docs/models/peptide-response-model.md).
- **HealthKit ingestion** (`engine/healthkit/`) — de-identified Apple HealthKit sync
  from the iOS app via `POST`/`GET /healthkit/samples`, guarded by device-token auth
  (fail-closed when `DATABASE_URL` is set). Samples bridge to tracking patients through
  an opaque subject map. See [`docs/healthkit-storage.md`](docs/healthkit-storage.md).

**Storage.** All caches and stores — annotation cache, rsID cache, tracking, jobs, and
HealthKit — use **Postgres** when `DATABASE_URL` is set, and fall back to local
**SQLite** otherwise (so local dev and the test suite work unchanged). Schema is applied
by `db/migrate.py`.

**Auth.** A `/users` surface (`engine/users/api.py`) resolves the Authentik-forwarded
subject (`GET /users/me` lazily upserts the caller; `GET /users` lists known users for
operator views).

**Deployment.** Production runs on the hwcopeland RKE2/Kubernetes cluster with Flux
GitOps, served at `https://flmanbiosci.net`. See
[`docs/server-management.md`](docs/server-management.md).

---

## Pipeline Steps

| Step | What happens |
|------|-------------|
| 1. Validate | File size ≤ 100 MB, VCF header check, UTF-8, genome-build gate (rejects confirmed non-GRCh38 coordinate files) |
| 2. Parse | VCF / 23andMe / rsID list / CSV → variant dicts |
| 3. Quality filter | Drop hom-ref, failed calls (--/NN/DI), low GQ/DP, indels |
| 4. Whitelist filter | Keep only ACMG81 / pharma / carrier variants (optional) |
| 5. rsID resolution | Ensembl REST: rsid_only variants → coordinates |
| 6. Deduplicate | By (chrom, pos, ref, alt) — eliminates double-annotation |
| 7. Annotate | VEP (consequence + gene) + ClinVar + gnomAD + MyVariant fallback |
| 8. Score | ClinVar > consequence > frequency. Carrier detection for recessive genes |
| 9. Summarize | Plain-English headline, rarity, action hint, zygosity |
| 10. Sort | By score descending |

---

## Result Dict Fields

Each variant in the returned list contains:

```
variant_id         str        rsid or "chrom:pos"
rsid               str|None   dbSNP rsID
location           str        "chrom:pos"
chrom              str        chromosome (no chr prefix)
pos                int        1-based position
ref, alt           str        alleles
zygosity           str        "heterozygous" | "homozygous_alt" | "unknown"

consequence        str        VEP SO term (e.g. "missense_variant")
genes              list[str]  affected gene symbols
clinvar            str|None   ClinVar classification (lowercased)
clinvar_raw        str|None   same — never overwritten by heuristics
disease_name       str|None   associated condition (human-readable, from ClinVar)
condition_key      str|None   stable lookup key for the condition library:
                              "OMIM:<id>" | "MedGen:<id>" | "ClinVar:<uid>" | null
gnomad_af          float|None allele frequency
gnomad_popmax      float|None highest AF across ancestry groups
gnomad_homozygote_count int|None

score              int        priority score
tier               str        "critical" | "high" | "medium" | "low"
tier_basis         str        "clinvar" (tier backed by a ClinVar classification)
                              | "heuristic_priority" (internal prioritization only,
                              NOT a clinical determination)
acmg               dict       ACMG/AMP 2015 evidence assembly (subset):
                              {classification, applied_codes, candidate_codes,
                               clinvar_comparison, requires_human_review,
                               method, disclaimer}. NOT a final clinical
                              classification — requires qualified human sign-out.
reasons            list[str]  scoring factors
frequency_derived_label str|None  additive frequency context (never overwrites clinvar)
carrier_note       str|None   set for heterozygous variants in recessive genes

emoji              str        🔴🟠🟡🟢🔵
headline           str        one-sentence plain-English summary
consequence_plain  str        molecular impact in plain English
rarity_plain       str        population frequency in plain English
clinvar_plain      str        ClinVar classification in plain English
action_hint        str        recommended next step
zygosity_plain     str|None   plain-English zygosity statement
```

### condition_key format

`condition_key` is the stable identifier used to look up the associated condition in the condition library (Sasank's spreadsheet). Priority order:

1. `"OMIM:<MIM number>"` — preferred; sourced from ClinVar trait cross-references
2. `"MedGen:<concept id>"` — NCBI MedGen CUI; fallback when no OMIM xref exists
3. `"ClinVar:<variation uid>"` — ClinVar Variation ID; last resort when no disease xref exists
4. `null` — no ClinVar record found for this variant

The backend uses `condition_key` to retrieve `condition_display_name`, `plain_description`, and `action_guidance` from the condition library. See [`docs/interpretation.md`](docs/interpretation.md) for the full condition library schema.

---

## Accepted File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| VCF | `.vcf`, `.vcf.gz` | Requires `pysam`. GQ/DP/GT extracted from FORMAT fields |
| 23andMe | `.txt` | rsID + genotype format. ref/alt resolved via Ensembl |
| rsID list | `.txt` | One rsID per line |
| CSV | `.csv` | Columns: chrom, pos, ref, alt, rsid (any subset) |

---

## rsID Whitelist Filters

Place filter files in the `data/` directory:

| Filename | Gene set |
|----------|----------|
| `acmg81_rsids.txt` | ACMG SF v3.2 actionable genes |
| `pharma_rsids.txt` | Pharmacogenomics (CYP2C19, CYP2D6, VKORC1, …) |
| `carrier_rsids.txt` | Carrier screening genes |
| `health_traits_rsids.txt` | Health trait associations |
| `all_clinvar_rsids.txt.gz` | All ClinVar rsIDs |

Apply with:
```python
results = run_pipeline(
    file_bytes, "my_23andme.txt",
    filters=["acmg81_rsids.txt", "pharma_rsids.txt"],
    data_dir="data",
)
```

---

## Wrapping for a FastAPI Worker

```python
from fastapi import FastAPI, UploadFile
from engine import run_pipeline

app = FastAPI()

@app.post("/analyze")
async def analyze(file: UploadFile, filters: list[str] = ["acmg81_rsids.txt"]):
    file_bytes = await file.read()
    results = run_pipeline(
        file_bytes,
        file.filename,
        filters=filters,
        progress_callback=lambda step, pct: print(f"[{pct}%] {step}"),
    )
    return {"count": len(results), "results": results}
```

---

## Wrapping for a Celery Worker

```python
from celery import Celery
from engine import run_pipeline

app = Celery("u4u")

@app.task(bind=True)
def run_analysis(self, file_bytes: bytes, filename: str, filters: list):
    def progress(step, pct):
        self.update_state(state="PROGRESS", meta={"step": step, "pct": pct})

    return run_pipeline(file_bytes, filename, filters=filters, progress_callback=progress)
```

---

## Scoring Model

| Signal | Points |
|--------|--------|
| ClinVar pathogenic | +1000 (short-circuit → CRITICAL) |
| ClinVar likely pathogenic | +500 |
| ClinVar benign | score=1 (short-circuit → LOW) |
| ClinVar VUS | +50 |
| Loss-of-function consequence | +100 |
| Missense / in-frame | +50 |
| Synonymous / intronic | +5 |
| Absent in gnomAD | +30 |
| Ultra-rare (AF < 0.0001) | +20 |
| Very rare (AF < 0.001) | +10 |
| Rare (AF < 0.01) | +5 |
| Common (AF ≥ 0.05) | −20 |
| Carrier in recessive gene | ×0.5 |
| Intergenic | −10 |

**Tiers:** CRITICAL ≥ 500 · HIGH ≥ 100 · MEDIUM ≥ 30 · LOW < 30

---

## Environment Variables

| Variable | Default | Effect |
|----------|---------|--------|
| `NCBI_API_KEY` | _(none)_ | Raises ClinVar rate limit from 3 to 10 req/s |

---

## Tests

```bash
pytest tests/

# without pytest:
PYTHONPATH=. python3 -m unittest discover tests/
```

---

## Running with Docker

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20+ recommended)
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)

### Backend API (port 8000)

The backend API serves the engine pipeline via FastAPI/uvicorn.

```bash
# 1. Create an .env file with your API keys (optional but recommended)
cp .env.example .env   # edit .env and set NCBI_API_KEY if you have one

# 2. Build and start the backend
docker compose up --build

# 3. Verify it's running
curl http://localhost:8000/health
# → {"status":"ok","jobs_running":0,"jobs_pending":0}

# 4. Run an analysis
curl -X POST http://localhost:8000/analyze -F "file=@your_file.vcf"
# → {"job_id":"...","status":"pending","poll_url":"/jobs/..."}
```

### Frontend UI (port 3000)

The frontend is a Next.js app that provides a browser-based interface for uploading genome files and viewing results.

```bash
# 1. Build the frontend Docker image
docker build -t u4u-frontend ./frontend

# 2. Run the frontend container
#    Point NEXT_PUBLIC_API_BASE at the backend API
docker run -d \
  --name u4u-frontend \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE=http://localhost:8000 \
  u4u-frontend

# 3. Open in your browser
#    → http://localhost:3000
```

> **Note:** If you're running both containers, the frontend needs network access
> to the backend. On Linux, use `--network host` or a shared Docker network.
> On macOS/Windows with Docker Desktop, `http://localhost:8000` works out of
> the box from the frontend container.

### Full-stack with Docker Compose

To run both backend and frontend together, you can extend `docker-compose.yml`:

```yaml
# In docker-compose.yml, add under services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE=http://api:8000
    depends_on:
      - api
    restart: unless-stopped
```

Then run:

```bash
docker compose up --build
```

Open **http://localhost:3000** in your browser to access the genome analysis UI.

### Environment Variables

| Variable | Default | Effect |
|----------|---------|--------|
| `NCBI_API_KEY` | _(none)_ | Raises ClinVar rate limit from 3 to 10 req/s |
| `DATABASE_URL` | _(none)_ | Postgres connection string. When set, all caches/stores use Postgres; without it they fall back to local SQLite |
| `DATA_DIR` | `data` | Path to rsID filter files inside the container |
| `FILTERS` | `acmg81_rsids.txt` | Comma-separated filter filenames (empty = all variants) |
| `WORKERS` | `4` | Thread pool size for concurrent pipeline runs |
| `MAX_UPLOAD_MB` | `100` | Maximum upload file size in megabytes |
| `JOB_TTL_HOURS` | `24` | Hours to keep completed jobs (in Postgres, or in memory when `DATABASE_URL` is unset) |
| `JOB_STORE_KEY` | _(none)_ | **Deprecated / unused.** The old Fernet-encrypted on-disk job store is gone — jobs now persist to Postgres when `DATABASE_URL` is set, and are in-memory only otherwise. Setting it logs a deprecation warning and has no effect. |
| `PGX_CONFORMAL_CALIBRATION` | `data/pgx/conformal_calibration.json` | Path to a validated PGx conformal calibration set. Without it, drug-response predictions are returned as `uncalibrated`. |
| `ENABLE_LIFTOVER` | `0` | When `1`, lift GRCh37 coordinate files to GRCh38 instead of rejecting them (requires the optional `pyliftover` package). |
| `LIFTOVER_CHAIN_37_TO_38` | _(none)_ | Optional local hg19→hg38 chain file for liftover (else fetched from UCSC). |
| `NEXT_PUBLIC_API_BASE` | `https://flmanbiosci.net/api/v1` | Backend API URL for the frontend |

### Stopping

```bash
# Stop all containers
docker compose down

# Stop and remove volumes
docker compose down -v
```

---

## BPC-157 response prediction

The engine includes a BPC-157 response predictor (`engine/annotators/bpc157_predictor.py`),
surfaced under `result["peptide_recommendations"]`. The original brainstorm notes that
seeded it — off-label use cases, candidate biomarkers, and predictor ideas — have moved to
[`docs/bpc157-grok-plan.md`](docs/bpc157-grok-plan.md) to keep this README focused.

> **Not medical advice.** BPC-157 is not FDA-approved for any medical use; human data are
> extremely limited. Any use is experimental/off-label — see the full disclaimer in the
> linked notes.
