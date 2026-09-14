# PeptOdyssey real-data inputs

This directory contains **provenance-labeled** inputs for reference
biomarker distributions and genotype→phenotype evidence.

## Landed public data

`nhanes_iii_ssigf.xpt` is the CDC NHANES III serum IGF-I / IGFBP-3 file.
`nhanes_iii_igf_axis.csv` is a normalized derivative with the same 6,061 rows
and columns:

- `SEQN` — NHANES participant key
- `IGP_I` — serum IGF-I
- `IGP_BP3` — serum IGFBP-3

The biomarker file is currently **not** joined to demographics: both the
household-adult and examination fixed-width files matched only `4,879/6,061`
`SEQN` values in the reproducibility check, so those partial joins were
removed. Age-, sex-, and race-stratified reference intervals are therefore
still pending a complete key-resolution audit. This file is a reference-
distribution dataset, not a peptide-response cohort.

Checksums and source status are recorded in `sources.yaml`. Do not replace
these files without updating the checksums and source URL.

## Landed public evidence

`glp1_response_gwas_freeze.tsv` is a 16-row transcription of the published
Dawed et al. Supplementary Table 5. It contains suggestive GLP-1-response
loci for HbA1c reduction, with the source PDF and checksum recorded in
`sources.yaml`. It is a literature evidence freeze, not a full summary-stats
matrix, patient-level data, or activated production scoring.

## Status vocabulary

- `candidate_source`: identified in the literature; file not landed
- `access_required`: controlled-access route must be approved
- `landed`: versioned file is present and checksum recorded
- `integrated`: production code consumes the file
- `validated`: locked evaluation has been run against real observations

A `landed` file is not automatically `integrated` or `validated`.

## Next acquisition gates

1. Add the matching NHANES III demographics/core file and join on `SEQN`.
2. Verify and land the Dawed GLP-1 response supplement or author-deposited
   summary statistics.
3. Add only explicitly verified PGS Catalog score IDs to
   `data/pgs/manifest.yaml`.
4. Obtain controlled-access UK Biobank RAP / All of Us approvals before
   describing those cohorts as available.
5. Generate paired genotype + serial-readout data in the FMB observational
   cohort for peptide classes without public response evidence.
