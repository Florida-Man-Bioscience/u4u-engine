# VERIFY — flmanbiosci.net preview/production gate

**Plan task:** `t-fmbweb-verify-deploy`  
**Kanban:** `t_0a90b71d`  
**Probed:** 2026-08-04 ~02:52–03:00 UTC  
**Overall gate (at probe):** **FAIL** (restructure not live; privacy TestFlight URL still 404)

> **Code status after probe (2026-08-04):** Company home + `/peptodyssey/*` route groups
> and Detect→Design→Deliver copy landed on `main` via PRs #124 / follow-up. This file is
> kept as the **gate checklist + historical probe evidence**. Re-run the live curl table
> after Flux rolls the frontend image before closing deploy/privacy tasks.

This is a **verification** deliverable. At probe time, upstream build/content tasks were
still incomplete in Arete; inventory is now in-repo at [`docs/SITE_INVENTORY.md`](./SITE_INVENTORY.md).

---

## Checklist

| # | Check | Result | Evidence |
|---|--------|--------|----------|
| 1 | `https://flmanbiosci.net/peptodyssey/privacy` → **200** | **FAIL** | HEAD/GET **404** Next.js not-found (also `app.` host). Source on `origin/main` (`05cf429`) but **not** in shipped frontend image. |
| 2 | `/` company homepage with **Detect → Design → Deliver** visible | **FAIL** | `/` **200**, title **“PeptOdyssey — Precision Peptide Genomics”**, product upload UI. No DDD triad. Footer: *Built by Florida Man Bioscience · **v1.0.137***. |
| 3 | `/peptodyssey/` product hub | **FAIL** | `/peptodyssey/` **308** → `/peptodyssey` → **404**. No hub page in tree (only `peptodyssey/privacy/page.tsx`). |
| 4 | Old paths redirect **or** documented broken-with-fix | **PARTIAL / documented** | Restructure **not applied**. Product routes still at apex root (`/tracking`, `/jobs`, `/regulatory`, `/study` = **200**). `www` **301** → apex (OK). No path moves to document as broken yet. |
| 5 | No held-out IP (Harmonia NSF, erv-immune Oxford) or clinical overclaims | **PASS (live surface)** | Grep on `/`, `/study`, `/regulatory`, `/tracking` HTML text: no `harmonia` / `erv-immune` / `NSF` / `Oxford`. `/study` uses ordinary “diagnostic / predictive-accuracy study” language (observational), not held-out IP. No “cure” / FDA-approved-peptide overclaims matched. |

**Sibling notify:** `t-pept-privacy-url` (**Deploy production privacy policy URL**) must stay **open** until check #1 is really **200**. Do **not** close it on this verify.

---

## Live route table (curl)

Probed with `curl -sI` + `curl -sL -o /dev/null -w '%{http_code}|%{url_effective}|%{num_redirects}'`.

| URL | HEAD | Location | GET final | Notes |
|-----|------|----------|-----------|-------|
| `https://flmanbiosci.net/` | 200 | — | 200 | PeptOdyssey product home, v1.0.137 |
| `https://flmanbiosci.net/peptodyssey` | 404 | — | 404 | No hub |
| `https://flmanbiosci.net/peptodyssey/` | 308 | `/peptodyssey` | 404 (1 redir) | Trailing-slash normalize then miss |
| `https://flmanbiosci.net/peptodyssey/privacy` | **404** | — | **404** | **TestFlight gate** |
| `https://app.flmanbiosci.net/` | 200 | — | 200 | Same product UI |
| `https://app.flmanbiosci.net/peptodyssey/privacy` | 404 | — | 404 | Same lag |
| `https://www.flmanbiosci.net/` | 301 | `https://flmanbiosci.net:443/` | 200 | Canonical host OK |
| `https://www.flmanbiosci.net/peptodyssey/privacy` | 301 | apex privacy | 404 | Redirect OK; target still 404 |
| `https://flmanbiosci.net/tracking` | 200 | — | 200 | Pre-restructure product path |
| `https://flmanbiosci.net/regulatory` | 200 | — | 200 | |
| `https://flmanbiosci.net/study` | 200 | — | 200 | |
| `https://flmanbiosci.net/jobs` | 200 | — | 200 | |
| `https://flmanbiosci.net/privacy` | 404 | — | 404 | No root privacy |
| `https://flmanbiosci.net/analyze` | 404 | — | 404 | Analyze is API, not FE route |
| `https://api.flmanbiosci.net/health` | 405 on HEAD | — | **200** GET | API up |

### `/` body signals

- Title: `PeptOdyssey — Precision Peptide Genomics`
- Hero themes: genome upload, peptide map, Bayesian response prediction
- **Absent:** company who/what block, Detect→Design→Deliver, FMB corporate nav
- Version string in footer HTML: `v<!-- -->1.0.137`

### Privacy body signals

- Title: `404: This page could not be found.`
- Next.js `_not-found` shell with PeptOdyssey chrome

---

## Source vs production

| Artifact | State |
|----------|--------|
| Next privacy page | `frontend/src/app/peptodyssey/privacy/page.tsx` on **`origin/main`** @ `05cf429` (2026-07-16) *and* later tip `15f845b` (version.json **1.0.142**) |
| Worktree HEAD | `05cf429` (this kanban tree); privacy file present |
| Static marketing privacy | `fmb-website` `peptodyssey/privacy/index.html` @ `d97fbdc` / docs `666f000` |
| Apex HTTPRoute | `iac/.../theswamp/httproute.yaml`: `/*` → **u4u-engine-frontend only** (fmb-website **not** wired) |
| Live frontend version | **1.0.137** (behind main 1.0.142) |
| Related main-only routes also dark | `/faq`, `/tracking/diagnostics` → live **404** (consistent image lag) |

### Root cause: frontend container CI red since privacy ship

Workflow **build and push frontend container** has failed on **every** `main` push checked after the last green (PR #93 era), including:

- `feat: host PeptOdyssey iOS privacy policy…` → run `29524821664` (2026-07-16) **failure**
- Latest sampled: PR #122 merge → run `30658423914` (2026-07-31) **failure**

Build log pattern (both runs):

1. `✓ Compiled successfully`
2. `Running TypeScript ...`
3. *“It looks like you're trying to use TypeScript but do not have the required package(s) installed.”* → Next auto-installs `typescript`
4. Peer hell (`typescript@7` vs `typescript-eslint` wanting `<6.1.0`, eslint 10 vs plugins wanting ≤9)
5. `npm run build` **exit 1** → no new image → Flux keeps old digest → live stays on **v1.0.137** without `/peptodyssey/privacy`

Last green frontend push found: **Merge PR #93** run `29156707937` (2026-07-11).

fmb-website Zot push also **failed** on privacy commits (`29524761228`, `29524820646`) — static path would not have rescued apex anyway while HTTPRoute points only at Next.

---

## Restructure status (why checks 2–4 fail)

Plan pipeline (all **open / 0%** at verify time):

1. `t-fmbweb-inventory` — inventory doc exists in worktree `t_f12a9f1a`
2. `t-fmbweb-ia` → `t-fmbweb-content` → `t-fmbweb-implement-routes` → `t-fmbweb-homepage`
3. **`t-fmbweb-verify-deploy`** (this task) — verification complete; **gate red**
4. `t-fmbweb-done` — blocked on green verify

Desired end state (plan): `/` = FMB company home (DDD); `/peptodyssey/*` = product tree; privacy URL preserved at **200**.

Today: dual-repo reality documented in SITE_INVENTORY — marketing HTML in `fmb-website` is **offline** relative to DNS; product Next owns apex.

---

## Held-out IP / claims scan (method)

```text
Pages: /, /study, /regulatory, /tracking
Patterns: harmonia, erv-immune, NSF, Oxford, cure, diagnos*, FDA-approved peptide,
          treats cancer/disease, clinically proven, guaranteed
```

Result: no held-out portfolio strings. Study page “diagnostic” = study-type wording only.

---

## Raw curl samples

```text
$ curl -sI https://flmanbiosci.net/
HTTP/2 200
content-type: text/html; charset=utf-8
x-powered-by: Next.js
...

$ curl -sI https://flmanbiosci.net/peptodyssey/privacy
HTTP/2 404
content-type: text/html; charset=utf-8
x-powered-by: Next.js
cache-control: private, no-cache, no-store, max-age=0, must-revalidate
...

$ curl -sI https://flmanbiosci.net/peptodyssey/
HTTP/2 308
location: /peptodyssey
...

$ curl -sI https://www.flmanbiosci.net/
HTTP/2 301
location: https://flmanbiosci.net:443/
...

$ curl -sL -o /dev/null -w '%{http_code} %{url_effective}\n' https://api.flmanbiosci.net/health
200 https://api.flmanbiosci.net/health
```

Full multi-URL dump also captured during this run under agent temp (`/tmp/fmb-verify-curls.txt` on worker host; not committed).

---

## Hand-off — exact steps for Noah (prod privacy 200 + later cutover)

### A. Unblock TestFlight privacy (priority; enables `t-pept-privacy-url`)

1. **Fix frontend Docker/CI build** in `Florida-Man-Bioscience/u4u-engine`:
   - Ensure `typescript` (supported major, likely **5.x** not auto-pulled 7) is a real installable dep for `npm ci` inside `frontend/Dockerfile` builder (today Next reports TS missing at typecheck).
   - Align `eslint` / `eslint-config-next` peers so `npm run build` does not exit 1 after compile.
   - Reproduce: `cd frontend && docker build -t u4u-fe:test .` (or re-run workflow `build-and-push-frontend.yml` on main after fix).
2. Confirm GH Actions **build and push frontend container** is **green** on `main` and pushes `zot.hwcopeland.net/florida-man-bioscience/u4u-engine-frontend:main`.
3. Wait for Flux ImageUpdateAutomation to rewrite  
   `iac/rke2/tooling/flux/theswamp/deployment-frontend.yaml` digest (or manually verify rollout if you have cluster access per `docs/server-management.md` / `ACCESS.md`).
4. Re-probe:

```bash
curl -sI https://flmanbiosci.net/peptodyssey/privacy | head -1   # expect HTTP/2 200
curl -sL https://flmanbiosci.net/peptodyssey/privacy | head -c 200
# footer version should advance past 1.0.137
```

5. When **200**, close/update **`t-pept-privacy-url`** and re-check row 1 of this checklist.

**No DNS change required** for privacy-only fix — path already hits Next frontend.

### B. Full restructure gate (checks 2–4) — not this verify’s code scope

1. Finish IA/content/routes/homepage tasks in plan order (or accept inventory + ship minimal path split).
2. Decide ownership: path-split HTTPRoute (static `fmb-website` on `/` + Next under `/peptodyssey` and/or `app.`) **or** pure Next multi-tree.
3. Implement redirects for any product URLs that move off apex root.
4. Re-run this VERIFY checklist; only then mark `t-fmbweb-done`.

### C. Credentials / access

- Cluster/Zot/Flux: collaborator path in iac `ACCESS.md` / `docs/server-management.md` (not exercised by this agent).
- No secrets were required for **read-only** public curl verification.

---

## Deliverables

| Item | Path / ref |
|------|------------|
| This report | `docs/VERIFY.md` (this file) |
| Prior inventory | `u4u-engine/.worktrees/t_f12a9f1a/docs/SITE_INVENTORY.md` |
| Privacy source (Next) | `frontend/src/app/peptodyssey/privacy/page.tsx` @ `05cf429` |
| Privacy source (static) | `~/fmb-website/peptodyssey/privacy/index.html` |
| Failed FE CI (privacy) | https://github.com/Florida-Man-Bioscience/u4u-engine/actions/runs/29524821664 |
| Failed FE CI (latest sampled) | https://github.com/Florida-Man-Bioscience/u4u-engine/actions/runs/30658423914 |

---

## Gate decision

| Question | Answer |
|----------|--------|
| Can we call the website restructure **done**? | **No** |
| Is production privacy URL shippable for TestFlight? | **No** (404) |
| Is verify work itself complete? | **Yes** — evidence + checklist + hand-off steps |

*Generated for Arete `t-fmbweb-verify-deploy` / Hermes kanban `t_0a90b71d`.*
