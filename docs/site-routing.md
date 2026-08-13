# flmanbiosci.net route ownership

Production apex `https://flmanbiosci.net` is served by the **u4u-engine Next.js
frontend** (Cilium Gateway → frontend Deployment). The sibling **fmb-website**
static nginx image is **not** on the public apex path today; keep it aligned as
a marketing source of truth and local compose preview (`docker compose` service
`website` on `:8080` when present).

## Host matrix (target vs today)

| Host | Role | Status (2026-08-13) |
|------|------|---------------------|
| `flmanbiosci.net` | Company marketing at `/`; product tree still served here until product DNS | **Live** |
| `www.flmanbiosci.net` | 301 → apex | Live |
| `app.flmanbiosci.net` | Product mirror (same Next FE) | **Live** (privacy 200) |
| `peptodyssey.flmanbiosci.net` | Canonical product UI + `/api/v1` | **DNS NXDOMAIN** until iac [PR #96](https://github.com/hwcopeland/iac/pull/96) merges + Cloudflare operator applies CNAME |
| `api.flmanbiosci.net` | Legacy API (unprefixed) | Live |
| `cytogate` / `u4u-privacy` / lab landings | Portfolio static | DNS pending same iac cutover |

**Do not enable FE-only 301s from apex → `peptodyssey.*` before that host resolves.**
Cross-host redirects ship in **gateway HTTPRoute** together with DNS (iac).

## Who owns which path (production = Next on apex / app today)

| Path | Owner (prod today) | Notes |
|------|--------------------|--------|
| `/` | u4u-engine Next `(marketing)/page.tsx` | Florida Man Bioscience company home (DDD) |
| `/peptodyssey` | u4u-engine Next | PeptOdyssey product hub |
| `/peptodyssey/analyze` | u4u-engine Next | Genome upload / analysis |
| `/peptodyssey/privacy` | u4u-engine Next | **TestFlight / App Store frozen URL — must HTTP 200** (or 301→200 only after product DNS) |
| `/privacy` | Next redirect → `/peptodyssey/privacy` | Bookmark helper (`next.config.ts`) |
| `/jobs`, `/tracking`, `/regulatory`, `/study`, `/faq`, … | u4u-engine Next | Product tools |
| `/api/v1/*` | u4u-engine API | Gateway rewrite to backend `/` (same-origin; no cross-host 301) |

### After iac product-host cutover (target)

| Path / host | Owner |
|-------------|--------|
| `https://peptodyssey.flmanbiosci.net/*` | Product UI (Authentik → `u4u-edge`) |
| `https://peptodyssey.flmanbiosci.net/privacy` | Canonical privacy **200** |
| `https://flmanbiosci.net/peptodyssey/privacy` | Gateway **301** → product `/privacy` (freeze OK if final is 200) |
| `https://flmanbiosci.net/` | Company marketing only |
| Company `/jobs`, `/peptodyssey`, … | Gateway **301** → product host |

Companion: `frontend/src/lib/site.ts`, `frontend/src/middleware.ts` (product-host alias only).

## fmb-website (static)

| Path | File | Role |
|------|------|------|
| `/` | `index.html` | Original marketing home (source for company copy) |
| `/peptodyssey/privacy/` | `peptodyssey/privacy/index.html` | Parallel privacy HTML — keep text in sync with Next page |

When the privacy policy changes, update **both**:

1. `frontend/src/app/(product)/peptodyssey/privacy/page.tsx` (production)
2. `fmb-website/peptodyssey/privacy/index.html` (static twin)

## Local preview checklist

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
# or: npm run build && npm run start
```

Hit:

- [ ] `GET /` → company home (FMB brand, Detect→Design→Deliver, not bare upload)
- [ ] `GET /peptodyssey` → product hub **200**
- [ ] `GET /peptodyssey/analyze` → genome upload UI **200**
- [ ] `GET /peptodyssey/privacy` → privacy policy **200** (TestFlight gate)
- [ ] `GET /privacy` → **308/301** → `/peptodyssey/privacy` → **200**
- [ ] `GET /analyze` → **308/301** → `/peptodyssey/analyze`
- [ ] `GET /jobs`, `/tracking`, `/faq` still **200** on same host
- [ ] Nav brand → `/peptodyssey`; “Florida Man Bioscience” → `/`
- [ ] FE must **not** 301 apex product paths to `peptodyssey.flmanbiosci.net` while that name NXDOMAINs

## Production cutover

1. Merge FE PR to `main` → CI image → Flux pin (this repo).
2. **Human / cluster-admin:** merge [hwcopeland/iac#96](https://github.com/hwcopeland/iac/pull/96) so `peptodyssey.flmanbiosci.net` CNAME + product HTTPRoute land **before** re-enabling apex→product gateway redirects in a way that drops apex content.
3. Re-check:
   - `curl -sS -o /dev/null -w '%{http_code}\n' https://flmanbiosci.net/peptodyssey/privacy` → **200** *or* 301 then final 200
   - `curl -sS -o /dev/null -w '%{http_code}\n' https://peptodyssey.flmanbiosci.net/privacy` → **200**
4. Do **not** force-push main.

### Why privacy broke (2026-08 post-#146)

u4u-engine shipped Next middleware that 301’d
`https://flmanbiosci.net/peptodyssey/privacy` →
`https://peptodyssey.flmanbiosci.net/privacy` while product DNS was still
NXDOMAIN (iac #96 open). Fix: serve frozen path on apex until gateway+DNS
cutover is atomic.
