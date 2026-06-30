"""
engine/annotators/pharmgkb.py
==============================
Fetches drug-gene interaction annotations from the PharmGKB REST API.

Public interface
----------------
    fetch_pharmgkb(rsid: str) -> dict | None

Returns
-------
    {
        "drug_interactions": [
            {
                "drug":           str,
                "effect":         str | None,
                "evidence_level": str | None,
                "phenotype":      str | None,
            },
            ...
        ]
    }
    None if no PharmGKB annotations are found for this rsID.
"""

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .cache import MISS, annotation_cache

_BASE = "https://api.pharmgkb.org/v1/data"
_TIMEOUT = 10


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    reraise=False,
)
def fetch_pharmgkb(rsid: str) -> dict | None:
    """
    Look up drug-gene interactions from PharmGKB by rsID.

    Parameters
    ----------
    rsid : str   A valid dbSNP rsID (e.g. "rs1799983").

    Returns
    -------
    dict | None   See module docstring for returned fields.
    """
    if not rsid or not str(rsid).lower().startswith("rs"):
        return None

    cached = annotation_cache.get("pharmgkb", rsid)
    if cached is not MISS:
        return cached

    try:
        # Step 1: Find the PharmGKB variant ID for this rsID
        resp = requests.get(
            f"{_BASE}/variant",
            params={"symbol": rsid, "view": "base"},
            headers={"Accept": "application/json"},
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        variants = data.get("data", [])
        if not variants:
            annotation_cache.put("pharmgkb", rsid, None)
            return None

        variant_id = variants[0].get("id")
        if not variant_id:
            annotation_cache.put("pharmgkb", rsid, None)
            return None

        # Step 2: Get clinical annotations for this variant
        ann_resp = requests.get(
            f"{_BASE}/clinicalAnnotation",
            params={"location.variants.id": variant_id, "view": "base"},
            headers={"Accept": "application/json"},
            timeout=_TIMEOUT,
        )
        if ann_resp.status_code != 200:
            return None

        ann_data = ann_resp.json()
        annotations = ann_data.get("data", [])

        if not annotations:
            return None

        interactions = []
        for ann in annotations:
            # Extract related chemicals (drugs)
            chemicals = ann.get("relatedChemicals", [])
            phenotypes = ann.get("relatedDiseases", [])
            evidence = ann.get("level", {})

            for chem in chemicals:
                drug_name = chem.get("name", "Unknown")
                phenotype_names = [p.get("name") for p in phenotypes if p.get("name")]

                interactions.append({
                    "drug": drug_name,
                    "effect": ann.get("phenotypeText"),
                    "evidence_level": evidence.get("term") if isinstance(evidence, dict) else str(evidence) if evidence else None,
                    "phenotype": "; ".join(phenotype_names) if phenotype_names else None,
                })

        if not interactions:
            annotation_cache.put("pharmgkb", rsid, None)
            return None

        result = {"drug_interactions": interactions}
        annotation_cache.put("pharmgkb", rsid, result)
        return result

    except Exception:
        return None
