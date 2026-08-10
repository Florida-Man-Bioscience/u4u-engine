# Input QC SOP — Genotype & Enrichment → Prediction (Trial)

**ID:** U4U-SOP-PRED-IN-001  
**Version:** 0.1-DRAFT  
**Date:** 2026-07-15  
**Aligns:** VMP H-01 (genome build), PEAP F-07  

---

## 1. Purpose

Ensure genomic and enrichment inputs used for T0 predictions are complete, build-correct, and non-synthetic for trial participants.

---

## 2. Acceptable genome inputs

| Format | Allowed | Notes |
|---|---|---|
| VCF / VCF.gz GRCh38 | Yes | Preferred |
| Array exports (23andMe, etc.) | Conditional | Only if build known and GRCh38 or validated liftover |
| GRCh37 without liftover | **Reject** | Silent mis-annotation risk |
| Synthetic profile (`POST .../genetics/synthetic`) | **Reject for trial** | Demo only |

---

## 3. Required metadata (CRF / job record)

- `genome_build` ∈ {`GRCh38`, `GRCh37+liftover`, `unknown`} — **unknown → reject**  
- `file_type`, `platform` if known  
- `job_id` if from `/analyze`  
- `liftover_tool_version` if applicable  
- Operator initials + date  

---

## 4. Genetic profile rules

1. Prefer `source=job:{job_id}` via `POST /tracking/patients/from-job/{job_id}`.  
2. Verify ownership: user owns job and patient (API already IDOR-guards).  
3. Record that catalog **weights are synthetic** even when genotypes are real (F-01).  
4. Minimum catalog call coverage: **ratify** with biostat (e.g. ≥70% of VARIANT_CATALOG loci called or explicitly missing-as-ref policy).  

---

## 5. Enrichment

From job results only:

- `prs_profile` (optional)  
- `bpc157` composite (optional; exploratory)  

If missing: adapters no-op; prediction still valid with genetics/panel only.

---

## 6. Reject / hold criteria

| Condition | Action |
|---|---|
| Build unknown or unhandled GRCh37 | Do not create T0 primary snapshot |
| Synthetic genetics | Exclude from primary cohort |
| Job not complete / not owned | 404 / exclude |
| Evidence of demo seed patient | Exclude |

---

## 7. Logging

Store with T0 snapshot: build, job_id, source, enrichment keys present (boolean), VCC id.
