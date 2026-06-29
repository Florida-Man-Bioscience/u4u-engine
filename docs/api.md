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

## Job lifecycle

```
POST /analyze  →  pending  →  running (progress 0→100%)  →  done
                                                           →  failed
```

Jobs are held in memory for `JOB_TTL_HOURS` hours after completion, then purged.

---

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
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
