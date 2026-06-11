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
import hmac
import json
import logging
import os
from pathlib import Path
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

from engine import run_pipeline
from engine.acmg import apply_signoff


class AcmgSignoffRequest(BaseModel):
    reviewer: str
    action: str = "approve"          # "approve" | "amend"
    final_classification: str | None = None
    notes: str = ""

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

# ── Authentication ─────────────────────────────────────────────────────────
# All endpoints except /health require a valid API key (Authorization: Bearer
# <key> or X-API-Key: <key>). The service fails CLOSED: if no keys are
# configured it refuses protected requests, unless ALLOW_INSECURE_NO_AUTH is
# explicitly set for local development/testing.
_raw_keys = os.getenv("API_KEYS", os.getenv("API_KEY", "")).strip()
API_KEYS = {k.strip() for k in _raw_keys.split(",") if k.strip()}
ALLOW_INSECURE_NO_AUTH = os.getenv("ALLOW_INSECURE_NO_AUTH", "").lower() in ("1", "true", "yes", "on")

# ── Job-store encryption ───────────────────────────────────────────────────
# Completed job results are derived from the user's genome (variants,
# genotypes, conditions) and are therefore sensitive. They are only persisted
# to disk when encrypted with a configured Fernet key (JOB_STORE_KEY). With no
# key, disk persistence is DISABLED (in-memory only) rather than writing
# plaintext PHI to disk.
JOB_STORE_KEY = os.getenv("JOB_STORE_KEY", "").strip()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("u4u.api")

try:
    from cryptography.fernet import Fernet, InvalidToken
    _CRYPTO_AVAILABLE = True
except Exception:  # ImportError, or a broken/incomplete crypto backend
    _CRYPTO_AVAILABLE = False
    InvalidToken = Exception  # type: ignore

_fernet = None
if JOB_STORE_KEY and _CRYPTO_AVAILABLE:
    try:
        _fernet = Fernet(JOB_STORE_KEY.encode())
    except Exception:
        log.error("JOB_STORE_KEY is not a valid Fernet key — disk persistence disabled.")
        _fernet = None

PERSIST_ENABLED = _fernet is not None
if not PERSIST_ENABLED:
    log.warning(
        "Job-store disk persistence DISABLED (no valid JOB_STORE_KEY or cryptography "
        "unavailable). Genomic-derived results are kept in memory only and lost on "
        "restart. Set JOB_STORE_KEY to a Fernet key to enable encrypted persistence."
    )
if not API_KEYS and not ALLOW_INSECURE_NO_AUTH:
    log.warning(
        "No API_KEYS configured — protected endpoints will reject all requests "
        "until keys are set (or ALLOW_INSECURE_NO_AUTH is enabled for dev)."
    )


def _valid_api_key(provided: str) -> bool:
    """Constant-time membership check against the configured API keys."""
    return any(hmac.compare_digest(provided, k) for k in API_KEYS)

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

# ── Authentication middleware ──────────────────────────────────────────────
# /auth/login is exempt so a fresh client can obtain a session token; every
# other /auth/* endpoint still requires authentication.
_AUTH_EXEMPT_PATHS = {
    "/health", "/", "/docs", "/redoc", "/openapi.json", "/auth/login",
}


@app.middleware("http")
async def _auth_middleware(request, call_next):
    path = request.url.path
    # Allow CORS preflight and unauthenticated liveness/docs.
    if request.method == "OPTIONS" or path in _AUTH_EXEMPT_PATHS:
        return await call_next(request)
    if ALLOW_INSECURE_NO_AUTH:
        return await call_next(request)

    # Two parallel auth paths:
    #   1. ``API_KEYS`` — service-to-service shared secrets (Bearer or
    #      X-API-Key), checked first because it's a cheap constant-time
    #      compare with no DB hit.
    #   2. Session tokens minted by /auth/login — checked when the API
    #      key path doesn't match, so end-user browsers can call the API
    #      after logging in.
    # The server fails closed only if neither mechanism is configured.
    from engine.auth import db as _auth_db, service as _auth_service  # local import to avoid cycles

    auth_header = request.headers.get("authorization", "")
    bearer = auth_header[7:].strip() if auth_header.lower().startswith("bearer ") else ""
    api_key_header = request.headers.get("x-api-key", "").strip()
    provided = bearer or api_key_header

    if API_KEYS and provided and _valid_api_key(provided):
        request.state.auth_user = None  # service-to-service caller
        return await call_next(request)

    if bearer:
        try:
            conn = _auth_db.get_conn()
            session_user = _auth_service.get_session_user(conn, bearer)
        except Exception:
            log.exception("auth: session lookup failed")
            session_user = None
        if session_user is not None:
            request.state.auth_user = session_user
            return await call_next(request)

    # Neither path matched.
    if not API_KEYS and not _has_any_user():
        return JSONResponse(
            status_code=503,
            content={"detail": "Authentication is not configured on this server."},
        )
    return JSONResponse(
        status_code=401, content={"detail": "Missing or invalid credentials."},
    )


def _has_any_user() -> bool:
    """Return True if at least one user account exists. Used to decide
    503 vs 401: a freshly-deployed server with no users and no API keys
    can't accept any login, so 503 is the truthful response."""
    try:
        from engine.auth import db as _auth_db, service as _auth_service
        return _auth_service.count_users(_auth_db.get_conn()) > 0
    except Exception:
        return False

# ── Auth router (username/password login → opaque session token) ────────────
from engine.auth.api import router as _auth_router  # noqa: E402
app.include_router(_auth_router)

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

    # Surface genome build and analysis completeness even when full results are
    # omitted, so a clinician/UI can see the build used and whether any variant
    # failed annotation (an incomplete analysis must not look like a clean run).
    results = job.get("results")
    if isinstance(results, dict):
        response["genome_build"] = results.get("genome_build")
        response["analysis_status"] = results.get("analysis_status")
        response["acmg_summary"] = results.get("acmg_summary")

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
    """Atomically mirror the in-memory job store to disk, encrypted at rest."""
    if not PERSIST_ENABLED:
        return  # in-memory only — never write plaintext genomic-derived data
    path = Path(JOB_STORE_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {jid: _serializable_job(job) for jid, job in _jobs.items()}
        ).encode("utf-8")
        token = _fernet.encrypt(payload)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_bytes(token)
        tmp_path.replace(path)
    except Exception:
        log.exception("failed to persist job store to %s", JOB_STORE_PATH)


def _persist_jobs() -> None:
    with _jobs_lock:
        _persist_jobs_locked()


def _load_jobs_from_disk() -> None:
    """Load persisted jobs, marking interrupted pending/running jobs failed."""
    if not PERSIST_ENABLED:
        return
    path = Path(JOB_STORE_PATH)
    if not path.exists():
        return

    try:
        token = path.read_bytes()
        data = json.loads(_fernet.decrypt(token).decode("utf-8"))
    except InvalidToken:
        log.error(
            "job store at %s could not be decrypted (wrong JOB_STORE_KEY?) — ignoring",
            JOB_STORE_PATH,
        )
        return
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
    # Seed the initial admin user from env vars if the users table is
    # empty. Seed-only-on-empty: subsequent env changes do not rotate
    # credentials. See engine/auth/service.bootstrap_admin for the
    # rationale.
    try:
        from engine.auth import db as _auth_db, service as _auth_service
        seeded = _auth_service.bootstrap_admin(_auth_db.get_conn())
        if seeded is not None:
            log.info("auth: bootstrapped admin user '%s' from env", seeded.username)
    except Exception:
        log.exception("auth: bootstrap failed")
    asyncio.create_task(_cleanup_old_jobs())
    asyncio.create_task(_purge_expired_sessions_loop())


async def _purge_expired_sessions_loop() -> None:
    """Hourly housekeeping for the sessions table.

    Expired tokens are also dropped on read by ``get_session_user``, but
    that only catches sessions someone actually tries to use again. A
    token that was issued and then the user closed the tab on stays in
    the table forever without this loop. Hourly is plenty — the table
    is tiny and SQLite handles a few-second blocking sweep easily.
    """
    from engine.auth import db as _auth_db, service as _auth_service
    while True:
        try:
            await asyncio.sleep(3600)
            n = _auth_service.purge_expired_sessions(_auth_db.get_conn())
            if n:
                log.info("auth: purged %d expired sessions", n)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("auth: session purge failed")


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
    # Medications are PHI — accept them as a multipart form field, never as a
    # URL query parameter (which would land in access logs / browser history).
    current_medications: str = Form(""),
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


@app.post("/jobs/{job_id}/variants/{variant_id}/acmg-signoff")
def acmg_signoff(job_id: str, variant_id: str, req: AcmgSignoffRequest):
    """
    Record a qualified reviewer's sign-out of a variant's automated ACMG/AMP
    classification (approve the draft, or amend it). Updates and persists the
    job. Returns the updated `acmg` block.
    """
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job["status"] != "done":
            raise HTTPException(status_code=409, detail="Job not yet complete")

        variants = (job.get("results") or {}).get("variants") or []
        target = next(
            (v for v in variants
             if v.get("variant_id") == variant_id or v.get("rsid") == variant_id),
            None,
        )
        if target is None:
            raise HTTPException(status_code=404, detail=f"Variant {variant_id!r} not found in job")
        if not target.get("acmg"):
            raise HTTPException(status_code=409, detail="Variant has no ACMG classification to sign out")

        try:
            target["acmg"] = apply_signoff(
                target["acmg"],
                reviewer=req.reviewer,
                action=req.action,
                final_classification=req.final_classification,
                notes=req.notes,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        _persist_jobs_locked()
        return target["acmg"]


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
