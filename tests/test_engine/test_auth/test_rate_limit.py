"""
Tests for engine/auth/rate_limit.RateLimiter.
"""
import time

from engine.auth.rate_limit import RateLimiter


def test_allows_attempts_up_to_max():
    rl = RateLimiter(max_attempts=3, window_seconds=60.0)
    for _ in range(3):
        assert rl.check("ip") is True
        rl.record("ip")
    assert rl.check("ip") is False


def test_per_key_isolation():
    """One IP burning through its budget should not affect another."""
    rl = RateLimiter(max_attempts=2, window_seconds=60.0)
    for _ in range(2):
        rl.record("alice")
    assert rl.check("alice") is False
    assert rl.check("bob") is True


def test_window_expiry_restores_budget():
    """After the window elapses, prior attempts no longer count."""
    rl = RateLimiter(max_attempts=2, window_seconds=0.05)
    for _ in range(2):
        rl.record("ip")
    assert rl.check("ip") is False
    time.sleep(0.07)
    assert rl.check("ip") is True


def test_retry_after_reports_time_until_oldest_falls_out():
    rl = RateLimiter(max_attempts=1, window_seconds=1.0)
    rl.record("ip")
    delay = rl.retry_after_seconds("ip")
    # Should be very close to 1 second — newly recorded attempt has the
    # full window to wait out.
    assert 0.5 < delay <= 1.0


def test_retry_after_zero_when_budget_available():
    rl = RateLimiter(max_attempts=2, window_seconds=60.0)
    rl.record("ip")
    assert rl.retry_after_seconds("ip") == 0.0


def test_reset_drops_state():
    rl = RateLimiter(max_attempts=1, window_seconds=60.0)
    rl.record("ip")
    assert rl.check("ip") is False
    rl.reset("ip")
    assert rl.check("ip") is True


def test_reset_all_keys_when_no_key_given():
    rl = RateLimiter(max_attempts=1, window_seconds=60.0)
    rl.record("alice")
    rl.record("bob")
    rl.reset()
    assert rl.check("alice") is True
    assert rl.check("bob") is True
