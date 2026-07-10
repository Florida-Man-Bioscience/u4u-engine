from engine.users import service
from engine.users.models import User


def test_user_has_issuer_field():
    u = User(
        id="1", authentik_uid="sub-1", username="a", email=None,
        full_name=None, groups=None, issuer="https://id.example/app",
        created_at="t", last_seen_at="t", disabled_at=None,
    )
    assert u.issuer == "https://id.example/app"
    assert u.to_dict()["issuer"] == "https://id.example/app"


def test_get_user_by_issuer_sub_roundtrip(conn):
    created = service.upsert_from_headers(
        conn, {"X-Authentik-Uid": "sub-1", "X-Authentik-Username": "a"}
    )
    # upsert_from_headers stamps the cluster issuer (see Task 5 note); look it up
    found = service.get_user_by_issuer_sub(conn, created.issuer, "sub-1")
    assert found is not None
    assert found.id == created.id
    assert service.get_user_by_issuer_sub(conn, "other-iss", "sub-1") is None
