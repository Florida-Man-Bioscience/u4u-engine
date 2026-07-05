# IRB Setup Plan — Performance Testing of the U4U / PeptidIQ Pipeline

**Document type:** IRB submission playbook (operational companion to the Clinical Validation Master Plan)
**Scope:** What is required to obtain IRB coverage for a study that **tests the analytical and clinical performance** of the `u4u-engine` pipeline.
**Status:** DRAFT v0.1 — planning artifact. Not a determination that any activity is or is not human-subjects research; only the IRB of record can make that call.
**Relationship to other docs:** This is the *submission playbook*. The governance/ethics rationale lives in `docs/clinical-validation-plan.md` §18 (Governance, Ethics, Oversight) and §9–§11 (the analytical/clinical validation designs this study would execute). This document does **not** restate them — it operationalizes the IRB path.

---

> **Read first — scope.** This plan now covers **two concurrent, defined tracks**, not one. (1) An **analytical-validation track** that runs **existing genome files** through the pipeline and compares its output to a truth/reference standard (analytical concordance) and, where available, to clinical reference results (clinical concordance) — reference materials and de-identified secondary data, no participant contact (Lanes A/B below). (2) A **prospective observational clinic-partnership study** — the primary human-facing study, defined and active — in which FMB partners with peptide-prescribing clinics to enroll **consenting adults who have INDEPENDENTLY been prescribed peptide therapy by their own clinicians** (treatment-as-usual) and tracks their progress over time using the engine's proposed per-peptide biomarker panels (`engine/peptides/measurements.py`), correlating the engine's genomic response predictions against observed per-peptide biomarker trajectories. **FMB does not prescribe, supply, dose, or direct any peptide** — it observes. This is a **minimal-risk, observational study** that reviews clinic-held biomarker data obtained under participant consent plus HIPAA[^hipaa] authorization; it does **not** run its own blood/saliva collection or biobanking. Because it is prospective, contacts and consents participants, and touches clinic-held PHI[^phi], it is **expedited-review** research (Lane C below) — no longer Exempt secondary-data research, but not full-board either, absent added interventions or identifiable return-of-results.

---

## 1. The threshold question — is this even Human Subjects Research?

The *analytical-validation* track can be done **without** triggering full IRB[^irb] review, because it uses reference materials and de-identified data that are not "human subjects" under the Common Rule (45 CFR 46)[^commonrule]. **But "no full review" is not "no IRB" — you still need the IRB/HRPP[^hrpp] to issue a written determination** (NHSR[^nhsr] or Exempt[^exempt]). Journals, regulators (FDA/CAP[^cap]), and partners will later ask to see that letter. **The prospective observational clinic-partnership study is different: it enrolls and consents participants and touches clinic-held PHI[^phi], so it is human-subjects research requiring positive review — but, being observational and minimal-risk, it routes to expedited (not full-board) review** (Lane C below).

Route **every planned data source** into one of three lanes:

| Lane | What it covers | Example sources | IRB action needed | Review burden |
|---|---|---|---|---|
| **A — Not Human Subjects Research (NHSR)** | Commercial / public **reference materials** with known truth genotypes; no living individual is identifiable | GIAB/NIST (NA12878 etc.), **GeT-RM** Coriell PGx cell lines (CYP2D6/2C19 diplotypes), PharmVar reference data | One-page **NHSR determination request** | Lowest — letter, no protocol |
| **B — Exempt** (45 CFR 46.104(d)(4)) | Secondary research on **existing, de-identified** human genomes the team did not generate for this study | 1000 Genomes, openSNP, de-identified institutional VCFs (no codes back to identity) | **Exempt determination request** + brief data description | Low — IRB confirms exemption |
| **C — Expedited** (45 CFR 46.110)[^expedited] | The **prospective observational clinic-partnership study** — consented, identifiable participants already on peptide therapy, tracked over time on clinic-held biomarker data (PHI). Minimal / no-more-than-minimal risk, observational. Also any identifiable existing samples or controlled-access data linked to identifiers | Consenting participants at partner clinics tracked on the engine's per-peptide biomarker panels; institutional biobank with a code key; dbGaP controlled-access tied to phenotypes | **Protocol + consent + HIPAA authorization + BAA/DUA + data security plan** | Moderate — expedited, likely 45 CFR 46.110 categories 5 and/or 4/7 (IRB confirms); full-board only if interventions or identifiable return-of-results are added |

**The single most useful artifact to produce first** is the table below — every data source you intend to use, assigned to a lane. This is what determines how much IRB work there actually is.

| Planned data source | Identifiable? | Generated for this study? | → Lane | Owner action |
|---|---|---|---|---|
| GIAB NA12878 (analytical truth set) | No | No | **A** | _TBD_ |
| GeT-RM Coriell PGx panel (star-allele truth) | No | No | **A** | _TBD_ |
| 1000 Genomes / openSNP (de-identified) | No | No | **B** | _TBD_ |
| Institutional / clinical VCFs w/ concordance labels | _depends on key_ | No | **B or C** | _confirm de-id_ |
| Partner-clinic participants on peptide therapy (consented; clinic-held biomarker trajectories) | Yes | No (treatment-as-usual; clinic-held) | **C (expedited)** | _consent + HIPAA auth + BAA/DUA_ |
| _add every source here_ | | | | |

> **Design implication:** the *analytical-validation* track (accuracy, precision, sensitivity/specificity, star-allele and STR concordance — `docs/clinical-validation-plan.md` §9) lands almost entirely in **Lanes A/B** and can move immediately on an NHSR/Exempt determination. **Lane C is the prospective observational clinic-partnership study — a defined, active, expedited/consented/observational protocol brought forward, not deferred.** It observes participants already on peptide therapy (treatment-as-usual) and does not run its own specimen collection, so it stays minimal-risk and expedited rather than full-board. Because FMB does not prescribe, supply, dose, or direct any peptide, the study sits **outside IND[^ind] and drug-administration requirements (21 CFR 312.2(b))** — even for unapproved research peptides (BPC-157, TB-500, and the rest of the panel), where the participant's own clinician prescribes and the study only observes. Run the two tracks in parallel; the Lane-C study need not wait on the analytical track.

---

## 2. Which IRB has jurisdiction — RESOLVED: UF as single IRB of record

This question is **settled**: the **University of Florida IRB is the canonical IRB of record**, and because the study spans **multiple sites**, UF IRB serves as the **single IRB of record (sIRB)** under the Common Rule cooperative-research provision (45 CFR 46.114) and NIH sIRB policy.

- **UF reviews for everyone.** All other sites — including **Florida Man Bioscience** — cede review to UF via reliance agreements rather than standing up their own (commercial) IRBs. **SMART IRB** is the standard reliance mechanism; **OneFlorida+** for in-network sites.
- **Engagement signals support this:** the work sits under UF infrastructure with a **UF Innovate patent disclosure**, so UF personnel/resources/IP are central → UF IRB must be engaged regardless of FMB's commercial role.
- The specific UF board routes by data type (IRB-01 Gainesville Health Science Center for genomic/clinical; IRB-02 social/behavioral; IRB-03 Jacksonville) — "UF canonical" fixes the institution; the sub-board is a routing detail confirmed with the UF HRPP[^hrpp] via myIRB.

→ **Action (human, now mechanical):** confirm the UF sub-board with the HRPP; build the **reliance-agreement / site-authorization roster** for every ceding site; set the CITI training host = UF. Everything downstream (forms, fees, training host, reliance agreements) follows from this fixed point.

---

## 3. Special issues this study must address (genetic + investigational + commercial)

These are the items an IRB will specifically scrutinize for *this* pipeline. Most apply to **Lane C** (the prospective observational clinic-partnership study), but the COI item applies regardless.

- **Conflict of interest — gating, not boilerplate.** The same organization both **recommends and sells** the peptides, and there is a **patent disclosure**. A written **financial COI management plan** is something the IRB (and an institutional COI committee) will *require* before approval. This is its own deliverable, independent of lane.
- **HIPAA authorization + BAA/DUA with each partner clinic (Lane C).** Partner clinics are **covered entities**, and the biomarker trajectories the study tracks are their **PHI**. Each enrolled participant must sign a **HIPAA authorization** alongside informed consent, and FMB must execute a **Business Associate Agreement (BAA)[^baa] and/or Data Use Agreement (DUA)[^dua]** with **each** partner clinic before any PHI moves. Scope the BAA/DUA to the minimum data the biomarker panels require.
- **Return-of-results / incidental findings (Lane C only).** The pipeline's **default input filter is the ACMG SF "actionable" gene panel (ACMG81)** — so the study will, by construction, encounter reportable secondary findings. A written **ROR / non-return plan** is mandatory: state up front whether results are returned, and if not, why (research-grade, not clinical). The default is no clinical return; any identifiable return-of-results would escalate the study toward full-board review.
- **CLIA boundary (Lane C only).** Research-grade pipeline calls **cannot be returned to participants as clinical results** without confirmation in a **CLIA-certified lab**. The protocol must say results are research-only and not for clinical decision-making.
- **Unapproved peptides — observe, never prescribe or direct (Lane C).** The panel includes unapproved research peptides (BPC-157, TB-500, and the rest of `engine/peptides/measurements.py`). The study **observes** participants whose own clinicians prescribed these under treatment-as-usual; FMB does not prescribe, supply, dose, or direct any drug, so the activity stays **outside IND and drug-administration requirements (21 CFR 312.2(b))**. The protocol tests whether labels like "Strong Fit" *predict* biomarker trajectories; it must **not** hand any participant an efficacy assertion for BPC-157/TB-500/etc. (see `docs/clinical-validation-plan.md` §11.6, §12.4). This is a hard constraint on consent language and any participant-facing output.
- **Adverse-event observation posture (Lane C).** Because unapproved peptides are in scope, the protocol must specify an **AE[^ae] observation and recording posture**: the study **observes and records** adverse events surfaced during observational tracking and routes them per the protocol's reporting plan, but it **does not manage therapy, adjust dosing, or issue clinical directives** — clinical management stays with the participant's own prescribing clinician.
- **Recruitment / coercion (Lane C).** Recruit at partner clinics from patients **already prescribed peptide therapy by their own clinician**; recruitment materials describe observational tracking only. **Avoid enrolling the investigators' own students, employees, or subordinates**, and **partner-clinic staff must not pressure enrollment** — participation must not affect a patient's clinical care. State this in the recruitment plan and consent script.
- **Genetic-privacy / GINA.** Consent and data-security language must address genetic data sensitivity, re-identification risk, and **GINA** protections (Lane C; lighter mention for Lane B).
- **Controlled-access data = parallel track.** dbGaP / managed-access cohorts need a **Data Access Committee approval + Data Use Agreement (DUA)** *in addition to* the IRB determination. Don't conflate the DUA track with the IRB track — they run in parallel.

---

## 4. Document checklist (by lane)

**Lane A (NHSR):**
- [ ] NHSR determination request form (institution-specific)
- [ ] One-paragraph description: reference materials used, no identifiable humans

**Lane B (Exempt):**
- [ ] Exempt determination request (cite 46.104(d)(4))
- [ ] Data description: source, de-identification basis, no key back to identity
- [ ] DUA, if the dataset requires one

**Lane C (Expedited — the prospective observational clinic-partnership study):**
- [ ] **Protocol** (objectives, per-peptide biomarker endpoints from the engine's proposed panels — `engine/peptides/measurements.py`, reference/prediction standard, sample size/power, statistical analysis plan — pull endpoints from `clinical-validation-plan.md` §9–§11; note observational, minimal-risk, treatment-as-usual design)
- [ ] **Informed consent** (observational tracking; no drug provided or directed by the study)
- [ ] **HIPAA authorization** (per participant; partner clinics are covered entities holding the biomarker PHI)
- [ ] **BAA and/or DUA with each partner clinic** (executed before any PHI transfer)
- [ ] **Recruitment materials** (recruit at partner clinics from patients already on peptide therapy; no coercion; exclude investigators' own students/employees/subordinates)
- [ ] **AE observation / reporting plan** (observe and record adverse events; do not manage therapy or issue clinical directives)
- [ ] **Data management & security plan** (storage, encryption at rest/in transit, access control, retention). Note current code state: jobs persist to Postgres via `db/pool.py` when `DATABASE_URL` is set (in-memory fallback otherwise); the deprecated `JOB_STORE_KEY`/Fernet `jobs.json` snapshot in `api.py` has been removed. Reconcile the residual gaps against `clinical-validation-plan.md` §13. <!-- NEEDS REVIEW: confirm the security posture (encryption at rest, access control) is sufficient for identifiable data against master-plan §13 B-3 status -->
- [ ] **ROR / incidental-findings plan** (ACMG SF; default no clinical return)
- [ ] **Financial COI management plan** ← required regardless of lane
- [ ] DUA / dbGaP DAC approval (if controlled-access secondary data is also used)
- [ ] PI CV + qualified-personnel list; reliance agreement (multi-site — UF as sIRB, others cede)

**Cross-cutting (all lanes, before submission):**
- [ ] **CITI Human Subjects Research training** for all study personnel (host = the IRB of record's institution)
- [ ] Named **PI of record** with appropriate credentials

---

## 5. Submission sequence

1. **Build the Lane Table** (§1) — assign every data source. *(delegable — I can draft from the planned source list)*
2. **Confirm the UF sub-board with the HRPP and build the reliance roster** (§2 — IRB of record is settled as UF/sIRB). *(human, mechanical)*
3. **Complete CITI training** for all personnel. *(human)*
4. **Draft the lane-appropriate documents** (§4). *(delegable — I draft protocol, consent, data-management plan, NHSR/exempt requests; human reviews/signs)*
5. **Author the COI management plan**; route through institutional COI office. *(human-led, I can draft)*
6. **Submit** to the IRB; respond to stipulations.
7. **Approval / determination letter in hand** → begin Lane A/B testing (typically usable immediately on determination); Lane C begins after approval.
8. **Maintain:** continuing review (if applicable), amendments for any scope/data-source change, records retention.

---

## 6. Indicative timeline

| Lane | Typical IRB turnaround | Gating dependency |
|---|---|---|
| A (NHSR) | days–2 weeks | reference materials identified |
| B (Exempt) | 1–4 weeks | de-identification documented |
| C (Expedited — observational clinic-partnership study) | 3–8 weeks | protocol + consent + HIPAA authorization + BAA/DUA + security plan complete |
| C (Full Board — only if escalated) | 1–3 months | board meeting cycle; triggered only if interventions or identifiable return-of-results are added |

The observational clinic-partnership study is the **expedited** (3–8 week) active human-facing track — not a deferred full-board undertaking. It runs **in parallel** with the analytical-validation work (Lanes A/B), which can move on a determination in **days to weeks**. Full-board timing applies only if the design later adds interventions or identifiable return-of-results. Sequence the two tracks concurrently; gate Lane C on its consent, HIPAA authorization, and BAA/DUA rather than on the analytical work.

---

## 7. Task split — yours vs. delegable

**[Only-you] (human decisions / accountability):**
- **Confirm the UF sub-board and execute reliance agreements** (§2) — IRB of record is settled (UF/sIRB); this is now setup, not a decision.
- **Sign the partner-clinic agreements**: negotiate and execute the **BAA/DUA** with each partner clinic (§ scope note; §3) — the study scope is settled as observational (no new specimen collection), so this is setup, not a fork.
- Serve as / name the **PI of record**; complete **CITI training**.
- Sign the **COI management plan** and route it through the institutional COI office.
- Final go/no-go on **return-of-results** policy.

**[Delegable] Hand to me (drafting, once the above are set):**
- The **Lane Table** from your list of intended data sources.
- Draft **protocol**, **informed consent + HIPAA authorization**, **recruitment materials**, **AE observation/reporting plan**, **data-management/security plan**, and the **NHSR/Exempt request** text; draft **BAA/DUA** templates for the partner clinics.
- Draft the **COI management plan** for your review.
- A performance-endpoints section pulled from `clinical-validation-plan.md` §9–§11 (sensitivity/specificity, star-allele concordance vs GeT-RM, etc.).

---

*Cross-references: `docs/clinical-validation-plan.md` §3 (intended use / regulatory posture), §9–§11 (analytical & clinical validation designs = the study endpoints), §13 (privacy/security = the data-management plan), §18 (governance/ethics rationale).*

[^irb]: **IRB (Institutional Review Board)** — the committee that reviews and approves human-subjects research to protect participants' rights and welfare; its written determination is required before regulated activities begin.
[^commonrule]: **Common Rule (45 CFR 46)** — the U.S. federal regulation governing the protection of human research subjects; its definitions decide whether an activity counts as "human subjects research" at all.
[^hrpp]: **HRPP (Human Research Protection Program)** — the institution-wide office that houses the IRB and issues official determination letters; the operational body you actually file with.
[^nhsr]: **NHSR (Not Human Subjects Research)** — a formal IRB determination that an activity falls outside the Common Rule definition, so full review does not apply — but the written letter still matters.
[^exempt]: **Exempt** — an IRB determination that research meets one of the regulatory exemption categories (e.g. secondary use of de-identified data); lighter review than full board, but still an official determination.
[^cap]: **CAP (College of American Pathologists)** — a laboratory accreditation body whose inspectors, alongside the FDA, may later request the IRB determination letter as evidence of compliant validation.
[^expedited]: **Expedited review (45 CFR 46.110)** — an IRB review pathway for research posing no more than minimal risk that fits defined categories (e.g. category 5, research on existing data/records; categories 4/7 for certain data-collection and behavioral research). Reviewed by the chair or a designated reviewer rather than the full board; the IRB confirms the applicable category.
[^hipaa]: **HIPAA authorization** — a participant's signed permission, under the Health Insurance Portability and Accountability Act, for a covered entity to use or disclose their protected health information for the described research.
[^phi]: **PHI (Protected Health Information)** — individually identifiable health information held or transmitted by a HIPAA covered entity (here, the partner clinics); its use in research requires authorization or a waiver.
[^baa]: **BAA (Business Associate Agreement)** — a HIPAA-required contract under which a covered entity permits a business associate to handle PHI on its behalf, binding the associate to safeguard that data.
[^dua]: **DUA (Data Use Agreement)** — a contract governing the transfer and permitted use of a limited data set (or other restricted data) between the data holder and the recipient.
[^ind]: **IND (Investigational New Drug)** — an FDA authorization required to administer an investigational drug to humans in a clinical investigation; observational research that does not administer, supply, or direct a drug falls outside the IND requirement (21 CFR 312.2(b)).
[^ae]: **AE (Adverse Event)** — any untoward medical occurrence in a participant; here, observed and recorded during observational tracking and routed per the reporting plan, without the study managing therapy.
