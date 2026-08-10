# PEAP Findings Register

**Package:** Prediction Efficacy Audit Program  
**Audit baseline commit:** `458aa2d73f0a576ee28353db631aa1fa9da368a2`  
**Audit date (UTC):** 2026-07-15  
**Severity:** S1 launch-blocking for trial primary · S2 high integrity · S3 medium · S4 low / process

| ID | Sev | Domain | Finding | Evidence | Mitigation | Owner | Gate | Status |
|---|---|---|---|---|---|---|---|---|
| F-01 | S1 | Genetics prior | `VARIANT_CATALOG` peptide effect weights are **synthetic/stylised**, not GWAS-derived | `engine/tracking/genetics.py` L20–22, `source` default `"synthetic"` | Primary SAP reports genetics-only sensitivity; label all genomic priors research-synthetic until replaced; optional primary = panel `expected_pct` only | Biostat + Clinical Bioinfo | B/C | **OPEN** — accepted as trial limitation if labeled |
| F-02 | S1 | Clinical validity | No independent human outcome validation of HBRI predictions exists | VMP §11.1; codebase has simulation tests only | Prospective observational trial is the clinical-validity vehicle | Medical Director | D/E | **OPEN** (by design — trial not run) |
| F-03 | S2 | Evidence coverage | Only **8 / ~181** panel biomarkers have citation-anchored evidence grades; majority use uncited `PANEL_REL_SD=0.20` | `data/biomarker_evidence.json` (8 entries); `engine/tracking/evidence.py` honesty contract | Restrict **trial primary** to grade-A GLP-1 class markers; secondary grade B; exploratory uncited | Biostat | C | **MITIGATED** by endpoint restriction |
| F-04 | S2 | Peptide tiers | Internal efficacy tiers (`Strong Fit`, `Likely Reduced`, …) still encode efficacy language; investigational path maps to pathway labels but FDA-approved path may still assert efficacy | `engine/annotators/peptide_mapper.py` `_determine_efficacy`, `_pathway_match_label` | **Out of trial primary**; suppress or research-label in UI for study participants; do not use tiers as endpoints | Product + Medical Director | A/C | **OPEN** — disposition Task 13 |
| F-05 | S2 | BPC-157 composite | Hand-weighted pathway responder score / tier; investigational compound | `engine/annotators/bpc157_predictor.py` | Exploratory enrichment feature only (`bpc157` adapter); not primary | Clinical Bioinfo | C | **MITIGATED** if β remains 0 or feature exploratory |
| F-06 | S2 | Conformal PGx | No real calibration file → `prediction_set=["uncalibrated"]`, `confidence_level=None` | `engine/pgx/hgnn/conformal.py`; missing `data/pgx/conformal_calibration.json` | Keep out of peptide PEAP primary; never display coverage guarantee | PGx lead | A | **CONTROLLED** (fail-closed in code) |
| F-07 | S1 | Genome build | VMP H-01: silent GRCh38 assumption can corrupt enrichment/genetics when build wrong | VMP §0.3; pipeline validators | Input QC SOP: require documented GRCh38 or controlled liftover; reject otherwise for trial genomics | Eng + Lab | A/C | **OPEN** — SOP written; eng hard-block may still be pending |
| F-08 | S2 | Cohort pooling | LOO population prior changes as cohort grows; early vs late enrollees differ | `pooling.MIN_DONORS=3`, `GENETIC_COHORT_CORRELATION=0.5` | Freeze **pre-trial population prior = None** for primary T0 snapshot (genetics/panel only) or document adaptive prior as secondary | Biostat | C | **OPEN** — firewall recommends freeze-off for primary |
| F-09 | S3 | Feature adapters | Non-genetic β default 0; PRS/BPC/HealthKit/covariates may be no-ops unless enrichment present | `feature_adapters/*`; model page copy | Document adapter inventory in VCC; T0 snapshot stores `responder_features` | Eng | B | **DOCUMENTED** |
| F-10 | S2 | Gated stubs | Dose-response & cross-biomarker OFF; enabling would break coverage contract without data | `DOSE_RESPONSE_ENABLED=False`, `CROSS_BIOMARKER_ENABLED=False` | VCC forbids enabling during trial | Eng | B | **CONTROLLED** |
| F-11 | S2 | Surrogate endpoints | Research-peptide biomarker panels not validated as clinical surrogates | VMP §12.3; grade D VEGF/NOx | Primary = GLP-1 weight/HbA1c only; co-collect clinical anchors | Medical Director | C | **MITIGATED** by primary restriction |
| F-12 | S3 | Demo seed | `/tracking/seed` can inject synthetic patients (dev-bypass only) | `api.py` seed endpoint | Prod OIDC blocks seed; segregate demo DB from trial DB | Ops | A | **CONTROLLED** if trial uses dedicated DB |
| F-13 | S2 | T0 snapshot | No immutable enrollment prediction store yet | `GET .../predictions` recomputes live | Implement analysis-firewall T0 snapshot before enrollment (eng) or offline CRF export | Eng + Clinical ops | C | **OPEN** — required for prospective purity |
| F-14 | S3 | Branch freshness | Audit run on `main` **behind origin/main by 6** | `git status` 2026-07-15 | Re-hash VCC after pull/rebase before Gate C signature | Eng | B | **OPEN** |
| F-15 | S4 | Roles | Medical Director / biostatistician names TBD in VMP approval table | VMP §18 | Name owners before Gate C | Sponsor | C | **OPEN** |

## Severity disposition for Gate C

- **Blockers unless de-scoped or accepted in writing:** F-01 (label), F-07 (genomics QC), F-13 (T0 snapshot), F-15 (named owners).  
- **Accepted limitations (document in protocol/consent):** F-02, F-03 (restricted endpoints), F-11.  
- **Out of primary scope:** F-04, F-05, F-06.

## Changelog

| Date | Change |
|---|---|
| 2026-07-15 | Initial PEAP seed from plan + codebase audit |
