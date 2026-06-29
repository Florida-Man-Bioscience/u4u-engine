# IRB Determination Request — u4u-engine Pipeline Performance Validation (Tiers A & B)

**To:** UF Institutional Review Board (IRB[^irb]-01, Gainesville HSC[^hsc]) / Exempt Auto-Determination tool, myIRB[^myirb]
**From:** [PI[^pi] name, credentials], [department / Florida Man Bioscience affiliation]
**Date:** [submission date]
**Re:** Request for determination that the described analytical-validation activities are **Not Human Subjects Research**[^nhsr] (Tier A) and **Exempt**[^exempt] (Tier B) under 45 CFR 46[^cfr46]

> **Purpose of this memo.** This requests a written determination for two categories of pipeline *performance-testing* activity that do **not** involve intervention/interaction with living individuals or identifiable private information. It does **not** cover any prospective enrollment, identifiable data, or return of results — those are submitted separately as a full (Tier C) protocol. A companion roadmap is on file (`docs/irb-setup-plan.md`); the underlying validation science is detailed in `docs/clinical-validation-plan.md` §9–§12.

---

## 1. Background and purpose

The `u4u-engine` is a genomic analysis pipeline that ingests a genome file (VCF / array export / rsID list), annotates variants against public databases, and produces variant prioritization, pharmacogenomic (PGx)[^pgx] star-allele[^starallele]/diplotype[^diplotype] calls, polygenic scores[^prs], and related outputs. The objective of the activities described here is purely **technical performance measurement of the software** — does the pipeline compute the correct answer when the correct answer is already known from an established reference standard[^refstandard].

The endpoints are software-accuracy metrics only: call concordance[^concordance], sensitivity, specificity, precision (repeatability/reproducibility)[^sensspec], and diplotype concordance versus reference truth sets[^truthset]. **No clinical claim is made, no participant is contacted, and no result is returned to any individual.**

---

## 2. Activity description

### Tier A — Analytical validation against reference materials
- **Inputs:** publicly available, de-identified reference materials and truth sets, specifically:
  - **NIST / Genome in a Bottle (GIAB)**[^giab] reference samples (e.g., NA12878/HG001[^na12878] and the HG002–HG007 set) and their high-confidence benchmark call sets;
  - **CDC GeT-RM**[^getrm] pharmacogenetic reference materials (consensus star-allele diplotypes for CYP2D6, CYP2C19[^cyp], etc.) on **Coriell cell-line**[^coriell] samples;
  - public population reference data (e.g., 1000 Genomes[^kgp]) used solely as input genotypes with known coordinates.
- **Procedure:** run these files through the pipeline and compare outputs to the published benchmark/consensus calls; compute concordance and accuracy metrics.
- **No human subjects involvement:** the materials are **cell lines** and **de-identified public datasets**, not living individuals, and contain no identifiable private information.

### Tier B — Secondary analysis of existing, de-identified human data
- **Inputs:** **already-collected**, **de-identified or coded**[^deidentified] genomic data and associated reference annotations (e.g., expert-panel ClinVar/ClinGen[^clingen] classifications, CPIC[^cpic] reference diplotypes; and, where applicable, banked/biobank or dbGaP[^dbgap] datasets obtained under a Data Use Agreement[^dua]).
- **Procedure:** compare pipeline interpretation/scoring and PGx-phenotype outputs to the established reference classification for the **same** records; compute concordance/calibration[^calibration].
- **No identifiable private information:** the investigators receive data that is de-identified or coded such that the identity of individuals cannot readily be ascertained, and the investigators will not have access to the key. No re-identification will be attempted (45 CFR 46.102(e)(5)).

---

## 3. Regulatory basis for the requested determination

### 3.1 Tier A — Not Human Subjects Research
Under **45 CFR 46.102(e)(1)**, a "human subject" is a living individual about whom an investigator obtains (i) data through intervention or interaction, or (ii) identifiable private information. Tier A uses **cell-line reference materials and de-identified public benchmark data**; it involves **no living individuals, no interaction/intervention, and no identifiable private information.** It therefore **does not meet the definition of human-subjects research** and is **Not Human Subjects Research (NHSR).**

### 3.2 Tier B — Exempt (secondary research use of de-identified data)
To the extent Tier B uses existing human-derived data, it qualifies for exemption under **45 CFR 46.104(d)(4)** — secondary research use of **identifiable** private information/biospecimens where the information is recorded such that subjects cannot be readily identified and the investigator does not contact subjects or re-identify them. Because the data the investigators will handle is **de-identified/coded**, the activity is at most **Exempt category 4**[^exempt4], and may itself be NHSR if no identifiable private information is involved. *(UF mechanism: the Exempt Auto-Determination tool in myIRB; IRB 850 training[^irb850].)*

---

## 4. Privacy, security, and scope limitations
- **No identifiable data** is requested, received, or generated under this determination. All inputs are de-identified, coded, or cell-line/public reference materials.
- **No return of results.** The pipeline is **not CLIA-certified**[^clia]; no output will be returned to any individual for any clinical or personal purpose.
- **Data handling.** De-identified files are stored on [institution-approved storage]; any Data Use Agreement terms for banked datasets will be honored.
- **Scope boundary.** This request explicitly **excludes**: prospective recruitment, any identifiable genomic data, any administration of peptides or other interventions, and any return of results. Those activities, if pursued, will be submitted as a separate full IRB protocol (Tier C).

---

## 5. Conflict of interest disclosure
The investigator(s) [have / do not have] a financial or intellectual-property interest in the `u4u-engine` technology under study. Specifically, **[a UF Innovate[^ufinnovate] patent disclosure exists on this pipeline]**. This interest has been / will be disclosed to the **UF Conflicts of Interest[^coi] office (coi.ufl.edu)** and is noted here for the IRB's awareness. The activities in this request are non-interventional software-accuracy measurements against fixed external reference standards, which limits the influence of investigator interest on the outcome, but the disclosure is made in the interest of transparency.

---

## 6. Determination requested
1. That the **Tier A** activities (analytical validation on GIAB/GeT-RM/public reference materials) are **Not Human Subjects Research** under 45 CFR 46.102(e).
2. That the **Tier B** activities (secondary analysis of de-identified existing human data) are **Exempt** under 45 CFR 46.104(d)(4) (or NHSR if no identifiable private information is involved).

A written determination will be retained in the study file and cited in any resulting publication.

---

*Attachments to provide on submission: (a) list of specific reference datasets and accession IDs[^accession]; (b) any Data Use Agreement(s) for banked data; (c) data-security description; (d) COI disclosure confirmation. Regulatory references: 45 CFR 46.102(e), 46.104(d)(4); UF HRPP[^hrpp] / IRB-01; UF Exempt Auto-Determination tool.*

---

## Footnotes

[^irb]: **IRB (Institutional Review Board)** — a committee that reviews and oversees research involving human subjects to protect their rights and welfare; required before such research begins.
[^hsc]: **HSC (Health Science Center)** — the University of Florida's health-sciences campus in Gainesville; IRB-01 is the IRB serving it.
[^myirb]: **myIRB** — UF's online IRB submission and review system, including an "Exempt Auto-Determination" self-service tool.
[^pi]: **PI (Principal Investigator)** — the researcher who holds primary responsibility for the conduct of a study.
[^nhsr]: **NHSR (Not Human Subjects Research)** — an official determination that an activity does not meet the regulatory definition of human-subjects research, so IRB approval is not required.
[^exempt]: **Exempt** — a category of human-subjects research that, while technically research, is low-risk enough to be exempt from full IRB review (but still requires a determination).
[^cfr46]: **45 CFR 46** — the U.S. federal regulation ("the Common Rule") governing the protection of human research subjects; its subsections define key terms and exemption categories.
[^pgx]: **PGx (Pharmacogenomics)** — the study of how genetic variation affects an individual's response to drugs (metabolism, efficacy, toxicity).
[^starallele]: **Star allele (\*-allele)** — standardized nomenclature (e.g. CYP2D6\*4) naming a specific haplotype of a pharmacogene that defines its functional status.
[^diplotype]: **Diplotype** — the pair of star alleles a person carries (one per chromosome), e.g. CYP2C19\*1/\*2; it determines the predicted metabolizer phenotype.
[^prs]: **Polygenic score (PRS)** — a single score aggregating many variants' small effects to estimate genetic predisposition to a trait.
[^refstandard]: **Reference standard / truth set** — an independently established, trusted set of "correct" answers against which the pipeline's output is graded.
[^concordance]: **Concordance** — the rate at which the pipeline's calls agree with the reference truth (exact-match agreement).
[^sensspec]: **Sensitivity / specificity / precision** — accuracy metrics: sensitivity = fraction of true positives correctly detected; specificity = fraction of true negatives correctly excluded; precision = fraction of positive calls that are correct. Repeatability (same run conditions) and reproducibility (varied conditions) measure consistency.
[^truthset]: **Truth set** — the curated set of known-correct calls for a reference sample, used as the gold standard for comparison.
[^giab]: **NIST / Genome in a Bottle (GIAB)** — a NIST-led consortium that produces extensively characterized human reference genomes with high-confidence "benchmark" variant calls for validating pipelines.
[^na12878]: **NA12878 / HG001, HG002–HG007** — specific GIAB reference individuals/cell lines with published benchmark call sets; standard samples for analytical validation.
[^getrm]: **CDC GeT-RM** — the CDC's Genetic Testing Reference Materials program, which provides consensus pharmacogenetic genotypes for reference cell lines.
[^cyp]: **CYP2D6 / CYP2C19** — cytochrome P450 drug-metabolizing enzyme genes; among the most clinically important pharmacogenes.
[^coriell]: **Coriell cell line** — an immortalized cell line from the Coriell Institute biorepository; a renewable, de-identified DNA source (not a living individual).
[^kgp]: **1000 Genomes** — a public catalog of human genetic variation across populations, usable as input genotypes with known coordinates.
[^deidentified]: **De-identified / coded** — data stripped of direct identifiers; "coded" means a key linking data to identity exists but is held separately and not accessible to the investigators.
[^clingen]: **ClinVar / ClinGen** — NCBI's ClinVar archives variant–clinical-significance assertions; ClinGen is an NIH expert-curation effort that produces authoritative variant classifications.
[^cpic]: **CPIC (Clinical Pharmacogenetics Implementation Consortium)** — publishes peer-reviewed guidelines mapping pharmacogene diplotypes to phenotypes and drug-dosing recommendations.
[^dbgap]: **dbGaP** — NIH's database of Genotypes and Phenotypes; controlled-access human datasets released only under a Data Use Agreement.
[^dua]: **Data Use Agreement (DUA)** — a contract governing how a restricted dataset may be accessed, used, and protected.
[^calibration]: **Calibration** — how well predicted probabilities match observed frequencies (e.g. events predicted at 70% actually occur ~70% of the time).
[^exempt4]: **Exempt category 4** — the 45 CFR 46.104(d)(4) exemption for secondary research use of already-collected, non-identifiable data/biospecimens.
[^irb850]: **IRB 850 training** — a UF research-compliance training module required for investigators handling exempt/secondary-use protocols.
[^clia]: **CLIA-certified** — holding the federal Clinical Laboratory Improvement Amendments certification required to return clinical test results to patients; the pipeline lacks it, so results cannot be returned.
[^ufinnovate]: **UF Innovate** — the University of Florida's technology-transfer/commercialization office, which manages patents/inventions; a patent disclosure there creates a financial conflict of interest to declare.
[^coi]: **COI (Conflict of Interest)** — a financial or personal interest that could bias research; must be disclosed and managed (here via UF's COI office at coi.ufl.edu).
[^accession]: **Accession ID** — a stable identifier assigned to a dataset/sample in a public repository, used to cite exactly which records were analyzed.
[^hrpp]: **HRPP (Human Research Protection Program)** — the institution-wide program (of which the IRB is part) responsible for protecting human research participants.
