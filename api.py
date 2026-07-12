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
Jobs are persisted to Postgres when DATABASE_URL is set; in dev (no
DATABASE_URL) they live only in the in-memory ``_jobs`` dict and are
lost on restart. Raw uploaded genome files are still processed from
memory and are never written to disk by this wrapper.

Environment variables
---------------------
NCBI_API_KEY    — NCBI API key (optional, raises ClinVar rate limit 3→10 req/s)
DATA_DIR        — path to directory containing rsID filter files (default: "data")
FILTERS         — comma-separated filter filenames (default: "acmg81_rsids.txt")
                  set to "" to run all variants without a panel filter
WORKERS         — thread pool size — set to CPU count of host (default: 4)
MAX_UPLOAD_MB   — file size limit in megabytes (default: 100)
JOB_TTL_HOURS   — hours to keep completed jobs in the job store (default: 24)
ALLOWED_ORIGINS — comma-separated CORS origins for browser clients
"""

import asyncio
import logging
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from engine import run_pipeline
from engine.acmg import apply_signoff
from engine.users.deps import required_user
from engine.users.models import User
from engine.users.ownership import guard_owner, owns

# ── Database (Postgres when DATABASE_URL is set, in-memory fallback otherwise) ─
_DB_URL = os.getenv("DATABASE_URL", "").strip()


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

_raw_filters = os.getenv("FILTERS", "acmg81_rsids.txt").strip()
FILTERS      = [f.strip() for f in _raw_filters.split(",") if f.strip()] if _raw_filters else []

_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").strip()
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("u4u.api")

# JOB_STORE_KEY used to drive a Fernet-encrypted JSON snapshot at
# data/jobs.json for deployments without a database. With Postgres now
# the canonical backend (and dev runs intentionally ephemeral), the
# snapshot path was removed in Phase 4 of the storage architecture
# rollout. We still read the env var so existing deploys don't see an
# "unknown variable" error — just a one-line deprecation warning. Drop
# the read entirely on the next release.
if os.getenv("JOB_STORE_KEY", "").strip():
    log.warning(
        "JOB_STORE_KEY is deprecated and no longer used — jobs persist "
        "to Postgres when DATABASE_URL is set and are in-memory only "
        "otherwise. Remove this env var on the next deploy."
    )
# ── App ───────────────────────────────────────────────────────────────────────

from contextlib import asynccontextmanager


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Startup + shutdown hooks. Replaces the deprecated
    ``@app.on_event("startup")`` pattern."""
    # Fail loud on partial U4U_OIDC_* config before doing anything else --
    # a misconfigured prod deploy must refuse to boot rather than silently
    # falling open to dev-bypass (one shared dev user for every caller).
    from engine.users.oidc import resolve_auth_mode
    auth_mode = resolve_auth_mode()
    if auth_mode == "oidc":
        log.info("Auth mode: oidc")
    else:
        log.info("Auth mode: dev-bypass (no OIDC configured)")
    _run_db_migrations()
    _load_jobs_from_store()
    # HealthKit tables (healthkit_*) are created by db/migrate.py (Postgres) or
    # lazily on first use (SQLite dev) — no lifespan hook needed.
    cleanup_task = asyncio.create_task(_cleanup_old_jobs())
    try:
        yield
    finally:
        # Tear down background tasks cleanly on shutdown so tests and
        # graceful restarts don't leak "Task was destroyed but it is
        # pending" warnings.
        cleanup_task.cancel()
        try:
            await cleanup_task
        except (asyncio.CancelledError, Exception):
            pass


app      = FastAPI(
    title="U4U Engine API",
    version="2.0.0",
    description="Genomic variant annotation and interpretation pipeline.",
    lifespan=_lifespan,
)

# ── CORS — allow configured browser clients to reach the API ───────────────
# Guard: a wildcard origin combined with credentials is a cross-origin-theft
# footgun (any site could make credentialed calls). If an operator sets
# ALLOWED_ORIGINS=*, disable credentials rather than honour the unsafe combo.
_cors_wildcard = "*" in ALLOWED_ORIGINS
if _cors_wildcard:
    log.warning(
        "ALLOWED_ORIGINS contains '*'; disabling allow_credentials for CORS. "
        "Set an explicit origin allowlist to use credentialed requests."
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=not _cors_wildcard,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _security_headers(request, call_next):
    """Baseline security response headers (defense-in-depth; the gateway may
    also set these). Applied to every response including errors."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
    )
    return response
_executor = ThreadPoolExecutor(max_workers=WORKERS)

# ── Biomarker tracking router (longitudinal measurements + cohort analysis) ──
from engine.tracking.api import router as _tracking_router  # noqa: E402

app.include_router(_tracking_router)

# ── App user accounts (Authentik-backed) ────────────────────────────────────
from engine.users.api import router as _users_router  # noqa: E402

app.include_router(_users_router)

# ── HealthKit ingestion (peptodyssey iOS app → healthkit_* tables) ───────────
from engine.healthkit.api import router as _healthkit_router  # noqa: E402

app.include_router(_healthkit_router)

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


def get_completed_job_results(job_id: str) -> dict | None:
    """Return the ``results`` dict for a completed job, or None.

    Public accessor used by the tracking module (engine/tracking/api.py)
    to derive a real-data ``GeneticProfile`` from a finished /analyze
    run without taking a circular import on this file. Returns None for
    pending/running/failed jobs and for unknown ids; the caller decides
    whether that's a 404 or a 409.
    """
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None or job.get("status") != "done":
            return None
        results = job.get("results")
        return dict(results) if isinstance(results, dict) else None


def get_job_owner(job_id: str) -> str | None:
    """Return the owning user id for a job, or None if the job is
    unknown or has no recorded owner.

    Used by the tracking module (engine/tracking/api.py) to guard
    ``POST /tracking/patients/from-job/{job_id}`` — a caller must not be
    able to seed a tracking patient from someone else's completed
    /analyze job.
    """
    with _jobs_lock:
        job = _jobs.get(job_id)
        return job.get("created_by_user_id") if job is not None else None


def get_job_filename(job_id: str) -> str | None:
    """Return the original upload filename for a job, or None.

    Lets the tracking endpoint label an auto-created patient with the
    source file ("Patient from chr1.vcf.gz") instead of an opaque uuid.
    """
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return None
        fname = job.get("filename")
        return fname if isinstance(fname, str) and fname else None


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


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
    response.pop("created_by_user_id", None)

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


def _run_db_migrations() -> None:
    """Run pending SQL migrations at startup.

    No-op when DATABASE_URL is absent (SQLite/local dev builds its schema
    lazily on first use). When DATABASE_URL is set, a migration failure is
    fatal: we log and re-raise so startup aborts — crash-looping the pod and
    surfacing the error — rather than serving requests against a half-migrated
    schema. Silently proceeding is what let missing tracking tables reach
    production and return HTTP 500 on the first query that needed them.
    """
    if not _DB_URL:
        return
    try:
        from db.migrate import run_migrations
        run_migrations(_DB_URL)
        log.info("Database migrations complete")
    except Exception:
        log.exception("Database migration failed — aborting startup")
        raise


def _pg_insert_results(job_id: str, variants: list[dict]) -> None:
    """Insert per-variant result rows. Called after pipeline completes."""
    if not _DB_URL or not variants:
        return
    try:
        import psycopg2.extras

        from db.pool import get_conn as pg_conn

        rows = []
        for v in variants:
            genes = v.get("genes") or []
            reasons = v.get("reasons") or []
            rows.append({
                "job_id": job_id,
                "variant_id": v.get("variant_id") or v.get("rsid") or f"{v.get('chrom')}:{v.get('pos')}",
                "rsid": v.get("rsid"),
                "location": v.get("location"),
                "chrom": v.get("chrom"),
                "pos": v.get("pos"),
                "ref": v.get("ref"),
                "alt": v.get("alt"),
                "zygosity": v.get("zygosity"),
                "consequence": v.get("consequence"),
                "genes": genes if isinstance(genes, list) else [genes],
                "clinvar": v.get("clinvar"),
                "clinvar_raw": v.get("clinvar_raw"),
                "disease_name": v.get("disease_name"),
                "condition_key": v.get("condition_key"),
                "gnomad_af": v.get("gnomad_af"),
                "gnomad_popmax": v.get("gnomad_popmax"),
                "gnomad_homozygote_count": v.get("gnomad_homozygote_count"),
                "score": v.get("score", 0),
                "tier": v.get("tier", "low"),
                "reasons": reasons if isinstance(reasons, list) else [reasons],
                "frequency_derived_label": v.get("frequency_derived_label"),
                "carrier_note": v.get("carrier_note"),
                "emoji": v.get("emoji"),
                "headline": v.get("headline"),
                "consequence_plain": v.get("consequence_plain"),
                "rarity_plain": v.get("rarity_plain"),
                "clinvar_plain": v.get("clinvar_plain"),
                "action_hint": v.get("action_hint"),
                "zygosity_plain": v.get("zygosity_plain"),
                "full_json": psycopg2.extras.Json(v),
            })

        with pg_conn() as conn:
            cur = conn.cursor()  # raw psycopg2 cursor via wrapper
            psycopg2.extras.execute_batch(
                cur,
                """
                INSERT INTO results (
                    job_id, variant_id, rsid, location, chrom, pos, ref, alt,
                    zygosity, consequence, genes, clinvar, clinvar_raw,
                    disease_name, condition_key, gnomad_af, gnomad_popmax,
                    gnomad_homozygote_count, score, tier, reasons,
                    frequency_derived_label, carrier_note, emoji, headline,
                    consequence_plain, rarity_plain, clinvar_plain, action_hint,
                    zygosity_plain, full_json
                ) VALUES (
                    %(job_id)s, %(variant_id)s, %(rsid)s, %(location)s,
                    %(chrom)s, %(pos)s, %(ref)s, %(alt)s, %(zygosity)s,
                    %(consequence)s, %(genes)s, %(clinvar)s, %(clinvar_raw)s,
                    %(disease_name)s, %(condition_key)s, %(gnomad_af)s,
                    %(gnomad_popmax)s, %(gnomad_homozygote_count)s, %(score)s,
                    %(tier)s, %(reasons)s, %(frequency_derived_label)s,
                    %(carrier_note)s, %(emoji)s, %(headline)s,
                    %(consequence_plain)s, %(rarity_plain)s, %(clinvar_plain)s,
                    %(action_hint)s, %(zygosity_plain)s, %(full_json)s
                )
                ON CONFLICT DO NOTHING
                """,
                rows,
                page_size=200,
            )
    except Exception:
        log.exception("failed to insert results for job %s into Postgres", job_id)


def _persist_jobs_locked() -> None:
    """Persist the current job store state.

    Postgres when DATABASE_URL is set; otherwise no-op — dev mode keeps
    jobs only in the in-memory ``_jobs`` dict and they're lost on
    restart, which is intentional. The pre-Phase-4 Fernet snapshot at
    data/jobs.json is gone.
    """
    if not _DB_URL:
        return
    try:
        import psycopg2.extras

        from db.pool import get_conn as pg_conn
        with pg_conn() as conn:
            for job_id, job in _jobs.items():
                pipeline_output = job.get("results")
                conn.execute(
                    """
                    INSERT INTO jobs (id, status, filename, file_size_bytes,
                        progress_step, progress_pct, variant_count, error_message,
                        pipeline_output_json, created_at, started_at, finished_at,
                        created_by_user_id)
                    VALUES (%(id)s, %(status)s, %(filename)s, %(file_size_bytes)s,
                        %(progress_step)s, %(progress_pct)s, %(variant_count)s,
                        %(error_message)s, %(pipeline_output_json)s,
                        %(created_at)s, %(started_at)s, %(finished_at)s,
                        %(created_by_user_id)s)
                    ON CONFLICT (id) DO UPDATE SET
                        status               = EXCLUDED.status,
                        progress_step        = EXCLUDED.progress_step,
                        progress_pct         = EXCLUDED.progress_pct,
                        variant_count        = EXCLUDED.variant_count,
                        error_message        = EXCLUDED.error_message,
                        pipeline_output_json = EXCLUDED.pipeline_output_json,
                        started_at           = EXCLUDED.started_at,
                        finished_at          = EXCLUDED.finished_at
                        -- created_by_user_id is provenance and is
                        -- never updated after the initial insert.
                    """,
                    {
                        "id": job_id,
                        "status": job.get("status", "pending"),
                        "filename": job.get("filename", ""),
                        "file_size_bytes": job.get("file_size", 0),
                        "progress_step": (job.get("progress") or {}).get("step"),
                        "progress_pct": (job.get("progress") or {}).get("pct", 0),
                        "variant_count": job.get("count"),
                        "error_message": job.get("error"),
                        "pipeline_output_json": (
                            psycopg2.extras.Json(pipeline_output)
                            if pipeline_output is not None else None
                        ),
                        "created_at": job.get("created_at"),
                        "started_at": job.get("started_at"),
                        "finished_at": job.get("finished_at"),
                        "created_by_user_id": job.get("created_by_user_id"),
                    },
                )
    except Exception:
        log.exception("failed to persist jobs to Postgres")


def _persist_jobs() -> None:
    with _jobs_lock:
        _persist_jobs_locked()


def _load_jobs_from_store() -> None:
    """Populate _jobs from Postgres if configured; no-op otherwise."""
    if _DB_URL:
        _load_jobs_from_pg()


def _load_jobs_from_pg() -> None:
    """Load recent jobs from Postgres into the in-memory store."""
    try:
        from db.pool import get_conn as pg_conn
        cutoff = datetime.now(UTC) - timedelta(hours=JOB_TTL_HOURS)
        now = _now_iso()
        restored = 0

        with pg_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id::text, status, filename, file_size_bytes,
                       progress_step, progress_pct, variant_count, error_message,
                       pipeline_output_json, created_at, started_at, finished_at,
                       created_by_user_id::text AS created_by_user_id
                FROM jobs
                WHERE created_at > %s
                ORDER BY created_at DESC
                LIMIT 500
                """,
                (cutoff,),
            )
            rows = cur.fetchall()

        with _jobs_lock:
            for row in rows:
                job_id = row["id"]
                status = row["status"]
                if status in {"pending", "running"}:
                    status = "failed"
                    error = "Job was interrupted by an API restart. Please upload again."
                    finished_at = now
                else:
                    error = row.get("error_message")
                    finished_at = row["finished_at"].isoformat() if row.get("finished_at") else None

                created_at = row["created_at"].isoformat() if row.get("created_at") else now
                started_at = row["started_at"].isoformat() if row.get("started_at") else None
                pipeline_output = row.get("pipeline_output_json")

                _jobs[job_id] = {
                    "status":          status,
                    "progress":        {"step": row.get("progress_step") or "Restored", "pct": row.get("progress_pct") or 0},
                    "count":           row.get("variant_count"),
                    "results":         pipeline_output,
                    "partial_results": [],
                    "error":           error,
                    "filename":        row.get("filename", ""),
                    "file_size":       row.get("file_size_bytes", 0),
                    "created_at":      created_at,
                    "started_at":      started_at,
                    "finished_at":     finished_at,
                    "created_by_user_id": row.get("created_by_user_id"),
                }
                restored += 1

        log.info("loaded %d jobs from Postgres", restored)
    except Exception:
        log.exception("failed to load jobs from Postgres — starting with empty job store")


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
        # Insert per-variant rows into results table (outside lock — can be slow)
        _pg_insert_results(job_id, variants)
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

    except Exception:
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
        cutoff = datetime.now(UTC) - timedelta(hours=JOB_TTL_HOURS)
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
    # Every new job must have a real owner so ownership guards on the
    # jobs endpoints can work — dev-bypass supplies a stable dev user
    # locally; in prod a missing/invalid bearer now 401s here instead
    # of silently creating an orphaned (NULL-owner) job.
    user: User = Depends(required_user),
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

    # ── Size guard (before job is created) ───────────────────────────────────
    # Read at most max_bytes + 1 so an oversized upload is rejected without
    # materialising the whole (potentially multi-GB) body into RAM. The gateway
    # should also enforce an ingress request-body limit (defense-in-depth).
    max_bytes  = MAX_UPLOAD_MB * 1024 * 1024
    file_bytes = await file.read(max_bytes + 1)
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
            # NULL in dev (no Authentik headers); the Authentik subject id
            # in prod. Stamped once at job creation and not touched on
            # subsequent _persist_jobs_locked() updates.
            "created_by_user_id": user.id,
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

    # Do NOT log the raw filename — genome upload names frequently embed patient
    # names/MRNs (PHI). Log the extension only, for format debugging.
    _ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else "(none)"
    log.info("job=%s queued ext=%s size=%d bytes", job_id, _ext, len(file_bytes))

    return JSONResponse(
        status_code=202,
        content={
            "job_id":   job_id,
            "status":   "pending",
            "poll_url": f"/jobs/{job_id}",
        },
    )


@app.get("/jobs/{job_id}")
def get_job(job_id: str, include_results: bool = True,
            user: User = Depends(required_user)):
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
        # Same 404 body as guard_owner's for both "doesn't exist" and
        # "exists but isn't yours" — a non-owner must not be able to
        # distinguish the two by inspecting the response.
        if job is None:
            raise HTTPException(status_code=404, detail="not found")
        guard_owner(job.get("created_by_user_id"), user)
        response = _public_job(job_id, job, include_results=include_results)

    return response


@app.get("/jobs")
def list_jobs(limit: int = 20, user: User = Depends(required_user)):
    """
    List recent jobs owned by the caller (status only — no results
    payload). Useful for ops dashboards. Returns newest first.
    """
    with _jobs_lock:
        snapshot = sorted(
            [
                _public_job(jid, j, include_results=False)
                for jid, j in _jobs.items()
                if owns(j.get("created_by_user_id"), user)
            ],
            key=lambda x: x.get("created_at", ""),
            reverse=True,
        )
    return {"jobs": snapshot[:limit]}


@app.get("/jobs/{job_id}/dossier/{peptide_name}", response_class=HTMLResponse)
def get_dossier(job_id: str, peptide_name: str,
                 user: User = Depends(required_user)):
    """
    Return the pre-rendered HTML dossier for a specific peptide therapy.
    """
    with _jobs_lock:
        job = _jobs.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="not found")
    guard_owner(job.get("created_by_user_id"), user)

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
def get_pgx(job_id: str, user: User = Depends(required_user)):
    """Return the full pharmacogenomics profile for a completed job."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="not found")
    guard_owner(job.get("created_by_user_id"), user)
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="Job not yet complete")
    pgx = (job.get("results") or {}).get("pgx_profile")
    if not pgx:
        raise HTTPException(status_code=404, detail="No PGx profile for this job")
    return pgx


@app.get("/jobs/{job_id}/drug/{drug}")
def get_drug(job_id: str, drug: str, user: User = Depends(required_user)):
    """
    Return per-drug PGx evidence for a specific drug: CPIC recommendations,
    matching star-allele phenotypes, contributing PRS, and the conformal
    prediction set from the HGNN/rule-based ranker.
    """
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="not found")
    guard_owner(job.get("created_by_user_id"), user)
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
def acmg_signoff(job_id: str, variant_id: str, req: AcmgSignoffRequest,
                  user: User = Depends(required_user)):
    """
    Record a qualified reviewer's sign-out of a variant's automated ACMG/AMP
    classification (approve the draft, or amend it). Updates and persists the
    job. Returns the updated `acmg` block.
    """
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="not found")
        guard_owner(job.get("created_by_user_id"), user)
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
            raise HTTPException(status_code=422, detail=str(exc)) from exc

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
