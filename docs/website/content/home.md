---
title: Florida Man Bioscience
description: >-
  Peptide medicine, matched to the genome. Genome-aware response prediction,
  longitudinal biomarker tracking, and a long-horizon delivery research track.
canonical: https://flmanbiosci.net/
status: draft-for-impl
plan_task: t-fmbweb-content
claims_posture: >-
  Decision-support information for clinicians and research tooling.
  Not a medical device. Does not diagnose, treat, cure, or prevent disease.
  Prescriber-in-the-loop. No outcome guarantees.
---

<!--
  Drop-in markdown/MDX for company homepage (/).
  Assembled ONLY from existing FMB sources — see SOURCES.md and GAPS section.
  Softened marketing phrases that read as clinical direction (see SOURCES L1).
-->

# Peptide medicine, *matched to the genome.*

**Eyebrow:** Precision peptide therapeutics

**Lead**

We build the analytics, the trackers, and the delivery platform behind
next-generation peptide therapy — so each patient can get the right peptide
at the right dose *for them*, and the system learns from every measurement.

**Primary CTA:** [Explore PeptOdyssey →](/peptodyssey/)  
**Secondary CTA:** [Partner with us](mailto:hello@flmanbiosci.net)

---

## 1. Who we are

**Florida Man Bioscience** builds peptide-led precision medicine as a **system**,
not a one-off report.

We treat peptide therapy as a **closed feedback loop** (internal platform name
**U4U**):

1. **Read** the patient’s genome.
2. **Predict** peptide and hormone response (**PeptidIQ**).
3. **Report** clear, individualized options (**PeptOdyssey** dossier).
4. **Track** biomarkers over time and refine the prediction (**Tracker**).
5. **Deliver** — long horizon — molecule delivery research (**MSP nanodisks**).

The **software loop is real and in active development**
([u4u-engine](https://github.com/Florida-Man-Bioscience/u4u-engine),
[peptodyssey](https://github.com/Florida-Man-Bioscience/peptodyssey)).
The delivery layer is **research-stage**.

**One line:** Peptide medicine, matched to the genome — and it gets smarter
every time a patient is measured.

**Contact:** [hello@flmanbiosci.net](mailto:hello@flmanbiosci.net) ·
[github.com/Florida-Man-Bioscience](https://github.com/Florida-Man-Bioscience)

**Brand voice (from company brand guide):** clear over clever; confident, not
grandiose; human; a little wit is allowed, substance is required. Prefer what
the platform *does* over what it *guarantees*.

> **Team block:** deferred on this draft. Public team names/roles on the current
> static marketing page disagree with the internal company roster (see GAPS).
> Do not ship a team grid until Noah/Curtis confirm attribution.

---

## 2. What we do — Stage A, software-first closed loop

**Stage A** (portfolio framing): a **software-first closed loop** only.
No Stage B/C lab or wet-lab platform claims on this site.

### Products at a glance

| Layer | Name | What it is today |
|-------|------|------------------|
| **Engine** | **PeptidIQ** | Genome → structured peptide/hormone response prediction. Multi-step annotation (variants, pathways, receptor genetics, PGx, polygenic signals, plain-English summaries). Ships as library + API + web tools in `u4u-engine`. |
| **Report + capture** | **PeptOdyssey** | Patient-facing dossier (options, safety flags, rationale, expected biomarkers, citations) **and** iOS HealthKit capture for consented longitudinal samples. Primary public product doorway. |
| **Feedback** | **Tracker** | Bayesian fusion of the genetic prior with measured biomarkers so predictions refine over time — turning each measurement into training data. |
| **Molecule (later)** | **MSP nanodisk delivery** | Research-stage membrane-scaffold-protein nanodisk platform for peptide/nucleic-acid payloads. Not a shipped therapeutic. |
| **Design surface (Stage A)** | **Protein Chemistry** | Structure design/visualization + simulated DBTL tooling (separate product surface). Secondary card only until web copy is ready. |

### Why it is one platform

Each stage feeds the next. The dossier is only as good as the engine; the engine
gets better only when the Tracker returns measured outcomes; delivery is the
long-horizon extension from “which peptide” to “which peptide, where.”
**The integration is the product.**

### Stage A wedge (business posture)

Lead where value is obvious and the regulatory surface is smallest: a
**genome-informed peptide-response dossier** for patients and the clinicians
already working with peptide therapy. Expand into longitudinal tracking; treat
molecule delivery as a later, separate heavyweight pathway.

---

## 3. Philosophy — Detect → Design → Deliver

> **Label status:** “Detect → Design → Deliver” is the **plan-mandated public
> triptych** for the company homepage (`p-01184334`). It is **not** an exact
> historical brand phrase in `fmb-company` / `fmb-website`. Below maps each leg
> onto the canonical internal loop
> **Read → Predict → Report → Track → Deliver**.
> Noah/Curtis should confirm labels vs. publishing the five-step loop as-is
> (see GAPS).

### Detect

**Source map:** *Read* the genome + *measure* biomarkers (labs + consented
HealthKit).

- Ingest raw genome/genotype files into **PeptidIQ**.
- Capture longitudinal health samples via **PeptOdyssey** (consent-gated) and
  clinic labs.
- Goal: stop leaving genomes idle and stop treating every visit as a blank slate.

### Design

**Source map:** *Predict* + *Report* individualized options for a **prescriber
in the loop**.

- Score variants across pharmacogenomics, receptor genetics, pathway and
  peptide-relevant biology.
- Produce a **PeptOdyssey** dossier: peptide options, safety flags, plain-English
  rationale, expected biomarkers, citations — information and rationale for
  clinical judgment, **not** a treatment directive to a patient.
- Stage A also includes a **structure design / viz** surface (Protein Chemistry)
  for in silico design loops; keep it secondary on the company home until
  dedicated copy exists.

### Deliver

**Source map:** *Track* (learn from every measurement) + long-horizon *Deliver*
(molecule).

- **Near term:** the **Tracker** closes the software loop — Bayesian updates
  fuse genetic priors with measured response so the system improves with use.
- **Long horizon:** **MSP nanodisk** research aims at getting peptide and
  nucleic-acid payloads across tissue barriers. Research-stage only; no
  approved-product or efficacy claims.

```
Detect                    Design                         Deliver
──────                    ──────                         ───────
genome + biomarkers  →    predict + individualized   →   learn over time
                          dossier (clinician loop)       (+ molecule R&D later)
```

---

## 4. CTAs and product links

### Primary

| Action | Link | Notes |
|--------|------|--------|
| **PeptOdyssey hub** | [`/peptodyssey/`](/peptodyssey/) | Primary ship-facing doorway (dossier + app + web tools story) |
| **Privacy (frozen path)** | [`/peptodyssey/privacy`](/peptodyssey/privacy) | App Store / TestFlight pin — **must stay HTTP 200** |
| **Analyze (genome upload)** | Today live at `/` tool UI; IA target [`/peptodyssey/analyze`](/peptodyssey/analyze) | Implementation task moves tool off company root |
| **Tracking UI** | [`/tracking`](/tracking) (IA: nest under `/peptodyssey/tracking`) | Biomarker tracking product surface |
| **Study (informational)** | [`/study`](/study) | Observational pipeline validation — **pending IRB / not recruiting** |
| **Contact / partner** | `mailto:hello@flmanbiosci.net` | Clinics, collaborators, investors |

### Secondary (cards only — no fake “Launch app”)

| Card | Status of public copy |
|------|------------------------|
| PeptidIQ engine | Describe; deep-link analyze/docs |
| Tracker | Deep-link tracking |
| MSP nanodisk delivery | Research description only |
| Neuro-creatine / CNS peptides | Early discovery track (from static marketing site) |
| Protein Chemistry / CytoGate / genomics SaaS | Placeholders until real web copy exists |

### Footer tagline (from marketing site)

> Peptide-led precision medicine. Built in Florida, opened to the world.

---

## Claims & compliance callouts (must render near product CTAs)

- Tools and reports are **information / research / decision-support**, not a
  substitute for clinical judgment.
- **Licensed prescriber in the loop** for any therapy decision.
- Say what the system **does** (annotate, score, assemble evidence, track) —
  not what it **guarantees** (outcomes).
- PeptOdyssey iOS app: **not a medical device**; does not diagnose, treat, cure,
  or prevent disease (privacy policy language).
- MSP nanodisk / delivery: **research-stage**, not a marketed drug.
- Privacy policy remains a **counsel-review-open** operational draft.

---

## GAPS — need Noah / Curtis voice (do not fabricate)

| ID | Gap | Why blocked |
|----|-----|-------------|
| G1 | Confirm **Detect → Design → Deliver** labels vs public five-step loop | Phrase is plan-mandated; not found verbatim in brand/KB |
| G2 | **Team grid** (names, titles, photos, who is “CEO”) | `fmb-website` lists Curtis as Founder & CEO; `fmb-company/company/team.md` lists Noah as Founder/CEO — do not pick |
| G3 | Hero tone: keep “right peptide at the right dose” or soften further | Claims posture prefers decision-support over dosing language |
| G4 | Public mention of **Arete Holdings** / portfolio structure | Internal docs only unless cleared for marketing |
| G5 | Pricing, raise/ask, clinic partner names | Explicit `[TBD]` in business plan |
| G6 | Whether to surface **peptide evidence grades** (A–D) on company home | Present on current Next product landing; easy to over-read as endorsement |
| G7 | Neuro-creatine / CNS discovery depth on public site | Marketing block exists; science narrative thin for external |
| G8 | Final legal sign-off on health-data and therapeutic-adjacent marketing | See `regulatory/clinical-and-claims.md`, privacy counsel banner |

---

*Draft assembled for `t-fmbweb-content`. Implementation: `t-fmbweb-homepage`.*
