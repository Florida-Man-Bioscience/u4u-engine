# FMB website information architecture

**Status:** proposal (no production changes)  
**Plan task:** `t-fmbweb-ia` · project `p-01184334`  
**Date:** 2026-08-04  
**Workspace:** `u4u-engine` worktree `t_ad15f7e7` @ branch `wt/t_ad15f7e7`  
**Depends on:** `t-fmbweb-inventory` (not journaled yet) — this doc embeds a **baseline inventory** from live checks + local repos so IA is not blocked.

---

## 1. Goals

| Goal | Target |
|------|--------|
| Company apex | `https://flmanbiosci.net/` = Florida Man Bioscience home (who / what / philosophy / product doorways) |
| Product tree | `https://flmanbiosci.net/peptodyssey/*` = PeptOdyssey product surface |
| Room to grow | Secondary nav/cards for other FMB products — **stubs only** unless real copy already exists |
| Non-goal | Full product microsites for every line; production cutover (later tasks) |

Hard external constraint (TestFlight / App Store):

> **`https://flmanbiosci.net/peptodyssey/privacy` must remain HTTP 200 forever** (path frozen).  
> Referenced from `peptodyssey` app (`AppLinks.privacyPolicy` / `docs/PRIVACY.md`) and `fmb-website` sitemap.

---

## 2. Baseline inventory (as of 2026-08-04)

### 2.1 Repos & deploy

| Surface | Path / repo | Role today |
|---------|-------------|------------|
| **Live apex UI** | `Florida-Man-Bioscience/u4u-engine` → `frontend/` (Next.js) | Serves **almost everything** at `flmanbiosci.net` and `app.flmanbiosci.net` |
| **Live API** | same repo → `api.py` + `engine/` | `/api/v1/*` (prefix rewrite) and `api.flmanbiosci.net/*` |
| **Marketing static (not live on apex)** | `/home/noahtjones/fmb-website` (org: `Florida-Man-Bioscience/fmb-website`) | Company SPA-style `index.html` + static privacy; README admits apex currently routes to Next, not this nginx image |
| **Company knowledge base** | `/home/noahtjones/fmb-company` | Business plan, product loop, brand, claims posture |
| **iOS app** | `/home/noahtjones/peptodyssey` | HealthKit research app; privacy URL pin |
| **GitOps** | `/home/noahtjones/iac/rke2/tooling/flux/theswamp/` | HTTPRoutes → `u4u-engine` + `u4u-engine-frontend` only (**no fmb-website Deployment** in this kustomization) |
| **Local compose** | `u4u-engine/docker-compose.yml` | Can build sibling `../fmb-website` as `website:8080` for local parity |

**Gateway (prod):** Cilium Gateway API

- `flmanbiosci.net`: `/api/v1` → API; `/` → Next frontend  
- `app.flmanbiosci.net`: same split (product mirror host)  
- `api.flmanbiosci.net`: API at root  
- `www` → 301 apex  

### 2.2 Live HTTP snapshot (curl, 2026-08-04)

| URL | Code | Notes |
|-----|------|--------|
| `https://flmanbiosci.net/` | **200** | Title: **PeptOdyssey — Precision Peptide Genomics** (genome upload tool, not company home) |
| `https://flmanbiosci.net/jobs` | 200 | Analysis history |
| `https://flmanbiosci.net/tracking` (+ cohort, model) | 200 | Biomarker tracking UI |
| `https://flmanbiosci.net/regulatory` | 200 | FDA peptide dashboard |
| `https://flmanbiosci.net/study` | 200 | Observational study landing (IRB pending copy) |
| `https://flmanbiosci.net/peptodyssey` | **404** | No hub page live |
| `https://flmanbiosci.net/peptodyssey/privacy` | **404** | **Broken TestFlight gate** — code exists on `main` (`05cf429`) but prod image digest has not picked it up yet |
| `https://app.flmanbiosci.net/*` | mirrors apex | Same 404 on privacy |

### 2.3 Next.js route table (source: `frontend/src/app/**/page.tsx`)

| Route | Current purpose | Brand ownership today |
|-------|-----------------|------------------------|
| `/` | Genome upload / “New Analysis” | PeptOdyssey product (occupies company root) |
| `/jobs`, `/jobs/[id]`, `/jobs/[id]/results` | Job status + results (peptides \| pgx \| variants) | Product tool |
| `/tracking`, `/tracking/cohort`, `/tracking/model`, `/tracking/patients/[id](+ /onboard)` | Longitudinal tracker | Product tool |
| `/regulatory` | Regulatory dashboard | Product / research tool |
| `/study`, `/study/dev` | Study info | Research / IRB surface |
| `/peptodyssey/privacy` | iOS privacy policy | **Canonical path** (in git; not live) |

Nav (`frontend/src/app/components/Nav.tsx`): PeptOdyssey brand · History · Tracking · Regulatory · Study · New Analysis. **No company nav.**

### 2.4 fmb-website static map (content ready, not on apex)

| Path | File |
|------|------|
| `/` | `index.html` — company hero, platform (PeptidIQ / PeptOdyssey / Tracker), programs (MSP nanodisk, neuro-creatine), team, contact |
| `/peptodyssey/privacy` | `peptodyssey/privacy/index.html` |
| `/assets/*` | CSS/JS/images |
| `/sitemap.xml`, `/robots.txt`, `/404.html` | present |

Nav anchors: `#platform` `#products` `#team` `#contact`.

### 2.5 Philosophy language (sources vs plan wording)

| Framing | Where it lives | Exact phrase? |
|---------|----------------|---------------|
| **Detect → Design → Deliver** | Arete plan `p-01184334` / homepage build tasks | **Plan-mandated marketing triptych** — **not found as an exact phrase** in `fmb-company` or `fmb-website` on this pass |
| **Read → Predict → Report → Track → Deliver** | `fmb-company/business-plan/01-executive-summary.md`, `03-platform.md` | Canonical internal loop (5 stages) |
| Platform cards PeptidIQ / PeptOdyssey / Tracker | `fmb-website/index.html` | Live marketing copy candidate |
| One-liner | brand + exec summary | “Peptide medicine, matched to the genome.” |

**IA recommendation for content (`t-fmbweb-content`):** treat **Detect → Design → Deliver** as the **public 3-leg story**, explicitly mapped from source loop (do not invent clinical meaning):

| Public leg | Maps from source | Doorway products |
|------------|------------------|------------------|
| **Detect** | Read genome + measure biomarkers (HealthKit / labs) | PeptidIQ upload, Tracker, PeptOdyssey iOS capture |
| **Design** | Predict + report individualized options (prescriber-in-loop) | PeptOdyssey dossier / web results |
| **Deliver** | Learn over time + long-horizon molecule delivery | Tracker feedback; MSP nanodisk (research — no therapeutic ship claim) |

Flag for brand: Noah/Curtis must confirm the 3-leg labels vs keeping the 5-step loop on the public site.

### 2.6 Other product names (secondary only)

From `fmb-company` / plan — **cards/stubs, not full trees unless copy exists:**

| Name | Evidence of copy | Proposed doorway |
|------|------------------|------------------|
| PeptOdyssey / PeptidIQ / Tracker | Strong (repos + site + KB) | Primary product tree |
| MSP nanodisk delivery | `fmb-website` + `product/msp-nanodisk-delivery.md` | Card on company home / `#programs` |
| Neuro-creatine / CNS peptides | `fmb-website` product block | Card only |
| Protein Chemistry | link out to external PRODUCT.md / repo | External or future `/protein-chemistry` stub |
| Genomics SaaS / CytoGate / Neurocreatine (plan list) | Plan wishlist; thin web copy | Secondary nav placeholders only |

### 2.7 Dropbox / local content index (paths for inventory/content tasks)

| Path | Use |
|------|-----|
| `/home/noahtjones/fmb-company/**` | Preferred structured source (brand, claims, platform) |
| `/home/noahtjones/fmb-website/**` | Preferred shipped marketing HTML |
| `/home/noahtjones/Dropbox (UFL)/Florida Man Bioscience/` | Decks, `fmb.org`, workshop PDFs, images — mine carefully; do not invent from sparse slides |
| `/home/noahtjones/peptodyssey/docs/PRIVACY.md` | Privacy source of truth alignment |
| `/home/noahtjones/Florida Man Bioscience/` | Local vault-style notes (if present) |

---

## 3. Target information architecture

### 3.1 Site map (logical)

```
flmanbiosci.net/                          Company home
├── #who / #what / #philosophy            In-page sections (or /about later)
├── #products                             Product cards / doorways
├── #team                                 Team
├── #contact                              Contact (mailto hello@flmanbiosci.net)
│
├── /peptodyssey/                         PeptOdyssey product hub
│   ├── /privacy                          **FROZEN** App Store / TestFlight privacy
│   ├── /analyze   (or /app)              Genome upload (today’s `/`)
│   ├── /jobs…                            Analysis history + results
│   ├── /tracking…                        Biomarker tracker UI
│   ├── /regulatory                       Optional: keep top-level alias (see redirects)
│   └── /study…                           Study pages (or keep top-level /study)
│
├── /products/…                           Optional future stubs (not required v1)
│   ├── peptidig → redirect → /peptodyssey or engine docs
│   └── …                                 CytoGate, Protein Chemistry, etc. when real
│
├── /api/v1/*                             Backend (unchanged)
app.flmanbiosci.net/*                     Product-only host (tools; no company chrome required)
api.flmanbiosci.net/*                     API host (unchanged)
```

### 3.2 Route map (from → to)

| Current (live / source) | Proposed canonical | Action |
|-------------------------|--------------------|--------|
| `/` genome upload (Next) | `/peptodyssey/analyze` **or** keep upload only on `app.flmanbiosci.net/` | **Move** tool off company root; 301 from old path after grace period |
| `/` company home (fmb-website, not live) | `/` | **Become** live company home |
| *(missing)* PeptOdyssey hub | `/peptodyssey` and `/peptodyssey/` | **Create** |
| `/peptodyssey/privacy` | `/peptodyssey/privacy` | **Preserve path**; restore 200 ASAP (deploy already-landed git) |
| `/jobs…` | `/peptodyssey/jobs…` | Prefer nest under product; **301** old paths |
| `/tracking…` | `/peptodyssey/tracking…` | Same |
| `/regulatory` | Option A: `/peptodyssey/regulatory` · Option B: stay top-level “research tools” | Prefer **A** for product cohesion; keep **301** alias either way |
| `/study`, `/study/dev` | `/peptodyssey/study…` **or** company `/research/study` | Prefer under PeptOdyssey (pipeline validation); keep top-level **301** for IRB bookmarks |
| `app.flmanbiosci.net/` | Product entry (analyze) | Keep as **stable product host**; optional no company chrome |
| fmb-website `/assets/*` | Either port into Next `public/` or static backend | Implementation choice (see §5) |

### 3.3 Nav sketch

**A. Company chrome** (apex `/` and shared marketing layout)

```
[ F mark | Florida Man Bioscience ]
  Philosophy   Products   Team   Contact
  [ PeptOdyssey → ]          primary CTA → /peptodyssey/
```

Footer: Platform links · Programs · Company · **Privacy (PeptOdyssey)** · GitHub · ©

**B. Product chrome** (`/peptodyssey/*` tools — evolve today’s `Nav.tsx`)

```
[ ◆ PeptOdyssey ]  ·  FMB ↗ (/)
  Hub · Analyze · History · Tracking · Regulatory · Study · Privacy
```

- **Hub** = `/peptodyssey/` marketing one-pager (not the upload form).  
- **Analyze** = upload form.  
- **Privacy** always visible in product footer (App Store reviewers + users).

**C. Secondary product row** (company home only — cards, not top nav clutter)

- PeptOdyssey (live CTA)  
- PeptidIQ engine (deep-link analyze or docs)  
- Tracker (deep-link tracking)  
- MSP nanodisk / Neuro-creatine (descriptive cards; no fake “Launch app”)  
- Protein Chemistry / CytoGate / Genomics SaaS — “Coming into the portfolio” if no copy  

### 3.4 Page briefs (IA only; copy = later task)

| Page | Must include | Must not |
|------|--------------|----------|
| `/` company | Who/what; Detect→Design→Deliver (mapped); product doorways; contact; plain-language claims discipline | Guaranteed clinical outcomes; DTC prescribing language |
| `/peptodyssey/` | What PeptOdyssey is (dossier + iOS capture + web tools); links to Analyze, Privacy, Study; research/not a device | Overclaim vs dossier evidence |
| `/peptodyssey/privacy` | Existing counsel-draft policy; version date | Path change; silent material edits without counsel |
| `/peptodyssey/analyze` | Today’s upload UX | Owning the company brand root |
| Tool pages | Existing functionality | Rewrites outside IA scope |

---

## 4. Redirect list

Implement with Next `next.config` redirects **and/or** Gateway HTTPRoute filters. Prefer **301** after a short dual-serve window; use **308** only if method preservation matters (mostly GET UI).

### 4.1 Required (product move)

| From | To | When |
|------|----|------|
| `/` *(tool only after company home ships — see cutover)* | — | Do **not** 301 `/` away from company home |
| `/analyze` (if introduced as alias) | `/peptodyssey/analyze` | optional |
| `/jobs` | `/peptodyssey/jobs` | on nest |
| `/jobs/:path*` | `/peptodyssey/jobs/:path*` | on nest |
| `/tracking` | `/peptodyssey/tracking` | on nest |
| `/tracking/:path*` | `/peptodyssey/tracking/:path*` | on nest |
| `/regulatory` | `/peptodyssey/regulatory` | if nested |
| `/study` | `/peptodyssey/study` | if nested |
| `/study/dev` | `/peptodyssey/study/dev` | if nested |

### 4.2 Privacy — **no redirect away**

| From | To | Rule |
|------|----|------|
| `/peptodyssey/privacy` | **itself** | Never 301 to `/privacy`, `/legal`, or query variants as sole target |
| `/peptodyssey/privacy/` | `/peptodyssey/privacy` | Trailing-slash normalize OK if both **200** or one 308→200 |
| `/privacy` (if ever added) | `/peptodyssey/privacy` | Optional convenience only |

### 4.3 Host convenience

| From | To | Notes |
|------|----|-------|
| `www.flmanbiosci.net/*` | apex | Already 301 |
| `app.flmanbiosci.net/peptodyssey/privacy` | same path on app host **or** 301→apex privacy | Prefer **same path 200 on both hosts** so either base URL works |
| Old bookmarks to apex tool URLs | nested product paths | After nest ships |

### 4.4 Explicit non-redirects

- `/api/v1/*` — stay.  
- Deep job result URLs — only change prefix via §4.1, preserve `:id` and query (`?tab=` etc.).

---

## 5. Implementation options (choose in build tasks — not this card)

| Option | Summary | Pros | Cons |
|--------|---------|------|------|
| **A. Next owns apex (recommended default)** | Port company home + assets into `u4u-engine/frontend`; single Flux image; nest product routes | One deploy path; shared design tokens; privacy already in Next | Larger frontend ownership; must not break tool UX |
| **B. Gateway path-split** | Exact `/` + `/assets` (+ maybe marketing-only paths) → `fmb-website` nginx; tools + `/peptodyssey/*` → Next | Reuses static repo as-is | Split brain; easy to 404 privacy if rules wrong; two images |
| **C. Subdomain split** | Apex = company static only; **all** tools only on `app.` | Clean brand separation | Breaks current apex tool bookmarks; privacy must still be on apex path for App Store string |

**Recommendation:** **A** for v1 restructure (matches current GitOps), keep **`app.`** as product mirror. Revisit **B/C** only if marketing wants zero React on `/`.

Cutover sequence (for later `t-fmbweb-homepage` / verify tasks):

1. **Unblock privacy 200** on current path (deploy `05cf429` or newer) — independent of IA.  
2. Ship `/peptodyssey` hub + nest tools behind feature flag or dual routes (old + new).  
3. Ship company `/`.  
4. Enable 301s from old tool paths.  
5. Verify privacy + redirects (`t-fmbweb-verify-deploy`).

---

## 6. Privacy URL preservation plan

| Control | Detail |
|---------|--------|
| **Canonical URL** | `https://flmanbiosci.net/peptodyssey/privacy` |
| **App pin** | `peptodyssey` → `AppLinks.privacyPolicy` / `docs/PRIVACY.md` — **do not change string** without coordinated app release |
| **Sources to keep aligned** | (1) `fmb-website/peptodyssey/privacy/index.html` (2) `u4u-engine/frontend/src/app/peptodyssey/privacy/page.tsx` (3) `peptodyssey/docs/PRIVACY.md` — pick one SSoT in a later chore; until then **diff on every policy edit** |
| **Prod gate** | Synthetic check: `curl -fsS -o /dev/null -w '%{http_code}' https://flmanbiosci.net/peptodyssey/privacy` expects `200` (and ideally `app.` too) |
| **Sitemap** | Keep URL in `fmb-website/sitemap.xml` and any Next sitemap |
| **IA freeze** | Nesting other routes under `/peptodyssey/*` is fine; **privacy leaf name stays `privacy`** |
| **Counsel** | Page already banners “Counsel review open” — material edits = human/legal, not drive-by marketing |
| **Current incident** | **Live 404** despite git on `main` — treat as **ship/verify P0** before App Store review; out of scope to force-deploy from this IA task |

---

## 7. Human brand / legal review flags

Anything below needs Noah/Curtis and/or counsel before broad external push. **Not invented legal conclusions** — pointers into existing posture docs.

| ID | Topic | Why it matters | Source / locus |
|----|--------|----------------|----------------|
| L1 | **Therapeutic / prescribing tone** | fmb-website: “prescribes the peptide”, “right peptide at the right dose” can read as clinical direction | `fmb-website/index.html`; posture in `fmb-company/regulatory/clinical-and-claims.md` (prescriber-in-loop, no guarantees) |
| L2 | **SaMD / CDS claims** | Genome → therapy guidance may be regulated depending on autonomy and claims | same regulatory note |
| L3 | **Health data / HIPAA-ish language** | Privacy + study pages describe HealthKit, genetics, retention | `/peptodyssey/privacy`, `/study`; `fmb-company/regulatory/health-data-privacy.md` |
| L4 | **Privacy counsel open** | Explicit draft banner; TestFlight OK ≠ broad distribution sign-off | privacy page + `peptodyssey/docs/PRIVACY.md` |
| L5 | **Study / IRB** | `/study` is “Pending IRB review / not recruiting” — keep non-soliciting | `frontend/.../study/page.tsx` |
| L6 | **Peptide panel marketing grades** | Landing lists BPC-157 etc. with evidence grades — easy to overread as endorsement | current Next `/` |
| L7 | **Delivery / nanodisk** | Research-stage; must not sound approved therapeutic | fmb-website products + MSP docs |
| L8 | **Team names / roles / photos** | Public attribution — confirm OK to ship | fmb-website `#team` |
| L9 | **Detect→Design→Deliver labels** | Plan phrase ≠ established brand asset yet | brand decision |
| L10 | **Entity / portfolio claims** | Do not invent ownership, cap table, or “Arete” public wording on marketing without approval | internal `fmb-company` only unless cleared |

Marketing rule of thumb (from claims doc): say what the system **does** (annotate, score, track), not what it **guarantees** (outcomes).

---

## 8. Open decisions (for humans — not blockers for IA.md itself)

1. Confirm **Detect → Design → Deliver** vs public **5-step loop** naming.  
2. Nest tools under `/peptodyssey/*` vs leave `/jobs` `/tracking` top-level with only marketing under `/peptodyssey`. (*IA default: nest + 301.*)  
3. Option A/B/C hosting (§5).  
4. Whether `app.flmanbiosci.net` stays full mirror or becomes the **only** tool host.  
5. Priority of **privacy 200** hotfix vs homepage build order (recommend privacy first).

---

## 9. Downstream handoff

| Next plan task | Consumes from this doc |
|----------------|------------------------|
| `t-fmbweb-content` | §3.4 briefs, §2.5 philosophy map, §7 claim flags, source paths |
| `t-fmbweb-homepage` | §3.1–3.3 nav + company `/` |
| PeptOdyssey hub build (if separate) | `/peptodyssey/` + nest |
| `t-fmbweb-verify-deploy` | §4 redirects + §6 privacy checks |
| `t-fmbweb-inventory` (if still open) | May promote §2 into standalone `SITE_INVENTORY.md` without redoing live curls |

---

## 10. Out of scope (this task)

- Production deploys, Flux/image pins, DNS changes  
- Final marketing copy  
- App binary / App Store metadata edits  
- Inventing CytoGate or other product sites  

---

*End of IA proposal.*
