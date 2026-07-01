# Peptide → Biomarker Viability Matrix, Assay Feasibility & Accessible Proxies

Clinical/bioinformatic reference for the tracking engine's pharmacodynamic
network. Scope: 20 peptides × 8 target biomarkers. Grounded in the engine's
curated panels (`engine/peptides/biomarkers.py`, `measurements.py`) and the
quantitative effect model (`engine/tracking/biomarker_params.py`).

**Evidence framing (read first).** With three exceptions — the GLP-1/incretin
class (not in this 20), Thymosin Alpha-1 (human trials in HBV/sepsis/COVID), and
Kisspeptin (human reproductive endocrinology) — the efficacy evidence for these
peptides is **predominantly preclinical** (rodent/in-vitro) or mechanistic.
Human RCT data are sparse, and most of these agents are not FDA-approved. The
viability calls below are mechanistic likelihoods, not validated clinical effect
sizes. This is a laboratory-monitoring reference, not clinical or dosing guidance.

### Legend

Viability that the peptide induces a **measurable change** in the biomarker:

| Symbol | Meaning |
|---|---|
| ● | **High** — direct, mechanistically established effect on this readout |
| ◐ | **Moderate** — plausible direct effect; mixed, context-dependent, or partial |
| ○ | **Low** — weak / indirect / speculative |
| **S** | **Safety monitor** — tracked for toxicity; *no expected directional efficacy change* |
| — | **Null** — no credible mechanistic link |

Evidence tier (superscript): `h` human clinical · `p` preclinical (animal/in-vitro) · `m` mechanistic inference only.

Target biomarkers (columns): **VEGF** = serum VEGF (proteomic) · **MMP2** = MMP-2
activity (proteomic) · **αSMA** = hepatic α-SMA expression (transcriptomic) ·
**HA** = serum hyaluronic acid (clinical chem) · **Wnd** = wound closure area
(imaging) · **Hair** = hair density / trichoscopy (imaging) · **ALT** (clinical
chem) · **CBC** = CBC w/ differential (hematology).

---

## Task 1 — Viability matrix

| Peptide | VEGF | MMP2 | αSMA | HA | Wnd | Hair | ALT | CBC |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **TB-500** | ●ᵖ | ●ᵖ | ◐ᵖ | ◐ᵖ | ●ᵖ | ◐ᵖ | S | S |
| **Thymosin Beta-4** | ●ᵖ | ●ᵖ | ◐ᵖ | ◐ᵖ | ●ᵖ | ◐ᵖ | S | S |
| **BPC-157** | ●ᵖ | ○ᵐ | ○ᵖ | — | ●ᵖ | ○ᵐ | S | S |
| **GHK-Cu** | ◐ᵖ | ◐ᵐ | ○ᵐ | ○ᵐ | ●ᵖ | ◐ᵖ | S | S |
| **LL-37** | ◐ᵖ | ◐ᵐ | ○ᵐ | — | ◐ᵖ | ○ᵐ | S | ○ᵐ |
| **Thymosin Alpha-1** | — | — | — | — | — | — | S | ●ᵖʰ |
| **MGF** | ○ᵐ | ○ᵐ | — | ○ᵐ | ◐ᵖ | — | S | S |
| **CJC-1295** | ○ᵐ | — | — | ○ᵖ | ○ᵐ | — | S | S |
| **GHRP-2** | ○ᵐ | — | — | ○ᵖ | ○ᵐ | — | S | S |
| **Ipamorelin** | ○ᵐ | — | — | ○ᵐ | ○ᵐ | — | S | S |
| **Dihexa** | ○ᵐ | ○ᵐ | — | — | ○ᵐ | — | S | S |
| **KPV** | ○ᵐ | ○ᵐ | — | — | ○ᵐ | — | S | ○ᵐ |
| **AOD-9604** | — | — | — | — | — | — | S | S |
| **MOTS-c** | — | — | — | — | — | — | ○ᵖ | S |
| **Semax** | ○ᵐ | — | — | — | — | — | S | S |
| **Kisspeptin** | — | — | — | — | — | — | S | S |
| **Melanotan II** | — | — | — | — | — | — | S | S |
| **Selank** | — | — | — | — | — | — | S | S |
| **DSIP** | — | — | — | — | — | — | S | S |
| **Epitalon** | — | — | — | — | — | — | S | S |

### Mechanistic notes (non-null cells only)

**Repair / angiogenesis / ECM-remodeling cluster** (the panel's natural coverage):

- **TB-500 / Thymosin Beta-4** — Tβ4 (TB-500 is its Tβ4(17–23)-region fragment).
  *VEGF*: pro-angiogenic, induces endothelial VEGF. *MMP2*: actin sequestration
  drives cell migration with upregulated MMP-2/MMP-9 and ECM turnover. *αSMA*:
  **decreases** hepatic stellate-cell α-SMA in liver-fibrosis models (anti-fibrotic;
  Kim & Jung 2015, in-repo). *HA*: serum HA as a fibrosis-turnover marker moves
  with the anti-fibrotic effect (expected ↓ if reversing hepatic fibrosis).
  *Wnd*: accelerated closure via migration/angiogenesis. *Hair*: induces hair
  growth in mice (Gao et al. 2015, in-repo). Direction of α-SMA/HA is **decrease**;
  VEGF/MMP2/Wnd/Hair are **increase**.
- **BPC-157** — *VEGF*: upregulates VEGFR2–eNOS–Egr-1 axis (robust rodent data).
  *Wnd*: accelerates tendon/muscle/skin healing. *MMP2/αSMA/Hair*: weak/indirect
  (MMP modulation during healing; hepatoprotection in tox models; angiogenic
  support of follicle — speculative).
- **GHK-Cu** — *Wnd/Hair*: stimulates dermal repair and hair-follicle/dermal-papilla
  activity (topical evidence). *VEGF*: pro-angiogenic in wound beds. *MMP2*:
  context-dependent modulation (remodeling vs. normalization). *αSMA/HA*: acts on
  **dermal** ECM (↑ dermal glycosaminoglycans/HA); against the **hepatic α-SMA /
  serum-HA fibrosis** readouts this is low/confounded, not a clean hepatic signal.
- **LL-37** — *VEGF*: pro-angiogenic via FPRL1. *MMP2*: induces MMPs (remodeling,
  also pathologic). *Wnd*: promotes re-epithelialization (diabetic-wound data).
  *αSMA/CBC*: can activate fibroblasts / modulate immune cells (weak).

**Immune:**

- **Thymosin Alpha-1** — *CBC*: increases absolute lymphocyte / CD4+ counts and
  CD4:CD8 ratio — a **direct, efficacy-relevant CBC-differential signal** (human
  data in HBV/HCV/sepsis/COVID adjunct). No credible link to the angiogenesis/
  ECM/wound readouts.

**GH-axis (CJC-1295, GHRP-2, Ipamorelin, MGF):** primary readouts are IGF-1 /
IGFBP-3 / GH, **not** this panel. Listed cells are indirect: GH/IGF-1 is mildly
angiogenic and supports healing (○), and sustained GH elevation can raise tissue/
serum HA via fibroblast stimulation (○–◐ for the GH secretagogues). MGF adds
modest tissue-repair plausibility (◐ Wnd) via satellite-cell activation.

**Metabolic / HPG / pigment / CNS / longevity (AOD-9604, MOTS-c, Kisspeptin,
Melanotan II, Semax, Selank, DSIP, Epitalon, Dihexa, KPV):** largely **Null** on
this panel — their pharmacodynamics live in other compartments (adiposity/leptin,
insulin sensitivity, LH/FSH/sex steroids, melanin, BDNF/NGF & cognitive scales,
sleep architecture, melatonin/telomerase, gut calprotectin/cytokines). MOTS-c
*ALT* (○) only if baseline hepatic steatosis improves; KPV/Semax carry weak
indirect cells via systemic inflammation / BDNF–VEGF crosstalk.

> **Design implication for the tracking engine.** This target panel is weighted
> toward angiogenesis / ECM-remodeling / fibrosis / wound-healing endpoints. It
> gives strong mechanistic coverage for ~5 peptides (TB-500, Tβ4, BPC-157, GHK-Cu,
> LL-37), a single specific hit for Thymosin Alpha-1 (CBC), and is **effectively
> Null for ~12 of the 20**. To detect activity of the GH-axis, metabolic, HPG,
> pigment, and neuro peptides, the engine must rely on the accessible proxies in
> Task 3, not these 8 markers.

### Cross-reference to engine data

| Target biomarker | In `biomarker_params.py`? | Notes |
|---|---|---|
| Serum VEGF | ✅ `"Serum VEGF"` (baseline 110, +45%, τ≈2w) | repair cluster |
| Wound closure area | ✅ several rows (`"Wound closure area"`, `"Dermal wound closure"`…) | imaging |
| Hair density (trichoscopy) | ✅ `"Hair density (trichoscopy)"` (+20%, τ≈12w) | imaging |
| ALT | ✅ `"ALT"` (flat — safety) | safety |
| CBC with differential | ✅ `"CBC with differential"` (flat — safety) | safety |
| MMP-2 activity | ❌ not modeled | add a `Params` row if tracked |
| Hepatic α-SMA expression | ❌ not modeled | transcriptomic; tissue-only |
| Serum hyaluronic acid | ❌ not modeled | add as fibrosis-turnover marker |

The engine's per-peptide `efficacy_markers` already list VEGF, MMP-2/MMP-9,
α-SMA/PDGFR, wound closure, and hair density for the repair peptides (see
`PEPTIDE_BIOMARKERS["TB-500"]`, `["Thymosin Beta-4"]`, `["GHK-Cu"]`,
`["BPC-157"]`, `["LL-37"]`), so this matrix is consistent with — and extends —
the curated data.

---

## Task 2 — Biomarker feasibility (longitudinal tracking in a standard human subject)

Scale: **1** = routine low-cost blood draw → **5** = highly invasive/specialized.

| # | Biomarker | Feas. | Assay type | Specimen | TAT (typical) | Cost barrier | Pre-analytical / interpretive caveats |
|---|---|:--:|---|---|---|---|---|
| 1 | **Serum VEGF** | 2–3 | Quantitative ELISA / multiplex immunoassay | Serum (prefer **plasma**) | 3–7 d (send-out / batched) | Low–moderate ($) | Platelets release VEGF on clotting → **serum overreads**; standardize tube, spin, and serum-vs-plasma; high CV |
| 2 | **MMP-2 activity** | 3–4 | Gelatin **zymography** or activity-based ELISA (vs. antigen ELISA) | Plasma / tissue | 5–10 d (research lab) | Moderate–high ($$) | *Activity* ≠ *antigen*; pro- vs. active-MMP-2 distinction; not a CLIA-routine test; freeze-thaw sensitive |
| 3 | **Hepatic α-SMA expression** | **5** | IHC or qPCR/RNA-seq on **liver biopsy** | Percutaneous liver core | 5–14 d | High ($$$) + procedural risk | Invasive; sampling variability; **not feasible for repeated/longitudinal** sampling in a healthy subject; ethics-limited |
| 4 | **Serum hyaluronic acid** | 2 | Immunoassay / latex agglutination (part of ELF, FibroMeter) | Serum | 2–7 d (send-out) | Moderate ($–$$) | Rises post-meal and with synovitis/age/renal clearance; non-specific to liver; standardize fasting |
| 5 | **Wound closure area** | 1–2 | Planimetry / standardized photographic imaging | Skin surface | Immediate | Low ($) | **Requires an existing wound** (context-limited); standardize lighting/scale/angle; inter-rater variability |
| 6 | **Hair density (trichoscopy)** | 2 | Dermoscope / phototrichogram with image analysis | Scalp (fixed target site) | Immediate–days | Low–moderate ($–$$) | Needs standardized site, lighting, and software; high anatomical variability; slow biology (τ≈months) |
| 7 | **ALT** | **1** | Automated enzymatic chemistry (CMP/LFT) | Serum/plasma | <24 h | Low ($) | Routine; diurnal/exercise/BMI effects; the default hepatic-safety marker |
| 8 | **CBC with differential** | **1** | Automated hematology analyzer (impedance + flow) | EDTA whole blood | <24 h | Low ($) | Routine; stable; flag-driven manual review; ideal longitudinal marker |

**Summary.** Routine and longitudinally trivial: ALT, CBC (1); wound/hair imaging
(1–2, but context-bound). Send-out but feasible: serum HA (2), serum VEGF (2–3,
pre-analytically fussy). Specialized/research: MMP-2 activity (3–4). Not
longitudinally feasible: hepatic α-SMA (5, requires repeat biopsy).

---

## Task 3 — Accessible proxy biomarkers (routine, downstream of activity)

For each peptide, 1–3 routine, widely available markers that proxy its
pharmacodynamics. Format: `Standard biomarker | expected perturbation | assay`.

| Peptide | Accessible proxies (perturbation · assay) |
|---|---|
| **CJC-1295** | IGF-1 ↑ · immunoassay · **(primary)** ‖ IGFBP-3 ↑ · immunoassay ‖ fasting glucose/HbA1c ↑ (safety) · chemistry |
| **Ipamorelin** | IGF-1 ↑ · immunoassay ‖ IGFBP-3 ↑ · immunoassay ‖ cortisol/prolactin = no change (selectivity) · immunoassay |
| **GHRP-2** | IGF-1 ↑ · immunoassay ‖ prolactin ↑ (mild) · immunoassay ‖ cortisol/ACTH ↑ (mild, off-target) · immunoassay |
| **MGF** | IGF-1 ↑ (modest) · immunoassay ‖ creatine kinase ↕ · chemistry ‖ (lean mass by DXA — imaging) |
| **AOD-9604** | Body weight / waist ↓ · anthropometry ‖ leptin ↓ · immunoassay ‖ lipid panel ↕ · chemistry |
| **MOTS-c** | HOMA-IR ↓ (fasting glucose+insulin) · chemistry/immunoassay ‖ HbA1c ↓ · HPLC/immunoassay ‖ ALT ↓ if NAFLD · chemistry |
| **Semaglutide-class context** | *(not in this 20 — see engine GLP-1 panels)* |
| **Kisspeptin** | LH ↑, FSH ↑ · immunoassay · **(primary)** ‖ estradiol / testosterone ↑ · immunoassay ‖ SHBG ↕ · immunoassay |
| **Thymosin Alpha-1** | Absolute lymphocyte count ↑ · CBC differential · **(routine & direct)** ‖ CD4:CD8 ↑ · flow cytometry ‖ hs-CRP ↓ · chemistry |
| **KPV** | hs-CRP ↓ · chemistry ‖ fecal calprotectin ↓ · stool immunoassay ‖ CBC (WBC normalize) · hematology |
| **LL-37** | 25-OH vitamin D ↑/correlate · immunoassay ‖ hs-CRP ↕ (biphasic; ↑ at high dose) · chemistry ‖ CBC · hematology |
| **BPC-157** | hs-CRP ↓ · chemistry ‖ IL-6 ↓ (if available) · immunoassay ‖ **no validated routine serum efficacy proxy** — readout is largely imaging/functional |
| **TB-500 / Thymosin Beta-4** | hs-CRP ↓ · chemistry ‖ CBC (safety) · hematology ‖ **no routine serum efficacy proxy** — VEGF/MMP-2/imaging are the real readouts |
| **GHK-Cu** | Serum copper ↑ / ceruloplasmin ↑ (exposure, not efficacy) · chemistry ‖ (skin/hair imaging is the efficacy readout) |
| **Dihexa** | **No routine serum proxy** — serum HGF (research) ↑; readout is cognitive scales (MoCA/ADAS-cog) |
| **Selank** | **No routine lab proxy** — GAD-7/HAM-A ↓ (clinical scale); serum BDNF (research) ↑ |
| **Semax** | **No routine lab proxy** — serum BDNF/NGF (research) ↑; NIHSS/MoCA (clinical) |
| **DSIP** | Cortisol ↓ (HPA) · immunoassay ‖ (PSQI / polysomnography — functional); no routine efficacy lab |
| **Epitalon** | Nocturnal melatonin ↑ (or urinary 6-sulfatoxymelatonin) · immunoassay ‖ no routine efficacy lab |
| **Melanotan II** | **No routine lab proxy** — melanin index (imaging), IIEF (ED); BP monitoring (safety) |

**Pattern.** Peptides with **excellent routine proxies**: CJC-1295/Ipamorelin/
GHRP-2/MGF (IGF-1 axis), MOTS-c (HOMA-IR/HbA1c), Kisspeptin (LH/FSH/sex steroids),
Thymosin Alpha-1 (lymphocyte count). Peptides with **poor serum proxies** whose
true readouts are imaging/tissue/functional: **BPC-157, TB-500, Thymosin Beta-4,
GHK-Cu, Melanotan II, and the neuro peptides (Selank, Semax, Dihexa)** — for these,
a serum-only tracking strategy will miss the effect; pair with imaging
(wound/hair/skin) or validated clinical scales.

---

## Primary references

Peptide-specific claims here are consistent with the **vetted citation set in
the repository** (`engine/peptides/biomarkers.py` + `engine/peptides/measurements.py`),
which were retrieved via scite and carry DOIs (e.g. Kim & Jung 2015 — Tβ4 /
hepatic fibrosis, `10.3390/ijms160510624`; Gao et al. 2015 — Tβ4 / hair,
`10.1371/journal.pone.0130040`; Orlovius et al. 2013 — AOD-9604, `10.1002/dta.1557`).
No citations are fabricated here; for a regulatory-grade dossier, run each
load-bearing claim through the literature tools and attach current evidence
(the `engine/regulatory` subsystem already pulls ClinicalTrials.gov / openFDA /
Federal Register for live status).
