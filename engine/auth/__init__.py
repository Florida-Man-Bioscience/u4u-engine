"""
engine/auth
===========
Username/password authentication backed by an opaque session-token table.

Design
------
- Users have bcrypt-hashed passwords.
- Login exchanges (username, password) for a random 256-bit opaque token
  with an expiry. Subsequent requests carry the token as
  ``Authorization: Bearer <token>``.
- The middleware in ``api.py`` accepts either the existing ``API_KEYS``
  (kept as a service-to-service escape hatch) or a valid session token —
  API keys are checked first.
- A single admin user is bootstrapped from
  ``AUTH_BOOTSTRAP_USERNAME`` + ``AUTH_BOOTSTRAP_PASSWORD`` env vars on
  startup, only when the users table is empty. Subsequent changes to
  those env vars are ignored on purpose: rotating a deployed account by
  editing env would let anyone with deploy access silently take over.
"""

from .service import (  # noqa: F401
    AuthError,
    Session,
    User,
    authenticate,
    create_session,
    create_user,
    get_session_user,
    purge_expired_sessions,
    revoke_session,
)
