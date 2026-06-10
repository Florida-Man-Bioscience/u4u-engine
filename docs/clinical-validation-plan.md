# Clinical Validation Master Plan — U4U / PeptidIQ Genomics-to-Peptide-Therapy Pipeline

**Document type:** Validation Master Plan (VMP) and Clinical Validation Protocol
**System under validation:** `u4u-engine` (a.k.a. PeptidIQ / PeptOdyssey), the genomic variant analysis and peptide-therapy recommendation pipeline in this repository
**Status of this document:** DRAFT v0.1 — planning artifact. This is a *plan for what would be required*; it is **not** a statement that the system is validated.
**Prepared in response to:** "A thoroughly documented plan for what would be required in order to validate this pipeline to the point where it is rigorously tested enough for clinical use."

---

> **READ THIS FIRST — Current-state safety statement.**
> As of the commit on which this plan was authored, the `u4u-engine` pipeline is a **research/prototype system**. It contains components that are explicitly self-described in the source code as *speculative*, *stylised*, *synthetic*, or *not validated* (see the BPC-157 predictor disclaimer in `engine/annotators/bpc157_predictor.py`, the "stylised, not pulled from any GWAS" admission in `engine/tracking/genetics.py`, and the synthetic conformal calibration default in `engine/pgx/hgnn/conformal.py`). The system has **no analytical validation, no clinical validation, and no quality management system** of record. It **must not be used to make, support, or influence clinical decisions for real patients** in its current state. This document describes the substantial body of work required to change that.

---

## Document Control

| Field | Value |
|---|---|
| Document title | Clinical Validation Master Plan — U4U / PeptidIQ Pipeline |
| Document ID | U4U-VMP-001 |
| Version | 0.1 (DRAFT) |
| Classification | Internal — Regulatory / Quality |
| Owner | (To be assigned — see §18, Medical Director / Quality Lead) |
| Status | Planning draft, not approved |
| Supersedes | None |

### Approval table (to be completed when this plan is adopted)

| Role | Name | Responsibility | Signature | Date |
|---|---|---|---|---|
| Sponsor / Executive | _TBD_ | Accountable for go/no-go and funding | | |
| Medical Director (licensed physician) | _TBD_ | Clinical accountability, intended-use sign-off | | |
| Laboratory Director (CLIA, if applicable) | _TBD_ | Analytical validation oversight | | |
| Quality / Regulatory Lead | _TBD_ | QMS, regulatory strategy | | |
| Clinical Bioinformatics Lead | _TBD_ | Pipeline analytical validation | | |
| Biostatistician | _TBD_ | Statistical analysis plan, model validation | | |
| Data Protection / Security Officer | _TBD_ | HIPAA, security, privacy | | |
| Software Engineering Lead | _TBD_ | IEC 62304 lifecycle, V&V | | |

### Revision history

| Version | Date | Author | Summary of change |
|---|---|---|---|
| 0.1 | 2026-06-10 | Validation planning | Initial draft authored against the as-built codebase |

### Distribution

This document is intended for the engineering, clinical, quality, and regulatory stakeholders of the U4U platform, and for any external auditor, IRB, notified body, or regulator who needs to understand the validation posture and roadmap.

---

## Table of Contents

0. Executive Summary
1. Introduction, Purpose, and the Three Pillars of Validation
2. System Description (As-Built)
3. Intended Use and Regulatory Classification
4. Applicable Standards and Frameworks
5. Gap Analysis — Current State vs. Clinical-Grade
6. Quality Management System Prerequisites
7. Risk Management (ISO 14971)
8. Software Verification and Validation (IEC 62304 / GAMP 5 / 21 CFR Part 11)
9. Analytical Validation of the Genomic Pipeline
10. Clinical Validation of Interpretation and Scoring
11. Clinical Validation of the Predictive Models
12. Clinical Utility and Evidence Generation
13. Data Management, Privacy, and Security
14. Human Factors, Labeling, and Results Communication
15. Bias, Equity, and Generalizability
16. Statistical Analysis Plan
17. Post-Market Surveillance and Change Control
18. Governance, Ethics, and Oversight
19. Validation Execution Plan — Phases, Timeline, Resources, Cost
20. Acceptance Criteria Master Table
- Appendix A — Requirements Traceability Matrix (template)
- Appendix B — Test Case Catalog (template and seed cases)
- Appendix C — Reference Materials and Truth Sets
- Appendix D — Hazard Analysis Register (worked entries)
- Appendix E — Module Validation Status Register
- Appendix F — Glossary
- Appendix G — References and Standards

---

## 0. Executive Summary

### 0.1 What this system does today

The `u4u-engine` ingests a consumer or clinical genome file (VCF, 23andMe text export, rsID list, or CSV), runs it through a ten-stage annotation pipeline (`engine/pipeline.py`), and emits, for each detected variant, a clinical-priority score and tier, plain-English summaries, and a set of downstream "interpretation" products. Those products go well beyond variant annotation. They include:

- **Polygenic risk scores (PRS)** for complex traits (`engine/annotators/prs_calculator.py`);
- **Pharmacogenomic (PGx) drug-response predictions**, including CYP star-allele diplotype calling, CPIC dosing recommendations, an "HGNN" graph-model path, and **conformal prediction sets** (`engine/pgx/`);
- **Peptide-therapy efficacy "recommendations"** with named tiers such as "Strong Fit" and "Likely Reduced" (`engine/annotators/peptide_mapper.py`);
- A dedicated **BPC-157 response predictor** (`engine/annotators/bpc157_predictor.py`);
- **Receptor expression / isoform predictions** (`engine/annotators/receptor_mapper.py`);
- **Longitudinal biomarker tracking with a Bayesian genetic-prior model** (`engine/tracking/`);
- Patient-facing, clinician-printable **HTML "dossiers"** that present a "Predicted Efficacy" tier and dosing context (`engine/dossier_generator.py`, `dossier_notes.md`).

The stated deployment intent (from `dossier_notes.md`) is that a clinician prints the dossier, reviews it with the patient in clinic, and sends it home with the patient as a rationale for the proposed peptide therapy — i.e., the output is used as **clinical decision support that recommends a therapy and contextualizes dosing.**

### 0.2 The central finding

The pipeline is an impressive engineering prototype, but it is **categorically not ready for clinical use, and the distance to clinical readiness is large and structural, not cosmetic.** The gap is not "add a few tests." It spans every one of the three pillars of diagnostic validation:

1. **Analytical validity** — Does the pipeline correctly determine what is in the genome (variants, genotypes, star alleles, repeat lengths)? *Today: unverified, with at least one latent correctness defect that can corrupt every downstream result — see §0.3.*
2. **Clinical validity** — Do the pipeline's calls correctly predict a clinically meaningful state (disease risk, drug phenotype, therapy response)? *Today: unestablished; several models are built on hand-curated or admittedly synthetic weights with no outcome data.*
3. **Clinical utility** — Does using the pipeline improve patient outcomes or decisions versus not using it? *Today: not studied.*

On top of these sit the system-level prerequisites for any clinical software: a **quality management system**, **risk management**, **software lifecycle controls**, **privacy/security controls**, **human-factors validation**, and **regulatory classification** — none of which currently exist in the repository.

### 0.3 The single most urgent technical defect: silent genome-build assumption

Every external annotation call in the pipeline (Ensembl VEP, ClinVar, gnomAD, MyVariant, ExpansionHunter) **implicitly assumes GRCh38/hg38 coordinates**, and **nothing in `engine/validators.py`, `engine/parsers.py`, or anywhere else detects or records the genome build of the uploaded file.** A very large fraction of real-world consumer genotyping data (including most historical 23andMe and AncestryDNA exports) and a large fraction of clinical VCFs are on **GRCh37/hg19**. If such a file is uploaded, its coordinates will be silently interpreted as GRCh38. The result is not a graceful failure — it is **confidently wrong annotation at every position**, which then flows into scoring, tiering, PRS, PGx, peptide recommendations, and the patient-facing dossier. This is a "wrong patient / wrong result" class hazard and is treated as a **launch-blocking defect** in this plan (Hazard H-01, Appendix D).

### 0.4 Components that cannot be "validated" without first being rebuilt

Some modules are not merely unvalidated — their current implementation is incompatible with a clinical claim and must be re-engineered before validation is even meaningful:

- **The variant scoring model** (`engine/scoring.py`) uses arbitrary integer point weights (ClinVar pathogenic `+1000`, missense `+50`, "absent in gnomAD" `+30`, etc.) and detects "autosomal recessive" by **substring-matching the words "recessive"/"biallelic" in free-text disease names.** This is a heuristic ranking, not an ACMG/AMP variant classification, and must not be presented as clinical significance.
- **The conformal predictor** (`engine/pgx/hgnn/conformal.py`) ships a **synthetic default calibration set** (`_DEFAULT_CAL_SCORES`) that the code itself comments is only "roughly drawn from" a distribution; the real calibration file does not exist, and the HGNN path is hard-disabled in favor of a `rule_based_fallback`. A conformal "guarantee" computed on invented calibration data **provides no statistical guarantee at all.**
- **The Bayesian tracking priors** (`engine/tracking/genetics.py`) are, per the module's own docstring, **"synthetic test data — the effect weights are stylised, not pulled from any GWAS."**
- **The BPC-157 and peptide-response predictors** map variants to "responder tiers" for compounds that are, by the project's own README and seed data, **not FDA-approved and supported only by preclinical/rodent data.** No genetic predictor of response to these compounds has ever been validated in humans; therefore the *prediction itself* cannot currently be made clinically valid — only honestly labeled as exploratory/non-clinical.

### 0.5 The peptide-evidence problem sits underneath everything

Even a perfectly engineered, analytically flawless pipeline cannot manufacture clinical evidence that does not exist in the world. The therapies the system recommends — BPC-157, TB-500, Epithalon, Semax, GHK-Cu, Argireline, SNAP-8, and similar — are predominantly **investigational, off-label, compounded, or research-only**, with little or no randomized human efficacy/safety data. A validation program can make the *software* trustworthy (it computes what it claims, reproducibly, safely, privately). It **cannot, by itself, make "this peptide will help this patient" a clinically valid claim**; that requires prospective human trials of the therapies, which is a separate, much larger, multi-year clinical-research undertaking. This plan is explicit about that boundary (see §12.4).

### 0.6 Recommended posture and phased path

This plan recommends the organization **explicitly decide its regulatory identity first** (the roadmap already flags this open decision: "info platform vs. medical device"), because that decision drives everything downstream. It then lays out a phased program:

- **Phase 0 — Containment & honest labeling (weeks):** Fix the genome-build hazard or hard-block non-GRCh38 input; gate or remove patient-facing efficacy claims for investigational compounds; lock down the API (authentication, PHI handling); freeze a versioned, deterministic pipeline.
- **Phase 1 — Foundations (3–6 months):** Stand up a QMS, risk management file, requirements/traceability, software V&V to IEC 62304, and security/privacy controls.
- **Phase 2 — Analytical validation (6–12 months):** Validate parsing, build handling, QC, annotation concordance, star-allele and STR calling against reference materials (GIAB, GeT-RM).
- **Phase 3 — Clinical validation of established claims (12–24 months):** Replace heuristic scoring with ACMG/AMP classification; validate PGx against CPIC and reference diplotypes; validate PRS against the PGS Catalog standards and independent cohorts.
- **Phase 4 — Investigational claims (multi-year, research track):** Generate genuine human evidence for the peptide-response and biomarker models, or permanently keep them out of clinical scope.

The remainder of this document specifies, in detail and grounded in the actual code, what each of these entails: the standards, the study designs, the acceptance criteria, the sample sizes, the reference materials, the documentation, and the governance.

---

## 1. Introduction, Purpose, and the Three Pillars of Validation

### 1.1 Background

The U4U platform analyzes personal genomic data to inform personalized peptide therapy in (per `dossier_notes.md`) a "boutique clinic" setting. The canonical example patient described in the design notes is "a 56-year-old woman who wants to (1) lose weight, (2) reduce inflammation in her osteoarthritic knees, and (3) reduce wrinkles." The dossier is designed to be "printed out by the clinician in clinic who will talk with the patient about it" and "go home with the patient." That is a clinical-decision-support use, and it is the use this validation plan assumes unless and until the organization formally adopts a narrower, non-clinical intended use (see §3).

The engine itself is a standalone Python package (`engine/`, ~11,000 lines) callable via `run_pipeline()`, wrapped by a FastAPI service (`api.py`) and a Next.js frontend (`frontend/`). It calls a number of external biological databases at runtime.

### 1.2 Purpose of this plan

This Validation Master Plan defines the complete set of activities, evidence, documentation, acceptance criteria, and governance required to take the pipeline from its current prototype state to a state where it is "rigorously tested enough for clinical use." It is written to be usable as:

- a **gap analysis** that an executive or investor can use to understand scope, risk, and cost;
- a **roadmap** the engineering and clinical teams can execute against;
- a **protocol skeleton** that the quality/regulatory function can mature into formal, controlled SOPs and validation protocols;
- a **due-diligence artifact** for an auditor, IRB, notified body, or regulator.

Nothing in this document should be read as asserting that any part of the system is currently validated. Where the document uses the present tense to describe the system ("the scorer assigns +1000…"), it is describing the as-built code, not endorsing it.

### 1.3 The three pillars: analytical validity, clinical validity, clinical utility

Genomic-medicine validation is conventionally decomposed into three questions (the **ACCE framework** — Analytic validity, Clinical validity, Clinical utility, and associated Ethical/legal/social implications — and the closely related CDC/EGAPP and ACMG frameworks):

1. **Analytical validity** asks: *given a specimen, does the assay/pipeline accurately and reproducibly measure what it claims to measure?* For this system that means: does it correctly parse the file, determine the genome build, call genotypes, resolve rsIDs, annotate consequence/ClinVar/gnomAD correctly, call star-allele diplotypes, and call STR repeat lengths? Analytical validity is measured with **accuracy, precision (repeatability/reproducibility), analytical sensitivity and specificity, limit of detection, and robustness** against truth sets.

2. **Clinical validity** asks: *does the measured result correctly identify or predict the clinical condition or phenotype of interest?* For this system: does a "pathogenic" tier correspond to true pathogenicity per expert standards; does a predicted CYP2C19 "poor metabolizer" phenotype predict the real metabolic phenotype; does a PRS decile predict trait risk in the intended population; does a "Strong Fit" peptide tier predict therapy response? Clinical validity is measured with **clinical sensitivity/specificity, positive/negative predictive value, odds/hazard ratios, calibration, and discrimination (AUC/C-index)** against clinical reference standards.

3. **Clinical utility** asks: *does using the test change management in a way that improves health outcomes (or other agreed endpoints) relative to not using it?* This is the highest bar and typically requires prospective, comparative study.

A system can be analytically valid but clinically invalid (it measures the variant correctly, but the variant does not predict anything useful). It can be clinically valid but lack utility (the prediction is correct but does not change what anyone does, or changes it without benefit). **All three are required for a defensible clinical claim, and they must be validated in that order**, because clinical and utility studies are meaningless if the underlying measurement is not analytically sound.

### 1.4 Verification vs. validation

Throughout, this plan distinguishes:

- **Verification** — "did we build the thing right?": the software meets its specified requirements (unit/integration/system tests, traceability). Governed by IEC 62304 and GAMP 5.
- **Validation** — "did we build the right thing?": the system, in its intended-use environment, with intended users, on intended specimens, produces results fit for the intended clinical purpose. Encompasses analytical validation, clinical validation, and human-factors validation.

Both are required. The current repository has a partial verification story (a `pytest` suite and CI) and **no validation story at all.**

### 1.5 How to read this document

§2–§5 establish *what the system is* and *how far it is from clinical-grade*. §6–§8 cover the *system-level prerequisites* (quality, risk, software). §9–§12 are the *scientific heart*: analytical validation, interpretation/scoring validation, predictive-model validation, and clinical-utility evidence. §13–§18 cover *privacy/security, human factors, equity, statistics, surveillance, and governance*. §19–§20 and the appendices provide the *execution plan, acceptance criteria, and working templates*.

---

## 2. System Description (As-Built)

A validation program can only validate a *defined, frozen* system. This section documents the system as it exists in the repository so that the configuration under validation is unambiguous. (Establishing a formally version-controlled, frozen "validated configuration" is itself a deliverable — see §8.)

### 2.1 High-level architecture

| Layer | Component | Location | Role |
|---|---|---|---|
| Frontend | Next.js app | `frontend/` | File upload, progress, results/dossier display, tracking UI |
| API | FastAPI service | `api.py` | Async job queue; `/analyze`, `/jobs/{id}`, dossier/PGx/drug/regulatory endpoints |
| Engine | Python package | `engine/` | The `run_pipeline()` analysis pipeline and all annotators/models |
| Data | rsID filters, BED, caches, condition library | `data/` | ACMG81 rsIDs, peptide gene BED, SQLite caches, condition library spreadsheet |
| External | Ensembl VEP, NCBI ClinVar, gnomAD, MyVariant, UniProt, PharmGKB, GWAS Catalog, KEGG, openFDA, ClinicalTrials.gov, Federal Register | network | Runtime annotation and regulatory enrichment |

### 2.2 Pipeline data flow (`engine/pipeline.py`)

`run_pipeline(file_bytes, filename, …)` executes the following ordered stages:

1. **Validate** (`validators.validate_file_bytes`) — size ≤ 100 MB, VCF magic header, UTF-8.
2. **Parse** (`parsers.parse_file`) — VCF / 23andMe / rsID-list / CSV → variant dicts.
3. **Quality filter** (`quality_filter.apply_quality_filter`) — drop hom-ref, failed calls (`--`/`NN`/`.`), low GQ/DP, indels.
4. **Panel/whitelist filter** (`filters.filter_variants`, `filter_variants_by_bed`) — restrict to ACMG81/pharma/carrier rsIDs and/or a BED region (`data/peptide_genes.bed`).
5. **rsID resolution** (`rsid_resolver.resolve_rsids`) — Ensembl REST: rsID → coordinates.
6. **Deduplicate** (`deduplicator.deduplicate`) — key by `(chrom, pos, ref, alt)`.
7. **Annotate** (`annotate_variant`, threaded, 8 workers) — VEP consequence+gene, ClinVar, gnomAD, MyVariant fallback, UniProt, PharmGKB, GWAS Catalog.
8. **Score** (`scoring.score_variant`) — heuristic point score, tier, carrier note.
9. **Enrichment stages (8b–8h):** KEGG pathway mapping; AR CAG STR calling via ExpansionHunter (if BAM); receptor expression mapping; PRS; BPC-157 prediction; peptide coverage mapping; PGx (star alleles → CPIC → PRS → conformal).
10. **Summarize** (`summary.generate_summary`) and **sort** by score; then **generate per-peptide HTML dossiers** (`dossier_generator.generate_dossiers`).

The function returns a dict with `variants`, `pathway_summary`, `receptor_genetics`, `prs_profile`, `ar_cag_repeat`, `peptide_recommendations`, `pgx_profile`, and `dossiers`.

**Validation-relevant behaviors observed in the orchestration code:**

- **Variants are silently dropped on annotation failure.** In the threaded annotation loop, `except Exception as e: print(...)` discards any variant whose annotation raised (`engine/pipeline.py`, ~line 241). A transient network error against VEP/ClinVar/gnomAD therefore causes a variant — potentially a clinically critical one — to vanish from results with no surfaced error and no record. This is a **determinism and completeness hazard** (Hazard H-07).
- **Enrichment stages "degrade gracefully" to empty/None.** The PGx stage and STR stage swallow exceptions and substitute placeholder output ("PGx stage skipped: …"). Graceful degradation is appropriate engineering but, for clinical use, *silent* degradation that is indistinguishable from a true-negative result is itself a hazard and must be made explicit and logged.
- **No genome build is ever read, recorded, or checked** (see §0.3, §9.3).

### 2.3 Module inventory and clinical-claim classification

The following classifies each major module by the strength of the clinical claim it implies, which drives the depth of validation required.

| Module | Implied clinical claim | Claim class | Evidence basis in code |
|---|---|---|---|
| `validators.py`, `parsers.py`, `quality_filter.py` | "We correctly read your genotype data" | Analytical (foundational) | Standard thresholds; **no build handling** |
| `rsid_resolver.py` | "We correctly map rsIDs to coordinates" | Analytical | Ensembl REST; cache |
| `annotators/vep.py`, `clinvar.py`, `gnomad.py`, `myvariant.py` | "We correctly annotate consequence, clinical significance, and frequency" | Analytical + clinical | External APIs, GRCh38 assumed, SQLite cache, retries |
| `scoring.py` | "This variant is critical/high/medium/low clinical priority" | **Clinical (high stakes)** | Arbitrary integer weights; substring recessive detection |
| `annotators/prs_calculator.py` | "Your polygenic risk for trait X is elevated" | **Clinical (high stakes)** | Hardcoded GWAS betas; crude ancestry multipliers; no calibration cohort |
| `pgx/star_alleles/*` | "Your CYP2C19 diplotype is *2/*3" | Analytical (high stakes) | Real CPIC/PharmVar defs; **no phasing; CYP2D6 SV gaps** |
| `pgx/cpic/recommendations.py` | "Per CPIC, avoid drug Y" | Clinical (high stakes) | Authentic CPIC snapshot; currency unknown |
| `pgx/hgnn/conformal.py`, `model.py` | "90% confidence the patient is a responder" | **Clinical (high stakes)** | **Synthetic calibration; HGNN disabled** |
| `annotators/peptide_mapper.py` | "Strong Fit for peptide Z" | **Investigational** | Hand-curated gene→peptide map; invented tiers |
| `annotators/bpc157_predictor.py` | "Likely good BPC-157 responder" | **Investigational/speculative** | Self-labeled speculative; non-FDA-approved compound |
| `annotators/receptor_mapper.py` | "ESR1 expression HIGH" | **Investigational** | Hand-curated modifiers; no eQTL basis |
| `tracking/bayes.py`, `genetics.py` | "Predicted response trajectory with 95% CI" | **Investigational** | Conjugate math sound; **priors admittedly synthetic** |
| `repeat_callers/expansion_hunter.py` | "AR CAG repeat = N; testosterone sensitivity" | Analytical + clinical | Real ExpansionHunter; ancestry ranges hand-curated |
| `dossier_generator.py` | The patient-facing rationale & "Predicted Efficacy" | **Communication of all the above** | Single-line disclaimer footer |
| `regulatory/*` | "FDA status of peptide" | Informational | Live openFDA/ClinicalTrials/Federal Register |

### 2.4 External runtime dependencies (reproducibility surface)

The pipeline's output depends on the *live state* of multiple external databases at the moment of execution. This is a fundamental reproducibility and validation challenge: **the same input file run on two different days can produce different results** if ClinVar reclassifies a variant, gnomAD releases a new version, or an API is transiently unavailable (causing silent variant drop, §2.2). The validation program must therefore **pin, snapshot, and version** all external knowledge sources (see §8.6, §9.7). Current caching (`engine/annotation_cache.py`, SQLite per-annotator caches, `data/rsid_cache.db`) improves performance and partial reproducibility but is not a versioned, validated knowledge-base snapshot.

### 2.5 Deployment topology and the API surface (`api.py`)

The FastAPI wrapper exposes `/analyze` (upload → `job_id`), `/jobs/{id}` (poll), `/jobs/{id}/dossier/{peptide}`, `/jobs/{id}/pgx`, `/jobs/{id}/drug/{drug}`, `/regulatory/*`, and a biomarker-tracking router. Validation-relevant facts:

- **No authentication or authorization.** Any client that can reach the service can submit genomes and retrieve any job's results by `job_id`. There is no user identity, no access control, and `job_id` is the only secret protecting a result.
- **Derived genomic results are persisted to disk** as JSON (`JOB_STORE_PATH`, default `data/jobs.json`). While the *raw* upload is processed in memory and "never written to disk," the **results — which are derived from and can re-identify the individual's genome (variants, genotypes, conditions)** — are written to a flat file with no encryption, no access control, and a 24-hour TTL. Genotype-derived data is PHI/regulated data (§13).
- **CORS allows credentials** for configured origins; defaults are localhost but production origins are environment-driven.
- The default panel filter is `acmg81_rsids.txt` and the API forces `bed_filter="peptide_genes.bed"`, meaning the production configuration is materially different from a bare `run_pipeline()` call — the **validated configuration must capture exact env-var settings** (`FILTERS`, `DATA_DIR`, `WORKERS`, `MAX_UPLOAD_MB`, etc.).

### 2.6 Test and CI baseline (`.github/workflows/test.yml`, `tests/`)

A `pytest` suite exists (~25 test modules under `tests/`) running on Python 3.11/3.12 in GitHub Actions, plus container build/push workflows. This is a reasonable engineering baseline but is **unit/behavioral testing of code, not validation**: there is no traceability to requirements, no coverage target of record, no reference-material concordance testing, no determinism/build testing, and no clinical/analytical acceptance criteria. The CI badge in the README points to a personal fork (`curtisdearing/u4u-engine`), which itself is a configuration-management observation to resolve.

---

## 3. Intended Use and Regulatory Classification

> **This section contains the single most consequential decision in the entire plan.** The intended-use statement determines whether the system is a regulated medical device, what regulatory pathway applies, and therefore the depth of every validation activity that follows. The project's own `docs/roadmap.md` lists this as an **open decision: "Regulatory position (info platform vs. medical device)."** That decision must be made, in writing, by accountable leadership, before validation execution begins.

### 3.1 Drafting the Intended Use Statement

A clinical Intended Use Statement (IUS) must specify, at minimum:

- **What** the device outputs (e.g., "annotated genomic variants and pharmacogenomic phenotype predictions");
- **For whom** (intended patient population — age, indication, ancestry scope);
- **By whom** it is used (intended user — licensed clinician? consumer? lab director?);
- **In what setting** (boutique clinic, telehealth, CLIA lab);
- **For what clinical purpose** (inform/guide/support/drive a decision — the verb matters legally);
- **What it is NOT** (limitations, contraindications, populations excluded);
- **The specimen/input scope** (which file types, which genome builds, which sequencing platforms, which arrays).

The current system has **no documented IUS.** Authoring one is the first deliverable of §3.

### 3.2 Candidate intended-use postures and their consequences

| Posture | Description | Regulatory consequence | Validation burden |
|---|---|---|---|
| **A. Wellness / general information** | Outputs framed strictly as non-diagnostic genomic education; no therapy recommendation; no disease risk | May fall under FDA "general wellness" enforcement discretion and be outside device regulation | Lower, but **incompatible with the current dossier**, which recommends therapies and presents "Predicted Efficacy" |
| **B. Clinical Decision Support (CDS)** | Outputs inform a licensed clinician who independently reviews the basis | May qualify for the 21st Century Cures Act CDS exclusion **only if all four statutory criteria are met** (see §3.4) | High — but possibly non-device if criteria met |
| **C. Software as a Medical Device (SaMD)** | Outputs drive/guide diagnosis or treatment | FDA device regulation (510(k)/De Novo/PMA depending on risk); EU IVDR in Europe | Highest — full design controls, clinical evidence |
| **D. Laboratory-Developed Test (LDT) under CLIA** | The genomic analysis is performed as a clinical lab test | CLIA certification, CAP accreditation, state licensure; evolving FDA LDT oversight | High — CLIA/CAP analytical + clinical validation |

The **current product behavior (recommending peptide therapies and presenting predicted efficacy in a patient-facing dossier) is consistent with Posture B or C, not A.** A wellness posture would require materially de-scoping the patient-facing claims.

### 3.3 IMDRF SaMD risk categorization

If the system is a SaMD, the IMDRF framework categorizes risk from the combination of (a) the **significance of the information** to the healthcare decision (treat/diagnose → drive → inform) and (b) the **state of the healthcare situation** (critical / serious / non-serious).

- A pipeline that **guides peptide therapy and surfaces ACMG SF "actionable" pathogenic findings** (the ACMG81 panel is literally the input filter default) touches **serious** conditions and **drives/guides treatment** — placing it in the **higher SaMD categories (III–IV)**, which demand independent clinical validation and rigorous analytical validation.
- The PGx outputs (e.g., "avoid clopidogrel," "DPYD poor metabolizer → fluoropyrimidine toxicity risk") concern **serious/critical** drug-safety decisions and are high-risk regardless of the peptide features.

### 3.4 The CDS exclusion analysis (U.S.)

To be a non-device CDS under the 21st Century Cures Act and FDA's CDS guidance, software must meet **all four** criteria, the most demanding being that it **enables the clinician to independently review the basis** for the recommendation (not rely primarily on it). Assessment against the current system:

| Criterion | Current system | Verdict |
|---|---|---|
| (1) Not intended to acquire/process/analyze a medical image or signal | Processes genomic data (not image/signal) | Likely met |
| (2) Intended to display/analyze medical information | Yes | Met |
| (3) Intended to support/provide recommendations to an HCP | Yes (dossier to clinician) | Met (pushes toward device if patient-facing) |
| (4) **HCP can independently review the basis** such that they do not rely primarily on it | **Fails today.** The scoring weights, the "synthetic" conformal/Bayesian internals, and the speculative peptide tiers are **not transparently sourced**; a clinician cannot independently reconstruct the basis of "Strong Fit" or "90% responder" | **Not met** |

**Conclusion:** As built, the system likely **does not qualify** for the CDS exclusion and would be regulated as a device under Posture C, *unless* it is re-engineered so that every recommendation is transparently and independently reviewable, and patient-facing efficacy claims for investigational compounds are removed. This re-engineering is itself a validation prerequisite.

### 3.5 CLIA/CAP considerations for the genomic analysis

If the genomic interpretation is offered as a clinical test result in the U.S., the testing must be performed in a **CLIA-certified laboratory**, typically **CAP-accredited**, under a qualified **laboratory director**, with the analytical validation, proficiency testing, and quality controls that CLIA/CAP require for high-complexity molecular testing and NGS. The pipeline as a software artifact would be one component of a larger validated laboratory test system. Key CAP/CLIA expectations relevant here: documented analytical validation (accuracy, precision, sensitivity, specificity, reportable range), bioinformatics pipeline validation per **CAP NGS bioinformatics checklist**, version control and change control of the pipeline, and ongoing QC/QA.

### 3.6 International scope

If marketed in the EU, genomic interpretation software that provides information for diagnosis/predisposition/treatment falls under the **In Vitro Diagnostic Regulation (IVDR 2017/746)**, with risk classification (likely Class C for genetic predisposition/PGx), conformity assessment via a notified body, performance evaluation (scientific validity, analytical performance, clinical performance), and post-market performance follow-up. The UK (UKCA/MHRA) and other jurisdictions have analogous regimes. The plan recommends **scoping the initial validation to a single jurisdiction (U.S.)** and treating international as a later expansion.

### 3.7 Required decision and deliverables for §3

1. **Decision memo** signed by the Sponsor and Medical Director selecting the intended-use posture (A/B/C/D), with rationale.
2. **Intended Use Statement** and **indications for use** document.
3. **Regulatory strategy document**: device determination, classification, predicate/comparator analysis, pathway (e.g., 510(k)/De Novo, CLIA/CAP, IVDR), and a list of claims that are **in scope** vs. **explicitly out of scope** (the latter must then be removed or hard-gated from the product).
4. A **claims register** mapping every user-visible output to (a) its intended-use posture, (b) its evidence basis, and (c) the validation activity that supports it. Any output without a defensible basis is removed before clinical launch.

---

## 4. Applicable Standards and Frameworks

The validation program is anchored to recognized standards. The following are the primary references; specific clauses are cited in the relevant sections. (Full citations in Appendix G.)

### 4.1 Quality and software lifecycle

| Standard | Scope | Where used in this plan |
|---|---|---|
| **ISO 13485** | Medical device quality management systems | §6 (QMS) |
| **ISO 14971** | Application of risk management to medical devices | §7 (Risk) |
| **IEC 62304** | Medical device software lifecycle processes | §8 (Software V&V) |
| **IEC 62366-1** | Usability engineering for medical devices | §14 (Human factors) |
| **GAMP 5 (ISPE)** | Risk-based computerized system validation | §8 |
| **21 CFR Part 820 / QSR → QMSR** | FDA Quality System Regulation (harmonizing to ISO 13485) | §6 |
| **21 CFR Part 11** | Electronic records and electronic signatures | §8.5, §13 |
| **FDA Good Machine Learning Practice (GMLP), predetermined change control plans (PCCP)** | AI/ML-enabled device development | §8, §11, §17 |

### 4.2 Genomic and laboratory analytical validation

| Standard / guideline | Scope |
|---|---|
| **CLIA (42 CFR 493)** | Clinical laboratory certification and quality |
| **CAP Molecular Pathology & NGS checklists** (incl. bioinformatics) | Accreditation requirements for NGS pipelines |
| **CDC / Gulley et al., ACMG analytical validation guidance** | Analytical validation of molecular genetic tests |
| **Roy et al. 2018 (AMP/CAP) — Bioinformatics pipeline validation** | Standards for clinical NGS bioinformatics pipelines |
| **GA4GH** benchmarking tools / **GIAB (NIST)** reference materials | Truth sets and benchmarking methodology |
| **GeT-RM (CDC)** pharmacogenetic reference materials | Reference diplotypes for PGx (CYP2D6, CYP2C19, etc.) |
| **CLSI MM09, MM17, EP05, EP12, EP17** | Nucleic acid methods; validation; precision; qualitative test evaluation; LoD |

### 4.3 Clinical interpretation and predictive models

| Standard / guideline | Scope |
|---|---|
| **ACMG/AMP 2015 (Richards et al.) + ClinGen SVI refinements** | Sequence variant pathogenicity classification |
| **ACMG SF v3.x** | Secondary findings gene list (the system's ACMG81 panel) |
| **CPIC guidelines** | Gene/drug pharmacogenomic dosing |
| **PharmVar** | Star-allele (haplotype) nomenclature definitions |
| **AMP/CAP/ASCO PGx allele reporting standards (Pratt et al.)** | Minimum allele sets and reporting for PGx |
| **PGS Catalog + ClinGen Complex Disease / Polygenic** | Polygenic score reporting and evaluation standards |
| **TRIPOD / TRIPOD-AI** | Transparent reporting of prediction models |
| **PROBAST / PROBAST-AI** | Risk-of-bias assessment for prediction models |
| **STARD 2015** | Reporting of diagnostic accuracy studies |
| **DECIDE-AI, SPIRIT-AI/CONSORT-AI** | Early-stage and trial reporting for AI clinical interventions |

### 4.4 Privacy, security, and ethics

| Standard / law | Scope |
|---|---|
| **HIPAA Privacy & Security Rules** | Protected health information |
| **GINA** | Genetic Information Nondiscrimination Act |
| **NIST SP 800-53 / 800-66 (HIPAA)** | Security controls |
| **Common Rule (45 CFR 46), ICH-GCP E6(R3)** | Human-subjects research conduct |
| **GA4GH Framework for Responsible Sharing of Genomic and Health-Related Data** | Genomic data governance |

---

## 5. Gap Analysis — Current State vs. Clinical-Grade

This section is the honest accounting of where the system stands. Each finding is grounded in the actual code. The gap analysis drives the work breakdown in §6–§19.

### 5.1 Summary scorecard

Rating key: **🔴 Absent / blocking** · **🟠 Major gap** · **🟡 Partial / needs rework** · **🟢 Reasonable baseline**

| Domain | Rating | One-line basis |
|---|---|---|
| Intended use & regulatory classification | 🔴 | Undecided ("info platform vs medical device" open in roadmap); no IUS |
| Quality management system | 🔴 | No QMS, SOPs, design history file, or document control |
| Risk management (ISO 14971) | 🔴 | No risk file; multiple uncontrolled hazards (build, variant-drop, auth) |
| Software lifecycle (IEC 62304) | 🟡 | Tests + CI exist; no requirements/traceability/coverage/V&V records |
| Genome build handling | 🔴 | **No build detection anywhere; GRCh38 silently assumed** |
| Input parsing / QC | 🟡 | Reasonable thresholds; platform scope unvalidated; build gap |
| Annotation accuracy | 🟠 | Authoritative APIs but unpinned, unbenchmarked, silent-drop on error |
| Variant scoring / tiering | 🟠 | Arbitrary weights; substring recessive logic; not ACMG/AMP |
| Star-allele calling | 🟠 | Real CPIC defs but no phasing; CYP2D6 SV gaps; unbenchmarked |
| CPIC recommendations | 🟡 | Authentic snapshot; currency/version unmanaged; untested integration |
| PRS | 🟠 | Hardcoded betas; crude ancestry factors; no calibration cohort |
| Conformal prediction | 🔴 | **Synthetic default calibration; HGNN disabled; no real guarantee** |
| Peptide-response / BPC-157 / receptor models | 🔴 | Self-labeled speculative/synthetic; investigational compounds; no human evidence |
| Bayesian tracking | 🟠 | Math sound but priors "stylised, not from any GWAS" |
| Privacy / security / PHI | 🔴 | No auth; derived results persisted unencrypted to `jobs.json` |
| Human factors / labeling | 🟠 | One-line dossier disclaimer; no usability validation; patient-facing efficacy claims |
| Equity / ancestry generalizability | 🟠 | Ancestry factors hand-set; reference params European-only |
| Reproducibility / determinism | 🟠 | Live external deps; silent variant drop; no snapshot/version pinning |
| Clinical validity evidence | 🔴 | None for any claim |
| Clinical utility evidence | 🔴 | None |
| Post-market surveillance | 🔴 | None |

### 5.2 Module-by-module findings

#### 5.2.1 Input, parsing, and quality control (`validators.py`, `parsers.py`, `quality_filter.py`)
- Enforces: file ≤ 100 MB, VCF `##fileformat` header, UTF-8; drops hom-ref, failed calls, indels; VCF `GQ ≥ 20`, `DP ≥ 5` (hardcoded).
- **Gaps:** (a) no genome-build detection or recording — the headline defect; (b) QC thresholds chosen reasonably but not validated against platform-specific truth data; assumes Illumina-like quality semantics; (c) assumes diploid; no ploidy/sex-chromosome handling at parse; (d) indel exclusion means the system is, by construction, **blind to a clinically important variant class** — this must be stated as a limitation or the scope must be expanded and validated.

#### 5.2.2 Annotation (`annotators/vep.py`, `clinvar.py`, `gnomad.py`, `myvariant.py`)
- Real Ensembl VEP, NCBI ClinVar (eUtils), gnomAD GraphQL, MyVariant fallback, with SQLite caching and tenacity retries.
- **Gaps:** (a) all assume GRCh38; (b) outputs depend on live DB state → **not reproducible** without snapshotting/version pinning; (c) the pipeline **silently drops** a variant if any annotator raises (§2.2); (d) ClinVar significance is taken as a lowercased string and fed to substring logic downstream; review status / star rating / conflicting interpretations are not used to weight confidence.

#### 5.2.3 Scoring (`engine/scoring.py`)
- Assigns an integer score: ClinVar pathogenic short-circuits to `+1000`/CRITICAL; benign → `1`/LOW; likely pathogenic `+500`; VUS `+50`; HIGH_IMPACT consequence `+100`; moderate `+50`; low `+5`; frequency bands `+30/+20/+10/+5/−20`; intergenic `−10`; carrier-in-recessive halves the score. Tiers: CRITICAL ≥ 500, HIGH ≥ 100, MEDIUM ≥ 30, LOW < 30.
- **Gaps:** (a) the weights are **arbitrary and unjustified**; the resulting "tier" is a ranking heuristic, **not an ACMG/AMP clinical classification**, yet is surfaced to clinicians/patients as clinical priority; (b) "recessive" is detected by **substring-matching free text** (`"recessive"`, `"biallelic"` in the disease name) — fragile, language-dependent, and silently wrong when ClinVar phrasing differs; (c) zygosity feeds carrier logic but the upstream zygosity determination is itself unvalidated; (d) no use of inheritance mode from an authoritative source (e.g., OMIM/ClinGen), gene-disease validity, or zygosity-appropriate interpretation.

#### 5.2.4 Polygenic risk scores (`annotators/prs_calculator.py`)
- Additive `Σ βᵢ·dosageᵢ`, sigmoid-normalized, with multiplicative ancestry factors; betas hardcoded from named consortia (DIAGRAM, MAGIC, GIANT, etc.) for three traits; European reference mean/SD hardcoded.
- **Gaps:** (a) no PMIDs/PGS Catalog IDs in code; provenance unverifiable; (b) ancestry handling is a **crude multiplier**, not ancestry-specific weights or a principal-components adjustment, and reference distribution is European-only → **known poor transferability and equity risk**; (c) **no calibration/validation cohort**; the mapping from raw score to "risk" is unvalidated; (d) handling of missing genotypes, strand, effect-allele orientation, and imputation is not evidenced.

#### 5.2.5 Pharmacogenomics (`pgx/`)
- **Star alleles** (`star_alleles/`): rsID-keyed matching against real PharmVar/CPIC definitions; activity-score summation → phenotype bins; **explicitly marks CYP2D6 from arrays as incomplete** (`evidence_tier='tentative-no-sv'`, confidence 0.55) because CNV/`*5` deletion/hybrids are not detectable.
- **CPIC** (`cpic/recommendations.py`): authentic hardcoded recommendation table citing CPIC literature; described as a snapshot needing `scripts/refresh_cpic.py`.
- **Conformal/HGNN** (`hgnn/conformal.py`, `model.py`, `orchestrator.py`): Mondrian split-conformal over a **synthetic default calibration set**; the real calibration file does not exist; the HGNN path is hard-disabled (`method = "rule_based_fallback"`); responder probability is a fixed sigmoid of an arbitrarily weighted risk sum.
- **Gaps:** (a) **no phasing** → cis/trans ambiguity can misassign diplotypes (e.g., two CYP2D6 hets); (b) **CYP2D6 structural variation unaddressed** — a documented major source of PGx error; (c) the **conformal "guarantee" is not real** (synthetic calibration violates exchangeability with any real population); (d) responder probability and ADR risk are conflated; (e) CPIC version currency is unmanaged.

#### 5.2.6 Investigational models (`peptide_mapper.py`, `bpc157_predictor.py`, `receptor_mapper.py`, `tracking/`)
- Peptide mapper: hand-curated gene→peptide sets, invented tier labels ("Strong Fit", etc.).
- BPC-157 predictor: self-labeled speculative; pathway/rsID weights are mechanism-of-action guesses; the module's own disclaimer states no validated human biomarkers or genetic predictors exist.
- Receptor mapper: hand-curated rsID "magnitude/direction" modifiers with no eQTL basis.
- Tracking: conjugate Normal-Normal math is correct, but genetic-prior weights are, per the docstring, **"synthetic … stylised, not pulled from any GWAS."**
- **Gaps:** these are not "under-validated" — they are **not validatable as clinical claims today** because (a) the compounds lack human efficacy evidence and (b) no genetic predictor of response exists in the literature. They can be kept only as clearly labeled, non-clinical, exploratory features, or removed.

#### 5.2.7 STR calling (`repeat_callers/expansion_hunter.py`)
- Genuine Illumina ExpansionHunter integration for AR CAG repeat; ancestry-adjusted interpretation tiers; requires hg38 BAM and an installed binary + reference FASTA.
- **Gaps:** (a) hard dependency on external binary/reference not validated as installed/versioned; (b) no build verification of the BAM; (c) interpretation tiers and ancestry reference means are hand-curated and need clinical-evidence backing; (d) no outcome data linking CAG length to the therapeutic decisions implied.

#### 5.2.8 API, persistence, and dossier (`api.py`, `dossier_generator.py`)
- No authentication; derived results persisted unencrypted to `jobs.json`; CORS with credentials; patient-facing dossier presents "Predicted Efficacy" tier + coverage with a single-line "decision support, not a prescription" footer.
- **Gaps:** §13 (privacy/security) and §14 (human factors) detail these; both are blocking for clinical use.

### 5.3 Cross-cutting deficiencies

1. **Genome build (H-01)** — silent GRCh37/GRCh38 conflation (launch-blocking).
2. **Silent data loss (H-07)** — variants dropped on annotation exception.
3. **Non-determinism / non-reproducibility** — live external dependencies, no snapshot/version pinning.
4. **No identity/audit** — unauthenticated API; no audit trail of who ran what, when, on which configuration and knowledge-base version.
5. **No provenance on claims** — clinicians cannot independently review the basis (defeats CDS exclusion and good practice).
6. **Equity** — European-centric reference data and crude ancestry adjustment.
7. **Configuration drift** — production config (forced BED filter, env vars) differs from the library default; CI badge points to a fork.

### 5.4 Launch-blocking items (must be resolved before *any* clinical exposure)

- B-1: Resolve genome-build handling (detect + record + reject/liftover) — §9.3.
- B-2: Eliminate silent variant drop; fail loudly and traceably — §8, §9.
- B-3: Authenticate the API and protect/encrypt all PHI at rest and in transit — §13.
- B-4: Remove or hard-gate patient-facing efficacy claims for investigational compounds — §3.7, §14.
- B-5: Make a documented intended-use and regulatory determination — §3.
- B-6: Replace heuristic "clinical significance" tiering with ACMG/AMP classification (or relabel it explicitly as non-clinical prioritization) — §10.
- B-7: Establish the minimum QMS, risk file, and version-frozen validated configuration — §6, §7, §8.

---

## 6. Quality Management System Prerequisites

Validation evidence is only credible inside a quality system that controls how the evidence is produced, reviewed, approved, and maintained. A regulator or accreditor will ask not just "is it validated?" but "show me the controlled procedure under which it was validated, the records, the approvals, and the change control since." None of this exists in the repository today. This section defines the minimum QMS to stand up.

### 6.1 QMS scope and standard

Adopt **ISO 13485** (and align to **FDA QMSR / 21 CFR Part 820** as it harmonizes to ISO 13485) as the QMS backbone, scaled appropriately for an early-stage software organization. If the genomic analysis is offered as a clinical laboratory test, layer **CLIA + CAP** requirements on top (§3.5).

### 6.2 Required QMS elements

| Element | Deliverable | Notes |
|---|---|---|
| Quality manual & quality policy | Controlled document | Defines scope, processes, responsibilities |
| Document & record control | SOP + controlled repository | Versioning, approval, retention; this VMP becomes a controlled doc |
| Design controls (Part 820.30 / ISO 13485 7.3) | Design History File (DHF) | Design inputs/outputs, reviews, V&V, transfer, changes |
| Design & development plan | Plan per project | Phases, deliverables, reviews, responsibilities |
| Risk management process | SOP + Risk Management File | §7 |
| Software lifecycle | SOP per IEC 62304 | §8 |
| Supplier/external-dependency control | SOP | For external knowledge bases and the ExpansionHunter binary, etc. |
| CAPA (corrective/preventive action) | SOP + log | Includes field issues, model drift, DB errors |
| Complaint handling & vigilance | SOP | Including adverse-event reporting (MDR) if a device |
| Training & competency | Records | For clinical curators, reviewers, lab staff |
| Internal audit & management review | SOP + schedule | |
| Change control & configuration management | SOP | Pipeline, models, knowledge bases, env config |

### 6.3 Roles to establish (see also §18)

A clinical-grade program requires named, qualified, accountable individuals: **Medical Director (licensed physician)**, **Laboratory Director** (if CLIA), **Quality/Regulatory Lead**, **Clinical Bioinformatics Lead**, **Biostatistician**, **Security/Privacy Officer**, **Clinical Variant/Curation Scientists**, and an independent **Clinical Advisory Board**. Validation deliverables must be authored, reviewed, and approved by appropriately qualified roles — e.g., variant-classification SOPs approved by board-certified clinical molecular geneticists.

### 6.4 The Design History File and validated-configuration baseline

Create a DHF that contains, at minimum: design inputs (requirements, IUS), design outputs (specifications, code, knowledge-base snapshots), design reviews, the risk management file, verification and validation protocols/reports, and a **formally frozen "validated configuration"** — an exact, reproducible specification of the software version, dependency versions, external knowledge-base snapshot versions, model weights, and runtime configuration that the validation evidence pertains to. Any change to that configuration triggers change control and, potentially, partial revalidation (§17).

---

## 7. Risk Management (ISO 14971)

### 7.1 Process

Establish a risk-management process per **ISO 14971** producing a **Risk Management File** containing: a risk management plan; identification of hazards and hazardous situations; estimation of risk (severity × probability of occurrence of harm); risk evaluation against criteria; risk control measures; verification of those controls; residual-risk evaluation; and an overall benefit-risk determination. For an AI/ML-enabled product, integrate **AAMI CR34971 / TR34971** guidance on AI-specific risks (data drift, dataset shift, automation bias, opacity).

### 7.2 Severity and probability scales (proposed)

**Severity:** S1 negligible · S2 minor · S3 serious (reversible) · S4 critical (irreversible/life-threatening). **Probability:** P1 improbable · P2 remote · P3 occasional · P4 probable · P5 frequent. Risk = S × P, evaluated against an acceptability matrix (to be approved by the team). Any S4 hazard with a credible pathway requires risk control to ALARP and explicit benefit-risk justification.

### 7.3 Worked hazard analysis (seed entries)

These seed entries are grounded in specific code behaviors and must be expanded into the full register (Appendix D). "Harm" is to the patient.

| ID | Hazard / cause (code basis) | Hazardous situation | Potential harm | Pre-control S×P | Risk control measures | Post-control target |
|---|---|---|---|---|---|---|
| **H-01** | **Genome build not detected**; GRCh37 input treated as GRCh38 (no build logic in `validators.py`/`parsers.py`; all annotators assume GRCh38) | Every annotation/score/PRS/PGx/peptide call is positionally wrong | Missed pathogenic finding; false pathogenic finding; wrong drug guidance → serious/critical mismanagement | **S4 × P4** | Detect build from VCF header/array signature; record build in record; reject or liftover non-GRCh38 with validated tooling; surface build to user; analytical validation across builds (§9.3) | S4 × P1 |
| **H-02** | **Heuristic tier presented as clinical significance** (`scoring.py` arbitrary weights; substring recessive) | Clinician reads "CRITICAL"/"LOW" as validated classification | Over- or under-action on a variant | S3 × P4 | Replace with ACMG/AMP classification or relabel as non-clinical prioritization; show evidence and provenance; clinician sign-out (§10) | S3 × P2 |
| **H-03** | **Conformal "confidence" from synthetic calibration** (`conformal.py` `_DEFAULT_CAL_SCORES`) | "90% confidence responder" shown but statistically meaningless | False confidence drives therapy choice | S3 × P4 | Disable confidence output until calibrated on real held-out data; validate coverage empirically; label uncertainty source (§11.4) | S3 × P2 |
| **H-04** | **Investigational peptide efficacy claim** (`peptide_mapper.py`, `bpc157_predictor.py`) on patient-facing dossier | Patient/clinician believe genetic "fit" predicts benefit of a non-approved compound | Exposure to unproven therapy; opportunity cost; financial harm | S3 × P4 | Remove patient-facing efficacy tiers for investigational compounds, or gate behind IRB-approved research with consent; strong labeling (§3.7, §12.4, §14) | S3 × P2 |
| **H-05** | **CYP2D6 mis-diplotyping** (no phasing; SV/CNV not detected; `star_alleles/`) | Wrong metabolizer phenotype → wrong CPIC guidance | Drug toxicity or therapeutic failure | S4 × P3 | Validate against GeT-RM; restrict reportable alleles to array-supported set; flag SV-uncertain genes; orthogonal confirmation for actionable calls (§9.10) | S4 × P2 |
| **H-06** | **PRS used outside validated ancestry** (European reference; crude multiplier) | Miscalibrated risk in non-European patient | Misinformed risk counseling | S3 × P4 | Restrict reportable population; ancestry-specific validation; calibration; explicit limitation labeling (§11.2, §15) | S3 × P2 |
| **H-07** | **Silent variant drop on annotation error** (`pipeline.py` `except: print`) | A clinically critical variant silently absent | Missed actionable finding | S4 × P3 | Fail loudly; retry/queue; record per-variant annotation status; reconcile expected vs annotated counts; block report on incompleteness (§8, §9.7) | S4 × P2 |
| **H-08** | **No authn; PHI persisted unencrypted** (`api.py` `jobs.json`) | Unauthorized access to genomic-derived data | Privacy breach; discrimination (GINA-adjacent) | S3 × P4 | AuthN/Z; encrypt at rest/in transit; access logging; retention controls (§13) | S3 × P2 |
| **H-09** | **External DB reclassification between runs** (live ClinVar/gnomAD) | Same input yields different result over time | Inconsistent clinical guidance | S3 × P3 | Versioned knowledge-base snapshots; record KB version on each report; controlled update cadence (§8.6, §17) | S3 × P2 |
| **H-10** | **Indels excluded by QC** (`quality_filter.py`) | Pathogenic indel never considered | Missed finding | S4 × P3 | Either expand scope to validate indels, or explicitly bound the intended use and label the limitation prominently | S4 × P2 |
| **H-11** | **Automation bias / opacity** (AI-specific) | Clinician defers to opaque output | Inappropriate management | S3 × P3 | Transparency, provenance, training, UI framing as support; human-factors validation (§14) | S3 × P2 |

### 7.4 Residual risk and benefit-risk

After controls, the team must evaluate residual risk per hazard and overall. For investigational-compound features (H-04), the residual benefit-risk in a *clinical* context is unfavorable until human evidence exists; the recommended control is to keep them out of the clinical claim set (research-only). The overall benefit-risk determination is a Medical-Director-accountable decision documented in the Risk Management File and revisited at every release.

---

## 8. Software Verification and Validation (IEC 62304 / GAMP 5 / 21 CFR Part 11)

### 8.1 Software safety classification and lifecycle

Classify the software per **IEC 62304** (Class A/B/C by the severity of harm a software failure could cause). Given H-01/H-05/H-07 can contribute to serious or critical harm, the system is **Class C** (the highest), requiring the full set of lifecycle processes: software development planning, requirements analysis, architectural design, detailed design, unit implementation and verification, integration and integration testing, system testing, and release — each with documented records, plus software risk management, configuration management, and problem resolution.

### 8.2 Requirements and traceability

Today there is code and tests but **no requirements specification and no traceability**. Establish:

- **Software Requirements Specification (SRS):** functional, performance, interface, and safety requirements, each with a unique ID, derived from the IUS and risk controls (e.g., REQ: "The system shall determine and record the genome build of every input and shall reject inputs whose build cannot be confirmed as GRCh38." — traces to H-01).
- **Requirements Traceability Matrix (RTM):** every requirement traces forward to design, code module, and the verification test(s) that demonstrate it, and backward to the design input / risk control it satisfies (template in Appendix A). For clinical software the RTM is a primary audit artifact.

### 8.3 Verification testing — current state and target

- **Current:** ~25 `pytest` modules; CI on Py 3.11/3.12; container builds. No coverage target, no requirement linkage, no negative/robustness suite of record, no reference-material concordance, no determinism tests.
- **Target:**
  - **Unit tests** for every module with defined coverage acceptance (e.g., ≥ 90% statement / ≥ 80% branch on clinical-logic modules: `scoring.py`, `prs_calculator.py`, `star_alleles/*`, `cpic/*`, `conformal.py`, `quality_filter.py`, `parsers.py`).
  - **Integration tests** for the full `run_pipeline()` across each input format and build scenario, with golden, version-pinned external-data fixtures (recorded API responses) so tests are deterministic.
  - **System tests** through the API (auth, job lifecycle, error paths, size/format limits, PHI handling).
  - **Negative & robustness tests:** malformed VCFs, mixed builds, truncated files, non-UTF-8, huge files, ambiguous genotypes, missing FORMAT fields, network-failure injection (to prove H-07 is fixed — variants must not silently vanish).
  - **Regression suite** gating every release; failures block release.
  - **Static analysis & security scanning:** linting, type-checking (e.g., mypy), SAST, dependency vulnerability scanning, and a generated **SBOM**; pin and review the vendored `tenacity`/`_vendor` shims.

### 8.4 Software architecture and configuration management

- Establish controlled **semantic versioning** of the engine and a release process tied to the QMS. The existing git-hook version auto-increment is a start but is not change control.
- **Pin all dependencies** (lockfiles) and the Python runtime; record them in the validated configuration.
- Treat **knowledge bases and model weights as configuration items** under version control (the ACMG81 list, CPIC table, PRS betas, star-allele definitions, BPC-157/receptor/tracking weight tables, condition library). Each has an owner, a source citation, a version, and a change-control path.
- Resolve **configuration drift:** the CI/test badge references a personal fork; the production API forces a BED filter and specific env vars that differ from library defaults — the validated configuration must capture the exact production settings.

### 8.5 Electronic records and signatures (21 CFR Part 11)

If results are clinical records, Part 11 applies: **audit trails** (who did what, when, to which record), record integrity and retention, access controls, and electronic signatures for clinical sign-out. The current `jobs.json` store has none of this. Required: an auditable datastore, immutable result records tied to the exact pipeline/KB version, and a clinician e-signature workflow for report finalization (ties to §10 sign-out and §13).

### 8.6 Reproducibility and determinism

A clinical pipeline must be reproducible: the same input and the same validated configuration must yield the same output. Required controls:

- **Snapshot external knowledge** (ClinVar, gnomAD, VEP cache, MyVariant, UniProt, PharmGKB, GWAS) into versioned, internally hosted datasets; run against the snapshot, not live endpoints, for clinical reporting; record the KB snapshot version on every report (addresses H-09).
- **Make annotation failures non-silent and non-lossy** (addresses H-07): per-variant annotation status, hard reconciliation of expected vs. reported variants, and report-blocking on incompleteness.
- **Pin tool/binary versions** (ExpansionHunter, reference FASTA) and verify them at runtime.
- **Determinism tests:** repeated runs on a fixed fixture set must be bit-for-bit (or defined-tolerance) identical; thread-pool ordering must not affect results.

### 8.7 AI/ML-specific lifecycle (GMLP)

For the learned/parametric components (PRS, conformal/HGNN, Bayesian tracking, any future ML), follow **FDA Good Machine Learning Practice** and consider a **Predetermined Change Control Plan (PCCP)** if models will be updated post-deployment. Required: documented training data provenance and representativeness, data/label quality, train/validation/test separation with no leakage, locked model artifacts under configuration control, performance monitoring, and a defined retraining/recalibration and re-validation process (§11, §17). Note that several "models" here are not learned at all but hand-set weight tables; those follow knowledge-base change control (§8.4) plus clinical-evidence review (§11).

---

## 9. Analytical Validation of the Genomic Pipeline

Analytical validation answers: *does the pipeline correctly and reproducibly determine what is in the genome?* This must be completed and passed before any clinical-validity work, because clinical claims built on an inaccurate measurement are meaningless. The approach follows CAP/CLIA NGS validation expectations, the AMP/CAP bioinformatics-pipeline validation principles (Roy et al.), CDC/ACMG analytical guidance, and GA4GH/GIAB benchmarking methodology.

### 9.1 Principles and metrics

For each analytical claim the pipeline makes (genotype, variant, consequence, ClinVar mapping, frequency, star-allele diplotype, repeat length), define and measure against a truth set:

- **Accuracy** = concordance with truth (overall, and stratified by variant type/region).
- **Analytical sensitivity** (true positive rate / recall) and **analytical specificity** (true negative rate).
- **Positive and negative predictive value** at the relevant prevalence.
- **Precision** = repeatability (same sample, same run/operator) and reproducibility (across runs, days, operators, environments, and — critically here — across software/KB versions).
- **Limit of detection / reportable range** as applicable.
- **Robustness** to input perturbations (format variants, quality, missingness, build).

Acceptance criteria with confidence intervals are pre-specified in §16 and Appendix B; e.g., for SNV genotype concordance the typical clinical bar is ≥ 99% with a lower 95% CI bound that is also pre-specified.

### 9.2 Input and specimen scope definition

Before testing, **freeze the input scope** the validation will cover and the product will accept:

- File formats actually supported and validated (VCF, VCF.gz, 23andMe txt, AncestryDNA, rsID list, CSV) — each validated separately; do not claim support for a format that is not in the truth-set testing.
- **Genotyping/sequencing platforms** in scope (e.g., specific consumer arrays vs. clinical WES/WGS) — array vs. sequencing have different error profiles and different star-allele/CNV capabilities.
- **Genome builds** in scope (recommended: GRCh38 only, with everything else rejected — see §9.3).
- Variant classes in scope (currently SNVs; indels are filtered out — either expand and validate or bound the claim, H-10).
- Regions in scope (the ACMG81 panel, the peptide BED, PGx genes) — analytical performance must be characterized **per region**, including difficult/low-complexity and segmental-duplication regions (e.g., CYP2D6).

### 9.3 Genome build determination and handling — the priority work item

This addresses the headline defect (H-01). Required capabilities and their validation:

1. **Build detection.** Implement robust detection: VCF `##reference`/`##contig` headers and contig lengths; array manifest/version signatures; coordinate sanity checks against known build-discriminating loci. Validate detection accuracy on a labeled corpus of GRCh37 and GRCh38 files from multiple sources/platforms; target ≥ 99% correct build identification with explicit "unknown" handling.
2. **Policy.** Recommended initial policy: **accept GRCh38 only; reject (do not silently process) any input not confirmed GRCh38.** Validate that rejection is correct and user-surfaced.
3. **Optional liftover.** If GRCh37 support is desired, integrate validated liftover (e.g., CrossMap/NCBI Remap-style) and validate post-liftover concordance, explicitly characterizing loci that fail to lift or change representation. Liftover is itself an analytical step requiring its own validation.
4. **Record-keeping.** The detected/confirmed build is recorded on the result and the report, and is part of the audit trail.
5. **Regression guard.** Negative tests prove a GRCh37 file can never be silently annotated as GRCh38.

### 9.4 Parsing accuracy

Validate `parse_file` for each format: correct extraction of chrom/pos/ref/alt/rsid/genotype/zygosity; correct handling of multiallelic sites, missing fields, no-calls, sex chromosomes, and edge cases (header-only files, trailing whitespace, CRLF, BOM). Truth: hand-curated parsing fixtures with known expected variant dicts. Acceptance: 100% on a defined parsing conformance suite (parsing is deterministic and should be exact).

### 9.5 Quality-control validation

Validate `apply_quality_filter`: confirm hom-ref/failed-call/indel removal and `GQ ≥ 20`/`DP ≥ 5` thresholds behave as specified, and — importantly — **justify the thresholds** for each in-scope platform with data (ROC of GQ/DP vs. truth concordance), rather than accepting the hardcoded defaults. Characterize what fraction of true variants are removed by QC (the "cost" of the filter) and what error fraction is removed (the "benefit"). Document indel exclusion as a bounded limitation (H-10).

### 9.6 rsID resolution accuracy

Validate `resolve_rsids` (Ensembl): correct rsID→coordinate/allele mapping, handling of merged/withdrawn/multi-mapping rsIDs, and build correctness of returned coordinates. Truth: a curated rsID set with known GRCh38 coordinates. Characterize behavior on ambiguous/retired rsIDs.

### 9.7 Annotation concordance

For VEP consequence, ClinVar significance, gnomAD frequency, and MyVariant fallback:

- Validate against the **pinned knowledge-base snapshot** (§8.6), not live endpoints, for the clinical configuration.
- Concordance testing: confirm the pipeline reproduces the snapshot's consequence/significance/frequency for a large variant panel (including all ACMG81 and PGx loci) within defined tolerance.
- **Canonical-transcript / consequence-selection logic** (`select_canonical_consequence`) must be validated: which transcript set, MANE Select adherence, and tie-breaking — clinically material because consequence drives scoring.
- **ClinVar handling** must use review status / star rating / conflicting-interpretation flags, not just the significance string; validate that conflicting and low-review-status records are represented honestly.
- **Completeness reconciliation** (fixes H-07): prove that the count and identity of variants entering annotation equals those leaving (minus intended QC), with explicit, logged status for any annotation miss; report-blocking on unreconciled loss.

### 9.8 Reference materials and truth sets

| Purpose | Reference material |
|---|---|
| SNV/indel genotype accuracy | **GIAB / NIST** (HG001–HG007) high-confidence calls and regions; GA4GH benchmarking (hap.py) |
| Pharmacogenetic diplotypes | **GeT-RM (CDC)** Coriell samples with consensus star-allele genotypes (CYP2D6, CYP2C19, CYP2C9, TPMT, NUDT15, DPYD, SLCO1B1, UGT1A1, VKORC1) |
| STR / repeat | Coriell/EMQN repeat-expansion reference samples for AR/relevant loci |
| Variant interpretation | ClinVar expert-panel (3–4 star) and ClinGen-curated variants as a classification truth set |
| Array-specific | Public 23andMe/AncestryDNA-format exports of GIAB samples (or simulated array genotypes from GIAB truth) to validate the consumer-array path |
| Build | Labeled GRCh37/GRCh38 corpora for build-detection validation |

Use multiple ancestries from these resources to support equity claims (§15).

### 9.9 Analytical performance study design and sample size

- **Accuracy/sensitivity/specificity:** Run all reference samples through the frozen pipeline; compute metrics overall and stratified (variant type, region difficulty, platform, ancestry). Pre-specify acceptance (e.g., SNV sensitivity ≥ 99%, specificity ≥ 99.5%, with lower 95% CI bounds; PGx diplotype concordance ≥ 99% on GeT-RM consensus calls).
- **Precision:** repeatability (≥ 20 replicates of representative samples within run) and reproducibility (across days/operators/environments and **across the exact software+KB version**). Per CLSI EP05 design.
- **Sample-size rationale:** size each study so that the lower confidence bound on the key metric meets the acceptance threshold at the target prevalence; document the statistical basis (Appendix B / §16). Rare/important variant classes may need targeted enrichment because genome-wide truth sets under-represent them.

### 9.10 Star-allele (PGx) analytical validation

This is high-stakes (drug safety) and currently has known gaps (no phasing, CYP2D6 SV). Required:

- **GeT-RM concordance** for every reportable gene and the **specific alleles the system can call**; report concordance per gene and per allele.
- **Constrain the reportable allele set** to what the input platform can actually support (the code already marks array-limited genes; validation must formalize and bound this). Do **not** report CYP2D6 diplotypes from arrays as definitive where CNV/`*5`/hybrids are undetectable — either suppress, or report with a validated "structural variation not assessed" qualifier and lower confidence, and validate that qualifier's behavior.
- **Phasing limitation:** characterize and bound the cis/trans ambiguity; where actionable, require orthogonal confirmation (e.g., long-read or targeted PGx assay) before the result drives prescribing.
- **Phenotype assignment:** validate activity-score→phenotype binning against CPIC's published consensus assignments; validate the **phenoconversion** logic (drug-interaction/comedication adjustments in `cpic/phenoconversion.py`) against CPIC rules.
- **CPIC mapping:** validate that, given a diplotype/phenotype, the engine returns the correct, current CPIC recommendation; manage CPIC version currency as a configuration item (run `scripts/refresh_cpic.py` under change control and record the version on reports).

### 9.11 STR / ExpansionHunter analytical validation

- Validate the AR CAG caller against reference samples of known repeat length; characterize accuracy and the limit beyond which sizing is unreliable (long expansions are harder for short-read STR callers).
- Validate the runtime dependency: ExpansionHunter binary version and reference FASTA are pinned, present, and verified; the BAM build is confirmed hg38 before calling (ties to §9.3).
- Validate graceful-degradation behavior is *explicit* (a "could not assess" state distinct from a true-negative).
- The clinical interpretation tiers and ancestry reference ranges require clinical-evidence backing (§11) before being reported clinically.

### 9.12 Robustness, carryover, and interfering factors (software analogs)

- **Robustness:** deliberately perturb inputs (quality degradation, missingness, format quirks, mixed builds, multiallelics) and confirm graceful, correct, non-lossy behavior.
- **Carryover/cross-contamination analog:** prove no state bleeds between jobs (caches keyed correctly; one patient's results never contaminate another's — directly relevant given the shared SQLite caches and shared job store).
- **Concurrency:** the threaded annotation must be proven order-independent and race-free (determinism, §8.6).

### 9.13 Analytical validation report

Compile an **Analytical Validation Report** per claim, with methods, truth sets, results vs. pre-specified acceptance criteria, deviations, limitations, and the validated configuration. Signed by the Bioinformatics Lead and Laboratory/Medical Director. This report is a gate to clinical-validation work.

---

## 10. Clinical Validation of Interpretation and Scoring

Analytical validation proves the pipeline correctly *reads* the genome. Clinical validation proves the *interpretation* layered on top is correct and clinically meaningful. This section covers the variant-significance interpretation and the scoring/tiering that the system presents as clinical priority.

### 10.1 Replace heuristic scoring with a defensible interpretation framework

The current `scoring.py` is a ranking heuristic with arbitrary weights and substring-based inheritance detection (§5.2.3). For clinical use, variant clinical significance must be determined by the recognized standard: **ACMG/AMP 2015 (Richards et al.) with ClinGen Sequence Variant Interpretation (SVI) refinements**, applied by qualified personnel with documented evidence codes (PVS1, PS1–4, PM1–6, PP1–5, BA1, BS1–4, BP1–7), gene-disease validity context (ClinGen), and appropriate inheritance and zygosity handling from authoritative sources (OMIM/ClinGen), **not** free-text substring matching.

Two acceptable paths:

- **Path A (clinical claim):** Implement an ACMG/AMP classification workflow (semi-automated evidence aggregation + mandatory qualified human review and sign-out). Validate the automated evidence assignment against expert-panel truth (ClinVar 3–4 star, ClinGen). The final clinical classification is human-approved.
- **Path B (de-scope):** Keep the heuristic strictly as an internal triage/prioritization aid that is **never surfaced as clinical significance**, with all clinically reported significance coming from expert-panel ClinVar/ClinGen sources directly, clearly labeled with review status. Patient-facing language must not imply the heuristic tier is a clinical determination.

Either way, the words "CRITICAL/HIGH/MEDIUM/LOW" must not be presented as a validated pathogenicity classification unless they *are* one (H-02).

### 10.2 Validation study for the interpretation layer

- **Truth set:** a large, ancestry-diverse panel of variants with expert-panel/ClinGen consensus classifications, including pathogenic, likely pathogenic, VUS, likely benign, benign, and deliberately included **conflicting** and **reclassified** variants.
- **Metrics:** concordance of the system's reported clinical significance with the truth classification; per-class sensitivity/specificity; rate and direction of misclassification (clinically, false-benign on an actionable gene is far more harmful than false-VUS); calibration of any confidence indicator.
- **VUS policy:** validate that VUS are handled per `docs/interpretation.md` policy (and that the policy itself is clinically sound — VUS must not be actioned as pathogenic). Validate the ACMG SF "actionable" handling, since the ACMG81 panel is the default filter.
- **Reclassification:** because ClinVar changes over time (H-09), validate the process for periodic re-interpretation and patient re-contact policy.

### 10.3 Condition library completeness and curation governance

`docs/project-status.md` indicates the **condition library content is incomplete** ("81 ACMG SF rows needed"; schema done, content missing). The `condition_key` (OMIM/MedGen/ClinVar) → human-readable condition, plain description, and action guidance mapping is patient-facing clinical content. Required:

- Complete the condition library with **clinically reviewed, sourced** content for every reportable condition.
- Establish a **curation SOP**: who writes/reviews/approves each entry, what sources are cited, how updates are controlled, and how action guidance is kept consistent with current guidelines.
- Validate that the engine correctly resolves `condition_key` and renders the approved content (no orphan keys, no wrong-condition mappings).

### 10.4 Carrier / zygosity interpretation

Validate the carrier logic end-to-end: correct zygosity determination upstream (analytical), correct identification of recessive inheritance from an authoritative source (replacing substring matching), and clinically correct carrier messaging (a carrier finding has reproductive-counseling implications and must be framed accordingly). Edge cases: X-linked genes, conditions with both dominant and recessive mechanisms, compound heterozygosity (which the system cannot detect without phasing).

### 10.5 Clinician sign-out and the human-in-the-loop

For clinical reporting, define a **clinician/lab-director sign-out** step: the automated output is a draft; a qualified professional reviews, may amend, and signs (e-signature, §8.5). Validate this workflow as part of human-factors validation (§14). Sign-out is also part of the CDS-transparency argument (§3.4): the reviewer must be able to see and independently assess the evidence behind every reported call.

---

## 11. Clinical Validation of the Predictive Models

The pipeline contains several parametric/predictive models that make clinical or quasi-clinical predictions. These require model-specific validation following **TRIPOD/TRIPOD-AI** (transparent reporting), **PROBAST/PROBAST-AI** (risk-of-bias), and **GMLP**. The universal requirements for every model below are: a documented and clinically justified specification; transparent, sourced parameters; an **independent validation cohort** (not used to derive the model); reported **discrimination** (AUC/C-index), **calibration** (calibration plot/intercept/slope), and clinical utility (decision-curve analysis where applicable); pre-specified acceptance criteria; subgroup performance (especially by ancestry); and a monitoring/recalibration plan.

### 11.1 Cross-cutting issues for all current models

- **Provenance:** several models use weights with no in-code citation (PRS betas reference consortia but not PMIDs/PGS IDs; receptor and BPC-157 weights are hand-set; tracking priors are admittedly synthetic). Clinical validation cannot proceed until every parameter has a documented, verifiable source or is fit on real data with proper methodology.
- **No validation cohort exists.** None of these models has been evaluated against held-out human outcomes. This is the central deficiency.
- **Leakage/overfitting risk:** when models are eventually fit on data, train/validation/test separation and avoidance of leakage must be designed in and documented.

### 11.2 Polygenic risk scores (`prs_calculator.py`)

Follow **PGS Catalog** reporting standards and ClinGen complex-disease guidance.

- **Specification & provenance:** register each score (SNP list, effect alleles, betas, source GWAS with PMIDs/PGS IDs, build, strand). Verify effect-allele orientation and that betas match the cited source. Replace ad-hoc reference mean/SD with values derived from a defined reference panel.
- **Ancestry:** the current crude multiplicative adjustment is inadequate; PRS are known to transfer poorly across ancestries. Required: ancestry-specific calibration (continuous ancestry via principal components, not categorical multipliers), and explicit **restriction of reportable populations** to those in which the score is validated (H-06, §15).
- **Calibration & discrimination:** evaluate in independent, ancestry-matched cohorts (e.g., suitable biobank data under appropriate governance). Report AUC, calibration plot, and absolute risk calibration. The mapping from raw score to the displayed risk/percentile must be validated, not a sigmoid heuristic.
- **Clinical meaning:** define what action (if any) a PRS result drives; if none, reconsider whether it belongs in a clinical report. Validate that PRS is not conflated with monogenic risk in the UI.
- **Acceptance:** pre-specify minimum discrimination/calibration per trait per ancestry; if not met, the score is not reported for that group.

### 11.3 Pharmacogenomics end-to-end clinical validity

Beyond analytical diplotype concordance (§9.10), validate **clinical** validity: that the predicted phenotype predicts the real metabolic/clinical phenotype and that applying CPIC guidance is appropriate. Much of this rests on CPIC's own evidence base (which is strong and authoritative), so the validation here is primarily (a) faithful, current implementation of CPIC logic, (b) correct diplotype→phenotype→recommendation chaining, and (c) honest handling of uncertainty and array limitations. The **conformal/HGNN responder probability** is a separate, non-CPIC construct (next section).

### 11.4 Conformal prediction and the responder model (`pgx/hgnn/`)

This is the most statistically misleading component as built (H-03):

- The Mondrian split-conformal method is *mathematically* valid **only** if the calibration scores are exchangeable with the deployment population. The shipped `_DEFAULT_CAL_SCORES` are synthetic; the code itself flags that they must be replaced with a real held-out PharmGKB clinical-annotation calibration set, which does not exist in the repo. The HGNN model path is disabled (`rule_based_fallback`).
- **Therefore the current "90% prediction set" provides no real coverage guarantee and must not be shown clinically.**
- To validate properly: (1) define the prediction target precisely (responder? ADR risk? — currently conflated); (2) assemble a real, representative, labeled dataset; (3) train/lock the underlying model with proper methodology and documented provenance (or keep the rule-based scorer but justify every weight); (4) compute conformal calibration on a genuine held-out exchangeable calibration set; (5) **empirically verify coverage** on an independent test set (does the 90% set contain truth ≥ 90% of the time, overall and per class/subgroup?); (6) report discrimination/calibration; (7) only then expose uncertainty, with clear labeling of what it means and does not mean.

### 11.5 Receptor expression/isoform model (`receptor_mapper.py`)

The expression "HIGH/NORMAL/LOW" and isoform calls derive from hand-curated rsID magnitude/direction modifiers with no eQTL basis. To make any clinical claim: ground each modifier in real eQTL/functional data (e.g., GTEx) with citations; validate predicted expression against measured expression in an appropriate dataset; report accuracy/calibration. Absent that, this feature is exploratory and must not be reported clinically. The clinical-template language ("likely to show enhanced response") must be removed or substantiated.

### 11.6 Peptide-response and BPC-157 predictors (`peptide_mapper.py`, `bpc157_predictor.py`)

These predict response to compounds that are predominantly investigational/off-label with little or no human RCT evidence (the README and DB seeds say so explicitly). Two layered problems:

1. **The therapy lacks human efficacy evidence** (a world-state fact the software cannot fix — §12.4).
2. **No validated genetic predictor of response to these compounds exists**; the pathway/rsID weights are mechanism-of-action *hypotheses*.

Consequently, a *clinical* "Strong Fit / Likely Good Responder" claim is **not validatable today**. Acceptable dispositions: **(a) remove from clinical scope**; or **(b) reframe explicitly as a research hypothesis** inside an IRB-approved study with informed consent, where the predictor's performance is *being studied*, not asserted (§12, §18). The mechanism/pathway content can remain as transparent educational information if clearly labeled as non-predictive. The invented tier vocabulary ("Strong Fit") must not imply validated predictive performance.

### 11.7 Bayesian longitudinal tracking (`tracking/bayes.py`, `genetics.py`)

The Normal-Normal conjugate update is correct mathematics, but the genetic-prior weights are, per the code, **synthetic/stylised**, and the measurement-noise and approach-curve parameters are guesses (garbage-in/garbage-out). To validate: derive priors from real data; fit/justify the noise and kinetic parameters from real longitudinal measurements; validate the **predictive trajectory and its 95% intervals against held-out patient time-series** (do the intervals achieve nominal coverage?); report calibration of the predictive distribution. Until then, the trajectory/CI is illustrative, not clinical, and must be labeled as such. Separately, the synthetic **seed/demo data** (`tracking/seed.py`) used to populate the tracking UI on container start must be unmistakably segregated from, and never confused with, real patient data in any clinical deployment.

### 11.8 Model monitoring, drift, and recalibration

For any model that does reach clinical use, define ongoing monitoring (§17): input-distribution drift, performance drift, calibration drift; thresholds that trigger investigation/recalibration; and a revalidation process under change control (and a PCCP if updates are anticipated). Subgroup monitoring by ancestry is mandatory given the equity risks (§15).

---

## 12. Clinical Utility and Evidence Generation

### 12.1 The ACCE/EGAPP utility question

Clinical utility asks whether using the pipeline improves outcomes or decisions versus standard care. For the *established* components (ACMG SF findings, validated PGx), utility evidence may be borrowed from existing literature and guidelines (e.g., CPIC implementations have demonstrated value; returning ACMG SF actionable findings has accepted utility). For the *novel* components (peptide-response prediction, receptor/PRS-guided peptide selection), there is **no existing utility evidence**, and it must be generated de novo or the claim must be withdrawn.

### 12.2 Study designs to generate clinical evidence

| Study type | Purpose | When to use |
|---|---|---|
| **Retrospective concordance** | Compare pipeline calls to an established reference method/expert panel on banked, consented samples | Early; analytical & clinical-validity bridging |
| **Prospective observational** | Characterize real-world performance, including build/platform diversity | Before/around limited launch |
| **Decision-impact study** | Does the report change clinician decisions? | Utility, lower cost than outcomes RCT |
| **Randomized controlled trial** | Does using the tool (and the therapy it recommends) improve patient outcomes vs. control? | Required for strong efficacy/utility claims, especially for the peptide therapies |

All human-subjects evidence generation requires **IRB approval, informed consent, and ICH-GCP conduct** (§18), and should be reported per **STARD** (diagnostic accuracy) and **SPIRIT-AI/CONSORT-AI / DECIDE-AI** (AI interventions).

### 12.3 Outcome measures and reference standards

Define, per claim, the reference standard and the clinically meaningful outcome:
- Variant interpretation → expert-panel classification; downstream: appropriate clinical action.
- PGx → measured metabolizer phenotype / drug levels / clinical drug response and ADR rates.
- PRS → incident disease over follow-up in a cohort.
- Peptide response → pre-specified, validated clinical endpoints (e.g., VAS pain, validated functional scores, imaging, the biomarker panels the engine itself proposes — which must first be validated as response surrogates, not assumed).

### 12.4 The peptide-evidence boundary (read carefully)

This plan can specify how to make the **software** trustworthy. It cannot, by itself, make **"this peptide will benefit this patient"** a valid clinical claim. The therapies the engine recommends — BPC-157, TB-500, Epithalon, Semax, GHK-Cu, Argireline, SNAP-8, and similar — are largely **not FDA-approved**, are often **compounded or research-only**, and lack the randomized human efficacy/safety data that underpins a clinical recommendation. The engine's own README states BPC-157 use is "experimental/off-label," "evidence quality is low," and "this is not medical advice"; the DB seeds label these compounds "Research only / not FDA-approved."

Implications for the validation program:
- **Validating the predictor does not validate the therapy.** Even a perfectly calibrated "responder" model predicts response to an intervention whose benefit/risk is itself unestablished.
- A clinical efficacy claim for these compounds would require **adequate and well-controlled human trials** of the therapies themselves — a separate, multi-year, expensive, and regulated clinical-research program (potentially IND-governed), far beyond software validation.
- Therefore the **recommended scope decision** (echoing §3, §11.6) is to **exclude investigational-compound efficacy claims from the clinical product**, retaining at most transparent educational/regulatory-status information, and to pursue any genuine efficacy/predictor evidence only under formal clinical research with IRB oversight and explicit consent.
- Where peptides *are* FDA-approved for an indication, claims must stay within the approved labeling, and dosing content must be traceable to FDA labeling or peer-reviewed trials (as `dossier_notes.md` itself states), with that traceability verified during validation.

---

## 13. Data Management, Privacy, and Security

Genomic data is uniquely sensitive: it is identifying, immutable, familial, and predictive. The current system has serious privacy/security gaps that are launch-blocking.

### 13.1 Current-state findings (grounded in `api.py`)

- **No authentication/authorization** on any endpoint; results retrievable by `job_id` alone.
- **Derived genomic results persisted to a flat `jobs.json`** (default under `data/`) **unencrypted**, with a 24-hour TTL. Although the raw upload is processed in memory, the persisted *results* (variants, genotypes, conditions, PGx, dossiers) are re-identifying genomic-derived data.
- **CORS allows credentials** for configured origins.
- No audit trail, no access logging, no key management, no data-subject controls.

### 13.2 Required controls

| Domain | Requirement |
|---|---|
| Authentication/authorization | Per-user identity; role-based access; results scoped to authorized users; no security-by-`job_id` |
| Encryption | TLS in transit; strong encryption at rest for all PHI/derived data; managed keys |
| Data minimization & retention | Define what is stored, where, for how long, and why; minimize; documented retention/deletion; secure deletion |
| Storage | Replace flat-file `jobs.json` with an access-controlled, encrypted, auditable datastore |
| Audit trail (Part 11) | Immutable logs of access and changes to records, tied to user identity and pipeline/KB version |
| HIPAA | If covered: Security Rule administrative/physical/technical safeguards; BAAs with any subprocessors (including external annotation services — see §13.3); breach-notification readiness |
| GINA & anti-discrimination | Governance preventing misuse of genetic information; appropriate consent language |
| Consent & data governance | Informed consent for processing, storage, secondary use, and any research; GA4GH responsible-sharing alignment |
| Secure SDLC | SAST/DAST, dependency/vulnerability scanning, SBOM, secrets management, penetration testing, secure code review (the repo includes a separate cybersecurity execution plan — align to it) |

### 13.3 External data egress

The pipeline transmits variant coordinates/rsIDs to external services (Ensembl, NCBI, gnomAD, MyVariant, UniProt, PharmGKB, GWAS, KEGG, openFDA). Even coordinate-level queries can be privacy-relevant. Validation/governance must: enumerate exactly **what user-derived data leaves the system and to whom** (a `docs/data-sources.md` is referenced for this — verify and keep current); assess re-identification risk; put **BAAs/agreements** in place where required; and consider hosting **internal mirrors** of these resources (which also serves reproducibility, §8.6) to eliminate per-patient egress for clinical reporting.

### 13.4 Validation of privacy/security controls

Security controls are verified by design review, configuration audit, vulnerability scanning, and penetration testing; privacy by a documented data-flow map, DPIA/privacy impact assessment, and verification that retention/deletion and access controls behave as specified (including the cross-job isolation test in §9.12).

---

## 14. Human Factors, Labeling, and Results Communication

Per **IEC 62366-1** and FDA human-factors guidance, the safety and effectiveness of the system depend on whether real users (clinicians and patients) interpret the outputs correctly. A correct computation that is misread is still a patient-safety problem (automation bias, H-11).

### 14.1 Current-state findings

- The patient-facing dossier (`dossier_generator.py`) presents a **"Predicted Efficacy" tier and coverage %** prominently, with a **single-line footer**: "For clinician-supervised use. Recommendations are decision support, not a prescription." The frontend has consent and "not medical advice" language.
- The strongest disclaimers (the BPC-157 caveats) live in the README, not necessarily in the patient artifact.
- Tier vocabulary ("Strong Fit," "Likely Good Responder," "CRITICAL") carries strong implied certainty not matched by the underlying evidence.

### 14.2 Required human-factors work

- **Use-related risk analysis:** identify how each output could be misinterpreted and the resulting harm (e.g., a patient reading "Strong Fit" as "this drug will work for me").
- **Labeling and report redesign:** clearly communicate (a) what each result means, (b) its evidence level and uncertainty, (c) genome build, KB version, and date, (d) limitations (build/platform/ancestry/variant-class scope), and (e) prominent, context-appropriate disclaimers — especially distinguishing **validated** findings (e.g., ACMG SF, CPIC) from **investigational/educational** content. Remove or strongly reframe efficacy claims for investigational compounds (B-4).
- **Provenance display:** show the basis for each call (sources, evidence) so a clinician can independently review it (supports CDS transparency, §3.4, and H-11 control).
- **Formative + summative usability testing:** with representative clinicians and patients, on representative tasks, to validate that outputs are understood as intended and that critical use errors are eliminated or mitigated. Pre-specify acceptance (no uncorrected critical use errors).
- **Reading-level and accessibility** of patient materials; truthful framing of certainty.
- **Sign-out integration:** the clinician review/amend/e-sign workflow (§10.5) is part of the validated use flow.

### 14.3 Results-return policy

Define and validate policies for returning results, including: secondary/incidental findings (the ACMG SF panel is central here), how/whether VUS are communicated, re-contact on reclassification (H-09), and pre/post-test counseling expectations. These are clinical-governance artifacts approved by the Medical Director and Clinical Advisory Board (§18).

---

## 15. Bias, Equity, and Generalizability

Genomic tools systematically underperform in under-represented populations, and this system has concrete equity risks baked in.

### 15.1 Current-state findings
- **PRS** uses European-derived betas and reference mean/SD with **crude categorical ancestry multipliers** (`prs_calculator.py`) — a known-inadequate transfer method.
- **Star-allele** definitions and array tag-SNP coverage vary in completeness across ancestries (some alleles are population-specific).
- **STR/AR** interpretation uses hand-set ancestry reference means.
- Truth sets and validation cohorts, if European-skewed, will hide poor minority performance.

### 15.2 Requirements
- **Ancestry-stratified validation:** report every analytical and clinical performance metric stratified by genetic ancestry; pre-specify minimum acceptable performance per group.
- **Bounded reporting:** if a model (e.g., a PRS) is not validated in a population, **do not report it for that population** (H-06) and say so plainly.
- **Representative reference materials and cohorts:** deliberately include diverse GIAB/GeT-RM/Coriell samples and ancestry-diverse validation cohorts.
- **Continuous ancestry handling** (principal components) rather than categorical multipliers for any ancestry adjustment that remains.
- **Equity monitoring** post-deployment (§17), with subgroup performance dashboards.
- **Health-equity review** by the Clinical Advisory Board of all reportable claims and their population scope.

---

## 16. Statistical Analysis Plan (SAP)

A pre-specified SAP, authored/approved by the biostatistician, governs every validation study so that acceptance is decided before data are seen (no post-hoc moving of goalposts).

### 16.1 General principles
- **Pre-specification** of hypotheses, metrics, acceptance thresholds, and analysis populations before execution.
- **Confidence intervals**, not point estimates alone; acceptance is typically stated on a CI bound (e.g., "lower 95% CI of sensitivity ≥ 99%").
- **Multiplicity** control where many claims/subgroups are tested.
- **Missing data / indeterminate** handling defined a priori (including silent-drop reconciliation, §9.7).
- **Sample-size justification** for each study, powered so the relevant CI bound can meet the threshold at the expected performance and prevalence.

### 16.2 Metric definitions and acceptance (representative; finalize per claim)

| Claim | Primary metric | Representative acceptance (to be ratified) |
|---|---|---|
| SNV genotype/variant accuracy | Sensitivity, specificity vs. GIAB | Sens ≥ 99.0%, Spec ≥ 99.5% (lower 95% CI bound) |
| Build detection | Correct-build rate | ≥ 99% on labeled corpus; 0 silent mis-processing |
| Annotation concordance | % agreement with pinned KB | ≥ 99.5% on tested loci |
| Variant interpretation | Concordance with expert-panel class | High concordance; **zero tolerance** target for false-benign on actionable genes (investigated individually) |
| PGx diplotype | Concordance with GeT-RM consensus | ≥ 99% on reportable alleles; SV-limited genes bounded |
| PGx phenotype/recommendation | Correct CPIC mapping | 100% on the implemented table (deterministic) |
| PRS | AUC, calibration (per ancestry) | Pre-specified per trait/ancestry; else not reported |
| Conformal coverage | Empirical coverage vs. nominal | Within tolerance of nominal on independent test set; else not shown |
| Precision | Repeatability/reproducibility concordance | ≥ pre-specified; identical across version-frozen reruns |
| Usability | Critical use errors | Zero uncorrected critical use errors |

### 16.3 Reference-standard and truth-set governance
Document the provenance, version, and limitations of every truth set; pre-register the validated configuration; lock analysis code; archive raw results for audit.

---

## 17. Post-Market Surveillance and Change Control

Validation is not a one-time event; a genomic pipeline lives in a changing world (databases reclassify, guidelines update, populations shift, dependencies change).

### 17.1 Change control
Any change to the validated configuration — engine code, dependency versions, external KB snapshot, model weights/tables (PRS betas, CPIC table, star-allele defs, condition library, peptide/receptor/tracking weights), or runtime config — goes through documented change control with **impact analysis** determining the scope of revalidation (from a targeted regression run to a full re-validation). A **Predetermined Change Control Plan (PCCP)** can pre-authorize bounded model/KB updates with pre-specified validation, avoiding re-clearance for each routine update (especially relevant for CPIC and ClinVar refreshes).

### 17.2 Surveillance
- **Performance monitoring:** ongoing metrics on real-world inputs; input-distribution and performance/calibration drift detection; ancestry-subgroup monitoring (§15).
- **Knowledge-base currency:** controlled cadence for updating ClinVar/gnomAD/CPIC/PharmVar snapshots, each triggering impact analysis and possible re-interpretation/re-contact (H-09).
- **Complaint handling, error/CAPA, and adverse-event/MDR reporting** (if a device): a route for clinicians to report suspected errors, investigated under CAPA.
- **Reclassification management:** process to re-interpret prior results when a variant's classification changes and to act on the patient re-contact policy (§14.3).
- **Dependency/security surveillance:** monitor and patch dependency vulnerabilities; re-run security tests after changes.

### 17.3 Periodic re-validation
Schedule periodic re-validation (e.g., annually and on major dependency/guideline changes) and management review of the overall validation state and benefit-risk.

---

## 18. Governance, Ethics, and Oversight

### 18.1 Accountable roles
Clinical operation requires named, qualified, accountable people (§6.3): a **Medical Director** (licensed physician accountable for clinical content and benefit-risk), a **Laboratory Director** (if CLIA), **board-certified clinical molecular geneticists / variant scientists** for interpretation sign-off, a **clinical pharmacist/PGx expert** for the PGx content, a **biostatistician**, a **Quality/Regulatory Lead**, and a **Security/Privacy Officer**.

### 18.2 Clinical Advisory Board
An independent multidisciplinary board (clinical genetics, pharmacogenomics, the relevant therapeutic areas, bioethics, health equity, biostatistics) reviews and approves: the reportable claim set and population scope, interpretation and results-return policies, the benefit-risk of any investigational features, and major changes.

### 18.3 Research ethics
Any evidence-generation involving human subjects or their data (retrospective concordance on banked samples, prospective studies, the peptide-response/predictor studies, biobank PRS validation) requires **IRB/ethics approval, informed consent appropriate to the use (including secondary use and return-of-results), and ICH-GCP-compliant conduct.** Using patient genomes to *study* an unvalidated predictor is research and must be governed as such — it cannot be done under the guise of clinical care.

### 18.4 Informed consent and disclosure
Patient-facing consent must truthfully disclose: what is analyzed; what is and is not validated; that investigational-compound content (if retained at all) is not proof of benefit; data storage, sharing (including external services), retention, and rights; and the limitations (build/platform/ancestry/variant-class). GINA and anti-discrimination protections must be explained.

### 18.5 Conflicts of interest
Where the same organization both recommends and supplies/sells peptide therapies, the conflict of interest must be governed transparently; recommendation logic must be defensible on clinical grounds independent of commercial interest, and this independence is something the Advisory Board and any auditor will scrutinize.

---

## 19. Validation Execution Plan — Phases, Timeline, Resources, Cost

The work is sequenced so that foundational correctness and safety come first, then analytical validation, then clinical validation of established claims, with investigational claims handled on a separate research track. Durations are planning-level estimates for a small, focused, appropriately staffed team; they assume access to reference materials, validation cohorts, and qualified clinical personnel. They are **not** commitments.

### 19.1 Phase 0 — Containment and honest labeling (≈ 4–8 weeks)
**Goal:** make the current system safe-by-default and honest while the program spins up.
- B-1: Genome-build detection + reject-non-GRCh38 (interim hard block) (H-01).
- B-2: Eliminate silent variant drop; fail loudly and traceably (H-07).
- B-3: Add authentication and encrypt/protect persisted data; remove flat-file PHI exposure (H-08).
- B-4: Remove/strongly relabel patient-facing efficacy claims for investigational compounds (H-04).
- B-5: Draft the intended-use & regulatory-determination memo (§3).
- Freeze a versioned, deterministic baseline configuration.
**Exit:** no launch-blocking hazard active without an interim control; documented IUS direction.

### 19.2 Phase 1 — Foundations (≈ 3–6 months, overlaps Phase 0)
**Goal:** the system-level scaffolding any clinical software requires.
- Stand up the QMS (§6): document control, design controls/DHF, SOPs.
- Risk management file (§7) with the full hazard register.
- SRS + RTM (§8.2); software classified Class C; lifecycle records begun.
- Verification uplift: coverage targets, negative/robustness/determinism suites, golden fixtures, static analysis, SBOM, dependency pinning (§8.3–8.4).
- Knowledge-base snapshotting & version pinning; internal mirrors plan (§8.6, §13.3).
- Security program: secure SDLC, encryption, audit trail, pen-test plan (§13).
- Regulatory strategy & claims register finalized (§3.7).

### 19.3 Phase 2 — Analytical validation (≈ 6–12 months)
**Goal:** prove the pipeline reads the genome correctly.
- Acquire/prepare reference materials (GIAB, GeT-RM, Coriell, labeled build corpora, array-format truth) (§9.8).
- Execute analytical studies: parsing, build, QC, rsID, annotation concordance, star-allele (GeT-RM), STR, precision/reproducibility, robustness, cross-job isolation (§9).
- Analytical Validation Report(s), signed (§9.13).
**Exit gate:** analytical acceptance criteria met for the in-scope claim set, or claims bounded/removed accordingly.

### 19.4 Phase 3 — Clinical validation of established claims (≈ 12–24 months)
**Goal:** validate interpretation and the *established* predictive claims.
- Replace heuristic significance with ACMG/AMP classification workflow + sign-out, and validate against expert-panel truth (§10).
- Complete and govern the condition library (§10.3).
- Validate PGx clinical chaining and currency; bound array/SV limitations (§9.10, §11.3).
- PRS: provenance, ancestry-specific calibration/validation in independent cohorts, bounded reporting (§11.2) — or de-scope.
- Conformal/responder: rebuild on real calibration data and empirically verify coverage, or suppress the confidence output (§11.4).
- Human-factors summative validation (§14); results-return and governance policies approved (§14.3, §18).
- Clinical-validity studies and (as feasible) decision-impact/utility studies (§12).
**Exit gate:** Medical-Director-accountable benefit-risk determination per reportable claim.

### 19.5 Phase 4 — Investigational claims (multi-year, separate research track)
**Goal:** either generate genuine human evidence for the peptide-response / receptor / tracking predictors **and the therapies themselves**, under IRB-governed research, or keep them permanently out of clinical scope.
- IRB protocols, consent, prospective data collection, predictor performance studies, and (for the therapies) appropriately controlled trials (§12.4, §18.3).
- Note this track depends on world-state clinical evidence the software cannot generate alone; timelines are inherently long and uncertain.

### 19.6 Indicative resourcing
Cross-functional team: clinical bioinformatics, software engineering, biostatistics, clinical molecular genetics, clinical pharmacology/PGx, quality/regulatory, security/privacy, clinical-research operations, and product/UX; plus the Medical Director and Clinical Advisory Board. Reference-material procurement, biobank/cohort data access, external mirroring/infrastructure, audits, security testing, and (Phase 4) clinical-trial costs are material budget lines. The dominant cost and schedule drivers are the clinical-validity cohorts (Phase 3) and any therapy trials (Phase 4).

### 19.7 Critical-path dependencies
- Intended-use/regulatory decision (§3) gates the depth of everything.
- Build handling (H-01) and silent-drop (H-07) gate trustworthy analytical results.
- KB snapshotting gates reproducibility, which gates valid analytical claims.
- Reference-material and cohort access gate analytical and clinical validation respectively.
- Qualified clinical personnel gate interpretation sign-off and benefit-risk decisions.

---

## 20. Acceptance Criteria Master Table

A consolidated, pre-specified gate list. Each item is PASS/FAIL against the criterion; clinical launch of a given claim requires all of its rows PASS (or the claim is bounded/removed). Thresholds marked *(ratify)* must be confirmed by the biostatistician and Medical Director before execution.

| # | Domain | Criterion | Gate |
|---|---|---|---|
| AC-01 | Regulatory | Signed IUS + regulatory determination + claims register exist | Phase 1 |
| AC-02 | QMS | Controlled QMS, DHF, and validated-configuration baseline exist | Phase 1 |
| AC-03 | Risk | Risk file complete; all S4 hazards controlled to target; benefit-risk signed | Phase 1→3 |
| AC-04 | Build | ≥ 99% correct build detection; **0** silent non-GRCh38 processing *(ratify)* | Phase 0/2 |
| AC-05 | Completeness | No silent variant loss; expected-vs-reported reconciliation enforced | Phase 0/2 |
| AC-06 | Parsing | 100% on parsing conformance suite | Phase 2 |
| AC-07 | QC | Thresholds data-justified per in-scope platform | Phase 2 |
| AC-08 | Annotation | ≥ 99.5% concordance with pinned KB on tested loci *(ratify)* | Phase 2 |
| AC-09 | SNV accuracy | Sens ≥ 99.0% / Spec ≥ 99.5% lower-95%-CI vs GIAB *(ratify)* | Phase 2 |
| AC-10 | Precision | Repeatability/reproducibility ≥ target; identical across version-frozen reruns | Phase 2 |
| AC-11 | PGx diplotype | ≥ 99% GeT-RM concordance on reportable alleles; SV-limited genes bounded *(ratify)* | Phase 2/3 |
| AC-12 | PGx mapping | Correct, current CPIC mapping; version recorded on report | Phase 3 |
| AC-13 | Interpretation | Expert-panel concordance met; false-benign on actionable genes individually adjudicated | Phase 3 |
| AC-14 | Condition library | Complete, sourced, clinically reviewed; correct rendering | Phase 3 |
| AC-15 | PRS | Per-ancestry discrimination/calibration met or score not reported for that group | Phase 3 |
| AC-16 | Conformal/responder | Empirical coverage ≈ nominal on independent test set, or output suppressed | Phase 3 |
| AC-17 | Investigational features | Removed from clinical scope OR under IRB research with consent; no asserted efficacy | Phase 0/4 |
| AC-18 | Privacy/security | AuthN/Z, encryption, audit trail, retention, pen-test passed; cross-job isolation proven | Phase 1 |
| AC-19 | Human factors | No uncorrected critical use errors; provenance + uncertainty + build/KB/date on report | Phase 3 |
| AC-20 | Equity | All metrics ancestry-stratified; bounded reporting enforced | Phase 2/3 |
| AC-21 | Surveillance | Change control, drift monitoring, reclassification & CAPA processes operational | Phase 3 |
| AC-22 | Governance | Medical Director + Advisory Board approvals; IRB where applicable | Phase 1→4 |

---

## Appendix A — Requirements Traceability Matrix (Template)

Each requirement is uniquely identified and traced backward to its source (design input / risk control / regulation) and forward to design, implementation, and verification/validation evidence.

| Req ID | Requirement (shall statement) | Source / rationale | Risk link | Design/Module | Verification test(s) | Validation evidence | Status |
|---|---|---|---|---|---|---|---|
| REQ-001 | The system shall determine and record the genome build of every input and reject inputs not confirmed GRCh38. | IUS; analytical correctness | H-01 | build-detection module; `validators.py` | UT-build-*, IT-build-* | AC-04 study | _open_ |
| REQ-002 | The system shall not silently discard a variant; every variant shall have a recorded annotation status and incompleteness shall block reporting. | Patient safety | H-07 | `pipeline.py` annotate loop | UT-annotate-failpath; IT-network-fault | AC-05 | _open_ |
| REQ-003 | The system shall require authenticated, authorized access for all endpoints and encrypt all persisted PHI/derived data. | HIPAA; privacy | H-08 | `api.py`; datastore | system security tests; pen-test | AC-18 | _open_ |
| REQ-004 | The system shall not present heuristic priority tiers as clinical pathogenicity classifications. | Clinical validity | H-02 | `scoring.py`; reporting | UT-label; HF summative | AC-13, AC-19 | _open_ |
| REQ-005 | The system shall not display a confidence/coverage value derived from synthetic calibration. | Statistical integrity | H-03 | `conformal.py` | UT-conformal-guard; coverage study | AC-16 | _open_ |
| REQ-006 | The system shall not assert efficacy of investigational compounds in patient-facing output. | Regulatory; ethics | H-04 | `peptide_mapper.py`, `bpc157_predictor.py`, `dossier_generator.py` | UT-claims-gate; HF | AC-17 | _open_ |
| REQ-007 | The system shall record the knowledge-base snapshot version on every clinical report. | Reproducibility | H-09 | reporting; KB config | IT-kb-version | AC-08, AC-21 | _open_ |
| REQ-008 | The system shall report PGx diplotypes only within the validated, platform-supported allele set, qualifying SV-uncertain genes. | Drug safety | H-05 | `star_alleles/*` | GeT-RM concordance | AC-11 | _open_ |
| … | (extend to full coverage of the SRS) | | | | | | |

---

## Appendix B — Test Case Catalog (Template and Seed Cases)

### B.1 Categories
Unit, integration, system/API, negative/robustness, determinism, security, performance, reference-material concordance, human-factors task scenarios.

### B.2 Seed test cases

| TC ID | Category | Precondition / input | Action | Expected result | Maps to |
|---|---|---|---|---|---|
| TC-B-01 | Negative/build | A GRCh37 23andMe export of a GIAB sample | Submit to `/analyze` | Rejected (or correctly lifted) — **never** silently annotated as GRCh38 | REQ-001, AC-04 |
| TC-B-02 | Robustness/network | Valid VCF; VEP/ClinVar endpoint forced to fail for one locus | Run pipeline | Variant not lost; status recorded; report blocked or flagged | REQ-002, AC-05 |
| TC-B-03 | Concordance/SNV | GIAB HG002, GRCh38 | Run pipeline | Genotype/variant calls meet AC-09 vs truth | AC-09 |
| TC-B-04 | Concordance/PGx | GeT-RM sample with known CYP2C19 *2/*17 | Run PGx | Correct diplotype/phenotype; correct CPIC text | AC-11, AC-12 |
| TC-B-05 | PGx/limitation | Array input for a CYP2D6 *5 (deletion) carrier | Run PGx | SV-uncertain qualifier; not reported as definitive normal | REQ-008, AC-11 |
| TC-B-06 | Determinism | Fixed fixture set, version-frozen config | Run x3 across threads/days | Identical results | AC-10 |
| TC-B-07 | Security/isolation | Two patients' jobs concurrently | Retrieve results | No cross-contamination; authz enforced | AC-18, §9.12 |
| TC-B-08 | Security/authz | Unauthenticated client with a valid `job_id` | GET `/jobs/{id}` | Denied | REQ-003, AC-18 |
| TC-B-09 | Labeling | Investigational-compound code path | Generate dossier | No asserted efficacy; correct disclaimers/provenance | REQ-006, AC-17, AC-19 |
| TC-B-10 | Conformal guard | PGx run without real calibration file | Request drug prediction | Confidence/coverage value suppressed or labeled non-guaranteed | REQ-005, AC-16 |
| TC-B-11 | Interpretation | ClinVar 4-star pathogenic variant on actionable gene | Run pipeline | Reported per ACMG/AMP with provenance; signed out | AC-13 |
| TC-B-12 | Reproducibility/KB | Same input, two KB snapshot versions | Run pipeline | KB version recorded; difference attributable & controlled | REQ-007, AC-08 |

---

## Appendix C — Reference Materials and Truth Sets

| Resource | Use | Notes |
|---|---|---|
| **GIAB / NIST** HG001–HG007 | SNV/indel accuracy & precision | Use high-confidence regions; GA4GH `hap.py` benchmarking; multiple ancestries |
| **GeT-RM (CDC)** Coriell PGx panels | Star-allele concordance | Consensus diplotypes for CYP2D6/2C19/2C9/TPMT/NUDT15/DPYD/SLCO1B1/UGT1A1/VKORC1 |
| **ClinVar expert-panel (3–4★) / ClinGen** | Interpretation truth | Include conflicting & reclassified variants |
| **gnomAD (versioned)** | Frequency reference | Pin version; GRCh38 |
| **Coriell / EMQN repeat panels** | STR/AR sizing | For ExpansionHunter validation |
| **Labeled GRCh37/GRCh38 corpora** | Build detection | Multi-platform |
| **Array-format GIAB exports / simulated array genotypes** | Consumer-array path | Validate 23andMe/AncestryDNA parsing & calling |
| **Independent biobank cohorts (governed)** | PRS & clinical-validity studies | Ancestry-diverse; IRB/data-use agreements |

---

## Appendix D — Hazard Analysis Register (Worked Entries)

The seed entries H-01…H-11 in §7.3 form the start of the register. The full ISO 14971 register must, for each hazard: enumerate foreseeable sequences of events; estimate pre- and post-control risk on the approved S×P scales; specify each risk-control measure and its verification; record residual risk; and feed the overall benefit-risk. The register is a living controlled document updated at every release and on every field signal. High-priority entries to expand beyond the seeds include: multiallelic/strand handling errors; sex-chromosome/ploidy handling; compound-heterozygosity blindness (no phasing); CPIC staleness; condition-library mis-mapping; demo/seed tracking data leaking into clinical views (`tracking/seed.py`); and automation bias in report consumption.

---

## Appendix E — Module Validation Status Register (As-Built)

A snapshot of each module's clinical-readiness, to be maintained as a living register. (Ratings per §5.1 key.)

| Module | Claim class | Status | Required before clinical use |
|---|---|---|---|
| `validators.py` / `parsers.py` / `quality_filter.py` | Analytical (foundational) | 🟡 | Build handling; platform-justified QC; scope/limitation labeling |
| `rsid_resolver.py` | Analytical | 🟡 | Accuracy validation; merged/retired rsID handling |
| `annotators/vep.py`,`clinvar.py`,`gnomad.py`,`myvariant.py` | Analytical+clinical | 🟠 | KB snapshot/pinning; concordance; transcript & review-status handling; no silent drop |
| `scoring.py` | Clinical (high) | 🟠 | ACMG/AMP classification or strict de-scope; remove substring inheritance logic |
| `prs_calculator.py` | Clinical (high) | 🟠 | Provenance; ancestry-specific calibration/validation; bounded reporting |
| `pgx/star_alleles/*` | Analytical (high) | 🟠 | GeT-RM concordance; bounded allele set; SV/phasing qualifiers |
| `pgx/cpic/*` | Clinical (high) | 🟡 | Currency management; chaining validation |
| `pgx/hgnn/conformal.py`,`model.py` | Clinical (high) | 🔴 | Real calibration + empirical coverage, or suppress |
| `peptide_mapper.py` | Investigational | 🔴 | Remove from clinical scope or IRB research only |
| `bpc157_predictor.py` | Investigational/speculative | 🔴 | Remove from clinical scope or IRB research only |
| `receptor_mapper.py` | Investigational | 🔴 | eQTL grounding + validation, or non-clinical |
| `tracking/bayes.py`,`genetics.py` | Investigational | 🟠 | Real priors/parameters; predictive-interval coverage validation; segregate demo data |
| `repeat_callers/expansion_hunter.py` | Analytical+clinical | 🟡 | Reference-sample validation; pinned binary/FASTA; BAM build check; interpretation evidence |
| `dossier_generator.py` | Communication | 🟠 | Human-factors validation; provenance/uncertainty/build/KB; claim gating |
| `api.py` (+ persistence) | Infrastructure | 🔴 | AuthN/Z; encryption; audit trail; PHI-safe storage |
| `regulatory/*` | Informational | 🟢 | Verify accuracy & disclaim as informational |

---

## Appendix F — Glossary

- **Analytical validity** — accuracy/precision of measuring what the assay claims to measure.
- **Clinical validity** — how well the measurement predicts the clinical state of interest.
- **Clinical utility** — whether using the test improves outcomes/decisions.
- **ACMG/AMP** — standards for sequence-variant pathogenicity classification.
- **ACMG SF** — Secondary Findings gene list (the "ACMG81" panel here).
- **CPIC** — Clinical Pharmacogenetics Implementation Consortium (gene/drug dosing guidance).
- **PharmVar** — pharmacogene variation (star-allele) nomenclature authority.
- **GeT-RM** — CDC Genetic Testing Reference Materials program.
- **GIAB** — Genome in a Bottle (NIST reference genomes/truth sets).
- **PRS** — polygenic risk score.
- **Conformal prediction** — method producing prediction sets with a coverage guarantee *given exchangeable calibration data*.
- **SaMD / CDS** — Software as a Medical Device / Clinical Decision Support.
- **CLIA / CAP** — U.S. lab certification / accreditation.
- **IVDR** — EU In Vitro Diagnostic Regulation.
- **DHF / RTM / SRS** — Design History File / Requirements Traceability Matrix / Software Requirements Specification.
- **PCCP** — Predetermined Change Control Plan (for AI/ML updates).
- **VUS** — Variant of Uncertain Significance.

---

## Appendix G — References and Standards (Indicative)

> Citations are listed for the reviewer to obtain authoritative current versions; verify the latest revision of each before use.

1. Richards S, et al. *Standards and guidelines for the interpretation of sequence variants* (ACMG/AMP). Genet Med. 2015. (+ ClinGen SVI updates.)
2. ACMG Secondary Findings (SF) policy statement and current gene list (v3.x).
3. Roy S, et al. *Standards and Guidelines for Validating Next-Generation Sequencing Bioinformatics Pipelines* (AMP/CAP). J Mol Diagn. 2018.
4. CDC/Gulley ML, et al.; ACMG analytical validation guidance for molecular genetic tests.
5. CLSI MM09, MM17, EP05, EP12, EP17 (nucleic-acid methods; validation; precision; qualitative evaluation; LoD).
6. CLIA (42 CFR 493); CAP Molecular Pathology and NGS (incl. bioinformatics) checklists.
7. CPIC guidelines (gene/drug); PharmVar allele definitions; Pratt VM, et al. PGx allele reporting standards (AMP/CAP/ASCP/CPIC).
8. PGS Catalog reporting standards; Wand H, et al. *Improving reporting standards for polygenic scores* (ClinGen/PGS Catalog). Nature 2021.
9. Collins GS, et al. **TRIPOD** and **TRIPOD-AI**; Wolff RF, et al. **PROBAST**/PROBAST-AI.
10. Bossuyt PM, et al. **STARD 2015**; **SPIRIT-AI/CONSORT-AI**; **DECIDE-AI**.
11. ISO 13485; ISO 14971 (+ AAMI TR34971 for AI); IEC 62304; IEC 62366-1; GAMP 5 (ISPE).
12. 21 CFR Part 820 / QMSR; 21 CFR Part 11; FDA SaMD and Clinical Decision Support guidances; IMDRF SaMD framework.
13. FDA **Good Machine Learning Practice (GMLP)**; FDA guidance on Predetermined Change Control Plans for AI-enabled devices.
14. EU IVDR 2017/746; relevant MDCG guidance.
15. HIPAA Privacy & Security Rules; NIST SP 800-66/800-53; GINA; Common Rule (45 CFR 46); ICH-GCP E6(R3); GA4GH Framework for Responsible Sharing of Genomic and Health-Related Data.
16. GA4GH benchmarking tools / `hap.py`; NIST Genome in a Bottle.

---

## Appendix H — Per-Gene Pharmacogenomics Validation Matrix

PGx is the highest-stakes *near-term-validatable* claim set (drug safety, real CPIC evidence base). Each reportable gene must be validated individually because each has distinct allele complexity, platform-coverage, and structural-variation considerations. The matrix below is the validation work plan per gene; "reportable allele set" must be finalized against the actual input platform's probe content before testing.

| Gene | Key alleles / function | Platform-coverage risk | Structural-variation risk | Phasing sensitivity | Validation reference | Bounding action if criteria not met |
|---|---|---|---|---|---|---|
| **CYP2C19** | `*2`,`*3` (no function), `*17` (increased) | Moderate (tag SNPs usually present) | Low | Moderate (multiple defining variants) | GeT-RM consensus | Suppress alleles not probe-covered |
| **CYP2D6** | `*3/*4/*5/*6/*10/*17/*41`, gene deletion/dup/hybrids | **High** | **High (CNV/`*5`/hybrids undetectable on array)** | **High** | GeT-RM (deep) | Report only SNP alleles with "SV not assessed" qualifier and reduced confidence, or suppress; require orthogonal assay for actionable calls |
| **CYP2C9** | `*2`,`*3` (reduced) | Moderate | Low | Low–moderate | GeT-RM | Bound to covered alleles |
| **TPMT** | `*2`,`*3A`,`*3B`,`*3C` (reduced) | Moderate | Low | **High (`*3A` = two variants in cis)** | GeT-RM | Require phasing confidence or orthogonal confirmation for `*3A` vs `*3B`+`*3C` |
| **NUDT15** | `*3` (reduced) | Moderate | Low | Low | GeT-RM | Bound to covered alleles |
| **DPYD** | `*2A`,`*13`, c.2846A>T, HapB3 (toxicity) | Moderate–high (rare variants often off-array) | Low | Moderate | GeT-RM / curated | **Critical safety**: do not report "normal" when key variants unprobed; explicit "limited panel" qualifier |
| **SLCO1B1** | `*5`/`*15` (function) | Moderate | Low | Moderate | GeT-RM | Bound to covered alleles |
| **UGT1A1** | `*28` (TA repeat), `*6` | **High (TA-repeat not a SNP; array tag-SNP proxy imperfect)** | Moderate (repeat) | Low | GeT-RM | Report repeat status only if validated proxy exists; else suppress |
| **VKORC1** | `-1639G>A` (warfarin dose) | Low | Low | Low | GeT-RM | Standard validation |

**Per-gene acceptance:** diplotype concordance with GeT-RM consensus ≥ 99% on the *reportable* allele set, with **zero unflagged false-normal calls on safety-critical genes (DPYD, CYP2D6)**. Phenoconversion logic (comedication effects) validated against CPIC rules. Each gene's limitations are stated in the report.

**Why this matters concretely:** the code already concedes CYP2D6 from arrays is "intrinsically incomplete (no CNV / *5 deletion / hybrids)" and lowers confidence to 0.55 with an `evidence_tier='tentative-no-sv'`. Validation must convert that internal flag into a *reported*, human-factors-validated qualifier so a prescriber never mistakes an array-limited CYP2D6 result for a definitive one (H-05).

---

## Appendix I — Analytical Study Protocols (CLSI-Style Outlines)

These outline the executable protocols referenced in §9. Final protocols are controlled QMS documents with pre-specified SAPs (§16).

### I.1 Accuracy / concordance study (per CLSI EP12-style qualitative evaluation + GA4GH benchmarking)
- **Objective:** quantify agreement between pipeline calls and reference truth.
- **Samples:** all in-scope GIAB samples (≥ 5–7 distinct genomes spanning ancestries) plus targeted panels enriching rare/important variants; GeT-RM panel for PGx.
- **Procedure:** run each sample through the frozen pipeline + validated configuration; compare to truth within high-confidence regions using GA4GH `hap.py` for small variants and consensus comparison for diplotypes.
- **Analysis:** sensitivity, specificity, PPV, NPV with 95% CIs, overall and stratified (variant type, region difficulty, platform, ancestry). 2×2 reconciliation per stratum; adjudicate discordances (true error vs. truth-set limitation).
- **Acceptance:** §16.2 / Appendix table; pre-ratified.

### I.2 Precision study (per CLSI EP05-style)
- **Repeatability:** ≥ 20 replicates of representative samples within a single run/operator/environment.
- **Reproducibility:** replicates across ≥ 3 days, ≥ 2 operators, ≥ 2 environments, and — critical for software — **across the exact frozen software + KB version** (and a deliberate negative: across a *changed* version to demonstrate change-detection).
- **Analysis:** percent agreement / variance components; for any quantitative outputs (e.g., PRS, repeat length), report SD/CV.
- **Acceptance:** version-frozen reruns identical (or within defined tolerance); cross-condition agreement ≥ pre-specified.

### I.3 Analytical sensitivity / limit-of-detection (where quantitative; e.g., STR sizing)
- Characterize the repeat-length range over which AR CAG sizing is reliable; identify the upper bound beyond which short-read sizing degrades; report as reportable range.

### I.4 Robustness / interfering-factors study
- Inputs deliberately perturbed: degraded quality (low GQ/DP near thresholds), missingness, multiallelic sites, strand issues, format quirks (CRLF/BOM/whitespace), mixed/incorrect build, truncation, oversize, non-UTF-8.
- **Acceptance:** correct, graceful, **non-lossy, non-silent** behavior on every case; build hazard (H-01) and silent-drop hazard (H-07) provably controlled.

### I.5 Build-detection study
- **Samples:** labeled GRCh37 and GRCh38 files across platforms (clinical VCF, 23andMe, AncestryDNA, rsID list, CSV).
- **Analysis:** confusion matrix of detected vs. true build; "unknown" handling.
- **Acceptance:** ≥ 99% correct identification; **0** instances of non-GRCh38 silently processed as GRCh38.

### I.6 Cross-job isolation / carryover-analog study
- Run interleaved jobs for distinct synthetic "patients" with known-different genotypes under concurrency; verify no result/cache bleed and correct authorization scoping.
- **Acceptance:** zero cross-contamination; zero unauthorized retrieval.

### I.7 Sample-size note
Each study is sized so the lower bound of the 95% CI on its key metric can meet the acceptance threshold at the expected performance level. For example, to claim sensitivity ≥ 99% with a lower 95% CI bound also ≥ 99% requires observing a large number of true positives with zero/near-zero misses; rare variant classes therefore require deliberate enrichment beyond what genome-wide truth sets provide. The biostatistician finalizes sizes in the SAP.

---

## Appendix J — End-to-End Traceability Walkthrough (Single Sample)

To make the abstract concrete, this traces one hypothetical sample and shows where each validation gate applies. (Illustrative; not a real patient.)

1. **Upload** — A clinician uploads `patient.txt`, a 23andMe v5 export.
   - *Gate:* AuthN/Z (REQ-003, AC-18); size/format validation; **build detection** — v5 exports are commonly GRCh37 → REQ-001 must detect this and either reject or validly lift over. *Today this is the failure point: the file would be silently treated as GRCh38 (H-01).*
2. **Parse** — rsID+genotype rows → variant dicts.
   - *Gate:* parsing conformance (AC-06); zygosity correctness.
3. **QC** — hom-ref/failed/indel drop; GQ/DP (N/A for array genotype calls — note the QC semantics differ for arrays vs VCF, which itself must be validated).
   - *Gate:* AC-07; documented array-vs-VCF QC behavior.
4. **Panel/BED filter** — ACMG81 + peptide BED (production forces this).
   - *Gate:* validated configuration captures exact filters (§8.4).
5. **rsID resolution → annotation** — Ensembl/VEP/ClinVar/gnomAD against the **pinned KB snapshot**.
   - *Gate:* annotation concordance (AC-08); **no silent variant drop** (REQ-002, AC-05); KB version recorded (REQ-007).
6. **Interpretation** — significance per ACMG/AMP (not the heuristic), with provenance and review status.
   - *Gate:* AC-13; clinician sign-out (§10.5).
7. **PGx** — star alleles → phenotype → CPIC; conformal output **suppressed** unless really calibrated.
   - *Gate:* AC-11/AC-12 (per Appendix H); AC-16 (REQ-005).
8. **PRS / receptor / peptide / BPC-157 / tracking** — only reported if validated/in-scope; investigational features gated out of clinical view.
   - *Gate:* AC-15, AC-17 (REQ-006).
9. **Dossier render** — provenance, uncertainty, build, KB version, date, disclaimers; no asserted investigational efficacy.
   - *Gate:* AC-19 (REQ-004, REQ-006); human-factors validation (§14).
10. **Persist & deliver** — encrypted, access-controlled, audited record; retention policy applied.
    - *Gate:* AC-18; Part 11 audit trail (§8.5).

Every numbered step has at least one acceptance criterion; a failure at any gate blocks clinical reporting of the affected claim.

---

## Appendix K — Privacy Data-Flow Inventory (To Complete and Maintain)

A controlled, current inventory of what user-derived data exists, where it goes, and how it is protected. Seed structure:

| Data element | Origin | Stored where | Leaves system to | Protection required | Status |
|---|---|---|---|---|---|
| Raw genome upload | User | In-memory only (per `api.py`) | — | TLS in transit; never persisted | Verify claim holds under all paths |
| Variant coordinates / rsIDs | Derived | In-memory + queries | Ensembl, NCBI, gnomAD, MyVariant, UniProt, PharmGKB, GWAS, KEGG | Egress assessment; BAAs / internal mirrors; re-identification review | **Open** (egress unmanaged) |
| Annotated results / scores / PGx / PRS | Derived | **`jobs.json` (unencrypted, TTL 24h)** | Frontend clients | Encrypted, access-controlled, audited datastore | **Open (H-08)** |
| Dossiers (HTML) | Derived | Job store | Clinician/patient | Same as results | **Open** |
| Tracking measurements | User/clinician | Tracking DB (`engine/tracking/db.py`) | — | Encryption, authz, audit | **Open** |
| Demo/seed tracking data | Synthetic | Tracking DB on container start | — | Must be unmistakably segregated from real data | **Open** |
| Audit logs | System | (none today) | — | Immutable, retained | **Missing** |

Completing this inventory, performing a DPIA/privacy-impact assessment, and putting the required agreements/mirrors in place are Phase 1 deliverables (§13).

---

## Appendix L — ACMG/AMP Evidence Operationalization (Replacing the Heuristic Scorer)

To move from `scoring.py`'s arbitrary points to a defensible clinical classification, operationalize the ACMG/AMP evidence framework. This is a specification sketch for the workflow that §10.1 Path A requires.

| ACMG code | Meaning (abbrev.) | Candidate automated evidence source | Human-review requirement |
|---|---|---|---|
| PVS1 | Null variant in LoF-mechanism gene | VEP consequence + gene LoF-mechanism (ClinGen) + transcript/MANE context | Yes — PVS1 mis-application is a known error source; needs review of NMD, last-exon, etc. |
| PS1 / PM5 | Same / different AA change as known pathogenic | ClinVar known-pathogenic at codon | Yes |
| PS3 / BS3 | Functional studies | Curated functional databases | Yes — curation required |
| PS4 | Prevalence in affected | Case-control / curated | Yes |
| PM2 | Absent/rare in population | gnomAD popmax (with ancestry-aware thresholds) | Confidence-weighted |
| PM1 | Mutational hotspot/domain | UniProt/domain annotation | Yes |
| PP3 / BP4 | Computational predictions | In-silico meta-predictors (calibrated per ClinGen) | Confidence-weighted; do not over-weight |
| BA1 / BS1 | Common in population | gnomAD AF vs. disease-specific thresholds | Confidence-weighted |
| PP5 / BP6 | Reputable source (deprecated by ClinGen) | — | Do not use |

**Key points the current code violates and the workflow must fix:** ACMG/AMP is a *rule-combining* framework with explicit codes and combining rules, not an additive point total; inheritance and gene-disease validity come from authoritative sources (ClinGen/OMIM), not substring matching; population thresholds are disease- and ancestry-specific, not a single global AF band; in-silico predictions are weak evidence and must be calibrated, not given large fixed weights; and the **final classification requires qualified human sign-out**. The automated layer's job is to *assemble and present evidence transparently* (supporting CDS independent-review, §3.4), not to assert significance.

---

## Appendix M — Detailed Work Breakdown and Deliverables Checklist

A deliverables checklist by phase (companion to §19). Each item is a controlled artifact in the DHF.

**Phase 0 (containment):**
- [ ] Build-detection + non-GRCh38 reject (code + tests) — H-01
- [ ] Loud, traceable annotation-failure handling (code + tests) — H-07
- [ ] API authentication + encrypted/protected persistence (code + tests) — H-08
- [ ] Investigational-claim gating in dossier/UI — H-04
- [ ] Intended-use direction memo (draft)
- [ ] Frozen baseline configuration record

**Phase 1 (foundations):**
- [ ] Quality manual, document-control SOP, design-control SOP
- [ ] Risk management plan + initial Risk Management File (full register)
- [ ] SRS + RTM; software safety classification record
- [ ] Verification plan; coverage targets; negative/robustness/determinism suites; CI gating
- [ ] Static analysis, SAST/DAST, SBOM, dependency pinning/lockfiles
- [ ] KB snapshotting design + internal-mirror plan
- [ ] Security architecture, encryption, audit trail, Part 11 datastore design; pen-test plan
- [ ] Regulatory strategy + claims register (final)
- [ ] Privacy data-flow inventory + DPIA (Appendix K)

**Phase 2 (analytical validation):**
- [ ] Reference-material procurement & qualification (Appendix C)
- [ ] Protocols I.1–I.7 executed; raw data archived
- [ ] Per-gene PGx validation (Appendix H)
- [ ] Analytical Validation Report(s), signed

**Phase 3 (clinical validation, established claims):**
- [ ] ACMG/AMP classification workflow + sign-out (Appendix L) validated
- [ ] Condition library completed, sourced, reviewed
- [ ] PGx clinical chaining + currency management validated
- [ ] PRS provenance + ancestry-specific calibration/validation (or de-scope)
- [ ] Conformal/responder rebuilt + coverage-verified (or suppressed)
- [ ] Human-factors summative validation report
- [ ] Results-return, reclassification, re-contact policies approved
- [ ] Clinical-validity study report(s); decision-impact study (as feasible)
- [ ] Benefit-risk determination per claim, signed by Medical Director

**Phase 4 (investigational, research track):**
- [ ] IRB protocol(s) + consent for predictor/therapy studies
- [ ] Prospective data collection + predictor-performance evaluation
- [ ] (For therapies) appropriately controlled trial design and conduct
- [ ] Decision: promote to clinical scope (with full validation) or retain research-only/remove

**Cross-phase (ongoing):**
- [ ] Change-control + configuration-management records
- [ ] Surveillance/drift monitoring dashboards (incl. ancestry subgroups)
- [ ] CAPA log; complaint handling; periodic re-validation; management reviews

---

## Appendix N — Clinical Hazard Vignettes (Why the Gaps Matter)

Abstract risk ratings become persuasive when made concrete. These illustrative vignettes show how *specific current code behaviors* translate into patient harm. They are hypothetical but mechanistically faithful to the as-built system.

### N.1 The build mix-up (H-01)
A 58-year-old woman uploads an older 23andMe export (GRCh37) through a partner clinic. The pipeline never checks build and queries VEP/ClinVar/gnomAD with the coordinates as if they were GRCh38. At a position that is a benign polymorphism on GRCh37, the *same numeric coordinate* on GRCh38 corresponds to a different base and a different gene context; the annotation returned is for the wrong locus entirely. Two failure modes follow: (a) a true pathogenic ACMG SF variant she actually carries is annotated as something benign and never surfaced — a **missed actionable finding**; and (b) an unrelated position is annotated as pathogenic and surfaced as "CRITICAL," prompting unnecessary follow-up, anxiety, and cost. Neither she nor the clinician has any signal that the build was wrong. *Control:* REQ-001 build detection + reject/liftover; AC-04; the result never leaves the system without a confirmed build.

### N.2 The vanishing variant (H-07)
A clinical VCF is processed during a transient Ensembl outage. For three loci, `fetch_vep` raises; the threaded loop's `except Exception: print(...)` drops those three variants. One was a pathogenic *BRCA2* frameshift. The report is generated, looks complete, lists no error, and shows no high-tier finding for that gene. The clinician reasonably concludes "nothing actionable here." The patient is not offered the screening/risk-reduction that an ACMG SF *BRCA2* finding warrants. *Control:* REQ-002 — fail loudly, retry/queue, reconcile expected-vs-reported counts, block the report on incompleteness; AC-05.

### N.3 False confidence from synthetic calibration (H-03)
A prescriber considering an antidepressant sees the drug panel report "Predicted responder — 90% prediction set." The number derives from the conformal module's synthetic `_DEFAULT_CAL_SCORES`, not from any real calibration cohort, and the HGNN path is disabled. The "90%" has no empirical coverage meaning. The prescriber, reasonably trusting a precise-looking probability, weights it in the decision. *Control:* REQ-005 — suppress the value until coverage is empirically verified on real, exchangeable data; AC-16; honest labeling of uncertainty source.

### N.4 The array CYP2D6 trap (H-05)
A patient who is actually a CYP2D6 poor metabolizer by virtue of a `*5` whole-gene deletion is genotyped on a consumer array. The array cannot see the deletion; the SNP-based caller finds the remaining haplotype and, without the SV context, the diplotype looks like a normal-function result. A CYP2D6-metabolized opioid (e.g., codeine→morphine) or atomoxetine decision is made on a false "normal metabolizer" basis. The code internally flags this (`evidence_tier='tentative-no-sv'`, confidence 0.55) but that flag is not a human-factors-validated reported qualifier. *Control:* REQ-008 + Appendix H — report CYP2D6 from arrays only with a validated "structural variation not assessed" qualifier and reduced confidence (or suppress), require orthogonal confirmation for actionable calls, and make the qualifier comprehensible at point of care (AC-11, AC-19).

### N.5 The investigational "Strong Fit" (H-04)
A patient receives a printed dossier headed "Predicted Efficacy: Strong Fit" for BPC-157, with a coverage percentage and confident mechanistic narrative, and a single-line footer. BPC-157 is not FDA-approved, human efficacy data are minimal, and no validated genetic predictor of response exists; the "Strong Fit" derives from hand-set pathway weights the module itself labels speculative. The patient interprets "Strong Fit" as "my genes say this will work for me," pays for compounded peptide, and forgoes evidence-based care for her osteoarthritis. *Control:* AC-17 — remove patient-facing efficacy tiers for investigational compounds from clinical scope (or confine to IRB-approved research with explicit consent); strong, honest labeling (§12.4, §14).

### N.6 The reclassification gap (H-09)
A variant reported last year as "VUS" is reclassified by an expert panel to "Likely Pathogenic" in ClinVar. Because the pipeline queries live data with no snapshot/version record and no re-interpretation process, there is no trigger to revisit the prior report and no record of which KB version produced it. The patient is never re-contacted. *Control:* REQ-007 + §17.2 — versioned KB snapshots recorded per report, controlled update cadence, re-interpretation and re-contact policy.

These vignettes are the human meaning of the launch-blocking items in §5.4. They are also the kind of scenarios a regulator, IRB, or plaintiff's expert will construct; pre-empting them through the controls above is the purpose of this plan.

---

## Appendix O — Worked Statistical Sizing Examples

Concrete illustrations of how acceptance criteria translate into study sizes, to demonstrate the rigor the SAP (§16) must apply. Numbers are illustrative; the biostatistician ratifies final designs.

### O.1 Demonstrating high sensitivity with a confidence bound
Suppose the acceptance criterion is **analytical sensitivity ≥ 99% with the lower bound of the 95% confidence interval also ≥ 99%** for SNV detection in high-confidence regions. Using an exact (Clopper–Pearson) binomial interval:
- If a study observes, say, several thousand true-positive sites with **zero** false negatives, the point estimate is 100% and the lower 95% bound rises with the number observed. Observing on the order of ~300 positives with zero misses yields a lower bound near 99% (one-sided); to hold a *two-sided* lower bound ≥ 99% comfortably and to allow for a small number of discordances, studies are typically sized to **thousands** of evaluable positive sites. GIAB genomes provide millions of high-confidence SNVs, so genome-wide sensitivity is well-powered — but **rare/important variant classes are not**, which is why targeted enrichment is required (Appendix I.7).
- *Takeaway:* "we validated on GIAB" is necessary but not sufficient; the report must show the *stratum-specific* counts and CIs for the clinically important categories, not just the genome-wide aggregate.

### O.2 The zero-false-negative problem on safety-critical PGx
For DPYD/CYP2D6 the criterion includes **zero unflagged false-normal calls**. Statistically, "zero observed in N" only bounds the true error rate from above (rule of three: with 0 events in N trials, the upper 95% bound on the rate is ≈ 3/N). To claim the false-normal rate is below, say, 1%, one needs roughly N ≥ 300 relevant evaluable cases with zero events. Because true poor-metabolizer/SV cases are uncommon, the GeT-RM panel must be **deliberately composed to include them**, possibly supplemented with characterized samples, rather than relying on whatever happens to appear in an unselected set.

### O.3 PRS calibration sample size
Demonstrating calibration (e.g., calibration slope near 1, intercept near 0) and discrimination (AUC with a useful CI) **per ancestry** requires cohorts large enough that each ancestry stratum is independently powered — not a single large European-majority cohort whose minority strata are too small to estimate. This is both a statistical and an equity requirement (§15): if a stratum cannot be powered, the score is not reported for that group (bounded reporting, H-06).

### O.4 Conformal coverage verification
A conformal predictor claiming 90% coverage must be **empirically checked**: on an independent test set, the fraction of cases whose true label lies in the prediction set should be ≈ 90%, overall and within each class/subgroup. Verifying coverage to within a few percentage points requires a test set on the order of hundreds to low-thousands of labeled cases per subgroup. The current synthetic-calibration implementation cannot pass this check because there is no real labeled data behind it; until such data and this verification exist, the coverage claim is suppressed (AC-16).

### O.5 Human-factors summative sizing
FDA human-factors guidance typically expects on the order of **≥ 15 representative users per distinct user group** (e.g., clinicians; patients) in the summative usability study, performing the critical tasks, with the acceptance of **no uncorrected critical use errors** and root-cause analysis of any use difficulties. The investigational-claim comprehension tasks (does a user correctly understand that "Strong Fit" is not a promise of benefit?) are prime candidates for these scenarios.

---

## Appendix P — Phase-0 Remediation Status (Living Changelog)

The body of this plan describes the system *as authored*. This appendix records
the Phase-0 "containment" remediation that has since landed in code, so the plan
stays honest as a living document. The original gap analysis (§5) is deliberately
left intact as the baseline.

**Important:** these changes make the system **safe-by-default and honest about
its limits**. They are necessary but **not sufficient** for clinical use — they
do not by themselves constitute analytical or clinical validation (Phases 2–4),
which remain outstanding.

| Item | Launch-blocker | What landed | Residual work |
|---|---|---|---|
| Genome build (H-01, B-1) | yes | `engine/genome_build.py` detects build; pipeline rejects confirmed non-GRCh38 coordinate (VCF) files; build recorded on result and surfaced via API. Optional, opt-in GRCh37→GRCh38 liftover (`engine/liftover.py`, `ENABLE_LIFTOVER`). | Validate detection accuracy on a labeled corpus; validate liftover concordance (§9.3); broaden build-detection evidence sources. |
| Silent variant drop (H-07, B-2) | yes | Annotation failures are logged at ERROR and recorded; result carries `analysis_status` (expected/annotated/failed/complete); API surfaces it. | Report-blocking policy on incompleteness; retry/queue strategy; per-annotator status (§9.7). |
| Synthetic conformal calibration (H-03) | yes | `conformal.py` no longer fabricates a guarantee; returns `["uncalibrated"]`/`confidence_level=None` unless a real calibration set is supplied; PGx summary states this. | Assemble a real, exchangeable calibration set and **empirically verify coverage** before enabling confidence output (§11.4). |
| Investigational efficacy claims (H-04, B-4) | yes | Peptide mapper marks non-FDA-approved peptides investigational with a neutral `pathway_match_label` + disclaimer; dossier drops "Predicted Efficacy" for them; BPC-157 and receptor-mapper narratives neutralized to mechanistic, non-predictive, non-dosing language. | Decide final disposition (remove vs IRB-research); human-factors validation of the reframed output (§14); curated regulatory-status source. |
| API auth + PHI at rest (H-08, B-3) | yes | All endpoints except `/health` require an API key (fail-closed; `ALLOW_INSECURE_NO_AUTH` dev override); job store encrypted with a Fernet `JOB_STORE_KEY` (else in-memory only); medications moved out of the URL query string. | Per-user identity/RBAC, audit trail (Part 11), key management, retention controls, pen-test (§13). |
| Demo-data segregation | — | Tracking seeder labels synthetic patients `DEMO-NNN`; seeding remains opt-in. | Enforce hard separation of demo vs clinical datastores in any deployment. |
| Heuristic scoring as clinical significance (H-02, B-6) | yes | *Partially addressed (containment).* Summaries now carry `tier_basis` and reframe critical/high tiers as explicit "prioritization signal, not a clinical diagnosis" whenever there is no ClinVar backing; clinically-reported significance still comes from ClinVar directly. | Full ACMG/AMP classification workflow with qualified human sign-out, or formal de-scope of the heuristic from any clinical surface (§10.1). |
| QMS / risk file / validated configuration (B-7) | yes | *Process work, not code.* | Stand up the minimum QMS, risk file, and frozen validated configuration (§6–§8). |

**Test status at time of writing:** full engine suite passing (499 tests), including new coverage for build detection/rejection, liftover, completeness reconciliation, uncalibrated/calibrated conformal output, investigational gating, API authentication, the medications form field, and demo labeling.

---

### Closing note

This plan is deliberately candid about the distance between the current prototype and a clinically validated system, because an honest gap analysis is the only useful starting point for real validation. The engineering in this repository is substantial and, in places, thoughtful (authentic CPIC/PharmVar definitions, mathematically sound Bayesian and conformal *frameworks*, graceful degradation, present-tense disclaimers). The work ahead is not to discard it but to (1) make it correct and safe by default, (2) prove it reads the genome accurately, (3) replace or properly validate every interpretive and predictive claim with sourced evidence and human oversight, (4) protect the data, (5) communicate honestly to clinicians and patients, and (6) keep the investigational from masquerading as the validated. Each of those is specified above with standards, study designs, acceptance criteria, and governance. The first and most urgent technical action remains unambiguous: **resolve the silent genome-build assumption before anything touches a real patient.**

*End of document.*










