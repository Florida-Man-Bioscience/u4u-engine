"""
engine/annotators/gwas_catalog.py
==================================
Fetches trait associations from the NHGRI-EBI GWAS Catalog REST API.

Public interface
----------------
    fetch_gwas(rsid: str) -> dict | None

Returns
-------
    {
        "trait_associations": [
            {
                "trait":       str,
                "p_value":     float | None,
                "effect_size": str | None,
                "pubmed_id":   str | None,
            },
            ...
        ]
    }
    None if no GWAS associations are found for this rsID.
"""

import requests
from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type,
)

_BASE = "https://www.ebi.ac.uk/gwas/rest/api"
_TIMEOUT = 10


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    reraise=False,
)
def fetch_gwas(rsid: str) -> dict | None:
    """
    Look up GWAS trait associations by rsID.

    Parameters
    ----------
    rsid : str   A valid dbSNP rsID (e.g. "rs1799983").

    Returns
    -------
    dict | None   See module docstring for returned fields.
    """
    if not rsid or not str(rsid).lower().startswith("rs"):
        return None

    try:
        resp = requests.get(
            f"{_BASE}/singleNucleotidePolymorphisms/{rsid}/associations",
            headers={"Accept": "application/json"},
            timeout=_TIMEOUT,
        )
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            return None

        data = resp.json()
        associations = data.get("_embedded", {}).get("associations", [])

        if not associations:
            return None

        traits = []
        seen_traits = set()

        for assoc in associations:
            # Extract trait name
            trait_name = None
            ef_traits = assoc.get("efoTraits", [])
            if ef_traits:
                trait_name = ef_traits[0].get("trait")

            if not trait_name:
                continue

            # Deduplicate by trait name
            if trait_name.lower() in seen_traits:
                continue
            seen_traits.add(trait_name.lower())

            # p-value
            p_mantissa = assoc.get("pvalueMantissa")
            p_exponent = assoc.get("pvalueExponent")
            p_value = None
            if p_mantissa is not None and p_exponent is not None:
                try:
                    p_value = float(p_mantissa) * (10 ** int(p_exponent))
                except (ValueError, TypeError):
                    pass

            # Effect size (beta or OR)
            effect_size = None
            beta = assoc.get("betaNum")
            odds_ratio = assoc.get("orPerCopyNum")
            if beta is not None:
                effect_size = f"β={beta}"
                beta_unit = assoc.get("betaUnit")
                if beta_unit:
                    effect_size += f" ({beta_unit})"
            elif odds_ratio is not None:
                effect_size = f"OR={odds_ratio}"

            # PubMed ID from study link
            pubmed_id = None
            study_link = assoc.get("_links", {}).get("study", {}).get("href", "")
            # We'll extract PubMed ID from the study endpoint if needed
            # For now, use the study accession
            study_accession = assoc.get("studyId")

            traits.append({
                "trait": trait_name,
                "p_value": p_value,
                "effect_size": effect_size,
                "pubmed_id": study_accession,
            })

        if not traits:
            return None

        # Sort by p-value (most significant first)
        traits.sort(key=lambda t: t["p_value"] if t["p_value"] is not None else 1.0)

        # Cap at 10 most significant associations
        return {"trait_associations": traits[:10]}

    except Exception:
        return None
