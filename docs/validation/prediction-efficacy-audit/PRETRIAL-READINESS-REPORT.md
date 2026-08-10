# Pre-Trial Prediction Readiness Report (PEAP)

**Document ID:** U4U-PEAP-READY-001  
**Version:** 0.1  
**Date:** 2026-07-15  
**Baseline git commit:** `458aa2d73f0a576ee28353db631aa1fa9da368a2`  
**VCC candidate:** `vcc-prediction-pretrial-2026-07-15`  

---

## 1. Executive decision (audit recommendation)

| Gate | Color | Decision |
|---|---|---|
| **A — Containment & honesty** | **YELLOW** | Proceed with labeling package; close genome-build operational SOP; suppress P2 efficacy tiers in study UI |
| **B — Analytical / model freeze** | **YELLOW→GREEN technical** | **93/93** core tracking tests passed; hashes recorded; re-freeze after catching up 6 commits behind origin; T0 snapshot store still missing |
| **C — Trial readiness (enroll with locked primary)** | **RED / HOLD** | Do **not** open enrollment claiming locked primary predictions until blockers below are cleared or formally accepted by Medical Director + biostat |

**Overall:** The prediction engine is **analytically freezeable as a research instrument** and has a clear primary validation design (GLP-1 grade-A markers). It is **not** clinically validated. Gate C is **not met**.

---

## 2. Scope & non-claims

### In scope
- HBRI Bayesian predictor (`engine/tracking/analysis.predict_response`)
- Evidence-graded panel priors (`data/biomarker_evidence.json`)
- Pre-trial audit against TRIPOD+AI / PROBAST+AI / GMLP / ACCE / IMDRF SaMD clinical evaluation layers

### Out of scope / excluded claims
- Peptide **therapy** efficacy  
- Conformal PGx coverage guarantees  
- Peptide “Strong Fit” tiers as validated response  
- Clinical utility RCT of the software  

Boundary language: validating that predictions match biomarker trajectories ≠ proving peptides work (`docs/clinical-validation-plan.md` §12.4).

---

## 3. Standards applied

| Standard | How used |
|---|---|
| ACCE | Ordered analytical → clinical validity (trial) → utility (later) |
| IMDRF SaMD CE | Valid clinical association (evidence matrix); analytical V&V (this report); clinical validation (future trial) |
| TRIPOD+AI | Protocol map + SAP structure |
| PROBAST+AI | Pre-trial ROB self-assessment |
| GMLP | Freeze, monitoring, multi-disciplinary design intent |
| FDA CDS transparency | Transparency pack |
| Repo VMP | `docs/clinical-validation-plan.md` §11.7, §12, AC-16/17 |

---

## 4. Claims summary

| Priority | Claims | Disposition |
|---|---|---|
| **P0** | T0 prior / prior_predictive for `Body weight (GLP-1 RA)` & `HbA1c (GLP-1 RA)` | Trial primary (SAP) |
| **P1** | Posterior monitoring; grade-B markers; sensitivities | Secondary |
| **P2** | Efficacy tiers, BPC clinical responder claims, synthetic genetics, conformal coverage | Suppress / exclude |

Full table: [`claims-register.md`](claims-register.md).

---

## 5. VCC freeze identifiers

- **VCC ID:** `vcc-prediction-pretrial-2026-07-15`  
- **Manifest:** `data/validation/vcc-manifest-2026-07-15.json`  
- **Doc:** [`frozen-config-vcc.md`](frozen-config-vcc.md)  
- **Gated OFF:** dose-response, cross-biomarker  
- **ρ default:** 0.5; **Δ:** 0.72  
- **Primary pooling:** OFF recommended  

---

## 6. Analytical V&V results

| Item | Result |
|---|---|
| pytest (calibration, responder_index, pooling, bayes, evidence, predictions) | **93 passed in 2.24s** (2026-07-15, nix develop / Python 3.12) |
| Simulation coverage contract | Met under generative assumptions ([`analytical-bayes-report.md`](analytical-bayes-report.md)) |
| Clinical human validation | **Not done** (by design) |

---

## 7. Evidence provenance summary

| Class | Count | Trial role |
|---|---|---|
| Grade A | 2 (GLP-1 weight, HbA1c) | **Primary** |
| Grade B | 2 (IGF-1, IGFBP-3) | Secondary |
| Grade C | 2 | Exploratory |
| Grade D | 2 (BPC VEGF/NOx) | Exploratory only |
| Uncited panel measurements | ~173 of 181 | Not primary |

Genetics catalog weights: **synthetic** (F-01).

Details: [`evidence-provenance-matrix.md`](evidence-provenance-matrix.md).

---

## 8. PROBAST+AI summary

- Overall ROB for product claim: **HIGH**  
- Validation-study posture: high residual ROB **disclosed**, mitigable via freeze + endpoint restriction + firewall  
- Details: [`probast-ai-self-assessment.md`](probast-ai-self-assessment.md)

---

## 9. SAP abstract

Locked T0 prior predictive % change will be compared to observed % change at week 12 (key secondary 24) for class-qualified GLP-1 markers using **calibration slope/intercept** (primary), MAE/RMSE, interval coverage, and secondary AUROC for binary response. Sample size **not yet powered**. Full draft: [`sap-prediction-clinical-validity.md`](sap-prediction-clinical-validity.md).

---

## 10. Findings blocking Gate C

| ID | Issue | Required action |
|---|---|---|
| **F-13** | No immutable T0 prediction snapshot store | Eng implement insert-only snapshots **or** controlled EDC export SOP with hash |
| **F-15** | Named Medical Director / biostatistician | Assign owners; sign SAP + VCC |
| **F-07** | Genome build hard-block may still be incomplete | Enforce SOP; preferably eng reject non-GRCh38 for trial jobs |
| **F-14** | Branch 6 commits behind origin | Pull, re-run tests, re-hash VCC |
| **F-01** | Synthetic genetics | Protocol/consent/UI disclosure; sensitivity genetics-off |
| **F-08** | Cohort pooling drift | Confirm primary pooling OFF |

Open register: [`findings-register.md`](findings-register.md).

---

## 11. Gate matrix

| # | Criterion | Gate | Color | Evidence |
|---|---|---|---|---|
| G-A1 | Research-only / no therapy efficacy claim in study materials | A | YELLOW | Transparency pack drafted; UI apply pending |
| G-A2 | P2 conformal coverage not claimed | A | GREEN | Code fail-closed uncalibrated |
| G-A3 | Demo seed cannot pollute trial DB | A | GREEN* | *if OIDC prod + no force seed |
| G-B1 | Core tracking tests green | B | GREEN | 93 passed |
| G-B2 | Content hashes recorded | B | GREEN | Manifest JSON |
| G-B3 | Gated stubs OFF | B | GREEN | Source constants |
| G-B4 | VCC signed after tip-of-main rehash | B | RED | F-14 |
| G-C1 | SAP v1.0 with powered N | C | RED | Placeholder N |
| G-C2 | T0 snapshot mechanism live | C | RED | F-13 |
| G-C3 | Named signatories | C | RED | F-15 |
| G-C4 | IRB approvals / BAA / consent | C | N/A here | Clinical ops (`irb-plan-glp1.md`) |
| G-C5 | Primary endpoints grade A only | C | GREEN | Claims + evidence matrix |

\*Environment-dependent.

---

## 12. Recommended next engineering tasks (post-audit)

1. **Prediction snapshot API + table** (migration) — insert-only T0 payloads with VCC metadata; optional `pooling=false` query flag.  
2. **Genome build detection / hard reject** for trial-bound jobs (VMP H-01).  
3. **UI banner** using transparency pack on `/tracking` and study surfaces.  
4. **Golden fixture** of `predict_response` for fixed synthetic patient JSON under VCC (optional harden).  
5. Re-run full `tests/test_engine/test_tracking/` after `git pull`.  

---

## 13. Package index

| Document | Path |
|---|---|
| Findings | `findings-register.md` |
| Claims | `claims-register.md` |
| PROBAST+AI | `probast-ai-self-assessment.md` |
| TRIPOD+AI map | `tripod-ai-protocol-map.md` |
| SAP draft | `sap-prediction-clinical-validity.md` |
| VCC freeze | `frozen-config-vcc.md` |
| Manifest | `../../data/validation/vcc-manifest-2026-07-15.json` |
| Analytical report | `analytical-bayes-report.md` |
| Evidence matrix | `evidence-provenance-matrix.md` |
| Input QC SOP | `input-qc-sop.md` |
| Outcome SOP | `outcome-measurement-sop.md` |
| Firewall | `analysis-firewall.md` |
| Transparency | `transparency-pack.md` |
| Monitoring | `monitoring-plan.md` |
| Plan | `.hermes/plans/2026-07-14_prediction-engine-pretrial-efficacy-audit.md` |

---

## 14. Signatures (Gate C — incomplete)

| Role | Name | Gate | Date | Signature |
|---|---|---|---|---|
| Clinical Bioinformatics | _TBD_ | B | | |
| Biostatistician | _TBD_ | B/C | | |
| Medical Director | _TBD_ | C | | |
| Quality / Sponsor | _TBD_ | C | | |

**Decision checkbox (Medical Director):**

- [ ] **HOLD enrollment** until F-13, F-14, F-15, powered SAP closed  
- [ ] **Proceed with bounded ops** (EDC snapshots, no software store) — describe residual risk: ________  
- [ ] **Do not use genomic prior in primary** (panel-only predictor) — reduces F-01 impact  

---

## 15. One-line summary

**Freeze-ready research predictor for GLP-1 grade-A endpoints; human efficacy of the predictor unproven; enrollment with locked primary should wait on T0 snapshot infrastructure, powered SAP, named owners, and VCC rehash at current main tip.**
