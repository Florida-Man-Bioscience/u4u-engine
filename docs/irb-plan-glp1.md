# IRB Setup Plan — Observational Response Tracking for Prescribed Peptide Therapy (GLP-1 Flagship, All-Peptide Cohort)

**Document type:** IRB submission playbook — clinic-partnership observational variant (companion to `docs/irb-plan.md`)
**Scope:** What is required to obtain IRB coverage for a prospective, observational, multi-site cohort study in which Florida Man Bioscience (FMB) partners with peptide-prescribing clinics, enrolls consenting adults who are *already prescribed peptide therapy by their own clinicians* (treatment-as-usual), and uses the `u4u-engine` / PeptidIQ pipeline to correlate its **genomic response predictions** against **observed per-peptide biomarker trajectories** over time. GLP-1 receptor agonists[^glp1ra] (semaglutide[^sema] and the incretin class) are highlighted first as the grade-A-evidence flagship, but the design covers **all peptides partner clinics prescribe** — the full panel in `PEPTIDE_MEASUREMENTS` (`engine/peptides/measurements.py`), including unapproved research peptides (BPC-157, TB-500, and the rest), observed but never supplied.
**Status:** DRAFT v0.2 — planning artifact. Not a determination that any activity is or is not human-subjects research, nor a regulatory determination about drug administration; only the IRB of record and (where relevant) FDA can make those calls.
**Relationship to other docs:** This mirrors the lane/checklist structure of `docs/irb-plan.md` but adapts it for a **prospective, participant-facing, PHI-touching observational cohort**. GLP-1 RAs are lawfully marketed and lowest-risk; unapproved research peptides are observed-not-supplied under an adverse-event-observation posture. In every case the study observes therapy that participants are already prescribed and taking under the care of their own clinicians.

---

> **Read first — scope assumption.** This plan assumes the study **observes** response to peptide therapy that participants are *already prescribed and taking under the care of their own clinicians* (treatment-as-usual), and correlates that response with genotype and biomarker data the pipeline analyzes. It does **not** assume the study *prescribes, supplies, doses, or directs administration* of any peptide — approved or unapproved. **The moment the study itself administers, assigns, or directs a drug, the regulatory frame changes** (drug-administration risk review, an IND-exemption analysis, possible IND) and this plan expands accordingly. That fork is flagged explicitly, but the design is committed to the observational side of it.

---

## 0. What kind of study this is — observational, all-peptide, GLP-1 flagship

FMB does not run a treatment arm. It partners with clinics that prescribe peptide therapy, enrolls their consenting patients, and tracks each participant's per-peptide biomarker panel (`engine/peptides/measurements.py`) longitudinally to test whether the engine's genomic response predictions match observed trajectories. That single design choice — observe, never supply — is what keeps the study minimal-risk and out of IND territory across the whole peptide spectrum.

The peptides in scope span a regulatory spectrum, and the plan treats them by risk tier while keeping one observational frame:

| Tier | Peptides | FDA status | Study posture |
|---|---|---|---|
| **Flagship (approved, lowest risk)** | GLP-1 RAs — semaglutide (Ozempic, Wegovy, Rybelsus), tirzepatide[^tirz] (Mounjaro, Zepbound), liraglutide (Victoza, Saxenda), plus dulaglutide/exenatide where prescribed | **Approved**; large RCT base, established label, boxed warning[^boxed], known AE profile; two grade-A evidence entries in `data/biomarker_evidence.json` | Observe response to therapy the participant is already prescribed |
| **Research peptides (unapproved)** | BPC-157, TB-500, and the remainder of `PEPTIDE_MEASUREMENTS` | **Unapproved / research-grade**; sparse, often preclinical or single-group evidence | Observe response to therapy the participant is already prescribed; **AE-observation posture** (see Section 3); FMB never supplies |

The reason to lead with GLP-1 is evidence quality, not exclusivity: the class-qualified GLP-1 markers (`Body weight (GLP-1 RA)`, `HbA1c (GLP-1 RA)`) carry grade-A citation-anchored evidence, so the prediction-vs-observation correlation is sharpest there. The unapproved peptides are lower-evidence but are the more novel validation target — and, precisely because they are unapproved, they raise the adverse-event-observation duty addressed in Section 3.

**Two consequences drive the rest of this plan:**

1. Because the study is now **prospective**, **enrolls participants**, **obtains informed consent**, and **touches clinic-held PHI**, it is **no longer** Exempt secondary-data research. The reframed human-facing study lands in **Expedited review** (Section 1).
2. Because the study **observes and never prescribes, supplies, doses, or directs** any peptide, it stays **non-interventional** and outside IND requirements — even for the unapproved peptides, because the clinic prescribes and the study only observes (Section 3).

---

## 1. The threshold question — is this Human Subjects Research, and which kind?

Two orthogonal questions must both be answered.

**(a) Common Rule[^commonrule] lane** — the same A/B/C partition as the peptide plan, driven by data identifiability and by whether the activity is prospective and participant-facing:

| Lane | What it covers | Example sources | IRB action | Burden |
|---|---|---|---|---|
| **A — Not Human Subjects Research (NHSR)**[^nhsr] | Reference materials with known truth genotypes; no identifiable living individual | GIAB/NIST, GeT-RM Coriell PGx cell lines, PharmVar | One-page NHSR request | Lowest |
| **B — Exempt**[^exempt] (45 CFR 46.104(d)(4)) | **Stage-1 analytical-validation track only** — secondary research on *existing, de-identified* data the team did not generate | De-identified reference/EHR extracts used for concordance benchmarking | Exempt determination + data description | Low |
| **C — Expedited** | **Prospective, participant-facing, minimal-risk** observational research: enrollment, consent, and analysis of identifiable clinic-held data on prescribed therapy | Prospective cohort of consented participants already prescribed peptide therapy by their own clinicians; longitudinal biomarker tracking correlated with genomic predictions | Full protocol + consent + HIPAA authorization + data-security + AE-observation plan | Moderate |

> **Lane-to-track mapping — read this carefully.** The **Stage-1 analytical-validation track** (reference materials, GeT-RM/GIAB concordance) stays in **Lane A (NHSR)** and, where it uses existing de-identified data, **Lane B (Exempt)** — unchanged. The **reframed prospective human study** — the clinic-partnership observational cohort that is the subject of this plan — lands in **Lane C, Expedited**. It is **not** Exempt secondary-data research: it enrolls participants, obtains consent, and touches identifiable PHI, which forecloses the Exempt-secondary path. It is also **not** full-board, because it is observational and minimal / no-more-than-minimal risk (likely 45 CFR 46.110 expedited categories 5 and/or 4/7 — the IRB confirms the category). It rises to full-board only if an intervention or identifiable return-of-results is added, neither of which is in scope.

**(b) Drug-involvement axis** — independent of the lane:

| Study posture | Does the study touch the drug? | FDA frame |
|---|---|---|
| **Stage-1 secondary analysis** | No — only analyzes existing genotype and outcome data | No IND; Lane A/B |
| **Prospective observational (this study)** | No — participants take therapy as prescribed by *their own* clinician; the study only observes and records biomarkers | **No IND — non-interventional** across all peptides; Lane C Expedited |
| **Interventional (out of scope)** | Yes — a study that assigns, supplies, doses, or directs a peptide | IND-exemption analysis required for approved drugs; IND if not exempt; full-board — a separate, later protocol |

> **Design implication:** the response-tracking study is committed to the **observational** posture (genotype and biomarker trajectory on therapy the participant is *already prescribed*). That keeps every peptide in scope — approved and unapproved alike — out of IND territory and in **Lane C, Expedited**. An interventional arm would be a separate, heavier, later protocol; it must not be allowed to drag the observational validation study into IND review.

**First artifact to produce:** the per-source lane table plus a one-line **drug-posture declaration** affirming, for the whole cohort, that the study is observational (clinic prescribes; study observes) and therefore non-interventional and IND-not-applicable.

---

## 2. Which IRB has jurisdiction — RESOLVED: UF as single IRB of record

The institutional decision is **made** and is not reopened here:

- **University of Florida IRB is the canonical IRB of record**, and because this is a **multi-site** study, UF IRB serves as the **single IRB of record (sIRB)**[^sirb] under the Common Rule cooperative-research provision (45 CFR 46.114) and NIH sIRB policy.
- **All other sites cede review to UF** via reliance agreements — **SMART IRB**[^smart] as the standard reliance mechanism; **OneFlorida+**[^onefl] for in-network sites. Partner clinics that are not research institutions cede via the same reliance mechanism (site-authorization / individual-investigator agreement as appropriate).
- Florida Man Bioscience relies on UF rather than standing up its own commercial IRB.
- The specific UF board routes by data type (IRB-01 Gainesville Health Science Center for genomic/clinical; IRB-02 social/behavioral; IRB-03 Jacksonville) — the institution is fixed; the sub-board is a routing detail confirmed with the UF HRPP[^hrpp].

**Action (human, mostly mechanical):** confirm the UF sub-board with the HRPP via myIRB; build the **reliance-agreement / site-authorization roster** for every participating site and partner clinic; set CITI[^citi] training host = UF.

---

## 3. Special issues this study must address (PHI + drug + genetic + commercial)

Because the study is prospective, participant-facing, and touches clinic-held PHI, the PHI/agreement surface is now the heaviest one. The COI, ROR, CLIA, and GINA items carry over from the peptide plan.

- **PHI, HIPAA authorization, and partner-clinic agreements — the new gate.** Partner clinics are covered entities, so their patient records are PHI[^phi]. Enrolling their patients and analyzing clinic-held biomarker data requires **participant informed consent plus HIPAA authorization**[^hipaa], and a **Business Associate Agreement (BAA)**[^baa] and/or **Data Use Agreement (DUA)**[^dua] with each partner clinic governing what data flows to FMB and under what safeguards. This is a first-class deliverable, not a footnote: no data moves before the consent, authorization, and clinic agreement are executed.
- **IND posture / drug administration — non-interventional across all peptides.** The study administers, supplies, doses, or directs **nothing**. For the approved GLP-1 class, the applicable exemption reasoning is the **21 CFR 312.2(b)** lawfully-marketed-drug analysis: a clinical investigation of an approved drug is exempt from IND when it is not intended to support a new indication or labeling/advertising change, does not significantly increase risk (route/dose/population) over approved use, and complies with IRB and informed-consent rules. For the **unapproved research peptides**, 312.2(b) does not apply (they are not lawfully marketed); the correct basis is that the study is **non-interventional** — the clinic prescribes and the study only observes, so no clinical investigation of a drug attaches to FMB and no IND is triggered. Either way, the result is the same: **no IND, because FMB observes and never directs the drug.** Document the determination affirmatively; do not leave it implicit.
- **Unapproved peptides — adverse-event observation and reporting posture.** For research peptides (BPC-157, TB-500, and the rest of `PEPTIDE_MEASUREMENTS`), the study **observes and records** adverse events as part of longitudinal tracking; it **does not manage therapy or issue clinical directives**. Clinical management of any AE remains with the participant's own prescribing clinician. The protocol must specify an AE-observation/recording workflow and an escalation path (advise the participant to contact their treating clinician; report to the IRB per protocol) that stops short of directing care. GLP-1 RAs, being approved and best-characterized, sit at the low-risk end of this same posture.
- **GLP-1 (and general) adverse-event profile must be in the protocol and consent.** Even an observational study should reference known risks so consent is honest. For GLP-1 RAs: the most common are **GI** (nausea, vomiting, diarrhea); labeled/boxed concerns include **thyroid C-cell tumor**[^boxed] risk (contraindicated with personal/family history of MTC or MEN2), plus signals for **pancreatitis, gallbladder disease, ileus, peri-operative aspiration**, and a more recent **NAION**[^naion] association. For unapproved peptides, consent must disclose that the evidence base is sparse and the safety profile incompletely characterized. The study does not manage these (the treating clinician does), but consent must not pretend they do not exist.
- **Conflict of interest — gating, not boilerplate.** FMB **recommends and sells** the engine/predictor and holds a **patent disclosure** (UF Innovate). A written **financial COI management plan** is required regardless of lane. Note the boundary: FMB does **not** prescribe, supply, or sell the peptides themselves in this study, so the classic "company sells the drug and runs the response study" conflict does not arise here — the conflict to manage is FMB's commercial interest in the *predictor*.
- **Compounded product — a clinic-side supply detail, disclosed not owned.** Some partner clinics may prescribe **compounded** GLP-1 or peptide products (503A[^compound] patient-specific compounding; 503B outsourcing is curtailed for semaglutide/tirzepatide since FDA removed them from the shortage list in 2024-2025). Compounded product is **not** FDA-approved, and consent should disclose that a participant's therapy may be compounded. But in this observational model that supply chain belongs to the **clinic and the treating clinician**, not to FMB — FMB observes and never supplies. Surface it in consent risk disclosures; it does not create an FMB supply-chain COI.
- **Return-of-results / actionability.** A genotype-based "predicted low responder" call is **clinically actionable**, which raises ROR[^ror] stakes. GLP-1 response prediction is currently **research-grade/polygenic** — there is **no CPIC**[^cpic] guideline and no FDA-actionable PGx label for GLP-1 RAs (candidate loci such as *GLP1R*, *TCF7L2*, *GIPR* are research signals, not clinical determinants); the same research-grade caveat applies more strongly to the unapproved peptides. State plainly: predictions are research-only, not for clinical decision-making, and not returnable as clinical results without **CLIA**[^clia] confirmation. The ACMG81 secondary-findings ROR plan still applies on the genomic side.
- **Genetic-privacy / GINA**[^gina]. Consent and data-security language must address genetic-data sensitivity, re-identification risk, and GINA's protections (and its gaps — life, disability, and long-term-care insurance are not covered).
- **Recruitment and coercion.** Recruit at partner clinics from patients *already* on peptide therapy. Avoid enrolling the investigators' own students, employees, or subordinates; clinic staff must not pressure patients to enroll, and consent must make clear that enrollment is voluntary and does not affect their care.

---

## 4. Document checklist (by lane)

**Lane A (NHSR) — Stage-1 track:**
- [ ] NHSR determination request (UF form via myIRB)
- [ ] One-paragraph description: reference materials only, no identifiable humans

**Lane B (Exempt) — Stage-1 secondary-data track only:**
- [ ] Exempt determination request (cite 46.104(d)(4))
- [ ] Data description: source, de-identification basis, no key to identity
- [ ] DUA, if the existing dataset requires one
- [ ] Drug-posture declaration: secondary analysis only (no IND)

**Lane C (Expedited) — the reframed prospective observational cohort:**
- [ ] **Protocol** (objectives; correlation of genomic predictions against per-peptide biomarker trajectories; response endpoints per `engine/peptides/measurements.py` — e.g. % weight change and HbA1c change for GLP-1 RAs; enrollment plan; sample size/power; analysis plan)
- [ ] **Informed consent** — includes peptide AE disclosure (GLP-1 profile and the sparse-evidence caveat for unapproved peptides) and disclosure that therapy may be compounded
- [ ] **HIPAA authorization** for use/disclosure of clinic-held PHI
- [ ] **BAA and/or DUA with each partner clinic** governing the PHI/biomarker data flow to FMB
- [ ] **Data management and security plan**
- [ ] **AE-observation / recording plan** (observe and record; escalate to the treating clinician; no clinical management) — required given unapproved peptides in scope
- [ ] **ROR / incidental-findings plan** (ACMG SF[^acmgsf] for the genomic side; peptide response predictions explicitly research-only)
- [ ] **Financial COI management plan** (FMB's commercial interest in the predictor) - required regardless of lane
- [ ] **Non-interventional / IND-not-applicable memo** — affirms clinic-prescribes / study-observes across all peptides; cites 21 CFR 312.2(b) for the approved GLP-1 class and the non-interventional basis for unapproved peptides
- [ ] Recruitment materials (recruit at partner clinics from patients already on peptide therapy)
- [ ] PI CV + qualified-personnel list; **reliance agreements / site-authorization roster (sIRB)**

**Cross-cutting (all lanes):**
- [ ] **CITI Human Subjects Research training** (host = UF)
- [ ] Named **PI of record** with appropriate credentials
- [ ] **Reliance roster** for every ceding site and partner clinic (sIRB)

---

## 5. Submission sequence

1. **Build the Lane Table + drug-posture declaration** (Section 1) — assign every data source a lane and affirm the observational posture for the cohort. *(delegable — I can draft)*
2. **Confirm UF sub-board** with the HRPP and **assemble the reliance roster**, including partner clinics (Section 2). *(human, mechanical)*
3. **Execute partner-clinic agreements** — BAA and/or DUA with each clinic, so PHI/biomarker data can flow lawfully (Section 3). *(human-led, I draft)*
4. **File the non-interventional / IND-not-applicable memo** (Section 3): clinic prescribes, study observes, across all peptides. No interventional arm exists, so no IND analysis beyond that affirmation is needed. *(human decision; I can draft the memo)*
5. **Complete CITI training** (host = UF) for all personnel. *(human)*
6. **Draft lane-appropriate documents** (Section 4), including informed consent + HIPAA authorization and peptide AE language. *(delegable)*
7. **Author the COI management plan** (FMB's interest in the predictor) and route through the UF COI office. *(human-led, I draft)*
8. **Submit to UF IRB as sIRB**; execute reliance agreements; respond to stipulations.
9. **Approval/determination in hand** then begin Lane A/B; Lane C after Expedited approval. **Maintain**: continuing review, amendments, AE reporting per protocol.

---

## 6. Indicative timeline

| Lane / posture | Typical UF IRB turnaround | Gating dependency |
|---|---|---|
| A (NHSR) | days to 2 weeks | reference materials identified |
| B (Exempt, Stage-1 secondary data) | 1 to 4 weeks | de-identification documented |
| C (Expedited, prospective observational) | 3 to 8 weeks | protocol + consent + HIPAA authorization + BAA/DUA + security + AE-observation plan |
| sIRB reliance execution | parallel, 2 to 6 weeks/site | SMART IRB letters; site and partner-clinic authorizations |

Full-board review is not anticipated: the study is observational and minimal-risk. It would only apply if an intervention or identifiable clinical return-of-results were added — out of scope for this plan.

---

## 7. Task split — yours vs. delegable

**Only-you (human decisions / accountability):**
- Confirm the **observational commitment**: the study observes therapy participants are already prescribed and never prescribes, supplies, doses, or directs any peptide (Section 1, Section 3).
- Stand up the **PHI / partner-clinic layer** — the real driver here: execute **BAA/DUA** with each clinic and approve the **HIPAA authorization** language (Section 3).
- Confirm UF sub-board; serve as / name the **PI**; complete **CITI**.
- Sign the **COI management plan**; final **return-of-results** go/no-go.

**Hand to me (drafting, once the above are set):**
- The **Lane Table** + cohort-wide observational drug-posture declaration.
- Draft **protocol**, **informed consent** (with peptide AE disclosure), **HIPAA authorization**, **data-management/security plan**, **AE-observation plan**, **NHSR/Exempt** requests for the Stage-1 track.
- Draft the **non-interventional / IND-not-applicable memo** (312.2(b) for the GLP-1 class; non-interventional basis for unapproved peptides).
- Draft the **COI management plan** and the **reliance-agreement / partner-clinic roster** scaffold for the sIRB.

---

*Cross-references: `docs/irb-plan.md` (the peptide-class playbook this adapts), `docs/clinical-validation-plan.md` Section 3 (intended use / regulatory posture), Sections 9 to 11 (validation designs / endpoints), Section 13 (privacy/security), Section 18 (governance/ethics). The UF-sIRB decision is recorded for the program as a whole, not just this study.*

[^glp1ra]: **GLP-1 receptor agonist (GLP-1 RA)** — a class of drugs that mimic glucagon-like peptide-1, used for type-2 diabetes and obesity; they enhance insulin secretion, slow gastric emptying, and reduce appetite.
[^sema]: **Semaglutide** — a long-acting GLP-1 RA marketed as Ozempic and Rybelsus (type-2 diabetes) and Wegovy (chronic weight management).
[^tirz]: **Tirzepatide** — a once-weekly **dual GIP/GLP-1** receptor agonist (Mounjaro for diabetes, Zepbound for obesity); related to but mechanistically broader than pure GLP-1 RAs, included here as part of "the class."
[^boxed]: **Boxed warning (thyroid C-cell tumors)** — GLP-1 RA labels carry a boxed warning based on rodent medullary thyroid carcinoma findings; contraindicated in patients with personal/family history of medullary thyroid carcinoma (MTC) or MEN2.
[^naion]: **NAION (non-arteritic anterior ischemic optic neuropathy)** — a form of sudden optic-nerve injury; a 2024 study reported an association signal with semaglutide use, still under investigation.
[^commonrule]: **Common Rule (45 CFR 46)** — the U.S. federal regulation governing protection of human research subjects; its definitions decide whether an activity is "human subjects research."
[^nhsr]: **NHSR (Not Human Subjects Research)** — a formal IRB determination that an activity falls outside the Common Rule, so full review does not apply (the written letter still matters).
[^exempt]: **Exempt** — an IRB determination that research meets a regulatory exemption category (e.g. secondary use of de-identified data); lighter than expedited or full-board review but still an official determination. In this plan it applies only to the Stage-1 secondary-data track, not to the prospective cohort.
[^sirb]: **sIRB (single IRB of record)** — for multi-site research, one IRB reviews on behalf of all sites (45 CFR 46.114 + NIH policy); other sites cede their review to it.
[^smart]: **SMART IRB** — a national master reliance agreement and platform that lets institutions cede IRB review to a single reviewing IRB without negotiating a bespoke agreement each time.
[^onefl]: **OneFlorida+** — a Florida clinical research consortium / data network whose member sites can rely on a shared IRB infrastructure.
[^hrpp]: **HRPP (Human Research Protection Program)** — the institution-wide office that houses the IRB and issues determination letters; at UF, accessed via the myIRB system.
[^citi]: **CITI training** — the standard online Human Subjects Research / Good Clinical Practice training program required of study personnel; hosted by the IRB-of-record's institution (here, UF).
[^phi]: **PHI (Protected Health Information)** — individually identifiable health information held by a HIPAA covered entity (such as a prescribing clinic); its use and disclosure for research require authorization or a waiver.
[^hipaa]: **HIPAA authorization** — a participant's signed permission for a covered entity to use or disclose their PHI for a specified research purpose; distinct from, and usually combined with, the informed-consent form.
[^baa]: **BAA (Business Associate Agreement)** — a HIPAA contract under which a covered entity permits a business associate (here, FMB) to handle PHI on its behalf, binding the associate to safeguard the data.
[^dua]: **DUA (Data Use Agreement)** — an agreement governing the transfer and permitted uses of a dataset (often a HIPAA limited data set) between the data provider and the recipient.
[^compound]: **503A / 503B compounding** — sections of the Food, Drug & Cosmetic Act governing pharmacy compounding: 503A is patient-specific compounding by a pharmacy; 503B is an FDA-registered outsourcing facility. Compounded drugs are **not** FDA-approved; mass compounding of a drug is generally permitted only during an official shortage.
[^cpic]: **CPIC (Clinical Pharmacogenetics Implementation Consortium)** — publishes peer-reviewed, actionable gene-drug dosing guidelines. There is **no** CPIC guideline for GLP-1 RAs, so any genotype-based response prediction for them is research-grade, not clinically actionable.
[^clia]: **CLIA-certified** — the federal certification required to return clinical lab results to patients; the research pipeline lacks it, so its genotype/response calls cannot be returned as clinical results.
[^ror]: **ROR (return of results)** — the policy on whether, and how, individual research findings are given back to participants; must be stated up front.
[^acmgsf]: **ACMG SF (Secondary Findings)** — the ACMG list of clinically actionable genes (the engine's default ACMG81 panel) whose pathogenic findings the genomic side of the study may encounter.
[^gina]: **GINA (Genetic Information Nondiscrimination Act)** — U.S. law barring genetic discrimination in health insurance and employment; it does **not** cover life, disability, or long-term-care insurance — a gap to disclose in consent.
