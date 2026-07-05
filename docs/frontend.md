# Frontend

**Read also:** `frontend/README.md` (dev/build commands), `docs/api.md` (API contract), `docs/architecture.md`

The frontend is a shipped, deployed [Next.js](https://nextjs.org) 16 app (App Router,
React 19, Tailwind CSS v4, Recharts). It is served in production at
`https://flmanbiosci.net` alongside the FastAPI backend. Source lives under
`frontend/src/app/`.

Product name in the UI: **PeptOdyssey — Precision Peptide Genomics**.

---

## How it talks to the backend

All browser API calls go through `frontend/src/app/lib/api.ts` and `authFetch.ts`.
The base URL is `process.env.NEXT_PUBLIC_API_BASE`, defaulting to **`/api/v1`**
(the gateway rewrites `/api/v1/*` → backend `/`). Server-rendered routes (e.g.
`/regulatory`) resolve their own base in `regulatory/lib/serverApi.ts`.

Set `NEXT_PUBLIC_API_BASE` for local dev when the backend is elsewhere, e.g.
`NEXT_PUBLIC_API_BASE=http://localhost:8000`.

The core analysis flow is the async job-queue pattern (see `docs/api.md`):

```
POST /analyze              multipart { file } → 202 { job_id }
GET  /jobs/{job_id}        poll → { status, progress, ... , result }
GET  /jobs                 recent job history
GET  /jobs/{id}/pgx        PGx profile for a completed job
```

`run_pipeline()` returns a **dict** (keys: `variants`, `pathway_summary`,
`receptor_genetics`, `prs_profile`, `ar_cag_repeat`, `peptide_recommendations`,
`pgx_profile`, `dossiers`, `acmg_summary`, `analysis_status`). The results page reads
`variants`, `peptide_recommendations`, and `pgx_profile` off that dict.

---

## Routes (the shipped surface)

Every route below has a `page.tsx` under `frontend/src/app/`. The top `Nav`
(`components/Nav.tsx`) links History, Tracking, Regulatory, Study, and New Analysis.

| Route | Purpose |
|-------|---------|
| `/` | **New analysis / upload.** Hero + genome file upload form (`.vcf`, `.txt`, `.csv`, ≤100 MB). `POST /analyze`, then routes to the job page. |
| `/jobs` | **Analysis history.** List of recent jobs with status. |
| `/jobs/[id]` | **Job status / processing.** Polls `GET /jobs/{id}`, shows progress until the job completes, then links to results. |
| `/jobs/[id]/results` | **Results.** Three tabs — `peptides \| pgx \| variants` — with **`pgx` as the default tab**. Tier filter, CSV export, and a "create tracking profile from this job" action (`createPatientFromJob`). |
| `/tracking` | **Biomarker tracking home.** Entry point to the longitudinal tracking UI. |
| `/tracking/cohort` | **Cohort analysis** — pooled cohort view, including dose-response. |
| `/tracking/model` | **Model documentation** — in-app explainer for the peptide-response model (HBRI), inline-SVG data flow mirroring `engine/tracking/bayes.py`. See `docs/models/peptide-response-model.md`. |
| `/tracking/patients/[id]` | **Patient detail** — per-patient measurements with Bayesian predictions per (peptide, biomarker). |
| `/tracking/patients/[id]/onboard` | **Patient onboarding** — multi-stage wizard: engine recommendations → peptide selection → baseline entry. |
| `/regulatory` | **FDA peptide regulatory dashboard** (server-rendered). Curated peptide FDA status merged with live sources; served from `/regulatory/peptides` + `/regulatory/events`. |
| `/study` | **Study landing** — public-facing description of the observational validation study (what it is / is not, participation, privacy). |
| `/study/dev` | **Study detail** — expanded study/methodology page. |

---

## Results page — the three tabs

`/jobs/[id]/results` (`ViewMode = "peptides" | "pgx" | "variants"`, default `pgx`):

- **PGx** (`pgx` — default): the PGx profile (`pgx_profile`) — star-allele calls, CPIC
  phenotypes, and drug recommendations. Rendered by `components/PGxReport.tsx`; drug
  detail via `getDrugDetail`.
- **Peptides** (`peptides`): peptide-therapy recommendations
  (`peptide_recommendations`) — the therapy candidates whose biology aligns with the
  uploaded genome.
- **Variants** (`variants`): the prioritized per-variant findings (`variants`),
  filterable by tier, exportable to CSV. Each variant renders through
  `components/VariantCard.tsx` + `components/TierBadge.tsx`.

Design principle carried over from the original spec: variants are shown as a
**prioritized findings list** (color-coded by tier, plain-English headline + action),
not a card grid. Tiers: `critical` / `high` / `medium` / `low`, plus a carrier
treatment when `carrier_note` is set. Tier and language semantics are documented in
`docs/pipeline.md` and `docs/interpretation.md`.

---

## Key files

| Area | Location |
|------|----------|
| Root layout + Nav | `src/app/layout.tsx`, `src/app/components/Nav.tsx` |
| API client (browser) | `src/app/lib/api.ts`, `src/app/lib/authFetch.ts` (`API_BASE`), `src/app/lib/types.ts` |
| Regulatory SSR client | `src/app/regulatory/lib/serverApi.ts` |
| Shared components | `src/app/components/` — `PGxReport`, `SummaryMetrics`, `TierBadge`, `VariantCard`, `Nav` |
| Build version stamp | `frontend/version.json` (auto-bumped per commit) |

---

## Dev / build

```bash
cd frontend
npm install
npm run dev      # dev server on :3000
npm run build    # production build (Next standalone output)
npm run start    # serve the production build
```

The app is dockerized (multi-stage build, Next standalone output) and deployed to the
RKE2 cluster via Flux GitOps — see `CLAUDE.md` and `docs/server-management.md`.
