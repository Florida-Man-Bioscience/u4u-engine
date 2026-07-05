# PeptOdyssey Frontend

The web UI for the u4u-engine peptide-genomics platform. A [Next.js](https://nextjs.org)
16 app (App Router, React 19, Tailwind CSS v4, Recharts), deployed in production at
`https://flmanbiosci.net`.

A fuller walkthrough of the routes, data flow, and components lives in
[`../docs/frontend.md`](../docs/frontend.md).

## Backend connection

Browser API calls go through `src/app/lib/api.ts` / `authFetch.ts`. The base URL is
`process.env.NEXT_PUBLIC_API_BASE`, defaulting to **`/api/v1`** (the gateway rewrites
`/api/v1/*` to the backend). For local dev against a backend on another host, set it
explicitly:

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

## Routes

| Route | Purpose |
|-------|---------|
| `/` | Genome upload / new analysis |
| `/jobs` | Analysis history |
| `/jobs/[id]` | Job status / progress polling |
| `/jobs/[id]/results` | Results — tabs `peptides \| pgx \| variants` (`pgx` default) |
| `/tracking`, `/tracking/cohort`, `/tracking/model` | Longitudinal biomarker tracking + model explainer |
| `/tracking/patients/[id]`, `.../onboard` | Patient detail + onboarding wizard |
| `/regulatory` | FDA peptide regulatory dashboard (SSR) |
| `/study`, `/study/dev` | Observational validation study pages |

## Development

```bash
npm install
npm run dev      # dev server on http://localhost:3000
npm run build    # production build (Next standalone output)
npm run start    # serve the production build
npm run lint     # eslint
```

## Deployment

Dockerized (multi-stage build, Next standalone output) and deployed to the RKE2
Kubernetes cluster via Flux GitOps. Pushing to `main` triggers CI to build/push a new
image; Flux rolls it out. See the repo root `CLAUDE.md` and `docs/server-management.md`.
