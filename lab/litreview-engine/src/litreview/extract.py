"""Local OA producer: PDF/JATS already on disk → sentence rows. No network."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

_ABBREV = re.compile(
    r"(?<=[A-Za-z])\.(?=\s+[a-z])"  # not used
)
# Split on . ! ? not after Fig./et al./e.g./i.e. or digits
_SPLIT = re.compile(
    r"(?<!\bFig)(?<!\bFigs)(?<!\bet al)(?<!\be\.g)(?<!\bi\.e)(?<!\bvs)"
    r"(?<!\d)(?<=[.!?])\s+(?=[A-Z\"'])"
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text.replace("\r", " "))
    text = re.sub(r"\n+", " ", text)
    parts = _SPLIT.split(text.strip())
    out = []
    for p in parts:
        s = p.strip()
        if len(s) >= 40:
            out.append(s)
    return out


def extract_pdf(path: str | Path) -> dict[str, Any]:
    import pymupdf

    p = Path(path)
    doc = pymupdf.open(p)
    pages = []
    sentences = []
    n = 0
    for i, page in enumerate(doc, 1):
        raw = page.get_text() or ""
        pages.append({"page": i, "n_chars": len(raw)})
        for s in split_sentences(raw):
            n += 1
            sentences.append(
                {"id": f"s{n}", "page": i, "section": "body", "sentence": s}
            )
    meta = doc.metadata or {}
    return {
        "path": str(p),
        "sha256": file_sha256(p),
        "n_pages": doc.page_count,
        "title": meta.get("title") or p.name,
        "sentences": sentences,
        "pages": pages,
    }


def extract_jats_xml(path: str | Path) -> dict[str, Any]:
    """Minimal JATS body paragraph extract. No network."""
    import xml.etree.ElementTree as ET

    p = Path(path)
    tree = ET.parse(p)
    texts = []
    for el in tree.iter():
        tag = el.tag.split("}")[-1]
        if tag in {"p", "title"} and el.text:
            texts.append(el.text)
    blob = " ".join(texts)
    sentences = []
    for i, s in enumerate(split_sentences(blob), 1):
        sentences.append({"id": f"s{i}", "page": 1, "section": "body", "sentence": s})
    return {
        "path": str(p),
        "sha256": file_sha256(p),
        "n_pages": 1,
        "title": p.stem,
        "sentences": sentences,
        "pages": [{"page": 1, "n_chars": len(blob)}],
    }
