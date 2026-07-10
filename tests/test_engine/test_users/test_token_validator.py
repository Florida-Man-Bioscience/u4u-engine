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
