"""Tests for ACMG sign-out domain logic and the API endpoint."""
import pytest

from engine.acmg import apply_signoff, classify_acmg


def _acmg():
    return classify_acmg({"genes": ["X"], "consequence": "missense_variant",
                          "gnomad_af": 0.3})  # → Benign (BA1)


def test_approve_keeps_automated_classification():
    a = _acmg()
    out = apply_signoff(a, reviewer="Dr. A", action="approve")
    assert out["status"] == "signed_off"
    assert out["requires_human_review"] is False
    assert out["final_classification"] == a["classification"]
    assert out["sign_out"]["reviewer"] == "Dr. A"
    assert out["sign_out"]["signed_at"]


def test_amend_overrides_classification():
    out = apply_signoff(_acmg(), reviewer="Dr. B", action="amend",
                        final_classification="Likely benign", notes="freq context")
    assert out["final_classification"] == "Likely benign"
    assert out["sign_out"]["action"] == "amend"
    assert out["sign_out"]["notes"] == "freq context"


def test_requires_reviewer():
    with pytest.raises(ValueError):
        apply_signoff(_acmg(), reviewer="", action="approve")


def test_invalid_action():
    with pytest.raises(ValueError):
        apply_signoff(_acmg(), reviewer="X", action="bogus")


def test_amend_requires_valid_classification():
    with pytest.raises(ValueError):
        apply_signoff(_acmg(), reviewer="X", action="amend",
                      final_classification="Definitely Bad")
    with pytest.raises(ValueError):
        apply_signoff(_acmg(), reviewer="X", action="amend")  # missing


# ── API endpoint ────────────────────────────────────────────────────────────

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402
import api  # noqa: E402


def _seed_job_with_variant():
    job_id = "test-job-acmg"
    variant = {"variant_id": "rs999", "rsid": "rs999",
               "acmg": classify_acmg({"genes": ["X"], "consequence": "missense_variant",
                                      "gnomad_af": 0.3})}
    with api._jobs_lock:
        api._jobs[job_id] = {
            "status": "done", "results": {"variants": [variant]},
            "progress": {"step": "Complete", "pct": 100},
        }
    return job_id


def test_signoff_endpoint_approves():
    job_id = _seed_job_with_variant()
    try:
        with TestClient(api.app) as c:
            r = c.post(f"/jobs/{job_id}/variants/rs999/acmg-signoff",
                       json={"reviewer": "Dr. C", "action": "approve"})
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["status"] == "signed_off"
            assert body["sign_out"]["reviewer"] == "Dr. C"
    finally:
        with api._jobs_lock:
            api._jobs.pop(job_id, None)


def test_signoff_endpoint_unknown_variant():
    job_id = _seed_job_with_variant()
    try:
        with TestClient(api.app) as c:
            r = c.post(f"/jobs/{job_id}/variants/nope/acmg-signoff",
                       json={"reviewer": "Dr. C", "action": "approve"})
            assert r.status_code == 404
    finally:
        with api._jobs_lock:
            api._jobs.pop(job_id, None)
