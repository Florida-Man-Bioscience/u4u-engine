#!/usr/bin/env python3
"""
scripts/seed_tracking_data.py
=============================
CLI wrapper around engine.tracking.seed for the deploy-time entrypoint and
ad-hoc seeding from the dev shell. Same seed logic backs the UI's
POST /tracking/seed button.

Usage:
    nix develop --command python scripts/seed_tracking_data.py
    nix develop --command python scripts/seed_tracking_data.py --reset
    nix develop --command python scripts/seed_tracking_data.py --db /tmp/x.db --seed 7
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.tracking import db, get_conn  # noqa: E402
from engine.tracking.seed import seed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=None,
                        help="Path to tracking DB (default: data/biomarker_tracking.db)")
    parser.add_argument("--reset", action="store_true",
                        help="Delete the DB file before seeding (recreates schema).")
    parser.add_argument("--seed", type=int, default=42,
                        help="RNG seed for reproducible data.")
    parser.add_argument("--patients", type=int, default=12,
                        help="Number of patients to create (default 12).")
    parser.add_argument("--force", action="store_true",
                        help="Wipe existing patients (FK cascade) and reseed.")
    parser.add_argument("--rich", action="store_true",
                        help="Denser series: more treatments, more markers, "
                             "interpolated sample weeks. For diagnostics.")
    args = parser.parse_args()

    target = Path(args.db or os.getenv("TRACKING_DB_PATH")
                  or "data/biomarker_tracking.db")

    if args.reset and target.exists():
        target.unlink()
        for suffix in ("-shm", "-wal"):
            sidecar = target.with_name(target.name + suffix)
            if sidecar.exists():
                sidecar.unlink()
        print(f"removed existing {target}")

    db.reset_initialized()
    with get_conn(str(target)) as conn:
        stats = seed(conn, rng=random.Random(args.seed),
                     n_patients=args.patients, force=args.force, rich=args.rich)

    if stats["skipped"]:
        print(f"tracking DB already has {stats['skipped']} patient(s) — "
              f"skipping seed ({target}). Pass --force to override.")
    else:
        print(f"seeded {stats['patients']} patients, "
              f"{stats['treatments']} treatments, "
              f"{stats['measurements']} measurements → {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
