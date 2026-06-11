"""
engine/auth/rate_limit.py
=========================
Tiny in-memory sliding-window rate limiter for /auth/login.

Why
---
Without a limit, a /auth/login endpoint is a free oracle for online
password attacks: bcrypt's work factor slows each attempt to ~50 ms, but
that's still 1200/min/IP — plenty fast for a six-character password
brute-force, or for spraying common credentials across many usernames.

Design
------
- Keyed by client IP. ``X-Forwarded-For`` is honoured when the request
  came through a trusted proxy (the Caddy in front of the API sets it).
- Sliding window: keep timestamps of recent attempts and count those
  within the window. O(failures) memory per IP; pruned opportunistically.
- Per-IP cap is generous enough that one mistyped password isn't a lockout
  (default 10 attempts per 5 minutes) but tight enough that brute-force
  is firmly out of reach.
- No persistence — a server restart resets state. Fine for this purpose:
  an attacker waiting out a restart is already throttled to one attempt
  every few seconds. Persistence would invite stuck-lockout bugs.

Not used elsewhere yet. If we ever rate-limit other endpoints, lift the
core into a generic helper.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Deque


class RateLimiter:
    """Sliding-window per-key counter. Thread-safe."""

    def __init__(self, *, max_attempts: int, window_seconds: float) -> None:
        if max_attempts <= 0 or window_seconds <= 0:
            raise ValueError("max_attempts and window_seconds must be positive")
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._attempts: dict[str, Deque[float]] = {}

    def _now(self) -> float:
        return time.monotonic()

    def _prune(self, dq: Deque[float], cutoff: float) -> None:
        while dq and dq[0] < cutoff:
            dq.popleft()

    def check(self, key: str) -> bool:
        """Return True if a new attempt is allowed for ``key``; False if
        the caller should be told 429. Does NOT record the attempt — call
        :meth:`record` after the protected work completes (so that we
        only count attempts the server actually processed).
        """
        with self._lock:
            dq = self._attempts.get(key)
            if dq is None:
                return True
            cutoff = self._now() - self.window_seconds
            self._prune(dq, cutoff)
            return len(dq) < self.max_attempts

    def record(self, key: str) -> None:
        """Record one attempt against ``key``. Call after every login
        attempt — both successful and failed — so a successful login from
        a brute-forcer doesn't reset the budget."""
        with self._lock:
            dq = self._attempts.setdefault(key, deque())
            cutoff = self._now() - self.window_seconds
            self._prune(dq, cutoff)
            dq.append(self._now())

    def retry_after_seconds(self, key: str) -> float:
        """How long until the oldest in-window attempt for ``key`` falls
        out of the window — i.e. when the caller will be allowed to try
        again. Returns 0 when there is currently budget available."""
        with self._lock:
            dq = self._attempts.get(key)
            if not dq:
                return 0.0
            cutoff = self._now() - self.window_seconds
            self._prune(dq, cutoff)
            if len(dq) < self.max_attempts:
                return 0.0
            return max(0.0, dq[0] + self.window_seconds - self._now())

    def reset(self, key: str | None = None) -> None:
        """Drop counters. Used by tests."""
        with self._lock:
            if key is None:
                self._attempts.clear()
            else:
                self._attempts.pop(key, None)


# Singleton used by engine/auth/api.py. Picked to allow ~10 mistakes per
# 5 minutes — much more permissive than the user will notice, much
# tighter than a brute-forcer needs.
login_limiter = RateLimiter(max_attempts=10, window_seconds=300.0)
