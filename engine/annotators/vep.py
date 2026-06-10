"""
engine/annotators/vep.py
========================
Fetches variant consequence data from the Ensembl VEP REST API.
Selects the canonical clinical consequence using MANE Select priority.

Public interface
----------------
    fetch_vep(chrom, pos, ref, alt) -> dict | None
    select_canonical_consequence(vep_result) -> (consequence: str, genes: list[str])

The _fallback_clinvar key in the returned dict contains ClinVar clinical
significance extracted from VEP's colocated_variants, used when the direct
ClinVar lookup returns nothing.
"""

import requests
from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type,
)
from ..validators import validate_coordinates
from .cache import annotation_cache, MISS


_VEP_URL = "https://rest.ensembl.org/vep/human/region"
_TIMEOUT = 10


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    reraise=False,
)
def fetch_vep(chrom: str, pos: int, ref: str, alt: str) -> dict | None:
    """
    Fetch VEP consequences for a single SNV or small variant.

    Returns a VEP result dict extended with a '_fallback_clinvar' key,
    or None if the call fails after retries or coordinates are invalid.
    """
    try:
        validate_coordinates(chrom, pos, ref, alt)
    except ValueError:
        return None

    clean_chrom = str(chrom).replace("chr", "").replace("CHR", "")
    cache_key = f"{clean_chrom}:{pos}:{ref}:{alt}"

    cached = annotation_cache.get("vep", cache_key)
    if cached is not MISS:
        return cached

    region_string = f"{clean_chrom}:{pos}-{pos}:1/{alt}"

    try:
        resp = requests.post(
            _VEP_URL,
            headers={"Content-Type": "application/json"},
            json={"variants": [region_string]},
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        if not data or not isinstance(data, list):
            return None

        result = data[0]

        # Extract ClinVar clinical significance from colocated_variants
        # as a fallback when the direct ClinVar lookup returns nothing.
        fallback_cv = {"clinical_significance": None, "disease_name": None}
        for cv in result.get("colocated_variants", []):
            if "clin_sig" in cv:
                sig = cv["clin_sig"]
                sig = sig[0] if isinstance(sig, list) else sig
                fallback_cv["clinical_significance"] = sig
                if cv.get("phenotype_or_disease") == 1:
                    fallback_cv["disease_name"] = "a specific condition (detailed in ClinVar)"
                break

        result["_fallback_clinvar"] = fallback_cv
        annotation_cache.put("vep", cache_key, result)
        return result

    except Exception:
        return None


def select_canonical_consequence(vep_result: dict) -> tuple[str, list[str]]:
    """
    Select the most clinically relevant consequence and gene from a VEP result.

    Priority order
    --------------
    1. MANE Select transcript — the clinical gold standard
    2. VEP canonical transcript flag
    3. most_severe_consequence field + all genes as fallback

    Returns
    -------
    (consequence: str, genes: list[str])
        A single consequence term and a list of affected gene symbols.
    """
    transcripts = vep_result.get("transcript_consequences", [])

    # 1. MANE Select
    for t in transcripts:
        flags = t.get("flags") or []
        if isinstance(flags, str):
            flags = [flags]
        if "mane_select" in flags:
            csq  = (t.get("consequence_terms") or ["unknown"])[0]
            gene = t.get("gene_symbol")
            return csq, ([gene] if gene else [])

    # 2. Canonical transcript
    for t in transcripts:
        if t.get("canonical") == 1:
            csq  = (t.get("consequence_terms") or ["unknown"])[0]
            gene = t.get("gene_symbol")
            return csq, ([gene] if gene else [])

    # 3. Fallback: most_severe_consequence + all gene symbols
    genes = list({
        t.get("gene_symbol")
        for t in transcripts
        if t.get("gene_symbol")
    })
    csq = vep_result.get("most_severe_consequence", "unknown")
    return csq, genes


def select_insilico(vep_result: dict) -> tuple[str | None, str | None]:
    """
    Extract SIFT and PolyPhen predictions from the clinically-relevant
    transcript (MANE Select, then canonical, then any transcript that has them).

    Returns (sift_prediction, polyphen_prediction), each a lowercased label
    (e.g. "deleterious"/"tolerated", "probably_damaging"/"benign") or None.
    """
    transcripts = vep_result.get("transcript_consequences", []) or []

    def _pick(predicate):
        for t in transcripts:
            if predicate(t) and (t.get("sift_prediction") or t.get("polyphen_prediction")):
                return t
        return None

    def _flags(t):
        f = t.get("flags") or []
        return [f] if isinstance(f, str) else f

    t = (
        _pick(lambda x: "mane_select" in _flags(x))
        or _pick(lambda x: x.get("canonical") == 1)
        or _pick(lambda x: True)
    )
    if not t:
        return None, None
    sift = t.get("sift_prediction")
    polyphen = t.get("polyphen_prediction")
    return (sift.lower() if sift else None), (polyphen.lower() if polyphen else None)


def select_protein_change(vep_result: dict) -> dict | None:
    """
    Extract the single-residue protein change (for PS1/PM5) from the
    clinically-relevant transcript.

    Returns ``{"gene", "protein_pos", "ref_aa", "alt_aa"}`` for a simple
    missense (amino_acids like "R/W"), or None when not a single-residue
    substitution.
    """
    transcripts = vep_result.get("transcript_consequences", []) or []

    def _flags(t):
        f = t.get("flags") or []
        return [f] if isinstance(f, str) else f

    def _pick(predicate):
        for t in transcripts:
            if predicate(t) and t.get("amino_acids") and t.get("protein_start") is not None:
                return t
        return None

    t = (
        _pick(lambda x: "mane_select" in _flags(x))
        or _pick(lambda x: x.get("canonical") == 1)
        or _pick(lambda x: True)
    )
    if not t:
        return None
    aa = str(t.get("amino_acids", ""))
    if "/" not in aa:
        return None  # not a substitution (e.g. synonymous)
    ref_aa, alt_aa = aa.split("/", 1)
    if len(ref_aa) != 1 or len(alt_aa) != 1:
        return None  # only simple single-residue substitutions
    try:
        pos = int(t.get("protein_start"))
    except (TypeError, ValueError):
        return None
    return {
        "gene": t.get("gene_symbol"),
        "protein_pos": pos,
        "ref_aa": ref_aa.upper(),
        "alt_aa": alt_aa.upper(),
    }
