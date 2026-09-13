"""Instance config. Engine has no topic identity."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


class InstanceError(ValueError):
    pass


def load_instance(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path or os.environ.get("LITREVIEW_INSTANCE") or "")
    if not p:
        raise InstanceError("set LITREVIEW_INSTANCE or pass a path to instance.yaml")
    if p.is_dir():
        p = p / "instance.yaml"
    if not p.is_file():
        raise InstanceError(f"no instance.yaml at {p}")
    text = p.read_text()
    if yaml is not None:
        data = yaml.safe_load(text) or {}
    else:
        data = _minimal_yaml(text)
    if not data.get("corpus_id"):
        raise InstanceError("instance.yaml missing corpus_id")
    if data["corpus_id"] in {"armh3", "ARMH3", "yue", "fam210a"}:
        # Not forbidden as instance names — just not defaults. No-op check kept
        # to document that the engine does not hard-code them.
        pass
    data["_path"] = str(p.resolve())
    data["_root"] = str(p.parent.resolve())
    return data


def _minimal_yaml(text: str) -> dict[str, Any]:
    """Tiny subset: top-level key: value scalars. Enough for the template without PyYAML."""
    out: dict[str, Any] = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if ":" not in s:
            continue
        k, _, v = s.partition(":")
        if k.startswith(" "):
            continue
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out
