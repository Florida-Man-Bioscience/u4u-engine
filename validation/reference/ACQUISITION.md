# Tier A Reference-Data Acquisition

How to obtain and convert the reference truth sets the data-gated Tier A tracks
need (PGx diplotype/phenotype vs. GeT-RM; variant genotype vs. GIAB). The
no-data tracks (genome-build handling, STR parser/interpretation) need nothing
here and already run.

> **Status:** the harness + converters are in place; the actual reference files
> are **not committed** (see "Where the data lives" — a decision for you). The
> committed `getrm_pgx_seed.tsv` is a labeled placeholder, not truth.

---

## 1. GeT-RM — PGx consensus diplotypes (cell lines → NHSR)

CDC/GeT-RM characterized Coriell cell lines with consensus star-allele
diplotypes across the major pharmacogenes. These are **cell-line** materials —
not human subjects (Tier A).

**Source:** CDC GeT-RM Reference Materials
<https://www.cdc.gov/lab-quality/php/get-rm/reference-materials.html>

Key downloads on that page:
- **"Consolidated Table of all GeT-RM Pharmacogenetic and HLA Reference Material
  Genotypes"** (`.xlsx`) — 363 samples × 34 genes/loci. The most complete source.
- Gene-specific tables: **CYP2D6 Test Methods and Consensus Genotypes**,
  **CYP2C8/2C9/2C19 NGS Results**, DPYD, TPMT/NUDT15, CYP3A4/3A5, etc.
- **GeT-RM PGx Search** (searchable web tool via Coriell) for spot lookups.

Primary publications with the supplementary consensus tables (record the exact
one you use in the `source` column):
- Pratt et al., *J Mol Diagn* — CYP2D6 reference materials (PMC6854474).
- Gaedigk/Pratt et al. — CYP2C9/2C19/VKORC1/CYP2C-cluster Tier-2 (PMC8491090).
- Pratt et al. 2010 — 107 genomic DNA RMs for CYP2D6/2C19/2C9/VKORC1/UGT1A1.

**Convert to the harness format** (`validation/reference/getrm_pgx.tsv`):
the loader (`reference.py::load_pgx_reference`) expects columns
`sample, gene, diplotype[, phenotype, source]`. Export the consolidated XLSX to
TSV and reshape to one row per (sample, gene). Keep only the samples you will
actually run through the pipeline (those you have input files for — see §3).

## 2. GIAB — variant genotype benchmark (de-identified public)

NIST Genome in a Bottle high-confidence small-variant benchmarks. Public,
de-identified reference samples (Tier A).

**Source (GRCh38 — the engine's only supported build):**
<https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/>
e.g. `NA12878_HG001/latest/GRCh38/` →
- `*_benchmark.vcf.gz` — high-confidence calls
- `*_benchmark.bed` — high-confidence regions (any panel site **inside** this
  BED but **absent** from the VCF is confidently homozygous-reference).

**Convert to the harness format** with the included converter
(`giab_truth_from_vcf.py`), restricting to a panel of sites so the truth set is
tractable and aligned to what the pipeline actually reports:

```bash
nix develop --command python validation/reference/giab_truth_from_vcf.py \
    --vcf      HG001_GRCh38_benchmark.vcf.gz \
    --sample   NA12878 \
    --panel    validation/reference/panel_sites_grch38.txt \
    --out      validation/reference/giab_genotypes.tsv
```

`--panel` is a file of `chrom:pos` (GRCh38) sites — e.g. positions distilled
from `data/peptide_genes.bed` / the ACMG81 panel — one per line. Panel sites
present in the VCF get their called genotype; panel sites absent get `ref`
(valid **only** when the site lies in the benchmark BED — see the converter's
`--confident-bed` option to enforce this).

## 3. Sample input files (what you feed the pipeline)

For each reference sample you score, you also need its **genome input file**
(VCF/array) to run through `run_pipeline`, referenced by the run's
`--sample-map` (`sample<TAB>path`). GIAB provides such files; for GeT-RM Coriell
samples, WGS is available via the European Nucleotide Archive (70 samples, linked
from the CDC page) or from Coriell directly.

## 4. Where the data lives — **your decision**

These files range from small (GeT-RM tables, KB) to large (GIAB VCFs/BAMs, GB).
They are deliberately **not committed**. Pick a policy and record it here:

- [ ] **Git-LFS** — for the small TSV truth sets, committed but stored via LFS.
- [ ] **DVC / object storage** — for large VCF/BAM inputs; commit only `.dvc`
      pointers.
- [ ] **Local-only / operator-supplied** — files live under
      `validation/reference/` on the validation workstation, never committed;
      provenance recorded in the report.

Whichever you choose, the **provenance** (source URL, file version/date, and for
GeT-RM the exact publication) must be captured — record it in the `source`
column (GeT-RM) and alongside each report, since Tier A evidence must be
traceable to a fixed, versioned reference (master plan §6.4, §9.7).

## 5. License / redistribution note

GIAB/NIST data is public-domain-style and freely redistributable. GeT-RM tables
are CDC publications; cell-line DNA is obtained from Coriell under their terms.
Confirm redistribution terms before committing any derived truth set to the repo
rather than referencing it.
