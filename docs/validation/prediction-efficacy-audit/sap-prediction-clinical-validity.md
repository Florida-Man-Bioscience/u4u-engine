# Statistical Analysis Plan (DRAFT) — Prediction Clinical Validity

**Document ID:** U4U-SAP-PRED-001  
**Version:** 0.1-DRAFT  
**Date:** 2026-07-15  
**Model:** HBRI + Normal–Normal conjugate update (`engine/tracking/`)  
**Status:** Planning draft — **not powered; biostatistician ratification required** before Gate C signature  

> Does **not** evaluate peptide therapy efficacy. Evaluates association between **locked software predictions** and **observed biomarker trajectories** under treatment-as-usual.

---

## 1. Objectives

### 1.1 Primary

Among enrolled adults prescribed a GLP-1 RA (semaglutide, tirzepatide, or liraglutide) by their own clinician, quantify **calibration** of the locked T0 prior predictive % change for:

1. `Body weight (GLP-1 RA)` at week **12** (and key secondary week **24**)  
2. `HbA1c (GLP-1 RA)` at week **12** / **24** among participants with protocol-defined glycemic indication  

### 1.2 Secondary

- Discrimination for pre-specified binary response  
- Interval coverage of model 95% predictive bands for observed values at anchor weeks  
- MAE / RMSE of predicted vs observed % change  
- Sensitivity analyses (genetics off; ρ; branded vs compounded)  
- Exploratory: grade-B GH-axis markers; other peptides  

### 1.3 Explicit non-objectives

- Efficacy or safety of any peptide  
- Non-inferiority of the tool vs clinician judgment  
- Validation of conformal PGx coverage  

---

## 2. Analysis populations

| Population | Definition |
|---|---|
| **Enrolled** | Consent + HIPAA auth; partner clinic patient |
| **GLP-1 primary cohort** | On branded or compounded semaglutide/tirzepatide/liraglutide with T0 snapshot + baseline weight |
| **Primary completers (weight)** | Primary cohort with week-12 weight (window ±14 days, ratify) |
| **Primary completers (HbA1c)** | As above with week-12 HbA1c |
| **Per-protocol** | Completers with no model-version change; product type known |

---

## 3. Endpoints / outcomes

### 3.1 Continuous (primary)

\[
Y = 100 \times \frac{V(t^*) - V_0}{V_0}
\]

- \(V_0\): baseline measurement (SOP window)  
- \(t^*\): 12 weeks (primary), 24 weeks (key secondary)  
- Marker-specific units per outcome SOP  

### 3.2 Binary (secondary)

| Endpoint | Proposed rule (**ratify**) |
|---|---|
| Weight response | \(Y \le -5\%\) at 12 weeks |
| Strong weight response | \(Y \le -10\%\) at 24 weeks |
| HbA1c response | absolute Δ ≤ −0.5 percentage points at 12 weeks |

### 3.3 Predictor (locked)

\[
\hat{Y} = 100 \times \mu_{\theta,\text{T0}} \times a(t^*)
\]

or equivalently the prior-predictive mean % change implied by T0 snapshot at week \(t^*\), with \(a(w)=1-e^{-w/\tau}\).

Store raw `prior.mean` / posterior-at-T0 (prior-only) and full JSON.

---

## 4. Primary performance measures

| Metric | Definition | Role |
|---|---|---|
| **Calibration slope** | Slope from regression \(Y \sim \hat{Y}\) (OLS or robust; pre-specify) | Primary |
| **Calibration intercept** | Intercept of same model (ideally 0 when slope fixed at 1 — report both flexible and fixed-slope forms) | Primary co-metric |
| Calibration plot | Deciles or continuous smoother of observed vs predicted | Visual primary |
| MAE | mean \(\|Y-\hat{Y}\|\) | Secondary |
| RMSE | root mean square error | Secondary |
| Pearson / Spearman ρ | Association | Secondary descriptive |
| 95% interval coverage | fraction of observed \(V(t^*)\) inside model predictive interval at \(t^*\) | Secondary honesty |
| AUROC | binary endpoints vs \(\hat{Y}\) | Secondary |

### 4.1 Illustrative acceptance (Gate E — **not final**)

- Calibration slope 95% CI includes 1.0 and lower bound > 0  
- Intercept near 0 with CI including 0 under slope=1 model  
- Predictive coverage in [0.85, 0.98] for nominal 95% (looser than simulation because of misspecification)  

Failure → no clinical claim; research iteration only.

---

## 5. Subgroups & sensitivity

Pre-specify (report even if underpowered):

- Product: branded vs compounded  
- Molecule: sema / tirz / lira  
- Sex  
- Genetic ancestry proxies if available (or “not evaluated”)  
- Baseline BMI / baseline HbA1c tertiles  

Sensitivity:

1. Genetics feature zeroed (panel prior only)  
2. T0 with vs without any pre-baseline measurements in likelihood  
3. ρ ∈ {0, 0.5} if pooling ever enabled  
4. Exclude HealthKit proxy observations  

---

## 6. Sample size (**PLACEHOLDER**)

**Status:** Not calculated.  

Biostatistician to power for:

- Precision of calibration slope (e.g. 95% CI half-width ≤ 0.25 at assumed residual variance), **or**  
- 80% power to detect slope ≠ 0 at clinically plausible R²  

Account for: loss to follow-up (suggest 20–30%), site clustering, dual primary endpoints (hierarchical: weight first, then HbA1c).

Record final N in SAP v1.0 before enrollment.

---

## 7. Missing data

- Primary: complete-case at \(t^*\) with reporting of missingness rates  
- If missingness >15% for primary endpoint: pre-specify multiple imputation sensitivity (MAR)  
- Missing predictors at T0: classify as ineligible for primary cohort if genetics required; or use no-genetics prior path if pre-allowed  

---

## 8. Multiplicity

Hierarchical:  
1. Weight calibration slope at 12w  
2. If 1 “positive” per Gate E criteria: HbA1c calibration slope at 12w  
Other analyses exploratory without alpha spending (label as such).

---

## 9. Interim analysis

No formal efficacy interim. Descriptive enrollment dashboards only.  
No model refit for primary. Monitoring triggers per `monitoring-plan.md`.

---

## 10. Software & reproducibility

- Analysis code version-controlled; seed fixed for any bootstrap  
- VCC id and git SHA attached to every T0 snapshot  
- Primary tables reproducible from export of snapshots + outcomes  

---

## 11. Amendments

Any change to primary endpoint, \(t^*\), or predictor definition requires version bump and Gate C re-approval if before LPLV; after enrollment starts, document as amendment with rationale.
