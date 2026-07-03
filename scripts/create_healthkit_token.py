#!/usr/bin/env python3
"""
scripts/create_healthkit_token.py
=================================
Mint an interim device bearer token for the peptodyssey HealthKit endpoint.

Stores only the token's SHA-256 hash and prints the raw token ONCE — paste it
into the app's Backend settings (sent as `Authorization: Bearer <token>`).

Usage (against the configured DB — set DATABASE_URL for Postgres, else SQLite):
    python scripts/create_healthkit_token.py --label "Curtis iPhone"
    python scripts/create_healthkit_token.py --label "Curtis iPhone" --subject subj-abc123

--subject binds the token to a single subject_id (it may then write only that
subject); omit it for a token that may write any subject_id.
"""
from __future__ import annotations

import argparse
import secrets

from engine.healthkit.auth import hash_token
from engine.healthkit.db import get_conn


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a peptodyssey HealthKit device token.")
    parser.add_argument("--label", default=None, help="human note, e.g. 'Curtis iPhone'")
    parser.add_argument("--subject", default=None, help="bind to this subject_id (optional)")
    args = parser.parse_args()

    raw = "pep_hk_" + secrets.token_urlsafe(32)
    with get_conn() as conn:
        ph = "%s" if getattr(conn, "_is_pg", False) else "?"
        conn.execute(
            f"INSERT INTO healthkit_device_tokens (token_hash, label, subject_id) "
            f"VALUES ({ph},{ph},{ph})",
            (hash_token(raw), args.label, args.subject),
        )
        conn.commit()

    print("\nHealthKit device token (store now — it is not recoverable):\n")
    print(f"    {raw}\n")
    if args.subject:
        print(f"Bound to subject_id: {args.subject}\n")


if __name__ == "__main__":
    main()
