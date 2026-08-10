# Model Monitoring Plan (Design-Now / Run During Trial)

**ID:** U4U-MON-PRED-001  
**Version:** 0.1-DRAFT  
**Date:** 2026-07-15  
**Aligns:** GMLP lifecycle, VMP §11.8 / §17  

---

## 1. Principles

- Primary analysis remains on **locked T0** snapshots.  
- Monitoring detects drift and data-quality failures; it does **not** silently retune the model.  
- Triggers open investigation / CAPA, not automatic weight updates.

---

## 2. Metrics to track (rolling)

| Metric | Cadence | Data source |
|---|---|---|
| Enrollment rate by site / peptide | Weekly | EDC |
| T0 snapshot completeness | Weekly | Snapshot store |
| Genome build reject rate | Weekly | Input QC log |
| Missing week-12 outcomes | Monthly | EDC |
| Branded vs compounded mix | Monthly | CRF |
| Rolling calibration slope (descriptive) | After N≥30 completers | Offline analysis |
| Interval coverage (descriptive) | After N≥30 | Offline |
| API error rate on `/predictions` | Continuous | Ops logs |

---

## 3. Trigger thresholds (**ratify**)

| Trigger | Action |
|---|---|
| Snapshot completeness < 95% of enrolled GLP-1 | Pause primary claims until remediated |
| Build unknown rate > 5% | Halt genomics-informed predictions |
| Coverage of 95% PI < 0.80 over last 50 completers | Biostat review; possible protocol amendment |
| Any production deploy of tracking code without VCC re-issue | Incident; re-map snapshots to version |

---

## 4. Change control

1. Propose change → impact analysis (does it affect T0 math?).  
2. If yes → new VCC, amendment if enrollment open, dual-run if needed.  
3. Gated modules (`dose_response`, `cross_biomarker`) require explicit data volume justification + new calibration backtest + Gate re-approval.

---

## 5. Post-trial

- Full performance report (TRIPOD+AI validation)  
- Decision: claim / no-claim / update model under new development protocol  
- Archive VCC + snapshots + analysis code  
