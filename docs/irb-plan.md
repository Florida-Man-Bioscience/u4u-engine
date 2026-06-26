# IRB Setup Plan — Performance Testing of the U4U / PeptidIQ Pipeline

**Document type:** IRB submission playbook (operational companion to the Clinical Validation Master Plan)
**Scope:** What is required to obtain IRB coverage for a study that **tests the analytical and clinical performance** of the `u4u-engine` pipeline.
**Status:** DRAFT v0.1 — planning artifact. Not a determination that any activity is or is not human-subjects research; only the IRB of record can make that call.
**Relationship to other docs:** This is the *submission playbook*. The governance/ethics rationale lives in `docs/clinical-validation-plan.md` §18 (Governance, Ethics, Oversight) and §9–§11 (the analytical/clinical validation designs this study would execute). This document does **not** restate them — it operationalizes the IRB path.

---

> **Read first — scope assumption.** This plan assumes "test the performance of the pipeline" means running **existing genome files** through the pipeline and comparing its output to a truth/reference standard (analytical concordance) and, where available, to clinical reference results (clinical concordance). It does **not** assume drawing new specimens from participants. **If new blood/saliva collection or prospective recruitment is intended, that is a different and larger undertaking** (consent, biobanking, full-board review — Lane C below); flag it and this plan expands accordingly.

---

## 1. The threshold question — is this even Human Subjects Research?

Most of pipeline *performance* testing can be done **without** triggering full IRB review, because it uses reference materials and de-identified data that are not "human subjects" under the Common Rule (45 CFR 46). **But "no full review" is not "no IRB" — you still need the IRB/HRPP to issue a written determination** (NHSR or Exempt). Journals, regulators (FDA/CAP), and partners will later ask to see that letter.

Route **every planned data source** into one of three lanes:

| Lane | What it covers | Example sources | IRB action needed | Review burden |
|---|---|---|---|---|
| **A — Not Human Subjects Research (NHSR)** | Commercial / public **reference materials** with known truth genotypes; no living individual is identifiable | GIAB/NIST (NA12878 etc.), **GeT-RM** Coriell PGx cell lines (CYP2D6/2C19 diplotypes), PharmVar reference data | One-page **NHSR determination request** | Lowest — letter, no protocol |
| **B — Exempt** (45 CFR 46.104(d)(4)) | Secondary research on **existing, de-identified** human genomes the team did not generate for this study | 1000 Genomes, openSNP, de-identified institutional VCFs (no codes back to identity) | **Exempt determination request** + brief data description | Low — IRB confirms exemption |
| **C — Expedited / Full Board** | **Identifiable** existing samples; controlled-access data linked to identifiers; anything **prospective** or that **returns results** | Institutional biobank with a code key; dbGaP controlled-access tied to phenotypes; any real-patient concordance where re-identification is possible; new collection | Full **protocol + consent (or waiver) + data security plan** | Highest |

**The single most useful artifact to produce first** is the table below — every data source you intend to use, assigned to a lane. This is what determines how much IRB work there actually is.

| Planned data source | Identifiable? | Generated for this study? | → Lane | Owner action |
|---|---|---|---|---|
| GIAB NA12878 (analytical truth set) | No | No | **A** | _TBD_ |
| GeT-RM Coriell PGx panel (star-allele truth) | No | No | **A** | _TBD_ |
| 1000 Genomes / openSNP (de-identified) | No | No | **B** | _TBD_ |
| Institutional / clinical VCFs w/ concordance labels | _depends on key_ | No | **B or C** | _confirm de-id_ |
| Any real-patient samples or returned results | Yes | Maybe | **C** | _full review_ |
| _add every source here_ | | | | |

> **Design implication:** scope the *analytical* performance study (accuracy, precision, sensitivity/specificity, star-allele and STR concordance — `docs/clinical-validation-plan.md` §9) to land almost entirely in **Lanes A/B**. Reserve **Lane C** for *clinical* concordance on real patients, and submit it as a separate, later protocol. Don't let one Lane-C source drag the whole performance study into full review.

---

## 2. Which IRB has jurisdiction — VERIFY, don't assume

This turns on **which entity is "engaged" in the research** (obtains identifiable data / consent / federal funding), and the signals here genuinely conflict. **This is a decision only you can make — flagged, not guessed:**

- The work sits under a **UF Dropbox**, and there's a **UF Innovate patent disclosure** in the repo → points to **University of Florida** engagement (UF IRB-01, or **IRB-02 / Health Science Center** for clinical/health data).
- But **Florida Man Bioscience is a company** that recommends *and* sells peptides → points to a **commercial / central IRB** (Advarra, WCG) for the corporate entity.

**Discriminators to confirm (answer these and the path falls out):**

1. **Is there federal funding** touching this work? → may trigger **single-IRB (sIRB)** requirements.
2. **Are UF personnel, resources, data, or UF-owned IP central** to the study? → UF IRB likely **must** be engaged; FMB may rely on it via a **reliance agreement**.
3. **Is FMB the entity obtaining identifiable data / running the study?** → FMB is "engaged" and needs **its own IRB** (commercial IRB is the standard route) or a reliance agreement with UF's.

→ **Action (human):** determine engaged entity/entities and pick the IRB of record before drafting the submission. Everything downstream (forms, fees, CITI training host, reliance agreements) depends on it.

---

## 3. Special issues this study must address (genetic + investigational + commercial)

These are the items an IRB will specifically scrutinize for *this* pipeline. Most only apply to **Lane C**, but the COI item applies regardless.

- **Conflict of interest — gating, not boilerplate.** The same organization both **recommends and sells** the peptides, and there is a **patent disclosure**. A written **financial COI management plan** is something the IRB (and an institutional COI committee) will *require* before approval. This is its own deliverable, independent of lane.
- **Return-of-results / incidental findings (Lane C only).** The pipeline's **default input filter is the ACMG SF "actionable" gene panel (ACMG81)** — so the study will, by construction, encounter reportable secondary findings. A written **ROR / non-return plan** is mandatory: state up front whether results are returned, and if not, why (research-grade, not clinical).
- **CLIA boundary (Lane C only).** Research-grade pipeline calls **cannot be returned to participants as clinical results** without confirmation in a **CLIA-certified lab**. The protocol must say results are research-only and not for clinical decision-making.
- **Investigational peptides — study the predictor, never return the claim.** The protocol tests whether labels like "Strong Fit" *predict* anything; it must **not** hand any participant an efficacy assertion for BPC-157/TB-500/etc. (see `docs/clinical-validation-plan.md` §11.6, §12.4). This is a hard constraint on consent language and any participant-facing output.
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

**Lane C (Expedited/Full):**
- [ ] **Protocol** (objectives, performance endpoints, reference standard, sample size/power, statistical analysis plan — pull endpoints from `clinical-validation-plan.md` §9–§11)
- [ ] **Informed consent** (or documented waiver of consent/HIPAA authorization, if secondary data meets criteria)
- [ ] **Data management & security plan** (storage, encryption at rest/in transit, access control, retention; addresses the current `api.py`/`jobs.json` gaps — `clinical-validation-plan.md` §13)
- [ ] **ROR / incidental-findings plan** (ACMG SF)
- [ ] **Financial COI management plan** ← required regardless of lane
- [ ] Recruitment materials (only if prospective)
- [ ] DUA / dbGaP DAC approval (if controlled-access)
- [ ] PI CV + qualified-personnel list; reliance agreement (if multi-entity)

**Cross-cutting (all lanes, before submission):**
- [ ] **CITI Human Subjects Research training** for all study personnel (host = the IRB of record's institution)
- [ ] Named **PI of record** with appropriate credentials

---

## 5. Submission sequence

1. **Build the Lane Table** (§1) — assign every data source. *(delegable — I can draft from the planned source list)*
2. **Determine the engaged entity → pick the IRB of record** (§2). *(human decision)*
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
| C (Expedited) | 3–8 weeks | protocol + consent + security plan complete |
| C (Full Board) | 1–3 months | board meeting cycle; COI + ROR plans |

The analytical performance work (Lanes A/B) can therefore start **weeks** ahead of any clinical-concordance work (Lane C). Sequence accordingly.

---

## 7. Task split — yours vs. delegable

**🔴 Only-you (human decisions / accountability):**
- Determine the engaged entity and **pick the IRB of record** (§2) — blocks everything.
- Decide the **scope fork**: existing-data-only vs. new specimen collection (§ scope note).
- Serve as / name the **PI of record**; complete **CITI training**.
- Sign the **COI management plan** and route it through the institutional COI office.
- Final go/no-go on **return-of-results** policy.

**🟢 Hand to me (drafting, once the above are set):**
- The **Lane Table** from your list of intended data sources.
- Draft **protocol**, **informed consent**, **data-management/security plan**, and the **NHSR/Exempt request** text.
- Draft the **COI management plan** for your review.
- A performance-endpoints section pulled from `clinical-validation-plan.md` §9–§11 (sensitivity/specificity, star-allele concordance vs GeT-RM, etc.).

---

*Cross-references: `docs/clinical-validation-plan.md` §3 (intended use / regulatory posture), §9–§11 (analytical & clinical validation designs = the study endpoints), §13 (privacy/security = the data-management plan), §18 (governance/ethics rationale).*
