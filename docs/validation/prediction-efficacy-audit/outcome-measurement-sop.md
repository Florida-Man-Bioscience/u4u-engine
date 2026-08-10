# Outcome Measurement SOP — Trial Biomarkers

**ID:** U4U-SOP-PRED-OUT-001  
**Version:** 0.1-DRAFT  
**Date:** 2026-07-15  

---

## 1. Primary markers

| Marker (exact engine name) | Population | Unit | Direction |
|---|---|---|---|
| `Body weight (GLP-1 RA)` | GLP-1 RA users | kg (preferred) or lb with unit recorded | decrease |
| `HbA1c (GLP-1 RA)` | Glycemic indication per protocol | % NGSP (or mmol/mol + conversion) | decrease |

**Critical:** Use **class-qualified** names so GLP-1 effect sizes do not bleed onto generic `Body weight` / `HbA1c` rows used by other peptides.

---

## 2. Time windows (**ratify**)

| Anchor | Target | Accept window |
|---|---|---|
| Baseline \(V_0\) | Day 0 / treatment start | −14 days to +3 days |
| Week 12 | 12 × 7 days from start | ±14 days |
| Week 24 | 24 × 7 days | ±14 days |

`treatment.start_date` in tracking must match clinic start-of-therapy date used for alignment.

---

## 3. Body weight procedure

1. Clinic calibrated scale preferred; same scale when possible.  
2. Light clothing, shoes off; time of day noted if available.  
3. Record: value, unit, modality (`clinic_scale` | `home_scale` | `other`), device id if any.  
4. Home scales: allowed as secondary; flag in analysis.  

---

## 4. HbA1c procedure

1. Certified lab assay; record lab name / method if known.  
2. Do not mix NGSP % and IFCC without conversion metadata.  
3. Point-of-care devices: allowed if method recorded; sensitivity analysis vs lab.  

---

## 5. Confounders to capture (minimum)

- Peptide name / molecule  
- Dose, unit, schedule, route  
- Branded vs compounded  
- Concurrent intensive lifestyle program (Y/N)  
- Missed-dose estimate (none / occasional / frequent)  
- Sex, birth year  

---

## 6. Secondary / exploratory markers

Grade B–D and uncited panel markers may be collected if clinics already order them; they are **not** primary SAP endpoints. Measurement SOPs for those can be site-standard with unit + date required.

---

## 7. Clinical anchors (recommended)

Even for prediction validation, co-collect when feasible:

- Waist circumference  
- Patient-reported outcomes relevant to indication  
- Serious AEs (AE-observation posture for unapproved peptides — see IRB plan)  

These do not replace primary biomarker endpoints but support surrogate honesty (F-11).
