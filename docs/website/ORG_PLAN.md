# ORG_PLAN — FMB website + clinic outreach paths

**Date:** 2026-09-05
**Plan task:** `t-fmbweb-tree-dedupe` (kanban `t_8eb67330`)
**Project:** `p-01184334` (FMB website restructure) · clinic pack lives under `p-2c765846`
**Supersedes:** untracked 2026-09-01 `ORG_PLAN.md` from `t-ops-ai-tree-org-wave` (wrongly called `~/fmb-website` the live apex)

Arete frame: Florida Man Bioscience is an opco under holdco `arete-holdings`. This file is path hygiene, not a cap table.

## Keep-canonical

| Role | Path |
|------|------|
| **Live company apex** (`flmanbiosci.net`) | `~/u4u-engine/frontend/src/app/(marketing)/` |
| **Live product UI** | `~/u4u-engine/frontend/src/app/(product)/` |
| Website *drafts* (not served) | `~/u4u-engine/docs/website/content/` |
| Website ops spine | `~/u4u-engine/docs/website/OPS_RUNBOOK.md` |
| **Legacy static** (git-ready, **not** on HTTPRoute) | `~/fmb-website` |
| Company knowledge base | `~/Documents/fmb-company` (there is **no** `~/fmb-company`) |
| **Clinic pipeline SSoT** | `~/Documents/fmb-company/operations/outreach/peptodyssey_partner_offer/tracking/pipeline.csv` |
| Clinic offer pack | `~/Documents/fmb-company/operations/outreach/peptodyssey_partner_offer/` |
| Contacts-verify grid (**not** send SSoT) | `~/Documents/fmb-company/operations/outreach/pipeline.csv` |
| Pitch / dossier corpus | `~/UF Dropbox/Noah Jones/Florida Man Bioscience/` |
| PeptOdyssey iOS | `~/peptodyssey-ios` (do not fold in) |
| Privacy product | `~/u4u-privacy` (do not fold in) |

Edit clinic send-state in **`tracking/pipeline.csv` only**, then `python3 tracking/sync_pipeline_mirrors.py` from the pack. Humans send mail.

## Nested `content/`

| Path | Verdict |
|------|---------|
| `u4u-engine/docs/website/content/` (`home.md`, `SOURCES.md`, `peptodyssey/index.md`) | **Keep.** Draft corpus. Not `content/content/`. |
| `docs/website/content/peptodyssey/` | Child section, not consecutive nesting. |

**Consecutive same-name nest (outside these repos):**

`~/UF Dropbox/Noah Jones/Florida Man Bioscience/Florida Man Bioscience/` — Notion-style export sitting *inside* the Dropbox corpus. Do **not** flatten from this pass (Dropbox sync). Human gate below.

No `path/path` consecutive nesting inside `u4u-engine` (this worktree) or `~/fmb-website`.

## Dual-copy (keep both; do not squash)

| A | B | Canonical / notes |
|---|---|-------------------|
| `~/fmb-website` (HTML/nginx) | `u4u-engine/frontend` (Next) | **Live = Next.** Static README still markets itself as the site; production HTTPRoute does not serve it. |
| `~/fmb-website/peptodyssey/privacy/` | `frontend/.../peptodyssey/privacy` | **Live = Next.** Keep static HTML aligned when the policy changes. |
| `docs/website/content/*` | live `(marketing)` / `(product)` pages | Drafts vs shipped UI. Ship is frontend. |
| `outreach/pipeline.csv` | `peptodyssey_partner_offer/tracking/pipeline.csv` | **SSoT = pack tracking CSV.** Parent file is the 2026-08-15 contacts-verify grid. |
| `outreach/tracking/` (stub README only) | `peptodyssey_partner_offer/tracking/` | Stub says “Tracking moved”. Keep as pointer; do not recreate files here. |
| `pack/outbox/wave1/` + `wave2/` (`intro.md` + `meta.yaml`) | `pack/tracking/outbox/{status}/` | Two different outboxes. Wave folders hold personalized intros. Status folders are CRM-lite drop targets. |
| `pack/outbox/queued_2026-08-18/` (untracked) | wave intros + LinkedIn notes | Send-queue snapshot (emails/, linkedin/, scripts/). Keep until Noah confirms send vs archive. |
| `docs/validation/` vs `validation/` vs `data/validation/` | engine | Complementary (docs / code / fixtures). |

Worktrees: do **not** force-prune. This card uses `u4u-engine/.worktrees/t_8eb67330`. `~/Documents/fmb-company` checkout is currently on abandoned branch `wt/t_4d1f6bec-wave2` (origin gone) plus `.worktrees/t_3250d804`.

## Empty outbox shells

| Path | Files | Action |
|------|-------|--------|
| `pack/tracking/outbox/{not_contacted,draft_ready,queued_send,sent,replied,meeting,nurture,pass,bounce,hold}/` | `.gitkeep` only + parent `README.md` | **Keep.** Contractual status shells from `t-clinic-track-pipeline`, not abandoned trees. Archiving them would break the documented drop path. |
| `pack/outbox/wave1/` (8 clinics) + `wave2/` (10 clinics) | `intro.md` + `meta.yaml` each | **Keep.** Filled. |
| `pack/outbox/replies/` | `README.md` only | **Keep.** Inbox stub, not empty. |
| `u4u-engine` worktree empty dirs | none | — |
| `~/fmb-website` empty dirs | none | — |

**Safe archive this pass:** none. No empty directories were moved or deleted.

## Safe actions this pass

- Wrote this file (and root pointer `ORG_PLAN.md`) on `wt/t_8eb67330`.
- Corrected the 2026-09-01 claim that `~/fmb-website` is the live public site.
- Located clinic `pipeline.csv` (previous pass marked “not found”).
- Did not rewrite live HTML, did not SMTP, did not flatten Dropbox, did not commit in `fmb-company` (stale branch).
- Updated local `~/fmb-website/ORG_PLAN.md` pointer (untracked in that repo).

## Human gates

1. **Dropbox nest** — decide whether to rename `Florida Man Bioscience/Florida Man Bioscience/` (Notion export) so the corpus is one folder deep. Not an agent move.
2. **`fmb-company` git** — checkout is `wt/t_4d1f6bec-wave2` with `origin` gone. Reset to the company default branch before any outreach commit.
3. **`queued_2026-08-18/`** — untracked send-queue. Commit or archive after Noah confirms whether those emails/LinkedIn notes went out.
4. **`~/fmb-website/ORG_PLAN.md`** — still untracked; optional tiny website PR.
5. Do not merge `u4u-privacy` into `u4u-engine`. Do not treat `~/fmb-website` as apex.
