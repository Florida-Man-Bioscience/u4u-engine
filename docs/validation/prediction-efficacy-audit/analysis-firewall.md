# Analysis Firewall — Prospective Prediction Integrity

**ID:** U4U-SOP-PRED-FW-001  
**Version:** 0.1-DRAFT  
**Date:** 2026-07-15  
**Finding:** F-08, F-13  

---

## 1. Goal

Ensure primary predictors are **locked, time-stamped, and free of outcome leakage**.

---

## 2. T0 snapshot (required before enrollment claims)

At enrollment or treatment start:

1. Run `predict_response` in **prior-only mode**:
   - Prefer `n_measurements == 0` for post-baseline observations, **or**  
   - Engineering flag / offline computation that forces `likelihood=None` for the stored primary object  
2. **Disable population prior fusion** for primary (pass-through genetics/panel only) — engineering or operational control until API supports `pooling=off`.  
3. Persist immutable record:

```json
{
  "snapshot_id": "uuid",
  "snapshot_mode": "prior_only",
  "snapshot_at": "ISO-8601",
  "vcc_id": "vcc-prediction-pretrial-YYYY-MM-DD",
  "git_sha": "...",
  "config_hashes": {},
  "patient_id": "...",
  "peptide": "Semaglutide",
  "biomarker_name": "Body weight (GLP-1 RA)",
  "genome_build": "GRCh38",
  "genetics_source": "job:...",
  "pooling_enabled": false,
  "payload": { "...full predict_response JSON..." }
}
```

4. Never overwrite; amendments only via new snapshot_id with reason.

**Current gap:** API recomputes live (`GET .../predictions`) — **no immutable store** (F-13). Gate C requires either:

- **Eng:** `POST /tracking/patients/{id}/prediction-snapshots` insert-only table, or  
- **Ops:** export JSON to controlled trial EDC at T0 with hash in CRF  

---

## 3. Forbidden operations for primary analysis

| Action | Why |
|---|---|
| Refit genetics weights / β on trial outcomes | Data leakage / optimism |
| Enable dose-response or cross-biomarker | Unvalidated; breaks coverage contract |
| Use synthetic genetics | Invalid predictor provenance |
| Change VCC mid-enrollment without amendment | Moving target |
| Use post-baseline labs inside T0 predictor | Leakage |

---

## 4. Allowed secondary analyses

- Live posterior updates for monitoring UI (clearly labeled non-primary)  
- Exploratory model updates **after** primary lock and separate SAP section  
- Sensitivity recompute offline under alternate ρ / genetics-off using **stored T0 features** if raw inputs saved  

---

## 5. Blinding / influence

- Study predictions are **research-only**; clinicians must not be instructed to change therapy based on PEAP outputs.  
- Prefer that outcome abstractors do not view T0 predictions when entering labs (pragmatic open-label otherwise — document).  

---

## 6. Separation of demo and trial data

- Trial DB: production Postgres, OIDC on, `/tracking/seed` 403  
- No force-reseed  
- Demo patients excluded by source tag / label convention  
