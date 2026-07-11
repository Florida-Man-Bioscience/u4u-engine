from engine.users import service

_ISS = "https://id.example/app"


def test_upsert_from_token_creates_then_updates(conn):
    u1 = service.upsert_from_token(
        conn, issuer=_ISS,
        claims={"sub": "abc", "email": "a@b.co", "name": "A B",
                "preferred_username": "ab"},
    )
    assert u1.issuer == _ISS
    assert u1.authentik_uid == "abc"
    assert u1.email == "a@b.co"
    assert u1.groups in (None, "")  # end-users get no staff groups

    u2 = service.upsert_from_token(
        conn, issuer=_ISS,
        claims={"sub": "abc", "email": "new@b.co", "name": "A B",
                "preferred_username": "ab"},
    )
    assert u2.id == u1.id           # same row (composite key)
    assert u2.email == "new@b.co"   # profile re-mirrored from token


def test_same_sub_different_issuer_is_distinct(conn):
    a = service.upsert_from_token(conn, issuer=_ISS, claims={"sub": "x"})
    b = service.upsert_from_token(conn, issuer="https://other/idp", claims={"sub": "x"})
    assert a.id != b.id
