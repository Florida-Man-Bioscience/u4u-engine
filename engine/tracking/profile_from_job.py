"""
engine/tracking/profile_from_job.py
====================================
Convert an ``/analyze`` job's results into a real-data ``GeneticProfile``.

The synthetic profile generator in ``genetics.py`` exists for demos. This
module is the production-side path: a patient's actual genome upload has
been annotated by the pipeline, and we now mine those annotations for
variants in ``pharmgkb_catalog.EVIDENCE_BASED_CATALOG`` to seed a
``GeneticProfile`` with their *real* genotypes and *evidence-based*
effect weights.

What we look at on each variant in the job
------------------------------------------
- ``rsid``      — primary join key against the catalog.
- ``alt``       — the allele observed on the patient's variant, used to
                  confirm that the patient really carries the catalog's
                  ``effect_allele`` (i.e. that this isn't a strand-flip
                  or a different alt allele than the one PharmGKB
                  studied).
- ``zygosity``  — "heterozygous" | "homozygous_alt" | "homozygous_ref"
                  from the parser. Converted to a 0/1/2 dosage of the
                  effect allele.

Variants whose ``alt`` doesn't match the catalog's ``effect_allele`` are
treated as dosage 0 — we don't try to be clever about strand flips here
because the resulting genotype is no longer the one the PharmGKB
evidence applies to. If we ever wire VEP's strand annotation through,
that logic could live here.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .genetics import GeneticProfile, GeneticVariant, Genotype
from .pharmgkb_catalog import EVIDENCE_BASED_CATALOG, evidence_for


def _zygosity_to_genotype(zygosity: str | None) -> Genotype | None:
    """Map the parser's zygosity strings to ``genetics.Genotype`` labels.

    Returns None when the input is missing or doesn't carry enough
    information to commit to a dosage.
    """
    if not zygosity:
        return None
    z = zygosity.lower().strip()
    if z in ("homozygous_alt", "homozygous-alt", "hom_alt"):
        return "hom_alt"
    if z in ("heterozygous", "het"):
        return "het"
    if z in ("homozygous_ref", "homozygous-ref", "hom_ref"):
        return "hom_ref"
    return None


def _index_variants_by_rsid(variants: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Last-wins index of pipeline variant records by rsID.

    If the same rsID appears multiple times (shouldn't normally happen
    but the upstream pipeline doesn't enforce uniqueness), the latest
    record wins — they're already in pipeline order at this point.
    """
    by_rsid: dict[str, dict[str, Any]] = {}
    for v in variants:
        rsid = (v.get("rsid") or "").strip()
        if rsid:
            by_rsid[rsid] = v
    return by_rsid


def build_profile_from_job_results(
    job_results: dict[str, Any],
    *,
    job_id: str,
) -> GeneticProfile:
    """Build a ``GeneticProfile`` from the pipeline output of one job.

    Only variants present in ``EVIDENCE_BASED_CATALOG`` AND carried by
    the patient (i.e. the patient's ``alt`` matches the catalog's
    ``effect_allele`` and zygosity indicates at least one copy of it)
    end up with non-zero effect weights. Catalog SNPs that aren't in
    the job (the patient is hom-ref or wasn't genotyped at that locus)
    are recorded as ``hom_ref`` with dosage 0 so the profile is dense
    over the catalog and the downstream ``derive_prior`` accounting is
    consistent.

    Parameters
    ----------
    job_results
        The ``results`` dict produced by ``run_pipeline``. Must carry
        a ``"variants"`` list of annotated variant dicts.
    job_id
        Used to tag the resulting profile's ``source`` so the UI can
        show "derived from job <id>" and so the row can be safely
        upserted/replaced if the job is re-analysed.

    Returns
    -------
    GeneticProfile
        A frozen-at-now profile with ``source = "job:<job_id>"``.
    """
    annotated_variants = job_results.get("variants") or []
    by_rsid = _index_variants_by_rsid(annotated_variants)

    profile_variants: list[GeneticVariant] = []
    for entry in EVIDENCE_BASED_CATALOG:
        record = by_rsid.get(entry.rsid)
        # Default: patient does not carry the effect allele at all.
        # `hom_ref` with dosage 0 keeps the catalog footprint stable
        # across patients so n_relevant_variants accounting is honest.
        genotype: Genotype = "hom_ref"
        dosage = 0

        if record is not None:
            alt = (record.get("alt") or "").strip().upper()
            mapped = _zygosity_to_genotype(record.get("zygosity"))
            # Only count the dose when the patient's alt allele is the
            # one PharmGKB studied. Different alt at the same position
            # is a different variant — the evidence doesn't apply.
            if mapped is not None and alt == entry.effect_allele.upper():
                genotype = mapped
                dosage = entry.dosage_for(genotype)

        scaled = {
            pep: round(weight * dosage, 4)
            for pep, weight in entry.peptide_effects.items()
        }
        profile_variants.append(
            GeneticVariant(
                rsid=entry.rsid,
                gene=entry.gene,
                chromosome=entry.chromosome,
                genotype=genotype,
                effect_allele=entry.effect_allele,
                other_allele=entry.other_allele,
                dosage=dosage,
                peptide_effects=scaled,
                description=entry.description,
            )
        )

    return GeneticProfile(
        variants=profile_variants,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        source=f"job:{job_id}",
    )


def evidence_payload(rsid: str) -> dict[str, Any] | None:
    """Public JSON-friendly accessor for the per-rsid evidence citation."""
    cite = evidence_for(rsid)
    if cite is None:
        return None
    return {
        "pharmgkb_level": cite.pharmgkb_level,
        "pmid": cite.pmid,
        "summary": cite.summary,
    }
