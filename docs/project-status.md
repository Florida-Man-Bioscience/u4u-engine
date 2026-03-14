# Project Status

---

## MVP scope

VCF upload → annotation engine → interactive dashboard. No genome storage. Email capture for future research updates. Target: 4 weeks.

---

## What works

- Parses VCF / `.vcf.gz` (MVP primary), 23andMe `.txt`, CSV, rsID lists
- 10-step pipeline: validate → parse → quality filter → whitelist → rsID resolution → deduplicate → annotate → score → summarize → sort
- Annotates against ClinVar, gnomAD, Ensembl VEP (retry + fallback)
- Returns plain-English headline, consequence, rarity, action hint per variant
- FastAPI job queue (`api.py`) — `POST /analyze` → 202 + `job_id`, `GET /jobs/:id` for polling
- Postgres schema (`db/schema.sql`) — jobs, results, condition_library, annotation_cache
- CI on push via GitHub Actions (Python 3.11 and 3.12)

---

## Repo

```
engine/         core pipeline
  annotators/   ClinVar, gnomAD, VEP, MyVariant modules
  pipeline.py   run_pipeline() entry point
  scoring.py    scoring + tier logic
  summary.py    plain-English text generation
api.py          FastAPI job queue
db/schema.sql   Postgres schema
tests/          pipeline tests
data/           rsID filter files
docs/           documentation
.github/        CI, issue templates, PR template
```

---

## What doesn't exist

| Area | Status |
|------|--------|
| Docker build + K8s deployment | Not deployed |
| Postgres instance running | Schema exists — not wired |
| Condition library content | 81 ACMG SF rows needed |
| Frontend | Not built — spec in `docs/frontend.md` |
| Domain + DNS | Not registered |
| Security audit | Not started — plan in `U4U_Cybersecurity_Execution_Plan.docx` |

---

## UI spec

Full spec in `docs/frontend.md`.

Three screens: Upload → Processing → Results.

Results screen is a **prioritized findings report** — single column, expandable rows with a colored left border (tier color). Two sections: "Needs Attention" (critical + high) and "For Your Records" (medium + low + carrier, collapsed by default).

**Tier visual treatment:**

| `tier` | Border | Emoji |
|--------|--------|-------|
| critical | red | 🔴 |
| high | orange | 🟠 |
| medium | yellow | 🟡 |
| low | green | 🟢 |
| carrier | blue | 🔵 |

**Error states:**

| State | Behavior |
|-------|----------|
| File too large / unsupported format | Inline error before submit |
| Invalid VCF header | Error screen after submit |
| All variants filtered | Results page with explanation |
| Zero ACMG findings | Message, not blank |
| Network error | Error screen with retry |
| Partial results | Show succeeded, note how many failed |

---

## Not in V1

User accounts, saved results, email delivery, pharmacogenomics, research tracking, PRS, mobile, API access for external developers.

Roadmap: `docs/roadmap.md`
