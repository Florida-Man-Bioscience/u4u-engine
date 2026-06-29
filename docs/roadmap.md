# Roadmap

---

## MVP[^mvp] target: 4 weeks from go

MVP is done when a user can upload a VCF[^vcf] file at a public URL and see an interactive results view of interpreted variants. No genome stored. Email capture for research updates.

---

## Phase 1 — Get a URL

**Done when:** `POST /analyze` at a public URL accepts a VCF file and returns annotated JSON.

- Deploy `api.py` to K8s[^k8s]: `docker compose up --build`
- Register domain, point DNS[^dns] at cluster
- Google Workspace[^workspace] email setup

---

## Phase 2 — Build the product

**Done when:** upload produces a styled results page with real condition content for 4 genes.

- Wire Postgres: `psql $DATABASE_URL -f db/schema.sql`
- Condition library: BRCA1, TP53, LDLR, RYR1[^genes] rows
- Results screen design (1 Critical row + 1 Carrier row using real text)
- Upload + processing screens
- Results screen build

---

## Phase 3 — Ship

**Done when:** 10 beta users have uploaded real files and seen real results.

- All 81 ACMG SF[^acmgsf] condition library rows
- Full results screen (all row states)
- Security audit + pre-deploy checklist
- CI/CD[^cicd]: main push triggers auto-deploy
- 10 named beta users committed

---

## Phase 4 — Acquire users

**Done when:** 100+ uploads, 10 user interviews, subscription CTA[^cta] at 20%+ click-through[^clickthrough].

- Landing page: hero, value props[^valueprop], waitlist
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
- Nightly PubMed[^pubmed] job + LLM[^llm] summarization
- Research feed UI
- Subscription paywall[^paywall]

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
- VUS[^vus] display language
- Gene scope beyond ACMG SF 81
- LLC[^llc] incorporation
- Regulatory position (info platform vs. medical device[^meddevice])

---

## Footnotes

[^mvp]: **MVP (Minimum Viable Product)** — the smallest release that delivers core value and can be tested with real users.
[^vcf]: **VCF (Variant Call Format)** — the standard text format for storing genetic variants; the primary upload type.
[^k8s]: **K8s (Kubernetes)** — a container-orchestration platform for deploying and scaling the service across a cluster.
[^dns]: **DNS (Domain Name System)** — the system that maps a domain name to a server's IP address; "pointing DNS at the cluster" routes the domain to the deployment.
[^workspace]: **Google Workspace** — Google's hosted email and productivity suite (custom-domain Gmail, Calendar, Drive).
[^genes]: **BRCA1, TP53, LDLR, RYR1** — the four launch genes: hereditary breast/ovarian cancer, Li-Fraumeni syndrome, familial hypercholesterolemia, and malignant hyperthermia, respectively.
[^acmgsf]: **ACMG SF** — the American College of Medical Genetics "Secondary Findings" gene list (v3.2, 81 genes) recommended for reporting actionable pathogenic findings.
[^cicd]: **CI/CD (Continuous Integration / Continuous Deployment)** — automation that builds and tests every code push and then deploys passing changes without manual steps.
[^cta]: **CTA (Call To Action)** — a prompt urging the user to act (e.g. a "Get notified" or "Subscribe" button), and the unit conversion is measured against.
[^clickthrough]: **Click-through rate** — the fraction of people who see an element (e.g. the CTA) and click it; a standard conversion metric.
[^valueprop]: **Value prop (value proposition)** — the concise statement of the benefit a product offers and why a user should choose it.
[^pubmed]: **PubMed** — the U.S. National Library of Medicine's database of biomedical literature; a nightly job would scan it for new papers relevant to a user's variants.
[^llm]: **LLM (Large Language Model)** — an AI text model (e.g. Claude) used here to summarize research papers into plain-language updates.
[^paywall]: **Paywall** — a gate restricting a feature to paying subscribers.
[^vus]: **VUS (Variant of Uncertain Significance)** — a variant whose evidence is insufficient to classify as pathogenic or benign; how to display these to consumers is an open decision.
[^llc]: **LLC (Limited Liability Company)** — a U.S. business entity that limits the owners' personal liability; "incorporation" is the act of legally forming it.
[^meddevice]: **Medical device** — a regulatory classification (FDA-governed) for products intended to diagnose or treat. Being a "medical device" triggers far heavier oversight than an informational platform; which side of that line the product sits on is an open decision.
