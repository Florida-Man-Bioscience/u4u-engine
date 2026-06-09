"""
api.py — U4U Engine FastAPI wrapper
====================================
Wraps run_pipeline() as an async job queue service.

Architecture
------------
  POST /analyze          — upload file, get back a job_id immediately
  GET  /jobs/{job_id}    — poll for status, progress, and results
  GET  /jobs/{job_id}/dossier/{peptide_name} — get dossier HTML for a peptide
  GET  /health           — liveness check

The pipeline runs in a thread pool (blocking IO — external API calls).
The client polls /jobs/{job_id} until status is "done" or "failed".

Job storage
-----------
Jobs are cached in memory and mirrored to a small JSON file so completed
results survive an API process restart.  Raw uploaded genome files are still
processed from memory and are never written to disk by this wrapper.

Environment variables
---------------------
NCBI_API_KEY    — NCBI API key (optional, raises ClinVar rate limit 3→10 req/s)
DATA_DIR        — path to directory containing rsID filter files (default: "data")
FILTERS         — comma-separated filter filenames (default: "acmg81_rsids.txt")
                  set to "" to run all variants without a panel filter
WORKERS         — thread pool size — set to CPU count of host (default: 4)
MAX_UPLOAD_MB   — file size limit in megabytes (default: 100)
JOB_TTL_HOURS   — hours to keep completed jobs in the job store (default: 24)
JOB_STORE_PATH  — JSON job store path (default: "${DATA_DIR}/jobs.json")
ALLOWED_ORIGINS — comma-separated CORS origins for browser clients
"""

import asyncio
import json
import logging
import os
from pathlib import Path
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

from engine import run_pipeline

# ── Configuration ─────────────────────────────────────────────────────────────

DATA_DIR      = os.getenv("DATA_DIR", "data")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "100"))
WORKERS       = int(os.getenv("WORKERS", "4"))
JOB_TTL_HOURS = int(os.getenv("JOB_TTL_HOURS", "24"))
JOB_STORE_PATH = os.getenv("JOB_STORE_PATH", os.path.join(DATA_DIR, "jobs.json"))

_raw_filters = os.getenv("FILTERS", "acmg81_rsids.txt").strip()
FILTERS      = [f.strip() for f in _raw_filters.split(",") if f.strip()] if _raw_filters else []

_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").strip()
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("u4u.api")

# ── App ───────────────────────────────────────────────────────────────────────

app      = FastAPI(
    title="U4U Engine API",
    version="2.0.0",
    description="Genomic variant annotation and interpretation pipeline.",
)

# ── CORS — allow configured browser clients to reach the API ───────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
_executor = ThreadPoolExecutor(max_workers=WORKERS)

# ── Biomarker tracking router (longitudinal measurements + cohort analysis) ──
from engine.tracking.api import router as _tracking_router  # noqa: E402
app.include_router(_tracking_router)

# ── Job store ─────────────────────────────────────────────────────────────────
# Schema per job:
#   status     : "pending" | "running" | "done" | "failed"
#   progress   : {"step": str, "pct": int}
#   count      : int | None     — number of variants found
#   results    : list[dict] | None
#   error      : str | None
#   filename   : str
#   file_size  : int
#   created_at : str (ISO-8601)
#   started_at : str | None
#   finished_at: str | None

_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public_job(job_id: str, job: dict, include_results: bool = True) -> dict:
    """Return a frontend-safe job payload with backward-compatible aliases."""
    progress = job.get("progress") or {}
    response = dict(job)
    response["job_id"] = job_id
    response["progress"] = {
        "step": progress.get("step", ""),
        "pct": int(progress.get("pct", 0) or 0),
    }
    response["progress_step"] = response["progress"]["step"]
    response["progress_pct"] = response["progress"]["pct"]
    response["error_message"] = job.get("error")
    response["variant_count"] = job.get("count")
    response["partial_results"] = list(job.get("partial_results") or [])
    response.pop("_persisted_partial_count", None)

    if not include_results:
        response.pop("results", None)
        response.pop("partial_results", None)

    return response


def _serializable_job(job: dict) -> dict:
    """Strip process-local fields before writing a job to disk."""
    payload = dict(job)
    payload["partial_results"] = list(job.get("partial_results") or [])
    return payload


def _persist_jobs_locked() -> None:
    """Atomically mirror the in-memory job store to disk."""
    path = Path(JOB_STORE_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump({jid: _serializable_job(job) for jid, job in _jobs.items()}, fh)
        tmp_path.replace(path)
    except Exception:
        log.exception("failed to persist job store to %s", JOB_STORE_PATH)


def _persist_jobs() -> None:
    with _jobs_lock:
        _persist_jobs_locked()


def _load_jobs_from_disk() -> None:
    """Load persisted jobs, marking interrupted pending/running jobs failed."""
    path = Path(JOB_STORE_PATH)
    if not path.exists():
        return

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        log.exception("failed to read job store from %s", JOB_STORE_PATH)
        return

    if not isinstance(data, dict):
        log.warning("ignoring invalid job store at %s", JOB_STORE_PATH)
        return

    now = _now_iso()
    restored = 0
    with _jobs_lock:
        for job_id, job in data.items():
            if not isinstance(job, dict):
                continue
            job.setdefault("progress", {"step": "Restored", "pct": 0})
            job.setdefault("count", None)
            job.setdefault("results", None)
            job.setdefault("partial_results", [])
            job.setdefault("error", None)
            job.setdefault("started_at", None)
            job.setdefault("finished_at", None)
            if job.get("status") in {"pending", "running"}:
                job.update({
                    "status": "failed",
                    "error": "Job was interrupted by an API restart. Please upload again.",
                    "finished_at": now,
                })
            _jobs[str(job_id)] = job
            restored += 1
    log.info("loaded %d jobs from %s", restored, JOB_STORE_PATH)


# ── Background job runner ─────────────────────────────────────────────────────

def _progress_callback(job_id: str, step: str, pct: int):
    """Called by the pipeline on each step — updates the job record."""
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id]["progress"] = {"step": step, "pct": pct}
            _persist_jobs_locked()


def _run_pipeline_task(
    job_id: str,
    file_bytes: bytes,
    filename: str,
    current_medications: list | None = None,
):
    """
    Blocking pipeline run — executed in the thread pool.
    Updates the in-memory job record as it runs.
    """
    with _jobs_lock:
        _jobs[job_id]["status"]     = "running"
        _jobs[job_id]["started_at"] = _now_iso()
        _persist_jobs_locked()

    log.info("job=%s starting file=%s size=%d bytes", job_id, filename, len(file_bytes))

    with _jobs_lock:
        partial_results_ref = _jobs[job_id]["partial_results"]

    try:
        pipeline_output = run_pipeline(
            file_bytes,
            filename,
            filters=FILTERS,
            bed_filter="peptide_genes.bed",
            data_dir=DATA_DIR,
            progress_callback=lambda step, pct: _progress_callback(job_id, step, pct),
            partial_results=partial_results_ref,
            current_medications=current_medications,
        )
        # V3: run_pipeline returns a dict with 'variants' and enrichment data.
        variants = pipeline_output.get("variants", [])
        with _jobs_lock:
            _jobs[job_id].update({
                "status":      "done",
                "count":       len(variants),
                "results":     pipeline_output,
                "progress":    {"step": "Complete", "pct": 100},
                "finished_at": _now_iso(),
            })
            _persist_jobs_locked()
        log.info("job=%s done variants=%d", job_id, len(variants))

    except ValueError as exc:
        with _jobs_lock:
            _jobs[job_id].update({
                "status":      "failed",
                "error":       str(exc),
                "finished_at": _now_iso(),
            })
            _persist_jobs_locked()
        log.warning("job=%s validation error: %s", job_id, exc)

    except Exception as exc:
        with _jobs_lock:
            _jobs[job_id].update({
                "status":      "failed",
                "error":       "Pipeline error. Check server logs.",
                "finished_at": _now_iso(),
            })
            _persist_jobs_locked()
        log.exception("job=%s unhandled pipeline error", job_id)


# ── Periodic job cleanup ──────────────────────────────────────────────────────

async def _cleanup_old_jobs():
    """Remove completed/failed jobs older than JOB_TTL_HOURS to prevent memory leak."""
    while True:
        await asyncio.sleep(3600)  # run hourly
        cutoff = datetime.now(timezone.utc) - timedelta(hours=JOB_TTL_HOURS)
        with _jobs_lock:
            expired = [
                jid for jid, j in _jobs.items()
                if j["status"] in ("done", "failed")
                and j.get("finished_at")
                and datetime.fromisoformat(j["finished_at"]) < cutoff
            ]
            for jid in expired:
                del _jobs[jid]
            if expired:
                _persist_jobs_locked()
        if expired:
            log.info("cleanup: removed %d expired jobs", len(expired))


@app.on_event("startup")
async def _startup():
    _load_jobs_from_disk()
    asyncio.create_task(_cleanup_old_jobs())


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """
    Liveness check. Returns 200 when the server is up.

    Also reports queue depth so ops can detect backlog.
    """
    with _jobs_lock:
        running = sum(1 for j in _jobs.values() if j["status"] == "running")
        pending = sum(1 for j in _jobs.values() if j["status"] == "pending")
    return {"status": "ok", "jobs_running": running, "jobs_pending": pending}


@app.post("/analyze", status_code=202)
async def analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_medications: str = "",
):
    """
    Upload a genome file and receive a job_id.

    The file is processed asynchronously. Poll GET /jobs/{job_id} for results.

    Accepted formats: .vcf, .vcf.gz (primary), .txt (23andMe), .csv, rsID list.
    File is read into memory, processed, and discarded — never written to disk.

    Returns
    -------
    {
        "job_id": str,
        "status": "pending",
        "poll_url": "/jobs/{job_id}"
    }

    Status codes
    ------------
    202  Job accepted
    413  File exceeds MAX_UPLOAD_MB limit
    422  Unsupported / empty file (caught before background task starts)
    """
    filename   = file.filename or "upload"
    file_bytes = await file.read()

    # ── Size guard (before job is created) ───────────────────────────────────
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {MAX_UPLOAD_MB} MB limit.",
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=422, detail="Empty file.")

    # ── Create job record ─────────────────────────────────────────────────────
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "status":      "pending",
            "progress":    {"step": "Queued", "pct": 0},
            "count":       None,
            "results":     None,
            "partial_results": [],
            "error":       None,
            "filename":    filename,
            "file_size":   len(file_bytes),
            "created_at":  _now_iso(),
            "started_at":  None,
            "finished_at": None,
        }
        _persist_jobs_locked()

    # ── Dispatch to thread pool via BackgroundTasks ──────────────────────────
    # BackgroundTasks runs after the response is sent, in the event loop.
    # We submit to _executor to keep the async event loop free.
    loop = asyncio.get_event_loop()
    meds = [m.strip() for m in current_medications.split(",") if m.strip()] if current_medications else None
    background_tasks.add_task(
        loop.run_in_executor,
        _executor,
        _run_pipeline_task,
        job_id,
        file_bytes,
        filename,
        meds,
    )

    log.info("job=%s queued file=%s size=%d bytes", job_id, filename, len(file_bytes))

    return JSONResponse(
        status_code=202,
        content={
            "job_id":   job_id,
            "status":   "pending",
            "poll_url": f"/jobs/{job_id}",
        },
    )


@app.get("/jobs/{job_id}")
def get_job(job_id: str, include_results: bool = True):
    """
    Poll job status and retrieve results when complete.

    Parameters
    ----------
    include_results : bool
        Set to false to get status/progress without the full results list.
        Useful for a progress bar that only fetches results once status=done.

    Returns
    -------
    {
        "job_id":     str,
        "status":     "pending" | "running" | "done" | "failed",
        "progress":   {"step": str, "pct": int},
        "count":      int | null,
        "results":    [...] | null,    # null if pending/running or include_results=false
        "error":      str | null,
        "filename":   str,
        "file_size":  int,
        "created_at": str,             # ISO-8601
        "started_at": str | null,
        "finished_at":str | null
    }

    Polling guidance
    ----------------
    - Poll every 2–5 seconds while status is "pending" or "running".
    - Stop when status is "done" or "failed".
    - Jobs expire after JOB_TTL_HOURS (default 24h) — 404 after that.
    """
    with _jobs_lock:
        job = _jobs.get(job_id)
        response = _public_job(job_id, job, include_results=include_results) if job else None

    if not response:
        raise HTTPException(status_code=404, detail="Job not found or expired.")

    return response


@app.get("/jobs")
def list_jobs(limit: int = 20):
    """
    List recent jobs (status only — no results payload).
    Useful for ops dashboards. Returns newest first.
    """
    with _jobs_lock:
        snapshot = sorted(
            [_public_job(jid, j, include_results=False) for jid, j in _jobs.items()],
            key=lambda x: x.get("created_at", ""),
            reverse=True,
        )
    return {"jobs": snapshot[:limit]}


@app.get("/jobs/{job_id}/dossier/{peptide_name}", response_class=HTMLResponse)
def get_dossier(job_id: str, peptide_name: str):
    """
    Return the pre-rendered HTML dossier for a specific peptide therapy.
    """
    with _jobs_lock:
        job = _jobs.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="Job not yet complete")

    results = job.get("results", {})
    dossiers = results.get("dossiers", {})

    if peptide_name not in dossiers:
        available = list(dossiers.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Dossier not found for '{peptide_name}'. Available: {available}",
        )

    return HTMLResponse(content=dossiers[peptide_name])


@app.get("/jobs/{job_id}/pgx")
def get_pgx(job_id: str):
    """Return the full pharmacogenomics profile for a completed job."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="Job not yet complete")
    pgx = (job.get("results") or {}).get("pgx_profile")
    if not pgx:
        raise HTTPException(status_code=404, detail="No PGx profile for this job")
    return pgx


@app.get("/jobs/{job_id}/drug/{drug}")
def get_drug(job_id: str, drug: str):
    """
    Return per-drug PGx evidence for a specific drug: CPIC recommendations,
    matching star-allele phenotypes, contributing PRS, and the conformal
    prediction set from the HGNN/rule-based ranker.
    """
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="Job not yet complete")
    pgx = (job.get("results") or {}).get("pgx_profile") or {}

    drug_l = drug.lower()
    recs = [r for r in pgx.get("recommendations", []) if r.get("drug", "").lower() == drug_l]
    prs = [p for p in pgx.get("prs_results", []) if drug_l in [d.lower() for d in p.get("drug_context", [])]]
    pred = next((d for d in pgx.get("drug_predictions", []) if d.get("drug", "").lower() == drug_l), None)
    hla = [h for h in pgx.get("hla_calls", []) if h.get("present") and drug_l in [d.lower() for d in h.get("risk_drugs", [])]]

    if not (recs or prs or pred or hla):
        raise HTTPException(status_code=404, detail=f"No PGx data available for drug '{drug}'")

    return {
        "drug": drug,
        "recommendations": recs,
        "prs": prs,
        "prediction": pred,
        "hla_warnings": hla,
    }


# ── Regulatory dashboard ──────────────────────────────────────────────────────


@app.get("/regulatory/peptides")
async def get_regulatory_peptides(include_live: bool = True):
    """
    FDA regulatory status per peptide — curated categorization plus live
    augments (ClinicalTrials.gov counts, openFDA recalls, Federal Register
    notices). Live source failures do not fail the request; each source
    carries a `status` of "fresh" | "stale" | "unavailable".
    """
    from engine.regulatory import build_dashboard_payload

    loop = asyncio.get_event_loop()
    payload = await loop.run_in_executor(
        _executor, lambda: build_dashboard_payload(include_live=include_live)
    )
    return payload


@app.get("/regulatory/events")
async def get_regulatory_events(include_live: bool = True):
    """
    Critical regulatory dates, the event timeline, official source links,
    and a live count of comments on docket FDA-2025-N-6895.
    """
    from engine.regulatory import build_events_payload

    loop = asyncio.get_event_loop()
    payload = await loop.run_in_executor(
        _executor, lambda: build_events_payload(include_live=include_live)
    )
    return payload
