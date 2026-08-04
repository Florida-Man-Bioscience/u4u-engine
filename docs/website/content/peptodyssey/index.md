---
title: PeptOdyssey
description: >-
  Genome-informed peptide dossiers, consented HealthKit capture, and the web
  tools behind Florida Man Bioscience’s Stage A measurement loop.
canonical: https://flmanbiosci.net/peptodyssey/
status: draft-for-impl
plan_task: t-fmbweb-content
privacy_path: /peptodyssey/privacy
privacy_canonical: https://flmanbiosci.net/peptodyssey/privacy
claims_posture: >-
  Research / product measurement tool and decision-support information.
  Not a medical device. Not medical advice. Prescriber-in-the-loop.
---

<!--
  Product hub one-pager for /peptodyssey/ (+ trailing slash).
  Preserve/relocate PeptOdyssey-specific content under this tree.
  Privacy leaf path is FROZEN — never rename.
-->

# PeptOdyssey

**Eyebrow:** Precision peptide genomics · Florida Man Bioscience  
**Tagline (product UI):** PeptOdyssey — Precision Peptide Genomics

**Lead**

PeptOdyssey is the **patient-facing layer** of Florida Man Bioscience’s Stage A
loop: it turns a genome-derived prediction into a clear, individualized
**dossier**, and — via the iOS research app — captures the consented biomarkers
that feed the **Tracker**.

**Name logic:** *Pept*ide + *Odyssey* — the patient’s individualized journey
through peptide therapy, made legible.

**CTAs**

| Action | Path | Status note |
|--------|------|-------------|
| **Privacy policy** | [`/peptodyssey/privacy`](/peptodyssey/privacy) | **Frozen URL** — App Store / TestFlight pin. Must remain HTTP 200. |
| **Run a genome analysis** | Today: `/` · IA target: `/peptodyssey/analyze` | Web upload (VCF / consumer genotype / CSV) |
| **Analysis history** | `/jobs` · IA: `/peptodyssey/jobs` | Job status + results |
| **Biomarker tracking** | `/tracking` · IA: `/peptodyssey/tracking` | Longitudinal tracker UI |
| **Regulatory dashboard** | `/regulatory` | Curated + live peptide regulatory context |
| **Validation study** | `/study` | Informational only — **pending IRB, not recruiting** |
| **Company home** | `/` (after restructure) | Florida Man Bioscience |
| **Contact** | `mailto:noahtjones@gmail.com` | Privacy + product questions |

---

## What PeptOdyssey is

### 1. The dossier (report)

For each person, PeptOdyssey translates **PeptidIQ** engine findings into:

- **Individualized peptide options** — candidates whose biology is relevant to
  this genome.
- **Safety flags** — receptor-, PGx-, and axis-level cautions surfaced for a
  **prescriber**.
- **Rationale** — plain-English *why*, not a black box.
- **Expected biomarkers** — what to measure and what direction of change the
  model is watching (priors for the Tracker).
- **Citations** — evidence behind each call.

Delivered as a **printed** clinic-friendly artifact and a **digital** report.
Machine shape is frozen as **DossierV0** (Stage A): options, flags, biomarkers,
citations, `engineVersion`, and a non-diagnostic disclaimer. **No efficacy
percentages** in v0.

### 2. The iOS research app (capture)

Native iOS app that:

- Runs a **consent gate** before any HealthKit read.
- Collects consented Apple Health samples (activity, vitals, sleep, nutrition,
  body measurements, and other granted types — see privacy policy).
- Enrolls a device, queues samples on-device, and uploads over **HTTPS/TLS** to
  the research backend (`https://flmanbiosci.net/api/v1`).
- Feeds the **Tracker** measurement loop.

**What the app is not:** a medical device; it does not diagnose, treat, cure, or
prevent any disease. Data is **not sold** and **not used for advertising**.

### 3. Web analysis tools (today on flmanbiosci.net)

The production Next.js app currently exposes:

| Surface | Purpose |
|---------|---------|
| Genome upload | `POST /analyze` job queue → results |
| Results | Tabs: **PGx** (default), peptides, variants |
| Tracking | Longitudinal biomarkers + Bayesian predictions |
| Regulatory | FDA peptide status dashboard |
| Study | Observational pipeline-validation study info |

IA moves the **company** story to `/` and nests these tools under
`/peptodyssey/*` while preserving bookmarks via redirects (see `docs/website/IA.md`).

---

## How it fits the Stage A loop

```
raw genome ─► PeptidIQ ─► DossierV0 ─► PeptOdyssey (human) ─► biomarkers ─► Tracker
                 │                          │
                 │                          └── expectedBiomarkers priors ──► Tracker
                 └── (engine API: POST /analyze, GET /jobs/{id})
```

- **PeptidIQ** (`u4u-engine`) computes the genetic prior / structured prediction.
- **PeptOdyssey** explains it and measures follow-up.
- **Tracker** refines the prediction over time (Bayesian update).
- **Protein Chemistry** design/viz is a separate Stage A surface — **not** wired
  to HealthKit subject IDs (deliberate non-integration).

---

## Privacy (required subpage)

| Item | Value |
|------|--------|
| **Canonical URL** | `https://flmanbiosci.net/peptodyssey/privacy` |
| **Path freeze** | Leaf name **`privacy`** under `/peptodyssey/` — do not rename or 301-away as sole target |
| **Production implementation (apex)** | `u4u-engine` Next route: `frontend/src/app/peptodyssey/privacy/page.tsx` |
| **Static mirror** | `fmb-website/peptodyssey/privacy/index.html` (not currently on apex HTTPRoute) |
| **App pin** | `peptodyssey` → `AppLinks.privacyPolicy` / `docs/PRIVACY.md` |
| **Policy status** | Operational draft for TestFlight / App Store disclosure; **counsel review open** |
| **Last updated (draft)** | 16 July 2026 · Version 1 |
| **Contact** | noahtjones@gmail.com |

Hub footer **must** link Privacy. Material policy edits require human/legal
review — not drive-by marketing changes.

> **Ops note (inventory 2026-08-03 / IA 2026-08-04):** live apex returned **404**
> for `/peptodyssey/privacy` while source exists on `main` (`05cf429`) — treat
> restoring HTTP 200 as P0 for TestFlight, independent of hub copy polish.

---

## Ship-readiness (honest status)

| Capability | Status (from product docs, mid-2026) |
|------------|--------------------------------------|
| Consent gate + HealthKit catalog + upload pipeline | Shipped in app repo |
| Privacy URL configured (not example.com) | Configured → must be **200** in prod |
| App Store nutrition label | Drafted |
| DossierV0 schema | **Frozen** |
| Live PeptidIQ → app dossier fetch | **Not wired** (fixture / placeholder UI) |
| TestFlight in external tester hands | **Open** (obligation `peptodyssey-testflight`) |
| Capture → Tracker end-to-end product loop | **Partial** |
| Counsel sign-off on privacy | **Open** |

Marketing on this hub should match the table: primary public door is real web
tools + privacy + study info; iOS is a **research capture** front door heading
toward TestFlight, not a promised App Store therapeutic product.

---

## Related PeptOdyssey content to preserve under this tree

| Existing content | Proposed home after restructure |
|------------------|----------------------------------|
| Privacy policy page | `/peptodyssey/privacy` (**unchanged path**) |
| Genome upload landing (current `/`) | `/peptodyssey/analyze` (or `app.flmanbiosci.net/`) |
| Jobs + results | `/peptodyssey/jobs…` |
| Tracking UI | `/peptodyssey/tracking…` |
| Study pages | `/peptodyssey/study…` (keep top-level 301) |
| Regulatory dashboard | Prefer `/peptodyssey/regulatory` + alias |
| Static dossier HTML samples in engine repo (`dossier.html`, `dossier_report.html`) | Internal/design artifacts — link only if intentionally public |
| Dropbox `Dossier_PeptOdyssey.pdf` | Design reference; not auto-published |

---

## Claims callouts (hub page)

- Dossier = **information and rationale** for clinician judgment.
- No guaranteed outcomes; confidence and evidence, not certainty.
- iOS app = research / product measurement collection with consent.
- Study page is **not** a solicitation to enroll while IRB is pending.
- Do not invent clinic partners, pricing, or efficacy stats.

---

## GAPS — Noah / Curtis / counsel

| ID | Gap |
|----|-----|
| P1 | Public “ship-ready” language for iOS vs “research / TestFlight” honesty |
| P2 | Whether hub leads with **web analyze** or **iOS capture** as primary CTA |
| P3 | Counsel close on privacy before broad distribution |
| P4 | Clinician validation of dossier layout (open product to-do) |
| P5 | Live engine→dossier wiring messaging once it ships |
| P6 | Confirm secondary links (regulatory, study) in product nav |

---

*Draft assembled for `t-fmbweb-content`. Build hub UI in follow-on implementation task.*
