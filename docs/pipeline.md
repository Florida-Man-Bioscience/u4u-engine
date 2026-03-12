# Pipeline

The engine is a single function. It takes a genome file and returns annotated variants.

```python
from engine import run_pipeline

results = run_pipeline(file_bytes, filename, filters, data_dir, progress_callback)
# returns list[dict], score descending
```

---

## Inputs

| Parameter | Type | Notes |
|-----------|------|-------|
| `file_bytes` | `bytes` | Raw file. Never written to disk. |
| `filename` | `str` | Used for format detection only. |
| `filters` | `list[str]` | rsID whitelist filenames. Empty = all variants. |
| `data_dir` | `str` | Directory for filter files. Default: `"data"`. |
| `progress_callback` | `callable` | `fn(step: str, pct: int)` for progress bars. Optional. |

---

## Output fields

Each dict in the returned list contains:

**Identity:** `variant_id`, `rsid`, `chrom`, `pos`, `ref`, `alt`, `location`, `zygosity`

**Annotation:** `consequence`, `genes`, `clinvar`, `clinvar_raw`, `disease_name`, `condition_key`, `gnomad_af`, `gnomad_popmax`, `gnomad_homozygote_count`

**Scoring:** `score`, `tier`, `reasons`, `frequency_derived_label`, `carrier_note`

**Summary:** `emoji`, `headline`, `consequence_plain`, `rarity_plain`, `clinvar_plain`, `action_hint`, `zygosity_plain`

---

## 10 Steps

### 1. Validate
Raises `ValueError` if: file is empty, file exceeds 100 MB, `.vcf` file does not start with `##fileformat=VCF`, `.txt` or `.csv` is not valid UTF-8.

### 2. Parse

| Format | Behavior |
|--------|----------|
| 23andMe `.txt` | Skip `#` comment lines. Skip non-`rs` IDs. Skip failed calls (`--`, `NN`, `DI`, `DD`, `II`, any with `I` or `D`). Infer zygosity from genotype string. |
| VCF | Parse with pysam. One dict per alt allele. Zygosity from GT field. |
| CSV | Columns: chrom, pos, ref, alt, rsid (any subset). |
| All | Strip `chr` prefix. Uppercase alleles. |

### 3. Quality filter
Drop if: `zygosity == "homozygous_ref"`, failed genotype string, VCF `GQ < 20`, VCF `DP < 5`, indel (`len(ref) > 1` or `len(alt) > 1`).

### 4. Whitelist filter
If `filters` is non-empty, keep only variants whose rsID appears in at least one filter file. Filter files are cached in memory. Missing files treated as empty sets.

### 5. rsID resolution
For rsid-only variants (23andMe), calls Ensembl Variation API to get genomic coordinates. Genotype-aware: only returns alt alleles the user actually carries.

### 6. Deduplicate
Key: `(chrom, pos, ref, alt)`. When duplicates exist, keep the one with an rsID. Skip variants missing pos/ref/alt.

### 7. Annotate
Calls VEP, ClinVar, gnomAD per variant. See `docs/integrations.md` for API details.

- VEP: selects canonical consequence (MANE Select > canonical flag > most_severe_consequence)
- ClinVar: esearch by rsID, then esummary. Tries multiple schema paths for the significance field.
- gnomAD: GraphQL, tries r4 then r2.1. Prefers genome over exome data.
- MyVariant: fallback only, called when ClinVar and gnomAD both return null.

### 8. Score

Short-circuit rules (nothing overrides):
- `clinvar == "pathogenic"` → score = 1000, tier = critical
- `clinvar == "benign"` → score = 1, tier = low

Score components:

| Signal | Points |
|--------|--------|
| Likely pathogenic | +500 |
| Likely benign | score = 5 |
| VUS | +50 |
| High-impact consequence (stop_gained, frameshift, splice site, start_lost, stop_lost, transcript_ablation) | +100 |
| Moderate-impact (missense, inframe) | +50 |
| Low-impact (synonymous, intron, UTR) | +5 |
| Unknown consequence | +1 |
| gnomAD AF = 0 | +30 |
| gnomAD AF < 0.0001 | +20 |
| gnomAD AF < 0.001 | +10 |
| gnomAD AF < 0.01 | +5 |
| gnomAD AF >= 0.01 | -20 |
| No gene annotation | -10 |

Carrier modifier: if `zygosity == "heterozygous"` and disease name contains recessive keywords, multiply score by 0.5 and set `carrier_note`.

Tier thresholds: CRITICAL >= 500, HIGH >= 100, MEDIUM >= 30, LOW < 30.

`frequency_derived_label` is additive context only. It never overwrites `clinvar`.

### 9. Summarize
Generates `emoji`, `headline`, `consequence_plain`, `rarity_plain`, `clinvar_plain`, `action_hint`, `zygosity_plain` from structured fields. Full text strings are in `engine/summary.py`.

### 10. Sort
By `score` descending. Ties preserve original list order (stable sort).

---

## Bugs that must not be reintroduced

1. Gene hardcoded to "N/A" — genes come from VEP `transcript_consequences` only
2. Annotating homozygous-reference variants — quality filter drops them before step 7
3. Accepting MyVariant hits without coordinate validation — validate chrom/pos match
4. Hardcoded variant cap (`:10` slice) — process all variants
5. No deduplication before annotation
6. Frequency heuristic overwriting ClinVar — `frequency_derived_label` is additive
7. Inconsistent `chr` prefix — strip internally, normalize everywhere
8. No retry logic on API calls — all external calls wrapped with tenacity (3 attempts, exponential backoff)

---

## Test cases

Tests live in `tests/`. These are the behaviors they must verify:

- 23andMe `--` genotype: variant absent from output
- 23andMe internal ID (`i7001348`): skipped
- 23andMe `CT` genotype: `zygosity = "heterozygous"`
- 23andMe `TT` genotype: `zygosity = "homozygous_alt"`
- `chr19` chromosome: stored as `"19"`
- Unsupported extension `.bam`: raises `ValueError`
- `zygosity = "homozygous_ref"`: dropped by quality filter
- `gq = 15`: dropped
- `ref = "AT"` (indel): dropped
- Two identical `(chrom, pos, ref, alt)`: one result
- Entry without rsID + entry with rsID at same locus: entry with rsID kept
- `clinvar = "pathogenic"`: score = 1000, tier = critical
- `clinvar = "benign"`: score = 1, tier = low
- `clinvar = "uncertain significance"` + `gnomad_af = 0.10`: `frequency_derived_label = "Likely benign (common in population)"`, `clinvar` field unchanged
- `zygosity = "heterozygous"` + recessive disease name: `carrier_note` set, score halved
- Empty file: raises `ValueError`
- Pathogenic variant: appears first in sorted output
