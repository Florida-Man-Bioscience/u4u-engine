# IRB Determination Request — u4u-engine Pipeline Performance Validation (Tiers A & B)

**To:** UF Institutional Review Board (IRB-01, Gainesville HSC) / Exempt Auto-Determination tool, myIRB
**From:** [PI name, credentials], [department / Florida Man Bioscience affiliation]
**Date:** [submission date]
**Re:** Request for determination that the described analytical-validation activities are **Not Human Subjects Research** (Tier A) and **Exempt** (Tier B) under 45 CFR 46

> **Purpose of this memo.** This requests a written determination for two categories of pipeline *performance-testing* activity that do **not** involve intervention/interaction with living individuals or identifiable private information. It does **not** cover any prospective enrollment, identifiable data, or return of results — those are submitted separately as a full (Tier C) protocol. A companion roadmap is on file (`docs/irb-setup-plan.md`); the underlying validation science is detailed in `docs/clinical-validation-plan.md` §9–§12.

---

## 1. Background and purpose

The `u4u-engine` is a genomic analysis pipeline that ingests a genome file (VCF / array export / rsID list), annotates variants against public databases, and produces variant prioritization, pharmacogenomic (PGx) star-allele/diplotype calls, polygenic scores, and related outputs. The objective of the activities described here is purely **technical performance measurement of the software** — does the pipeline compute the correct answer when the correct answer is already known from an established reference standard.

The endpoints are software-accuracy metrics only: call concordance, sensitivity, specificity, precision (repeatability/reproducibility), and diplotype concordance versus reference truth sets. **No clinical claim is made, no participant is contacted, and no result is returned to any individual.**

---

## 2. Activity description

### Tier A — Analytical validation against reference materials
- **Inputs:** publicly available, de-identified reference materials and truth sets, specifically:
  - **NIST / Genome in a Bottle (GIAB)** reference samples (e.g., NA12878/HG001 and the HG002–HG007 set) and their high-confidence benchmark call sets;
  - **CDC GeT-RM** pharmacogenetic reference materials (consensus star-allele diplotypes for CYP2D6, CYP2C19, etc.) on **Coriell cell-line** samples;
  - public population reference data (e.g., 1000 Genomes) used solely as input genotypes with known coordinates.
- **Procedure:** run these files through the pipeline and compare outputs to the published benchmark/consensus calls; compute concordance and accuracy metrics.
- **No human subjects involvement:** the materials are **cell lines** and **de-identified public datasets**, not living individuals, and contain no identifiable private information.

### Tier B — Secondary analysis of existing, de-identified human data
- **Inputs:** **already-collected**, **de-identified or coded** genomic data and associated reference annotations (e.g., expert-panel ClinVar/ClinGen classifications, CPIC reference diplotypes; and, where applicable, banked/biobank or dbGaP datasets obtained under a Data Use Agreement).
- **Procedure:** compare pipeline interpretation/scoring and PGx-phenotype outputs to the established reference classification for the **same** records; compute concordance/calibration.
- **No identifiable private information:** the investigators receive data that is de-identified or coded such that the identity of individuals cannot readily be ascertained, and the investigators will not have access to the key. No re-identification will be attempted (45 CFR 46.102(e)(5)).

---

## 3. Regulatory basis for the requested determination

### 3.1 Tier A — Not Human Subjects Research
Under **45 CFR 46.102(e)(1)**, a "human subject" is a living individual about whom an investigator obtains (i) data through intervention or interaction, or (ii) identifiable private information. Tier A uses **cell-line reference materials and de-identified public benchmark data**; it involves **no living individuals, no interaction/intervention, and no identifiable private information.** It therefore **does not meet the definition of human-subjects research** and is **Not Human Subjects Research (NHSR).**

### 3.2 Tier B — Exempt (secondary research use of de-identified data)
To the extent Tier B uses existing human-derived data, it qualifies for exemption under **45 CFR 46.104(d)(4)** — secondary research use of **identifiable** private information/biospecimens where the information is recorded such that subjects cannot be readily identified and the investigator does not contact subjects or re-identify them. Because the data the investigators will handle is **de-identified/coded**, the activity is at most **Exempt category 4**, and may itself be NHSR if no identifiable private information is involved. *(UF mechanism: the Exempt Auto-Determination tool in myIRB; IRB 850 training.)*

---

## 4. Privacy, security, and scope limitations
- **No identifiable data** is requested, received, or generated under this determination. All inputs are de-identified, coded, or cell-line/public reference materials.
- **No return of results.** The pipeline is **not CLIA-certified**; no output will be returned to any individual for any clinical or personal purpose.
- **Data handling.** De-identified files are stored on [institution-approved storage]; any Data Use Agreement terms for banked datasets will be honored.
- **Scope boundary.** This request explicitly **excludes**: prospective recruitment, any identifiable genomic data, any administration of peptides or other interventions, and any return of results. Those activities, if pursued, will be submitted as a separate full IRB protocol (Tier C).

---

## 5. Conflict of interest disclosure
The investigator(s) [have / do not have] a financial or intellectual-property interest in the `u4u-engine` technology under study. Specifically, **[a UF Innovate patent disclosure exists on this pipeline]**. This interest has been / will be disclosed to the **UF Conflicts of Interest office (coi.ufl.edu)** and is noted here for the IRB's awareness. The activities in this request are non-interventional software-accuracy measurements against fixed external reference standards, which limits the influence of investigator interest on the outcome, but the disclosure is made in the interest of transparency.

---

## 6. Determination requested
1. That the **Tier A** activities (analytical validation on GIAB/GeT-RM/public reference materials) are **Not Human Subjects Research** under 45 CFR 46.102(e).
2. That the **Tier B** activities (secondary analysis of de-identified existing human data) are **Exempt** under 45 CFR 46.104(d)(4) (or NHSR if no identifiable private information is involved).

A written determination will be retained in the study file and cited in any resulting publication.

---

*Attachments to provide on submission: (a) list of specific reference datasets and accession IDs; (b) any Data Use Agreement(s) for banked data; (c) data-security description; (d) COI disclosure confirmation. Regulatory references: 45 CFR 46.102(e), 46.104(d)(4); UF HRPP / IRB-01; UF Exempt Auto-Determination tool.*
