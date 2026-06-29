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
| `filters` | `list[str]` | rsID[^rsid] whitelist filenames. Empty = all variants. |
| `data_dir` | `str` | Filter file directory. Default: `"data"`. |
| `progress_callback` | `callable` | `fn(step: str, pct: int)`. Optional. |

---

## Output fields

**Identity:** `variant_id`, `rsid`, `chrom`, `pos`, `ref`[^allele], `alt`, `location`, `zygosity`[^zygosity]

**Annotation:** `consequence`[^consequence], `genes`, `clinvar`[^clinvar], `clinvar_raw`, `disease_name`, `condition_key`, `gnomad_af`[^gnomad], `gnomad_popmax`[^popmax], `gnomad_homozygote_count`

**Scoring:** `score`, `tier`, `reasons`, `frequency_derived_label`, `carrier_note`

**Summary:** `emoji`, `headline`, `consequence_plain`, `rarity_plain`, `clinvar_plain`, `action_hint`, `zygosity_plain`

---

## Steps

1. **Validate** — empty file, >100 MB, invalid VCF[^vcf] header, non-UTF-8 all raise `ValueError`
2. **Parse** — 23andMe[^23andme]: skip `#` lines, non-`rs` IDs, failed calls (`--`, `NN`, indels[^indel]). VCF: pysam[^pysam], one dict per alt. CSV: chrom/pos/ref/alt/rsid. All: strip `chr` prefix, uppercase alleles.
3. **Quality filter** — drop `homozygous_ref`[^homref], VCF `GQ < 20`[^gq], VCF `DP < 5`[^dp], indels
4. **Whitelist filter** — if `filters` non-empty, keep only rsIDs in at least one filter file
5. **rsID resolution** — 23andMe rsIDs → Ensembl Variation API[^ensembl] → genomic coordinates. Genotype-aware: returns only alt alleles the user carries.
6. **Deduplicate** — key: `(chrom, pos, ref, alt)`. Prefer entry with rsID.
7. **Annotate** — VEP[^vep] → ClinVar → gnomAD per variant. MyVariant.info[^myvariant] if both null. See `docs/integrations.md`.
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
| Likely pathogenic[^pathogenic] | +500 |
| VUS[^vus] | +50 |
| High-impact consequence (stop_gained, frameshift, splice site, start_lost, stop_lost, transcript_ablation)[^highimpact] | +100 |
| Moderate-impact (missense, inframe)[^moderate] | +50 |
| Low-impact (synonymous, intron, UTR)[^lowimpact] | +5 |
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

1. Gene hardcoded to "N/A" — genes come from VEP `transcript_consequences`[^transcript] only
2. Annotating `homozygous_ref` variants — quality filter must drop these before step 7
3. MyVariant hits without coordinate validation — validate `chrom`/`pos` match before accepting
4. Hardcoded variant cap (`:10` slice) — process all variants
5. No deduplication before annotation
6. Frequency heuristic overwriting ClinVar — `frequency_derived_label` is additive only
7. Inconsistent `chr` prefix — strip and normalize internally
8. Missing retry logic — all external calls use tenacity[^tenacity] (3 attempts, 2s/4s/8s backoff)

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

---

## Footnotes

[^rsid]: **rsID** — a Reference SNP cluster ID (e.g. `rs12345`), the stable dbSNP identifier for a known genetic variant. Consumer arrays like 23andMe report genotypes keyed by rsID.
[^allele]: **Allele / ref / alt** — an allele is one of the alternative DNA sequences at a site. `ref` is the reference-genome base; `alt` is the observed alternative base. A variant call describes how a sample differs from `ref`.
[^zygosity]: **Zygosity** — whether the two inherited copies at a site match: *homozygous reference* (both ref), *heterozygous* (one ref, one alt), or *homozygous alternate* (both alt).
[^consequence]: **Consequence** — the predicted functional effect of a variant on a gene/transcript (e.g. missense, frameshift, synonymous), as computed by a variant-effect predictor.
[^clinvar]: **ClinVar** — NCBI's public archive linking variants to clinical significance classifications (pathogenic, benign, VUS, etc.).
[^gnomad]: **gnomAD AF** — allele frequency from the Genome Aggregation Database, the fraction of population chromosomes carrying the allele. High frequency argues against rare-disease causation.
[^popmax]: **gnomAD popmax** — the highest allele frequency observed across gnomAD's individual continental populations (rather than the global average); used to avoid masking a variant that is common in one ancestry group.
[^vcf]: **VCF (Variant Call Format)** — the standard tab-delimited text format for storing sequence variants, with a `#`-prefixed header describing columns and metadata.
[^23andme]: **23andMe file** — the raw genotype export from the 23andMe consumer array: a text file of `rsid / chromosome / position / genotype` rows. "Failed calls" are sites the array could not read (`--`, `NN`).
[^indel]: **Indel** — an insertion or deletion variant (the ref/alt differ in length), as opposed to a single-nucleotide substitution. These are dropped during quality filtering here.
[^pysam]: **pysam** — a Python library wrapping htslib for reading/writing genomic file formats (VCF/BAM/CRAM).
[^homref]: **homozygous_ref** — a site where the sample matches the reference genome on both copies, i.e. no variant; dropped before annotation.
[^gq]: **GQ (Genotype Quality)** — a Phred-scaled confidence score for a called genotype in a VCF; higher is more confident. `GQ < 20` (< 99% confidence) is filtered out.
[^dp]: **DP (Depth)** — the number of sequencing reads covering a site; low depth (`DP < 5`) means an unreliable call.
[^ensembl]: **Ensembl Variation API** — Ensembl's public REST service that maps variant identifiers (rsIDs) to genomic coordinates and allele information.
[^vep]: **VEP (Variant Effect Predictor)** — Ensembl's tool/API that annotates variants with their predicted molecular consequences, affected genes, and transcripts.
[^myvariant]: **MyVariant.info** — an aggregator API that consolidates variant annotations from many sources; used here as a fallback when VEP and ClinVar both return nothing.
[^pathogenic]: **Pathogenic / likely pathogenic / VUS** — ACMG/AMP clinical-significance tiers: strong evidence of disease causation, probable causation, and uncertain significance, respectively.
[^vus]: **VUS (Variant of Uncertain Significance)** — evidence is insufficient to call the variant either pathogenic or benign.
[^highimpact]: **High-impact consequences** — variant effects likely to abolish or truncate the protein: `stop_gained` (premature stop codon), `frameshift` (insertion/deletion shifting the reading frame), splice-site disruption, `start_lost`/`stop_lost`, `transcript_ablation` (loss of the whole transcript).
[^moderate]: **Moderate-impact consequences** — `missense` (an amino-acid substitution) and `inframe` indels (change length without shifting the reading frame); potentially but not certainly damaging.
[^lowimpact]: **Low-impact consequences** — `synonymous` (no amino-acid change), `intron` (in a non-coding intron), and `UTR` (untranslated region) variants; usually benign.
[^transcript]: **transcript_consequences** — the VEP output block listing, per overlapping transcript, the gene and predicted effect. Gene symbols are taken from here rather than hardcoded.
[^tenacity]: **tenacity** — a Python retry library; here configured for 3 attempts with exponential backoff (2s/4s/8s) on external API calls.
