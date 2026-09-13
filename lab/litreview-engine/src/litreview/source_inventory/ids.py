"""Source-inventory IDs. Location-stable; never row order."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def unit_id(source_id: str, revision_sha256: str, kind: str, locator: dict) -> str:
    payload = [source_id, revision_sha256, kind, locator]
    return "u:" + sha256_bytes(canonical(payload).encode("utf-8"))
