"""
engine/annotators/uniprot.py
============================
Fetches protein function, domain, and subcellular location data from
the UniProt REST API by gene symbol.

Public interface
----------------
    fetch_uniprot(gene_symbol: str) -> dict | None

Returns
-------
    {
        "protein_name":        str | None,
        "function":            str | None,
        "subcellular_location": str | None,
        "domains":             list[str],
    }
    None if no UniProt entry is found for the given gene symbol.
"""

import requests
from functools import lru_cache
from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type,
)

_BASE = "https://rest.uniprot.org/uniprotkb"
_TIMEOUT = 10


@lru_cache(maxsize=256)
def fetch_uniprot(gene_symbol: str) -> dict | None:
    """
    Look up protein information from UniProt by gene symbol.

    Results are LRU-cached since many variants share the same gene.

    Parameters
    ----------
    gene_symbol : str   HGNC gene symbol (e.g. "COL1A1").

    Returns
    -------
    dict | None   See module docstring for returned fields.
    """
    if not gene_symbol or not isinstance(gene_symbol, str):
        return None

    data = _query_uniprot(gene_symbol.strip().upper())
    if data is None:
        return None

    return data


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    reraise=False,
)
def _query_uniprot(gene_symbol: str) -> dict | None:
    """Query UniProt REST API for a human gene symbol."""
    try:
        # Search for reviewed (Swiss-Prot) human entries for this gene
        params = {
            "query": f"gene_exact:{gene_symbol} AND organism_id:9606 AND reviewed:true",
            "format": "json",
            "size": "1",
            "fields": "protein_name,cc_function,cc_subcellular_location,ft_domain",
        }
        resp = requests.get(
            f"{_BASE}/search",
            params=params,
            headers={"Accept": "application/json"},
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200:
            return None

        results = resp.json().get("results", [])
        if not results:
            return None

        entry = results[0]
        return _extract(entry)

    except Exception:
        return None


def _extract(entry: dict) -> dict:
    """Extract relevant fields from a UniProt JSON entry."""

    # Protein name
    protein_name = None
    pn = entry.get("proteinDescription", {})
    rec = pn.get("recommendedName", {})
    if rec:
        protein_name = rec.get("fullName", {}).get("value")
    if not protein_name:
        sub = pn.get("submissionNames", [])
        if sub:
            protein_name = sub[0].get("fullName", {}).get("value")

    # Function
    function_text = None
    for comment in entry.get("comments", []):
        if comment.get("commentType") == "FUNCTION":
            texts = comment.get("texts", [])
            if texts:
                function_text = texts[0].get("value")
                break

    # Subcellular location
    subcellular = None
    for comment in entry.get("comments", []):
        if comment.get("commentType") == "SUBCELLULAR LOCATION":
            locs = comment.get("subcellularLocations", [])
            if locs:
                loc_names = []
                for loc in locs:
                    loc_val = loc.get("location", {}).get("value")
                    if loc_val:
                        loc_names.append(loc_val)
                if loc_names:
                    subcellular = "; ".join(loc_names)
            break

    # Domains
    domains = []
    for feature in entry.get("features", []):
        if feature.get("type") == "Domain":
            desc = feature.get("description", "")
            if desc and desc not in domains:
                domains.append(desc)

    return {
        "protein_name": protein_name,
        "function": function_text,
        "subcellular_location": subcellular,
        "domains": domains,
    }
