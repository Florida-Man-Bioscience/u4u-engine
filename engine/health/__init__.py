"""
engine/health — HealthKit ingestion.

Receives batches of HealthKit samples from the peptodyssey iOS app and stores
them in Postgres, keyed to a user via a long-lived per-device bearer token.

Optional feature: only active when DATABASE_URL is set. With no DATABASE_URL the
ingestion endpoints return 503 and the rest of the engine runs unaffected.
"""
