# GLP-1 response evidence freeze

`glp1_response_gwas_freeze.tsv` is a transcription of Supplementary Table 5
from Dawed et al., *Lancet Diabetes & Endocrinology* (2023), DOI
`10.1016/S2213-8587(22)00340-0`, PMID `36528349`.

- Source PDF: `dawed_2023_glp1_response_supplement.pdf`
- Source SHA-256: `5abb27b0ae5d13a6d443e2232b0fbb64d00013acc1fca4e7ac96483b7e32970b`
- Rows: 16 suggestive loci (`p < 1×10⁻⁵`)
- Outcome: HbA1c reduction after GLP-1 receptor agonist treatment
- Cohort: GLP1RA meta-GWAS; reported `n` varies by locus

This is a **published evidence freeze**, not a full genome-wide summary-statistics
release and not patient-level data. It is not wired into production scoring.
The beta sign follows the supplement’s definition: a negative beta indicates
reduced response for the effective allele.

Before any catalog or model update, this freeze still requires:

1. independent transcription review against the PDF;
2. allele/build harmonization against the engine’s variant representation;
3. a prespecified weight mapping and genetics-off sensitivity; and
4. a new model/VCC review—published association is not clinical validation.
