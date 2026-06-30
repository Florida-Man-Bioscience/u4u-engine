#!/usr/bin/env python3
"""
scripts/migrate_sqlite_to_postgres.py
=======================================
One-shot migration of live SQLite data into the Postgres database.

Run this ONCE while the old pod is still running (or from a copy of the
data/ directory) BEFORE deploying the new image with DATABASE_URL set.

Usage
-----
  # From inside the cluster (exec into the old pod):
  kubectl exec -it deploy/u4u-engine -- python scripts/migrate_sqlite_to_postgres.py

  # Or locally with a port-forward to Postgres:
  DATABASE_URL="postgresql://u4u:PASSWORD@localhost:5432/u4u" \
    python scripts/migrate_sqlite_to_postgres.py

The script is idempotent — rows that already exist in Postgres are skipped
(ON CONFLICT DO NOTHING). Safe to run multiple times.

Migrated databases
------------------
  data/biomarker_tracking.db   → patients, treatments, measurements, patient_genetics
  data/annotation_cache.db     → annotation_cache
  data/rsid_cache.db           → rsid_cache
"""

import os
import sqlite3
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    sys.exit("ERROR: DATABASE_URL must be set to the Postgres DSN")


def open_sqlite(path: Path):
    if not path.exists():
        print(f"  skipping {path} (not found)")
        return None
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def migrate_tracking(pg):
    sqlite_path = DATA_DIR / "biomarker_tracking.db"
    sq = open_sqlite(sqlite_path)
    if sq is None:
        return

    print(f"\n→ Migrating {sqlite_path}")

    # patients
    rows = sq.execute("SELECT * FROM patients").fetchall()
    print(f"  patients: {len(rows)} rows")
    with pg.cursor() as cur:
        for r in rows:
            d = dict(r)
            cur.execute(
                """
                INSERT INTO patients (id, label, sex, birth_year, notes, created_at)
                VALUES (%(id)s, %(label)s, %(sex)s, %(birth_year)s, %(notes)s, %(created_at)s)
                ON CONFLICT (id) DO NOTHING
                """,
                d,
            )
    pg.commit()

    # treatments
    rows = sq.execute("SELECT * FROM treatments").fetchall()
    print(f"  treatments: {len(rows)} rows")
    with pg.cursor() as cur:
        for r in rows:
            d = dict(r)
            cur.execute(
                """
                INSERT INTO treatments
                    (id, patient_id, peptide_name, dose, dose_unit, schedule,
                     route, start_date, end_date, notes, created_at)
                VALUES
                    (%(id)s, %(patient_id)s, %(peptide_name)s, %(dose)s,
                     %(dose_unit)s, %(schedule)s, %(route)s, %(start_date)s,
                     %(end_date)s, %(notes)s, %(created_at)s)
                ON CONFLICT (id) DO NOTHING
                """,
                d,
            )
    pg.commit()

    # measurements
    rows = sq.execute("SELECT * FROM measurements").fetchall()
    print(f"  measurements: {len(rows)} rows")
    with pg.cursor() as cur:
        for r in rows:
            d = dict(r)
            cur.execute(
                """
                INSERT INTO measurements
                    (id, patient_id, treatment_id, biomarker_name, modality,
                     value, unit, measured_at, notes, created_at)
                VALUES
                    (%(id)s, %(patient_id)s, %(treatment_id)s,
                     %(biomarker_name)s, %(modality)s, %(value)s, %(unit)s,
                     %(measured_at)s, %(notes)s, %(created_at)s)
                ON CONFLICT (id) DO NOTHING
                """,
                d,
            )
    pg.commit()

    # patient_genetics
    rows = sq.execute("SELECT * FROM patient_genetics").fetchall()
    print(f"  patient_genetics: {len(rows)} rows")
    with pg.cursor() as cur:
        for r in rows:
            d = dict(r)
            cur.execute(
                """
                INSERT INTO patient_genetics (patient_id, profile_json, source, created_at)
                VALUES (%(patient_id)s, %(profile_json)s, %(source)s, %(created_at)s)
                ON CONFLICT (patient_id) DO NOTHING
                """,
                d,
            )
    pg.commit()
    sq.close()


def migrate_annotation_cache(pg):
    sqlite_path = DATA_DIR / "annotation_cache.db"
    sq = open_sqlite(sqlite_path)
    if sq is None:
        return

    print(f"\n→ Migrating {sqlite_path}")
    rows = sq.execute("SELECT source, lookup_key, result_json FROM annotation_cache").fetchall()
    print(f"  annotation_cache: {len(rows)} rows")
    with pg.cursor() as cur:
        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO annotation_cache (source, lookup_key, result_json)
            VALUES (%s, %s, %s)
            ON CONFLICT (source, lookup_key) DO NOTHING
            """,
            [(r["source"], r["lookup_key"], r["result_json"]) for r in rows],
            page_size=500,
        )
    pg.commit()
    sq.close()


def migrate_rsid_cache(pg):
    sqlite_path = DATA_DIR / "rsid_cache.db"
    sq = open_sqlite(sqlite_path)
    if sq is None:
        return

    print(f"\n→ Migrating {sqlite_path}")
    rows = sq.execute("SELECT rsid, genotype, result_json FROM rsid_cache").fetchall()
    print(f"  rsid_cache: {len(rows)} rows")
    with pg.cursor() as cur:
        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO rsid_cache (rsid, genotype, result_json)
            VALUES (%s, %s, %s)
            ON CONFLICT (rsid, genotype) DO NOTHING
            """,
            [(r["rsid"], r["genotype"] or "", r["result_json"]) for r in rows],
            page_size=500,
        )
    pg.commit()
    sq.close()


def main():
    print(f"Connecting to Postgres: {DATABASE_URL.split('@')[-1]}")
    pg = psycopg2.connect(DATABASE_URL)
    pg.cursor_factory = psycopg2.extras.RealDictCursor

    try:
        migrate_tracking(pg)
        migrate_annotation_cache(pg)
        migrate_rsid_cache(pg)
        print("\n✓ Migration complete")
    finally:
        pg.close()


if __name__ == "__main__":
    main()
