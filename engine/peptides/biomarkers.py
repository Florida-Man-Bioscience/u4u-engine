"""
engine/peptides/biomarkers.py
==============================
Curated peptide → off-label-use → biomarker mapping for the 20 peptides
referenced on the regulatory dashboard (frontend/public/regulatory-dashboard.html).

Each entry lists:
  - off_label_uses    : the most-cited off-label / clinical applications
  - efficacy_markers  : measurable readouts of mechanism/response
  - safety_markers    : routine lab + organ-system monitoring
  - citation_apa      : APA-formatted primary reference
  - doi               : DOI link (constructed as https://doi.org/{doi})

All citations were retrieved via scite (mcp__scite__search_literature). No
fabricated references. See docs/peptide-biomarkers-references.md (generated)
for the full reference list. None of the cited papers carry editorial
notices at the time of writing.

Public API:
    get_biomarker_panel(peptide_name: str) -> BiomarkerPanel | None

The lookup tolerates the existing engine peptide names (e.g. "BPC-157",
"CJC-1295 + Ipamorelin", "Thymosin Alpha-1") via the ALIASES table.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Literal

Modality = Literal[
    "clinical_chem",          # standard chemistry panel (glucose, ALT, creatinine…)
    "hematology",             # CBC, differential
    "hormone",                # IGF-1, cortisol, LH, FSH, testosterone…
    "cytokine",               # IL-6, TNF-α, IFN-γ…
    "transcriptomic",         # mRNA or gene expression readout
    "metabolomic",            # small-molecule metabolite
    "proteomic",              # circulating protein not covered above
    "lipidomic",              # lipid species / panel
    "imaging",                # MRI, ultrasound, DXA, dermoscopy
    "physical",               # skin thickness, BP, grip strength, body composition
    "functional",             # VO₂max, range of motion, IIEF
    "patient_reported",       # VAS pain, HAM-A, GAD-7, MoCA, NIHSS
    "microbiome",             # stool 16S, fecal markers
]

Direction = Literal["increase", "decrease", "biphasic", "no_change", "variable"]
Purpose = Literal["efficacy", "safety", "mechanism", "selectivity"]


@dataclass(frozen=True)
class BiomarkerMeasurement:
    """A single literature-grounded measurement that tracks peptide response.

    Designed to feed a predictive model: every field except effect_size and
    citations is structured so the model can compare observed vs. expected.
    """
    name: str
    modality: Modality
    specimen: str                          # 'serum', 'plasma', 'urine', 'stool', 'skin biopsy', 'tendon US', 'self-report'…
    unit: str                              # 'ng/mL', '%', 'mm', 'score', etc. — '' for categorical
    direction: Direction                   # expected change vs. baseline
    timeframe_weeks_min: float | None      # earliest expected detectable change
    timeframe_weeks_max: float | None      # by when the effect typically plateaus
    purpose: Purpose                       # efficacy / safety / mechanism / selectivity
    effect_size: str | None = None         # free-text — '~+30% IGF-1', 'no change', etc.
    citation_apa: str | None = None        # APA reference; None = inherits panel-level citation
    doi: str | None = None                 # bare DOI; URL constructed at serialization

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["doi_url"] = f"https://doi.org/{self.doi}" if self.doi else None
        return d


@dataclass(frozen=True)
class BiomarkerPanel:
    peptide: str
    off_label_uses: tuple[str, ...]
    efficacy_markers: tuple[str, ...]
    safety_markers: tuple[str, ...]
    citation_apa: str
    doi: str
    measurements: tuple[BiomarkerMeasurement, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["doi_url"] = f"https://doi.org/{self.doi}" if self.doi else None
        d["measurements"] = [m.to_dict() for m in self.measurements]
        return d


# ── Canonical mapping ───────────────────────────────────────────────────────

PEPTIDE_BIOMARKERS: dict[str, BiomarkerPanel] = {
    "BPC-157": BiomarkerPanel(
        peptide="BPC-157",
        off_label_uses=(
            "Tendon, ligament, and muscle injury recovery",
            "Chronic knee / joint pain",
            "Gut barrier and inflammatory bowel symptoms",
        ),
        efficacy_markers=(
            "VEGF", "Nitric oxide (NO) metabolites", "IL-6", "TNF-α",
            "Pain VAS score", "MRI / US tendon thickness", "Range of motion",
        ),
        safety_markers=(
            "ALT / AST (LFTs)", "Creatinine / BUN", "CBC with differential",
            "Injection-site exam",
        ),
        citation_apa=(
            "Vasireddi, N., Hahamyan, H. A., Salata, M. J., et al. (2025). "
            "Emerging use of BPC-157 in orthopaedic sports medicine: A "
            "systematic review. HSS Journal, 21(4), 485–495."
        ),
        doi="10.1177/15563316251355551",
    ),
    "TB-500": BiomarkerPanel(
        peptide="TB-500",
        off_label_uses=(
            "Soft-tissue and cardiac repair",
            "Hair regrowth",
            "Liver fibrosis adjunct",
        ),
        efficacy_markers=(
            "VEGF", "MMP-2 / MMP-9", "Laminin-5", "Wound closure area",
            "Hair density (trichoscopy)",
        ),
        safety_markers=(
            "α-SMA / PDGFR fibrosis markers (research)", "ALT / AST",
            "CBC with differential",
        ),
        citation_apa=(
            "Kim, J., & Jung, Y. (2015). Potential role of thymosin beta 4 "
            "in liver fibrosis. International Journal of Molecular Sciences, "
            "16(5), 10624–10635."
        ),
        doi="10.3390/ijms160510624",
    ),
    "Thymosin Beta-4": BiomarkerPanel(
        peptide="Thymosin Beta-4",
        off_label_uses=(
            "Dry eye / corneal ulcer",
            "Dermal wound healing",
        ),
        efficacy_markers=(
            "Wound closure %", "VEGF", "Corneal staining score",
        ),
        safety_markers=("CBC", "LFTs"),
        citation_apa=(
            "Gao, X., Liang, H., Hou, F., et al. (2015). Thymosin beta-4 "
            "induces mouse hair growth. PLoS ONE, 10(6), e0130040."
        ),
        doi="10.1371/journal.pone.0130040",
    ),
    "GHK-Cu": BiomarkerPanel(
        peptide="GHK-Cu",
        off_label_uses=(
            "Skin healing and photoaging",
            "Scalp / hair restoration",
        ),
        efficacy_markers=(
            "Collagen I / III", "MMP-1 / MMP-2", "TGF-β1",
            "Wrinkle imaging score",
        ),
        safety_markers=(
            "Serum copper", "Ceruloplasmin", "ALT / AST",
        ),
        citation_apa=(
            "He, Q., Liao, Y., & Wu, Y. (2025). Bioactive oligopeptides and "
            "the application in skin regeneration and rejuvenation. Journal "
            "of Applied Biomaterials & Functional Materials, 23."
        ),
        doi="10.1177/22808000251330974",
    ),
    "MOTS-c": BiomarkerPanel(
        peptide="MOTS-c",
        off_label_uses=(
            "Insulin resistance / type 2 diabetes adjunct",
            "Exercise tolerance",
            "Post-menopausal metabolic decline",
        ),
        efficacy_markers=(
            "HOMA-IR", "Fasting glucose / insulin", "HbA1c",
            "IL-1β / IL-6", "VO₂max",
        ),
        safety_markers=("ALT / AST", "Lactate", "Creatine kinase"),
        citation_apa=(
            "Kim, S.-J., Miller, B., & Kumagai, H. (2019). MOTS-c: An equal "
            "opportunity insulin sensitizer. Journal of Molecular Medicine, "
            "97(4), 487–490."
        ),
        doi="10.1007/s00109-019-01758-0",
    ),
    "CJC-1295": BiomarkerPanel(
        peptide="CJC-1295",
        off_label_uses=(
            "Adult GH / IGF-1 augmentation",
            "Muscle preservation in aging",
        ),
        efficacy_markers=(
            "IGF-1", "IGFBP-3", "GH peak",
            "Lean body mass (DXA)",
        ),
        safety_markers=(
            "Fasting glucose / HbA1c", "PSA", "Edema / carpal tunnel exam",
            "IGF-1 ceiling vs. age-adjusted reference",
        ),
        citation_apa=(
            "Mayfield, C. K., Bolia, I. K., Feingold, C. L., et al. (2026). "
            "Injectable peptide therapy: A primer for orthopaedic and sports "
            "medicine physicians. American Journal of Sports Medicine, 54(1), "
            "223–229."
        ),
        doi="10.1177/03635465251357593",
    ),
    "Ipamorelin": BiomarkerPanel(
        peptide="Ipamorelin",
        off_label_uses=(
            "Pulsatile GH stimulation",
            "Sarcopenia adjunct",
        ),
        efficacy_markers=("IGF-1", "IGFBP-3", "GH AUC"),
        safety_markers=(
            "Cortisol (selectivity)", "Prolactin (selectivity)",
            "Fasting glucose",
        ),
        citation_apa=(
            "Ishida, J., Saitoh, M., Ebner, N., et al. (2020). Growth hormone "
            "secretagogues: History, mechanism of action, and clinical "
            "development. JCSM Rapid Communications, 3(1), 25–37."
        ),
        doi="10.1002/rco2.9",
    ),
    "GHRP-2": BiomarkerPanel(
        peptide="GHRP-2",
        off_label_uses=(
            "GH-deficiency diagnostic stimulation",
            "Appetite / cachexia management",
        ),
        efficacy_markers=("GH peak", "IGF-1", "IGFBP-3", "Body weight"),
        safety_markers=("Cortisol", "Prolactin", "ACTH", "Fasting glucose"),
        citation_apa=(
            "Ishida, J., Saitoh, M., Ebner, N., et al. (2020). Growth hormone "
            "secretagogues: History, mechanism of action, and clinical "
            "development. JCSM Rapid Communications, 3(1), 25–37."
        ),
        doi="10.1002/rco2.9",
    ),
    "MGF": BiomarkerPanel(
        peptide="MGF",
        off_label_uses=(
            "Muscle and cartilage repair",
            "Sarcopenia adjunct",
        ),
        efficacy_markers=(
            "Lean mass (DXA)", "Satellite cell markers", "IGF-1",
            "Grip strength",
        ),
        safety_markers=(
            "Fasting glucose", "IGF-1 ceiling", "Baseline tumor screen",
        ),
        citation_apa=(
            "Mills, P. R., Dominique, J.-C., Lafreniere, J. F., et al. "
            "(2007). A synthetic mechano-growth-factor E peptide enhances "
            "myogenic-precursor-cell transplantation success. American "
            "Journal of Transplantation, 7(10), 2247–2259."
        ),
        doi="10.1111/j.1600-6143.2007.01927.x",
    ),
    "AOD-9604": BiomarkerPanel(
        peptide="AOD-9604",
        off_label_uses=("Adiposity reduction",),
        efficacy_markers=(
            "Body weight", "Waist circumference", "% body fat (DXA)",
            "Leptin",
        ),
        safety_markers=(
            "WADA hGH isoform immunoassay (unaffected — confirms purity)",
            "Lipid panel", "Fasting glucose",
        ),
        citation_apa=(
            "Orlovius, A. K., Thomas, A., & Schänzer, W. (2013). AOD-9604 "
            "does not influence the WADA hGH isoform immunoassay. Drug "
            "Testing and Analysis, 5(11–12), 850–852."
        ),
        doi="10.1002/dta.1557",
    ),
    "Thymosin Alpha-1": BiomarkerPanel(
        peptide="Thymosin Alpha-1",
        off_label_uses=(
            "Chronic HBV / HCV adjunct",
            "Sepsis and immune restoration",
            "COVID-19 adjunctive immune support",
        ),
        efficacy_markers=(
            "CD4 / CD8 ratio", "Absolute lymphocyte count",
            "IFN-γ", "IL-2", "Viral load",
        ),
        safety_markers=("CBC with differential", "ALT / AST", "hs-CRP"),
        citation_apa=(
            "Dominari, A., Hathaway, D., & Pandav, K. (2020). Thymosin alpha "
            "1: A comprehensive review of the literature. World Journal of "
            "Virology, 9(5), 67–78."
        ),
        doi="10.5501/wjv.v9.i5.67",
    ),
    "Epitalon": BiomarkerPanel(
        peptide="Epitalon",
        off_label_uses=(
            "Geroprotection / longevity",
            "Sleep and circadian rhythm support",
        ),
        efficacy_markers=(
            "Nocturnal melatonin", "Telomerase activity", "AANAT", "IL-2",
        ),
        safety_markers=(
            "CBC", "Lipid panel", "Fasting glucose",
            "Cancer-surveillance (theoretical telomerase risk)",
        ),
        citation_apa=(
            "Araj, S. K., Brzezik, J., & Mądra-Gackowska, K. (2025). "
            "Overview of Epitalon—Highly bioactive pineal tetrapeptide with "
            "promising properties. International Journal of Molecular "
            "Sciences, 26(6), 2691."
        ),
        doi="10.3390/ijms26062691",
    ),
    "Selank": BiomarkerPanel(
        peptide="Selank",
        off_label_uses=(
            "Generalized anxiety disorder",
            "Anxiety-asthenia syndrome",
        ),
        efficacy_markers=(
            "HAM-A / GAD-7 score", "Serum BDNF", "Enkephalinase activity",
        ),
        safety_markers=("LFTs", "CBC"),
        citation_apa=(
            "Kasian, A., Kolomin, T., Andreeva, L., et al. (2017). Peptide "
            "Selank enhances the effect of diazepam in reducing anxiety. "
            "Behavioural Neurology, 2017, 5091027."
        ),
        doi="10.1155/2017/5091027",
    ),
    "Semax": BiomarkerPanel(
        peptide="Semax",
        off_label_uses=(
            "Ischemic stroke recovery",
            "Attention deficit / cognitive impairment",
        ),
        efficacy_markers=(
            "BDNF", "NGF", "NIHSS / MoCA score",
            "IL-1β / IL-6 / TNF-α",
        ),
        safety_markers=("Cortisol (negligible effect)", "CBC", "Blood pressure"),
        citation_apa=(
            "Kolomin, T., Shadrina, M. I., & Slominsky, P. A. (2013). A new "
            "generation of drugs: Synthetic peptides based on natural "
            "regulatory peptides. Neuroscience & Medicine, 4(4), 223–252."
        ),
        doi="10.4236/nm.2013.44035",
    ),
    "DSIP": BiomarkerPanel(
        peptide="DSIP",
        off_label_uses=(
            "Insomnia",
            "Chronic pain",
            "Opioid withdrawal",
        ),
        efficacy_markers=(
            "Polysomnography slow-wave-sleep %", "Sleep onset latency",
            "Serotonin (5-HIAA)",
        ),
        safety_markers=("Cortisol", "ACTH", "LH / FSH (HPA modulation)"),
        citation_apa=(
            "Koval'zon, V. M., & Strekalova, T. (2006). Delta sleep-inducing "
            "peptide (DSIP): A still unresolved riddle. Journal of "
            "Neurochemistry, 97(2), 303–309."
        ),
        doi="10.1111/j.1471-4159.2006.03693.x",
    ),
    "Dihexa": BiomarkerPanel(
        peptide="Dihexa",
        off_label_uses=(
            "Alzheimer's disease cognitive decline",
            "Parkinson's disease cognitive symptoms",
        ),
        efficacy_markers=(
            "MoCA / ADAS-cog", "Serum HGF", "c-Met activation (research)",
        ),
        safety_markers=(
            "LFTs", "Blood pressure",
            "Baseline tumor screen (HGF/c-Met oncogenic concern)",
        ),
        citation_apa=(
            "Wells, R. G., Azzam, A. F., Hiller, A., et al. (2024). Effects "
            "of an angiotensin IV analog on 3-nitropropionic-acid-induced "
            "Huntington's-disease-like symptoms in rats. Journal of "
            "Huntington's Disease, 13(1), 55–66."
        ),
        doi="10.3233/jhd-231507",
    ),
    "Kisspeptin": BiomarkerPanel(
        peptide="Kisspeptin",
        off_label_uses=(
            "Functional hypothalamic amenorrhea",
            "Infertility / ovulation induction",
            "Hypogonadism evaluation",
        ),
        efficacy_markers=(
            "LH", "FSH", "Estradiol", "Testosterone",
            "Ovulation (transvaginal US)",
        ),
        safety_markers=("Prolactin", "SHBG", "LFTs"),
        citation_apa=(
            "Patel, A., Koysombat, K., Pierret, A., et al. (2024). "
            "Kisspeptin in functional hypothalamic amenorrhea: "
            "Pathophysiology and therapeutic potential. Annals of the New "
            "York Academy of Sciences."
        ),
        doi="10.1111/nyas.15220",
    ),
    "Melanotan II": BiomarkerPanel(
        peptide="Melanotan II",
        off_label_uses=(
            "Cosmetic tanning",
            "Erectile dysfunction",
        ),
        efficacy_markers=(
            "Skin melanin index", "IIEF score",
        ),
        safety_markers=(
            "Dermoscopic naevus surveillance (melanoma risk)",
            "Blood pressure", "Priapism exam", "LFTs",
        ),
        citation_apa=(
            "Habbema, L., Halk, A. B., & Neumann, M. (2017). Risks of "
            "unregulated use of alpha-melanocyte-stimulating hormone "
            "analogues: A review. International Journal of Dermatology, "
            "56(10), 975–980."
        ),
        doi="10.1111/ijd.13585",
    ),
    "LL-37": BiomarkerPanel(
        peptide="LL-37",
        off_label_uses=(
            "Chronic / diabetic wound healing",
            "Antimicrobial adjunct in topical infection",
        ),
        efficacy_markers=(
            "Wound closure %", "Bacterial bioburden",
            "25-OH vitamin D",
        ),
        safety_markers=(
            "hs-CRP (pro-inflammatory risk at high dose)",
            "CBC", "LFTs",
        ),
        citation_apa=(
            "Frew, L., Makieva, S., McKinlay, A., et al. (2014). Human "
            "cathelicidin production by the cervix. PLoS ONE, 9(8), e103434."
        ),
        doi="10.1371/journal.pone.0103434",
    ),
    "KPV": BiomarkerPanel(
        peptide="KPV",
        off_label_uses=(
            "Ulcerative colitis / IBD",
            "Atopic dermatitis",
        ),
        efficacy_markers=(
            "Fecal calprotectin", "IL-6", "IL-1β", "TNF-α", "IFN-γ",
            "Endoscopic Mayo score",
        ),
        safety_markers=("CBC", "LFTs", "CRP"),
        citation_apa=(
            "Dalmasso, G., Charrier-Hisamuddin, L., Nguyen, H. T. T., et al. "
            "(2008). PepT1-mediated tripeptide KPV uptake reduces intestinal "
            "inflammation. Gastroenterology, 134(1), 166–178."
        ),
        doi="10.1053/j.gastro.2007.10.026",
    ),
    "Semaglutide": BiomarkerPanel(
        peptide="Semaglutide",
        off_label_uses=(
            "Weight management / obesity",
            "Type 2 diabetes glycemic control",
            "Cardiometabolic risk reduction",
        ),
        efficacy_markers=(
            "Body weight / BMI", "Waist circumference", "HbA1c",
            "Fasting glucose / insulin", "HOMA-IR", "Lipid panel",
        ),
        safety_markers=(
            "Lipase / amylase (pancreatitis)", "ALT / AST", "Heart rate",
            "Resting gallbladder ultrasound (if symptomatic)",
            "Thyroid exam (MTC/MEN2 contraindication screen)",
        ),
        citation_apa=(
            "Wilding, J. P. H., Batterham, R. L., Calanna, S., et al. (2021). "
            "Once-weekly semaglutide in adults with overweight or obesity. New "
            "England Journal of Medicine, 384(11), 989–1002."
        ),
        doi="10.1056/NEJMoa2032183",
    ),
    "Tirzepatide": BiomarkerPanel(
        peptide="Tirzepatide",
        off_label_uses=(
            "Weight management / obesity",
            "Type 2 diabetes glycemic control",
            "Obstructive sleep apnea adjunct",
        ),
        efficacy_markers=(
            "Body weight / BMI", "Waist circumference", "HbA1c",
            "Fasting glucose / insulin", "HOMA-IR", "Lipid panel",
        ),
        safety_markers=(
            "Lipase / amylase (pancreatitis)", "ALT / AST", "Heart rate",
            "Thyroid exam (MTC/MEN2 contraindication screen)",
        ),
        citation_apa=(
            "Jastreboff, A. M., Aronne, L. J., Ahmad, N. N., et al. (2022). "
            "Tirzepatide once weekly for the treatment of obesity. New England "
            "Journal of Medicine, 387(3), 205–216."
        ),
        doi="10.1056/NEJMoa2206038",
    ),
    "Liraglutide": BiomarkerPanel(
        peptide="Liraglutide",
        off_label_uses=(
            "Weight management / obesity",
            "Type 2 diabetes glycemic control",
        ),
        efficacy_markers=(
            "Body weight / BMI", "Waist circumference", "HbA1c",
            "Fasting glucose / insulin", "HOMA-IR",
        ),
        safety_markers=(
            "Lipase / amylase (pancreatitis)", "ALT / AST", "Heart rate",
            "Thyroid exam (MTC/MEN2 contraindication screen)",
        ),
        citation_apa=(
            "Pi-Sunyer, X., Astrup, A., Fujioka, K., et al. (2015). A "
            "randomized, controlled trial of 3.0 mg of liraglutide in weight "
            "management. New England Journal of Medicine, 373(1), 11–22."
        ),
        doi="10.1056/NEJMoa1411892",
    ),
}


# ── Aliases — match the names already used by engine/annotators/peptide_mapper.py ──

ALIASES: dict[str, str] = {
    # peptide_mapper.PEPTIDE_GENE_MAP keys → canonical biomarker keys
    "BPC-157": "BPC-157",
    "BPC-157 + TB-500": "BPC-157",                          # composite — show BPC-157 panel
    "GHK-Cu + BPC-157 + TB-500": "GHK-Cu",                  # composite — show GHK-Cu panel
    "CJC-1295 + Ipamorelin": "CJC-1295",
    "Thymosin Alpha-1": "Thymosin Alpha-1",
    "Epithalon": "Epitalon",
    "AOD-9604": "AOD-9604",
    "MOTS-c": "MOTS-c",
    "MOTS-C": "MOTS-c",
    "Matrixyl": "GHK-Cu",                                   # collagen pathway — closest validated panel
    "Argireline": "GHK-Cu",                                 # no peptide-specific human biomarker
    "SNAP-8": "GHK-Cu",
    # Dashboard peptides not yet in peptide_mapper get their own canonical entries
    "TB-500": "TB-500",
    "Thymosin Beta-4": "Thymosin Beta-4",
    "GHK-Cu": "GHK-Cu",
    "Ipamorelin": "Ipamorelin",
    "GHRP-2": "GHRP-2",
    "MGF": "MGF",
    "Epitalon": "Epitalon",
    "Selank": "Selank",
    "Semax": "Semax",
    "DSIP": "DSIP",
    "Dihexa": "Dihexa",
    "Kisspeptin": "Kisspeptin",
    "Melanotan": "Melanotan II",
    "Melanotan II": "Melanotan II",
    "LL-37": "LL-37",
    "KPV": "KPV",
    # GLP-1 / incretin class (peptide_mapper keys → canonical biomarker keys)
    "Semaglutide": "Semaglutide",
    "Tirzepatide": "Tirzepatide",
    "Liraglutide": "Liraglutide",
}


# ── Attach structured measurements ──────────────────────────────────────────
# Imported lazily here to avoid a circular import (measurements.py imports
# BiomarkerMeasurement from this module).
from .measurements import PEPTIDE_MEASUREMENTS  # noqa: E402

PEPTIDE_BIOMARKERS = {
    name: replace(panel, measurements=PEPTIDE_MEASUREMENTS.get(name, ()))
    for name, panel in PEPTIDE_BIOMARKERS.items()
}


def get_biomarker_panel(peptide_name: str) -> BiomarkerPanel | None:
    """Look up the biomarker panel for a peptide by canonical name or alias."""
    if not peptide_name:
        return None
    key = ALIASES.get(peptide_name) or ALIASES.get(peptide_name.strip())
    if not key:
        # Direct lookup as a last resort
        return PEPTIDE_BIOMARKERS.get(peptide_name)
    return PEPTIDE_BIOMARKERS.get(key)
