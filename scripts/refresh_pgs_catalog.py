#!/usr/bin/env python3
"""Download explicitly approved PGS Catalog scoring files.

This script is intentionally conservative: it never searches for, selects, or
activates a score on its own. The manifest must contain a verified PGS ID,
trait, source URL, and checksum before a file is downloaded.

The downloaded files are evidence inputs/trait-context assets only. They are
not drug-response predictors and are not wired into the PeptOdyssey model by
this script.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys
import urllib.error
import urllib.request


class ManifestError(ValueError):
    """Raised when a PGS manifest is incomplete or unsafe."""


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: pathlib.Path) -> dict:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - exercised by deployment
        raise ManifestError("PyYAML is required to read the PGS manifest") from exc
    with path.open(encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle)
    if not isinstance(manifest, dict):
        raise ManifestError("manifest root must be a mapping")
    return manifest


def validate_manifest(manifest: dict) -> list[dict]:
    records = manifest.get("scores")
    if not isinstance(records, list):
        raise ManifestError("manifest must contain a scores list")
    for record in records:
        required = {"id", "trait", "url", "sha256", "path", "status"}
        missing = required - set(record)
        if missing:
            raise ManifestError(f"score record missing {sorted(missing)}")
        if not record["id"].startswith("PGS"):
            raise ManifestError(f"invalid PGS id: {record['id']}")
        if record["status"] != "approved":
            raise ManifestError(
                f"{record['id']} is {record['status']!r}; only approved records download"
            )
        if len(record["sha256"]) != 64 or any(
            char not in "0123456789abcdef" for char in record["sha256"].lower()
        ):
            raise ManifestError(f"{record['id']} needs a verified SHA-256 checksum")
    return records


def download_record(record: dict, root: pathlib.Path) -> pathlib.Path:
    destination = root / record["path"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        record["url"], headers={"User-Agent": "u4u-engine/real-data-fetcher"}
    )
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as out:
        while chunk := response.read(1024 * 1024):
            out.write(chunk)
    actual = sha256(destination)
    if actual.lower() != record["sha256"].lower():
        destination.unlink(missing_ok=True)
        raise ManifestError(
            f"{record['id']} checksum mismatch: expected {record['sha256']}, got {actual}"
        )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=pathlib.Path("data/pgs/manifest.yaml"))
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        records = validate_manifest(load_manifest(args.repo_root / args.manifest))
        for record in records:
            destination = args.repo_root / record["path"]
            if args.dry_run:
                print(f"APPROVED {record['id']} {record['trait']} -> {destination}")
            else:
                print(f"DOWNLOADING {record['id']} {record['trait']}")
                print(download_record(record, args.repo_root))
    except (OSError, ManifestError, urllib.error.URLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
