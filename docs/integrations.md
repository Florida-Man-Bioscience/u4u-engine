# Integrations

External APIs called during annotation (pipeline step 7), plus internal data stores.

---

## External APIs

### Ensembl VEP

**Provides:** Functional consequence. Which gene is affected, what the variant does to the protein.

**Endpoint:** `POST https://rest.ensembl.org/vep/human/region`

**Rate limit:** 15 req/sec unauthenticated.

**What we extract:** `most_severe_consequence`, `transcript_consequences[].gene_symbol`, `colocated_variants[].clin_sig` (ClinVar fallback only).

**Transcript priority:** MANE Select > canonical flag > `most_severe_consequence`.

**Fallback if unavailable:** `consequence = "unknown"`, `genes = []`.

---

### NCBI ClinVar (eUtils)

**Provides:** Clinical significance. Pathogenic / likely pathogenic / VUS / benign / likely benign. Associated condition name.

**Endpoints:**
- `GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` (rsID to UID)
- `GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi` (UID to record)

**Auth:** Set `NCBI_API_KEY` env var. Without key: 3 req/sec. With key: 10 req/sec.

**What we extract:** `clinical_significance`, `disease_name`, `condition_key` (from `trait_set[].trait_xrefs` -- OMIM preferred, MedGen fallback, ClinVar UID last resort).

**Fallback if unavailable:** Uses ClinVar data embedded in VEP `colocated_variants` response.

---

### gnomAD

**Provides:** Population allele frequency across ~800,000 human genomes.

**Endpoint:** `POST https://gnomad.broadinstitute.org/api/` (GraphQL)

**Auth:** None.

**What we extract:** `genome.af`, `exome.af` (fallback), `genome.homozygote_count`, `genome.popmax.af`.

**Dataset order:** gnomAD r4 first, r2.1 if variant absent from r4. Genome data preferred over exome.

**Fallback if unavailable:** `gnomad_af = null`. Scoring treats null as no frequency data.

---

### MyVariant.info (fallback only)

**Provides:** ClinVar and gnomAD data via aggregation. Called only when both primary sources return null.

**Endpoint:** `GET https://myvariant.info/v1/query` (by rsID) or `/v1/variant/{hgvs}` (by coordinate)

**Auth:** None. Rate limit: 10 req/sec, 1000 req/day unauthenticated.

**Validation required:** When querying by rsID, validate returned hit's coordinates match the variant before accepting data.

---

## Priority order

| Field | Order |
|-------|-------|
| `clinvar` | Direct ClinVar eUtils > VEP colocated fallback > MyVariant.info |
| `gnomad_af` | Direct gnomAD GraphQL (r4 then r2.1) > MyVariant.info |
| `consequence` | VEP MANE Select > VEP canonical > VEP most_severe_consequence |

A lower-priority source never overwrites a higher-priority one.

---

## rsID resolution (Ensembl Variation API)

23andMe files contain rsIDs without coordinates. Called during pipeline step 5.

**Endpoint:** `GET https://rest.ensembl.org/variation/human/{rsid}`

**Rate limit:** 15 req/sec. Engine sleeps 70ms between calls.

**Genotype-aware:** Uses the user's genotype string to return only alt alleles they actually carry.

---

## Retry behavior (all external APIs)

3 attempts with exponential backoff: 2s, 4s, 8s. Network timeouts and connection errors trigger retry. Non-200 responses do not retry.

---

## Internal data stores

### Postgres (not yet built)

| Table | Contents | Status |
|-------|----------|--------|
| `annotation_cache` | Annotation results keyed by `(chrom, pos, ref, alt)`. TTL: 30 days. | Not built |
| `condition_library` | Sasank's condition rows, loaded from CSV at deploy time. | Not built |
| `user_variants` | Stored variant profiles per user. Required for research tracking. | V2 |
| `research_updates` | LLM summaries of new PubMed papers, linked to user_variant records. | V2 |

Hampton owns the Postgres schema and migrations.

### Local filter files (`data/`)

Plain text, one rsID per line. Used by the whitelist filter step.

| File | Contents |
|------|----------|
| `acmg81_rsids.txt` | Pathogenic/likely pathogenic rsIDs in ACMG SF v3.2 genes |
| `pharma_rsids.txt` | Pharmacogenomics rsIDs |
| `carrier_rsids.txt` | Carrier screening gene rsIDs |
| `health_traits_rsids.txt` | Health trait rsIDs |
| `all_clinvar_rsids.txt.gz` | All ClinVar rsIDs (large) |

Generated from ClinVar bulk downloads. Regeneration script: `scripts/generate_filters.py` (not yet written).

---

## What user data leaves the system

| Data | Sent to | When |
|------|---------|------|
| Variant coordinates (chrom, pos, ref, alt) | Ensembl VEP | During annotation |
| rsIDs | Ensembl Variation API, NCBI ClinVar, MyVariant.info | During annotation |
| Raw genome file | Nobody | Never |
| User identity | Nobody | V1 has no accounts |
| Gene symbols from stored profile | NCBI Entrez | V2 only, after user opts into research tracking |
