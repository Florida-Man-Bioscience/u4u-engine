import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from engine.users import token_validator as tv
from engine.users.oidc import OidcSettings

_SETTINGS = OidcSettings(
    issuer="https://id.example/app",
    audience="u4u-web",
    jwks_url="https://id.example/app/jwks",
)


@pytest.fixture
def keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key


def _make_token(key, *, iss=_SETTINGS.issuer, aud=_SETTINGS.audience,
                exp_delta=3600, sub="user-123", extra=None, kid="k1"):
    # Real relative time, not a fixed future epoch: PyJWT 2.12.x validates
    # exp/iat against `datetime.now(tz=timezone.utc)`, not `time.time()`, so
    # tokens must be genuinely valid/expired relative to the real wall clock.
    now = int(time.time())
    payload = {"iss": iss, "aud": aud, "sub": sub,
               "iat": now, "exp": now + exp_delta}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": kid})


def _install_fake_jwks(monkeypatch, key, kid="k1"):
    """Bypass network: feed the validator the public key directly.

    Patches the module-level `_signing_key_for(token, jwks_url)` seam with a
    plain function matching its real two-argument signature (no network,
    no PyJWKClient involved) — real RS256 signature/claims verification
    still happens in `jwt.decode` inside `validate_token`.
    """
    pub = key.public_key()

    class _FakeSigningKey:
        def __init__(self, k):
            self.key = k

    def _fake_signing_key_for(token, jwks_url):
        return _FakeSigningKey(pub)

    monkeypatch.setattr(tv, "_signing_key_for", _fake_signing_key_for, raising=True)


def test_valid_token_returns_claims(monkeypatch, keypair):
    _install_fake_jwks(monkeypatch, keypair)
    token = _make_token(keypair, extra={"email": "a@b.co", "name": "A B"})
    claims = tv.validate_token(token, _SETTINGS)
    assert claims["sub"] == "user-123"
    assert claims["email"] == "a@b.co"


def test_expired_token_rejected(monkeypatch, keypair):
    _install_fake_jwks(monkeypatch, keypair)
    token = _make_token(keypair, exp_delta=-10)
    with pytest.raises(tv.TokenError):
        tv.validate_token(token, _SETTINGS)


def test_wrong_issuer_rejected(monkeypatch, keypair):
    _install_fake_jwks(monkeypatch, keypair)
    token = _make_token(keypair, iss="https://evil.example")
    with pytest.raises(tv.TokenError):
        tv.validate_token(token, _SETTINGS)


def test_wrong_audience_rejected(monkeypatch, keypair):
    _install_fake_jwks(monkeypatch, keypair)
    token = _make_token(keypair, aud="some-other-client")
    with pytest.raises(tv.TokenError):
        tv.validate_token(token, _SETTINGS)


def test_bad_signature_rejected(monkeypatch, keypair):
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _install_fake_jwks(monkeypatch, keypair)  # validator trusts keypair's pubkey
    token = _make_token(other)                # but token signed by a different key
    with pytest.raises(tv.TokenError):
        tv.validate_token(token, _SETTINGS)


def test_jwks_unavailable_fails_closed(monkeypatch, keypair):
    """JWKS fetch failure must surface as JwksUnavailable (-> 503), not be
    swallowed into TokenError (-> 401) or fail open."""
    def _raise_unavailable(token, jwks_url):
        raise tv.JwksUnavailable("jwks endpoint unreachable")

    monkeypatch.setattr(tv, "_signing_key_for", _raise_unavailable, raising=True)
    token = _make_token(keypair)
    with pytest.raises(tv.JwksUnavailable):
        tv.validate_token(token, _SETTINGS)


def test_malformed_token_rejected(monkeypatch, keypair):
    """A garbage Authorization value must surface as TokenError (-> 401),
    not an unhandled jwt.exceptions.DecodeError (-> 500).

    A malformed token fails during unverified-header decoding inside
    PyJWKClient.get_signing_key_from_jwt itself (before any real JWKS
    lookup would matter), so this genuinely exercises the malformed-input
    path through the real `_signing_key_for` -> `_client_for` machinery —
    it does NOT install the fake-JWKS monkeypatch, since that would bypass
    the exact code path under test. No network call happens because the
    decode error is raised before any HTTP request would be made.
    """
    with pytest.raises(tv.TokenError):
        tv.validate_token("not-a-jwt-at-all", _SETTINGS)


def test_real_jwks_client_error_converted(monkeypatch, keypair):
    """Exercise the actual `except jwt.PyJWKClientError` conversion line in
    `_signing_key_for` (the existing fail-closed test bypasses it entirely
    by monkeypatching `_signing_key_for` itself). Stub out `_client_for` so
    no network call happens, but let `_signing_key_for`'s own try/except
    run for real."""
    class _StubClient:
        def get_signing_key_from_jwt(self, token):
            raise jwt.PyJWKClientError("jwks endpoint unreachable")

    monkeypatch.setattr(tv, "_client_for", lambda jwks_url: _StubClient(), raising=True)
    token = _make_token(keypair)
    with pytest.raises(tv.JwksUnavailable):
        tv.validate_token(token, _SETTINGS)
