"""
engine/pipeline.py
==================
Orchestrates the full variant analysis pipeline. Raw file bytes go in,
a sorted list of scored and summarized variant dicts comes out.

This is the function your workers call. It has zero knowledge of HTTP
servers, job queues, databases, or UI frameworks — those concerns belong
to the wrapper layer.

Pipeline steps
--------------
  1.  validate_file_bytes      — size, magic bytes, UTF-8 check
  2.  parse_file               — VCF / 23andMe / CSV / rsID list
  3.  apply_quality_filter     — drop hom-ref, failed calls, low GQ/DP, indels
  4.  filter_variants          — rsID whitelist (ACMG81, pharma, carrier…)
  5.  resolve_rsids             — Ensembl REST: rsid_only → coordinates
  6.  deduplicate               — key by (chrom, pos, ref, alt)
  7.  annotate_variant (loop)  — VEP + ClinVar + gnomAD + MyVariant fallback
  8.  score_variant  (loop)    — clinical score, tier, zygosity, carrier note
  8b. map_kegg_pathways         — KEGG pathway mapping for gene hits
  8c. call_ar_cag_repeat        — ExpansionHunter STR calling (if BAM provided)
  8d. map_receptors             — receptor expression + isoform prediction
  8e. calculate_prs             — polygenic risk scores for complex traits
   8f. predict_bpc157_response   — BPC-157 response prediction (Grok Plan)
   8g. map_peptide_coverage       — peptide therapy candidate coverage
  9.  generate_summary (loop)  — plain-English consumer output
  10. sort by score descending

Public interface
----------------
    run_pipeline(
        file_bytes: bytes,
        filename: str,
        filters: list[str] = (),
        data_dir: str = "data",
        progress_callback: callable = None,
        bam_path: str = None,
        sex: str = None,
        ancestry: str = "Unknown",
    ) -> dict

    annotate_variant(v: dict) -> dict   — usable alone for cache-aware workers
"""

from .parsers      import parse_file
from .validators   import validate_file_bytes
from .genome_build import detect_build, plan_build_handling
from .liftover     import liftover_available, lift_variants_to_grch38
from .quality_filter import apply_quality_filter, filter_stats
from .filters      import filter_variants, filter_variants_by_bed
from .rsid_resolver import resolve_rsids
from .deduplicator import deduplicate
import concurrent.futures
from .annotators.vep     import (
    fetch_vep, select_canonical_consequence, select_insilico, select_protein_change,
)
from .annotators.clinvar import fetch_clinvar
from .annotators.gnomad  import fetch_gnomad
from .annotators.myvariant import fetch_myvariant
from .scoring  import score_variant
from .summary  import generate_summary
from .acmg     import (
    classify_acmg, AcmgConfig, load_lof_mechanism_genes,
    load_known_pathogenic_aa, summarize_acmg,
)

# Built once: the curated LoF-mechanism gene set (lets PVS1 be counted) and the
# known-pathogenic-AA reference (lets PS1/PM5 be applied). Both default to
# their data files, which are conservative/empty until curated.
_ACMG_CONFIG = AcmgConfig(
    lof_mechanism_genes=load_lof_mechanism_genes(),
    known_pathogenic_aa=load_known_pathogenic_aa(),
)

# V3 annotators
from .annotators.kegg_mapper import map_variants_to_pathways, generate_pathway_summary
from .annotators.receptor_mapper import map_receptors, generate_receptor_summary
from .annotators.prs_calculator import calculate_prs
from .annotators.bpc157_predictor import predict_bpc157_response, generate_bpc157_summary
from .annotators.peptide_mapper import map_peptide_coverage
from .annotators.uniprot import fetch_uniprot
from .annotators.pharmgkb import fetch_pharmgkb
from .annotators.gwas_catalog import fetch_gwas
from .dossier_generator import generate_dossiers

import logging
log = logging.getLogger(__name__)

# V3 STR caller (optional — requires BAM + ExpansionHunter binary)
try:
    from .repeat_callers.expansion_hunter import call_ar_cag_repeat
    _HAS_EXPANSION_HUNTER = True
except ImportError:
    _HAS_EXPANSION_HUNTER = False


def run_pipeline(
    file_bytes: bytes,
    filename: str,
    filters: list = (),
    bed_filter: str = None,
    data_dir: str = "data",
    progress_callback=None,
    # V3 parameters
    bam_path: str = None,
    sex: str = None,
    ancestry: str = "Unknown",
    partial_results: list = None,
    # V4 pharmacogenomics parameters
    current_medications: list = None,
    pgx_confidence: float = 0.90,
) -> dict:
    """
    Run the full variant analysis pipeline.

    Parameters
    ----------
    file_bytes : bytes
        Raw file content. Never written to disk by this function.
    filename : str
        Original filename — used for format detection and validation only.
    filters : list[str]
        rsID filter filenames to apply (e.g. ["acmg81_rsids.txt"]).
        Empty list = process all variants (use for VCF files).
    bed_filter : str | None
        Optional BED filename in `data_dir` for coordinate-based restriction.
    data_dir : str
        Path to the directory containing filter files.
    progress_callback : callable | None
        Optional function called as progress_callback(step: str, pct: int).

    bam_path : str | None
        Path to BAM/CRAM file for ExpansionHunter STR calling. Optional.
    sex : str | None
        Biological sex ('M' or 'F'). Required if bam_path is provided.
    ancestry : str
        Ancestry label for PRS adjustment and CAG repeat normalization.

    Returns
    -------
    dict
        V3 result dict with keys:
          - 'variants': list[dict] sorted by score descending
          - 'pathway_summary': KEGG pathway analysis
          - 'receptor_genetics': receptor expression + isoform predictions
          - 'prs_profile': polygenic risk scores
          - 'ar_cag_repeat': STR analysis (or None)
    """
    def _progress(step: str, pct: int):
        log.info("Pipeline step: %s (Progress: %d%%)", step, pct)
        if progress_callback:
            progress_callback(step, pct)

    # ── Step 1: Validate ────────────────────────────────────────────────────
    _progress("Validating file", 2)
    validate_file_bytes(file_bytes, filename)

    # ── Step 1b: Genome build gate ──────────────────────────────────────────
    # Coordinate files on a confirmed non-GRCh38 build are rejected before any
    # coordinate-based annotation can silently mis-map them — unless liftover is
    # explicitly enabled, in which case GRCh37 coordinates are lifted to GRCh38
    # after parsing. The detected build is recorded on the result.
    _progress("Checking genome build", 3)
    genome_build = detect_build(file_bytes, filename)
    build_plan = plan_build_handling(
        genome_build, filename,
        liftover_available=liftover_available(genome_build["build"]),
    )
    if build_plan["action"] == "reject":
        raise ValueError(build_plan["message"])
    log.info("Detected genome build: %s (%s); action=%s",
             genome_build["build"], genome_build["source"], build_plan["action"])

    # ── Step 2: Parse ───────────────────────────────────────────────────────
    _progress("Parsing file", 5)
    raw_variants = parse_file(file_bytes, filename)

    # ── Step 2b: Liftover (only when planned) ───────────────────────────────
    if build_plan["action"] == "liftover":
        _progress("Lifting coordinates to GRCh38", 6)
        raw_variants, unmapped = lift_variants_to_grch38(raw_variants)
        genome_build = {
            **genome_build,
            "original_build": build_plan["from_build"],
            "lifted_to": "GRCh38",
            "liftover_unmapped": len(unmapped),
        }
        if unmapped:
            log.warning("liftover: %d coordinate variant(s) could not be mapped to GRCh38",
                        len(unmapped))

    # ── Step 3: Quality filter ──────────────────────────────────────────────
    _progress("Applying quality filter", 8)
    quality_filtered = apply_quality_filter(raw_variants)
    stats = filter_stats(raw_variants, quality_filtered)
    if stats["removed_count"]:
        _progress(
            f"Quality filter: removed {stats['removed_count']} low-quality / "
            f"reference calls ({stats['removed_pct']}%)",
            10,
        )

    # ── Step 4: Apply Target Filters ─────────────────────────────────────────
    _progress("Applying targeted filters", 12)
    
    if not filters and not bed_filter:
        panel_filtered = quality_filtered
    else:
        var_set = set() # use id() to deduplicate refs
        panel_filtered = []
        
        if filters:
            list1 = filter_variants(quality_filtered, list(filters), data_dir)
            for v in list1:
                var_set.add(id(v))
                panel_filtered.append(v)
                
        if bed_filter:
            list2 = filter_variants_by_bed(quality_filtered, bed_filter, data_dir)
            for v in list2:
                if id(v) not in var_set:
                    var_set.add(id(v))
                    panel_filtered.append(v)

    # ── Step 5: Resolve rsid_only variants to coordinates ───────────────────
    rsid_only   = [(v["rsid"], v.get("genotype")) for v in panel_filtered
                   if v["variant_type"] == "rsid_only"]
    coord_vars  = [v for v in panel_filtered if v["variant_type"] == "coordinate"]

    if rsid_only:
        _progress(f"Resolving {len(rsid_only)} rsIDs via Ensembl", 14)

        def _resolve_progress(current, total):
            if total > 50 and current % max(1, total // 50) != 0 and current != total:
                return
            pct = 14 + int((current / max(total, 1)) * 5)
            _progress(f"Resolving rsIDs ({current}/{total})", pct)

        resolved = resolve_rsids(rsid_only, progress_callback=_resolve_progress)
        coord_vars.extend(resolved)

    # ── Step 6: Coordinate BED Filter ───────────────────────────────────────
    if bed_filter:
        _progress("Applying BED coordinate filter", 20)
        coord_vars = filter_variants_by_bed(coord_vars, bed_filter, data_dir)

    # ── Step 7: Deduplicate ─────────────────────────────────────────────────
    _progress("Deduplicating variants", 26)
    unique_variants = deduplicate(coord_vars)

    # ── Steps 7–9: Annotate → Score → Summarize ─────────────────────────────
    # Process variants in parallel due to high IO bounds
    total = len(unique_variants)
    final_results = []
    
    _progress(f"Annotating {total} variants...", 30)

    def process_variant(v):
        annotated = annotate_variant(v)
        scored = score_variant(annotated)
        summary = generate_summary(scored)
        
        combined = dict(scored)
        combined.update({
            "emoji":             summary.emoji,
            "headline":          summary.headline,
            "consequence_plain": summary.consequence_plain,
            "rarity_plain":      summary.rarity_plain,
            "clinvar_plain":     summary.clinvar_plain,
            "action_hint":       summary.action_hint,
            "zygosity_plain":    summary.zygosity_plain,
            "tier_basis":        summary.tier_basis,
        })

        # Transparent ACMG/AMP evidence assembly (subset; requires human
        # sign-out). Kept separate from the heuristic priority score/tier.
        combined["acmg"] = classify_acmg(combined, _ACMG_CONFIG)

        if partial_results is not None:
            partial_results.append(combined)
            
        return combined

    completed = 0
    annotation_failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_v = {executor.submit(process_variant, v): v for v in unique_variants}
        for future in concurrent.futures.as_completed(future_to_v):
            v = future_to_v[future]
            try:
                res = future.result()
                final_results.append(res)
            except Exception as e:
                # Do NOT silently drop the variant: a dropped variant is
                # indistinguishable from a true-negative and could be a
                # clinically critical finding. Record it loudly so the caller
                # can detect the incomplete analysis and block reporting.
                vid = v.get("rsid") or (
                    f"{v.get('chrom')}:{v.get('pos')}" if v.get("chrom") else "unknown"
                )
                annotation_failures.append({
                    "variant_id": vid,
                    "location": f"{v.get('chrom')}:{v.get('pos')}" if v.get("chrom") else None,
                    "rsid": v.get("rsid"),
                    "error": f"{type(e).__name__}: {e}",
                })
                log.error("variant annotation failed for %s: %s", vid, e)

            completed += 1
            if completed % max(1, total // 10) == 0 or completed == total:
                pct = 30 + int((completed / max(total, 1)) * 55)
                _progress(f"Annotating variants ({completed}/{total})", pct)

    if annotation_failures:
        log.error(
            "annotation incomplete: %d of %d variant(s) failed and are NOT in results",
            len(annotation_failures), total,
        )

    # ── Step 8b: KEGG Pathway Mapping ──────────────────────────────────────
    _progress("Mapping KEGG pathways", 92)
    all_genes = []
    for r in final_results:
        genes = r.get("genes", [])
        if isinstance(genes, str):
            genes = [genes]
        all_genes.extend(genes)
    all_genes = list(set(g for g in all_genes if g))

    pathway_hits = map_variants_to_pathways(all_genes)
    pathway_summary_text = generate_pathway_summary(pathway_hits)

    # ── Step 8c: AR CAG Repeat (if BAM provided) ──────────────────────────
    ar_cag_result = None
    if bam_path and _HAS_EXPANSION_HUNTER:
        _progress("Running ExpansionHunter STR analysis", 94)
        try:
            ar_cag_result = call_ar_cag_repeat(bam_path, sex=sex, ancestry=ancestry)
        except Exception:
            ar_cag_result = None  # Graceful degradation

    # ── Step 8d: Receptor Genetics ─────────────────────────────────────────
    _progress("Predicting receptor expression", 96)
    receptor_profiles = map_receptors(final_results)
    receptor_summary_text = generate_receptor_summary(receptor_profiles)

    # ── Step 8e: Polygenic Risk Scores ─────────────────────────────────────
    _progress("Calculating polygenic risk scores", 97)
    prs_profile = calculate_prs(final_results, ancestry=ancestry)

    # ── Step 8f: BPC-157 Response Prediction (Grok Plan) ──────────────────
    _progress("Predicting BPC-157 response", 98)
    bpc157_prediction = predict_bpc157_response(final_results)

    # ── Step 8g: Peptide Therapy Coverage ──────────────────────────────────
    _progress("Mapping peptide therapy candidates", 99)
    peptide_mapping = map_peptide_coverage(final_results)

    # ── Merge BPC-157 detailed prediction into the BPC-157 peptide entry ──
    for rec in peptide_mapping["recommendations"]:
        if rec["peptide_name"] == "BPC-157":
            rec["bpc157_prediction"] = bpc157_prediction
            # Override tier with the more detailed BPC-157 predictor's tier
            rec["predicted_tier"] = bpc157_prediction["responder_tier"]
            rec["prediction_description"] = bpc157_prediction["summary_text"]
            break

    # ── Step 8h: Pharmacogenomics (star alleles → CPIC → PRS → conformal) ──
    _progress("Pharmacogenomics: star alleles, CPIC, PRS, conformal", 99)
    try:
        from .pgx.orchestrator import pgx_stage
        pgx_profile = pgx_stage(
            final_results,
            medications=current_medications,
            bam_path=bam_path,
            confidence=pgx_confidence,
        ).to_dict()
    except Exception as _e:  # pragma: no cover — degrade gracefully
        pgx_profile = {
            "summary_text": f"PGx stage skipped: {_e}",
            "star_alleles": [], "hla_calls": [], "recommendations": [],
            "prs_results": [], "drug_predictions": [],
            "phenoconversion_notes": [], "input_path": "array",
        }

    # ── Step 10: Sort ────────────────────────────────────────────────────────
    final_results.sort(key=lambda x: x["score"], reverse=True)

    _progress("Complete", 100)

    # ── ACMG result-level summary (counts + ClinVar discordances) ───────────
    acmg_summary = summarize_acmg(final_results)

    # ── V3 Result Assembly ─────────────────────────────────────────────────
    result = {
        "genome_build": genome_build,
        "acmg_summary": acmg_summary,
        "analysis_status": {
            "expected_variants": total,
            "annotated_variants": len(final_results),
            "failed_variants": len(annotation_failures),
            "failures": annotation_failures,
            "complete": len(annotation_failures) == 0,
        },
        "variants": final_results,
        "pathway_summary": {
            "pathways_hit": pathway_hits,
            "summary_text": pathway_summary_text,
        },
        "receptor_genetics": {
            "receptor_profiles": receptor_profiles,
            "summary_text": receptor_summary_text,
        },
        "prs_profile": prs_profile,
        "ar_cag_repeat": ar_cag_result,
        "peptide_recommendations": peptide_mapping,
        "pgx_profile": pgx_profile,
    }

    # Generate per-peptide dossier reports
    result["dossiers"] = generate_dossiers(result)

    return result


def annotate_variant(v: dict) -> dict:
    """
    Annotate a single coordinate variant using VEP, ClinVar, gnomAD, and
    MyVariant.info as a fallback.

    This function is exported directly for use in cache-aware workers:
        result = cache.get(key) or annotate_variant(v)

    Parameters
    ----------
    v : dict
        A coordinate variant dict (chrom, pos, ref, alt, rsid).

    Returns
    -------
    dict
        The input dict extended with:
        variant_id, location, consequence, genes,
        clinvar, disease_name, condition_key, gnomad_af, gnomad_popmax,
        gnomad_homozygote_count.

        condition_key is a stable lookup key for the associated condition:
            "OMIM:<id>"      — OMIM MIM number (preferred)
            "MedGen:<id>"    — NCBI MedGen concept ID
            "ClinVar:<uid>"  — ClinVar Variation UID (last resort)
            None             — no ClinVar record or lookup failed
    """
    chrom = v.get("chrom")
    pos   = v.get("pos")
    ref   = v.get("ref")
    alt   = v.get("alt")
    rsid  = v.get("rsid")

    result = dict(v)
    result["variant_id"] = rsid or f"{chrom}:{pos}"
    result["location"]   = f"{chrom}:{pos}"

    # ── VEP ──────────────────────────────────────────────────────────────────
    vep_data = fetch_vep(chrom, pos, ref, alt)
    if vep_data:
        consequence, genes = select_canonical_consequence(vep_data)
        result["consequence"] = consequence

        sift_pred, polyphen_pred = select_insilico(vep_data)
        result["sift_pred"]     = sift_pred
        result["polyphen_pred"] = polyphen_pred

        protein_change = select_protein_change(vep_data)
        if protein_change:
            result["protein_pos"] = protein_change["protein_pos"]
            result["ref_aa"]      = protein_change["ref_aa"]
            result["alt_aa"]      = protein_change["alt_aa"]

        bed_genes = v.get("bed_genes", [])
        result["genes"]       = list(set(genes + bed_genes))
        fallback_cv           = vep_data.get("_fallback_clinvar", {})
    else:
        result["consequence"] = "unknown"
        result["genes"]       = v.get("bed_genes", [])
        fallback_cv           = {}

    # ── ClinVar (primary: NCBI eUtils; fallback: VEP colocated) ─────────────
    cv_data = fetch_clinvar(rsid) if rsid else None

    if cv_data and cv_data.get("clinical_significance"):
        result["clinvar"]        = cv_data["clinical_significance"]
        result["disease_name"]   = cv_data.get("disease_name")
        result["condition_key"]  = cv_data.get("condition_key")
    elif fallback_cv.get("clinical_significance"):
        result["clinvar"]        = fallback_cv["clinical_significance"]
        result["disease_name"]   = fallback_cv.get("disease_name")
        result["condition_key"]  = fallback_cv.get("condition_key")
    else:
        result["clinvar"]        = None
        result["disease_name"]   = None
        result["condition_key"]  = None

    # ── gnomAD (primary: GraphQL API) ────────────────────────────────────────
    gnomad_data = fetch_gnomad(chrom, pos, ref, alt)
    if gnomad_data:
        result["gnomad_af"]               = gnomad_data.get("af")
        result["gnomad_popmax"]           = gnomad_data.get("popmax_af")
        result["gnomad_homozygote_count"] = gnomad_data.get("homozygote_count")
    else:
        result["gnomad_af"]               = None
        result["gnomad_popmax"]           = None
        result["gnomad_homozygote_count"] = None

    # ── MyVariant.info fallback ───────────────────────────────────────────────
    # If we're still missing ClinVar or gnomAD data, try MyVariant.info
    missing_clinvar = not result.get("clinvar")
    missing_gnomad  = result.get("gnomad_af") is None

    if missing_clinvar or missing_gnomad:
        mv = fetch_myvariant(rsid=rsid, chrom=chrom, pos=pos, ref=ref, alt=alt)
        if mv:
            if missing_clinvar and mv.get("clinvar_classification"):
                result["clinvar"]       = mv["clinvar_classification"]
                result["disease_name"]  = mv.get("clinvar_condition")
                # Only overwrite condition_key from MyVariant if we don't
                # already have one from the primary ClinVar lookup.
                if not result.get("condition_key"):
                    result["condition_key"] = mv.get("condition_key")
            if missing_gnomad and mv.get("gnomad_af") is not None:
                result["gnomad_af"]    = mv["gnomad_af"]
                result["gnomad_popmax"] = mv.get("gnomad_popmax")

    # ── UniProt (protein function per gene) ───────────────────────────────
    uniprot_data = []
    for gene in result.get("genes", []):
        up = fetch_uniprot(gene)
        if up:
            up["gene"] = gene
            uniprot_data.append(up)
    result["uniprot"] = uniprot_data if uniprot_data else None

    # ── PharmGKB (drug-gene interactions) ─────────────────────────────────
    pgkb = fetch_pharmgkb(rsid) if rsid else None
    result["pharmgkb"] = pgkb

    # ── GWAS Catalog (trait associations) ─────────────────────────────────
    gwas = fetch_gwas(rsid) if rsid else None
    result["gwas"] = gwas

    return result
