# Transparency Pack — Plain-Language Prediction Disclosure

**Purpose:** FDA CDS–style independent review material + trial honesty labeling  
**Date:** 2026-07-15  

---

## 1. Master disclosure (paste into protocol, consent, UI footer)

**What this software does**  
It estimates a research “response trajectory” for selected biomarkers under peptide therapy you (or your clinician) already chose. It combines a literature-based expected effect size with an optional genetic modifier and updates as new measurements arrive.

**What it does not do**  
It does **not** diagnose disease, prescribe medication, prove that a peptide works, or replace clinical judgment. It is **not** a validated clinical diagnostic device in its current state.

**Who it is for (research)**  
Adults in an IRB-approved observational study of prediction accuracy, or users exploring research tooling with clear non-clinical labeling.

**Inputs**  
Biomarker panel selection; optional genetic profile (from a genome file); optional enrichment (PRS, wearables); treatment start date; serial measurements.

**Algorithm (plain language)**  
A Bayesian model predicts the fractional change from baseline at plateau, with uncertainty bands. Genetic weights in the current version are **research hypotheses (synthetic catalog weights)**, not established polygenic scores for peptide response. Prior uncertainty is tighter when human RCT evidence grades are higher (e.g. GLP-1 weight and HbA1c).

**Validation status**  
- Software unit tests and **simulation** calibration: performed on locked version (see VCC).  
- **Human external validation:** pending / ongoing observational study.  
- Until that study completes and is reviewed, outputs are **research-only**.

**Limitations**  
Ancestry transfer unknown; dose–response not modeled; many biomarkers lack strong evidence; intervals may be miscalibrated in real patients; clinic population may not match yours.

---

## 2. Surface-specific lines

### Tracking chart (`/tracking`)

> Research prediction model (VCC: …). 95% bands reflect model uncertainty, not guaranteed coverage for every patient. Not for clinical decision-making.

### Prior-only / T0

> Baseline genetic/panel prior only — no post-treatment labs used in this snapshot.

### Peptide tier list (results)

> Pathway-overlap labels for investigational compounds are **not** proven efficacy. FDA-approved drug information does not mean genotype guarantees response.

### BPC-157 composite

> Experimental research score; not a validated responder test.

### PGx conformal

> Prediction set uncalibrated unless a validated calibration file is loaded; no coverage guarantee.

---

## 3. HCP independent-review checklist

1. Intended use & population stated?  
2. Required inputs listed?  
3. Algorithm class (Bayesian + evidence grades + synthetic genetics caveat) clear?  
4. Validation status (simulation vs human) clear?  
5. Limitations & subgroups not evaluated stated?  
6. Can the HCP ignore the tool without system coercion?  

If any answer is no, do not expose that surface in the study UI.
