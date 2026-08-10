# Evidence & Prior Provenance Matrix

**Source:** `data/biomarker_evidence.json` (schema_version 1)  
**sha256:** `87f30badbf13c7cc03d1dfcf32f375c27a0f20b7f5c82c83ea82d41650a4eab7`  
**Panel size:** 23 peptides, **181** `BiomarkerMeasurement` rows in `engine/peptides/measurements.py`  
**Cited entries:** **8** biomarkers  

Honesty contract (`engine/tracking/evidence.py`): entry requires ≥1 retrieved DOI; uncited markers use `uncited_relative_sd = 0.20`.

---

## 1. Grade definitions

| Grade | Definition (registry) | Default relative_sd |
|---|---|---|
| A | Multiple human RCTs or meta-analysis; magnitude well established | 0.10 |
| B | ≥1 human RCT; direction firm, magnitude class/dose-approximate | 0.15 |
| C | Observational / open-label / soft magnitude | 0.22 |
| D | Preclinical only; human magnitude extrapolated | 0.30 |

---

## 2. Cited biomarker entries

| Biomarker | Grade | max_pct_change | rel_sd | Peptides | DOIs |
|---|---|---|---|---|---|
| **Body weight (GLP-1 RA)** | **A** | −0.13 | 0.10 | Semaglutide, Tirzepatide, Liraglutide | 10.1001/jama.2021.1831; 10.1001/jama.2021.23619; 10.1056/nejmoa2107519 |
| **HbA1c (GLP-1 RA)** | **A** | −0.18 | 0.10 | Semaglutide, Tirzepatide, Liraglutide | 10.2337/dc20-1815; 10.1056/nejmoa2107519 |
| Serum IGF-1 | B | +0.55 | 0.15 | Tesamorelin, CJC-1295, Ipamorelin, GHRP-2 | 10.1056/nejmoa072375; 10.1001/jama.292.2.210 |
| Serum IGFBP-3 | B | +0.40 | 0.15 | Tesamorelin, CJC-1295, Ipamorelin, GHRP-2 | 10.1210/jcem.85.11.6964; 10.1046/j.1365-2265.2003.01754.x |
| Lean body mass (DXA) | C | +0.05 | 0.22 | Tesamorelin, CJC-1295, Ipamorelin | 10.1056/nejmoa072375 |
| Absolute CD4+ T-lymphocyte count | C | +0.55 | 0.22 | Thymosin Alpha-1 | 10.1111/j.1365-2249.2003.02331.x; 10.1186/cc11932 |
| Serum VEGF | D | +0.45 | 0.30 | BPC-157 | 10.3389/fphar.2021.627533; 10.2147/dddt.s82030 |
| Plasma nitrite/nitrate (NOx) | D | +0.50 | 0.30 | BPC-157 | 10.1038/s41598-020-74022-y |

**Class-qualified GLP-1 markers do not apply to generic `Body weight` / `HbA1c` used by weaker peptides** (registry rationales).

---

## 3. Genetics prior provenance

| Element | Provenance | Clinical use |
|---|---|---|
| `VARIANT_CATALOG` peptide effect weights | **Synthetic / stylised** (`genetics.py` docstring) | Research only; sensitivity genetics-off |
| Profile `source=synthetic` | RNG demo | **Forbidden** for trial subjects |
| Profile `source=job:{id}` | Built from analyze job rsIDs via catalog weights | Trial-allowed **if** labeled synthetic weights |
| η scale Δ=0.72 | Model design constant | Locked in VCC |

---

## 4. Trial binding rules

| Evidence class | Trial role |
|---|---|
| Grade A | **Primary endpoints** |
| Grade B | Secondary / exploratory strata |
| Grade C–D | Exploratory only; no product claim |
| Uncited (~173 measurements) | Not primary; wide prior only |

---

## 5. Valid clinical association (IMDRF)

| Association | Status |
|---|---|
| GLP-1 RA → weight / HbA1c change | **Strong** (label + RCTs cited) |
| Software genetics → differential response | **Unestablished** (synthetic weights) |
| HBRI θ prediction → observed trajectory | **Under test** (this study) |
| BPC-157 → VEGF/NOx in humans | **Weak / preclinical** |

---

## 6. Curator commands

```bash
nix develop --command python -m engine.tracking.evidence_update validate
nix develop --command python -m engine.tracking.evidence_update show
```

Do not add grades without real DOIs (honesty contract).
