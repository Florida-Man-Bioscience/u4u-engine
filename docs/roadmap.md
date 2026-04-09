# Roadmap

---

## MVP target: 4 weeks from go

MVP is done when a user can upload a VCF file at a public URL and see an interactive results view of interpreted variants. No genome stored. Email capture for research updates.

---

## Phase 1 — Get a URL

**Done when:** `POST /analyze` at a public URL accepts a VCF file and returns annotated JSON.

- Deploy `api.py` to K8s: `docker compose up --build`
- Register domain, point DNS at cluster
- Google Workspace email setup

---

## Phase 2 — Build the product

**Done when:** upload produces a styled results page with real condition content for 4 genes.

- Wire Postgres: `psql $DATABASE_URL -f db/schema.sql`
- Condition library: BRCA1, TP53, LDLR, RYR1 rows
- Results screen design (1 Critical row + 1 Carrier row using real text)
- Upload + processing screens
- Results screen build

---

## Phase 3 — Ship

**Done when:** 10 beta users have uploaded real files and seen real results.

- All 81 ACMG SF condition library rows
- Full results screen (all row states)
- Security audit + pre-deploy checklist
- CI/CD: main push triggers auto-deploy
- 10 named beta users committed

---

## Phase 4 — Acquire users

**Done when:** 100+ uploads, 10 user interviews, subscription CTA at 20%+ click-through.

- Landing page: hero, value props, waitlist
- Community outreach (r/23andme, r/genetics, r/Biohackers)
- Weekly newsletter (plain-English genomics finding + CTA)
- 10 user interviews completed
- Waitlist-to-user email flow
- Subscription CTA on results page

---

## V2 — Research tracking (subscription)

Not started. Requires Phases 1–3 complete.

- User accounts
- `user_variants` table (stored profiles)
- Nightly PubMed job + LLM summarization
- Research feed UI
- Subscription paywall

---

## Experiments

| ID | Hypothesis | Method | Success threshold |
|----|-----------|--------|-------------------|
| EXP-01 | Users sign up when they understand the value prop | Community post + waitlist link | 50 signups in 72h |
| EXP-02 | Non-experts understand one result row | Show 5 people, ask them to explain it back | 4 of 5 understand |
| EXP-03 | Users upload to a free tool when privacy is explained | Track upload completion | 30% completion |
| EXP-04 | Users pay for updating interpretation | "Get notified" CTA on results page | 20% click-through |

---

## Open decisions

- Domain / URL
- Subscription price
- Consumer brand name
- VUS display language
- Gene scope beyond ACMG SF 81
- LLC incorporation
- Regulatory position (info platform vs. medical device)
