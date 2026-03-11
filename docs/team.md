# U4U — Team and Ownership

> **Status:** Active. Update this when roles or assignments change.

---

## The rule

One repo. One `docs/` folder. All decisions live in these markdown files. If it's not written here, it hasn't been decided.

When you build something, you build it against the spec documents in this folder. If the spec is wrong, you fix the spec — you do not silently deviate from it.

---

## Team

| Person | Role | Owns |
|--------|------|------|
| **Curtis** | Product Lead / Engine | Engine (`engine/`), all docs in `docs/`, repo structure, condition library integration |
| **Sasank** | Scientific Advisor | `docs/interpretation-spec.md`, condition library spreadsheet (OMIM IDs, plain descriptions, action guidance) |
| **Hampton** | Backend / Infra / DevOps | API server, Celery workers, Docker, CI/CD, database, auth (Authelia), security hardening |
| **Tom** | Frontend Dev | React app — upload page, processing page, results page |
| **Rocky** | Frontend Design | Results card mockup, visual design system |
| **Jeran** | Marketing / Growth | Community outreach, early users, brand, Google Workspace |
| **Cane** | Security / Compliance | Pre-launch security audit, Nmap scan, privacy policy, consent gate |

---

## What each person reads first

| Person | Read this |
|--------|-----------|
| Curtis | Everything — you wrote it |
| Sasank | `docs/narrative.md`, `docs/interpretation-spec.md` — then write your sections |
| Hampton | `docs/engine-spec.md` (API section), `docs/data-sources.md`, engine `README.md` |
| Tom | `docs/product-spec.md` — every screen, every state |
| Rocky | `docs/product-spec.md` (results card sections), `docs/interpretation-spec.md` (tiers and VUS section) |
| Jeran | `docs/narrative.md` |
| Cane | `docs/data-sources.md` (what user data leaves the system), `docs/product-spec.md` (consent checkbox) |

---

## Architecture (decided, not up for debate)

- **Runtime:** SaaS web app on Hampton's Kubernetes cluster
- **API layer:** FastAPI wrapping the engine — `from engine import run_pipeline`, one endpoint, async workers
- **Database:** Postgres is the source of truth. Variant annotation results, user profiles (when accounts exist), condition library, research tracking records — all in Postgres
- **Auth:** Authelia (Hampton deploys and owns this)
- **CI/CD:** Push to `main` → Docker build → auto-deploy. No manual deploys
- **Annotation cache:** Postgres stores annotation results so repeated lookups don't re-hit the external APIs
- **Research tracking (subscription):** Nightly job polls PubMed for new papers matching stored variant profiles; LLM summarizes; results written to Postgres; user notified
- **LLM use:** Research summarization only. Not variant classification, not summary generation, not anything in the engine pipeline

## Critical path

This is the sequence nothing can skip. Everything else runs in parallel.

```
Hampton: FastAPI + Docker + K8s cluster running
    ↓
Engine callable via HTTP (even with mock results)
    ↓
Tom: Upload → Processing → Results screens wired to real API
    ↓
Sasank: Condition library populated (ACMG81 genes minimum)
    ↓
Rocky: Results card designed against real content
    ↓
Cane: Security audit passes
    ↓
Jeran: First users lined up
    ↓
Soft launch
```

Hampton's infra and Sasank's content run in parallel. Tom cannot finish the results page until Sasank has at least a few real condition library entries to design against — use BRCA1 and TP53 as unblocking examples first.

---

## How to contribute to the repo

**If you are Sasank:**
- Pull the repo
- Navigate to `docs/`
- Edit `interpretation-spec.md` — find sections marked `[SASANK REVIEW]` and fill them in
- Create and populate the condition library spreadsheet (schema in `docs/interpretation-spec.md`)
- Do not touch any `.py` files unless you have discussed it with Curtis first

**If you are Tom:**
- Build against `docs/product-spec.md`
- The API response shape is documented in `docs/engine-spec.md` (Output section)
- Use mock data that matches the field names exactly — the real API will return the same shape
- If the spec is ambiguous, ask Curtis to clarify the spec before building

**If you are Hampton:**
- The engine is imported as `from engine import run_pipeline`
- Workers call `run_pipeline(file_bytes, filename, filters=[...])` and get back `list[dict]`
- The engine README has FastAPI and Celery wrapping examples
- `NCBI_API_KEY` env var raises ClinVar rate limit — set it in production

**If you are Rocky:**
- Design the results card against `docs/product-spec.md`
- The five tier states are: 🔴 Critical, 🟠 High, 🟡 Medium/VUS, 🟢 Low, 🔵 Carrier
- VUS cards and Carrier cards have distinct layouts — see product-spec for specifics
- Sasank's condition library text is what goes in the "plain description" section — design around that length

---

## Immediate next deliverable per person

These are the things that are blocking other people right now. Each person should complete their item before anything else.

| Person | Deliverable | Blocks |
|--------|-------------|--------|
| **Hampton** | Docker container running the engine behind FastAPI, accessible at a URL | Everything. No URL = no product. |
| **Sasank** | Condition library rows for BRCA1, TP53, LDLR, RYR1 (4 rows minimum to unblock design) | Rocky's design, Tom's results page |
| **Tom** | Upload screen wired to real API endpoint (even if results are mock data) | Visible progress for demo |
| **Rocky** | Results card mockup — one Critical card and one Carrier card, using Sasank's real text | Tom's implementation |
| **Jeran** | Get a Google Workspace account with a real branded email | Everything Jeran does publicly |
| **Cane** | Privacy policy draft and consent gate language reviewed | Launch |
| **Curtis** | Condition library `condition_key` format confirmed with Sasank (OMIM ID or what?) | Sasank can't build the spreadsheet without this |

## Open decisions (needs resolution)

| Decision | Status | Owner |
|----------|--------|-------|
| Domain / URL | ❌ Unresolved — Hampton needs this to deploy | Hampton + Curtis |
| Beyond ACMG SF scope for V1 — what genes? | ❌ Unresolved | Sasank |
| VUS exact display language | ❌ Draft in interpretation-spec | Sasank |
| Carrier language for specific genes (CFTR, HBB, etc.) | ❌ Unresolved | Sasank |
| Consumer brand name | ❌ Not now — legal entity is "40 Minute Bioscience" | Jeran |
| Subscription pricing | ❌ Not now | Curtis |
| Pharmacogenomics in V1? | ❌ Not in scope — confirm | Curtis + Sasank |
| LLC incorporation | ❌ Must happen before first paying customer | Curtis |

---

## Not in scope for V1

- User accounts / saved results
- Email delivery of reports
- PRS (polygenic risk scores)
- Multi-omic data
- Clinician-facing features
- Mobile app
- API access for third-party developers
- Pharmacogenomics (infrastructure exists; content not ready)
- Direct-to-consumer sequencing

---

*Anyone can edit this file. Keep it accurate.*
