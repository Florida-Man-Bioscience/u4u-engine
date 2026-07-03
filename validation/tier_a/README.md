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
| **Genome build handling** | synthetic labeled headers (no external data) | detection concordance + gating correctness + H-01 unsafe-pass count |
| **PGx diplotype** | GeT-RM consensus star-allele diplotypes | exact-match concordance, per gene |
| **PGx phenotype** | GeT-RM consensus phenotype (PM/IM/NM/RM/UM) | concordance, per gene |
| **Variant genotype** | GIAB benchmark (site-level subset) | sensitivity / specificity / precision / F1 + genotype concordance |
| **AR CAG STR calling** | synthetic EH output (no binary needed) | parser concordance + interpretation-boundary verification |

### AR CAG STR calling — runnable now, no binary needed

Validates `engine.repeat_callers.expansion_hunter` in two deterministic
sub-tracks: (1) **parser concordance** — feeds synthetic ExpansionHunter
VCF+JSON with known repeat counts through `parse_eh_output` and checks the count
is read correctly; (2) **interpretation boundary verification** — checks the CAG
sensitivity-tier classifier implements its documented breakpoints without
off-by-one errors.

```bash
nix develop --command python -m validation.tier_a.str_calling \
    --out-dir validation/reports
```

> ⚠️ Sub-track 2 is software *verification* (code matches its own spec), **not**
> clinical validation: the master plan §5.2.7 flags the CAG breakpoints and
> ancestry means as hand-curated and needing clinical-evidence backing — that is
> a Tier C claim, out of scope here. The full instrument-in-the-loop concordance
> (real binary + BAM + reference + STR truth set) is a documented hook; the
> runner reports whether the binary/reference are even present. Current status:
> 100% parser, 100% interpretation-boundary.

### Genome build handling — runnable now, no reference data needed

Validates `engine.genome_build`, the control for the master plan's #1
launch-blocking hazard **H-01** (silent GRCh37/GRCh38 conflation). Build
detection is pure header parsing, so this track is fully deterministic and needs
no acquired reference materials — it produces real numbers immediately:

```bash
nix develop --command python -m validation.tier_a.build_handling \
    --out-dir validation/reports
```

It exits **non-zero if the H-01 control fails** (any non-GRCh38 coordinate file
allowed to proceed), so it can be wired in as a CI gate. Current status on the
fixture matrix: 100% detection, 100% gating, **0 unsafe passes — H-01 holds**.

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
- **End-to-end ExpansionHunter STR concordance** — running the real binary on
  reference BAMs vs. an orthogonal CAG truth set. The deterministic parser +
  interpretation sub-tracks are implemented (see above); the instrument-in-the-
  loop run is the remaining hook. (Build-handling validation is also implemented.)
- **Acceptance thresholds.** This computes the numbers; the pass/fail criteria
  (e.g. ≥99% PGx diplotype concordance) are set in the validation protocol, not
  hard-coded here.
