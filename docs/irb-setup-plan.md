# IRB Setup Plan — Performance Validation of the u4u-engine Pipeline

**Document type:** IRB strategy & submission roadmap (actionable companion to the Clinical Validation Master Plan)
**Scope:** What is required to obtain human-subjects oversight for studies that *measure the performance* of the `u4u-engine` pipeline.
**Status:** DRAFT v0.1 — planning artifact. Not legal or regulatory advice; the institution's Human Research Protection Program (HRPP)[^hrpp]/IRB[^irb] office and regulatory counsel are the authorities of record.
**Relationship to other docs:** This plan operationalizes §18 (Governance, Ethics, Oversight) of `docs/clinical-validation-plan.md`. It cross-references that master plan for intended use (§3), analytical validation (§9), clinical validation (§10–§12), and privacy/security (§13) rather than restating them.

---

> **The one-paragraph version.** "Testing the performance of this pipeline" is not a single study and does not uniformly require an IRB. It splits into three tiers of human-subjects involvement with very different burdens. **Analytical performance testing against reference materials (GIAB, GeT-RM) and de-identified public data is *not human-subjects research* and can begin now with no IRB.** The track that touches identifiable living people is now a defined, scoped study: a prospective, observational, multi-site cohort run in partnership with peptide-prescribing clinics, enrolling consenting adults who are *already* prescribed peptide therapy by their own clinicians (treatment-as-usual) and tracking their per-peptide biomarker trajectories over time. Because it is minimal-risk and observational, it takes the **expedited** IRB pathway (a full submission with informed consent and HIPAA authorization, reviewed by the chair/designated reviewer rather than the full board). The plan below partitions the work that way so the non-gated science can start immediately while the IRB package is assembled in parallel.

---

## 1. Threshold partition — what actually needs an IRB

Per the Common Rule (45 CFR 46)[^commonrule], an activity needs IRB oversight only if it is **research** involving **human subjects** — i.e., obtaining data through *intervention/interaction* with a living individual, or obtaining *identifiable private information*[^identifiable]. Map every "performance" question onto one of three tiers:

| Tier | What it tests | Data source | Human-subjects status | IRB action |
|---|---|---|---|---|
| **Tier A — Analytical validation**[^analyticalval] | Does the pipeline read the genome correctly? (variant-call concordance, sensitivity/specificity/precision; star-allele diplotype concordance; STR/CAG[^strcag] length accuracy; build handling[^buildhandling]) | **Cell-line reference materials & de-identified public truth sets** — GIAB/NIST[^giab] (NA12878 et al.), GeT-RM (CDC)[^getrm] Coriell[^coriell] PGx[^pgx] diplotypes, 1000 Genomes[^kgp] / public VCFs | **Not human subjects** (45 CFR 46.102(e)) — cell lines and de-identified public data | **None.** Start now. (Maps to master plan §9) |
| **Tier B — Secondary use of existing human data** | Does a pipeline call predict a real clinical state? (interpretation/scoring concordance, PGx phenotype concordance, PRS[^prs] calibration) using **already-collected** clinical genomes/outcomes | Banked/retrospective de-identified or coded clinical data; biobank/dbGaP[^dbgap] under a Data Use Agreement[^dua] | Often **Exempt**[^exempt] (45 CFR 46.104(d)(4) — secondary use of de-identified/recorded data) or **not-HSR**[^nhsr] | **Determination request** (fast track). DUA likely required. |
| **Tier C — Prospective observational clinic-partnership study** | Does the engine's genomic response prediction track a participant's actual per-peptide biomarker trajectory over time? Enroll consenting adults *already* prescribed peptide therapy by their own clinicians (treatment-as-usual) at partner clinics, and observe their biomarker panels longitudinally | New enrollment with informed consent + HIPAA authorization; clinic-held PHI under a BAA/DUA; identifiable, longitudinal biomarker + genomic data | **Human-subjects research** — prospective, consented, but observational and minimal-risk | **Expedited IRB submission** (45 CFR 46.110)[^expedited] — full protocol + consent + HIPAA authorization, chair/designated-reviewer review, not full board (§3, §4 below). |

**Actionable headline:** Tier A is the bulk of "does the pipeline compute correctly" and is **un-gated** — begin immediately. Tier B is fast and light. Tier C is the defined prospective study — a minimal-risk, consented, observational clinic partnership — and it takes the expedited pathway with a complete submission package (§3, §4).

> Do not let the institution's IRB *self-determine* tiers for you. For Tiers A and B, submit a short **"IRB determination request"** (a.k.a. "not human subjects research" / "exempt determination") and keep the written determination on file. That letter is what protects publications and audits — "we decided it was exempt ourselves" does not.
>
> **At UF specifically:** there is a self-service **Exempt Auto-Determination tool** for exactly this (it uses the lighter IRB 850 training[^irb850]). Use it for the Tier B exempt/not-HSR determination; note that IRB 850 alone is *not* sufficient to submit a full (Tier C) study via myIRB[^myirb] — that needs IRB 803[^irb803] (§5).

---

## 2. IRB of record — settled: UF is the single IRB (sIRB)

This question is **settled** (decided 2026-06-30): **the University of Florida IRB is the single IRB of record (sIRB)**[^sirb] for the multi-site Tier C study. This is a prospective, multi-site study conducted under UF auspices (UF investigator, UF data/resources), so UF HRPP holds review and the other participating sites — including Florida Man Bioscience and the partner clinics — **cede review to UF via reliance agreements**. No commercial/central-IRB hedging remains.

- **UF HRPP is the IRB of record.** Within UF, genomic / HIPAA[^hipaa]-protected / health-data protocols route to **IRB-01** (Gainesville Health Science Center) — IRB-01 reviews *all medical research, tissue/data banks, and anything involving HIPAA-protected data*. **Not IRB-02**, which is explicitly limited to social/behavioral/survey research and excludes clinical/tissue-bank/HIPAA studies. Submit via **myIRB**[^myirb]. *(Address submissions to the HRPP office — **not** to a named chair: the IRB-01 chair role transitions effective 2026-07-01, so a hard-coded name will go stale.)* (UF Innovate holds a patent disclosure on this pipeline — see §3.3 COI — reinforcing that this is UF-engaged research.)
- **Other sites cede to UF as sIRB via reliance agreements**[^reliance]. The reliance vehicles: **IRB-01 *is* the OneFlorida+ consortium IRB**[^oneflorida] (the natural sIRB for multi-site Florida academic and clinic collaboration), and UF participates in **SMART IRB**[^smartirb] master reliance (SMART IAA / UF Master IAA). Each partner clinic and FMB executes a reliance agreement (SMART IRB, or OneFlorida+ where applicable) ceding review to UF; FMB and the clinics do **not** run separate boards.
- **If any activity routes through the UF Jacksonville campus**, note the local board there is historically **IRB-03**; under the settled sIRB model that site still cedes to IRB-01 as the reviewing IRB of record for this protocol.

**Decision owner:** Noah + the UF faculty sponsor execute the reliance agreements and route the submission to IRB-01. UF is **AAHRPP-accredited**[^aahrpp] (since 2018), so expect rigorous documentation standards. This settles submission *mechanics*, not the structure of this plan.

---

## 3. Scoping the Tier C study — the prospective observational clinic partnership

### 3.1 What the study *is*
A **prospective, observational, multi-site cohort study** run in partnership with peptide-prescribing clinics. FMB enrolls consenting adults who have **independently** been prescribed peptide therapy by their own clinicians (treatment-as-usual), and tracks their progress over time using the engine's proposed per-peptide biomarker panels. **Primary aim:** correlate the engine's genomic response predictions against observed per-peptide biomarker trajectories, to establish the analytical and clinical validity of those predictions — a **diagnostic/predictive-accuracy design**. Report per **STARD 2015**[^stard] (diagnostic accuracy) and **TRIPOD-AI / PROBAST-AI**[^tripod] (prediction models). Primary endpoints are concordance/sensitivity/specificity/PPV-NPV[^ppvnpv]/calibration of the prediction vs. an accepted reference (CPIC[^cpic] diplotypes, expert-panel ClinVar/ClinGen[^clingen], and the measured longitudinal biomarker trajectories). FMB does **not** prescribe, supply, dose, or direct any peptide — it observes whatever the partner clinic has independently prescribed.

### 3.2 The peptide boundary — observational, treatment-as-usual, all peptides
The line that keeps this study observational (and therefore expedited, minimal-risk, and outside the IND framework) is simple: **FMB observes; it never supplies, doses, or directs therapy.**

- **In scope — all peptides the partner clinics prescribe.** The study observes participants' biomarker trajectories on **whatever peptide their own clinician has independently prescribed**, across the full engine panel in `PEPTIDE_MEASUREMENTS` (`engine/peptides/measurements.py`), **including unapproved research peptides** (BPC-157, TB-500, and the rest). GLP-1 receptor agonists (Semaglutide / Tirzepatide / Liraglutide) may be highlighted first because they carry grade-A evidence, but the design covers every peptide the clinics use. The peptide is **observed, never supplied by the study.**
- **Outside the IND framework — even for unapproved peptides.** Because FMB does not prescribe, supply, dose, or direct any drug, the study is **not clinical investigation of a drug under an IND** (21 CFR 312.2(b))[^ind]. The treatment decision, the product, and the dosing all belong to the participant's own clinician as treatment-as-usual; the study only records outcomes.
- **Out of scope (separate, much larger undertaking):** *administering* BPC-157 / TB-500 / etc. to participants to test response. That would be an **interventional trial of an investigational compound** — it would require an **FDA IND**, a DSMB[^dsmb], full-board review, and a multi-year budget. This study is the observational former, not the latter. (Master plan §12.4 draws the same line.)
- **Adverse-event posture for unapproved peptides — observe and record, do not manage.** Because unapproved peptides are in scope, the protocol adopts an **AE observation/reporting** posture: investigators observe and record adverse events reported by participants and document them per IRB/HRPP reporting requirements, but they do **not** manage, adjust, or direct the participant's therapy. Clinical management stays with the prescribing clinician; safety concerns are referred back to that clinician (and to emergency care as appropriate).

### 3.3 Conflict of interest — name it up front
Noah holds a **UF Innovate[^ufinnovate] patent disclosure on the very pipeline under study.** Investigator financial/intellectual interest in the technology being validated is the single thing IRBs and COI[^coi] committees scrutinize hardest. **Deliverable: a written COI management plan** (disclosure to the IRB and institutional COI committee; independent oversight of data analysis; disclosure in consent forms and publications). Do not submit the protocol without it.

### 3.4 The CLIA wall on return of results — a design constraint, not a footnote
The research pipeline is **not CLIA-certified.**[^clia] Genomic results generated by it **cannot be returned to participants for clinical use.** The protocol must do **one** of:
1. **Return nothing** (analytic-only study; cleanest for Tier A/B), or
2. **Confirm any returnable/actionable finding in a CLIA-certified lab** before disclosure, with a defined return-of-results pathway and genetic counseling (especially for ACMG SF actionable genes[^acmgsf] — the pipeline's default ACMG81 panel *will* surface these).

Decide this explicitly; it shapes consent, budget, and the data-flow diagram.

### 3.5 Genetic-data specifics to address in the protocol
- **GINA**[^gina] protections (and their gaps — life/disability/long-term-care insurance) stated in consent.
- **Re-identification risk**[^reid] of genomic data; data-security plan per master plan §13. Current code state (reconcile, do not assume prior text): `/analyze` carries **soft auth** (`Depends(current_user)`; the Authentik proxy stamps the operator in prod, NULL ownership in dev — not hard enforcement), a `/users` auth router (`engine/users/api.py`) is mounted, and HealthKit ingestion uses **device-token auth that fails closed when `DATABASE_URL` is set**. Derived job results persist to **Postgres** via `db/pool.py` when `DATABASE_URL` is set (in-memory fallback otherwise); the deprecated `JOB_STORE_KEY`/Fernet `jobs.json` snapshot has been removed. At-rest encryption remains a deployment/infra configuration, not a code guarantee. <!-- NEEDS REVIEW: whether this posture satisfies "identifiable data may flow" is a determination owned by master-plan §13 launch-blocker B-3 — reconcile with that doc's current status rather than re-deciding here. -->
- **Genetic-specific consent language**: secondary use, data sharing/repositories (GA4GH[^ga4gh] responsible-sharing), future-use, withdrawal limits once data is de-identified/shared.
- Consider an **NIH Certificate of Confidentiality**[^coc] (free; shields against compelled disclosure).

### 3.6 Recruitment and undue-influence safeguards
- **Recruit at partner clinics from patients already prescribed peptide therapy.** Participants are identified through the partner clinics among patients who are *already* on treatment-as-usual; the study does not solicit anyone to start peptide therapy, and enrollment is never a condition of receiving care.
- **Avoid coercion / undue influence.** Investigators must not recruit their own students, employees, or subordinates. Recruitment materials and the consent process make clear that participation is voluntary, declining has no effect on the participant's clinical care at the clinic, and the participant may withdraw at any time.
- **Clinic-held PHI is accessed only under authorization.** Recruitment contact and any use of clinic records proceed under HIPAA authorization and the BAA/DUA with each partner clinic (§4), not through open-ended chart mining.
- **Enrollment operations (how to reach study headcount).** Site network math, funnel definitions (screened → enrolled → T0 → completer), GLP-1–heavy stratum targets, activation waves, pace gates, and pre-FPI checklist: **`docs/enrollment-strategy.md`** (ops target ~1,000 enrolled; statistical N remains SAP-owned).

---

## 4. The submission package (Tier C)

| Document | Notes / owner |
|---|---|
| **Protocol** | Background, aims, design, reference standards, endpoints, sample size & statistical analysis plan (biostatistician), data flow, COI plan. Build from master plan §9–§12, §16. |
| **Informed consent form(s) + HIPAA authorization** | Genetic-specific language (§3.5); HIPAA authorization for use of clinic-held PHI (§2, §3.6); separate return-of-results & future-use elements; COI disclosure (§3.3). |
| **Recruitment materials** | Active — the prospective study recruits at partner clinics from patients already prescribed peptide therapy (§3.6). Voluntary-participation and no-effect-on-care language. Channel mix, site waves, and prohibited tactics: `docs/enrollment-strategy.md`. |
| **BAA / DUA with each partner clinic** | Required — partner clinics are HIPAA covered entities. Execute a Business Associate Agreement and/or Data Use Agreement with each clinic before any PHI flows to FMB (§2, §3.6). |
| **Data Management & Security Plan** | HIPAA/GINA; encryption, access control, retention, de-identification/coding scheme. Depends on API remediation (master plan §13, B-3). |
| **Data Use Agreement(s)** | For any banked/biobank/dbGaP data (Tier B) in addition to the partner-clinic DUAs above. |
| **COI management plan** | §3.3 — institutional COI committee + IRB. |
| **Reliance / sIRB agreement** | UF is the single IRB of record (§2); each partner clinic and FMB executes a reliance agreement (SMART IRB / OneFlorida+) ceding review to UF. |
| **Investigator CVs / qualifications** | PI and key personnel. |
| **Certificate of Confidentiality application** | Optional but recommended (§3.5). |

---

## 5. Prerequisites (do these regardless of tier) — UF-specific

- [ ] **Register in myIRB** — UF's electronic submission system; *all* submissions and determinations go through it.
- [ ] **Training — IRB 803** (the mandatory human-subjects course for **all** investigators and study staff). Renew **every 3 years**; *new myIRB studies cannot be submitted until training is complete and loaded* (allow **2–4 business days** to process). For the Tier B exempt route, **IRB 850** suffices with the Exempt Auto-Determination tool — but not for a full Tier C study.
- [ ] **GCP training**[^gcp] — required for NIH-funded clinical trials. Note the UF module `UF_CTS904_OLT` does **not** satisfy the NIH GCP requirement; UF's NIH-compliant GCP course is **`UF_GCP100_OLT`** (GCP for Social & Behavioral Research) in myTraining — confirm the current course code there before enrolling.
- [ ] **HIPAA training (PRV800)** — annual, via myTraining / UF Privacy Office, for anyone with HIPAA responsibilities. Relevant the moment any PHI[^phi]-linked genomic data is touched.
- [ ] **COI disclosure** — file the patent/financial-interest disclosure with the **UF Conflicts of Interest office (coi.ufl.edu)**; HRPP integrates COI review into approval (see §3.3). This is the formal channel for the UF Innovate patent.
- [ ] **Execute reliance under the settled UF sIRB** (§2) — route the submission to IRB-01 (direct, or as the OneFlorida+ sIRB) and have each partner clinic and FMB execute a SMART IRB / OneFlorida+ reliance agreement ceding review to UF. The IRB of record is settled; this step is execution, not a choice.
- [ ] **Identify a qualified PI** — for a UF/clinical study this typically must be a faculty member or licensed clinician; for biostatistics and variant interpretation, the master plan §6.3 / §18 roles apply.
- [ ] **Check ancillary committees** — Institutional Biosafety Committee (IBC)[^ibc] if biospecimens are handled; Division of Sponsored Programs if externally funded.
- [ ] **Stand up the minimum data-security posture** so identifiable data can legally flow (API auth + encryption at rest/in transit — master plan B-3). Tier A/B on de-identified data does **not** block on this.

---

## 6. Sequence

1. **Now (no IRB):** Begin **Tier A** analytical validation against GIAB/GeT-RM reference materials (master plan §9, Appendix C). This is the largest body of "performance" evidence and needs no approval.
2. **Weeks 1–4:** Execute reliance under the settled UF sIRB and route to IRB-01 (§2). File **Tier B** determination/exemption request for any retrospective de-identified data. Complete CITI. Draft COI management plan. Begin BAA/DUA negotiation with partner clinics.
3. **Parallel, weeks 2–8:** Author the **Tier C** protocol + consent + HIPAA authorization + data-security + BAA/DUA package (§4). Requires the intended-use decision (master plan §3) and API security remediation (B-3) to be underway.
4. **Submit Tier C for expedited IRB review** (§1; expect revisions — genetic + COI studies draw scrutiny even on the expedited track). Do not enroll, contact participants, or touch identifiable/clinic PHI until approval.
5. **Maintain:** continuing review/renewals, amendments for any protocol change, adverse-event/unanticipated-problem reporting.

---

## 7. Human vs. delegable

**[HUMAN-ONLY] Only-you / human decisions & actions**
- Execute the **reliance agreements** ceding review to the settled **UF sIRB** (§2), and sign the **BAA/DUA** with each partner clinic.
- Sign the **COI disclosure** and own the management plan (§3.3).
- Decide the **return-of-results posture** (§3.4). (The IRB of record and the observational peptide-scope boundary are settled — §2, §3.2.)
- Complete **CITI[^citi] training**; secure a **qualified PI / faculty sponsor**.
- All IRB submissions, signatures, and communications with the HRPP office.

**[DELEGABLE] I can draft / build for you**
- The **Tier A analytical-validation harness** — wiring GIAB/GeT-RM reference sets through the pipeline and computing concordance/sensitivity/specificity (real code, startable now; master plan §9 + Appendix C).
- **First drafts** of the protocol, the data-management & security plan, and the genetic-specific consent language (you + IRB finalize).
- The **API security remediation** (auth + encryption, B-3) that gates identifiable-data studies.
- A **determination-request memo** for Tiers A/B to file with the IRB office.

---

*Cross-references: `docs/clinical-validation-plan.md` §3 (intended use), §9 (analytical validation), §10–§12 (clinical validation), §13 (privacy/security), §18 (governance/ethics). Standards: Common Rule 45 CFR 46; ICH-GCP E6(R3)[^ichgcp]; HIPAA; GINA; STARD 2015; TRIPOD-AI/PROBAST-AI; GA4GH.*

---

## Footnotes

[^hrpp]: **HRPP (Human Research Protection Program)** — the institution-wide program responsible for protecting human research participants; the IRB is its review arm.
[^irb]: **IRB (Institutional Review Board)** — the committee that reviews and approves human-subjects research to safeguard participants' rights and welfare.
[^commonrule]: **Common Rule (45 CFR 46)** — the baseline U.S. federal regulation for protecting human research subjects, defining what counts as research, human subjects, and exemptions.
[^identifiable]: **Identifiable private information** — information about a living person that is private and from which their identity can readily be determined; obtaining it is one trigger for human-subjects oversight.
[^analyticalval]: **Analytical validation** — testing whether the software/assay produces the technically correct measurement (does it read the genome right), separate from whether that measurement is clinically meaningful.
[^strcag]: **STR / CAG length** — short-tandem-repeat sizing, such as the CAG-repeat count in the AR gene; accuracy of the called repeat length is an analytical-validation endpoint.
[^buildhandling]: **Build handling** — correctly recognizing and converting between human reference-genome assemblies (GRCh37/hg19 vs GRCh38/hg38), whose coordinates differ.
[^giab]: **GIAB / NIST** — Genome in a Bottle, a NIST-led project providing thoroughly characterized reference genomes (e.g. NA12878) with benchmark truth calls for validating pipelines.
[^getrm]: **GeT-RM (CDC)** — the CDC's Genetic Testing Reference Materials program, supplying consensus pharmacogenetic genotypes on reference cell lines.
[^coriell]: **Coriell** — the biorepository providing the immortalized cell lines used as renewable, de-identified reference DNA (not living individuals).
[^pgx]: **PGx (Pharmacogenomics)** — how genetic variation affects drug response; "PGx diplotypes" are the star-allele pairs that predict drug-metabolism phenotypes.
[^kgp]: **1000 Genomes** — a public reference catalog of human variation across populations, used here as input genotypes with known coordinates.
[^prs]: **PRS (Polygenic Risk Score)** — a score combining many variants' effects to estimate genetic predisposition; "calibration" checks its predicted risks match observed rates.
[^dbgap]: **dbGaP** — NIH's controlled-access database of Genotypes and Phenotypes; human datasets released only under a Data Use Agreement.
[^dua]: **DUA (Data Use Agreement)** — a contract governing how a restricted dataset may be accessed, used, and protected.
[^exempt]: **Exempt** — research that meets a Common Rule exemption category (low-risk) and so is spared full IRB review, though a determination is still required.
[^expedited]: **Expedited review (45 CFR 46.110)** — a review pathway for minimal-risk research in listed categories, conducted by the IRB chair or a designated reviewer rather than the full convened board. It still requires a complete submission (protocol, consent, HIPAA authorization); only the review mechanism is lighter than full-board review.
[^nhsr]: **not-HSR / NHSR (Not Human Subjects Research)** — a determination that an activity falls outside the regulatory definition of human-subjects research entirely.
[^irb850]: **IRB 850** — UF's lighter training course tied to the exempt/self-determination pathway; insufficient on its own for a full study.
[^irb803]: **IRB 803** — UF's mandatory comprehensive human-subjects training required to submit a full (Tier C) study; renewed every 3 years.
[^myirb]: **myIRB** — UF's electronic IRB submission and review system.
[^citi]: **CITI** — the Collaborative Institutional Training Initiative, the standard online human-subjects/research-ethics training platform many institutions require.
[^reliance]: **Reliance agreement** — a formal arrangement letting one institution's IRB review on behalf of another, avoiding duplicate reviews in multi-site studies.
[^hipaa]: **HIPAA** — the U.S. Health Insurance Portability and Accountability Act, which governs the privacy and security of protected health information.
[^sirb]: **sIRB (single IRB)** — one IRB designated to review a multi-site study for all participating sites (now generally required for federally funded multi-site research).
[^oneflorida]: **OneFlorida+** — a statewide clinical research consortium; IRB-01 serves as its consortium IRB for multi-site Florida academic studies.
[^smartirb]: **SMART IRB** — a national master reliance framework (with standard agreements/IAAs) that streamlines IRB reliance across institutions.
[^aahrpp]: **AAHRPP-accredited** — accredited by the Association for the Accreditation of Human Research Protection Programs, signaling high, audited standards for human-research oversight.
[^stard]: **STARD 2015** — Standards for Reporting Diagnostic Accuracy Studies; a reporting checklist for diagnostic-test performance studies.
[^tripod]: **TRIPOD-AI / PROBAST-AI** — reporting (TRIPOD) and risk-of-bias (PROBAST) guidelines for clinical prediction models, in their AI-specific updates.
[^ppvnpv]: **PPV / NPV** — Positive and Negative Predictive Value: the probability that a positive (or negative) test result is actually correct, given the disease prevalence.
[^cpic]: **CPIC** — the Clinical Pharmacogenetics Implementation Consortium; publishes the reference diplotype-to-phenotype and dosing guidelines used as truth for PGx.
[^clingen]: **ClinVar / ClinGen** — NCBI's archive of variant clinical-significance assertions (ClinVar) and the NIH expert-curation effort producing authoritative classifications (ClinGen).
[^ind]: **FDA IND (Investigational New Drug)** — the FDA application required before administering an investigational drug to humans; triggers a much heavier regulatory burden.
[^dsmb]: **DSMB (Data Safety Monitoring Board)** — an independent committee that monitors participant safety and data integrity during an interventional trial.
[^ufinnovate]: **UF Innovate** — UF's technology-transfer office managing patents/inventions; a patent disclosure there is a financial conflict of interest to disclose and manage.
[^coi]: **COI (Conflict of Interest)** — a financial/personal interest that could bias the research; must be disclosed to and managed by the IRB and COI committee.
[^clia]: **CLIA-certified** — holding the federal certification required to return clinical lab results to patients; the research pipeline lacks it, constraining return of results.
[^acmgsf]: **ACMG SF actionable genes** — the ACMG "Secondary Findings" gene list (the engine's default ACMG81 panel) of clinically actionable genes whose pathogenic findings warrant disclosure/management.
[^gina]: **GINA (Genetic Information Nondiscrimination Act)** — U.S. law barring genetic discrimination in health insurance and employment; it does NOT cover life, disability, or long-term-care insurance — a gap to disclose in consent.
[^reid]: **Re-identification risk** — the possibility that "de-identified" genomic data could be traced back to an individual; genomes are inherently identifying, raising this risk.
[^ga4gh]: **GA4GH (Global Alliance for Genomics and Health)** — an international body setting standards and frameworks for responsible genomic data sharing.
[^coc]: **NIH Certificate of Confidentiality** — a free federal protection shielding identifiable research data from compelled legal disclosure (e.g. subpoena).
[^gcp]: **GCP (Good Clinical Practice)** — the international quality standard for designing and conducting clinical trials; NIH requires GCP training for trial staff.
[^phi]: **PHI (Protected Health Information)** — individually identifiable health information covered by HIPAA; handling it triggers privacy/security obligations.
[^ibc]: **IBC (Institutional Biosafety Committee)** — the committee overseeing safe handling of biological materials/biospecimens; a separate review from the IRB.
[^ichgcp]: **ICH-GCP E6(R3)** — the International Council for Harmonisation's Good Clinical Practice guideline (revision 3), the global standard governing clinical-trial conduct.
