"""
engine/genome_build.py
======================
Genome reference-build detection and gating.

Background
----------
Every external annotator in this engine (Ensembl VEP, ClinVar-by-coordinate,
gnomAD, MyVariant, ExpansionHunter) interprets coordinates as **GRCh38/hg38**.
If a file built on GRCh37/hg19 is processed as if it were GRCh38, every
coordinate-based annotation is silently wrong — a "wrong result" class hazard.

This module detects the build of an input file and lets the pipeline refuse to
silently process coordinate data on an unsupported build.

Policy
------
- VCF / coordinate files: coordinates are used *directly* for annotation, so a
  confirmed non-GRCh38 build is **rejected** (ValueError).
- 23andMe / rsID-list files: the file's own positions are discarded and each
  rsID is re-resolved to GRCh38 coordinates via Ensembl, so the file's build is
  recorded for transparency but does **not** block processing.
- CSV: build cannot be inferred from the file; treated as "unknown" and allowed
  (the operator is responsible for supplying GRCh38 coordinates).

Public interface
----------------
    detect_build(file_bytes: bytes, filename: str) -> dict
    assert_supported_build(file_bytes: bytes, filename: str) -> dict
"""

from __future__ import annotations

import re

SUPPORTED_BUILD = "GRCh38"

# Authoritative chr1 lengths discriminate the major human builds unambiguously.
_CONTIG1_LENGTHS = {
    248956422: "GRCh38",
    249250621: "GRCh37",
    247249719: "NCBI36",   # hg18 — ancient, also unsupported
}

# Substring signatures found in ##reference / ##assembly / 23andMe header text.
_BUILD38_TOKENS = ("grch38", "hg38", "b38", "hs38", "build 38", "build38", "release 38")
_BUILD37_TOKENS = ("grch37", "hg19", "b37", "hs37", "build 37", "build37", "release 37")
_BUILD36_TOKENS = ("grch36", "ncbi36", "hg18", "b36", "build 36", "build36")

_CONTIG_RE = re.compile(
    r"##contig=<[^>]*?ID=(?:chr)?1[,>][^>]*?length=(\d+)", re.IGNORECASE
)


def _coordinate_authoritative(filename: str) -> bool:
    """True when the file's own coordinates are used directly for annotation."""
    name = filename.lower()
    return name.endswith(".vcf") or name.endswith(".vcf.gz")


def detect_build(file_bytes: bytes, filename: str) -> dict:
    """
    Best-effort detection of the genome reference build of an input file.

    Returns a dict:
        {"build": "GRCh38"|"GRCh37"|"NCBI36"|"unknown",
         "confidence": "high"|"medium"|"low"|"none",
         "source": str,        # what evidence was used
         "evidence": str}      # the matched token / contig length, for the audit trail
    """
    name = filename.lower()
    head = file_bytes[:65536].decode("utf-8", errors="ignore")

    # ── VCF: prefer the unambiguous contig length, then ##reference text ──────
    if name.endswith(".vcf") or name.endswith(".vcf.gz"):
        m = _CONTIG_RE.search(head)
        if m:
            length = int(m.group(1))
            build = _CONTIG1_LENGTHS.get(length)
            if build:
                return {"build": build, "confidence": "high",
                        "source": "vcf_contig_length",
                        "evidence": f"chr1 length={length}"}
        ref_lines = "\n".join(
            ln for ln in head.splitlines()
            if ln.lower().startswith(("##reference", "##assembly"))
        ).lower()
        hit = _match_tokens(ref_lines)
        if hit:
            return {"build": hit, "confidence": "medium",
                    "source": "vcf_reference_header", "evidence": ref_lines[:120]}
        return {"build": "unknown", "confidence": "none",
                "source": "vcf_no_build_metadata", "evidence": ""}

    # ── 23andMe / text: build is usually stated in the comment header ─────────
    if name.endswith(".txt"):
        comment = "\n".join(ln for ln in head.splitlines() if ln.startswith("#")).lower()
        hit = _match_tokens(comment)
        if hit:
            return {"build": hit, "confidence": "medium",
                    "source": "text_comment_header", "evidence": comment[:160]}
        return {"build": "unknown", "confidence": "none",
                "source": "text_no_build_metadata", "evidence": ""}

    # ── CSV / other: cannot infer ────────────────────────────────────────────
    return {"build": "unknown", "confidence": "none",
            "source": "format_not_build_aware", "evidence": ""}


def _match_tokens(text: str) -> str | None:
    """Return the build implied by build-token substrings, or None."""
    if any(t in text for t in _BUILD38_TOKENS):
        return "GRCh38"
    if any(t in text for t in _BUILD37_TOKENS):
        return "GRCh37"
    if any(t in text for t in _BUILD36_TOKENS):
        return "NCBI36"
    return None


def assert_supported_build(file_bytes: bytes, filename: str) -> dict:
    """
    Detect the build and reject confirmed-unsupported builds for coordinate files.

    Returns the detection dict (also recorded by the pipeline). Raises ValueError
    when a coordinate-authoritative file is confirmed to be on a non-GRCh38 build.

    rsID-resolved formats (23andMe, rsID list) are never rejected here because
    their coordinates are re-derived on GRCh38 from the rsID; the detected build
    is returned for transparency only.
    """
    detection = detect_build(file_bytes, filename)
    build = detection["build"]

    if _coordinate_authoritative(filename) and build not in (SUPPORTED_BUILD, "unknown"):
        raise ValueError(
            f"This file appears to use the {build} reference build "
            f"({detection['evidence'] or detection['source']}), but the engine "
            f"only supports {SUPPORTED_BUILD}/hg38 coordinates. Processing it as "
            f"{SUPPORTED_BUILD} would mis-annotate every variant. Please supply a "
            f"{SUPPORTED_BUILD}-aligned file, or lift the coordinates over to "
            f"{SUPPORTED_BUILD} before uploading."
        )

    return detection
