# flmanbiosci.net route ownership

Production apex `https://flmanbiosci.net` is served by the **u4u-engine Next.js
frontend** (Cilium Gateway → frontend Deployment). The sibling **fmb-website**
static nginx image is **not** on the public apex path today; keep it aligned as
a marketing source of truth and local compose preview (`docker compose` service
`website` on `:8080` when present).

## Who owns which path (production = Next)

| Path | Owner (prod) | Notes |
|------|--------------|--------|
| `/` | u4u-engine Next `(marketing)/page.tsx` | Florida Man Bioscience company home (copy from fmb-website) |
| `/peptodyssey` | u4u-engine Next | PeptOdyssey product hub |
| `/peptodyssey/analyze` | u4u-engine Next | Genome upload / analysis (legacy product home) |
| `/peptodyssey/privacy` | u4u-engine Next | **TestFlight / App Store privacy URL — must HTTP 200** |
| `/jobs`, `/tracking`, `/regulatory`, `/study`, `/faq`, … | u4u-engine Next | Product tools (linked from hub; URLs unchanged) |
| `/api/v1/*` | u4u-engine API | Gateway rewrite to backend `/` |
| `/privacy`, `/analyze`, `/upload`, `/new` | Next redirects | Permanent redirects into `/peptodyssey/*` |

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
```

Hit:

- [ ] `GET /` → company home (FMB brand, not genome upload)
- [ ] `GET /peptodyssey` → product hub
- [ ] `GET /peptodyssey/analyze` → genome upload UI
- [ ] `GET /peptodyssey/privacy` → privacy policy **200**
- [ ] `GET /privacy` → **308/301** → `/peptodyssey/privacy`
- [ ] `GET /analyze` → **308/301** → `/peptodyssey/analyze`
- [ ] `GET /jobs`, `/tracking`, `/faq` still 200
- [ ] Nav brand → `/peptodyssey`; “Florida Man Bioscience” → `/`

Production cutover: merge PR to `main` → CI image → Flux pin update. Do **not**
force-push main. After deploy, re-check
`https://flmanbiosci.net/peptodyssey/privacy` returns 200 (was 404 while the
deployed frontend image lagged the tree that already contained the page).
