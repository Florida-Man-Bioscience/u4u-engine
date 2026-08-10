# Analytical Bayes / HBRI Audit Report

**VCC:** `vcc-prediction-pretrial-2026-07-15`  
**Date:** 2026-07-15  
**Scope:** Software statistical integrity under the model’s generative assumptions — **not** clinical validity.

---

## 1. Model summary

Per `docs/models/peptide-response-model.md`:

- Latent θ = fractional plateau change from baseline  
- Prior μ₀ = η · expected_pct_k with η = 1 + Δ tanh(βᵀx), Δ = 0.72  
- Kinetics a(w) = 1 − e^(−w/τ)  
- Likelihood via joint fit of baseline b and θ; Normal–Normal conjugate update  
- Optional BLUE fusion of genetics prior with LOO cohort prior at ρ = 0.5  

Spec disclaimer: research / decision-support; CIs are model belief.

---

## 2. Verification evidence

| Check | Location | Result (audit run) |
|---|---|---|
| Conjugate update / joint fit unit tests | `test_bayes.py` | PASS (suite) |
| Genetics-only HBRI identity vs legacy | `test_responder_index.py` | PASS |
| Multi-feature variance propagation | calibration + responder tests | PASS |
| BLUE fusion matched-ρ + fixed-ρ conservatism | `test_calibration.py` section 3 | PASS |
| Uncorrected ρ=0 under-coverage control | `test_calibration.py` | PASS (documents load-bearing correction) |
| Coverage band ~[0.90, 0.995] @ N=2000 MC | `test_calibration.py` | PASS |
| Evidence registry load/grade SD | `test_evidence.py` | PASS |
| Prediction wiring | `test_predictions.py` | PASS |
| **Aggregate** | listed files | **93 passed in 2.24s** |

---

## 3. What the calibration backtest does and does not prove

**Does prove (under synthetic truth):**

- If data are generated from the same Normal kinetics/noise model the code assumes, 95% intervals cover near nominally across genetics-only, multi-feature, and fused-prior regimes.  
- Correlation-aware fusion fixes double-counting under-coverage seen when ρ is ignored.

**Does not prove:**

- Real patient trajectories follow the generative model  
- Genetics weights are biologically true  
- Panel expected_pct or τ match reality  
- Clinical decisions improve  
- Interval coverage on human data  

---

## 4. Residual analytical risks (carry to trial)

| Risk | Mechanism | Trial mitigation |
|---|---|---|
| Non-Normal / heteroskedastic noise | Labs, adherence | Robust regression; report coverage empirically |
| Wrong τ | Approach too fast/slow | Sensitivity; secondary free τ fit exploratory only |
| Dose unmodeled | Single-dose cohort | Capture dose; gated dose module stays OFF |
| Cross-marker dependence ignored | Independent θ_k | Stay independent; don’t enable Σ |
| Changing cohort prior | LOO pool grows | Disable pooling for T0 primary |
| HealthKit proxy contamination | Extra likelihood | Flag in snapshot; sensitivity without HK |

---

## 5. Conclusion (Gate B technical)

Analytical software verification for the HBRI stack is **adequate to freeze a research VCC** for external validation, **conditional on** honesty labels and primary endpoint restriction. Simulation calibration is **necessary but not sufficient** for clinical efficacy of the predictor.
