-- =============================================================================
-- Seed: peptide_seed_data.sql
-- Description: Initial 12 rows for peptide_condition_library — covering AR,
--              ESR1, ESR2, OXTR, MC4R, GLP1R, RET, TP53, and BRCA1 gene-
--              variant-peptide combinations for the PeptidIQ V3 menopause/
--              HRT protocol response engine.
-- Author:  PeptidIQ Engineering
-- Date:    2026-04-08
-- Depends: 003_peptide_condition_library.sql
-- =============================================================================

BEGIN;

INSERT INTO peptide_condition_library (
    gene_symbol,
    variant_type,
    rsid,
    variant_description,
    peptide_name,
    peptide_class,
    target_receptor,
    response_direction,
    confidence_tier,
    mechanism_summary,
    dosing_guidance,
    trade_off_text,
    contraindication_flag,
    contraindication_genes,
    kegg_pathways,
    source_pmids
)
VALUES

-- -------------------------------------------------------------------------
-- Row 1: AR / Short CAG repeat / Testosterone (topical) — ENHANCED
-- -------------------------------------------------------------------------
(
    'AR',
    'STR_repeat',
    NULL,
    'CAG repeat < 22 (short)',
    'Testosterone (topical)',
    'Androgen',
    'AR',
    'enhanced',
    'B',
    'Short AR CAG repeat (< 22) produces a hypersensitive androgen receptor with increased transactivation efficiency. Lower testosterone concentrations achieve equivalent downstream gene activation. Inverse correlation between CAG length and receptor transcriptional activity is well-established.',
    'Start at lower quartile of standard range (e.g., 0.25 mg topical instead of 0.5 mg). Monitor for androgenic excess at 4 weeks: acne, hair thinning, mood changes. Monthly CBC for polycythemia.',
    'Testosterone converts to DHT via 5-alpha-reductase (SRD5A2). Short CAG + high SRD5A2 activity = amplified DHT effects: hair loss, acne, LUTS. Monitor DHT:T ratio. Also converts to E2 via aromatase (CYP19A1) — monitor estradiol if symptoms of estrogen excess appear.',
    FALSE,
    NULL,
    ARRAY['map00140', 'hsa04912'],
    ARRAY['24165020', '23844628', '26421011']
),

-- -------------------------------------------------------------------------
-- Row 2: AR / Long CAG repeat / Testosterone (topical) — BLUNTED
-- -------------------------------------------------------------------------
(
    'AR',
    'STR_repeat',
    NULL,
    'CAG repeat > 27 (long)',
    'Testosterone (topical)',
    'Androgen',
    'AR',
    'blunted',
    'B',
    'Long AR CAG repeat (> 27) structurally perturbs the transactivation domain, requiring higher testosterone concentrations to achieve standard receptor activation. Patients may report subtherapeutic effects at standard doses.',
    'Start at standard dose but prepare for dose escalation at week 6 review. Consider pellet therapy for sustained higher levels if topical is insufficient. 3-month evaluation window before declaring treatment failure.',
    'Higher doses increase aromatization to estradiol. Monitor E2 at each dose escalation. Risk of polycythemia increases with supraphysiologic T levels.',
    FALSE,
    NULL,
    ARRAY['map00140', 'hsa04912'],
    ARRAY['24165020', '24593124', '21712734']
),

-- -------------------------------------------------------------------------
-- Row 3: AR / Pathologic CAG repeat > 35 / Testosterone (topical) — CONTRAINDICATED
-- -------------------------------------------------------------------------
(
    'AR',
    'STR_repeat',
    NULL,
    'CAG repeat > 35 (pathologic)',
    'Testosterone (topical)',
    'Androgen',
    'AR',
    'contraindicated',
    'A',
    'CAG repeat > 35 is in the Kennedy disease (SBMA) range. The expanded polyglutamine tract causes toxic protein aggregation in motor neurons. High-dose androgen therapy may accelerate neurotoxic aggregation.',
    'HALT androgen-based protocols. Mandatory neurology referral. This is a critical safety flag.',
    'Androgen receptor with > 35 CAG repeats is non-functional for therapeutic purposes and the expanded protein is directly neurotoxic under androgen stimulation.',
    TRUE,
    ARRAY['AR'],
    ARRAY['map00140'],
    ARRAY['24593124']
),

-- -------------------------------------------------------------------------
-- Row 4: ESR1 / rs2234693 PvuII T allele / Estradiol (E2) — ENHANCED
-- -------------------------------------------------------------------------
(
    'ESR1',
    'SNP',
    'rs2234693',
    'PvuII T allele',
    'Estradiol (E2)',
    'HRT',
    'ERalpha',
    'enhanced',
    'B',
    'ESR1 PvuII T allele is associated with enhanced non-genomic estrogen signaling via PI3K/AKT pathway and increased HDL response to estrogen therapy. Also associated with elevated breast cancer risk in multiple cohort studies.',
    'Standard estradiol dosing appropriate — patient may see above-average cardiovascular benefit. However, baseline mammography and annual breast monitoring recommended given elevated oncological risk.',
    'Enhanced estrogen signaling is a double-edged sword: cardioprotective (HDL, vascular function) but potentially oncogenic (ERalpha-driven breast proliferation). BRCA1/2 status must be confirmed before initiating estradiol in TT carriers.',
    FALSE,
    NULL,
    ARRAY['hsa04915', 'hsa04151'],
    ARRAY['17713466', '20827267', '17889406']
),

-- -------------------------------------------------------------------------
-- Row 5: ESR2 / rs1256049 A allele / Estradiol (E2) — ENHANCED (VTE flag)
-- -------------------------------------------------------------------------
(
    'ESR2',
    'SNP',
    'rs1256049',
    'A allele',
    'Estradiol (E2)',
    'HRT',
    'ERbeta',
    'enhanced',
    'B',
    'ESR2 rs1256049 A allele is associated with increased deep vein thrombosis and venous thromboembolism risk in HRT users. ERbeta modulates coagulation factor expression.',
    'This is a safety flag, not a dosing adjustment. Screen for VTE risk factors before initiating estrogen therapy. Consider transdermal route (lower VTE risk than oral). Avoid oral estrogen in carriers with additional VTE risk factors (Factor V Leiden, obesity, immobility).',
    'VTE risk is the primary trade-off. Oral estrogen increases hepatic clotting factor synthesis; transdermal bypasses first-pass metabolism and substantially reduces VTE risk. Genotype-informed route selection is the actionable recommendation.',
    FALSE,
    NULL,
    ARRAY['hsa04915'],
    ARRAY['17184825']
),

-- -------------------------------------------------------------------------
-- Row 6: OXTR / rs53576 AA genotype / Oxytocin (intranasal) — ENHANCED
-- -------------------------------------------------------------------------
(
    'OXTR',
    'SNP',
    'rs53576',
    'AA genotype',
    'Oxytocin (intranasal)',
    'Neuropeptide',
    'OXTR',
    'enhanced',
    'C',
    'OXTR rs53576 AA carriers have reduced baseline oxytocin receptor sensitivity and lower prosocial affect. Paradoxically, these patients may benefit most from exogenous oxytocin supplementation because they have the most room for improvement. Combined with ESR1 PvuII T allele, AA carriers showed significantly enhanced arousal and orgasm scores (FSFI).',
    'Standard intranasal oxytocin protocol. Consider co-administration with PT-141 for HSDD-presenting patients, especially if ESR1 PvuII T allele also present.',
    'Estrogen primes OXTR expression — declining estrogen in menopause reduces OXTR density. Exogenous oxytocin without estrogen co-administration may have reduced efficacy. Consider estradiol status when prescribing.',
    FALSE,
    NULL,
    ARRAY['hsa04726'],
    ARRAY['28093060', '26150031']
),

-- -------------------------------------------------------------------------
-- Row 7: MC4R / Loss-of-function variants / PT-141 (Bremelanotide) — BLUNTED
-- -------------------------------------------------------------------------
(
    'MC4R',
    'SNP',
    NULL,
    'Loss-of-function variants',
    'PT-141 (Bremelanotide)',
    'Melanocortin Agonist',
    'MC3R/MC4R',
    'blunted',
    'B',
    'MC4R loss-of-function variants reduce downstream melanocortin signaling. PT-141 (bremelanotide) is an MC3R/MC4R agonist. Reduced receptor function blunts the hypothalamic arousal cascade that PT-141 depends on.',
    'PT-141 may be ineffective. Consider alternative approaches for HSDD: oxytocin (different pathway), kisspeptin (upstream HPG axis), or combined oxytocin + low-dose PT-141.',
    'MC4R LOF is also associated with severe obesity and hyperphagia. If MC4R LOF is detected, the weight management conversation is as important as the sexual function conversation.',
    FALSE,
    NULL,
    ARRAY['hsa04916'],
    ARRAY['32487249', '23512951']
),

-- -------------------------------------------------------------------------
-- Row 8: GLP1R / rs3765467 A allele (Lys168Arg) / Semaglutide — BLUNTED
-- -------------------------------------------------------------------------
(
    'GLP1R',
    'SNP',
    'rs3765467',
    'A allele (Lys168Arg)',
    'Semaglutide',
    'GLP-1 RA',
    'GLP1R',
    'blunted',
    'B',
    'GLP1R rs3765467 (Lys168Arg) reduces GLP-1 binding affinity at the receptor. Lower binding affinity means standard semaglutide doses may produce subtherapeutic incretin signaling.',
    'Start at standard dose but set expectation for dose escalation at week 4. If < 5% body weight loss at 8 weeks on maximum tolerated dose, the genetic basis for reduced response is documented — switch to tirzepatide (dual GLP1R/GIPR agonist) which may partially compensate via the GIP pathway.',
    'Higher semaglutide doses increase GI side effects (nausea, vomiting, diarrhea). Dose escalation should be slow (every 4 weeks). Also screen RET proto-oncogene — GLP-1 RAs are contraindicated in MEN2/medullary thyroid carcinoma family history.',
    FALSE,
    NULL,
    ARRAY['hsa04151', 'hsa04920'],
    ARRAY['34170647']
),

-- -------------------------------------------------------------------------
-- Row 9: GLP1R / rs6923761 A allele (Arg131Gln) / Tirzepatide — BLUNTED
-- -------------------------------------------------------------------------
(
    'GLP1R',
    'SNP',
    'rs6923761',
    'A allele (Arg131Gln)',
    'Tirzepatide',
    'GLP-1 RA',
    'GLP1R/GIPR',
    'blunted',
    'B',
    'GLP1R rs6923761 (Arg131Gln) blunts GLP-1-stimulated insulin secretion. Tirzepatide''s dual GLP1R/GIPR agonism may partially compensate via the GIP pathway, but baseline GLP-1 sensitivity is reduced.',
    'Tirzepatide may outperform semaglutide in this genotype due to dual receptor engagement. Start at standard dose. Note: postmenopausal women on tirzepatide + MHT showed 35% greater weight loss than tirzepatide alone — estrogen status modifies GLP-1 RA efficacy.',
    'Same GI side effect profile as semaglutide. Additionally, rapid weight loss (> 1 kg/week) increases gallstone risk. Monitor hepatobiliary symptoms. PCSK9 LOF carriers may have altered bile acid metabolism — additional monitoring warranted.',
    FALSE,
    NULL,
    ARRAY['hsa04151', 'hsa04920'],
    ARRAY['34170647']
),

-- -------------------------------------------------------------------------
-- Row 10: RET / Pathogenic (MEN2) / Semaglutide — CONTRAINDICATED
-- -------------------------------------------------------------------------
(
    'RET',
    'SNP',
    NULL,
    'Pathogenic (MEN2)',
    'Semaglutide',
    'GLP-1 RA',
    'GLP1R',
    'contraindicated',
    'A',
    'RET proto-oncogene pathogenic variants cause Multiple Endocrine Neoplasia type 2 (MEN2) including medullary thyroid carcinoma (MTC). GLP-1 RAs caused thyroid C-cell tumors in rodent studies. FDA black box warning on all GLP-1 RAs.',
    'ABSOLUTE CONTRAINDICATION. Do not prescribe any GLP-1 RA (semaglutide, tirzepatide, liraglutide) in patients with RET pathogenic variants or personal/family history of MTC or MEN2.',
    'N/A — this is a hard contraindication, not a trade-off.',
    TRUE,
    ARRAY['RET'],
    ARRAY[]::TEXT[],
    ARRAY[]::TEXT[]
),

-- -------------------------------------------------------------------------
-- Row 11: TP53 / Pathogenic variants / BPC-157 — CONTRAINDICATED
-- -------------------------------------------------------------------------
(
    'TP53',
    'SNP',
    NULL,
    'Pathogenic variants',
    'BPC-157',
    'Tissue Repair',
    'VEGFR/EGFR/FAK',
    'contraindicated',
    'C',
    'BPC-157 promotes angiogenesis via VEGFR pathway and tissue growth via EGFR/FAK signaling. In a patient with TP53 pathogenic variants (Li-Fraumeni syndrome or somatic driver), these pro-growth signals may promote tumor vascularization and proliferation.',
    'CONTRAINDICATED. Do not prescribe BPC-157 in patients with TP53 pathogenic variants. Screen APC and KRAS as well — any active oncogenic driver is a contraindication to pro-angiogenic peptides.',
    'N/A — hard contraindication in the presence of oncogenic driver mutations.',
    TRUE,
    ARRAY['TP53', 'APC', 'KRAS'],
    ARRAY[]::TEXT[],
    ARRAY[]::TEXT[]
),

-- -------------------------------------------------------------------------
-- Row 12: BRCA1 / Pathogenic variants / Kisspeptin-10/54 — CONTRAINDICATED
-- -------------------------------------------------------------------------
(
    'BRCA1',
    'SNP',
    NULL,
    'Pathogenic variants',
    'Kisspeptin-10/54',
    'Neuropeptide',
    'KISS1R',
    'contraindicated',
    'B',
    'Kisspeptin activates KISS1R on GnRH neurons, stimulating LH/FSH secretion, which in turn stimulates ovarian estrogen production. In BRCA1/2 pathogenic carriers, stimulating estrogen synthesis increases breast and ovarian cancer risk.',
    'CONTRAINDICATED in BRCA1/2 pathogenic carriers unless oophorectomy has been performed (removing the estrogen source). If ovaries are intact, use non-estrogenic approaches for hot flash management.',
    'Kisspeptin''s mechanism of action inherently stimulates the HPG axis and estrogen production. This is the desired effect for most menopause patients but is the exact wrong signal in hereditary breast/ovarian cancer syndrome.',
    TRUE,
    ARRAY['BRCA1', 'BRCA2'],
    ARRAY['hsa04912'],
    ARRAY[]::TEXT[]
);

COMMIT;
