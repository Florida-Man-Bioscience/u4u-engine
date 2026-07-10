"""
Tests for the baseline security-hardening tier.

Covers the identity-independent hardening: the decompression-bomb variant cap in
the VCF parser, the /tracking/seed force-wipe production guard, and the baseline
security response headers. (The access-control core — auth + ownership scoping —
is a separate, infra-coordinated change; see docs/security-hardening.md.)
"""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

# ── Decompression-bomb / variant cap ─────────────────────────────────────────

def test_vcf_parser_rejects_more_than_max_variants(monkeypatch):
    pysam = pytest.importorskip("pysam")  # noqa: F841
    from engine import parsers

    vcf = (
        b"##fileformat=VCFv4.2\n"
        b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
        b"1\t100\t.\tA\tG\t.\t.\t.\n"
        b"1\t200\t.\tC\tT\t.\t.\t.\n"
        b"1\t300\t.\tG\tA\t.\t.\t.\n"
    )

    # Cap below the record count → the bomb guard fires and aborts the parse.
    monkeypatch.setattr(parsers, "MAX_VARIANTS", 1)
    with pytest.raises(parsers.TooManyVariantsError):
        parsers._parse_vcf_bytes(vcf, "sample.vcf")

    # A generous cap parses the same file fine (guard doesn't false-positive).
    monkeypatch.setattr(parsers, "MAX_VARIANTS", 1_000_000)
    variants = parsers._parse_vcf_bytes(vcf, "sample.vcf")
    assert len(variants) == 3


# ── /tracking/seed force-wipe production guard ───────────────────────────────

@pytest.fixture
def client(tmp_path, monkeypatch):
    from engine.tracking import db
    monkeypatch.setattr(db, "_DEFAULT_PATH", tmp_path / "tracking.db")
    monkeypatch.setattr(db, "_is_postgres_configured", lambda path: False)
    db.reset_initialized()
    from api import app
    with TestClient(app) as c:
        yield c


def test_seed_force_allowed_on_sqlite(client):
    # Dev/SQLite: force-reseed stays allowed (unchanged behaviour).
    assert client.post("/tracking/seed", json={"patients": 2}).status_code == 200
    r = client.post("/tracking/seed", json={"patients": 3, "force": True})
    assert r.status_code == 200, r.text


def test_seed_force_refused_on_postgres(client, monkeypatch):
    # Simulate a Postgres-backed tracking store: the connection reports _is_pg.
    from engine.tracking import api as tapi

    class _PGConn:
        _is_pg = True

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(tapi, "get_conn", lambda *a, **k: _PGConn())
    r = client.post("/tracking/seed", json={"patients": 3, "force": True})
    assert r.status_code == 403
    assert "force-wipe" in r.json()["detail"].lower()


# ── Baseline security headers ────────────────────────────────────────────────

def test_security_headers_present(client):
    r = client.get("/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "no-referrer"
    assert "max-age=" in r.headers.get("Strict-Transport-Security", "")
