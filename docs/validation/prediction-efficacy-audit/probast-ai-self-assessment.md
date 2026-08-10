# PROBAST+AI Pre-Trial Self-Assessment (HBRI Predictor)

**Tool:** PROBAST / PROBAST+AI domains (participants, predictors, outcome, analysis)  
**Model under assessment:** Hierarchical Bayesian Responder Index + Normal–Normal update  
**Purpose of assessment:** Risk-of-bias / applicability **before** external validation study enrollment  
**Date:** 2026-07-15 · **Commit:** `458aa2d`

> This is a **self-assessment for mitigation design**, not a published ROB review.  
> Overall ROB for a *clinical product claim* today: **HIGH**.  
> Target after mitigations for a *validation study protocol*: **acceptable for research with high residual ROB disclosed**.

---

## 1. Participants

| Signalling question | Judgment | Notes |
|---|---|---|
| Appropriate data sources / design for validation? | **Partly** | Prospective multi-site observational (clinic partnership) is appropriate for external validation of predictions under treatment-as-usual; not an RCT of the tool |
| Inclusion/exclusion appropriate? | **Unclear until protocol lock** | Must define age, already-on-therapy, minimum planned follow-up, which peptides |
| Participants reflect intended use population? | **Partly** | Boutique peptide clinics ≠ general endocrinology; compounded GLP-1 common — capture product type |
| Selection bias (who enrolls)? | **High risk** | Volunteers may be more adherent / different SES; document refusal rates |

**Mitigations:** eligibility SOP; product type (branded/compounded); multi-site; report participation flow (TRIPOD+AI).

**Domain ROB:** High → **Moderate** if mitigations executed.

---

## 2. Predictors

| Signalling question | Judgment | Notes |
|---|---|---|
| Predictors defined and assessed similarly for all? | **Partly** | Genetics from job VCF/array vs synthetic path; enrichment optional |
| Predictors available at time prediction is intended? | **Yes if T0 snapshot** | Must not use post-baseline labs in “baseline prediction” |
| All predictors part of model? | **Yes (documented)** | Genetics (anchored), PRS, BPC-157, covariates, HealthKit; non-genetic β≈0 |
| Predictor assessment blinded to outcome? | **Yes if firewall** | T0 freeze before outcome known |
| Complex predictors (AI) handled transparently? | **Partly** | Spec + model page good; genetics weights synthetic (F-01) |

**Mitigations:** claims register; forbid synthetic genetics in trial; genome-build QC; freeze VCC; disable cohort pooling for primary; store `responder_features`.

**Domain ROB:** High (synthetic genetics) — **cannot fully clear pre-trial**; disclose.

---

## 3. Outcome

| Signalling question | Judgment | Notes |
|---|---|---|
| Outcome determined appropriately? | **Partly** | Weight/HbA1c standard for GLP-1; research-peptide markers weak (grade D) |
| Outcome definition pre-specified? | **In progress** | SAP draft sets 12/24w % change; binary thresholds need biostat ratification |
| Outcome assessed without knowledge of prediction? | **Design-dependent** | Prefer clinic measures entered without viewing research prediction, or accept pragmatic contamination and sensitivity analysis |
| Same outcome definition for all participants? | **Requires SOP** | Units, scales, lab methods |

**Mitigations:** outcome SOP; primary grade-A endpoints only; co-collect method metadata.

**Domain ROB:** Low–moderate for GLP-1 flagship; high for research peptides (de-scoped).

---

## 4. Analysis

| Signalling question | Judgment | Notes |
|---|---|---|
| Reasonable number of participants / events? | **Unknown** | Sample size TBD biostat (SAP) |
| Continuous predictors handled appropriately? | **Yes** | Continuous θ / % change primary |
| Missing data handled? | **Needs pre-spec** | Complete-case vs multiple imputation for primary |
| Complexities (clustering by site) accounted? | **Needs pre-spec** | Multi-site ICC |
| Performance measures appropriate? | **Yes if SAP followed** | Calibration slope/intercept, coverage, MAE; not accuracy alone |
| Model overfitting / optimism? | **N/A for pure external validation of locked model** | Critical that model is **not** refit on study data for primary |
| Classification thresholds pre-specified? | **Pending** | Binary response cutpoints |

**Mitigations:** locked VCC; analysis firewall; SAP metrics; no primary refit; sensitivity analyses for ρ and genetics.

**Domain ROB:** Low **if** freeze + firewall hold; High if live model updates mid-study.

---

## 5. Overall

| | Development (historical) | External validation (planned) |
|---|---|---|
| ROB | High (synthetic priors, limited evidence grades) | High residual but protocol-mitigated |
| Applicability to boutique peptide clinics on branded GLP-1 | Moderate | Intended setting |
| Applicability to broad primary care | Poor | Do not generalize without data |

**PROBAST-style conclusion for Gate C:** Proceed to validation study **only** with (1) restricted primary endpoints, (2) locked model, (3) explicit disclosure of synthetic genetics, (4) T0 snapshot firewall. Do **not** proceed to product clinical claims.

---

## 6. Mapping to findings register

| Domain | Findings |
|---|---|
| Participants | F-11, protocol ops |
| Predictors | F-01, F-05, F-07, F-08, F-09 |
| Outcome | F-03, F-11 |
| Analysis | F-02, F-13, F-10 |
