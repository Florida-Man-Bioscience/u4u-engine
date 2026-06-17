"""
Postgres smoke tests for the dual-mode persistence layer.

Off by default — opt in with ``PG_TESTS=1``. When enabled, boots an
ephemeral Postgres instance with ``initdb`` + ``pg_ctl``, runs the
migration suite, and exercises the key write/read paths against a real
Postgres. Designed to surface SQL-dialect drift between the SQLite and
Postgres branches before it reaches production — the default suite only
ever runs SQLite.

Requires ``initdb``, ``pg_ctl``, and ``psycopg2`` on PATH (already
present in the Nix devShell).
"""

from __future__ import annotations

import os
import subprocess
import time

import psycopg2
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("PG_TESTS"),
    reason="Postgres smoke tests are opt-in; set PG_TESTS=1 to enable.",
)


def _wait_for_pg(socket_dir, timeout_s: float = 10.0) -> None:
    deadline = time.time() + timeout_s
    last_exc: Exception | None = None
    while time.time() < deadline:
        try:
            conn = psycopg2.connect(f"postgresql:///postgres?host={socket_dir}")
            conn.close()
            return
        except psycopg2.OperationalError as exc:
            last_exc = exc
            time.sleep(0.2)
    raise RuntimeError(
        f"Postgres did not start within {timeout_s}s: {last_exc}"
    )


@pytest.fixture(scope="session")
def pg_database(tmp_path_factory):
    """Boot a unix-socket-only Postgres, run migrations, yield the DSN."""
    tmp = tmp_path_factory.mktemp("pg")
    datadir = tmp / "data"
    sockdir = tmp / "sock"
    sockdir.mkdir()
    logfile = tmp / "pg.log"

    subprocess.run(
        ["initdb", "-D", str(datadir), "-A", "trust", "-E", "UTF8", "--no-locale"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "pg_ctl", "-D", str(datadir), "-l", str(logfile),
            # Socket only — no TCP. Avoids port conflicts in CI / shared envs.
            "-o", f"-h '' -k {sockdir}",
            "start",
        ],
        check=True,
        capture_output=True,
    )

    try:
        _wait_for_pg(sockdir)

        bootstrap = psycopg2.connect(f"postgresql:///postgres?host={sockdir}")
        bootstrap.autocommit = True
        with bootstrap.cursor() as cur:
            cur.execute("CREATE DATABASE u4u_test")
        bootstrap.close()

        dsn = f"postgresql:///u4u_test?host={sockdir}"

        # db.pool reads DATABASE_URL once at import time and caches a
        # connection pool. If anything else already imported it during
        # collection, the constant is stale and the pool is None for the
        # wrong URL — rebind both.
        os.environ["DATABASE_URL"] = dsn
        import db.pool as pool_mod
        pool_mod.DATABASE_URL = dsn
        pool_mod._pool = None

        from db.migrate import run_migrations
        run_migrations(dsn)

        yield dsn
    finally:
        subprocess.run(
            ["pg_ctl", "-D", str(datadir), "-m", "fast", "stop"],
            capture_output=True,
        )


@pytest.fixture
def pg_clean(pg_database):
    """Truncate all writable tables between tests; keep schema_migrations."""
    yield
    with psycopg2.connect(pg_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename != 'schema_migrations'
                """
            )
            tables = [r[0] for r in cur.fetchall()]
            if tables:
                cur.execute(
                    f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"
                )
        conn.commit()


# ── Migration layer ──────────────────────────────────────────────────────────


def test_migrations_recorded(pg_database):
    with psycopg2.connect(pg_database) as conn, conn.cursor() as cur:
        cur.execute("SELECT filename FROM schema_migrations ORDER BY filename")
        applied = [r[0] for r in cur.fetchall()]
    assert "001_initial_schema.sql" in applied
    assert "002_caches_and_tracking.sql" in applied


def test_migrations_idempotent(pg_database):
    """Re-running the migrations on an already-migrated DB is a no-op."""
    from db.migrate import run_migrations
    run_migrations(pg_database)
    run_migrations(pg_database)


# ── Annotation cache ─────────────────────────────────────────────────────────


def test_annotation_cache_roundtrip(pg_database, pg_clean):
    """Put then get returns the original payload via the Postgres path."""
    from engine.annotators.cache import MISS, AnnotationCache

    cache = AnnotationCache()
    assert cache._use_pg is True, "expected Postgres mode under DATABASE_URL"

    payload = {"clinvar_id": "12345", "significance": "pathogenic", "n": 3}
    cache.put("clinvar", "rs123", payload)

    assert cache.get("clinvar", "rs123") == payload
    assert cache.get("clinvar", "rs_not_there") is MISS


def test_annotation_cache_preserves_none(pg_database, pg_clean):
    """None must round-trip as a hit (negative-result caching)."""
    from engine.annotators.cache import MISS, AnnotationCache

    cache = AnnotationCache()
    cache.put("clinvar", "rs_no_data", None)
    assert cache.get("clinvar", "rs_no_data") is None
    assert cache.get("clinvar", "rs_other") is MISS


# ── Tracking domain ──────────────────────────────────────────────────────────


def test_tracking_patient_treatment_measurement_flow(pg_database, pg_clean):
    """End-to-end: create patient, treatment, measurement, list it back."""
    from engine.tracking import db as tracking_db
    from engine.tracking import service

    with tracking_db.get_conn() as conn:
        assert getattr(conn, "_is_pg", False) is True, "expected Postgres conn"

        patient = service.create_patient(
            conn, label="P-PG-001", sex="F", birth_year=1990
        )
        assert patient.label == "P-PG-001"

        treatment = service.create_treatment(
            conn,
            patient_id=patient.id,
            peptide_name="bpc-157",
            start_date="2026-01-01",
            dose=250.0,
            dose_unit="mcg",
        )
        assert treatment.peptide_name == "bpc-157"

        m = service.create_measurement(
            conn,
            patient_id=patient.id,
            biomarker_name="CRP",
            value=3.5,
            measured_at="2026-02-01T10:00:00",
            unit="mg/L",
            treatment_id=treatment.id,
        )
        assert m.value == 3.5
        assert m.treatment_id == treatment.id

        rows = service.list_measurements_for_patient(conn, patient.id)
        assert len(rows) == 1
        assert rows[0].id == m.id
        assert rows[0].biomarker_name == "CRP"


# ── Phase 1 ownership wiring ─────────────────────────────────────────────────


def _seed_user(pg_database) -> str:
    """Insert a user directly via psycopg2 and return its id.

    The smoke fixture doesn't carry a request, so this stands in for
    upsert_from_headers. Returns the row id so callers can verify FK
    propagation.
    """
    with psycopg2.connect(pg_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (authentik_uid, username)
                VALUES (%s, %s)
                RETURNING id::text
                """,
                ("ak-smoke-001", "smoketester"),
            )
            user_id = cur.fetchone()[0]
        conn.commit()
    return user_id


def test_tracking_created_by_persisted(pg_database, pg_clean):
    """create_patient / create_treatment / create_measurement must
    propagate the user id to the row so ownership survives a SELECT."""
    from engine.tracking import db as tracking_db
    from engine.tracking import service

    user_id = _seed_user(pg_database)

    with tracking_db.get_conn() as conn:
        patient = service.create_patient(
            conn, label="P-OWN-001", created_by_user_id=user_id
        )
        treatment = service.create_treatment(
            conn,
            patient_id=patient.id,
            peptide_name="bpc-157",
            start_date="2026-01-01",
            created_by_user_id=user_id,
        )
        measurement = service.create_measurement(
            conn,
            patient_id=patient.id,
            biomarker_name="CRP",
            value=3.5,
            measured_at="2026-02-01T10:00:00",
            treatment_id=treatment.id,
            created_by_user_id=user_id,
        )

    # Re-SELECT directly so we're verifying the column landed in PG, not
    # the dataclass round-trip.
    with psycopg2.connect(pg_database) as raw, raw.cursor() as cur:
        cur.execute(
            "SELECT created_by_user_id::text FROM patients WHERE id = %s",
            (patient.id,),
        )
        assert cur.fetchone()[0] == user_id
        cur.execute(
            "SELECT created_by_user_id::text FROM treatments WHERE id = %s",
            (treatment.id,),
        )
        assert cur.fetchone()[0] == user_id
        cur.execute(
            "SELECT created_by_user_id::text FROM measurements WHERE id = %s",
            (measurement.id,),
        )
        assert cur.fetchone()[0] == user_id


def test_jobs_created_by_persisted(pg_database, pg_clean, monkeypatch):
    """_persist_jobs_locked must stamp created_by_user_id on the jobs
    row when the in-memory dict carries it. We seed a fake job in the
    api._jobs dict (rather than running the real pipeline) so the test
    stays tight on the SQL path."""
    import api

    user_id = _seed_user(pg_database)

    job_id = "00000000-0000-0000-0000-000000000abc"
    monkeypatch.setattr(api, "_DB_URL", pg_database)
    with api._jobs_lock:
        api._jobs.clear()
        api._jobs[job_id] = {
            "status": "pending",
            "progress": {"step": "Queued", "pct": 0},
            "count": None,
            "results": None,
            "partial_results": [],
            "error": None,
            "filename": "smoke.vcf",
            "file_size": 1,
            "created_at": "2026-06-15T12:00:00+00:00",
            "started_at": None,
            "finished_at": None,
            "created_by_user_id": user_id,
        }
        api._persist_jobs_locked()
        api._jobs.clear()

    with psycopg2.connect(pg_database) as raw, raw.cursor() as cur:
        cur.execute(
            "SELECT created_by_user_id::text FROM jobs WHERE id = %s::uuid",
            (job_id,),
        )
        row = cur.fetchone()
    assert row is not None, "job was not persisted"
    assert row[0] == user_id
