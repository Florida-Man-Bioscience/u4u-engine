"""
engine/healthkit — HealthKit ingestion.

Receives batches of Apple HealthKit samples from the peptodyssey iOS app and
stores them in the de-identified healthkit_* tables (Postgres in prod, SQLite in
dev/tests). See docs/healthkit-storage.md for the design.
"""
