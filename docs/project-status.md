# Project Status

---

## What exists and works today

**Annotation pipeline (`engine/`)**
- Parses 23andMe `.txt`, VCF, `.vcf.gz`, CSV, and rsID list files
- 10-step pipeline: validate, parse, quality filter, whitelist filter, rsID resolution, deduplicate, annotate, score, summarize, sort
- Annotates against ClinVar, gnomAD, Ensembl VEP (with retry and fallback)
- Scores and tiers each variant (Critical / High / Medium / Low / Carrier)
- Returns plain-English headline, consequence, rarity, action hint per variant

**Tests (`tests/`)**
- Parser tests, quality filter tests, deduplication tests, scoring tests
- CI runs on push and PR via GitHub Actions (Python 3.11 and 3.12)

**Documentation (`docs/`)**
- Architecture, pipeline spec, interpretation spec, integrations, this file

---

## Repo structure

```
engine/         core pipeline package
  annotators/   ClinVar, gnomAD, VEP, MyVariant modules
  pipeline.py   run_pipeline() entry point
  scoring.py    scoring and tier logic
  summary.py    plain-English text generation
tests/          pipeline tests
data/           rsID filter files (acmg81_rsids.txt, etc.)
docs/           system documentation
.github/        CI workflow, issue templates, PR template
```

---

## What does not exist yet

### Web API
- FastAPI wrapper around `run_pipeline()`
- `POST /analyze` endpoint accepting file upload
- Background worker (run engine in thread pool)
- Owner: Hampton

### Database
- Postgres schema and migrations
- Annotation cache (keyed by variant coordinates, TTL 30 days)
- Condition library table (loaded from Sasank's CSV at deploy time)
- Owner: Hampton

### Condition library content
- Schema exists in `docs/interpretation.md`
- 81 ACMG SF v3.2 genes need a complete row each before launch
- 4 rows needed immediately to unblock design: BRCA1, TP53, LDLR, RYR1
- Owner: Sasank

### Frontend
- Upload screen (file drop, consent checkbox, panel selector)
- Processing screen (progress bar wired to `progress_callback`)
- Results screen (cards, filter chips, expanded card states)
- Owner: Tom (implementation), Rocky (design)

### Infrastructure
- Docker container for engine + API
- K8s deployment on Hampton's cluster
- Domain registered and pointed at cluster
- CI/CD: push to main triggers Docker build and auto-deploy
- Owner: Hampton (deployment), Curtis (domain)

### Security and legal
- Privacy policy draft
- Consent gate language review
- Nmap scan and security audit on the cluster
- LLC incorporation (40 Minute Bioscience)
- Owner: Cane (audit, privacy policy), Curtis (LLC)

---

## Immediate blockers (in dependency order)

| Blocker | Who resolves it |
|---------|----------------|
| No deployed URL | Hampton builds FastAPI + Docker + K8s. Curtis registers domain. |
| No condition library content | Sasank writes 4 rows (BRCA1, TP53, LDLR, RYR1) to unblock design. |
| No branded email | Jeran sets up Google Workspace. |

---

## Team

| Person | Owns |
|--------|------|
| Curtis | Engine, docs, product, domain |
| Hampton | FastAPI, Postgres, Docker, K8s, CI/CD |
| Sasank | Condition library content, clinical interpretation review |
| Tom | Frontend (all three screens) |
| Rocky | Visual design, results card design |
| Jeran | Marketing, user acquisition, brand |
| Cane | Security audit, privacy policy, consent gate |

### What each person reads first

| Person | Read this |
|--------|-----------|
| Hampton | `docs/architecture.md`, `docs/pipeline.md` (FastAPI section), `docs/integrations.md` |
| Tom | `docs/architecture.md`, then build against UI specs below |
| Rocky | UI specs below, `docs/interpretation.md` (tiers and VUS section) |
| Sasank | `docs/interpretation.md` (condition library schema and all `[SASANK REVIEW]` sections) |
| Cane | `docs/integrations.md` (what user data leaves the system) |

---

## UI spec (for Tom and Rocky)

### Screen 1 — Upload
- Logo and tagline
- File drop area (23andMe .txt, .vcf, .vcf.gz, .csv accepted)
- File size limit: 100 MB
- Consent checkbox (required before submit)
- Panel selector (collapsed by default): ACMG SF v3.2 always on, pharmacogenomics and carrier screening optional
- Analyze button disabled until file selected and checkbox checked

### Screen 2 — Processing
- Progress bar
- Status label from `progress_callback(step, pct)`
- No navigation away without warning

### Screen 3 — Results
- Header: count and one-line summary
- Filter chips: 🔴 Critical, 🟠 High, 🟡 Medium/VUS, 🟢 Low, 🔵 Carrier with counts
- Default view: Critical and High shown; others toggled off
- One card per variant, score descending

**Card collapsed state:** emoji + tier badge, gene name, headline, condition name, ClinVar badge

**Card expanded state:** headline, consequence_plain, zygosity_plain, rarity_plain, clinvar_plain, action_hint, condition-specific action guidance (from condition library), source links (ClinVar, gnomAD, ACMG)

**Carrier card:** blue styling, "You appear to be a carrier" headline, carrier_note text, condition name, action_hint

**VUS card:** explicit "uncertain significance" header, consequence_plain, rarity_plain, frequency_derived_label

**Disclaimer footer (persistent):** "This information is not medical advice. Findings are sourced from ClinVar, gnomAD, and Ensembl VEP. Discuss significant findings with a qualified healthcare provider."

### Error states the UI must handle

| State | Behavior |
|-------|----------|
| File too large | Inline error before submit |
| Unsupported format | Inline error before submit |
| Invalid VCF header | Error screen after submit |
| All variants filtered out | Results screen with explanation, not blank |
| Zero ACMG findings | Show message, not blank screen |
| Network error during annotation | Graceful error screen with retry |
| Partial results | Show succeeded results, note how many failed |
| Pipeline timeout | Error screen with retry |

---

## Not in V1

- User accounts or saved results
- Email delivery of results
- Pharmacogenomics results (engine infrastructure exists, content not ready)
- Research tracking / subscription features
- PRS (polygenic risk scores)
- Mobile app
- API access for external developers
- Sharing results with a provider

Roadmap: `docs/roadmap.md`
