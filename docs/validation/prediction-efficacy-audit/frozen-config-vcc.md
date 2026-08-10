# Frozen Configuration Candidate (VCC) — Prediction Engine

**VCC ID:** `vcc-prediction-pretrial-2026-07-15`  
**Status:** **CANDIDATE** — analytical tests green; Gate B incomplete until branch catch-up (F-14) + T0 snapshot eng (F-13) + human signatures  
**Freeze date (UTC):** 2026-07-15T14:09:19Z  
**Git commit:** `458aa2d73f0a576ee28353db631aa1fa9da368a2`  
**Branch note:** `main` was **behind origin/main by 6** at audit — re-run hashes after update before signing Gate B.

---

## 1. Scope of freeze

| Included | Excluded / must remain OFF |
|---|---|
| `engine/tracking/analysis.predict_response` | `DOSE_RESPONSE_ENABLED` → **False** |
| `bayes.py`, `responder_index.py`, `pooling.py` | `CROSS_BIOMARKER_ENABLED` → **False** |
| `genetics.py` catalog + `R_DELTA_SCALE=0.72` | Enabling gated stubs mid-trial |
| `data/biomarker_evidence.json` schema 1 | Live refit of genetics weights on trial data |
| Feature adapters as shipped | Synthetic genetics for enrolled subjects |
| Evidence-driven `relative_sd` | Conformal PGx coverage claims |

---

## 2. Content-addressed hashes (sha256)

| Artifact | sha256 |
|---|---|
| `data/biomarker_evidence.json` | `87f30badbf13c7cc03d1dfcf32f375c27a0f20b7f5c82c83ea82d41650a4eab7` |
| `engine/tracking/genetics.py` | `786c9c875e79835e4c03ced25c6a09a737112da76a6d2cba1b91bd119d9ad223` |
| `engine/tracking/bayes.py` | `216b676ad1d6dbb2f353516edfa6b14fcc84bf27767b1b34518375b6337dc297` |
| `engine/tracking/responder_index.py` | `d79125e8bf40b8162165de100ea8031a3756ca8d68d6fc8ba5983f32b461a919` |
| `engine/tracking/pooling.py` | `dfdb62cc31e29a288fd5fb6754e349b710eb1e80d729827b22481d69e42dc3ba` |
| `engine/tracking/biomarker_params.py` | `85219744214171664757b42ec17cc9426304de0ca01fb31a7a7ec8008df338ff` |
| `engine/tracking/analysis.py` | `c5d6fd3c79461c9261845561eaacb444ca8f353b102f7520f7dab7fca3bc67c6` |
| `docs/models/peptide-response-model.md` | `04a3d72bb597ddf8b6ce2fefa74d38decf76bfc0594e64f38024cb4046b307fd` |

Machine-readable copy: `data/validation/vcc-manifest-2026-07-15.json`.

---

## 3. Structural parameters (locked)

| Parameter | Value | Location |
|---|---|---|
| \( \Delta \) / `R_DELTA_SCALE` | 0.72 | `genetics.py` / `responder_index.py` |
| `GENETIC_COHORT_CORRELATION` ρ | 0.5 | `pooling.py` |
| `MIN_DONORS` | 3 | `pooling.py` |
| Genetics β | 1.0 (anchored) | HBRI contract |
| Non-genetic β default | 0 (ridge prior) | adapters |
| Primary snapshot pooling | **OFF recommended** | analysis firewall |
| Evidence uncited relative_sd | 0.20 | evidence JSON |
| Grade A/B/C/D default relative_sd | 0.10 / 0.15 / 0.22 / 0.30 | evidence JSON |

---

## 4. Feature adapters (inventory)

| Adapter module | Role at freeze |
|---|---|
| `genetics_adapter.py` | Anchored reference feature |
| `prs_adapter.py` | Fires if `patient_enrichment.prs_profile` present; β default 0 |
| `bpc157_adapter.py` | Fires if enrichment `bpc157`; β default 0 |
| `covariates_adapter.py` | Demographics; β default 0 |
| `healthkit_behavior_adapter.py` | Behaviour covariates; β default 0 |

HealthKit **proxy observations** may enter likelihood (higher noise scale) if subject mapped — document in T0 whether proxies present.

---

## 5. Analytical verification run (this audit)

```text
nix develop --command python -m pytest \
  tests/test_engine/test_tracking/test_calibration.py \
  tests/test_engine/test_tracking/test_responder_index.py \
  tests/test_engine/test_tracking/test_pooling.py \
  tests/test_engine/test_tracking/test_bayes.py \
  tests/test_engine/test_tracking/test_evidence.py \
  tests/test_engine/test_tracking/test_predictions.py -q
```

**Result (2026-07-15):** `93 passed in 2.24s`

Also recommended before Gate B sign:

```text
nix develop --command python -m pytest tests/test_engine/test_tracking/ -v
nix develop --command python -m engine.tracking.evidence_update validate
```

---

## 6. Environment variables affecting prediction

| Variable | Effect | Trial rule |
|---|---|---|
| `DATABASE_URL` | Postgres vs SQLite store | Dedicated trial DB; no seed force |
| `DATA_DIR` | Evidence / data paths | Pin to image path |
| `PGX_CONFORMAL_CALIBRATION` | PGx only | N/A to HBRI primary |
| `U4U_OIDC_*` | Auth mode | Prod OIDC on; seed blocked |
| `HEALTHKIT_REQUIRE_TOKEN` | HK auth | On in prod |

---

## 7. Determinism statement

Unit/integration tests pin identity contracts (genetics-only HBRI ≡ legacy; BLUE ρ=0 ≡ precision sum). Production determinism for identical inputs is **expected** for pure functions; floating order and DB donor sets can change population prior — hence **primary T0 disables pooling**.

---

## 8. Sign-off (Gate B)

| Role | Name | Date | Signature |
|---|---|---|---|
| Software / Clinical Bioinfo | _TBD_ | | |
| Biostatistician | _TBD_ | | |
| Medical Director | _TBD_ | | |

Re-issue VCC id if any hashed file changes.
