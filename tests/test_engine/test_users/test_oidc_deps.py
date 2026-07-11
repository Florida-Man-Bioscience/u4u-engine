"""Guard: the JWT/JWKS validation stack must be importable."""


def test_jwt_and_crypto_importable():
    import jwt  # PyJWT
    from cryptography.hazmat.primitives.asymmetric import rsa

    assert hasattr(jwt, "decode")
    assert hasattr(rsa, "generate_private_key")
