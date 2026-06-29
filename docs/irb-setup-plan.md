# IRB Setup Plan — Performance Validation of the u4u-engine Pipeline

**Document type:** IRB strategy & submission roadmap (actionable companion to the Clinical Validation Master Plan)
**Scope:** What is required to obtain human-subjects oversight for studies that *measure the performance* of the `u4u-engine` pipeline.
**Status:** DRAFT v0.1 — planning artifact. Not legal or regulatory advice; the institution's Human Research Protection Program (HRPP)[^hrpp]/IRB[^irb] office and regulatory counsel are the authorities of record.
**Relationship to other docs:** This plan operationalizes §18 (Governance, Ethics, Oversight) of `docs/clinical-validation-plan.md`. It cross-references that master plan for intended use (§3), analytical validation (§9), clinical validation (§10–§12), and privacy/security (§13) rather than restating them.

---

> **The one-paragraph version.** "Testing the performance of this pipeline" is not a single study and does not uniformly require an IRB. It splits into three tiers of human-subjects involvement with very different burdens. **Analytical performance testing against reference materials (GIAB, GeT-RM) and de-identified public data is *not human-subjects research* and can begin now with no IRB.** Only the track that touches identifiable living people — clinical concordance on real patient samples, prospective recruitment, or return of results — needs a full IRB submission. The plan below partitions the work that way so the non-gated science can start immediately while the IRB package is assembled in parallel.

---

## 1. Threshold partition — what actually needs an IRB

Per the Common Rule (45 CFR 46)[^commonrule], an activity needs IRB oversight only if it is **research** involving **human subjects** — i.e., obtaining data through *intervention/interaction* with a living individual, or obtaining *identifiable private information*[^identifiable]. Map every "performance" question onto one of three tiers:

| Tier | What it tests | Data source | Human-subjects status | IRB action |
|---|---|---|---|---|
| **Tier A — Analytical validation**[^analyticalval] | Does the pipeline read the genome correctly? (variant-call concordance, sensitivity/specificity/precision; star-allele diplotype concordance; STR/CAG[^strcag] length accuracy; build handling[^buildhandling]) | **Cell-line reference materials & de-identified public truth sets** — GIAB/NIST[^giab] (NA12878 et al.), GeT-RM (CDC)[^getrm] Coriell[^coriell] PGx[^pgx] diplotypes, 1000 Genomes[^kgp] / public VCFs | **Not human subjects** (45 CFR 46.102(e)) — cell lines and de-identified public data | **None.** Start now. (Maps to master plan §9) |
| **Tier B — Secondary use of existing human data** | Does a pipeline call predict a real clinical state? (interpretation/scoring concordance, PGx phenotype concordance, PRS[^prs] calibration) using **already-collected** clinical genomes/outcomes | Banked/retrospective de-identified or coded clinical data; biobank/dbGaP[^dbgap] under a Data Use Agreement[^dua] | Often **Exempt**[^exempt] (45 CFR 46.104(d)(4) — secondary use of de-identified/recorded data) or **not-HSR**[^nhsr] | **Determination request** (fast track). DUA likely required. |
| **Tier C — Prospective / identifiable / return-of-results** | Performance on freshly recruited participants; any study where results are returned; identifiable genomic data | New enrollment, identifiable specimens, longitudinal biomarker tracking on real people | **Human-subjects research** | **Full IRB submission** — protocol, consent, the works (§4 below). |

**Actionable headline:** Tier A is the bulk of "does the pipeline compute correctly" and is **un-gated** — begin immediately. Tier B is fast and light. Tier C is the only track that needs the full machinery, and it should be scoped tightly (§3).

> Do not let the institution's IRB *self-determine* tiers for you. For Tiers A and B, submit a short **"IRB determination request"** (a.k.a. "not human subjects research" / "exempt determination") and keep the written determination on file. That letter is what protects publications and audits — "we decided it was exempt ourselves" does not.
>
> **At UF specifically:** there is a self-service **Exempt Auto-Determination tool** for exactly this (it uses the lighter IRB 850 training[^irb850]). Use it for the Tier B exempt/not-HSR determination; note that IRB 850 alone is *not* sufficient to submit a full (Tier C) study via myIRB[^myirb] — that needs IRB 803[^irb803] (§5).

---

## 2. IRB of record — the top human decision (gating, but does not block drafting)

Everything institution-specific (forms, e-submission system, CITI[^citi] pathway, fees, reliance agreements[^reliance]) flows from **one question**:

> **Is this research conducted under the University of Florida's auspices** — by a UF employee or student, using UF funds, UF data, or UF resources/facilities?

- **If yes → UF HRPP is the IRB of record.** Within UF, this work routes to **IRB-01** (Gainesville Health Science Center) — IRB-01 reviews *all medical research, tissue/data banks, and anything involving HIPAA[^hipaa]-protected data*. **Not IRB-02**, which is explicitly limited to social/behavioral/survey research and excludes clinical/tissue-bank/HIPAA studies. (UF Innovate already holds a patent disclosure on this pipeline — see §3.3 COI — which suggests institutional entanglement worth confirming with UF's office.) *(Address submissions to the HRPP office via myIRB — **not** to a named chair: the IRB-01 chair role transitions effective 2026-07-01, so a hard-coded name will go stale.)* If any activity routes through the **UF Jacksonville** campus, the board of record there is **IRB-03**, not IRB-01.
- **If no — purely Florida Man Bioscience (commercial) work → a commercial/central IRB** (e.g., Advarra, WCG) is the route. Companies without an internal IRB contract one.
- **If both UF and the company are "engaged"** (UF investigator + company sponsor), expect a **single-IRB (sIRB) reliance agreement**[^sirb]. UF offers several reliance vehicles, and WCG is not the only one: **IRB-01 *is* the OneFlorida+ consortium IRB**[^oneflorida] (the natural sIRB for multi-site Florida academic collaboration); UF participates in **SMART IRB**[^smartirb] master reliance (SMART IAA / UF Master IAA); and **IRB-04 / WCG (Western IRB)**[^wcg] is the commercial-IRB cede pathway. Pick the vehicle by who the other engaged sites/sponsors are.

**Decision owner:** Noah + any UF faculty sponsor. **This is a human task — confirm UF engagement before choosing the IRB.** UF is **AAHRPP-accredited**[^aahrpp] (since 2018), so expect rigorous documentation standards regardless of board. It changes submission *mechanics*, not the structure of this plan, so the rest is written IRB-agnostic.

---

## 3. Scoping the Tier C study — keep it from sprawling

### 3.1 What the study *is*
A **diagnostic/predictive-accuracy study** of the pipeline's outputs against reference standards — observational. Report per **STARD 2015**[^stard] (diagnostic accuracy) and **TRIPOD-AI / PROBAST-AI**[^tripod] (prediction models). Primary endpoints are concordance/sensitivity/specificity/PPV-NPV[^ppvnpv]/calibration vs. an accepted reference (CPIC[^cpic] diplotypes, expert-panel ClinVar/ClinGen[^clingen], measured biomarker trajectories).

### 3.2 The peptide boundary — do not let scope creep into a therapy trial
- **In scope:** validating the pipeline's *predictions* observationally — e.g., does a "responder" call correspond to outcomes in **already-existing** data, or in participants who are receiving peptides **independently of this study**.
- **Out of scope (separate, much larger undertaking):** *administering* BPC-157/TB-500/etc. to participants to test response. That is an **interventional trial of an investigational compound** — likely requires an **FDA IND**[^ind], a DSMB[^dsmb], and a multi-year budget. "Test the performance of *this pipeline*" is the observational former, not the latter. (Master plan §12.4 draws the same line.)

### 3.3 Conflict of interest — name it up front
Noah holds a **UF Innovate[^ufinnovate] patent disclosure on the very pipeline under study.** Investigator financial/intellectual interest in the technology being validated is the single thing IRBs and COI[^coi] committees scrutinize hardest. **Deliverable: a written COI management plan** (disclosure to the IRB and institutional COI committee; independent oversight of data analysis; disclosure in consent forms and publications). Do not submit the protocol without it.

### 3.4 The CLIA wall on return of results — a design constraint, not a footnote
The research pipeline is **not CLIA-certified.**[^clia] Genomic results generated by it **cannot be returned to participants for clinical use.** The protocol must do **one** of:
1. **Return nothing** (analytic-only study; cleanest for Tier A/B), or
2. **Confirm any returnable/actionable finding in a CLIA-certified lab** before disclosure, with a defined return-of-results pathway and genetic counseling (especially for ACMG SF actionable genes[^acmgsf] — the pipeline's default ACMG81 panel *will* surface these).

Decide this explicitly; it shapes consent, budget, and the data-flow diagram.

### 3.5 Genetic-data specifics to address in the protocol
- **GINA**[^gina] protections (and their gaps — life/disability/long-term-care insurance) stated in consent.
- **Re-identification risk**[^reid] of genomic data; data-security plan per master plan §13 (the current API has no auth and persists derived results unencrypted — **this must be remediated before any identifiable data flows through it**; it is a launch-blocker B-3 in the master plan).
- **Genetic-specific consent language**: secondary use, data sharing/repositories (GA4GH[^ga4gh] responsible-sharing), future-use, withdrawal limits once data is de-identified/shared.
- Consider an **NIH Certificate of Confidentiality**[^coc] (free; shields against compelled disclosure).

---

## 4. The submission package (Tier C)

| Document | Notes / owner |
|---|---|
| **Protocol** | Background, aims, design, reference standards, endpoints, sample size & statistical analysis plan (biostatistician), data flow, COI plan. Build from master plan §9–§12, §16. |
| **Informed consent form(s)** | Genetic-specific language (§3.5); separate return-of-results & future-use elements; COI disclosure (§3.3). |
| **Recruitment materials** | If prospective (Tier C only). |
| **Data Management & Security Plan** | HIPAA/GINA; encryption, access control, retention, de-identification/coding scheme. Depends on API remediation (master plan §13, B-3). |
| **Data Use Agreement(s)** | For banked/biobank/dbGaP data (Tier B). |
| **COI management plan** | §3.3 — institutional COI committee + IRB. |
| **Reliance / sIRB agreement** | If UF + company both engaged (§2). |
| **Investigator CVs / qualifications** | PI and key personnel. |
| **Certificate of Confidentiality application** | Optional but recommended (§3.5). |

---

## 5. Prerequisites (do these regardless of tier) — UF-specific

- [ ] **Register in myIRB** — UF's electronic submission system; *all* submissions and determinations go through it.
- [ ] **Training — IRB 803** (the mandatory human-subjects course for **all** investigators and study staff). Renew **every 3 years**; *new myIRB studies cannot be submitted until training is complete and loaded* (allow **2–4 business days** to process). For the Tier B exempt route, **IRB 850** suffices with the Exempt Auto-Determination tool — but not for a full Tier C study.
- [ ] **GCP training**[^gcp] — required for NIH-funded clinical trials. Note the UF module `UF_CTS904_OLT` does **not** satisfy the NIH GCP requirement; UF's NIH-compliant GCP course is **`UF_GCP100_OLT`** (GCP for Social & Behavioral Research) in myTraining — confirm the current course code there before enrolling.
- [ ] **HIPAA training (PRV800)** — annual, via myTraining / UF Privacy Office, for anyone with HIPAA responsibilities. Relevant the moment any PHI[^phi]-linked genomic data is touched.
- [ ] **COI disclosure** — file the patent/financial-interest disclosure with the **UF Conflicts of Interest office (coi.ufl.edu)**; HRPP integrates COI review into approval (see §3.3). This is the formal channel for the UF Innovate patent.
- [ ] **Confirm IRB of record** (§2 decision) — IRB-01 (direct, or as the OneFlorida+ sIRB) vs. SMART IRB reliance vs. WCG/IRB-04 cede.
- [ ] **Identify a qualified PI** — for a UF/clinical study this typically must be a faculty member or licensed clinician; for biostatistics and variant interpretation, the master plan §6.3 / §18 roles apply.
- [ ] **Check ancillary committees** — Institutional Biosafety Committee (IBC)[^ibc] if biospecimens are handled; Division of Sponsored Programs if externally funded.
- [ ] **Stand up the minimum data-security posture** so identifiable data can legally flow (API auth + encryption at rest/in transit — master plan B-3). Tier A/B on de-identified data does **not** block on this.

---

## 6. Sequence

1. **Now (no IRB):** Begin **Tier A** analytical validation against GIAB/GeT-RM reference materials (master plan §9, Appendix C). This is the largest body of "performance" evidence and needs no approval.
2. **Weeks 1–4:** Confirm IRB of record (§2). File **Tier B** determination/exemption request for any retrospective de-identified data. Complete CITI. Draft COI management plan.
3. **Parallel, weeks 2–8:** Author the **Tier C** protocol + consent + data-security + DUA package (§4). Requires the intended-use decision (master plan §3) and API security remediation (B-3) to be underway.
4. **Submit Tier C → IRB review** (expect revisions; genetic + COI studies draw scrutiny). Do not enroll or touch identifiable data until approval.
5. **Maintain:** continuing review/renewals, amendments for any protocol change, adverse-event/unanticipated-problem reporting.

---

## 7. Human vs. delegable

**🔴 Only-you / human decisions & actions**
- Confirm **UF engagement** and choose the **IRB of record** (§2).
- Sign the **COI disclosure** and own the management plan (§3.3).
- Decide the **return-of-results posture** (§3.4) and the **peptide scope boundary** (§3.2).
- Complete **CITI training**; secure a **qualified PI / faculty sponsor**.
- All IRB submissions, signatures, and communications with the HRPP office.

**🟢 I can draft / build for you**
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
[^wcg]: **WCG / Western IRB (IRB-04)** — a commercial (for-profit) central IRB; the "cede" pathway lets an institution defer review to it.
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
