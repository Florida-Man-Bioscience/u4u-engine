# U4U — Roadmap

> This document tracks what gets built, in what order, and who owns it. Update it when phases complete or priorities change. If a task is not listed here, it is not a current priority.

---

## Phase 1 — Get a URL

**Goal:** A file can be uploaded to a real URL and results come back.

**Done when:** `POST /analyze` at a public URL accepts a 23andMe file and returns annotated JSON.

| Task | Owner | Blocks |
|------|-------|--------|
| FastAPI endpoint: POST /analyze, accepts file upload, calls run_pipeline(), returns JSON | Hampton | Everything |
| Docker container for engine + API | Hampton | Deployment |
| K8s deployment to Hampton's cluster | Hampton | Public URL |
| Domain registered and pointed at cluster | Curtis | Hampton cannot deploy publicly without it |
| Branded Google Workspace email set up | Jeran | Any public-facing communication |

---

## Phase 2 — Build the product

**Goal:** A working web interface with real condition content for at least 4 genes.

**Done when:** A user uploads a file, sees a styled results page, and at least BRCA1, TP53, LDLR, and RYR1 show human-written condition descriptions.

| Task | Owner | Blocks |
|------|-------|--------|
| Postgres schema: annotation_cache and condition_library tables | Hampton | Caching, condition lookup |
| Annotation cache: check Postgres before hitting external APIs | Hampton | Performance |
| Condition library merge: condition_key lookup in API layer before returning results | Hampton | Condition content in results |
| Condition library rows for BRCA1, TP53, LDLR, RYR1 (4 rows minimum) | Sasank | Rocky's design, Tom's results page |
| Results card design: one Critical card and one Carrier card using Sasank's real text | Rocky | Tom's implementation |
| Upload screen: file drop, consent checkbox, panel selector | Tom | User flow |
| Processing screen: progress bar wired to progress_callback | Tom | User flow |
| Results screen scaffolding: card list, filter chips, header count | Tom | Can complete after Rocky's design |
| Privacy policy draft: what data leaves the system, when, to whom | Cane | Launch |

---

## Phase 3 — Ship

**Goal:** Product is live, condition library is complete for all ACMG SF genes, security audit passes, first users are in.

**Done when:** 10 beta users have uploaded real files and seen real results.

| Task | Owner | Blocks |
|------|-------|--------|
| All 81 ACMG SF v3.2 condition library rows complete | Sasank | Shipping |
| Full results page: all card states, expanded cards, sources section | Tom | Shipping |
| Carrier card layout and VUS card layout | Tom + Rocky | Shipping |
| Security audit: Nmap scan on cluster, consent gate, data flow | Cane | Launch |
| CI/CD: main push triggers Docker build and auto-deploy | Hampton | Safe deploys |
| 10 named beta users committed | Jeran | Soft launch |
| Incorporate 40 Minute Bioscience LLC | Curtis | First paying customer |

---

## Phase 4 — Acquire users

**Goal:** Validate free-to-paid conversion. 100+ uploads, 10+ user interviews, subscription interest measured.

**Done when:** At least 20% of users who see the subscription CTA click through to learn more (EXP-04 success threshold).

| Task | Owner | Blocks |
|------|-------|--------|
| Landing page: hero headline, three value props, waitlist email capture | Tom + Rocky | Organic conversion |
| Reddit posts: r/23andme, r/genetics, r/Biohackers, r/QuantifiedSelf | Jeran | Initial traffic |
| Weekly newsletter: one genomics finding per issue, plain English, CTA to upload | Jeran | Audience building |
| User interviews: 10 completed, 3+ users describe a specific insight they got | Jeran | Knowing what to build next |
| Waitlist-to-user email flow | Hampton | Conversion |
| "Get notified when your interpretation updates" subscription CTA on results page | Curtis + Tom | Revenue hypothesis test |

---

## V2 — Research tracking (subscription feature)

Not started. Requires Phase 1–3 complete first. This is the subscription revenue driver.

| Task | Owner |
|------|-------|
| User accounts (Authelia, registration, login) | Hampton |
| Postgres user_variants table (stored profiles per user) | Hampton |
| Nightly PubMed job: query NCBI Entrez by gene symbols from stored profiles | Curtis |
| LLM summarization of returned papers | Curtis |
| Postgres research_updates table: LLM summaries linked to user_variant records | Hampton |
| Research feed UI: new section on results page, one entry per relevant paper | Tom |
| Email notification when new relevant papers publish | Hampton |
| Subscription paywall: free users see 1 preview entry, paid users get full feed | Tom + Hampton |

---

## Experiments

These are the hypotheses being tested. Each has a defined success threshold.

| ID | Hypothesis | Method | Success threshold | Status |
|----|-----------|--------|-------------------|--------|
| EXP-01 | Tier 1 users sign up when they understand the value prop | Reddit post in r/23andme + waitlist link | 50 signups in 72 hours | Not started — blocked on landing page |
| EXP-02 | Non-experts understand one result card without prompting | Show 5 non-biologists one card, ask them to explain it back | 4 of 5 understand it | Blocked — needs condition library content |
| EXP-03 | Users upload a real file to a free tool when privacy is clearly explained | Launch publicly, track upload completion rate | 30% completion | Blocked — needs deployment |
| EXP-04 | Users will pay for interpretation that updates | "Get notified when your interpretation updates" CTA on results page | 20% click-through | Phase 2+ |

---

## Open decisions

These must be resolved before work that depends on them begins.

| Decision | Needed by | Owner |
|----------|-----------|-------|
| Domain / URL | Phase 1 | Curtis + Hampton |
| Subscription price | Phase 4 | Curtis |
| Consumer brand name | Phase 4 | Jeran |
| VUS exact display language | Phase 3 | Sasank |
| Gene scope beyond ACMG SF 81 for V1 | Phase 3 | Sasank + Curtis |
| Pharmacogenomics: V1 or V2? | Phase 3 | Curtis + Sasank |
| LLC incorporation | Phase 3 | Curtis |
| Regulatory position (information platform vs. medical device) | Before first paying customer | Curtis + legal counsel |

---

*Curtis owns this document. Update it when decisions are made or phases complete.*
