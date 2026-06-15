"""
db/migrate.py
=============
Runs all SQL migration files in order at application startup.

Migrations are numbered (001_, 002_, ...) and run in order. Each file is
wrapped in a transaction and is idempotent (IF NOT EXISTS guards throughout),
so re-running is safe. A `schema_migrations` table tracks which files have
already been applied.
"""

import logging
import os
from pathlib import Path

import psycopg2

log = logging.getLogger(__name__)

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def run_migrations(dsn: str) -> None:
    """Apply any pending migrations to the database at `dsn`."""
    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False

        # Bootstrap the migrations tracking table (not in a migration file
        # itself to avoid a chicken-and-egg problem).
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename   TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
        conn.commit()

        files = sorted(
            f for f in _MIGRATIONS_DIR.iterdir()
            if f.suffix == ".sql" and f.stem[0].isdigit()
        )

        for migration_file in files:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM schema_migrations WHERE filename = %s",
                    (migration_file.name,),
                )
                if cur.fetchone():
                    continue  # already applied

            log.info("Applying migration: %s", migration_file.name)
            sql = migration_file.read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(sql)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)",
                    (migration_file.name,),
                )
            conn.commit()
            log.info("Applied: %s", migration_file.name)

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
