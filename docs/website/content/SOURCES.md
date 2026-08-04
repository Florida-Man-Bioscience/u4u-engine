# SOURCES — homepage + PeptOdyssey hub copy

**Plan task:** `t-fmbweb-content` (kanban `t_840e118e`)  
**Project:** `p-01184334` FMB website (flmanbiosci.net) restructure  
**Draft date:** 2026-08-04  
**Worktree:** `/home/noahtjones/u4u-engine/.worktrees/t_840e118e`  
**Deliverables:**

| File | Role |
|------|------|
| [`home.md`](./home.md) | Company homepage sections (MDX-ready) |
| [`peptodyssey/index.md`](./peptodyssey/index.md) | `/peptodyssey/` product hub |
| this file | Citations + gaps + risk flags |
| [`../IA.md`](../IA.md) | Route map / philosophy mapping (from `t-fmbweb-ia`; copied into this tree) |

**Method:** Assemble real copy from Dropbox + repos. Do **not** invent brand voice
or clinical claims. Where the plan asks for **Detect → Design → Deliver**, map
explicitly from the internal five-step loop (see §3).

---

## 1. Preferred structured sources (used heavily)

| Path | What was taken |
|------|----------------|
| `/home/noahtjones/fmb-website/index.html` | Hero, platform cards (PeptidIQ / PeptOdyssey / Tracker), programs (MSP nanodisk, neuro-creatine), CTAs, footer tagline, meta description, contact email |
| `/home/noahtjones/fmb-website/README.md` | Privacy canonical URL; dual-copy note (static + Next); deploy reality (apex → Next) |
| `/home/noahtjones/fmb-website/peptodyssey/privacy/index.html` | Privacy page structure, counsel banner, “not a medical device” language |
| `/home/noahtjones/fmb-company/README.md` | Company one-paragraph version; repo map; U4U framing |
| `/home/noahtjones/fmb-company/brand/README.md` | Positioning line; voice rules; product naming (PeptidIQ / PeptOdyssey / Tracker / U4U) |
| `/home/noahtjones/fmb-company/business-plan/01-executive-summary.md` | Closed loop Read→Predict→Report→Track→Deliver; why now; wedge; stage; one-liner |
| `/home/noahtjones/fmb-company/business-plan/02-problem-and-opportunity.md` | Problem (prescribed blind); three gaps; flywheel moat |
| `/home/noahtjones/fmb-company/business-plan/03-platform.md` | Platform diagram; four product stages; “integration is the product” |
| `/home/noahtjones/fmb-company/business-plan/05-business-model.md` | Software/report first → tracking → delivery ordering |
| `/home/noahtjones/fmb-company/business-plan/07-go-to-market.md` | Clinic-first wedge; prescriber-in-loop; flmanbiosci.net as front door |
| `/home/noahtjones/fmb-company/product/README.md` | U4U loop; design principle; Stage A product table |
| `/home/noahtjones/fmb-company/product/peptidiq-engine.md` | Engine pipeline map; privacy arm |
| `/home/noahtjones/fmb-company/product/peptodyssey-dossier.md` | Dossier contents; iOS capture status table; DossierV0; privacy URL pin |
| `/home/noahtjones/fmb-company/product/tracker.md` | Bayesian loop; Stage A contracts pointer |
| `/home/noahtjones/fmb-company/product/msp-nanodisk-delivery.md` | Research-stage delivery framing |
| `/home/noahtjones/fmb-company/regulatory/clinical-and-claims.md` | Claims discipline; CDS vs practicing medicine; no guarantees |
| `/home/noahtjones/fmb-company/company/team.md` | Internal founder roster (used only to **flag conflict**, not to invent public titles) |
| `/home/noahtjones/arete-holdings-llc/docs/superpowers/specs/2026-07-16-stage-a-product-contracts.md` | Stage A = software-first closed loop; interface map; non-integrations |
| `/home/noahtjones/arete-holdings-llc/docs/superpowers/plans/2026-07-16-autonomy-operator-os-and-stage-a-products.md` | Stage A product elevation language |
| `/home/noahtjones/u4u-engine/.worktrees/t_ad15f7e7/docs/website/IA.md` | Detect→Design→Deliver **mapping table**; route targets; legal flags L1–L10 |
| `/home/noahtjones/u4u-engine/.worktrees/t_f12a9f1a/docs/SITE_INVENTORY.md` | Live routes; deploy topology; privacy 404 incident; Dropbox index |

## 2. Product / engine / app sources

| Path | What was taken |
|------|----------------|
| `/home/noahtjones/u4u-engine/.worktrees/t_840e118e/frontend/src/app/peptodyssey/privacy/page.tsx` | Production privacy page content + metadata |
| `/home/noahtjones/u4u-engine/.worktrees/t_840e118e/frontend/src/app/page.tsx` | Current product landing stats/pipeline language (reference only; company home should not own upload chrome) |
| `/home/noahtjones/u4u-engine/.worktrees/t_840e118e/docs/frontend.md` | Product name in UI; route table |
| `/home/noahtjones/u4u-engine/.worktrees/t_840e118e/frontend/src/app/study/page.tsx` | IRB pending / not recruiting posture |
| `/home/noahtjones/peptodyssey/README.md` | App purpose; privacy URL; Stage A measurement front door; non-claims |
| `/home/noahtjones/peptodyssey/docs/PRIVACY.md` | (aligned with hosted policy; pin referenced) |
| `/home/noahtjones/peptodyssey/docs/DOSSIER_SCHEMA.md` | DossierV0 fields (via product doc pointers) |

## 3. Dropbox / UF Dropbox (mined carefully)

Root checked:

`/home/noahtjones/UF Dropbox/Noah Jones/Florida Man Bioscience/`  
(also reachable via `/home/noahtjones/Dropbox (UFL)/…` symlink patterns on this host)

| Path / file | Use in this draft |
|-------------|-------------------|
| `…/Florida Man Bioscience/` directory listing | Confirmed decks, PDFs, images, workshop materials exist |
| `…/fmb.org` | Org-mode work log only — **no public marketing copy** extracted |
| `…/Technical Risk and Scientific Plan/Executive_Summary_FloridaManBioscience.txt` | Workshop coaching notes — **not** used as public claims |
| `…/Dossier_PeptOdyssey.pdf` | Noted as design reference for hub “preserve” list — not transcribed into claims |
| `…/PeptidIQ_Pitch_Deck_2026-05-07.pptx`, `pitch_deck.pdf`, strategic plan pptx | **Not** auto-extracted into copy (binary decks; avoid inventing slide claims without human pass) |
| `…/FloridaManBioscience_Workshop2.pdf`, nanodisk reports | Background only; MSP remains research-stage per company product docs |

**Local vault:** `/home/noahtjones/Florida Man Bioscience/` — empty/sparse Obsidian stubs; unused.

**Personal Dropbox** `/home/noahtjones/Dropbox` — no FMB marketing folder found at shallow search; UF Dropbox is the content sink.

---

## 4. Detect → Design → Deliver — provenance

| Phrase | Found as exact public brand line? | Treatment in drafts |
|--------|-----------------------------------|---------------------|
| **Detect → Design → Deliver** | **No** in `fmb-company` / `fmb-website` (IA §2.5) | Used as **plan-mandated** public triptych with explicit map from internal loop |
| **Read → Predict → Report → Track → Deliver** | **Yes** — exec summary + platform | Canonical internal loop quoted/paraphrased |
| Stage A software-first closed loop | **Yes** — Stage A contracts + autonomy plan | Homepage “What we do” framing |

**Public mapping used in `home.md` (from IA §2.5):**

| Public leg | Source legs | Doorways |
|------------|-------------|----------|
| Detect | Read + measure | PeptidIQ, Tracker, PeptOdyssey capture |
| Design | Predict + report (+ design/viz surface) | PeptOdyssey dossier / web results; Protein Chemistry secondary |
| Deliver | Track (learn) + Deliver (molecule R&D) | Tracker; MSP research |

---

## 5. Risk flags (health_data · therapeutic_claims)

| Flag | Mitigation in drafts |
|------|----------------------|
| **therapeutic_claims** | Prescriber-in-loop; information vs advice; no outcome guarantees; research-stage delivery |
| **health_data** | Privacy path + counsel-open banner; consent-gated HealthKit; not sold / no ads |
| **SaMD / CDS** | Point to regulatory posture doc; no autonomous treatment language |
| **Study solicitation** | Keep “pending IRB / not recruiting” |
| **Softened vs fmb-website** | Avoid “platform … prescribes the peptide” as literal clinical act; keep dose language as goal of matching, not a shipped dosing engine claim |
| **Team / ownership** | No invented legal/tax/Arete public wording; team grid blocked on conflict |

---

## 6. Gaps needing Noah / Curtis (and counsel)

Consolidated from `home.md` + `peptodyssey/index.md`:

1. **G1 / L9** — Approve Detect→Design→Deliver labels vs five-step public loop.  
2. **G2 / L8** — Resolve public team titles (Curtis vs Noah as CEO on marketing).  
3. **G3 / L1** — Hero dosing / “right peptide” intensity.  
4. **G4 / L10** — Any public portfolio/Arete mention.  
5. **G5** — Pricing, raise, named design-partner clinics.  
6. **G6 / L6** — Peptide evidence-grade marketing on company vs product pages.  
7. **P1–P3** — iOS ship language, primary hub CTA, privacy counsel close.  
8. **Privacy 200** — Production deploy lag (ops), not a copy invention issue.

---

## 7. What was deliberately *not* written

- Guaranteed clinical outcomes or cure language  
- Invented customer logos, revenue, or market $ figures beyond source placeholders  
- Cap table / unit economics on the public pages  
- Full CytoGate / Neurocreatine product sites  
- Changes to privacy policy body (point only)  
- Production route implementation (homepage build is a later task)

---

## 8. Suggested next tasks

| Task | Consumes |
|------|----------|
| `t-fmbweb-homepage` | `home.md` + `IA.md` |
| PeptOdyssey hub implementation | `peptodyssey/index.md` + privacy preserve |
| Human brand pass (Noah/Curtis) | GAPS lists |
| Privacy deploy verify | SITE_INVENTORY + IA §6 |

---

*End of SOURCES.md*
