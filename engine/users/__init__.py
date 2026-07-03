"""
engine/users — app user accounts (operators of the engine).

Mirrors the engine/tracking module layout: schema.sql for SQLite dev,
db.get_conn() picks Postgres or SQLite, service.py is the data layer,
api.py exposes a FastAPI router.

Users are populated from the Authentik forward-auth proxy's headers
(see ``engine/users/service.upsert_from_headers``). The api never sees
a password.
"""
from .db import get_conn  # re-exported for convenience
