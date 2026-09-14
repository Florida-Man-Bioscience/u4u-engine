# PeptOdyssey genotype→phenotype readout inventory

**Status:** research implementation slice; real-data acquisition is partial.
**Scope:** `peptodyssey` / `fmb`.

This table is the source-of-truth boundary for the first practical route. A
source being listed does not mean it is landed, integrated, or validated; see
`data/g2p/sources.yaml` for the provenance state.

| Peptide / class | Readout | Grade | Genetic evidence source | Priority | Current product posture |
|---|---|---:|---|---:|---|
| Semaglutide / GLP-1 RA | Body weight | A | Published GLP-1 response GWAS candidate; 2026 response summary statistics not yet landed | P0 | Research-only; no production response weight update |
| Semaglutide / GLP-1 RA | HbA1c | A | Dawed et al. GLP-1 pharmacogenomic meta-analysis; summary table not yet landed | P0 | Research-only; catalog evidence only |
| Tirzepatide / dual GLP-1/GIP RA | Body weight / HbA1c | A | GLP-1 response evidence plus GIPR-specific evidence where applicable | P0 | Keep GIPR effects scoped to tirzepatide |
| Liraglutide / GLP-1 RA | Body weight / HbA1c | A | Same GLP-1 response evidence family | P0 | Research-only; no efficacy claim |
| Tesamorelin / CJC-1295 / Ipamorelin | Serum IGF-1 / IGFBP-3 | B | NHANES III IGF-axis reference file landed; no large peptide-response GWAS | P1 | Wide reference prior; demographics join pending |
| BPC-157 | VEGF / NOx | D | No sufficiently large public human genotype×response dataset identified | P2 | Genetic weight zero; no validated genetic predictor |
| TB-500 / GHK-Cu / similar sparse classes | Named class readouts | D | No sufficiently large public human genotype×response dataset identified | P2 | Genetic weight zero; generate paired data prospectively |

## Source-state rules

- **Landed:** the NHANES III IGF-I/IGFBP-3 biomarker file is versioned and
  checksummed under `data/g2p/`; it is not yet integrated into the tracking
  model.
- **Candidate:** the Dawed response evidence and the 2026 GLP-1 response GWAS
  are named sources, but no unverified HTML or secondary report is converted
  into coefficients.
- **Controlled:** UK Biobank RAP and All of Us require approved workspaces;
  their full biobank counts are not treated as treated-response sample sizes.
- **Prospective:** sparse peptide classes require FMB-observed genotype plus
  serial-readout data, a locked T0 snapshot, and a prespecified analysis plan.

## Explicit non-goals for this slice

- Do not use BMI/T2D PGS as a GLP-1-response oracle.
- Do not add `rs10305420` to production weights until the primary 2026 source
  table and effect definition are verified.
- Do not copy published kilograms or HbA1c effects into panel efficacy
  parameters.
- Do not call the synthetic diagnostics backtest clinical validation.
