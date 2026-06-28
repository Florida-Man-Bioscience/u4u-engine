# Tier A — Analytical Concordance Harness

Measures whether the `u4u-engine` pipeline computes the **correct answer when the
correct answer is already known**, by running reference materials through the
pipeline and comparing output to published truth sets.

**Why this needs no IRB:** Tier A uses cell-line reference materials (Coriell)
and de-identified public benchmark data (GIAB/NIST, GeT-RM/CDC). These are *not
human subjects* under 45 CFR 46.102(e), so this work can run **now**, before any
determination is granted. See `docs/irb-setup-plan.md` (§1, Tier A) and
`docs/irb-determination-request.md`.

## What it measures

| Track | Reference | Metric |
|---|---|---|
| **PGx diplotype** | GeT-RM consensus star-allele diplotypes | exact-match concordance, per gene |
| **PGx phenotype** | GeT-RM consensus phenotype (PM/IM/NM/RM/UM) | concordance, per gene |
| **Variant genotype** | GIAB benchmark (site-level subset) | sensitivity / specificity / precision / F1 + genotype concordance |

Maps onto the Clinical Validation Master Plan §9 (analytical validation) and the
GeT-RM/GIAB reference materials named in its Appendix C.

## Layout

```
validation/
  tier_a/
    metrics.py     # pure concordance math — no I/O, no network (unit-tested)
    reference.py   # TSV loaders for truth sets
    run.py         # CLI: pipeline → metrics → JSON + Markdown report
  reference/
    getrm_pgx_seed.tsv   # SEED placeholder — replace with real GeT-RM tables
tests/test_validation/
    test_tier_a_metrics.py   # offline unit tests (run in CI)
```

## Run it

```bash
# offline unit tests (fast, no network) — verifies the metrics math
nix develop --command python -m pytest tests/test_validation/ -v

# full concordance run against reference samples
nix develop --command python -m validation.tier_a.run \
    --pgx-reference  validation/reference/getrm_pgx_seed.tsv \
    --genotype-truth validation/reference/giab_genotypes.tsv \
    --sample-map     validation/reference/sample_inputs.tsv \
    --out-dir        validation/reports
```

`--sample-map` is a `sample<TAB>path` TSV pointing each reference sample id (e.g.
`NA12878`) to its genome input file. Run with at least one of `--pgx-reference`
or `--genotype-truth`.

## Reference data you must supply (the gating step — see "What's NOT here")

The repo ships **only a tiny seed** so the wiring runs. Real validation needs:

1. **GeT-RM PGx tables** — replace `getrm_pgx_seed.tsv` with the full, citable
   consensus diplotypes (Pratt et al. / CDC GeT-RM) for the samples you run.
   Record exact source + version in the `source` column. *The seed values are
   placeholders and are labeled as such — do not report numbers computed
   against them.*
2. **GIAB inputs + truth** — obtain GIAB sample files (e.g. NA12878/HG001) and
   distill a site-level genotype truth TSV (`sample`, `site`, `genotype`) from
   the high-confidence benchmark VCF for the sites your panel covers.
3. **Sample input files** — the actual VCF/array exports for each sample,
   referenced by the sample map.

These files are **not committed** (large, and licensing varies). Add them under
`validation/reference/` locally or via DVC/Git-LFS per your data policy.

## Reproducibility note (important)

The pipeline calls live external annotation APIs (VEP/ClinVar/gnomAD) for
coordinate variants, so naïve runs are **non-deterministic** — the master plan
flags this (§2.4, §8.6). For citable numbers, run against a **warmed annotation
cache** or a **pinned knowledge-base snapshot**, and record the snapshot version
alongside the report. The harness deliberately disables the production
ACMG81/peptide panel filters (`filters=[]`) so truth sites are not filtered out
before comparison.

## Honesty contract

The runner never invents a denominator. Missing reference file, unmapped sample,
or "pipeline made no call" → the comparison is **skipped and the rate reported as
`null` (undefined)**, never as a passing 0%/100%. A green report with
`n_compared = 0` means *nothing was tested*, not *everything passed*.

## What's NOT here (deliberately out of scaffold scope)

- **Full GA4GH / hap.py VCF benchmarking.** Whole-genome GIAB comparison is an
  external-tool integration, not a parser; this harness covers the site-level
  subset directly comparable to the pipeline's per-variant output. Wire `hap.py`
  in as a follow-up if you need genome-wide stratified stats.
- **STR / CAG-repeat concordance** (ExpansionHunter) and **build-handling
  validation** — separate Tier A tracks; add as parallel modules.
- **Acceptance thresholds.** This computes the numbers; the pass/fail criteria
  (e.g. ≥99% PGx diplotype concordance) are set in the validation protocol, not
  hard-coded here.
