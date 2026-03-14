# U4U Engine API Reference

Base URL: `http://<host>:8000`

All responses are JSON. All timestamps are ISO-8601.

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

Upload a genome file and start an asynchronous analysis job.

**Request**
- Content-Type: `multipart/form-data`
- Field: `file` (required) — `.vcf`, `.vcf.gz`, `.txt` (23andMe), `.csv`, or rsID list
- Max size: `MAX_UPLOAD_MB` (default 100 MB)

**Response 202**
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
| 413 | File exceeds MAX_UPLOAD_MB |
| 422 | Empty file or unsupported format |

---

### GET /jobs/{job_id}

Poll job status and retrieve results when complete.

**Path parameters**
- `job_id` (string) — UUID from POST /analyze

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

**Notes**
- `results` is `null` while status is `pending` or `running`, or if `include_results=false`
- Results are pre-sorted by score descending
- Jobs expire after `JOB_TTL_HOURS` (default 24 h) and return 404
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
