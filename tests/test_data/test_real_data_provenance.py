from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.refresh_pgs_catalog import ManifestError, load_manifest, validate_manifest

ROOT = Path(__file__).parents[2]


def test_landed_nhanes_artifacts_match_manifest() -> None:
    source = (ROOT / "data/g2p/sources.yaml").read_text(encoding="utf-8")
    assert "status: landed" in source
    raw = ROOT / "data/g2p/nhanes_iii_ssigf.xpt"
    normalized = ROOT / "data/g2p/nhanes_iii_igf_axis.csv"
    assert raw.exists()
    assert normalized.exists()

    digest = hashlib.sha256(raw.read_bytes()).hexdigest()
    assert digest == "10253a32092809529ed73646000ac303550dfcdb5be9843263104d3c87679912"


def test_pgs_manifest_stays_closed_until_ids_are_verified() -> None:
    manifest = load_manifest(ROOT / "data/pgs/manifest.yaml")
    assert manifest["status"] == "pending_verified_score_ids"
    assert validate_manifest(manifest) == []


def test_pgs_manifest_rejects_unapproved_or_unchecksummed_records() -> None:
    record = {
        "id": "PGS999999",
        "trait": "BMI",
        "url": "https://example.invalid/score.txt.gz",
        "sha256": "0" * 64,
        "path": "data/pgs/PGS999999.txt.gz",
        "status": "candidate_source",
    }
    with pytest.raises(ManifestError, match="only approved"):
        validate_manifest({"scores": [record]})

    record["status"] = "approved"
    record["sha256"] = "unverified"
    with pytest.raises(ManifestError, match="verified SHA-256"):
        validate_manifest({"scores": [record]})
