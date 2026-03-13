# Integrations

External APIs called during pipeline step 7, plus internal data stores.

---

## APIs

### Ensembl VEP
- **Endpoint:** `POST https://rest.ensembl.org/vep/human/region`
- **Rate limit:** 15 req/sec unauthenticated
- **Extracts:** `most_severe_consequence`, `transcript_consequences[].gene_symbol`, `colocated_variants[].clin_sig` (ClinVar fallback)
- **Transcript priority:** MANE Select > canonical flag > `most_severe_consequence`
- **Fallback:** `consequence = "unknown"`, `genes = []`

### NCBI ClinVar (eUtils)
- **Endpoints:** `esearch.fcgi` (rsID → UID), `esummary.fcgi` (UID → record)
- **Auth:** Set `NCBI_API_KEY` env var. Without: 3 req/sec. With: 10 req/sec.
- **Extracts:** `clinical_significance`, `disease_name`, `condition_key` (from `trait_set[].trait_xrefs` — OMIM preferred, MedGen fallback, ClinVar UID last resort)
- **Fallback:** VEP `colocated_variants` ClinVar data

### gnomAD
- **Endpoint:** `POST https://gnomad.broadinstitute.org/api/` (GraphQL)
- **Auth:** None
- **Extracts:** `genome.af`, `exome.af` (fallback), `genome.homozygote_count`, `genome.popmax.af`
- **Dataset order:** r4 first, r2.1 if absent. Genome preferred over exome.
- **Fallback:** `gnomad_af = null` — scoring treats null as no frequency data

### MyVariant.info (fallback only)
- **Endpoint:** `GET https://myvariant.info/v1/query` (rsID) or `/v1/variant/{hgvs}` (coordinate)
- **Rate limit:** 1000 req/day unauthenticated
- **Called only when:** both ClinVar and gnomAD return null
- **Required:** validate returned hit's coordinates match the variant before accepting data

---

## Priority order

| Field | Source order |
|-------|-------------|
| `clinvar` | ClinVar eUtils → VEP colocated fallback → MyVariant.info |
| `gnomad_af` | gnomAD GraphQL (r4 → r2.1) → MyVariant.info |
| `consequence` | VEP MANE Select → canonical → most_severe_consequence |

A lower-priority source never overwrites a higher-priority one.

---

## rsID resolution

Called during step 5 for 23andMe files (rsID without coordinates).

- **Endpoint:** `GET https://rest.ensembl.org/variation/human/{rsid}`
- **Rate limit:** 15 req/sec. Engine sleeps 70ms between calls.
- Genotype-aware: returns only alt alleles the user actually carries.

---

## Retry behavior

All external APIs: 3 attempts, exponential backoff (2s, 4s, 8s). Network timeouts and connection errors retry. Non-200 responses do not retry.

---

## Internal data stores (Postgres — not yet built)

| Table | Contents | Status |
|-------|----------|--------|
| `annotation_cache` | Results keyed by `(chrom, pos, ref, alt)`. TTL: 30 days. | Not built |
| `condition_library` | Sasank's condition rows, loaded from CSV at deploy. | Not built |
| `user_variants` | Stored profiles per user. | V2 |
| `research_updates` | LLM paper summaries linked to user_variant records. | V2 |

Hampton owns schema and migrations.

---

## Filter files (`data/`)

| File | Contents |
|------|----------|
| `acmg81_rsids.txt` | Pathogenic/likely pathogenic rsIDs for ACMG SF v3.2 genes |
| `pharma_rsids.txt` | Pharmacogenomics rsIDs |
| `carrier_rsids.txt` | Carrier screening rsIDs |
| `all_clinvar_rsids.txt.gz` | All ClinVar rsIDs (large) |

Regeneration: `scripts/generate_filters.py` — not yet written.

---

## What leaves the system

| Data | Sent to | When |
|------|---------|------|
| Variant coordinates (chrom, pos, ref, alt) | Ensembl VEP | Annotation |
| rsIDs | Ensembl, ClinVar, MyVariant.info | Annotation |
| Raw genome file | Nobody | Never |
| User identity | Nobody | V1 has no accounts |
| Gene symbols | NCBI Entrez | V2 only, after user opts in |

---

## Next steps

1. **Curtis** — register free NCBI API key at https://www.ncbi.nlm.nih.gov/account/ and add `NCBI_API_KEY` to `.env.example`; without it ClinVar annotates at 3 req/sec and will be the bottleneck under any real load
2. **Curtis** — write `scripts/generate_filters.py`: fetch `https://ftp.ncbi.nlm.nih.gov/pub/clinvar/xml/ClinVarFullRelease_00-latest.xml.gz`, filter to ACMG SF v3.2 gene list, write rsIDs to `data/acmg81_rsids.txt`; this file is required before the whitelist filter step works
3. **Hampton** — design Postgres `annotation_cache` schema: `(chrom TEXT, pos INT, ref TEXT, alt TEXT, vep_json JSONB, clinvar_json JSONB, gnomad_json JSONB, cached_at TIMESTAMP)`, unique index on `(chrom, pos, ref, alt)`, cron job or trigger for 30-day TTL cleanup
