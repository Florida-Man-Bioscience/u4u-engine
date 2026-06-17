"""
engine/rsid_resolver.py
=======================
Resolves rsIDs to genomic coordinates using the Ensembl REST API.

Key improvement over the prior implementation: when a 23andMe genotype
string is available, the resolver uses it to select only the allele the
user actually carries — rather than returning all possible alt alleles
for that rsID. This eliminates phantom variants for alleles the user
does not have.

Public interface
----------------
    resolve_rsid(rsid: str, genotype: str | None = None) -> list[dict]
    resolve_rsids(rsids_and_genotypes: list[tuple], progress_callback=None) -> list[dict]

Each returned dict has the canonical variant shape from parsers.py:
    chrom, pos, ref, alt, rsid, variant_type="coordinate", genotype, zygosity
"""

import time
import requests
import json
import os
from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type,
)
from .validators import validate_rsid
from .parsers import _infer_zygosity_from_genotype


_ENSEMBL_BASE    = "https://rest.ensembl.org"
_REQUEST_TIMEOUT = 10  # seconds
_RATE_LIMIT_SLEEP = 0.07  # ~14 req/s — within Ensembl's unauthenticated limit
_CACHE_DB_PATH   = os.path.join(os.getenv("DATA_DIR", "data"), "rsid_cache.db")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    reraise=False,
)
def resolve_rsid(rsid: str, genotype: str | None = None) -> list[dict]:
    """
    Convert a single rsID to coordinate variant dicts.

    Parameters
    ----------
    rsid     : str            A valid dbSNP rsID (e.g. "rs429358").
    genotype : str | None     23andMe genotype string (e.g. "TC" or "TT").
                              When provided, only alleles the user actually
                              carries are returned. Without it, all known
                              alt alleles for the rsID are returned.

    Returns
    -------
    list[dict]
        Zero or more coordinate variant dicts. Returns [] on failure.
    """
    try:
        validate_rsid(rsid)
    except ValueError:
        return []

    try:
        resp = requests.get(
            f"{_ENSEMBL_BASE}/variation/human/{rsid}",
            headers={"Content-Type": "application/json"},
            timeout=_REQUEST_TIMEOUT,
        )
        time.sleep(_RATE_LIMIT_SLEEP)
        if resp.status_code != 200:
            return []

        data = resp.json()
        mappings = data.get("mappings", [])
        if not mappings:
            return []

        # Use the first (primary assembly) mapping only
        mapping = mappings[0]
        allele_string = mapping.get("allele_string", "")
        alleles = allele_string.split("/")
        if len(alleles) < 2:
            return []

        ref  = alleles[0].upper()
        chrom = str(mapping.get("seq_region_name", "")).replace("chr", "").replace("CHR", "")
        pos   = mapping.get("start")

        if genotype:
            # Genotype-aware: only return the alt alleles the user carries.
            # Find chars in the genotype string that differ from the reference.
            alt_candidates = list(dict.fromkeys(
                a.upper() for a in genotype if a.upper() != ref and a.upper() in "ACGT"
            ))

            if not alt_candidates:
                # All genotype chars match the reference → homozygous ref
                # Return nothing — this position is not a variant for this user.
                return []

            zygosity = _infer_zygosity_from_genotype(genotype, ref)
            results = [
                {
                    "chrom":        chrom,
                    "pos":          pos,
                    "ref":          ref,
                    "alt":          alt,
                    "rsid":         rsid,
                    "variant_type": "coordinate",
                    "genotype":     genotype,
                    "zygosity":     zygosity,
                    "gq":           None,
                    "dp":           None,
                }
                for alt in alt_candidates
            ]

        else:
            # No genotype available — return all known alt alleles
            all_alts = [a.upper() for a in alleles[1:] if a.upper() in "ACGT"]
            results = [
                {
                    "chrom":        chrom,
                    "pos":          pos,
                    "ref":          ref,
                    "alt":          alt,
                    "rsid":         rsid,
                    "variant_type": "coordinate",
                    "genotype":     None,
                    "zygosity":     "unknown",
                    "gq":           None,
                    "dp":           None,
                }
                for alt in all_alts
            ]
            
        return results

    except Exception:
        return []


def _get_cache_conn():
    """Return a (conn, is_postgres) tuple. Falls back to SQLite."""
    try:
        from db.pool import DATABASE_URL, get_raw_conn
        if DATABASE_URL:
            return get_raw_conn(), True
    except Exception:
        pass
    import sqlite3
    conn = sqlite3.connect(_CACHE_DB_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rsid_cache (
            rsid TEXT,
            genotype TEXT,
            result_json TEXT,
            fetched_at REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (rsid, genotype)
        )
    """)
    # SQLite lacks ADD COLUMN IF NOT EXISTS — probe and ALTER so dev DBs
    # created before migration 007 gain the new column on first run.
    cols = {row[1] for row in conn.execute("PRAGMA table_info(rsid_cache)").fetchall()}
    if "fetched_at" not in cols:
        conn.execute("ALTER TABLE rsid_cache ADD COLUMN fetched_at REAL NOT NULL DEFAULT 0")
        conn.commit()
    return conn, False


def _evict_old_rsid_cache(conn, is_pg: bool) -> None:
    """Drop rows older than 90 days. Called once per resolve_rsids batch
    so we keep eviction lazy without paying it on every individual
    insert. Cheap with the fetched_at index from migration 007."""
    try:
        if is_pg:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM rsid_cache "
                "WHERE fetched_at < NOW() - INTERVAL '90 days'"
            )
            conn.commit()
        else:
            cutoff = time.time() - 90 * 86400
            conn.execute("DELETE FROM rsid_cache WHERE fetched_at < ?", (cutoff,))
            conn.commit()
    except Exception:
        # Eviction is best-effort; never let it stop a resolve from running.
        pass


def resolve_rsids(
    rsids_and_genotypes: list,
    progress_callback=None,
) -> list[dict]:
    """
    Resolve a list of rsIDs to coordinate variants.

    Parameters
    ----------
    rsids_and_genotypes : list
        Either a list of str rsIDs (no genotype context), or a list of
        (rsid, genotype) tuples for 23andMe-sourced variants.

    progress_callback : callable | None
        Optional function called as progress_callback(current: int, total: int).

    Returns
    -------
    list[dict]   All resolved coordinate variants (flattened, order preserved).
    """
    resolved = []
    total = len(rsids_and_genotypes)

    conn, is_pg = _get_cache_conn()
    _evict_old_rsid_cache(conn, is_pg)

    try:
        for i, item in enumerate(rsids_and_genotypes):
            if isinstance(item, tuple):
                rsid, genotype = item[0], item[1] if len(item) > 1 else None
            else:
                rsid, genotype = item, None

            geno_key = genotype or ""

            if is_pg:
                cur = conn.cursor()
                cur.execute(
                    "SELECT result_json FROM rsid_cache WHERE rsid = %s AND genotype = %s",
                    (rsid, geno_key),
                )
                row = cur.fetchone()
                hit = row["result_json"] if row else None
            else:
                cur = conn.cursor()
                cur.execute(
                    "SELECT result_json FROM rsid_cache WHERE rsid = ? AND genotype = ?",
                    (rsid, geno_key),
                )
                row = cur.fetchone()
                hit = row[0] if row else None

            if hit:
                resolved.extend(json.loads(hit))
            else:
                variants = resolve_rsid(rsid, genotype)
                if is_pg:
                    cur.execute(
                        """
                        INSERT INTO rsid_cache (rsid, genotype, result_json, fetched_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (rsid, genotype) DO UPDATE
                            SET result_json = EXCLUDED.result_json,
                                fetched_at  = EXCLUDED.fetched_at
                        """,
                        (rsid, geno_key, json.dumps(variants)),
                    )
                    conn.commit()
                else:
                    cur.execute(
                        "INSERT OR REPLACE INTO rsid_cache "
                        "(rsid, genotype, result_json, fetched_at) VALUES (?, ?, ?, ?)",
                        (rsid, geno_key, json.dumps(variants), time.time()),
                    )
                    conn.commit()
                resolved.extend(variants)

            if progress_callback:
                progress_callback(i + 1, total)

    finally:
        if is_pg:
            from db.pool import put_conn
            put_conn(conn)
        else:
            conn.close()

    return resolved
