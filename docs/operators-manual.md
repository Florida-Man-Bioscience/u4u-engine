# u4u-engine — Operator's Manual

A practical guide for running, configuring, and operating the u4u-engine in
development and production. For engine internals see
[`architecture.md`](architecture.md) and [`pipeline.md`](pipeline.md); for the
production cluster runbook see [`server-management.md`](server-management.md).

> **Clinical scope.** The engine is an analysis and evidence-assembly aid, **not**
> a diagnostic device. ACMG/AMP classifications require qualified human sign-out,
> PGx predictions are `uncalibrated` unless a validated calibration set is supplied,
> and peptide/BPC-157 output is not medical advice. Operate accordingly.

---

## 1. What you are operating

| Component | Path | Role |
|-----------|------|------|
| **Engine library** | `engine/` | Pure Python. `run_pipeline(file_bytes, filename, ...) -> dict`. No web/DB dependency. |
| **API** | `api.py` (FastAPI) | Async job queue around the engine + regulatory, PGx, ACMG sign-off, and `/tracking` routes. |
| **Frontend** | `frontend/` (Next.js 15) | Upload, results, regulatory dashboard, biomarker tracking UI. |
| **Storage** | Postgres *or* SQLite | Annotation cache, rsID cache, tracking store, job store. |

The API is a thin wrapper: `POST /analyze` enqueues a job that runs the engine in
a `ThreadPoolExecutor`; clients poll `GET /jobs/{job_id}`.

---

## 2. Prerequisites

- **Dev (NixOS):** [Nix](https://nixos.org/). Everything else comes from `nix develop`.
- **Dev (non-Nix):** Python 3.11 or 3.12; `pip install -e ./engine`.
- **API/full stack:** Docker + Docker Compose (v20+).
- **Optional:** a Postgres instance (`DATABASE_URL`) for persistence; `NCBI_API_KEY`
  for higher ClinVar rate limits; a BAM file for AR CAG repeat calling.

---

## 3. Installation & first run

### Option A — Nix dev shell (recommended for dev/tests)

```bash
nix develop                                   # Python 3.12 + pytest + Node 20
nix develop --command python -m pytest tests/ -v
```

### Option B — pip (library only)

```bash
pip install -e ./engine            # core: requests>=2.31, tenacity>=8.2
pip install -e "./engine[vcf]"     # + pysam for VCF (needs a C compiler)
git config core.hooksPath scripts  # auto-bumps version on each commit
```

### Option C — Docker (API + frontend)

```bash
cp .env.example .env               # set NCBI_API_KEY / DATABASE_URL etc. (all optional)
docker compose up --build          # API on :8000
curl http://localhost:8000/health  # {"status":"ok","jobs_running":0,"jobs_pending":0}
```

Frontend (separate container, point it at the API):

```bash
docker build -t u4u-frontend ./frontend
docker run -d --name u4u-frontend -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE=http://localhost:8000 u4u-frontend
# → http://localhost:3000
```

### Smoke test the pipeline directly

```bash
nix develop --command python -c "
from engine import run_pipeline
res = run_pipeline(open('sample.vcf','rb').read(), 'sample.vcf', filters=['acmg81_rsids.txt'])
print(res['analysis_status'], len(res['variants']), 'variants')
"
```

---

## 4. Configuration reference (environment variables)

| Variable | Default | Effect |
|----------|---------|--------|
| `DATABASE_URL` | _(none)_ | Postgres DSN. Set → all caches/stores use Postgres; unset → local SQLite. |
| `NCBI_API_KEY` | _(none)_ | Raises ClinVar rate limit 3→10 req/s. |
| `JOB_STORE_KEY` | _(none)_ | Fernet key to encrypt the on-disk job store. **Without it, results live in memory only** and are lost on restart (never written as plaintext). |
| `PGX_CONFORMAL_CALIBRATION` | `data/pgx/conformal_calibration.json` | Validated PGx calibration set. Missing → drug predictions returned as `uncalibrated`. |
| `FILTERS` | `acmg81_rsids.txt` | Comma-separated rsID whitelist files (empty = keep all variants). |
| `DATA_DIR` | `data` | Directory holding filter files. |
| `WORKERS` | `4` | Thread-pool size for concurrent pipeline runs. |
| `MAX_UPLOAD_MB` | `100` | Max upload size. |
| `JOB_TTL_HOURS` | `24` | How long completed jobs stay in memory. |
| `ENABLE_LIFTOVER` | `0` | `1` = lift GRCh37 files to GRCh38 (needs optional `pyliftover`) instead of rejecting them. |
| `LIFTOVER_CHAIN_37_TO_38` | _(none)_ | Local hg19→hg38 chain file (else fetched from UCSC). |
| `ALLOWED_ORIGINS` | _(app default)_ | CORS origins for the API. |
| `OPENFDA_API_KEY`, `REGULATIONS_GOV_API_KEY` | _(none)_ | Raise rate limits for the regulatory module's live sources. |
| `NEXT_PUBLIC_API_BASE` | `https://flmanbiosci.net/api/v1` | Frontend → backend base URL. |

---

## 5. Operating the API

**Job lifecycle:** `POST /analyze` → `202 {job_id, poll_url}` → poll `GET /jobs/{job_id}`
until status is `completed`/`failed`.

| Method & path | Purpose |
|---------------|---------|
| `GET /health` | Liveness + `jobs_running` / `jobs_pending` counts. |
| `POST /analyze` | Upload a genome file (multipart `file`). Optional `current_medications` form field (**PHI — form field only, never a query param**). Returns a `job_id`. |
| `GET /jobs` | List jobs. |
| `GET /jobs/{job_id}` | Poll status / fetch full result dict. |
| `GET /jobs/{job_id}/pgx` | PGx profile for a job. |
| `GET /jobs/{job_id}/drug/{drug}` | Drug-specific PGx recommendation. |
| `GET /jobs/{job_id}/dossier/{peptide_name}` | HTML peptide dossier. |
| `POST /jobs/{job_id}/variants/{variant_id}/acmg-signoff` | **Required** human sign-out on an ACMG classification. |
| `GET /regulatory/peptides`, `GET /regulatory/events` | Peptide FDA status + regulatory events (live sources degrade gracefully). |
| `/tracking/...` | Longitudinal biomarker tracking (patients, treatments, measurements, cohort, predictions, priors). See [`api.md`](api.md). |

**Auth model.** Soft auth: in production the Authentik proxy stamps identity headers
and the job records its creating operator. In dev (no proxy) ownership is recorded
as NULL rather than returning 401 — so a bare local API is unauthenticated by design.
**Do not expose a dev API to the internet without the proxy in front.**

**Upload example:**

```bash
curl -X POST http://localhost:8000/analyze -F "file=@genome.vcf"
# → {"job_id":"...","status":"pending","poll_url":"/jobs/..."}
curl http://localhost:8000/jobs/<job_id>
```

---

## 6. Data, storage & caches

Two SQLite caches in `data/` when `DATABASE_URL` is unset (all move to Postgres when set):

1. `data/annotation_cache.db` — all annotators, keyed `(source, lookup_key)`; caches
   both hits and "no-data-found". Shared across runs — **persistent, safe to reuse.**
2. `data/rsid_cache.db` — rsID → coordinate resolution.

- **Postgres:** connection pool in `db/pool.py` (max 25 conns); migrations in
  `db/migrations/00N_*.sql` run automatically at startup (`db/migrate.py`).
- **Job store:** in-memory by default; set `JOB_STORE_KEY` to persist encrypted to disk.
- **Clearing caches:** delete the `.db` files (SQLite) or truncate the cache tables
  (Postgres) if annotations are stale after an upstream data-source change. Expect a
  slower first run afterward while caches re-warm.

---

## 7. Input files & filters

Accepted: `.vcf` / `.vcf.gz` (needs `pysam`), `.txt` (23andMe or rsID list), `.csv`
(`chrom,pos,ref,alt,rsid` subset). Files are read into memory and **discarded — never
written to disk.** Build gate rejects confirmed non-GRCh38 coordinates unless
`ENABLE_LIFTOVER=1`.

rsID whitelist files live in `DATA_DIR` (`data/`): `acmg81_rsids.txt`,
`pharma_rsids.txt`, `carrier_rsids.txt`, `health_traits_rsids.txt`,
`all_clinvar_rsids.txt.gz`. Select at call time via `filters=[...]` or the `FILTERS`
env var.

---

## 8. Health checks & monitoring

- **Liveness:** `GET /health` — non-`ok`, or a wedged non-decreasing `jobs_pending`,
  means the worker pool is stuck; restart the API pod.
- **Grafana "Swamp" dashboard:** `https://grafana.hwcopeland.net` (FMB group grants
  Editor + Swamp-folder Admin). Runbook and onboarding steps are in
  [`server-management.md`](server-management.md).
- **PGx calibration status:** if drug predictions come back `uncalibrated`, the
  `PGX_CONFORMAL_CALIBRATION` file is missing or unreadable — that is a config issue,
  not an engine failure.

---

## 9. Production deployment & release flow

Production runs on the hwcopeland RKE2/Kubernetes cluster, GitOps via Flux, served at
`https://flmanbiosci.net` (`/api/v1/*` → API, `/*` → frontend). Namespace `theswamp`.

**Normal release — fully automated:**

```
push to main → CI builds image on the self-hosted runner → pushes to
zot.hwcopeland.net → Flux detects the new digest, commits the SHA pin to the
iac repo, and rolls the pod. No manual kubectl apply.
```

You generally touch nothing. The `# {"$imagepolicy": ...}` comments in the theswamp
`deployment*.yaml` files are Flux markers — **do not remove or reformat them.**

---

## 10. Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Push merged but site version frozen | Self-hosted CI runner (`arc-chem-runner` in `arc-system`) offline → `build and push` jobs stuck `queued`; `tests` (GitHub-hosted) still pass. | Confirm: `gh run list` shows queued builds and `gh api .../actions/runners` is empty. Fix needs cluster-admin: `kubectl -n arc-system rollout restart deployment/arc-chem-runner`. Read-only operators must escalate to the cluster admin (Hampton / `hwcopeland`). |
| File rejected at validation | Non-GRCh38 coordinates, >`MAX_UPLOAD_MB`, or bad header. | Confirm build is GRCh38, or set `ENABLE_LIFTOVER=1` (needs `pyliftover`). |
| Drug predictions `uncalibrated` | `PGX_CONFORMAL_CALIBRATION` missing. | Point it at a validated calibration set. |
| Results lost after API restart | No `JOB_STORE_KEY`, so jobs are memory-only. | Set `JOB_STORE_KEY` (Fernet) to persist encrypted, or use `DATABASE_URL`. |
| VCF upload errors on import | `pysam` not installed. | `pip install -e "./engine[vcf]"` (Linux/Mac; needs a C compiler). |
| Regulatory dashboard sparse | Live sources (ClinicalTrials.gov / openFDA / Federal Register) rate-limited or down. | Expected — it degrades gracefully to curated data; add `OPENFDA_API_KEY` / `REGULATIONS_GOV_API_KEY` to raise limits. |
| Slow first run after cache wipe | Caches cold. | Expected; they re-warm. Avoid deleting `annotation_cache.db` unless upstream data changed. |
| `jobs_pending` climbing, none complete | Worker pool wedged or under-sized. | Raise `WORKERS`; if still stuck, restart the API. |

---

## 11. Security & PHI notes

- Genome uploads and medication lists are **PHI**: uploads are processed in memory and
  never persisted; medications are accepted only as a multipart form field (kept out of
  URLs, access logs, and browser history).
- Never expose an unauthenticated dev API publicly — production auth depends on the
  Authentik proxy sitting in front of the API.
- The on-disk job store is only ever written encrypted (`JOB_STORE_KEY`); there is no
  plaintext-on-disk mode.
- Reference data is local-only by policy; do not commit patient data or reference panels.

---

*Cross-references: [`architecture.md`](architecture.md) · [`pipeline.md`](pipeline.md) ·
[`api.md`](api.md) · [`deploy.md`](deploy.md) · [`server-management.md`](server-management.md) ·
[`interpretation.md`](interpretation.md).*
