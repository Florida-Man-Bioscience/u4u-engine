# IRB Setup Plan — Pharmacogenomic Response Prediction for GLP-1 Receptor Agonists (Semaglutide and Class)

**Document type:** IRB submission playbook — GLP-1 variant (companion to `docs/irb-plan.md`)
**Scope:** What is required to obtain IRB coverage for a study that uses the `u4u-engine` / PeptidIQ pipeline to **predict individual response to GLP-1 receptor agonists**[^glp1ra] (semaglutide[^sema] and the related incretin class) from genetic and biomarker data.
**Status:** DRAFT v0.1 — planning artifact. Not a determination that any activity is or is not human-subjects research, nor a regulatory determination about drug administration; only the IRB of record and (where relevant) FDA can make those calls.
**Relationship to other docs:** This mirrors the lane/checklist structure of `docs/irb-plan.md` but adapts it for an **FDA-approved drug class**. Where the peptide plan treats the agents as *investigational and unapproved*, this plan treats GLP-1 RAs as *lawfully marketed* — which lowers the investigational-risk posture but adds a drug-administration / IND[^ind] question the peptide plan never had to face.

---

> **Read first — scope assumption.** This plan assumes the study **observes** response to GLP-1 RAs that participants are *already prescribed and taking under the care of their own clinicians*, and correlates that response with genotype/biomarker data the pipeline analyzes. It does **not** assume the study *prescribes, supplies, doses, or directs administration* of any GLP-1 RA. **The moment the study itself administers or assigns the drug, the regulatory frame changes** (drug-administration risk review, the IND-exemption analysis in §3, possible IND) and this plan expands accordingly. Flag that fork explicitly before drafting.

---

## 0. Why GLP-1 is a different regulatory animal than the research peptides

The peptide plan (`irb-plan.md`) treats BPC-157 / TB-500 / etc. as **unapproved, investigational** substances — hence its hard rule "study the predictor, never return the claim." GLP-1 RAs invert several of those assumptions, and the differences drive everything below:

| Dimension | Research peptides (`irb-plan.md`) | GLP-1 RAs (this plan) |
|---|---|---|
| FDA status | Unapproved / gray-market | **Approved** — semaglutide (Ozempic, Wegovy, Rybelsus), liraglutide (Victoza, Saxenda), dulaglutide (Trulicity), exenatide; tirzepatide[^tirz] (Mounjaro, Zepbound) is a related **dual GIP/GLP-1** agonist |
| Efficacy/safety base | Sparse, often preclinical/single-group | Large RCT base; established label, **boxed warning**[^boxed] and known AE profile |
| Core IRB worry | "Don't hand participants an unproven efficacy claim" | "Don't *direct* a prescription drug without the right drug-administration review / IND posture" |
| New axis introduced | — | **IND-exemption analysis** (21 CFR 312.2(b)); **compounding** legality; **AE-monitoring** duties |
| Return-of-results stakes | Low (research-grade peptide labels) | **Higher** — a genotype-based "likely non-responder to semaglutide" call is clinically actionable, so the CLIA[^clia]/ROR[^ror] boundary matters more |

**Net:** the *investigational-substance* risk goes **down** (these are studied, approved drugs), but two **new** review surfaces appear — the **IND/drug-administration** question (§3) and **compounded-GLP-1 legality** (§3) — and the **return-of-results** boundary gets sharper because the prediction is more actionable.

---

## 1. The threshold question — is this even Human Subjects Research? (and which *kind*)

Two orthogonal questions must both be answered:

**(a) Common Rule[^commonrule] lane** — same A/B/C partition as the peptide plan, driven by data identifiability:

| Lane | What it covers | Example sources | IRB action | Burden |
|---|---|---|---|---|
| **A — Not Human Subjects Research (NHSR)**[^nhsr] | Reference materials with known truth genotypes; no identifiable living individual | GIAB/NIST, GeT-RM Coriell PGx cell lines, PharmVar | One-page NHSR request | Lowest |
| **B — Exempt**[^exempt] (45 CFR 46.104(d)(4)) | Secondary research on **existing, de-identified** genotype↔GLP-1-response data the team did not generate | De-identified EHR/registry extracts of patients on GLP-1 RAs (weight, HbA1c, tolerability) with no key to identity | Exempt determination + data description | Low |
| **C — Expedited / Full Board** | **Identifiable** or **prospective** data; anything that **returns results** or **touches drug administration** | Prospective cohort of consented patients on prescribed GLP-1 RAs; any re-identifiable concordance; any arm that directs dosing | Full protocol + consent + data-security + AE plan | Highest |

**(b) Drug-involvement axis** — *new for GLP-1*, independent of the lane:

| Study posture | Does the study touch the drug? | Likely FDA frame |
|---|---|---|
| **Pure secondary analysis** | No — only analyzes existing genotype + outcome data | No IND; usually Lane B Exempt |
| **Prospective observational** | No — patients take drug as prescribed by *their own* clinician; study only measures | No IND (non-interventional); Lane C, expedited possible |
| **Interventional** | Yes — study assigns, supplies, doses, or directs the GLP-1 RA | **IND-exemption analysis required** (21 CFR 312.2(b)); IND if not exempt; Lane C full board |

> **Design implication:** keep the response-prediction study **observational** (genotype ↔ outcome on drug taken as already prescribed). That keeps it out of IND territory and most likely in **Lane B/C-expedited**. An interventional arm is a separate, heavier, later protocol — do not let it drag the predictor-validation study into IND review.

**First artifact to produce:** the same per-source lane table as the peptide plan, plus a one-line **drug-posture** declaration (observational vs interventional) for each study arm.

---

## 2. Which IRB has jurisdiction — RESOLVED: UF as single IRB of record

Unlike the peptide plan (which left this open), the institutional decision is **made**:

- **University of Florida IRB is the canonical IRB of record**, and because this is a **multi-site** study, UF IRB serves as the **single IRB of record (sIRB)**[^sirb] under the Common Rule cooperative-research provision (45 CFR 46.114) and NIH sIRB policy.
- **All other sites cede review to UF** via reliance agreements — **SMART IRB**[^smart] as the standard reliance mechanism; **OneFlorida+**[^onefl] for in-network sites.
- Florida Man Bioscience relies on UF rather than standing up its own commercial IRB.
- The specific UF board routes by data type (IRB-01 Gainesville Health Science Center for genomic/clinical; IRB-02 social/behavioral; IRB-03 Jacksonville) — institution is fixed, sub-board is a routing detail confirmed with the UF HRPP[^hrpp].

→ **Action (human, mostly mechanical now):** confirm the UF sub-board with the HRPP via myIRB; build the **reliance-agreement / site-authorization roster** for every participating site; set CITI[^citi] training host = UF.

---

## 3. Special issues this study must address (drug + genetic + commercial)

The COI, ROR, CLIA, and GINA items carry over from the peptide plan. GLP-1 adds three review surfaces.

- **IND posture / drug administration — the new gate.** If any arm administers, supplies, or directs the GLP-1 RA, run the **21 CFR 312.2(b) IND-exemption analysis**: a clinical investigation of a *lawfully marketed* drug is exempt from IND only if it is **not** intended to support a new indication/labeling change, is **not** intended to support a change in advertising, does **not** significantly increase the risk (route/dose/population) over approved use, and complies with IRB + informed-consent rules. A purely **observational** study of patients on their own prescriptions is **non-interventional** and needs no IND — keep it there if at all possible. Document the determination; do not leave it implicit.
- **Compounded GLP-1 — a hard commercial flag.** If Florida Man Bioscience **sells or supplies compounded semaglutide/tirzepatide**, that is a serious, separate regulatory exposure: FDA removed semaglutide and tirzepatide from the drug-shortage list (2024–2025), which curtails mass **503B**[^compound] compounding; patient-specific **503A** compounding remains but is under active FDA/state scrutiny, and compounded product is **not** FDA-approved. The IRB and COI committee will treat "company sells the compounded drug *and* runs the response study" as a major conflict. **Surface the supply chain explicitly** — approved branded product vs. compounded — because it changes both the COI plan and the consent's risk disclosures.
- **GLP-1 adverse-event profile must be in the protocol & consent.** Even observational studies should reference the known risks so consent is honest: most common are **GI** (nausea, vomiting, diarrhea); labeled/boxed concerns include **thyroid C-cell tumor**[^boxed] risk (contraindicated with personal/family history of MTC or MEN2), and signals for **pancreatitis, gallbladder disease, ileus, peri-operative aspiration**, and a more recent **NAION**[^naion] association. The study does not manage these (the treating clinician does), but consent must not pretend they don't exist.
- **Conflict of interest — gating, not boilerplate.** Same as the peptide plan: FMB **recommends and sells** the product and holds a **patent disclosure** (UF Innovate). A written **financial COI management plan** is required regardless of lane — and is *heavier* here if compounded product is involved.
- **Return-of-results / actionability.** A genotype-based "predicted low responder to semaglutide" is **clinically actionable**, which raises the ROR stakes versus the peptide labels. Note also that GLP-1 response prediction is currently **research-grade/polygenic** — there is **no CPIC**[^cpic] guideline and no FDA-actionable PGx label for GLP-1 RAs (candidate loci such as *GLP1R*, *TCF7L2*, *GIPR* are research signals, not clinical determinants). State plainly: predictions are research-only, not for clinical decision-making, and not returnable as clinical results without **CLIA** confirmation.
- **Genetic-privacy / GINA**[^gina]. Consent and data-security language must address genetic-data sensitivity, re-identification risk, and GINA's protections (and its gaps — life/disability/long-term-care insurance are not covered).

---

## 4. Document checklist (by lane)

**Lane A (NHSR):**
- [ ] NHSR determination request (UF form via myIRB)
- [ ] One-paragraph description: reference materials only, no identifiable humans

**Lane B (Exempt):**
- [ ] Exempt determination request (cite 46.104(d)(4))
- [ ] Data description: source, de-identification basis, no key to identity
- [ ] DUA, if the dataset requires one
- [ ] **Drug-posture declaration: observational / secondary only (no IND)**

**Lane C (Expedited/Full):**
- [ ] **Protocol** (objectives, response endpoints — % weight change, HbA1c change, tolerability/discontinuation; reference standard; sample size/power; analysis plan)
- [ ] **Informed consent** (or documented waiver, if secondary data qualifies) — includes GLP-1 AE disclosure
- [ ] **Data management & security plan**
- [ ] **ROR / incidental-findings plan** (ACMG SF[^acmgsf] for the genomic side; GLP-1 response predictions explicitly research-only)
- [ ] **Financial COI management plan** ← required regardless of lane; expanded if compounded product is involved
- [ ] **IND-exemption memo (21 CFR 312.2(b))** — required for *any* interventional arm; affirmative "observational, IND-not-applicable" note otherwise
- [ ] **Supply-chain statement** — branded vs compounded GLP-1, if the study touches the drug at all
- [ ] Recruitment materials (if prospective)
- [ ] PI CV + qualified-personnel list; **reliance agreements / site-authorization roster (sIRB)**

**Cross-cutting (all lanes):**
- [ ] **CITI Human Subjects Research training** (host = UF)
- [ ] Named **PI of record** with appropriate credentials
- [ ] **Reliance roster** for every ceding site (sIRB)

---

## 5. Submission sequence

1. **Build the Lane Table + drug-posture declaration** (§1) — assign every data source a lane *and* an observational/interventional posture. *(delegable — I can draft)*
2. **Confirm UF sub-board** with the HRPP and **assemble the reliance roster** (§2). *(human, mechanical)*
3. **Complete CITI training** (host = UF) for all personnel. *(human)*
4. **Run the IND-exemption analysis** for any interventional arm; otherwise file the observational note (§3). *(human decision; I can draft the memo)*
5. **Draft lane-appropriate documents** (§4), including GLP-1 AE language in consent. *(delegable)*
6. **Author the COI management plan** (heavier if compounded product) and route through the UF COI office. *(human-led, I draft)*
7. **Submit to UF IRB as sIRB**; execute reliance agreements; respond to stipulations.
8. **Approval/determination in hand** → begin Lane A/B; Lane C after approval. **Maintain**: continuing review, amendments, AE reporting per protocol.

---

## 6. Indicative timeline

| Lane / posture | Typical UF IRB turnaround | Gating dependency |
|---|---|---|
| A (NHSR) | days–2 weeks | reference materials identified |
| B (Exempt, observational) | 1–4 weeks | de-identification documented; observational posture confirmed |
| C (Expedited, observational) | 3–8 weeks | protocol + consent + security + AE plan |
| C (Full Board) or any interventional/IND arm | 1–3 months+ | board cycle; COI + ROR; IND-exemption memo or IND |
| sIRB reliance execution | parallel, 2–6 weeks/site | SMART IRB letters; site authorizations |

---

## 7. Task split — yours vs. delegable

**🔴 Only-you (human decisions / accountability):**
- Decide the **drug posture**: observational vs interventional — this is the single biggest driver here (§1, §3).
- Disclose the **supply chain**: branded vs **compounded** GLP-1, and FMB's commercial role (§3).
- Confirm UF sub-board; serve as / name the **PI**; complete **CITI**.
- Sign the **COI management plan**; final **return-of-results** go/no-go.

**🟢 Hand to me (drafting, once the above are set):**
- The **Lane Table** + per-arm drug-posture declaration.
- Draft **protocol**, **informed consent** (with GLP-1 AE disclosure), **data-management/security plan**, **NHSR/Exempt** requests.
- Draft the **IND-exemption memo** (21 CFR 312.2(b)) or the observational "IND-not-applicable" note.
- Draft the **COI management plan** and the **reliance-agreement roster** scaffold for the sIRB.

---

*Cross-references: `docs/irb-plan.md` (the peptide-class playbook this adapts), `docs/clinical-validation-plan.md` §3 (intended use / regulatory posture), §9–§11 (validation designs / endpoints), §13 (privacy/security), §18 (governance/ethics). The UF-sIRB decision is recorded for the program as a whole, not just this study.*

[^glp1ra]: **GLP-1 receptor agonist (GLP-1 RA)** — a class of drugs that mimic glucagon-like peptide-1, used for type-2 diabetes and obesity; they enhance insulin secretion, slow gastric emptying, and reduce appetite.
[^sema]: **Semaglutide** — a long-acting GLP-1 RA marketed as Ozempic and Rybelsus (type-2 diabetes) and Wegovy (chronic weight management).
[^tirz]: **Tirzepatide** — a once-weekly **dual GIP/GLP-1** receptor agonist (Mounjaro for diabetes, Zepbound for obesity); related to but mechanistically broader than pure GLP-1 RAs, included here as "the class."
[^ind]: **IND (Investigational New Drug application)** — the FDA authorization normally required before administering an investigational drug to humans; clinical studies of *already-marketed* drugs may be **exempt** under 21 CFR 312.2(b).
[^boxed]: **Boxed warning (thyroid C-cell tumors)** — GLP-1 RA labels carry a boxed warning based on rodent medullary thyroid carcinoma findings; contraindicated in patients with personal/family history of medullary thyroid carcinoma (MTC) or MEN2.
[^naion]: **NAION (non-arteritic anterior ischemic optic neuropathy)** — a form of sudden optic-nerve injury; a 2024 study reported an association signal with semaglutide use, still under investigation.
[^commonrule]: **Common Rule (45 CFR 46)** — the U.S. federal regulation governing protection of human research subjects; its definitions decide whether an activity is "human subjects research."
[^nhsr]: **NHSR (Not Human Subjects Research)** — a formal IRB determination that an activity falls outside the Common Rule, so full review does not apply (the written letter still matters).
[^exempt]: **Exempt** — an IRB determination that research meets a regulatory exemption category (e.g. secondary use of de-identified data); lighter than full-board review but still an official determination.
[^sirb]: **sIRB (single IRB of record)** — for multi-site research, one IRB reviews on behalf of all sites (45 CFR 46.114 + NIH policy); other sites cede their review to it.
[^smart]: **SMART IRB** — a national master reliance agreement and platform that lets institutions cede IRB review to a single reviewing IRB without negotiating a bespoke agreement each time.
[^onefl]: **OneFlorida+** — a Florida clinical research consortium / data network whose member sites can rely on a shared IRB infrastructure.
[^hrpp]: **HRPP (Human Research Protection Program)** — the institution-wide office that houses the IRB and issues determination letters; at UF, accessed via the myIRB system.
[^citi]: **CITI training** — the standard online Human Subjects Research / Good Clinical Practice training program required of study personnel; hosted by the IRB-of-record's institution (here, UF).
[^compound]: **503A / 503B compounding** — sections of the Food, Drug & Cosmetic Act governing pharmacy compounding: 503A is patient-specific compounding by a pharmacy; 503B is an FDA-registered outsourcing facility. Compounded drugs are **not** FDA-approved; mass compounding of a drug is generally permitted only during an official shortage.
[^cpic]: **CPIC (Clinical Pharmacogenetics Implementation Consortium)** — publishes peer-reviewed, actionable gene–drug dosing guidelines. There is **no** CPIC guideline for GLP-1 RAs, so any genotype-based response prediction for them is research-grade, not clinically actionable.
[^clia]: **CLIA-certified** — the federal certification required to return clinical lab results to patients; the research pipeline lacks it, so its genotype/response calls cannot be returned as clinical results.
[^ror]: **ROR (return of results)** — the policy on whether, and how, individual research findings are given back to participants; must be stated up front.
[^acmgsf]: **ACMG SF (Secondary Findings)** — the ACMG list of clinically actionable genes (the engine's default ACMG81 panel) whose pathogenic findings the genomic side of the study may encounter.
[^gina]: **GINA (Genetic Information Nondiscrimination Act)** — U.S. law barring genetic discrimination in health insurance and employment; it does **not** cover life, disability, or long-term-care insurance — a gap to disclose in consent.
