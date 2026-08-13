# Study Summary: Validation of a Genomic Model for Predicting Peptide-Therapy Response and Individualized Treatment Optimization

**Developer:** Florida Man Bioscience (FMB)
**Product:** the `u4u-engine` analysis pipeline (PeptidIQ)
**Prepared by:** Curtis Dearing and Noah Jones, BMS PhD candidates, University of Florida
**Purpose:** a concise summary of the study rationale, design, data sources, and regulatory posture, prepared to support an IRB consultation and an initial review with Dr. Wayne McCormack.

---

## Objective

Florida Man Bioscience is conducting a trial to evaluate a computational model that predicts individual response to peptide therapies and supports individualized treatment optimization. The model ingests a genome file, annotates the variants against public reference databases, and produces variant prioritization, pharmacogenomic (PGx) star-allele and diplotype calls, polygenic risk scores, and peptide-therapy response predictions. The work summarized here establishes, in stages, that these predictions are accurate and clinically meaningful before any output is used to inform an individual's care.

---

## Study design

The evaluation proceeds in two stages, so that the low-risk analytical work is not delayed by the requirements of the later human-facing study.

### Stage 1: Analytical performance validation (no human subjects)

Objective: confirm that the model computes correct genomic and pharmacogenomic results on inputs whose correct answers are already established.

- Materials: cell-line reference materials (Coriell) and de-identified public benchmark datasets. No participant contact, no new specimens, and no return of results.
- Method: reference genomes are processed through the pipeline, and its CYP2D6 and CYP2C19 star-allele and diplotype calls, together with its variant classifications, are compared against published reference truth.
- Primary endpoint: diplotype and star-allele concordance against the CDC GeT-RM reference set, with sensitivity, specificity, and reproducibility measured against GIAB benchmark call sets.
- Data collected: software-accuracy metrics only. No personal, identifiable, or health information.
- Use of results: internal validation evidence, publication, and a documented record for partners and regulators.

Because Stage 1 uses only reference materials and de-identified data, FMB's position is that it constitutes Not Human Subjects Research (NHSR) or Exempt research, subject to IRB confirmation.

### Stage 2: Prospective observational clinic-partnership study (subsequent, separate protocol)

Objective: evaluate the analytical and clinical validity of the model's per-peptide response predictions by enrolling consenting adults who have independently been prescribed peptide therapy by their own clinicians (treatment-as-usual), and tracking their progress over time. The primary aim is to correlate the engine's genomic response predictions against the observed per-peptide biomarker trajectories.

Design:

- Prospective, observational, multi-site cohort study, run in partnership with peptide-prescribing clinics. FMB enrolls participants who are already on peptide therapy and follows them longitudinally using the engine's proposed per-peptide biomarker panels (`engine/peptides/measurements.py`).
- The study covers all peptides that partner clinics prescribe, including unapproved research peptides (for example BPC-157 and TB-500). These are observed as prescribed by the participant's own clinician; FMB never supplies, doses, or directs them. GLP-1 receptor agonists (Semaglutide, Tirzepatide, Liraglutide) may be highlighted first for their grade-A evidence base, but the design is not limited to them.
- Observational only. FMB does not prescribe, supply, dose, or direct any peptide, which keeps the study outside IND and drug-administration requirements (21 CFR 312.2(b)) even for unapproved peptides: the clinic prescribes, and the study observes.
- The study evaluates whether a genomic signature predicts observed biomarker response. It does not return efficacy claims or clinical directives to participants.

---

## Regulatory questions for the IRB

The following are FMB's working determinations, submitted for IRB confirmation.

| Question | Working position |
|---|---|
| Human-subjects research? | Stage 1: no (reference materials and de-identified data). Stage 2: yes. It is prospective, enrolls and contacts participants under informed consent, and touches clinic-held PHI, so it is human-subjects research and not Exempt secondary-data research. |
| Exempt, expedited, or full board? | Stage 1: NHSR (Tier A) or Exempt under 45 CFR 46.104(d)(4) (Tier B). Stage 2: expedited review (minimal or no-more-than-minimal risk, observational; likely 45 CFR 46.110 categories 5 and/or 4/7, for IRB to confirm). Full board is not anticipated unless interventions or identifiable return-of-results are added. |
| Minimal risk? | Yes for Stage 1. Stage 2 is observational, treatment-as-usual, and is expected to qualify as minimal or no-more-than-minimal risk; FMB does not prescribe, supply, dose, or direct any peptide. |
| Consent and HIPAA authorization? | Not applicable to Stage 1. Stage 2 requires informed consent plus HIPAA authorization, because partner clinics are covered entities and participant data is PHI. Consent language will also cover commercial and secondary use of research data; specific wording is requested. |
| Data-security plan? | A written data-management and security plan will be provided, covering encryption in transit and at rest, access control, retention, and PHI handling. Current API and job-store handling will be hardened before any identifiable data is processed. |
| Recruitment via institutional lists, students, patients, or employees? | No recruitment in Stage 1. Stage 2 recruits at partner clinics from patients already prescribed peptide therapy by their own clinicians, not from UF student or employee lists. Clinic staff must not pressure enrollment. |
| Coercion concerns? | Not applicable to Stage 1. Stage 2 avoids recruiting the investigators' own students, employees, or subordinates, and partner-clinic staff must not pressure patients to enroll; IRB guidance is requested on role boundaries. |
| Other reviews (HIPAA, BAA/DUA, FERPA, COI, tech transfer)? | COI: required and gating (see below). UF Innovate and tech transfer: required (patent disclosure filed). HIPAA: required for Stage 2; partner clinics are covered entities and participant data is PHI. A Business Associate Agreement (BAA) and/or Data Use Agreement (DUA) is required with each partner clinic. DUA also required for any controlled-access dataset. FERPA: not anticipated. |
| Adverse-event posture for unapproved peptides? | Unapproved research peptides are in scope but observed only. The study observes and records adverse events; it does not manage therapy or issue clinical directives. AE handling remains with the participant's own clinician. |

---

## Data sources

| Data source | Identifiable | Generated for this study | Classification | Review |
|---|---|---|---|---|
| GIAB / NIST benchmark sets (HG001 to HG007) | No | No | A: NHSR | NHSR request |
| CDC GeT-RM PGx panel (Coriell) | No | No | A: NHSR | NHSR request |
| 1000 Genomes / openSNP public genotypes | No | No | B: Exempt | Exempt determination |
| De-identified institutional or registry VCFs | Depends on key | No | B or C | Confirm de-identification; DUA if required |
| Prospective clinic-partnership enrollment, patients already prescribed peptide therapy (Stage 2) | Yes (participant-level, identifiable via partner clinic; PHI) | Yes (longitudinal biomarker tracking) | C: Expedited | Consent + HIPAA authorization, BAA/DUA per partner clinic, expedited review |
| Identifiable samples or returned results | Yes | Possibly | C: Full or expedited | Full protocol, consent, security, COI, return-of-results |

The Stage 1 analytical study is designed to remain in Classifications A and B. The prospective Stage 2 study is participant-level and identifiable (PHI held by partner clinics), and proceeds under consent, HIPAA authorization, and BAA/DUA on an expedited-review basis.

---

## Conflict of interest, intellectual property, and institutional roles

- Conflict of interest is material and central. The organization that would recommend peptides also sells them, and a UF Innovate patent disclosure covers the pipeline. A written financial conflict-of-interest management plan is expected before approval and will be disclosed proactively to the UF COI office.
- IRB approval is understood to be distinct from institutional permission to access data, recruit participants, use university resources, or commercialize intellectual property. A UF Innovate consultation is treated as an early, required step given the investigators' dual roles as UF students and company founders.
- Guidance is requested on sequencing public disclosure (posters, publications, and determination letters) to preserve patentability, and on how the UF Innovate disclosure interacts with that timing.

---

## IRB of record

The University of Florida IRB is the IRB of record. Because the program spans multiple sites, UF IRB will serve as the single IRB of record (sIRB) under 45 CFR 46.114 and NIH sIRB policy; other sites, including Florida Man Bioscience, cede review to UF through reliance agreements (SMART IRB, and OneFlorida+ where applicable). Genomic and health-data protocols route to UF IRB-01 (Gainesville Health Science Center), and filings proceed through myIRB. The remaining steps are procedural: confirming the sub-board with the HRPP and building the reliance roster.

---

## Known considerations

- Return of results. The default input filter is the ACMG SF actionable-gene panel (ACMG81), so reportable secondary findings can arise by design. A written return-of-results plan will be filed; the default posture is research-only, with no return.
- CLIA. The pipeline is not CLIA-certified, so no output may be returned as a clinical result. Protocol and consent language will state that results are research-grade and not for clinical decision-making.
- Investigational peptides versus approved drugs. All peptides that partner clinics prescribe are in scope and are observed, never supplied. Unapproved research peptides (for example BPC-157, TB-500) are observed only as prescribed by the participant's own clinician; because FMB does not prescribe, supply, dose, or direct any peptide, the study stays outside IND and drug-administration requirements (21 CFR 312.2(b)) even for these agents. Because unapproved peptides are in scope, the protocol adopts an adverse-event observation and reporting posture: observe and record AEs, but do not manage therapy or issue clinical directives.
- Genetic privacy. Consent and data-security language will address genetic-data sensitivity, re-identification risk, and GINA protections.
- Controlled-access data. Any dbGaP or managed-access dataset requires Data Access Committee approval and a DUA in addition to the IRB determination.

---

## Status and requested input

Stage 1 scoping, the data-source classification, and draft NHSR/Exempt determination language are complete and available on request. An IRB consultation and a UF Innovate consultation are being scheduled.

Input requested from Dr. McCormack:

1. Confirmation of the Stage 1 NHSR/Exempt classification and of the expedited, prospective-observational framing of Stage 2.
2. Guidance on coercion boundaries given the investigators' founder roles, since Stage 2 recruits participants at partner clinics.
3. Consent and HIPAA-authorization language, including commercial and secondary use of research data.
4. Sequencing of publication and patentability in coordination with UF Innovate.
5. Whether any element should route to HIPAA, BAA/DUA, COI, or tech-transfer review earlier than assumed.

Scheduling: the meeting times originally offered were for the week of June 24 and have now passed. A new time, in person or by Zoom, can be arranged at Dr. McCormack's convenience.

---

## Appendix: terms and source documents

**Terms.** NHSR: Not Human Subjects Research, a formal determination that an activity falls outside the Common Rule. Exempt: low-risk research exempt from full review but still requiring a determination; category 4 covers secondary use of de-identified data (45 CFR 46.104(d)(4)). PGx, star-allele, diplotype: pharmacogenomics; a named haplotype (e.g., CYP2D6\*4) and the pair an individual carries, which together set the predicted drug-metabolism phenotype. GIAB: NIST Genome-in-a-Bottle reference genomes. GeT-RM: CDC pharmacogenetic reference-material consensus genotypes on Coriell cell lines. sIRB: single IRB of record for a multi-site study. CLIA: the federal certification required to return clinical results. GINA: Genetic Information Nondiscrimination Act. IND: FDA Investigational New Drug application.

**Source documents (available on request):** `docs/irb-plan.md` (submission playbook and lane structure), `docs/irb-determination-request.md` (drafted NHSR/Exempt request), `docs/irb-plan-glp1.md` (GLP-1 variant), `docs/irb-setup-plan.md` (roadmap), `docs/enrollment-strategy.md` (Stage 2 / Lane C recruitment and ~1,000-enrolled ops target), and `docs/clinical-validation-plan.md` (validation science and endpoints).
