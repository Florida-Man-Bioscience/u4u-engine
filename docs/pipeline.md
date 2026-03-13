# Pipeline

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
| `filename` | `str` | Format detection only. |
| `filters` | `list[str]` | rsID whitelist filenames. Empty = all variants. |
| `data_dir` | `str` | Filter file directory. Default: `"data"`. |
| `progress_callback` | `callable` | `fn(step: str, pct: int)`. Optional. |

---

## Output fields

**Identity:** `variant_id`, `rsid`, `chrom`, `pos`, `ref`, `alt`, `location`, `zygosity`

**Annotation:** `consequence`, `genes`, `clinvar`, `clinvar_raw`, `disease_name`, `condition_key`, `gnomad_af`, `gnomad_popmax`, `gnomad_homozygote_count`

**Scoring:** `score`, `tier`, `reasons`, `frequency_derived_label`, `carrier_note`

**Summary:** `emoji`, `headline`, `consequence_plain`, `rarity_plain`, `clinvar_plain`, `action_hint`, `zygosity_plain`

---

## Steps

1. **Validate** — empty file, >100 MB, invalid VCF header, non-UTF-8 all raise `ValueError`
2. **Parse** — 23andMe: skip `#` lines, non-`rs` IDs, failed calls (`--`, `NN`, indels). VCF: pysam, one dict per alt. CSV: chrom/pos/ref/alt/rsid. All: strip `chr` prefix, uppercase alleles.
3. **Quality filter** — drop `homozygous_ref`, VCF `GQ < 20`, VCF `DP < 5`, indels
4. **Whitelist filter** — if `filters` non-empty, keep only rsIDs in at least one filter file
5. **rsID resolution** — 23andMe rsIDs → Ensembl Variation API → genomic coordinates. Genotype-aware: returns only alt alleles the user carries.
6. **Deduplicate** — key: `(chrom, pos, ref, alt)`. Prefer entry with rsID.
7. **Annotate** — VEP → ClinVar → gnomAD per variant. MyVariant.info if both null. See `docs/integrations.md`.
8. **Score** — see scoring table below
9. **Summarize** — generates plain-English fields from `engine/summary.py`
10. **Sort** — by `score` descending, stable

---

## Scoring

Short-circuit (nothing overrides):
- `clinvar = "pathogenic"` → score = 1000, tier = critical
- `clinvar = "benign"` → score = 1, tier = low

| Signal | Points |
|--------|--------|
| Likely pathogenic | +500 |
| VUS | +50 |
| High-impact consequence (stop_gained, frameshift, splice site, start_lost, stop_lost, transcript_ablation) | +100 |
| Moderate-impact (missense, inframe) | +50 |
| Low-impact (synonymous, intron, UTR) | +5 |
| gnomAD AF = 0 | +30 |
| gnomAD AF < 0.0001 | +20 |
| gnomAD AF < 0.001 | +10 |
| gnomAD AF < 0.01 | +5 |
| gnomAD AF >= 0.01 | -20 |
| No gene annotation | -10 |

Carrier modifier: `zygosity = "heterozygous"` + recessive disease → score × 0.5, `carrier_note` set.

Tier thresholds: CRITICAL ≥ 500, HIGH ≥ 100, MEDIUM ≥ 30, LOW < 30.

---

## Bugs that must not come back

1. Gene hardcoded to "N/A" — genes come from VEP `transcript_consequences` only
2. Annotating `homozygous_ref` variants — quality filter must drop these before step 7
3. MyVariant hits without coordinate validation — validate `chrom`/`pos` match before accepting
4. Hardcoded variant cap (`:10` slice) — process all variants
5. No deduplication before annotation
6. Frequency heuristic overwriting ClinVar — `frequency_derived_label` is additive only
7. Inconsistent `chr` prefix — strip and normalize internally
8. Missing retry logic — all external calls use tenacity (3 attempts, 2s/4s/8s backoff)

---

## Test cases (in `tests/`)

- `--` genotype → absent from output
- `i7001348` internal ID → skipped
- `CT` → `heterozygous`, `TT` → `homozygous_alt`
- `chr19` → stored as `"19"`
- `.bam` extension → raises `ValueError`
- `homozygous_ref` → dropped; `GQ=15` → dropped; `ref="AT"` (indel) → dropped
- Duplicate `(chrom, pos, ref, alt)` → one result, rsID-bearing entry kept
- `clinvar="pathogenic"` → score=1000, tier=critical
- `clinvar="benign"` → score=1, tier=low
- VUS + `gnomad_af=0.10` → `frequency_derived_label` set, `clinvar` unchanged
- Heterozygous + recessive disease → `carrier_note` set, score halved
- Empty file → raises `ValueError`
- Pathogenic variant → first in sorted output

---

## Next steps

1. **Curtis** — write `scripts/generate_filters.py`: download ClinVar bulk XML from `https://ftp.ncbi.nlm.nih.gov/pub/clinvar/xml/ClinVarFullRelease_00-latest.xml.gz`, filter to ACMG SF v3.2 gene list, write rsIDs to `data/acmg81_rsids.txt`
2. **Curtis** — add integration test with a real (anonymized) 23andMe sample file: call `run_pipeline(sample_bytes, "sample.txt", ["acmg81_rsids.txt"])`, assert at least one result has `tier="critical"` or `tier="high"`
3. **Hampton** — wire `progress_callback` in the FastAPI layer: pass a callback that writes `{"step": step, "pct": pct}` to a channel keyed by upload ID; frontend polls this channel for the live progress bar
