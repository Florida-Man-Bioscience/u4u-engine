# Roadmap

---

## MVP target: 4 weeks from go

MVP is done when a user can upload a VCF file at a public URL and see an interactive dashboard of interpreted variants. No genome stored. Email capture for research updates.

**MVP priority order:**
1. API wrapper — FastAPI `POST /analyze` wrapping `run_pipeline()`
2. Genome upload — file drop, VCF validation, size limit
3. Annotation cache — Postgres table to avoid repeat API calls on same variants
4. UI dashboard — scored variant cards, filter chips, expanded card state
5. Report generation — downloadable summary of findings
6. Deploy — Docker + K8s, domain pointed, CI/CD on main push

---

## Next steps (do these now)

1. **Hampton** — share a timeline estimate for Phase 1 (FastAPI + Docker + K8s); every other person's Phase 2 work is sequenced against this date
2. **Sasank** — commit to a delivery date for 4 condition library rows (BRCA1, TP53, LDLR, RYR1); Rocky's card design and Tom's results screen both hard-block on this
3. **Jeran** — identify 10 specific people (name + contact) who have a 23andMe or Ancestry file and are willing to be beta users; recruit now so testers are waiting when Phase 3 ships

---

## Phase 1 — Get a URL

**Done when:** `POST /analyze` at a public URL accepts a 23andMe file and returns annotated JSON.

| Task | Owner |
|------|-------|
| FastAPI: `POST /analyze`, calls `run_pipeline()`, returns JSON | Hampton |
| Dockerfile for engine + API | Hampton |
| K8s deployment | Hampton |
| Register domain, point DNS at cluster | Curtis |
| Google Workspace email | Jeran |

---

## Phase 2 — Build the product

**Done when:** upload produces a styled results page with real condition content for 4 genes.

| Task | Owner |
|------|-------|
| Postgres: `annotation_cache` + `condition_library` tables | Hampton |
| Condition library: BRCA1, TP53, LDLR, RYR1 rows | Sasank |
| Results card design (1 Critical + 1 Carrier using real text) | Rocky |
| Upload + processing screens | Tom |
| Results screen scaffolding | Tom |
| Privacy policy draft | Cane |

---

## Phase 3 — Ship

**Done when:** 10 beta users have uploaded real files and seen real results.

| Task | Owner |
|------|-------|
| All 81 ACMG SF condition library rows | Sasank |
| Full results page (all card states) | Tom |
| Security audit + Nmap scan | Cane |
| CI/CD: main push triggers auto-deploy | Hampton |
| 10 named beta users committed | Jeran |
| Incorporate 40 Minute Bioscience LLC | Curtis |

---

## Phase 4 — Acquire users

**Done when:** 100+ uploads, 10 user interviews, subscription CTA at 20%+ click-through.

| Task | Owner |
|------|-------|
| Landing page: hero, value props, waitlist | Tom + Rocky |
| Reddit posts: r/23andme, r/genetics, r/Biohackers | Jeran |
| Weekly newsletter (plain-English genomics finding + CTA) | Jeran |
| 10 user interviews completed | Jeran |
| Waitlist-to-user email flow | Hampton |
| Subscription CTA on results page | Curtis + Tom |

---

## V2 — Research tracking (subscription)

Not started. Requires Phases 1–3 complete.

| Task | Owner |
|------|-------|
| User accounts (Authelia) | Hampton |
| `user_variants` table (stored profiles) | Hampton |
| Nightly PubMed job + LLM summarization | Curtis |
| Research feed UI | Tom |
| Subscription paywall | Tom + Hampton |

---

## Experiments

| ID | Hypothesis | Method | Success threshold |
|----|-----------|--------|-------------------|
| EXP-01 | Users sign up when they understand the value prop | Reddit post + waitlist link | 50 signups in 72h |
| EXP-02 | Non-experts understand one result card | Show 5 people, ask them to explain it back | 4 of 5 understand |
| EXP-03 | Users upload to a free tool when privacy is explained | Track upload completion | 30% completion |
| EXP-04 | Users pay for updating interpretation | "Get notified" CTA on results page | 20% click-through |

---

## Open decisions

| Decision | Owner |
|----------|-------|
| Domain / URL | Curtis + Hampton |
| Subscription price | Curtis |
| Consumer brand name | Jeran |
| VUS display language | Sasank |
| Gene scope beyond ACMG SF 81 | Sasank + Curtis |
| LLC incorporation | Curtis |
| Regulatory position (info platform vs. medical device) | Curtis + legal |
