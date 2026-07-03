"""
engine/healthkit/service.py
==========================
Ingest + read for HealthKit samples. Database-agnostic (Postgres via db.pool,
SQLite fallback in dev/tests) using the same _ph()/_row() pattern as
engine/tracking/service.py. Idempotent: samples upsert-by-uuid with
ON CONFLICT DO NOTHING, so re-syncs and HKAnchoredObjectQuery replays are safe.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime

from .schemas import SampleIn


def _ph(conn) -> str:
    return "%s" if getattr(conn, "_is_pg", False) else "?"


def _json(conn, value):
    """Adapt a dict for a JSON/JSONB column across both backends."""
    if getattr(conn, "_is_pg", False):
        import psycopg2.extras
        return psycopg2.extras.Json(value or {})
    return json.dumps(value or {})


def _row(row) -> dict:
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    # JSON columns come back as text on SQLite; decode for a uniform response.
    for k in ("device", "metadata"):
        if isinstance(d.get(k), str):
            try:
                d[k] = json.loads(d[k])
            except (ValueError, TypeError):
                pass
    return d


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def ingest(
    conn,
    *,
    subject_id: str,
    samples: list[SampleIn],
    anchors: dict[str, str] | None = None,
    source_name: str | None = None,
    notes: str | None = None,
) -> tuple[int, int]:
    """Insert a batch of samples for a subject. Returns (received, inserted).

    `inserted` counts only genuinely new rows — re-sent samples (same uuid) are
    skipped via ON CONFLICT DO NOTHING.
    """
    ph = _ph(conn)

    # Ensure the (opaque) subject exists.
    conn.execute(
        f"INSERT INTO healthkit_subjects (id) VALUES ({ph}) "
        f"ON CONFLICT (id) DO NOTHING",
        (subject_id,),
    )

    inserted = 0
    for s in samples:
        cur = conn.execute(
            f"""INSERT INTO healthkit_samples
                  (sample_uuid, subject_id, sample_class, type_identifier, value, unit,
                   start_time, end_time, source_name, source_bundle_id, device, metadata)
                VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})
                ON CONFLICT (sample_uuid) DO NOTHING""",
            (
                str(s.uuid), subject_id, s.cls, s.type, s.value, s.unit,
                s.start.isoformat(), s.end.isoformat(),
                s.source.name if s.source else None,
                s.source.bundleId if s.source else None,
                _json(conn, s.device), _json(conn, s.metadata),
            ),
        )
        if cur.rowcount and cur.rowcount > 0:
            inserted += 1
            if s.cls == "workout" and s.workout is not None:
                w = s.workout
                conn.execute(
                    f"""INSERT INTO healthkit_workouts
                          (sample_uuid, activity_type, duration_s, total_energy_kcal, total_distance_m)
                        VALUES ({ph},{ph},{ph},{ph},{ph})
                        ON CONFLICT (sample_uuid) DO NOTHING""",
                    (str(s.uuid), w.activity_type, w.duration_s, w.total_energy_kcal, w.total_distance_m),
                )

    # Mirror the client's anchors, if provided.
    if anchors:
        now = _now_iso()
        for type_identifier, anchor in anchors.items():
            conn.execute(
                f"""INSERT INTO healthkit_sync_anchors (subject_id, type_identifier, anchor, updated_at)
                    VALUES ({ph},{ph},{ph},{ph})
                    ON CONFLICT (subject_id, type_identifier)
                    DO UPDATE SET anchor = excluded.anchor, updated_at = excluded.updated_at""",
                (subject_id, type_identifier, anchor, now),
            )

    # Audit row for the batch.
    conn.execute(
        f"""INSERT INTO healthkit_ingestions
              (subject_id, sample_count, inserted_count, source_name, notes)
            VALUES ({ph},{ph},{ph},{ph},{ph})""",
        (subject_id, len(samples), inserted, source_name, notes),
    )

    conn.commit()
    return len(samples), inserted


def read_samples(
    conn,
    *,
    subject_id: str,
    type_identifier: str | None = None,
    since: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    ph = _ph(conn)
    sql = f"SELECT * FROM healthkit_samples WHERE subject_id = {ph}"
    params: list = [subject_id]
    if type_identifier:
        sql += f" AND type_identifier = {ph}"
        params.append(type_identifier)
    if since:
        sql += f" AND start_time >= {ph}"
        params.append(since)
    sql += f" ORDER BY start_time DESC LIMIT {ph}"
    params.append(limit)

    rows = conn.execute(sql, tuple(params)).fetchall()
    return [_row(r) for r in rows]
