# Enrollment Strategy — Prospective Observational Clinic-Partnership Study (Lane C / Tier C)

**Document type:** Clinical operations / recruitment strategy (companion to the IRB package and SAP)  
**Study:** Prospective, multi-site, **observational** cohort validating genomic peptide-response predictions against real-world biomarker trajectories  
**Sponsor (ops):** Florida Man Bioscience (FMB)  
**IRB of record:** University of Florida (sIRB) — see `docs/irb-plan.md`, `docs/irb-setup-plan.md`  
**Status:** DRAFT v0.1 (2026-08-13) — **not an IRB-approved recruitment plan.** Materials that touch participants must be IRB-stamped before use. **Not yet recruiting.**  
**Ops enrollment target:** **N ≈ 1,000 consented / enrolled** (working headcount).  
**Statistical N:** still **PLACEHOLDER** in `docs/validation/prediction-efficacy-audit/sap-prediction-clinical-validity.md` §6 — biostatistician must lock primary-completer N before claiming powered primary analysis.

---

## 0. Relationship to other documents

| Document | Role |
|---|---|
| `docs/clinical-validation-plan.md` | Science / validation pillars, endpoints, hazards |
| `docs/irb-plan.md` | Lane A/B/C IRB pathways; Lane C checklist |
| `docs/irb-plan-glp1.md` | GLP-1–forward observational variant of Lane C |
| `docs/irb-setup-plan.md` | UF sIRB mechanics, reliance, training |
| `docs/irb-determination-request.md` | Stage 1 NHSR/Exempt only (no enrollment) |
| `docs/mccormack-briefing.md` | Short Stage 1 / Stage 2 summary for consultation |
| `docs/validation/prediction-efficacy-audit/` (PEAP) | Predictor freeze, SAP, Gate C enrollment hold criteria |
| `docs/validation/prediction-efficacy-audit/sap-prediction-clinical-validity.md` | Analysis population, endpoints, sample-size placeholder |
| Frontend `/study` | Public informational page — **not a solicitation to enroll** until IRB opens recruitment |

This document answers: **how we operationally reach ~1,000 enrolled participants** under the observational design already fixed in the IRB plans.

---

## 1. Non-negotiable design constraints (enrollment implications)

These are fixed by the IRB posture. Enrollment strategy **must not** violate them.

1. **Observational only.** FMB does **not** prescribe, supply, dose, or direct any peptide (including unapproved research peptides). Therapy is **treatment-as-usual** by the participant’s own clinician.  
2. **Recruit from patients already on therapy** at partner clinics — not “start peptides with us.”  
3. **No coercion.** Clinic staff must not pressure enrollment; declining must not affect care. No recruitment of investigators’ own students, employees, or subordinates.  
4. **No clinical return of research pipeline results** by default (research-grade, not CLIA). Identifiable return-of-results would escalate review.  
5. **PHI only under consent + HIPAA authorization + BAA/DUA** with each clinic.  
6. **PEAP Gate C:** do **not** open enrollment claiming a **locked primary predictor** until PEAP readiness criteria are met or formally de-scoped (`docs/validation/prediction-efficacy-audit/PRETRIAL-READINESS-REPORT.md`). Process pilots and systems dry-runs may proceed under separate, clearly labeled scopes when IRB allows.  
7. **Public product traffic** (PeptOdyssey) is a **side channel** (interest registry / clinic leads), not the main enrollment engine.

---

## 2. Definitions (funnel stages)

| Stage | Definition | Counts toward “1,000”? |
|---|---|---|
| **Screened** | Clinic identifies adult on protocol-listed therapy; research intro offered | No |
| **Eligible** | Meets inclusion/exclusion; baseline data obtainable | No |
| **Enrolled** | Signed informed consent + HIPAA authorization; study ID assigned | **Yes (ops target)** |
| **Analyzable T0** | Enrolled + genetics path complete (or pre-allowed no-genetics path) + baseline primary endpoint(s) | Primary analysis entry |
| **Primary completer** | T0 + primary outcome at \(t^*\) (e.g. week-12 weight ±14 days for GLP-1 track per SAP) | Powered primary N |

**Planning attrition (ops assumptions — not SAP):**

| Transition | Assumed yield |
|---|---|
| Screen → eligible | 40–70% |
| Eligible → enrolled | 30–50% |
| Enrolled → analyzable T0 | 70–85% |
| T0 → primary completer | 70–80% (≈20–30% loss to follow-up, aligned with SAP suggestion) |

### 2.1 Back-solve for 1,000 enrolled

| Eligible→enroll | Eligible needed | Screen→eligible 50% | Screens needed |
|---|---|---|---|
| 40% | ~2,500 | 50% | **~5,000** |
| 50% | ~2,000 | 50% | **~4,000** |

**Implication:** 1,000 enrolled is a **site-capacity problem**, not a consumer-ad problem.

If the biostatistician later requires ~700 GLP-1 primary completers, plan either higher enrolled N in that stratum or lower LTFU via visit-aligned data capture — do not silently equate “1,000 enrolled” with “1,000 completers.”

---

## 3. Strategic principle: sites first

| Channel | Role | Expected share of enrolled |
|---|---|---|
| **In-clinic at partner sites** | Primary | **70–85%** |
| Clinic CRM / authorized follow-up | Secondary | **10–20%** |
| PeptOdyssey `/study` interest registry → site routing | Lead-gen / waitlist | **≤5–10%** of enrolled; higher share of **site leads** |

**Do not** run mass DTC ads that imply the study provides peptides, optimizes dosing, or returns clinical genetic advice.

---

## 4. Cohort architecture (how 1,000 is composed)

Total N is a **platform cohort**. Primary powered analyses may be stratum-specific (especially GLP-1).

| Tier | Population | Ops target (enrolled) | Analysis posture |
|---|---|---|---|
| **A — GLP-1 backbone** | Semaglutide, tirzepatide, liraglutide (branded or compounded — **capture source**) | **500–600** (50–60%) | Primary calibration path (weight → HbA1c hierarchical per SAP) |
| **B — GH-axis / metabolic adjacent** | e.g. tesamorelin, GH-secretagogue class as prescribed | **200–250** (20–25%) | Secondary / exploratory per protocol |
| **C — MSK / recovery peptides** | e.g. BPC-157, TB-500 as prescribed | **150–200** (15–20%) | Exploratory; **cap** so they do not dominate ops |
| **D — Other / multi-peptide** | Remainder of clinic panel | Remainder to 1,000 | Registry / exploratory |

**Rationale:** GLP-1 volume and endpoint clarity maximize completer yield; research peptides remain observational and scientifically harder — useful for breadth, not for carrying the primary claim alone.

**Compounded vs branded (GLP-1):** record product source, lot/COA availability if clinic holds it, and dose. Product-identity uncertainty is a **covariate / sensitivity factor**, not a reason to exclude treatment-as-usual patients a priori (protocol may refine).

---

## 5. Site network design

### 5.1 Indicative productivity (steady state)

| Site type | Rough active volume | Enroll/month (after ramp) |
|---|---|---|
| High-volume weight / endo / GLP-1 clinic | High starts/month | **8–25** |
| Mid boutique peptide / longevity clinic | Moderate panel | **3–10** |
| Low / new partnership | Low | **0–3** |

### 5.2 Capacity for 1,000 in ~12 months open enrollment

Target pace ≈ **83 enrolled/month** after ramp, which typically requires:

- **6–10** high-volume GLP-1–capable sites, **or**  
- **4–5** high-volume + **10–15** boutique sites, **or**  
- a longer (**~18 month**) accrual window with a thinner network.

### 5.3 Activation waves

| Wave | Sites | Purpose |
|---|---|---|
| **Wave 0 (pilot)** | **2–3** high-trust clinics | Process proof: BAA, eConsent, chart pull, genetics upload, dashboard |
| **Wave 1** | **+5–7** | Reach ~40–60 enroll/month |
| **Wave 2** | **+8–12** | Reach ~80–100/month; geography / case-mix diversity |
| **Reserve** | ≥5 identified | Replace non-performing sites |

**Site kill rule:** &lt;2 enrolled in 60 days post-activation (after training complete) → retrain once or close.

### 5.4 Site hit-list fields (maintain as living appendix / spreadsheet)

For each candidate site track at minimum:

- Legal name, location, NPI/group  
- Primary contact (clinician + coordinator)  
- Monthly peptide / GLP-1 starts (estimate)  
- EHR / lab workflow notes  
- Wave (0/1/2/reserve)  
- BAA/DUA status, reliance status  
- IRB stamp of local recruitment materials  
- Activation date, enrolled MTD, T0 completeness %  
- Notes (compounded GLP-1 mix, research-peptide mix)

---

## 6. Phased enrollment plan

### 6.1 Phase G0 — Gates before participant contact

| ID | Gate | Done when |
|---|---|---|
| G0.1 | Protocol + I/E + endpoints; SAP sample size path agreed (ops N=1000 vs powered completer N distinguished) | Versioned protocol + SAP note |
| G0.2 | UF sIRB approval (expedited Lane/Tier C) | Approval letter |
| G0.3 | COI management plan (FMB commercial interest + UF Innovate patent context) | Institutional COI + IRB accepted |
| G0.4 | BAA/DUA executed for each activating clinic | Signed agreements on file |
| G0.5 | eConsent + HIPAA auth live; recruitment scripts IRB-stamped | Production paths + stamp dates |
| G0.6 | Data path dry-run: clinic labs → tracking; genetics → analysis job; **no clinical ROR** | Signed dry-run log |
| G0.7 | CITI / IRB 803 (and HIPAA PRV800 as required) for all study personnel | Training matrix |
| G0.8 | Enrollment dashboard (see §8) | Weekly report running |
| G0.9 | PEAP Gate C status explicit: HOLD vs conditional open vs research-ops-only pilot | Written decision |

**Do not** change `/study` from “not yet recruiting” to open enrollment until G0.2 + G0.5.

### 6.2 Phase G1 — Pilot (first 50–100 enrolled, ~8–12 weeks post-FPI)

- Wave 0 sites only.  
- Optimize consent length, missing labs, genetics friction.  
- Freeze SOPs after pilot.  
- **Success criteria:** ≥70% enrolled reach analyzable T0; manageable query rate; **zero** deviations of type “study directed therapy.”

### 6.3 Phase G2 — Scale to ~500

- Activate Wave 1.  
- Preferential focus on **Tier A (GLP-1)** until primary stratum is on pace.  
- Monthly site scorecards.

### 6.4 Phase G3 — Fill to 1,000 + diversity

- Wave 2; top up under-enrolling strata only if scientifically useful.  
- Monitor age, sex, race/ethnicity, BMI, branded vs compounded, geography.  
- Soft-close slow exploratory strata rather than relaxing I/E.

### 6.5 Phase G4 — LPLV and lock

- Complete primary outcome windows.  
- Database lock per SAP; **no model refit for locked primary** (PEAP/SAP).  
- Descriptive enrollment dashboards only for interims (no efficacy interim).

---

## 7. Recruitment methods (detail)

### 7.1 In-clinic (primary)

1. Treating clinician or trained coordinator identifies patient **already** on a protocol-listed therapy.  
2. IRB-approved brief script: observational research; optional; no change in care; research-only genetics/predictions.  
3. Tablet/QR → eConsent + HIPAA authorization.  
4. Align baseline packet with clinically ordered visits/labs when possible (minimize extra burden).  
5. Genetics: supported consumer file upload and/or protocol-allowed research kit pathway.

**Site payment:** fair reimbursement for coordinator time, start-up, and chart abstraction — structured to avoid undue influence / finder’s-fee coercion. Exact fee schedule is a budget + IRB/HRPP matter.

### 7.2 Authorized clinic follow-up

Email/SMS only via clinic-authorized channels and IRB-approved text, to patients already in care on listed therapies who missed the in-visit pitch.

### 7.3 Interest registry (PeptOdyssey `/study`)

- **Pre-approval:** “Register interest” only; banner remains **not recruiting**.  
- **Post-approval:** route by geography / therapy class to open sites; do not enroll purely remote without protocol language for identity, eligibility, and lab provenance.  
- Screen out people **not** already prescribed therapy (or route them nowhere except educational content).

### 7.4 Prohibited / high-risk tactics

- Ads promising personalized peptide prescriptions or clinical genetic diagnoses from the study.  
- Conditional care (“enroll to stay on therapy”).  
- Recruiting UF students/staff subordinate to investigators.  
- Participant payments that effectively subsidize drug purchase.  
- Any suggestion FMB supplies or directs unapproved peptides.

---

## 8. Minimum participant packet

| Element | Required for |
|---|---|
| Consent + HIPAA authorization | Enrolled |
| Demographics | T0 |
| Therapy record (agent, dose, route, start date, branded vs compounded, prescriber clinic) | T0 / analysis |
| Baseline primary endpoint(s) from clinic record (e.g. weight; HbA1c as applicable) | Analyzable T0 |
| Genome file or pre-specified alternate genetics path | Analyzable T0 (if genetics required for primary) |
| Longitudinal clinic labs/visits already occurring | Completer path |
| HealthKit (optional) | Enrichment only unless SAP elevates it — PEAP notes proxy exclusion for some analyses |

**Genetics friction is a top failure mode.** Target &lt;10 minutes for supported file types; provide a help path; track genetics completion % weekly.

---

## 9. Metrics, cadence, and pace gates

### 9.1 Dashboard KPIs (minimum)

- Counts: screened, eligible, enrolled, analyzable T0, week-4/12 completers  
- Breakdown: **site**, **peptide tier**, **branded vs compounded**  
- Cycle times: screen→consent, consent→T0, T0→week-12  
- Genetics success rate; baseline missingness (weight, HbA1c)  
- Decline rate by site (≈0% declines = coercion red flag)  
- Protocol deviations; AE observations (observe/record only)

### 9.2 Weekly 30-minute ops standup

1. Enrolled this week vs target pace.  
2. Bottom three sites → action.  
3. T0 incomplete &gt;14 days → coordinator chase.  
4. Deviations / AE observation log.  
5. BAA and activation pipeline.

### 9.3 Pace gate

If enrollment is **&lt;50% of target pace for two consecutive months** after Wave 1 is fully active → add sites or extend timeline. **Do not** loosen eligibility solely to hit headcount.

---

## 10. Timeline sketch (illustrative)

| Window | Milestone |
|---|---|
| M0–M2 | Protocol/SAP distinction, COI, eConsent build, first BAAs, UF submission |
| M2–M4 | Approval; Wave 0 initiation; **FPI** |
| M4–M6 | Pilot 50–100; SOP freeze; Wave 1 on |
| M6–M14 | Scale; pass ~500 enrolled |
| M14–M18 | Fill toward 1,000; Wave 2; diversity top-up |
| M18–M21 | Complete primary follow-up windows |
| M21–M24 | Lock and primary analysis |

Faster accrual requires **pre-contracted high-volume GLP-1 sites** before approval.

---

## 11. Budget levers that move enrollment

(Enrollment-critical lines — not a full trial budget.)

| Line | Why |
|---|---|
| Site start-up + per-patient coordinator fees | Primary throughput driver |
| Central study coordinator (part- or full-time) | Multi-site 1,000 without this stalls |
| eConsent + data systems (EDC or study-qualified tracking stack) | Throughput + audit trail |
| Genetics help desk / optional kit (if IRB-allowed) | T0 completeness |
| Remote site training | Activation speed |
| eClinical / computer infrastructure | Mostly fixed; see ops notes — usually **far smaller** than site + coordinator costs for this design |

Indicative eClinical/computer band for ~1,000 observational enrollees (software + hosting + build, not site grants): often **~$80k–$400k** commercial mid-stack; lean/academic lower. Full “technology” as 5–15% of a multi-million program is a different budget frame.

---

## 12. Risk register (enrollment-specific)

| Risk | Mitigation |
|---|---|
| IRB / COI delay | Parallel COI + BAA drafting with protocol; don’t serialize unnecessarily |
| Clinics avoid “research peptide” association | Lead with **GLP-1 observational** track; research peptides as capped exploratory appendix |
| Product-identity noise (compounded) | Capture source; sensitivity analyses; do not over-claim |
| Low genetics completion | UX + support + optional kit path; pre-specify no-genetics secondary if allowed |
| Coercion at high-performing sites | Monitor decline rates; retrain/stop |
| Conflating ops N=1000 with powered N | Biostats lock completer N; report both |
| Opening enrollment before PEAP Gate C | Explicit written hold/conditional decision |
| Over-enrollment of exploratory tiers | Hard caps in dashboard |

---

## 13. Immediate next actions (ops checklist)

- [ ] Confirm with biostatistics: **ops target 1,000 enrolled** vs **primary completer N** (write into SAP §6).  
- [ ] Name **PI of record** + complete UF training matrix.  
- [ ] Build **20-site hit list** (GLP-1-heavy first).  
- [ ] One-page **clinic partnership** sheet (observational, no drug, fair site costs).  
- [ ] Finish G0 packet (protocol, consent, HIPAA, recruitment, AE observe-only, ROR=no clinical return, COI).  
- [ ] Keep `/study` honest: not recruiting until G0.2 + G0.5.  
- [ ] No mass DTC enrollment spend pre-IRB.

---

## 14. One-line strategy

**Contract a GLP-1–heavy clinic network, clear UF expedited IRB and BAAs, pilot ~100 clean packets, then scale with site capacity and a central coordinator to ~1,000 consented participants — using PeptOdyssey public traffic only as a side door for interest and site leads.**

---

## 15. Document control

| Version | Date | Summary |
|---|---|---|
| 0.1 | 2026-08-13 | Initial enrollment strategy; ops target N≈1000; clinic-first funnel; cross-links to IRB/PEAP/SAP |

**Owners (to assign):** Study coordinator / clinical ops lead; PI; biostatistician (N lock); FMB partnerships (site BAAs).

**Not legal or regulatory advice.** UF HRPP/IRB and counsel govern human-subjects conduct.
