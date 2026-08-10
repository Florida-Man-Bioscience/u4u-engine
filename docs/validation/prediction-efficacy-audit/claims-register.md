# Claims Register — Prediction Surfaces

**Baseline commit:** `458aa2d`  
**Date:** 2026-07-15  

**Priority:**  
- **P0** — trial-primary candidate (pre-specified SAP)  
- **P1** — secondary / exploratory in trial  
- **P2** — suppress, relabel, or exclude from clinical/study primary narrative  

| claim_id | Surface | Output fields | Math object | User | Research label today? | Priority | Code path | Notes |
|---|---|---|---|---|---|---|---|---|
| C-HBRI-POST | `GET /tracking/patients/{id}/predictions?peptide=&biomarker=` | `posterior`, `posterior_predictive`, `expected_window` | Posterior on θ + predictive curve after likelihood | Tracking UI / API | Spec says research; UI chart language is predictive | **P0** (secondary: *after* observations) | `analysis.predict_response` | Not pure prospective once measurements enter likelihood |
| C-HBRI-PRIOR | same endpoint | `prior`, `prior_predictive`, `prior_expected_window`, `responder_features` | Prior on θ (η·expected_pct, BLUE-fused if donors) | Tracking UI / API | Partial | **P0 primary** (T0 prior / prior_predictive @ fixed horizon) | same | **Recommended trial primary** when captured at enrollment with n_measurements=0 or pre-baseline only |
| C-HBRI-POP | same | `population_prior` | LOO cohort empirical prior | API | Implicit | **P1** | `pooling.combine_priors` | Prefer **off** for primary purity (F-08) |
| C-HBRI-PRIORS | `GET /tracking/patients/{id}/priors` | per-peptide responder strength list | Genetics-derived r / prior objects | API | Genetics synthetic | **P1** | `derive_responder_prior` | Synthetic weights (F-01) |
| C-GEN-SYN | `POST .../genetics/synthetic` | synthetic profile | Simulated genotypes | Dev/demo | Explicit synthetic | **P2** for trial | `generate_synthetic_profile` | **Forbidden** for trial participants |
| C-FROM-JOB | `POST /tracking/patients/from-job/{job_id}` | patient + profile + enrichment + engine_recs tiers | Job→tracking bridge | Product | Mixed | **P1** inputs | `profile_from_job`, enrichment | Genomics must pass build QC (F-07) |
| C-UI-CHART | `/tracking` PosteriorChart | 95% bands, “predicted plateau” | Renders C-HBRI-* | Clinician/user | Model page disclaims clinical result | **P0 display** | `frontend/.../PosteriorChart.tsx` | Must show research/validation status (transparency pack) |
| C-UI-MODEL | `/tracking/model` | formalization copy | Documentation | Users | Explicit non-clinical | **P1** (good) | `model/page.tsx` | Keep aligned with freeze |
| C-TIER | pipeline `peptide_recommendations` | `predicted_tier`, `prediction_description` | Heuristic gene-overlap tiers | Results / from-job | Pathway remap for investigational | **P2** | `peptide_mapper.py` | Not a validated response model |
| C-BPC | `bpc157_prediction` / enrichment | composite score, responder tier | Hand weights | Results + HBRI feature | Experimental | **P2** / exploratory P1 feature | `bpc157_predictor.py` | Not primary endpoint |
| C-PRS | `prs_profile` | trait scores / percentiles | PRS calculator | Results + PRS adapter | European-skew risk | **P1** feature only | `prs_calculator.py` | Ancestry caveats (VMP §15) |
| C-PGX-CP | drug prediction conformal set | `prediction_set`, `confidence_level` | Mondrian split-CP | PGx tab | Uncalibrated without file | **P2** for coverage claims | `pgx/hgnn/conformal.py` | Fail-closed uncalibrated |
| C-PGX-CPIC | CPIC phenotype / dose text | phenotype, recommendation | Guideline table | PGx tab | Strong external evidence | **Out of PEAP** | `pgx/cpic/` | Separate analytical track |
| C-RECEPTOR | receptor HIGH/NORMAL/LOW | expression/isoform labels | Hand rsID modifiers | Pipeline | Not fused into HBRI | **P2** | `receptor_mapper.py` | Display-only per model page |
| C-SEED | `POST /tracking/seed` | synthetic cohort | Demo generator | Dev | Explicit demo | **P2** | `seed.py` | Not trial data |

## Recommended trial claim set

### Primary (P0)

**Object:** Immutable **T0 prior predictive** for fractional change θ (and implied biomarker value at weeks **12 and 24**) for:

1. `Body weight (GLP-1 RA)` among participants prescribed Semaglutide / Tirzepatide / Liraglutide  
2. `HbA1c (GLP-1 RA)` among participants with T2D or prediabetes indication as defined in protocol  

**Snapshot definition:**  
- Captured at enrollment or treatment start **before** post-baseline measurements enter the likelihood (or with likelihood deliberately null for the snapshot).  
- Model version = VCC (`frozen-config-vcc.md`).  
- Population prior **disabled** for primary snapshot (genetics + panel evidence only) — *ratify*.  
- Store full JSON of `predict_response` payload + commit/config hash.

**Estimand (plain language):** Association between locked T0 predicted % change and observed % change at the anchor week.

### Secondary (P1)

- Posterior predictions after partial follow-up (calibration of monitoring, not pure prospective).  
- Grade-B markers (IGF-1, IGFBP-3) in GH-secretagogue strata.  
- Sensitivity: genetics-on vs genetics-off; ρ ∈ {0, 0.5}; with/without enrichment adapters.  
- Binary response AUROC (e.g. ≥5% weight loss at 12 weeks).

### Excluded from efficacy narrative (P2)

- Peptide `Strong Fit` / efficacy tiers as proof of response.  
- BPC-157 “responder” clinical claims.  
- Conformal coverage guarantees.  
- Synthetic genetics for enrolled subjects.  
- Any claim that validates **therapy efficacy**.

## Redlines (copy)

| Location | Issue | Required language |
|---|---|---|
| Tracking charts | “predicted plateau” without context | Append: “Research model — not a clinical determination; human validation ongoing.” |
| Results peptide tiers | Efficacy vocabulary | Investigational: pathway-match labels only; approved drugs: no patient-level efficacy guarantee from genetics alone |
| Consent / protocol | Predictor purpose | “Study evaluates whether software predictions match biomarker changes; it does not prove peptides work.” |

## API contract (P0 fields to persist)

From `predict_response` return dict (`analysis.py` ~L631–656):

```
patient_id, peptide, biomarker_name, tau_weeks, baseline,
prior, responder_features, population_prior (expect null if frozen off),
likelihood (expect null at pure T0), posterior (== prior at pure T0),
prior_predictive, posterior_predictive, prior_expected_window, expected_window,
n_measurements, last_observed_week, treatment_id, treatment_start
```

Plus metadata: `vcc_id`, `git_sha`, `config_sha256`, `snapshot_at`, `snapshot_mode` (`prior_only` | `full`).
