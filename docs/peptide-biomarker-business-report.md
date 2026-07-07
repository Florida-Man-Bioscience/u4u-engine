# Peptide Biomarker Measurements — Financial, Business, Capital & Practical Considerations

**Source repository:** [`florida-man-bioscience/u4u-engine`](https://github.com/florida-man-bioscience/u4u-engine)
**Source modules:** `engine/peptides/biomarkers.py`, `engine/peptides/measurements.py`, `engine/tracking/biomarker_params.py`
**Scope:** 23 peptide[^peptide] panels[^panel] · 181 measurement records · 137 unique biomarker[^biomarker] assays[^assay]
<!-- NEEDS REVIEW: `engine/peptides/measurements.py` currently enumerates 23 panels and 181 measurement records (both verified), but 141 unique measurement names — not 137. Reconcile the unique-assay count (the delta may reflect a different "unique assay" definition than raw distinct names). -->
**Prepared:** June 12, 2026

---

## Executive summary

The `peptideIQ` engine ships 23 panels covering BPC‑157, TB‑500, Thymosin Beta‑4, GHK‑Cu, MOTS‑c, CJC‑1295, Ipamorelin, GHRP‑2, MGF, AOD‑9604, Thymosin Alpha‑1, Epitalon, Selank, Semax, DSIP, Dihexa, Kisspeptin, Melanotan II, LL‑37, KPV, Semaglutide, Tirzepatide, and Liraglutide.[^peptidelist] Each panel mixes (a) cheap, commoditized clinical chemistry[^clinchem], (b) mid‑cost hormone immunoassays[^immunoassay], and (c) a long tail of specialty assays, imaging, and procedure‑based readouts that drive the bulk of the per‑participant cost.

**Study context.** These figures describe the assay, imaging, and logistics economics of a prospective, observational, multi‑site cohort study. FMB partners with peptide‑prescribing clinics and enrolls consenting adults who have already been prescribed peptide therapy by their own clinicians (treatment‑as‑usual). FMB tracks each participant's biomarker trajectory over time against the engine's genomic response predictions; it does not prescribe, supply, dose, or direct any peptide. Every cost below is an observational‑tracking cost (assays, imaging, specimen logistics, data capture), not a cost of supplying drug.

The single biggest financial lever is **tier discipline** — letting the routine safety markers fall on the LabCorp/Quest physician‑account[^physicianaccount] price sheet (single‑digit dollars per analyte[^analyte]) while reserving research‑grade ELISA[^elisa] / multiplex[^multiplex], imaging, and polysomnography[^psg] for milestone visits. A reasonable per‑participant envelope for a 12‑week observational tracking program is roughly **\$300–\$500 (lean), \$900–\$1,800 (typical), or \$3,500–\$8,000+ (premium)** depending on imaging frequency, cytokine[^cytokine] multiplexing, and the inclusion of MRI[^mri] or PSG.

The biggest business risks are *not* the assay costs — they are (1) the **CLIA[^clia] / LDT[^ldt] regulatory perimeter** around research markers used clinically, (2) **state-by-state direct‑to‑consumer[^dtc] lab restrictions** (NY, NJ, RI, MD, CA gating), (3) compounded‑peptide[^compounding] enforcement (the FDA's 503A/503B[^503] activity around BPC‑157, CJC‑1295, ipamorelin, MOTS‑c, etc.), and (4) **WADA[^wada] / sports anti‑doping** exposure for the GH‑axis[^ghaxis] and erythropoiesis[^erythropoiesis]‑adjacent peptides.

---

## 1 · Coverage map — what the engine actually measures

The 137 unique measurements break down by modality[^modality] as follows ([engine/peptides/measurements.py](https://github.com/florida-man-bioscience/u4u-engine/blob/main/engine/peptides/measurements.py)):

| Modality | Unique assays | Representative examples |
|---|---|---|
| Clinical chemistry | 20 | ALT, AST, creatinine, fasting glucose, HbA1c[^hba1c], HOMA‑IR[^homair], lipase, PSA[^psa], ceruloplasmin, hs‑CRP[^hscrp] |
| Imaging | 22 | DXA[^dxa] body composition, MSK[^msk] ultrasound, trichoscopy[^trichoscopy], transvaginal US, DWI[^dwi] brain MRI, dermoscopy[^dermoscopy] |
| Hormone | 14 | IGF‑1[^igf1], IGFBP‑3, GH peak/AUC[^auc], LH, FSH, estradiol, testosterone, prolactin, cortisol, ACTH |
| Proteomic | 13 | VEGF[^growthfactors], MMP‑2, S100B, HGF, NGF, laminin‑5, leptin |
| Patient‑reported / functional | ~20 | VAS, HAM‑A, GAD‑7, MoCA, NIHSS, IIEF‑5, OSDI, PSQI, ADAS‑cog, Stroop, COWS[^scales] |
| Cytokine | 4 | IL‑6, TNF‑α, IFN‑γ, IL‑8[^cytokine] |
| Transcriptomic | 12 | Hepatic α‑SMA, skin VEGF, dermal collagen I, AANAT, neurotrophin transcripts[^transcriptomic] |
| Metabolomic | ~5 | Nitrite/nitrate (NOx), folate‑cycle metabolites, kynurenine/tryptophan, 5‑HIAA[^metabolomic] |
| Microbiome / GI | ~3 | Fecal calprotectin[^calprotectin], colonic MPO, histologic colitis score |
| Hematology / specialty flow | ~3 | CBC w/diff, CD4/CD8 ratio[^cd4], absolute CD4 |

The full structured inventory lives in code as the `PEPTIDE_MEASUREMENTS` dict in [`engine/peptides/measurements.py`](https://github.com/florida-man-bioscience/u4u-engine/blob/main/engine/peptides/measurements.py) (181 records) for downstream cost modeling.

---

## 2 · Cost tiering — what every category actually costs

Prices below are **U.S. cash / physician‑account benchmarks**, not list. They are the practical numbers a clinic or sponsor will see when negotiating with LabCorp, Quest, or a direct‑to‑consumer marketplace. Hospital sticker pricing is 3–20× higher under the federal Hospital Price Transparency rule ([MedicalPriceCheck MRI analysis](https://medicalpricecheck.com/research/mri-cost/)).

### 2.1 Tier 1 — Commodity clinical chemistry (≈ \$1–\$25 / analyte)

The bulk of the safety markers and a meaningful share of efficacy markers fall here. On a published LabCorp physician‑account sheet, **IGF‑1 ran \$14.15** and **FSH/LH ran \$6.40** ([Integrity Health & Wellness LabCorp price sheet, Aug 2025](https://static1.squarespace.com/static/6882d28a87311f496e6204a6/t/68a69d4b36eceb142f2d3838/1755749707225/Integrity+Health+%26+Wellness+-+Common+LabCorp+Prices+-+August+2025.pdf)); a separate Ally Primary Care LabCorp 2025 sheet lists **IGF‑1 with Z‑score at \$18.20** ([LabCorp 2025 pricing via Ally Primary Care](https://static1.squarespace.com/static/63a8aaf1bfe65d3cb8d85ae6/t/6838b64bc8521a1bc0d4c445/1748547147439/LabCorp+2025+Pricing.pdf)). DTC retail for IGF‑1 sits at **\$24 + ~\$28 in collection/order fees on JustLabs/Quest** ([JustLabs IGF‑1 listing](https://justlabs.health/tests/igf-1)).

| Assay (from panels) | Typical cash/PA price | Used in panels |
|---|---|---|
| ALT, AST, creatinine, CBC, BMP | \$3–\$15 / analyte | BPC‑157, TB‑500, MOTS‑c, GHK‑Cu, Thymosin‑α1, Selank, KPV, GLP‑1 class |
| Fasting glucose | \$5–\$15 ([Well Built Florida HOMA‑IR guide](https://wellbuiltflorida.com/homa-ir-test-cost-pricing/)) | MOTS‑c, CJC‑1295, GHRP‑2, MGF, AOD‑9604, GLP‑1s |
| HbA1c | \$10–\$25 | MOTS‑c, CJC‑1295, GLP‑1s |
| Lipid panel | \$10–\$25 | AOD‑9604, GLP‑1s, Epitalon |
| Lipase / amylase | \$10–\$20 | Semaglutide, Tirzepatide, Liraglutide |
| Ceruloplasmin, copper | \$10–\$30 | GHK‑Cu |
| IGF‑1, IGFBP‑3 | \$14–\$30 (PA) / \$24–\$60 (DTC) | CJC‑1295, Ipamorelin, GHRP‑2, MGF |
| LH, FSH, estradiol, testosterone, prolactin, cortisol | \$6–\$30 each (PA) | Kisspeptin, Ipamorelin, GHRP‑2, Selank, DSIP, CJC‑1295 |
| hs‑CRP | \$10–\$20 | Epitalon, Thymosin‑α1, LL‑37 |
| PSA | \$15–\$30 | CJC‑1295 |
| Fecal calprotectin | Medicare CLFS reimburses **\$19.63**; DTC \$100–\$200 ([AAFP review, 2021](https://www.aafp.org/afp/2021/0900/p303)) | KPV |

**Take‑away:** roughly **60–70 % of measurements in the panel set** are Tier 1. A full safety+routine‑efficacy draw for almost any of the 23 peptides costs **under \$150 in reagent / lab pass‑through** if billed at physician‑account rates.

### 2.2 Tier 2 — Mid‑cost specialty hormone / metabolic (\$50–\$300)

| Assay | Typical cash | Panels |
|---|---|---|
| GH stimulation (peak + AUC, multi‑draw) | \$200–\$500 in the U.S.; OHSU Endocrine Tech Core charges **\$16.80 / sample but you need 5–10 draws** ([OHSU ETC 2024‑25 rate sheet](https://www.ohsu.edu/sites/default/files/2024-06/YR65%20Endocrine%20Technologies%20Core%20External%20Rate%20Sheet.pdf)) | CJC‑1295, Ipamorelin, GHRP‑2 |
| HOMA‑IR (glucose + insulin computed) | **\$40–\$150 lab only**, **\$60–\$430 with consult** ([Well Built Florida cost guide](https://wellbuiltflorida.com/homa-ir-test-cost-pricing/)) | MOTS‑c, GLP‑1s |
| IL‑6 (single‑plex CLIA) | DTC **\$132–\$220** ([Ulta Lab Tests IL‑6](https://www.ultalabtests.com/test/interleukin-6-test)) | BPC‑157, MOTS‑c, Thymosin‑α1 |
| CD4/CD8 flow cytometry | **\$95–\$159** ([LabCorp via Find Lab Tests](https://www.findlabtest.com/lab-test/general-wellness/helper-t-lymphocyte-marker-cd4-labcorp-505008)) | Thymosin Alpha‑1 |
| HBV‑DNA / HCV‑RNA quantitative PCR | **\$329–\$699** ([LabCorp via Find Lab Tests](https://www.findlabtest.com/lab-test/general-wellness/hepatitis-b-virus-hbv-quantitative-dna-real-time-pcr-nongraphical-labcorp-551610)) | Thymosin Alpha‑1 |
| Diurnal salivary cortisol 4‑point (ZRT) | \$130–\$390 ([ZRT Sleep Balance / Diurnal Cortisol Cx4](https://labtestsplus.com/product/sleep-balance-profile-zrt-labs/)) | Selank, DSIP |
| Telomere[^telomere] length qPCR[^qpcr] (T/S) | **\$50–\$178** DTC (TeloYears legacy) ([Nebula TeloYears review](https://nebula.org/blog/teloyears-review/)); Life Length F‑ISH ~\$435 ([The Independent](https://www.independent.co.uk/news/science/the-163-400-test-that-tells-you-how-long-you-ll-live-2284639.html)) | Epitalon |

### 2.3 Tier 3 — ELISA / multiplex research markers (\$15–\$80 / analyte at scale; \$250–\$700 retail)

The cytokine, growth‑factor, and neurotrophin[^neurotrophin] readouts in the panels are not routinely reimbursable — they need a research‑use immunoassay or a CLIA‑validated LDT.

| Assay | Per‑sample cost (research) | Notes / panels |
|---|---|---|
| BDNF, NGF (Biosensis Rapid ELISA) | **\$417–\$677 / kit ≈ \$10–\$20 per sample at 38–40 samples** ([Biosensis BDNF/NGF kit](https://www.biosensis.com/products/elisa-kits-reagents/elisa-kits.html)) | Selank, Semax |
| BDNF, NGF (Columbia Irving Biomarkers Core processing) | **\$5.75–\$10.92 / sample (kit extra)** ([Columbia FY22 Biomarkers Core price list](https://www.irvinginstitute.columbia.edu/file/6037/download?token=SkSL2oWw)) | Same |
| IL‑6, TNF‑α, IL‑1β, IFN‑γ singleplex ELISA | **~\$12–\$17 / analyte / sample** ([NCBI PMC2562869 — ELISA vs Multiplex comparison](https://pmc.ncbi.nlm.nih.gov/articles/PMC2562869/table/T1/)) | BPC‑157, MOTS‑c, KPV, Thymosin‑α1, Semax |
| 4‑plex cytokine MSD multiplex (IL‑1β, IL‑6, TNF‑α, IFN‑γ) | **~\$19 / sample (vs \$62 single‑plex)** — same NCBI source | Switch from singleplex once N > ~30 |
| Salivary TNF‑α (Salimetrics, 38‑sample kit) | **\$600–\$655 / kit ≈ \$16 / sample** ([Montana State CAIRHE salivary ELISA list](https://www.montana.edu/cairhe/translational-biomarkers-core/pricing-lists/ELISAs-saliva-11.19.19.pdf)) | Selank, Semax (if salivary route preferred) |
| VEGF, MMP‑2 / 9, laminin‑5 ELISA | **\$15–\$25 / sample at scale** | BPC‑157, TB‑500, Thymosin β4 |
| Telomerase activity (in‑house qTRAP) | **\$2 / reaction** ([Clinics PMC7847253](https://pmc.ncbi.nlm.nih.gov/articles/PMC7847253/)) vs commercial kits \$0.53–\$1.13/rxn but \$400+ kit setup ([Herbert TRAP protocol](https://www.telomer.com.tr/wp-content/uploads/2015/12/Detection-of-Telomerase-Activity-by-TRAP_Herbert-et-al_Nature-Protocol-2006.pdf)) | Epitalon |

A practical rule: **multiplex panels are cheaper per analyte above ~20 samples**; below that, individual ELISA is the right choice. The KPV, Semax, Selank, and Thymosin‑α1 panels all measure ≥ 3 cytokines/neurotrophins simultaneously and therefore reward multiplexing.

### 2.4 Tier 4 — Imaging (\$50–\$3,500)

| Modality | Cash price | Panels |
|---|---|---|
| DXA body composition only | **\$50–\$125** ([Desert Dexa](https://desertdexa.com), [Precision Health by Science](https://precisionhealthbyscience.com/dexa/), [Endocrine Advantage](https://www.endocrineadvantage.com/pricing)) | CJC‑1295, Ipamorelin, MGF, AOD‑9604 |
| DXA full (body comp + bone) | **\$150–\$199** (same sources) | Same |
| MSK / tendon ultrasound | **\$160 / area UK** ([RAD Clinics](https://radclinics.co.uk/fee-guide-aylesbury/)); U.S. cash median **~\$428** for shoulder ([Turquoise Health](https://turquoise.health/services/ultrasound-shoulder-jointsoft-tissue/)) | BPC‑157 |
| Trichoscopy | **\$100–\$300** ([Hair Restoration Tour](https://hairrestorationtour.com/trichoscopy/), [Shapiro Medical](https://shapiromedical.com/blog/trichoscopy-hair-loss-diagnosis/)) | TB‑500, GHK‑Cu, Thymosin β4 |
| Transvaginal US (follicular monitoring) | **\$150–\$250 / scan in U.S.**; \$10–\$25 per scan in India; need 2–3 scans/cycle ([Sudha Fertility Centre](https://sudhafertilitycentre.com/blog/fertility-tests-for-women/)) | Kisspeptin |
| Brain MRI (with/without contrast) | **Median \$2,200 / \$2,900 cash**, range \$406–\$18,000+ ([MedicalPriceCheck](https://medicalpricecheck.com/research/mri-cost/), [MyCareCost](https://mycarecost.net/brain-mri-cost)) — freestanding centers 40–60 % cheaper | Semax (DWI), Dihexa (striatal volume) |
| Wound photography (planimetry) | **<\$25 in equipment amortization** | TB‑500, Thymosin β4, LL‑37 |
| Polysomnography | **\$1,000–\$5,000 in‑lab**; **\$150–\$600 home sleep test** ([SleepDr](https://sleepdr.com/the-sleep-blog/how-much-will-a-sleep-study-cost-me), [GoodRx](https://www.goodrx.com/health-topic/procedures/how-much-sleep-study-cost), [Sleep Foundation](https://www.sleepfoundation.org/sleep-studies/how-much-does-a-sleep-study-cost)) | DSIP (slow‑wave‑sleep %, sleep onset latency) |
| Dermoscopic nevus surveillance | **\$100–\$300 / visit** | Melanotan II |
| Endoscopy + Mayo score | **\$1,000–\$3,000 cash** (avoidance is the point of fecal calprotectin) | KPV |

Imaging is the **single biggest cost driver** in any panel that ships an MRI or PSG. Substituting home sleep apnea testing for in‑lab PSG cuts ~80 % of cost on the DSIP panel; substituting freestanding‑center MRI for hospital MRI saves 50–60 % on Semax and Dihexa neurology panels.

### 2.5 Tier 5 — Patient‑reported & functional (≈ \$0 marginal, **all rest is labor**)

VAS, HAM‑A, GAD‑7, MoCA, NIHSS, IIEF‑5, OSDI, PSQI, COWS, ADAS‑cog, Stroop, Brief Pain Inventory — these are zero‑reagent. They cost only:

- **Licensing:** HAM‑A and most legacy scales are free; MoCA requires a paid clinician certification (\$125 / clinician one‑time as of 2026); some proprietary scales (ADAS‑Cog) require sponsor licensing in commercial studies.
- **Administration:** **5–25 minutes of trained staff time** per visit per instrument. At a U.S. fully‑loaded clinical‑coordinator rate of ~\$50/hour, that is **\$4–\$20 of labor per scale per visit**.
- **EDC[^edc] capture:** REDCap[^redcap] (free at academic sites), Castor, Medable, or Greenphire ePRO[^epro] at \$1–\$5 per completed instrument.

For chronic‑pain, anxiety, sleep, sexual‑function, and cognition panels (BPC‑157 VAS, Selank GAD‑7, DSIP PSQI, Melanotan II IIEF, Dihexa ADAS‑Cog, Semax NIHSS), the patient‑reported endpoints are the **best dollars‑per‑signal expenditure in the whole panel** — they are essentially free relative to imaging and ELISA, and they are the closest readout to what the patient cares about.

### 2.6 Tier 6 — Research‑only / tissue assays (typically \$0 in clinic, \$100s–\$1000s in animal studies)

Several measurements are research‑use markers from the cited primary papers and are **not feasible in routine human practice**:

- **Hepatic α‑SMA expression** (TB‑500) — needs liver biopsy + qPCR/IHC[^ihc]; biopsy alone \$1,500–\$3,000.
- **Hippocampal c‑Met phosphorylation, striatal volume** (Dihexa) — animal model markers in original papers; in humans only striatal MRI volumetry is feasible.
- **Skin VEGF / collagen I / elastin / TGF‑β1 expression** (GHK‑Cu, Thymosin β4) — needs punch biopsy (~\$74–\$220 plus pathology, per [Hair Loss Korea](https://hairlosskorea.com/hair-loss-diagnosis-korea-complete-guide/)) + qPCR.
- **Colonic IL‑6/IL‑8 mRNA, MPO, NF‑κB translocation, histologic colitis score** (KPV) — needs colonoscopy + biopsy.
- **Satellite cell markers (Pax7/MyoD), myogenic precursor engraftment** (MGF) — muscle biopsy + flow/IHC.
- **CAMP cathelicidin gene expression** (LL‑37) — wound biopsy.
- **Pineal AANAT expression** (Epitalon) — post‑mortem only in humans.
- **Tyrosinase activity** (Melanotan II) — skin biopsy / research.
- **Skeletal muscle p‑AMPK** (MOTS‑c) — muscle biopsy.

These should be flagged in any clinical product as **mechanistic markers from the literature, not bedside measurements**. They support credibility of the model but do not generate consumer revenue.

---

## 3 · Per‑peptide cost profile (12‑week observational tracking program)

These envelopes assume **baseline + week 4 + week 12** sampling of participants already prescribed the peptide by their own clinicians (treatment‑as‑usual), at physician‑account or marketplace pricing. They explicitly *exclude* the peptide itself (which FMB never supplies), prescriber visits, and shipping.

| Peptide | Lean panel cost (3 visits) | Typical | Premium (adds imaging/multiplex) | Primary cost drivers |
|---|---|---|---|---|
| BPC‑157 | \$120 | \$450 | \$1,600 | MSK ultrasound, VEGF/IL‑6 ELISA |
| TB‑500 | \$130 | \$500 | \$1,400 | Trichoscopy, MMP‑2 ELISA, optional liver α‑SMA (research only) |
| Thymosin Beta‑4 | \$100 | \$350 | \$900 | Corneal staining (clinician‑in‑office), wound photography, optional skin biopsy panel |
| GHK‑Cu | \$120 | \$420 | \$1,200 | Wrinkle / skin US imaging, MMP‑1, optional biopsy for collagen I |
| MOTS‑c | \$180 | \$500 | \$1,400 | HOMA‑IR + multiplex IL‑6/IL‑1β + VO₂max test |
| CJC‑1295 | \$180 | \$600 | \$1,800 | IGF‑1/IGFBP‑3 + GH peak + DXA |
| Ipamorelin | \$160 | \$520 | \$1,500 | GH AUC (multi‑draw stim test) + DXA |
| GHRP‑2 | \$170 | \$540 | \$1,500 | GH peak + ACTH + cortisol + DXA |
| MGF | \$160 | \$560 | \$1,700 | DXA + grip dynamometry + IGF‑1 + research markers excluded |
| AOD‑9604 | \$140 | \$430 | \$1,200 | DXA + leptin ELISA + WADA hGH isoform (forensic) |
| Thymosin Alpha‑1 | \$280 | \$900 | \$2,400 | CD4/CD8 flow + IFN‑γ + viral load PCR |
| Epitalon | \$200 | \$700 | \$2,000 | Telomere T/S + telomerase qTRAP + cancer surveillance |
| Selank | \$130 | \$450 | \$1,200 | Plasma BDNF + diurnal cortisol + Stroop |
| Semax | \$240 | \$900 | \$3,800 | NIHSS / MoCA + BDNF/NGF + DWI MRI |
| DSIP | \$220 | \$700 | \$3,200 | HSAT (\$200) or in‑lab PSG (\$1,500+) + 5‑HIAA |
| Dihexa | \$260 | \$900 | \$4,500 | ADAS‑cog + serum HGF + striatal MRI + oncology surveillance |
| Kisspeptin | \$220 | \$700 | \$1,800 | LH/FSH/E2/T + serial transvaginal US |
| Melanotan II | \$160 | \$500 | \$1,300 | Dermoscopy + IIEF + BP monitoring |
| LL‑37 | \$120 | \$380 | \$1,000 | Wound photography + bacterial swab culture + 25‑OH‑D |
| KPV | \$160 | \$500 | \$2,400 | Fecal calprotectin + endoscopic Mayo (rare) |
| Semaglutide | \$140 | \$450 | \$1,100 | HbA1c + lipase + lipid panel (commodity) |
| Tirzepatide | \$140 | \$450 | \$1,100 | Same as semaglutide |
| Liraglutide | \$130 | \$430 | \$1,000 | Same as semaglutide |

**Portfolio weighted average:** roughly **\$170 lean / \$550 typical / \$1,800 premium** per peptide per 12‑week cycle.

---

## 4 · Capital cost — what is needed to in‑source vs out‑source

### 4.1 Out‑source everything (asset‑light)
- Pass‑through to LabCorp / Quest / Mayo Reference at physician‑account rates.
- Imaging via freestanding partners (DXA, MSK US, MRI).
- Multiplex / ELISA via a CRO[^cro] biomarker core (Columbia‑style \$5–\$30 / sample plus kit).
- **Up‑front capex[^capex]: <\$50K** (EDC, ePRO licenses, courier kits, freezer at a clinic site).
- **Per‑participant cost: full Tier 2.7 table above.**

### 4.2 In‑source the high‑volume immunoassays
- Plate reader / luminometer: \$15K–\$30K.
- MSD[^msd] QuickPlex SQ 120MM (multiplex): **\$60K–\$120K** + kit consumables.
- –80 °C freezer + LIMS[^lims]: \$15K.
- 1 FTE[^fte] research associate: \$70K–\$120K loaded.
- **Breakeven against CRO biomarker core:** ~3,000–5,000 cytokine samples / yr.

### 4.3 In‑source flow cytometry[^flowcytometry] (CD4/CD8, satellite cell markers)
- 3‑laser benchtop cytometer: **\$80K–\$200K** (e.g., Partec/Sysmex CyFlow at ~\$25K used; BD Accuri/Attune \$80K–\$120K new; **price per CD4 test ~€2.50 ≈ \$2.70 once amortized**, per [Partec CyFlow SL3 spec sheet](http://www.cyto.purdue.edu/cdroms/cyto10a/sponsors/media/partec/cyflowsl3.pdf)).
- CLIA high‑complexity certification + flow‑cyto SOPs[^sop]: \$30K–\$60K + ongoing.

### 4.4 In‑source imaging
- DXA Hologic / GE iDXA: **\$60K–\$110K** used, \$120K–\$180K new. Site licensure + radiation safety officer required in most states.
- High‑resolution MSK ultrasound: **\$25K–\$60K** (GE LOGIQ E, Mindray, Butterfly iQ3 \$3K–\$5K for portable).
- Polysomnography hardware: **\$15K–\$40K** for HSAT capacity; in‑lab PSG suite is a 7‑figure build.
- MRI: **not feasible** to in‑source — pay per scan.

**Recommended capital path for a peptide observational tracking program:**
1. Start fully out‑sourced.
2. At ~250–500 active participants, in‑source DXA (covers CJC‑1295, Ipamorelin, MGF, AOD‑9604 — four of the highest‑volume panels).
3. At ~1,000 active participants with cytokine‑heavy panels (BPC‑157, KPV, MOTS‑c, Thymosin α1, Semax), in‑source MSD multiplex.
4. Flow cytometry only if Thymosin α1 / immunology becomes a flagship line.
5. Never in‑source MRI, PSG (in‑lab), or HBV/HCV PCR — they are scale‑disadvantaged.

---

## 5 · Business & reimbursement considerations

### 5.1 What is reimbursable vs cash‑pay

| Category | Reimbursable today? | Notes |
|---|---|---|
| Standard chemistry, LFTs[^lft], CBC, HbA1c, lipids, fasting insulin | Yes | CPT[^cpt] 80048, 80053, 85025, 83036, 80061, 83525. Trivially covered when ordered by physician. |
| IGF‑1, IGFBP‑3, GH stim | Yes when ICD‑10[^icd10] supports it (GH deficiency, pituitary, IGF‑1 deficiency); off‑label[^offlabel] "anti‑aging" use is **not** reimbursable. |
| Cytokines, BDNF, NGF, VEGF, MMPs | **No.** Research‑use only or LDT cash‑pay. |
| Fecal calprotectin | Yes, Medicare CLFS \$19.63 ([AAFP review](https://www.aafp.org/afp/2021/0900/p303)). |
| CD4/CD8 flow | Yes with HIV / immunodeficiency dx; not for general immunity assessment. |
| Telomere length / telomerase | **No.** All cash. |
| DXA | Bone density yes with osteoporosis dx; **body composition is cash‑only**. |
| MSK ultrasound | Yes with injury dx. |
| MRI brain | Yes with neurologic dx. |
| Polysomnography | Yes for OSA; sleep architecture for DSIP off‑label is cash. |
| Trichoscopy | Cash, ~\$100–\$300. |
| Transvaginal US ovulation tracking | Yes inside a fertility benefit; cash outside. |
| Patient‑reported scales | Bundled into E&M[^em] code (97 series); not separately billable. |

**Practical implication:** essentially the *entire* off‑label peptide biomarker tracking effort is a **cash‑pay / research‑funded** exercise rather than a reimbursable one. Insurance optionality matters only where the indication[^indication] crosses into a recognized FDA‑approved use (GLP‑1s[^glp1] for T2DM[^t2dm]/obesity; Thymosin α1 in chronic viral hepatitis ex‑US; Kisspeptin in hypogonadism[^hypogonadism] workup; ipamorelin/CJC for documented adult GHD[^ghd]).

### 5.2 Cost‑recovery models that fit the panel structure

These describe how the *tracking* cost can be structured; the peptide itself is prescribed and dispensed independently by the participant's own clinician, so none of these models involve FMB supplying or co‑selling drug.

1. **Per‑draw menu** — the partner clinic publishes \$X per analyte; the participant (or study) selects. Highest per‑draw margin, lowest longitudinal completeness.
2. **Subscription / membership tracking** — \$99–\$299 / mo gates a quarterly panel + telehealth review of results. Best fit for the chronic peptides (CJC‑1295, MOTS‑c, Epitalon, GLP‑1s).
3. **Panel‑bundled package** — e.g., "12‑week BPC‑157 tracking package: 3 panels + 2 US + telehealth review = \$1,495." Cleanest cost storytelling.
4. **Clinic‑bundled tracking kit** — at a partner clinic the prescription and dispensing are handled independently by the clinic (or its compounding pharmacy); FMB supplies only the biomarker / dried blood spot[^dbs] kit[^sku] alongside the participant's existing prescription, so tracking travels with the therapy they are already receiving. FMB never ships or co‑sells the vial.

### 5.3 Unit economics (representative typical‑tier package)
- Pass‑through cost: \$550 (per §3).
- Phlebotomy[^phlebotomy], supplies, courier: \$40–\$80.
- Clinician interpretation (15–30 min): \$50–\$120.
- Platform / EDC / ePRO: \$10–\$30.
- **Loaded COGS[^cogs]: ~\$650–\$780.**
- Sell price: \$1,200–\$2,400 → **gross margin[^grossmargin] ~45–65 %** before customer acquisition cost.
- CAC[^cac] in peptide / longevity DTC is currently \$200–\$600 → payback usually 1 cycle.

---

## 6 · Regulatory & enforcement landscape

This is where most peptide‑biomarker programs underwrite the real risk.

### 6.1 FDA — the peptide side
- BPC‑157, CJC‑1295, Ipamorelin, MOTS‑c, Thymosin α1, Thymosin β4 / TB‑500, Epitalon, Semax, Selank, Melanotan II, Dihexa, Kisspeptin (most uses), LL‑37, KPV — **not FDA‑approved drugs in the U.S.** Most appeared on FDA's 503A bulks‑review category 2 list in 2023, restricting 503A pharmacy compounding. Operating under 503B requires an outsourcing‑facility registration and cGMP[^cgmp] compliance.
- Semaglutide, Tirzepatide, Liraglutide — FDA‑approved; compounded versions came off shortage in late 2024 / 2025 and are now enforcement priority.
- AOD‑9604 — failed Phase 2b[^phase] obesity (Metabolic Pharmaceuticals 2007). Has GRAS[^gras] status as a food‑supplement *flavoring agent* but **not** as a drug.

### 6.2 Lab side — CLIA, state, and LDT rule
- Every clinical lab needs **CLIA certification** matched to test complexity. Cytokine ELISAs and flow are high‑complexity.
- **FDA Final Rule on LDTs (May 2024)** phases regulation of laboratory‑developed tests over four years (Stage 1 May 2025 → Stage 5 May 2028). Research‑use cytokine and neurotrophin assays used to gate peptide therapy will need to be re‑validated as IVDs[^ivd] unless they fall under the small grandfather pocket[^grandfather] — **plan the 4‑year ramp now.**
- **State direct‑to‑consumer restrictions:** New York, New Jersey, Rhode Island, and Maryland are the most aggressive. Many DTC marketplaces blacklist these states ([Find Lab Tests Online CD4 listing](https://www.findlabtest.com/lab-test/general-wellness/helper-t-lymphocyte-marker-cd4-labcorp-505008) explicitly notes "Blacklisted States: NY, NJ, RI"); ZRT saliva tests require a clinician script in CA, MD, NY ([ZRT Cx4 product page](https://www.evenbetternow.com/products/diurnal-cortisol-saliva-test-kit-zrt)).

### 6.3 WADA / anti‑doping exposure
A **substantial fraction of the panel** sits on or near the WADA Prohibited List:
- **Growth‑hormone secretagogues**[^secretagogue] (CJC‑1295, Ipamorelin, GHRP‑2, MGF) — S2 banned.
- **TB‑500 / Thymosin β4** — S2 banned.
- **BPC‑157** — currently S0 (non‑approved), banned in‑ and out‑of‑competition since 2022.
- **GH releasers more broadly, IGF‑1 elevation** — S2.
- **Erythropoietic and angiogenic peptides** — S2.
- AOD‑9604 paper exists *because* WADA needed to confirm its hGH isoform immunoassay is not fooled by AOD‑9604 ([Orlovius et al., 2013, DTA](https://doi.org/10.1002/dta.1557)). That same paper is now used by Olympic federations to clear AOD‑9604 users; do not assume the same applies to other peptides in the list.

If the engine's customer base includes any professional or NCAA athletes, the platform almost certainly needs an **explicit athlete‑exclusion or therapeutic‑use‑exemption[^tue] workflow** layered on the biomarker workflow.

### 6.4 Oncology surveillance flags built into the panels
The panel author already wired in three oncology safety hooks:
- **Epitalon** → "Cancer surveillance (theoretical telomerase[^telomerase] risk)" — sensible; telomerase reactivation is a hallmark of malignancy.
- **MGF** → "Baseline tumor screen" — IGF‑1‑axis activation.
- **Dihexa** → "Baseline tumor screen (HGF/c‑Met oncogenic concern)" — c‑Met[^cmet] is a validated oncogenic driver.
- **Melanotan II** → "Dermoscopic naevus surveillance (melanoma risk)" — multiple case reports of dysplastic nevi[^dysplasticnevi] changes.

These are **the four panels where insurance / liability exposure is highest**. A pre‑treatment age‑appropriate cancer screen (PSA, mammogram, colon, full‑body dermatology) should be a **gating SOP**, not an optional extra.

---

## 7 · Practical operational considerations

### 7.1 Specimen logistics
- **Serum / plasma cytokines, BDNF[^bdnf], NGF, VEGF** — temperature‑sensitive. Need centrifugation[^centrifugation] within 30 min and –80 °C storage. Hub‑and‑spoke courier model with dry‑ice shipping required if drawing at distributed clinics.
- **Salivary cortisol / α‑MSH metabolites** — stable at room temperature 1–2 weeks; courier‑friendly; great fit for direct‑to‑home kits.
- **Urinary aMT6s (Epitalon)** — first‑morning void or overnight collection; refrigerate; protein cup logistics straightforward.
- **Wound photography, dermoscopy, trichoscopy** — standardize lighting, distance, angle. Without a standardized protocol the readouts are visually appealing but quantitatively useless.
- **Stool calprotectin** — 1–2 g sample, stable 3 days refrigerated. DTC kit costs \$5–\$10; ELISA on the back end is the cost.

### 7.2 Timeframe / cadence design

The engine's `timeframe_weeks_min/max` field and the `tau_weeks`[^tau] constants in [`biomarker_params.py`](https://github.com/florida-man-bioscience/u4u-engine/blob/main/engine/tracking/biomarker_params.py) already encode the right cadence for most markers:

- **Fast‑moving (τ = 0.5–2 weeks):** GH peak/AUC, NOx, VEGF, wound closure, IL‑6 → measurable by week 2, draws at baseline, 2 w, 6 w, 12 w.
- **Medium (τ = 3–6 weeks):** IGF‑1, IGFBP‑3, IL‑6, pain VAS, HAM‑A, GAD‑7, HOMA‑IR → baseline, 4 w, 12 w cadence is right.
- **Slow (τ = 8–12 weeks):** HbA1c, lean body mass, hair density, MoCA → only worth measuring at baseline, 12 w, 24 w.

**Cost optimization:** Drop redundant intermediate timepoints on slow markers. A 24‑week HbA1c‑heavy GLP‑1 program does not need 4‑week HbA1c (it has not moved); it needs 4‑week tolerability + 12 w / 24 w HbA1c. That single change can take a Semaglutide/Tirzepatide protocol from \$450 to \$300 per participant without losing signal.

### 7.3 Data infrastructure
- The engine emits structured `BiomarkerMeasurement` records with `direction`, `timeframe_weeks_min/max`, and free‑text `effect_size`[^effectsize]; the numeric effect magnitude and the response time constant `tau_weeks` are attached per marker in [`biomarker_params.py`](https://github.com/florida-man-bioscience/u4u-engine/blob/main/engine/tracking/biomarker_params.py). This schema **already feeds the shipped responder model**[^bayes]: the Hierarchical Bayesian Responder Index (HBRI) computes a genotype‑driven responder index η in [`tracking/responder_index.py`](https://github.com/florida-man-bioscience/u4u-engine/blob/main/engine/tracking/responder_index.py) and updates a Normal–Normal posterior over each biomarker trajectory in [`tracking/bayes.py`](https://github.com/florida-man-bioscience/u4u-engine/blob/main/engine/tracking/bayes.py).
- The headline research asset is **the longitudinal database that pairs peptide + dose + biomarker trajectory + outcome**. Each enrolled participant contributing 3 timepoints is one data point in a precision‑peptide model that does not exist anywhere else outside Phase‑2/3 industry trials.
- Plan the data pathway so that this observational data set is usable as a real‑world‑evidence[^rwe] package. Because FMB only observes treatment‑as‑usual and never supplies, doses, or directs any peptide, the study sits outside IND[^ind] (21 CFR 312.2(b)) and is a minimal‑risk observational design eligible for expedited review under the UF single IRB. The operative requirements are **informed consent plus HIPAA authorization obtained at each partner clinic**, a **BAA/DUA** governing PHI flow from the clinic to FMB, GCP[^gcp]‑lite SOPs, consent language covering secondary use, and de‑identification compatible with HIPAA Safe Harbor[^safeharbor]. The captured biomarker data is **research‑grade, not CLIA[^clia] clinical‑reportable**.

### 7.4 Liability hot spots
1. **Melanotan II** dysplastic nevus / melanoma — a single missed melanoma in a tanning user is an existential lawsuit.
2. **Dihexa / MGF** oncologic activation — c‑Met and IGF‑1 elevation in undiagnosed cancer.
3. **Kisspeptin** — ovarian hyperstimulation, multiple gestation in fertility use cases.
4. **GLP‑1 class** — medullary thyroid carcinoma / MEN2[^men2] contraindication[^contraindication]; pancreatitis; gallbladder; gastroparesis under anesthesia.
5. **Semax / Dihexa / Selank** — cognitive enhancement claims fall under FTC[^ftc]/FDA misleading‑claim risk if marketed beyond "off‑label research".

The engine already encodes the right surveillance markers in its `safety_markers` tuples; the operational gap is informed consent, HIPAA authorization, and SOPs, not measurements. Because peptides are prescribed and dosed by the participant's own clinician, treatment‑related safety decisions remain with that clinician; FMB observes and records.

---

## 8 · Recommended scorecard for prioritizing the panels

If the goal is to stand up observational tracking for a subset of the 23 panels first, sort by **(signal density × reimbursement support × low capital intensity × tolerable regulatory profile)**.[^signaldensity]

**Top quartile (build first):**
- **Semaglutide / Tirzepatide / Liraglutide** — FDA‑approved, reimbursable, cheap biomarkers, mainstream prescribing. Build the metabolic tracking cohort here.
- **CJC‑1295, Ipamorelin** — high consumer demand, well‑understood IGF‑1 readout, DXA fits in‑sourcing path, but FDA / WADA exposure.
- **BPC‑157** — strong off‑label demand, cheap MSK ultrasound + VAS endpoints, but FDA 503A category‑2 risk.
- **MOTS‑c** — cheap metabolic panel, growing aging market.

**Middle quartile (build second):**
- **GHK‑Cu** — strong consumer story (skin/hair), modest assay cost, low regulatory heat (sold as cosmeceutical[^cosmeceutical] for years).
- **Thymosin α1** — strongest evidence base; CD4/CD8 + IFN‑γ is expensive but reimbursable in viral indications; ex‑U.S. approval gives an international story.
- **KPV** — fecal calprotectin is cheap and reimbursable; UC/IBD[^ibd] adjunct is a real unmet need; complements gastroenterology referrals.
- **Epitalon** — cheap urinary aMT6s + telomere T/S; "longevity" pricing power; cancer‑surveillance overhead.

**Bottom quartile (carry but de‑prioritize):**
- **Dihexa, Semax, DSIP, MGF, Melanotan II, Kisspeptin** — expensive endpoints (MRI, PSG, transvaginal US), highest oncologic/CV liability, smaller addressable market.
- **TB‑500, Thymosin β4, AOD‑9604, LL‑37, Selank** — niche demand or evidence gaps; keep as catalog items but not pillars.

---

## 9 · One‑line conclusion

The peptide panels in `u4u-engine` are **mostly cheap to measure but expensive to operate**: 60–70 % of the markers are commodity LabCorp/Quest analytes under \$30, and the real cost — and the real moat — sits in (a) the imaging modalities (DXA, MSK US, MRI, PSG), (b) the ELISA/multiplex stack, (c) the regulatory perimeter around compounded peptides and the 2024 LDT rule, and (d) the longitudinal data asset that the biomarker database creates over time.

---

## Appendix · Files and sources

- Repository: [florida-man-bioscience/u4u-engine](https://github.com/florida-man-bioscience/u4u-engine)
- Engine modules referenced: [`engine/peptides/biomarkers.py`](https://github.com/florida-man-bioscience/u4u-engine/blob/main/engine/peptides/biomarkers.py), [`engine/peptides/measurements.py`](https://github.com/florida-man-bioscience/u4u-engine/blob/main/engine/peptides/measurements.py), [`engine/tracking/biomarker_params.py`](https://github.com/florida-man-bioscience/u4u-engine/blob/main/engine/tracking/biomarker_params.py)
- Structured inventory: the `PEPTIDE_MEASUREMENTS` dict in [`engine/peptides/measurements.py`](https://github.com/florida-man-bioscience/u4u-engine/blob/main/engine/peptides/measurements.py) (181 measurement records)
- Pricing sources: LabCorp PA sheets ([IHW Aug 2025](https://static1.squarespace.com/static/6882d28a87311f496e6204a6/t/68a69d4b36eceb142f2d3838/1755749707225/Integrity+Health+%26+Wellness+-+Common+LabCorp+Prices+-+August+2025.pdf), [Ally Primary Care 2025](https://static1.squarespace.com/static/63a8aaf1bfe65d3cb8d85ae6/t/6838b64bc8521a1bc0d4c445/1748547147439/LabCorp+2025+Pricing.pdf)), [JustLabs / Quest](https://justlabs.health/tests/igf-1), [Well Built Florida HOMA‑IR guide](https://wellbuiltflorida.com/homa-ir-test-cost-pricing/), [LatestCost HOMA‑IR](https://latestcost.com/homa-ir-test-cost-prices-budget-tips/), [OHSU Endocrine Technologies Core](https://www.ohsu.edu/sites/default/files/2024-06/YR65%20Endocrine%20Technologies%20Core%20External%20Rate%20Sheet.pdf), [Ulta Lab Tests IL‑6](https://www.ultalabtests.com/test/interleukin-6-test), [Biosensis BDNF/NGF kits](https://www.biosensis.com/products/elisa-kits-reagents/elisa-kits.html), [Columbia FY22 Biomarkers Core](https://www.irvinginstitute.columbia.edu/file/6037/download?token=SkSL2oWw), [Montana State CAIRHE ELISA list](https://www.montana.edu/cairhe/translational-biomarkers-core/pricing-lists/ELISAs-saliva-11.19.19.pdf), [NCBI PMC2562869 — ELISA vs multiplex](https://pmc.ncbi.nlm.nih.gov/articles/PMC2562869/table/T1/), [AAFP fecal calprotectin review](https://www.aafp.org/afp/2021/0900/p303), [LabCorp CD4/CD8 via Find Lab Tests](https://www.findlabtest.com/lab-test/general-wellness/helper-t-lymphocyte-marker-cd4-labcorp-505008), [LabCorp HBV‑PCR](https://www.findlabtest.com/lab-test/general-wellness/hepatitis-b-virus-hbv-quantitative-dna-real-time-pcr-nongraphical-labcorp-551610), [Telomerase qTRAP \$2/rxn](https://pmc.ncbi.nlm.nih.gov/articles/PMC7847253/), [TeloYears review](https://nebula.org/blog/teloyears-review/), [Life Length F‑ISH](https://www.independent.co.uk/news/science/the-163-400-test-that-tells-you-how-long-you-ll-live-2284639.html), [Precision Health by Science DXA](https://precisionhealthbyscience.com/dexa/), [Endocrine Advantage DXA](https://www.endocrineadvantage.com/pricing), [Desert Dexa](https://desertdexa.com), [Body Analytics DXA](https://bodyanalytics.fit/pricing/), [Turquoise Health shoulder US](https://turquoise.health/services/ultrasound-shoulder-jointsoft-tissue/), [RAD Clinics MSK US](https://radclinics.co.uk/fee-guide-aylesbury/), [Hair Restoration Tour trichoscopy](https://hairrestorationtour.com/trichoscopy/), [Shapiro Medical trichoscopy](https://shapiromedical.com/blog/trichoscopy-hair-loss-diagnosis/), [Hair Loss Korea scalp biopsy](https://hairlosskorea.com/hair-loss-diagnosis-korea-complete-guide/), [Sudha Fertility Centre TVUS](https://sudhafertilitycentre.com/blog/fertility-tests-for-women/), [MedicalPriceCheck MRI brain](https://medicalpricecheck.com/research/mri-cost/), [MyCareCost brain MRI](https://mycarecost.net/brain-mri-cost), [SleepDr PSG cost](https://sleepdr.com/the-sleep-blog/how-much-will-a-sleep-study-cost-me), [GoodRx sleep study](https://www.goodrx.com/health-topic/procedures/how-much-sleep-study-cost), [Sleep Foundation](https://www.sleepfoundation.org/sleep-studies/how-much-does-a-sleep-study-cost), [Partec CyFlow CD4](http://www.cyto.purdue.edu/cdroms/cyto10a/sponsors/media/partec/cyflowsl3.pdf), [ZRT Sleep Balance/Diurnal Cortisol](https://labtestsplus.com/product/sleep-balance-profile-zrt-labs/), [Evenbetternow ZRT state restrictions](https://www.evenbetternow.com/products/diurnal-cortisol-saliva-test-kit-zrt).
- Primary peptide reference embedded in panels (e.g., [Orlovius et al. 2013, DTA — AOD‑9604 WADA assay](https://doi.org/10.1002/dta.1557)).

---

## Footnotes

[^peptide]: **Peptide** — a short chain of amino acids (a small protein fragment). Therapeutic peptides mimic or modulate signaling molecules in the body.
[^panel]: **Panel** — a predefined bundle of lab/imaging measurements tracked together for one therapy (here, one per peptide).
[^biomarker]: **Biomarker** — a measurable biological indicator (a blood level, image metric, or score) used to track a drug's effect or safety.
[^assay]: **Assay** — a laboratory test that detects or quantifies a specific substance in a sample.
[^peptidelist]: **The 23 peptides** — investigational/therapeutic peptides grouped by use: tissue repair (BPC‑157, TB‑500/Thymosin β4, GHK‑Cu, MGF, LL‑37, KPV), growth-hormone axis (CJC‑1295, Ipamorelin, GHRP‑2, AOD‑9604, MOTS‑c), immune (Thymosin α1), longevity/neuro (Epitalon, Selank, Semax, DSIP, Dihexa), reproductive/cosmetic (Kisspeptin, Melanotan II), and the FDA-approved GLP‑1 metabolic drugs (Semaglutide, Tirzepatide, Liraglutide).
[^clinchem]: **Clinical chemistry** — routine blood/urine chemistry tests (enzymes, glucose, lipids, electrolytes); high-volume, cheap, and widely reimbursed.
[^immunoassay]: **Immunoassay** — a test that uses antibodies to detect/measure a target molecule (e.g. a hormone); the basis of most ELISA and hormone tests.
[^physicianaccount]: **Physician-account (PA) pricing** — the discounted lab rate available to clinicians ordering tests, far below hospital "list/sticker" prices.
[^analyte]: **Analyte** — the specific substance a test measures (e.g. IGF‑1, glucose).
[^elisa]: **ELISA (Enzyme-Linked Immunosorbent Assay)** — a common plate-based immunoassay that quantifies one protein per well using a color/enzyme readout.
[^multiplex]: **Multiplex** — an assay format measuring many analytes from one sample simultaneously; cheaper per analyte at scale than running separate single-plex tests.
[^psg]: **Polysomnography (PSG)** — an overnight in-lab sleep study recording brain waves, breathing, oxygen, and movement; expensive. A home sleep apnea test (HSAT) is the cheaper alternative.
[^cytokine]: **Cytokine** — a small signaling protein of the immune system (e.g. IL‑6, TNF‑α, IFN‑γ); used here as inflammation markers.
[^mri]: **MRI (Magnetic Resonance Imaging)** — a high-resolution, non-radiation imaging method; the single most expensive readout in any panel.
[^clia]: **CLIA (Clinical Laboratory Improvement Amendments)** — U.S. federal certification a lab must hold to report patient results; complexity tiers (waived → high) gate which tests it may run.
[^ldt]: **LDT (Laboratory-Developed Test)** — a test designed, made, and used within a single lab. The 2024 FDA Final Rule is phasing these under medical-device (IVD) regulation.
[^dtc]: **DTC (Direct-To-Consumer)** — sold straight to the public without a clinician order; several U.S. states restrict DTC lab testing.
[^compounding]: **Compounded peptide** — a drug custom-made by a pharmacy rather than a mass-manufactured FDA-approved product; governed by sections 503A/503B.
[^503]: **503A / 503B** — sections of the U.S. Food, Drug & Cosmetic Act: 503A covers traditional pharmacy compounding for an individual prescription; 503B covers registered "outsourcing facilities" that compound at scale under cGMP.
[^wada]: **WADA (World Anti-Doping Agency)** — sets the Prohibited List for sport; "S0/S2" are its categories (S0 = non-approved substances, S2 = peptide hormones/growth factors).
[^ghaxis]: **GH-axis** — the growth-hormone signaling system (hypothalamus → pituitary GH → liver IGF‑1); many of these peptides act on it, which is why they draw anti-doping scrutiny.
[^erythropoiesis]: **Erythropoiesis** — red blood cell production; peptides that stimulate it (or angiogenesis) raise doping concerns and cardiovascular risk.
[^modality]: **Modality** — the category/method of a measurement (lab chemistry, imaging, questionnaire, etc.).
[^hba1c]: **HbA1c** — glycated hemoglobin, reflecting average blood glucose over ~3 months; the standard diabetes-control marker.
[^homair]: **HOMA-IR** — Homeostatic Model Assessment of Insulin Resistance, a value computed from fasting glucose and insulin estimating how insulin-resistant a person is.
[^psa]: **PSA (Prostate-Specific Antigen)** — a blood marker used in prostate cancer screening; relevant as a safety check for GH-axis peptides.
[^hscrp]: **hs-CRP** — high-sensitivity C-reactive protein, a sensitive blood marker of systemic inflammation.
[^dxa]: **DXA** — Dual-energy X-ray Absorptiometry, a low-dose scan measuring body composition (fat/lean mass) and bone density.
[^msk]: **MSK ultrasound** — musculoskeletal ultrasound imaging of tendons, muscles, and joints.
[^trichoscopy]: **Trichoscopy** — magnified imaging of the scalp/hair used to quantify hair density and follicle health.
[^dwi]: **DWI** — Diffusion-Weighted Imaging, an MRI sequence sensitive to tissue microstructure and acute brain changes.
[^dermoscopy]: **Dermoscopy** — magnified skin-surface imaging used to monitor moles/lesions for melanoma.
[^igf1]: **IGF-1 / IGFBP-3** — Insulin-like Growth Factor 1 and its binding protein 3; downstream readouts of growth-hormone activity.
[^auc]: **AUC (Area Under the Curve)** — the integrated total of a marker measured across several timed draws (e.g. a GH stimulation test), capturing cumulative exposure rather than a single value.
[^growthfactors]: **Growth factors / proteomic markers (VEGF, MMP-2, HGF, NGF, etc.)** — proteins driving tissue growth, remodeling, and repair; measured to track a peptide's regenerative effect.
[^scales]: **Patient-reported / functional scales** — standardized questionnaires and clinician-administered tests: VAS (pain visual analog scale), HAM-A / GAD-7 (anxiety), MoCA / ADAS-cog (cognition), NIHSS (stroke severity), IIEF-5 (erectile function), OSDI (dry eye), PSQI (sleep quality), Stroop (attention), COWS (opioid withdrawal).
[^transcriptomic]: **Transcriptomic** — measurement of gene expression (mRNA transcript levels), indicating which genes a tissue is actively using.
[^metabolomic]: **Metabolomic** — measurement of small-molecule metabolites (e.g. NOx nitric-oxide markers, 5-HIAA a serotonin metabolite), reflecting biochemical activity.
[^calprotectin]: **Fecal calprotectin** — a stool protein marker of gut inflammation; a cheap, non-invasive proxy that can avoid colonoscopy.
[^cd4]: **CD4/CD8 ratio** — counts of helper (CD4) vs cytotoxic (CD8) T-cells, an immune-status readout (e.g. for Thymosin α1).
[^neurotrophin]: **Neurotrophin** — a protein supporting neuron growth/survival (e.g. BDNF, NGF); measured for the neuro-active peptides.
[^telomere]: **Telomere** — the protective DNA cap at chromosome ends that shortens with cell division; telomere length is used as an aging biomarker. "T/S" is the telomere-to-single-copy-gene ratio.
[^qpcr]: **qPCR** — quantitative Polymerase Chain Reaction, a method that amplifies and counts specific DNA/RNA sequences; used to measure telomere length, viral load, and gene expression.
[^ihc]: **IHC (Immunohistochemistry)** — staining tissue sections with antibodies to visualize where a protein is expressed; requires a biopsy.
[^edc]: **EDC (Electronic Data Capture)** — software for collecting and managing clinical-study data (e.g. REDCap, Castor).
[^redcap]: **REDCap** — a widely used, free-for-academia EDC platform for building study data forms and surveys.
[^epro]: **ePRO (electronic Patient-Reported Outcomes)** — digital collection of questionnaire responses directly from patients.
[^cro]: **CRO (Contract Research Organization)** — an outside company that runs lab work or clinical-trial operations on a sponsor's behalf.
[^capex]: **Capex (Capital expenditure)** — up-front spending on durable equipment/infrastructure, as opposed to per-sample operating cost.
[^msd]: **MSD (Meso Scale Discovery)** — a vendor of electrochemiluminescence multiplex immunoassay platforms (e.g. QuickPlex) for measuring many cytokines at once.
[^lims]: **LIMS (Laboratory Information Management System)** — software tracking samples, tests, and results through a lab's workflow.
[^fte]: **FTE (Full-Time Equivalent)** — one full-time staff member's worth of labor; a unit for headcount/cost planning.
[^flowcytometry]: **Flow cytometry** — a technique that streams cells past lasers to count and characterize them by surface markers (e.g. CD4/CD8 T-cells).
[^sop]: **SOP (Standard Operating Procedure)** — a written, validated protocol ensuring a process is performed consistently (required for regulated labs).
[^lft]: **LFTs (Liver Function Tests)** — a blood panel (ALT, AST, etc.) assessing liver health/safety.
[^cpt]: **CPT code** — Current Procedural Terminology, the standardized billing codes for medical services/tests used by U.S. insurers.
[^icd10]: **ICD-10** — the International Classification of Diseases (10th revision) diagnosis codes; reimbursement requires an ICD-10 diagnosis that justifies the test.
[^offlabel]: **Off-label** — using an approved drug, or ordering a test, for a purpose not in its FDA-approved indication; generally not reimbursed.
[^em]: **E&M code** — Evaluation and Management billing codes for a clinician visit; some services (like administering scales) are bundled into them rather than billed separately.
[^indication]: **Indication** — the specific approved medical condition a drug/test is intended for.
[^glp1]: **GLP-1 (class)** — Glucagon-Like Peptide-1 receptor agonists (semaglutide, tirzepatide, liraglutide); FDA-approved drugs for diabetes and obesity.
[^t2dm]: **T2DM** — Type 2 Diabetes Mellitus.
[^hypogonadism]: **Hypogonadism** — clinically low sex-hormone production; a recognized indication for some hormone-axis workups.
[^ghd]: **GHD (Growth Hormone Deficiency)** — a documented deficiency that justifies (and makes reimbursable) GH-axis testing/treatment.
[^sku]: **SKU (Stock Keeping Unit)** — a single sellable product/inventory item; bundling peptide + test as one SKU sells them as a unit.
[^dbs]: **Dried blood spot (DBS)** — a few drops of blood dried on a card; a shippable, low-cost, at-home sampling method.
[^phlebotomy]: **Phlebotomy** — the act of drawing blood for testing.
[^cogs]: **COGS (Cost of Goods Sold)** — the direct cost to deliver one unit of service (labs, supplies, labor), before marketing/overhead.
[^grossmargin]: **Gross margin** — the share of the sell price left after COGS; here ~45–65%, before customer-acquisition cost.
[^cac]: **CAC (Customer Acquisition Cost)** — the average marketing/sales spend to acquire one paying customer; "payback in 1 cycle" means the first purchase recovers it.
[^cgmp]: **cGMP (current Good Manufacturing Practice)** — FDA-enforced manufacturing quality standards required of 503B outsourcing facilities and drug makers.
[^phase]: **Phase 2b** — a mid-stage clinical trial testing efficacy and dose; "failed Phase 2b" means it did not show enough benefit to advance.
[^gras]: **GRAS (Generally Recognized As Safe)** — an FDA food-additive status; it permits use as a food ingredient but does NOT authorize use as a drug.
[^ivd]: **IVD (In Vitro Diagnostic)** — a regulated diagnostic test/device; the FDA LDT rule pushes lab-developed tests toward formal IVD validation.
[^grandfather]: **Grandfather pocket** — a narrow exemption letting some existing tests continue under old rules rather than meeting the new requirements.
[^secretagogue]: **Secretagogue** — a substance that triggers secretion of another; GH secretagogues prompt the body to release its own growth hormone.
[^tue]: **TUE (Therapeutic Use Exemption)** — anti-doping authorization letting an athlete use an otherwise-banned substance for a legitimate medical need.
[^telomerase]: **Telomerase** — the enzyme that rebuilds telomeres; its reactivation lets cells divide indefinitely and is a hallmark of cancer.
[^cmet]: **c-Met / HGF** — a receptor (c-Met) and its growth-factor ligand (HGF) that drive cell proliferation; overactivity is a validated cancer (oncogenic) pathway.
[^dysplasticnevi]: **Dysplastic nevi** — atypical moles that can be precursors to melanoma; warrant surveillance under a melanin-stimulating peptide like Melanotan II.
[^bdnf]: **BDNF** — Brain-Derived Neurotrophic Factor, a neurotrophin marker of brain plasticity; temperature-sensitive in handling.
[^centrifugation]: **Centrifugation** — spinning a blood sample to separate serum/plasma from cells; must be done promptly to preserve labile markers.
[^tau]: **τ (tau_weeks)** — the characteristic timescale (in weeks) over which a biomarker responds; it sets the optimal sampling cadence (fast markers need early draws, slow markers only late ones).
[^bayes]: **Bayesian responder model** — a statistical model that updates the probability a patient is responding as each new measurement arrives, combining prior expectation with observed data.
[^effectsize]: **Effect size** — the standardized magnitude of a change/difference, indicating how large (not just whether) an effect is.
[^ind]: **IND (Investigational New Drug)** — an FDA application allowing a drug to be studied in humans; structuring data for an eventual IND keeps a regulatory path open.
[^rwe]: **Real-world evidence (RWE)** — clinical evidence derived from routine practice data (rather than a controlled trial), increasingly accepted by regulators.
[^gcp]: **GCP (Good Clinical Practice)** — the international ethical/quality standard for conducting clinical research; "GCP-lite" means lightweight but compatible procedures.
[^safeharbor]: **HIPAA Safe Harbor** — a U.S. de-identification method that removes 18 specified identifiers so health data is no longer "protected health information."
[^men2]: **MEN2** — Multiple Endocrine Neoplasia type 2, a hereditary syndrome with medullary thyroid carcinoma risk; a contraindication for GLP-1 drugs.
[^contraindication]: **Contraindication** — a condition that makes a treatment inadvisable or unsafe for that patient.
[^ftc]: **FTC (Federal Trade Commission)** — the U.S. regulator of advertising/marketing claims; aggressive efficacy claims risk FTC (and FDA) action.
[^signaldensity]: **Signal density** — how much useful, decision-relevant information a panel yields per dollar/effort spent; a prioritization criterion alongside reimbursement, capital intensity, and regulatory risk.
[^cosmeceutical]: **Cosmeceutical** — a product marketed between cosmetic and pharmaceutical (cosmetic claims, bioactive ingredient); lighter regulation than a drug.
[^ibd]: **UC / IBD** — Ulcerative Colitis, a form of Inflammatory Bowel Disease; an area of unmet therapeutic need relevant to the KPV peptide.
