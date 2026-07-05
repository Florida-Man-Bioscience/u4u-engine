# U4U Engine API Reference

Base URL: `http://<host>:8000`

All responses are JSON. All timestamps are ISO-8601[^iso8601].

---

## Endpoints

### GET /health

Liveness check and queue depth.

**Response 200**
```json
{
  "status": "ok",
  "jobs_running": 0,
  "jobs_pending": 0
}
```

---

### POST /analyze

Upload a genome file and start an asynchronous[^async] analysis job.

**Request**
- Content-Type: `multipart/form-data`[^multipart]
- Field: `file` (required) — `.vcf`, `.vcf.gz`, `.txt` (23andMe), `.csv`, or rsID list
- Max size: `MAX_UPLOAD_MB` (default 100 MB)

**Response 202**[^http202]
```json
{
  "job_id": "uuid-string",
  "status": "pending",
  "poll_url": "/jobs/{job_id}"
}
```

**Error responses**
| Code | Reason |
|------|--------|
| 413[^http413] | File exceeds MAX_UPLOAD_MB |
| 422[^http422] | Empty file or unsupported format |

---

### GET /jobs/{job_id}

Poll job status and retrieve results when complete.

**Path parameters**
- `job_id` (string) — UUID[^uuid] from POST /analyze

**Query parameters**
- `include_results` (boolean, default `true`) — Set to `false` to get status/progress without the full results array

**Response 200**
```json
{
  "job_id": "uuid-string",
  "status": "pending|running|done|failed",
  "progress": {
    "step": "Annotating rs80357906 (4/81)",
    "pct": 42
  },
  "count": null,
  "results": [...] ,
  "error": null,
  "filename": "genome.vcf",
  "file_size": 1048576,
  "created_at": "2026-03-14T12:00:00Z",
  "started_at": "2026-03-14T12:00:01Z",
  "finished_at": null
}
```

**Result object** (each item in `results`)
```json
{
  "variant_id": "string",
  "rsid": "rs80357906",
  "location": "17:41245466",
  "chrom": "17",
  "pos": 41245466,
  "ref": "A",
  "alt": "G",
  "zygosity": "heterozygous|homozygous_alt|unknown",
  "consequence": "missense_variant",
  "genes": ["BRCA1"],
  "clinvar": "Pathogenic",
  "clinvar_raw": "string",
  "disease_name": "Breast-ovarian cancer, familial 1",
  "condition_key": "OMIM:604370",
  "gnomad_af": 0.000012,
  "gnomad_popmax": 0.000034,
  "gnomad_homozygote_count": 0,
  "score": 95,
  "tier": "critical|high|medium|low",
  "reasons": ["Pathogenic in ClinVar", "Ultra-rare variant"],
  "frequency_derived_label": "Ultra-rare",
  "carrier_note": "string|null",
  "emoji": "🔴",
  "headline": "string",
  "consequence_plain": "string",
  "rarity_plain": "string",
  "clinvar_plain": "string",
  "action_hint": "string",
  "zygosity_plain": "string|null"
}
```

Result-field meanings — `zygosity`[^zygosity], `consequence`[^consequence], `clinvar`[^clinvar], `condition_key`[^conditionkey], `gnomad_af`/`gnomad_popmax`[^gnomad], `tier`[^tier] — are defined in the footnotes below; see also `docs/pipeline.md` and `docs/architecture.md` for full field tables.

**Notes**
- `results` is `null` while status is `pending` or `running`, or if `include_results=false`
- Results are pre-sorted by score descending
- Jobs expire after `JOB_TTL_HOURS`[^ttl] (default 24 h) and return 404[^http404]
- Poll every 2–5 s while status is `pending` or `running`

**Error responses**
| Code | Reason |
|------|--------|
| 404 | Job not found or expired |

---

### GET /jobs

List recent jobs (status only, no results payload).

**Query parameters**
- `limit` (integer, default `20`) — Number of jobs to return, newest first

**Response 200**
```json
{
  "jobs": [
    {
      "job_id": "uuid-string",
      "status": "done",
      "progress": { "step": "Complete", "pct": 100 },
      "count": 81,
      "error": null,
      "filename": "genome.vcf",
      "file_size": 1048576,
      "created_at": "2026-03-14T12:00:00Z",
      "started_at": "2026-03-14T12:00:01Z",
      "finished_at": "2026-03-14T12:02:34Z"
    }
  ]
}
```

---

## Biomarker tracking API (`/tracking`)

Longitudinal biomarker tracking with Bayesian response prediction (`engine/tracking/`, mounted under `/tracking`). All routes return JSON.

**Patients & data**

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/tracking/patients` | Create a patient |
| `GET` | `/tracking/patients` | List patients |
| `GET` | `/tracking/patients/{id}` | Get one patient |
| `DELETE` | `/tracking/patients/{id}` | Delete patient (cascades treatments + measurements) |
| `POST` | `/tracking/patients/{id}/treatments` | Add a peptide treatment (peptide, dose, schedule, start date) |
| `GET` | `/tracking/patients/{id}/treatments` | List a patient's treatments |
| `POST` | `/tracking/measurements` | Add one biomarker measurement |
| `POST` | `/tracking/measurements/bulk` | Add many measurements at once |
| `POST` | `/tracking/measurements/csv` | Upload measurements as CSV |
| `GET` | `/tracking/patients/{id}/measurements` | List a patient's measurements |

**Genetics & priors**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/tracking/patients/{id}/genetics` | Get the patient's genetic profile |
| `POST` | `/tracking/patients/{id}/genetics/synthetic` | Attach a synthetic genetic profile (demo) |
| `POST` | `/tracking/patients/from-job/{job_id}` | Create a tracking patient from a finished analysis job |
| `GET` | `/tracking/patients/{id}/priors` | Per-peptide responder-strength priors derived from genetics |

**Prediction**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/tracking/patients/{id}/predictions?peptide={p}&biomarker={b}` | Bayesian posterior + 95% credible-interval predictive curve for one (patient, peptide, biomarker) |

The prediction response fuses a genetics-derived prior, leave-one-out cohort pooling, and the measurement likelihood into a Normal–Normal posterior. Key fields: `posterior` (`mean_pct_change`, `credible_lo_95`, `credible_hi_95`), `posterior_predictive` / `prior_predictive` (per-week `mean`, `lo_95`, `hi_95` curves), `prior` (carries `evidence_grade` when the biomarker has a research-backed registry entry — see `docs/architecture.md`), `expected_window`, and `responder_features`.

`responder_features` is the per-feature provenance of the HBRI[^hbri] responder index — an array (one entry per feature-adapter that fired) of `{ "name", "value", "beta", "variance", "source" }`, where `source` is the emitting adapter (e.g. `genetics`, and, when patient enrichment is present, `prs_inflammatory_baseline` / `bpc157_composite` / `covariates` / `healthkit_behavior`). The full generative model is in `docs/models/peptide-response-model.md`.

**Catalog & demo**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/tracking/peptides` | List supported peptides (includes the GLP-1 / incretin class) |
| `GET` | `/tracking/peptides/{name}/biomarkers` | Biomarker panel for a peptide |
| `GET` | `/tracking/cohort?peptide={p}&biomarker={b}` | Cohort trajectory (median + IQR band) |
| `POST` | `/tracking/seed` | Populate synthetic demo data |

> The generative model is documented in-app at `/tracking/model`.

---

## HealthKit ingestion API (`/healthkit`)

De-identified ingestion of Apple HealthKit samples from the peptodyssey iOS app (`engine/healthkit/`, mounted under `/healthkit`). Subjects are the app-assigned opaque `subject_id` — never a user identity. A migration-010 subject↔patient bridge (`healthkit_subject_map`) links a subject to a tracking patient; see `docs/healthkit-storage.md`.

**Authentication** — interim per-device bearer token (`Authorization: Bearer pep_hk_…`). Enforcement is **fail-closed in prod**: when a real database is configured (`DATABASE_URL` set) a valid token is **always** required and no env var can open it. The local SQLite dev/test fallback (no `DATABASE_URL`) is open unless `HEALTHKIT_REQUIRE_TOKEN=1`. A token may be bound to a single `subject_id` (a bound token may only touch that subject); read requests additionally require a *bound* token so a shared token cannot read every subject's data. Tokens are stored only as SHA-256 hashes (mint via `scripts/create_healthkit_token.py`). The longer-term auth target is Authentik device-code flow.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/healthkit/samples` | Idempotent batch upload of HealthKit samples (insert-only by sample `uuid`) |
| `GET` | `/healthkit/samples` | Read back a subject's stored samples |

### POST /healthkit/samples

**Request body** (JSON; keys accept iOS-natural camelCase)
```json
{
  "subjectId": "opaque-subject-id",
  "samples": [
    {
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "class": "HKQuantitySample",
      "type": "HKQuantityTypeIdentifierBodyMass",
      "value": 81.2,
      "unit": "kg",
      "start": "2026-07-01T08:00:00Z",
      "end": "2026-07-01T08:00:00Z",
      "source": { "name": "iPhone", "bundleId": "com.apple.Health" },
      "device": {},
      "metadata": {},
      "workout": {
        "activityType": "running",
        "durationSeconds": 1800,
        "totalEnergyKcal": 240,
        "totalDistanceMeters": 4200
      }
    }
  ],
  "anchors": { "HKQuantityTypeIdentifierBodyMass": "base64-HKQueryAnchor" }
}
```
- `subjectId` (aliased `subject_id`) — required, 1–128 chars
- `samples[].class` — HealthKit sample class (aliased from the reserved word `class`)
- `value`, `unit`, `source`, `device`, `metadata`, `workout` are optional per sample
- `anchors` — optional per-type `HKQueryAnchor` mirror (base64), `type_identifier → anchor`

**Response 200**
```json
{ "received": 1, "inserted": 1 }
```
`received` counts samples in the request; `inserted` counts newly stored rows (duplicates by `uuid` are skipped — the write is idempotent).

### GET /healthkit/samples

**Query parameters**
- `subject_id` (string, required)
- `type` (string, optional) — filter by HealthKit type identifier
- `since` (ISO-8601, optional) — only samples with `start_time >= since`
- `limit` (integer, default `1000`, range 1–10000)

**Response 200** — a JSON array of stored sample rows.

**Error responses**
| Code | Reason |
|------|--------|
| 401 | Token required (prod / `HEALTHKIT_REQUIRE_TOKEN=1`) but missing, invalid, or revoked |
| 403 | Token bound to a different `subject_id`, or (read) an unbound token used |

---

## User accounts API (`/users`)

Local app-user rows behind an Authentik forward-auth proxy (`engine/users/`, mounted under `/users`). The proxy is expected to forward trusted `X-Authentik-*` headers identifying the caller; the router materialises a local users row on first sight.

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/users/me` | Return (and lazily create) the user row for the Authentik subject on this request |
| `GET` | `/users` | List all known users (admin/operator view; the proxy gates access) |

**User object**
```json
{
  "id": "string",
  "authentik_uid": "string",
  "username": "string",
  "email": "string|null",
  "full_name": "string|null",
  "groups": ["group-a"],
  "created_at": "2026-07-01T00:00:00Z",
  "last_seen_at": "2026-07-01T00:00:00Z",
  "disabled_at": "string|null"
}
```

**Error responses**
| Code | Reason |
|------|--------|
| 401 | `GET /users/me` when no Authentik subject was forwarded (request bypassed the proxy or open-demo mode) — treat as unauthenticated |

---

## Other endpoints

- `POST /jobs/{job_id}/variants/{variant_id}/acmg-signoff` — qualified human sign-out of an ACMG/AMP classification (the pipeline assembles evidence; a human makes the final call).
- `GET /regulatory/peptides` — curated peptide FDA status merged with live sources.
- `GET /regulatory/events` — regulatory events feed (ClinicalTrials.gov, openFDA, Federal Register); live-source failures degrade gracefully.

---

## Job lifecycle

```
POST /analyze  →  pending  →  running (progress 0→100%)  →  done
                                                           →  failed
```

Jobs persist to Postgres when `DATABASE_URL` is set; without it they live only in an in-memory store and are lost on restart. Either way, completed jobs are retained for `JOB_TTL_HOURS` hours, then purged. (The former `JOB_STORE_KEY`/Fernet on-disk snapshot is deprecated and no longer used.)

---

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `DATABASE_URL` | _(none)_ | Postgres connection string. When set, all caches/stores — annotation cache, rsID cache, tracking, jobs, HealthKit — use Postgres (via `db/pool.py`, migrations applied by `db/migrate.py`); without it, SQLite/in-memory fallback for local dev/tests |
| `HEALTHKIT_REQUIRE_TOKEN` | _(unset)_ | Set to `1` to require a device token even in the open SQLite dev/test fallback (always required when `DATABASE_URL` is set) |
| `WORKERS` | `4` | Thread pool size |
| `MAX_UPLOAD_MB` | `100` | Upload size limit (MB) |
| `JOB_TTL_HOURS` | `24` | Job retention window (hours) |
| `FILTERS` | `acmg81_rsids.txt` | Comma-separated filter files in DATA_DIR |
| `DATA_DIR` | `data` | Path to filter file directory |
| `NCBI_API_KEY` | _(none)_ | NCBI API key (raises ClinVar rate limit 3→10 req/s) |

---

## Footnotes

[^iso8601]: **ISO-8601** — the international date/time format standard, e.g. `2026-03-14T12:00:00Z` (the trailing `Z` means UTC).
[^async]: **Asynchronous job** — the request returns immediately with a `job_id` instead of waiting for the work to finish; the client polls a separate endpoint for the result. Suits long-running analysis.
[^multipart]: **multipart/form-data** — the HTTP body encoding used to upload files in a form POST; each part carries one field or file with its own headers.
[^uuid]: **UUID** — Universally Unique Identifier, a 128-bit random ID (e.g. `550e8400-e29b-...`) used so each job has a collision-free handle.
[^http202]: **HTTP 202 Accepted** — the request was accepted for processing but is not yet complete; used here to acknowledge a job submission before analysis runs.
[^http413]: **HTTP 413 Payload Too Large** — the uploaded file exceeds the server's size limit (`MAX_UPLOAD_MB`).
[^http422]: **HTTP 422 Unprocessable Entity** — the request was well-formed but semantically invalid (here: empty file or unsupported genome format).
[^http404]: **HTTP 404 Not Found** — no job exists for the given ID, or it has expired and been purged.
[^ttl]: **TTL (Time To Live)** — how long a completed job is retained in memory before being purged (`JOB_TTL_HOURS`, default 24 h).
[^zygosity]: **Zygosity** — whether the two copies at a site match: heterozygous (one alt), homozygous_alt (two alt), or unknown.
[^consequence]: **Consequence** — the predicted molecular effect of the variant, given as a Sequence Ontology term such as `missense_variant`.
[^clinvar]: **ClinVar** — NCBI's archive of variant–clinical-significance relationships; supplies the `clinvar` classification (Pathogenic, Benign, etc.).
[^conditionkey]: **condition_key** — a stable identifier for the associated condition, formatted `OMIM:<id>`, `MedGen:<id>`, or `ClinVar:<id>`; used to join curated plain-English condition text.
[^gnomad]: **gnomAD AF / popmax** — population allele frequency from the Genome Aggregation Database; `gnomad_af` is the overall frequency, `gnomad_popmax` the highest across individual ancestry groups.
[^tier]: **Tier** — the engine's clinical-priority bucket (critical / high / medium / low) derived from the numeric `score`.
[^hbri]: **HBRI** — the tracking module's unified peptide-response model: a responder index `η = 1 + Δ·tanh(βᵀx)` assembled from an auto-discovering feature-adapter registry (`engine/tracking/feature_adapters/`). Authoritative spec: `docs/models/peptide-response-model.md`.
