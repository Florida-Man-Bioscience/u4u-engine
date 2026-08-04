# SITE_INVENTORY — flmanbiosci.net sources + live routes

**Task:** `t-fmbweb-inventory` / kanban `t_f12a9f1a`  
**Inventory date:** 2026-08-03  
**Scope:** Map how flmanbiosci.net is built and what is live today. **No production changes.**

---

## 1. Executive snapshot

| Fact | Detail |
|------|--------|
| **What serves apex today** | **u4u-engine Next.js frontend** (`u4u-engine-frontend`), not the static marketing repo |
| **Live title at `/`** | “PeptOdyssey — Precision Peptide Genomics” (product upload UI) |
| **Marketing site repo** | `fmb-website` exists and was designed as the corporate front door; **not** on the production HTTPRoute |
| **Deploy** | RKE2 + Flux GitOps on hwcopeland cluster (`theswamp`); Cloudflare DNS proxied |
| **Not Vercel/Netlify** | No Vercel/Netlify production path for flmanbiosci.net |
| **Critical gate** | `https://flmanbiosci.net/peptodyssey/privacy` → **HTTP 404 live** (TestFlight blocker). Source **is** on `origin/main`; production image lags |

---

## 2. Repositories (GitHub org `Florida-Man-Bioscience`)

Local clones checked on this host unless noted.

| Repo | Local path | Role | Git remote |
|------|------------|------|------------|
| **u4u-engine** | `/home/noahtjones/u4u-engine` (+ worktree `/home/noahtjones/u4u-engine/.worktrees/t_f12a9f1a`) | Genome→peptide engine, FastAPI, **production Next frontend** | `https://github.com/Florida-Man-Bioscience/u4u-engine` |
| **fmb-website** | `/home/noahtjones/fmb-website` | Static HTML/CSS marketing site (nginx image). README still says “marketing site for flmanbiosci.net” but apex routes to Next | `https://github.com/Florida-Man-Bioscience/fmb-website` |
| **company** (clone often `fmb-company`) | `/home/noahtjones/fmb-company` | Operating knowledge base: business plan, product, brand, regulatory posture | `https://github.com/Florida-Man-Bioscience/company` |
| **peptodyssey** | `/home/noahtjones/peptodyssey` | iOS HealthKit app; hard-depends on privacy URL + `/api/v1` | private GH |
| **u4u-privacy** | (org listed; optional local) | Local-first consumer-genomics toolkit | GH org |
| **iac** (ops, not FMB org) | `/home/noahtjones/iac` | Cluster GitOps: HTTPRoutes, Deployments, DNSRecords | `https://github.com/hwcopeland/iac` |
| **Planning** | `/home/noahtjones/Planning` | Older product-planning markdown | GH org `Planning` |
| Legacy / peripheral | `frontend`, `u4u-app`, `genomics-platform1`, `variant-prioritization`, `pettides`, `demo-repository`, `tailstail` | Historical or unrelated; **not** what serves apex today | GH org |

### Worktree note

This inventory file lives in kanban worktree:

`/home/noahtjones/u4u-engine/.worktrees/t_f12a9f1a`  
branch `wt/t_f12a9f1a` (based on u4u-engine history including privacy page commit `05cf429`).

---

## 3. Deploy target (production)

### Topology (authoritative: `docs/server-management.md` + iac manifests)

```
Internet
  → Cloudflare (proxied A → 69.180.240.158)
  → Cilium Gateway (hwcopeland-gateway, kube-system)
  → HTTPRoute theswamp/u4u-engine
       /api/v1/*  → Service u4u-engine          → Deployment u4u-engine (:8000)
                    (prefix rewrite /api/v1 → /)
       /*         → Service u4u-engine-frontend → Deployment u4u-engine-frontend (:3000)
```

| Piece | Path / value |
|-------|----------------|
| Namespace | `theswamp` |
| Manifests | `/home/noahtjones/iac/rke2/tooling/flux/theswamp/` |
| HTTPRoute | `httproute.yaml` — hostnames `flmanbiosci.net` |
| App host | `app.flmanbiosci.net` — same frontend + `/api/v1` rewrite |
| API host | `api.flmanbiosci.net` — backend at **root** (no `/api/v1` prefix) |
| www | `httproute-www-redirect.yaml` — **301** → `https://flmanbiosci.net` |
| DNS | `/home/noahtjones/iac/rke2/kube-system/flmanbiosci-dnsrecord.yaml` (Cloudflare operator) |
| Images | `zot.hwcopeland.net/florida-man-bioscience/u4u-engine` + `u4u-engine-frontend` |
| Frontend pin (local iac) | `deployment-frontend.yaml` → digest `sha256:0f6ae08d…` (Flux `# {"$imagepolicy": "tooling:u4u-engine-frontend"}`) |
| Release loop | push `main` → self-hosted GH Actions build/push Zot → Flux ImageUpdateAutomation rewrites digest → rollout |
| Secrets | External Secrets / Bitwarden (see ACCESS.md for collaborator kubectl) |

### What is **not** production

- **Vercel / Netlify / static-host-only:** no production config found for flmanbiosci.net.
- **fmb-website nginx image:** not referenced in `theswamp` HTTPRoutes. Local `docker-compose.yml` in u4u-engine **no longer** mounts a `website` service (fmb-website README still describes an older compose layout with website on `:8080`).
- **Standalone VPS compose** (`docs/deploy.md`): alternate path only; not apex.

### Hosts probed 2026-08-03

| Host / path | Result |
|-------------|--------|
| `https://flmanbiosci.net/` | **200** Next PeptOdyssey shell |
| `https://www.flmanbiosci.net/` | **301** → `https://flmanbiosci.net/` |
| `https://app.flmanbiosci.net/` | **200** (same product UI) |
| `https://api.flmanbiosci.net/health` | **200** `{"status":"ok",…}` |
| `https://flmanbiosci.net/api/v1/health` | **200** |
| `https://app.flmanbiosci.net/api/v1/health` | **200** |
| Live `/robots.txt` | **200** — Cloudflare “content signals” body (not app `public/` assets) |

---

## 4. Current route table

### 4.1 Next.js App Router (source of truth in repo)

Under `frontend/src/app/` (worktree + extra pages on `origin/main`):

| Route | Source file | Live HTTP (2026-08-03) | Notes |
|-------|-------------|------------------------|-------|
| `/` | `page.tsx` | **200** | Genome upload / “New Analysis”; branded PeptOdyssey not FMB corporate |
| `/jobs` | `jobs/page.tsx` | **200** | History |
| `/jobs/[id]` | `jobs/[id]/page.tsx` | **200** (dynamic) | Job progress |
| `/jobs/[id]/results` | `jobs/[id]/results/page.tsx` | (dynamic) | Results tabs peptides \| pgx \| variants |
| `/tracking` | `tracking/page.tsx` | **200** | Biomarker tracking |
| `/tracking/cohort` | `tracking/cohort/page.tsx` | **200** | |
| `/tracking/model` | `tracking/model/page.tsx` | **200** | Model docs UI |
| `/tracking/patients/[id]` | `tracking/patients/[id]/page.tsx` | (dynamic) | |
| `/tracking/patients/[id]/onboard` | `…/onboard/page.tsx` | (dynamic) | |
| `/tracking/diagnostics` | on **origin/main** (`frontend/src/app/tracking/diagnostics/page.tsx`) | **404 live** | In main, not in shipped image |
| `/regulatory` | `regulatory/page.tsx` | **200** | FDA peptide dashboard (SSR) |
| `/study` | `study/page.tsx` | **200** | Human study surface |
| `/study/dev` | `study/dev/page.tsx` | **200** | Internal design/status |
| `/faq` | on **origin/main** | **404 live** | Merged ~2026-07-31; not live |
| `/peptodyssey/privacy` | `peptodyssey/privacy/page.tsx` (commit `05cf429`, **2026-07-16**, on main) | **404 live** | **TestFlight / App Store privacy URL** |
| `/peptodyssey` (index) | none | **404** | No product hub page yet |
| `/about`, `/contact`, `/peptides`, `/privacy` | none | **404** | |

**Nav (live + source `frontend/src/app/components/Nav.tsx`):** History · Tracking · Regulatory · Study · New Analysis — all PeptOdyssey product chrome.

**next.config.ts:** `output: 'standalone'` only; no redirects/rewrites in Next.

### 4.2 fmb-website static (not on apex today)

| Path | File | Intent |
|------|------|--------|
| `/` | `index.html` | Corporate marketing: hero, `#platform`, `#products`, `#team`, `#contact` |
| `/peptodyssey/privacy/` | `peptodyssey/privacy/index.html` | Static privacy (nginx `try_files`) |
| `/404.html`, `/robots.txt`, `/sitemap.xml` | root | Static SEO |

README in fmb-website explicitly notes production apex goes to Next and that privacy must be mirrored there.

### 4.3 Backend API (public via gateway)

Prefixed with `/api/v1` on apex/app; bare paths on `api.flmanbiosci.net`.

| Area | Paths (backend root) |
|------|----------------------|
| Core | `GET /health`, `POST /analyze`, `GET /jobs`, `GET /jobs/{id}`, dossier/pgx/drug, ACMG sign-off |
| Tracking | `/tracking/*` (patients, treatments, measurements, cohort, predictions, …) |
| HealthKit | `/healthkit/enroll`, `/healthkit/samples` |
| Users | `/users`, `/users/me` |
| Regulatory | `/regulatory/peptides`, `/regulatory/events` |

### 4.4 Redirects / coupling

| From | To | Mechanism |
|------|-----|-----------|
| `www.flmanbiosci.net/*` | `https://flmanbiosci.net/*` | Gateway RequestRedirect 301 |
| Browser `/api/v1/*` | backend `/` | HTTPRoute URLRewrite |
| **No** marketing↔app path split | Single `/*` → frontend | Corporate homepage cannot go live without route ownership change |

---

## 5. PeptOdyssey privacy coupling (must stay HTTP 200)

**Canonical URL (hard requirement):**  
`https://flmanbiosci.net/peptodyssey/privacy`

| Artifact | Absolute path / ref |
|----------|---------------------|
| Next page (production owner of record) | `/home/noahtjones/u4u-engine/.worktrees/t_f12a9f1a/frontend/src/app/peptodyssey/privacy/page.tsx` |
| Commit on main | `05cf429` *feat: host PeptOdyssey iOS privacy policy at /peptodyssey/privacy* (2026-07-16) |
| Static mirror | `/home/noahtjones/fmb-website/peptodyssey/privacy/index.html` |
| iOS app link | `peptodyssey` → `AppLinks.privacyPolicy` in `peptodyssey/App/ConsentView.swift` |
| Ship docs | `/home/noahtjones/peptodyssey/README.md`, `docs/TESTFLIGHT_CHECKLIST.md`, `docs/PRIVACY_LABEL.md` |

**Live status (re-probed 2026-08-03):** **HTTP 404** (Next.js 404 HTML ~11KB). Same failure logged in TestFlight checklist (2026-07-26).  

**Implication for restructure:** any IA that moves paths must keep this URL **200** (redirect or leave page in place). Today the gate is already broken — fix is deploy/image lag, not missing source. Sibling main-only routes (`/faq`, `/tracking/diagnostics`) also 404, consistent with **frontend image behind `origin/main`**.

Do **not** treat fmb-website alone as restoring the URL until HTTPRoute points at it or Next image includes the page.

---

## 6. Content source index (absolute paths)

### 6.1 Primary narrative / company copy (repos)

| Path | Use for restructure |
|------|---------------------|
| `/home/noahtjones/fmb-company/README.md` | One-paragraph company story; repo map |
| `/home/noahtjones/fmb-company/brand/README.md` | Positioning, voice, product naming |
| `/home/noahtjones/fmb-company/business-plan/01-executive-summary.md` | **Read → Predict → Report → Track → Deliver** loop (closest philosophy ladder) |
| `/home/noahtjones/fmb-company/business-plan/03-platform.md` | Platform flywheel diagram + product stages |
| `/home/noahtjones/fmb-company/business-plan/*.md` | Market, GTM, roadmap, risks |
| `/home/noahtjones/fmb-company/product/*.md` | PeptidIQ, PeptOdyssey dossier, Tracker, MSP-nanodisk |
| `/home/noahtjones/fmb-company/company/*.md` | Team, structure, cap table, governance |
| `/home/noahtjones/fmb-company/regulatory/*.md` | Claims / privacy posture |
| `/home/noahtjones/fmb-website/index.html` | **Shipped marketing copy** (not live on apex): hero, platform cards, programs, team, contact |
| `/home/noahtjones/fmb-website/assets/` | Brand images (team, nanodisk, neurocreatine, mark) |
| `/home/noahtjones/u4u-engine/.../frontend/src/app/**` | Live product UI copy |
| `/home/noahtjones/u4u-engine/.../docs/server-management.md` | Deploy runbook |
| `/home/noahtjones/u4u-engine/.../docs/frontend.md` | Frontend/API base conventions |

### 6.2 Dropbox / cloud folders

| Path | Contents (high signal) |
|------|------------------------|
| **`/home/noahtjones/UF Dropbox/Noah Jones/Florida Man Bioscience/`** | **Main Dropbox FMB dump** — pitch decks, roadmaps, team photos, PeptOdyssey dossier PDF, nanodisk reports, workshop notes, Figma export, org notes |
| `…/pitch_deck.pdf` / `pitch_deck.pptx` / `PeptidIQ_Pitch_Deck_2026-05-07.pptx` | Investor/pitch narratives |
| `…/roadmaps/` | `U4u Roadmap.pdf`, `U4u Part 2 + Overview.pdf`, `U4u Tom Depth.pdf`, `Nanodisk Roadmap.pdf`, `Vr Roadmap.pdf`, `Pitch Ideas.pdf` |
| `…/Dossier_PeptOdyssey.pdf` | Sample dossier artifact |
| `…/Florida_Man_Bioscience_Strategic_Plan.pptx` | Strategy deck |
| `…/Florida_Man_Bioscience_Teams_Model.pptx` | Team model |
| `…/5_Slide_Pitch_Deck.pptx`, `single-slide.*`, `slide_for_activator.*` | Short pitches |
| `…/Histone_Mimetic_MSP_Nanodisk_Project_Report.pdf`, `MSP_nanodisk_siRNA_docking_report.pdf`, `Nanodisk_Project_Summary_Presentation.pptx` | Delivery science copy |
| `…/PeptOdyssey_Advisor_Report_Auralis.pdf` | Advisor-facing PeptOdyssey |
| `…/FloridaManBioScience – Figma Make.html` (+ `_files/`) | Design export (not clean copy source) |
| `…/Technical Risk and Scientific Plan/Executive_Summary_FloridaManBioscience.txt` | Workshop post-work notes (advisor feedback; **not** polished brand philosophy) |
| `…/Strategic Fundraising/Executive_Summary_FloridaManBioscience.txt` | Stub / instructions only |
| `…/Secret Score Cards and Rubrics/` | Investor DD templates (not website copy) |
| `…/fmb.org` | Noah org-mode work log (ops TODOs; not public site copy) |
| `…/curtis.png`, `jacob.png`, `tyler.png`, `michael.jpg`, headshots | Team photography sources (also mirrored into fmb-website assets) |

**Not found:**

- Personal Dropbox root `/home/noahtjones/Dropbox` — **no** dedicated Florida Man Bioscience folder (personal academic dump only).
- Obsidian vault `/home/noahtjones/Florida Man Bioscience` — nearly empty scratch vault (Welcome + empty dated notes); **not** a content library.
- `/home/noahtjones/Box` — no FMB website corpus found at shallow depth.

### 6.3 Arete plan context (restructure program)

| Path | Note |
|------|------|
| `/home/noahtjones/arete-holdings-llc/data/plan.yaml` | Project `p-01184334` FMB website restructure; tasks inventory → IA → content → build |
| Target philosophy phrasing in **plan** (not yet in company brand docs as exact triad): **Detect → Design → Deliver** |

---

## 7. Detect / Design / Deliver language

### 7.1 Exact triad “Detect → Design → Deliver”

**Not found** as an existing published slogan in:

- `fmb-website/index.html`
- `fmb-company/brand/*` or business-plan body copy
- UF Dropbox executive summary text files (workshop notes only)
- Live PeptOdyssey frontend nav/home

It appears as **program language** in Arete plan / dispatch bodies for the restructure (desired homepage philosophy), not as mined historical site copy.

### 7.2 Closest existing ladders / exact phrases (use for content drafting)

From **`/home/noahtjones/fmb-company/business-plan/01-executive-summary.md`**:

1. **Read** the patient's genome.  
2. **Predict** their peptide/hormone response — **PeptidIQ**.  
3. **Report** it in a clear, individualized dossier — **PeptOdyssey**.  
4. **Track** the response over time — the **Tracker**.  
5. **Deliver** the molecule — **MSP-nanodisk**.

Tagline (repeated brand + marketing):

> **Peptide medicine, matched to the genome.**

Brand positioning (`brand/README.md` / marketing hero):

> We build the **analytics**, the **trackers**, and the **delivery platform** behind precision peptide therapy…

Marketing platform section (`fmb-website/index.html`):

> **Three layers, one feedback loop.**  
> PeptidIQ · PeptOdyssey · Tracker  

Product kickers on marketing page: **Delivery** (MSP nanodisk), **Discovery** (Neuro-creatine & CNS peptides).

**Mapping suggestion for IA (non-authoritative):** Detect ≈ Read+Predict (genome/analytics); Design ≈ Report+Track / productization of the loop; Deliver ≈ MSP-nanodisk + getting therapy to the patient — *or* collapse to three stages if brand wants the plan’s triad. Content task should not invent clinical claims beyond these sources.

---

## 8. Dual-host reality (restructure constraint)

| Concern | Today |
|---------|--------|
| Corporate homepage | **Offline** relative to DNS: only exists in `fmb-website` / company docs |
| Product app | **Owns** entire apex `/*` |
| Privacy | Implemented in **both** repos; **neither** currently yields 200 on apex |
| Compose local | api + postgres + frontend only |
| Desired end state (plan) | `/` company home; `/peptodyssey/*` product tree; preserve privacy URL |

Any cutover needs an explicit HTTPRoute or reverse-proxy ownership map (static vs Next vs path split). Documented for follow-on IA task `t-fmbweb-ia`.

---

## 9. Gaps / follow-ups (out of inventory scope)

1. **Restore privacy HTTP 200** without waiting for full restructure (frontend image rebuild/rollout or temporary static route) — TestFlight gate.  
2. Confirm why Flux/image lag leaves July 16+ frontend routes dark while main has advanced (CI frontend path filter, runner, or failed automation).  
3. IA: company home vs PeptOdyssey tree; redirect list when `/` stops being upload UI.  
4. Content: draft Detect→Design→Deliver from §7 sources; cite Dropbox decks for voice (prefer human review of pitch PDFs for claims).  
5. fmb-website README / compose docs are **stale** vs production topology — update when ownership is decided.

---

## 10. Verification commands (re-run anytime)

```bash
curl -sS -o /dev/null -w "%{http_code}\n" https://flmanbiosci.net/
curl -sS -o /dev/null -w "%{http_code}\n" https://flmanbiosci.net/peptodyssey/privacy   # must be 200 for TestFlight
curl -sS https://flmanbiosci.net/api/v1/health
curl -sS -o /dev/null -w "%{http_code}\n" -L --max-redirs 0 https://www.flmanbiosci.net/
```

---

*Generated for Arete plan task `t-fmbweb-inventory`. Deliverable path: `docs/SITE_INVENTORY.md` in u4u-engine worktree `t_f12a9f1a`.*
