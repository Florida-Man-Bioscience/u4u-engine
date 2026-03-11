# U4U — Platform Overview

> This is the canonical description of the platform. If something here is wrong, fix it here first. Everything else — Notion, pitch decks, README — should match this document.

---

## What U4U is

U4U is a genomic interpretation platform. A user uploads a raw genome file from 23andMe, AncestryDNA, or a clinical sequencing lab. The platform annotates their variants against clinical and population databases and returns a prioritized list of findings in plain English.

The annotation pipeline is a standalone Python package (`engine/`). The product is a web application that wraps it.

---

## What problem it solves

Roughly 30 million people have a raw genome file from a consumer DTC test. The companies that ran the test gave them an ancestry dashboard and a handful of simplified trait reports. The raw data — thousands of variants that may have clinical meaning — was never explained.

Clinical labs that sequence genomes are required to report findings in 81 specific genes (the ACMG Secondary Findings v3.2 list). If a variant is of uncertain significance, or is in a gene not on the mandatory list, labs say nothing.

U4U surfaces what the science actually says about a person's specific variants: known pathogenic findings, uncertain findings with honest context, carrier status, and in V2, ongoing research relevant to their specific genome.

---

## Who it is for

**V1 primary:** People who already have a 23andMe or AncestryDNA raw data file and received limited information from the company that ran the test.

**V1 secondary:** People who received a VCF from a clinical sequencing lab and want context beyond what the lab report said — particularly around VUS findings.

**Not V1:** Clinicians ordering tests on behalf of patients. Researchers. People who do not yet have a genome file. Anyone seeking a diagnosis or treatment recommendation.

---

## How it works

1. User uploads a genome file (.txt from 23andMe, .vcf, .vcf.gz, or .csv)
2. The file is parsed in memory. It is never written to disk or stored server-side.
3. Variants pass through quality filters, then a whitelist filter (ACMG SF v3.2 by default)
4. Each variant is annotated against four external databases:
   - Ensembl VEP — functional consequence (what the variant does to the protein)
   - NCBI ClinVar — clinical classification (pathogenic / VUS / benign)
   - gnomAD — population allele frequency (how rare the variant is)
   - MyVariant.info — fallback aggregator when primary sources return nothing
5. Variants are scored and assigned a tier: Critical / High / Medium / Low / Carrier
6. Plain-English summaries are generated: headline, consequence, rarity, ClinVar classification, action hint
7. Results are returned sorted by score, highest priority first

The engine is a pure Python function: `run_pipeline(file_bytes, filename, filters) -> list[dict]`. No web framework, no database, no UI inside the engine. The web application wraps it.

Full pipeline documentation is in `docs/engine-spec.md`. External databases are documented in `docs/data-sources.md`.

---

## Privacy

The raw genome file is processed in memory and discarded after the pipeline completes. It is never stored server-side.

What does leave the system during annotation: individual variant coordinates (chromosome, position, ref, alt) sent to Ensembl VEP, and rsIDs sent to ClinVar and MyVariant.info. This is unavoidable — annotation requires querying external databases with variant data.

What never leaves the system: the raw genome file itself, any user identity (V1 has no accounts), any assembled genomic profile.

In V2, when user accounts and research tracking exist, gene symbols from stored variant profiles will be sent to PubMed on a nightly basis. This will be disclosed in the privacy policy before accounts are offered.

Full data flow documentation is in `docs/data-sources.md`.

---

## What makes it different

**ACMG floor, enforced.** Every variant in the 81-gene ACMG SF v3.2 list surfaces in results regardless of score. A pathogenic ACMG SF variant that fails to appear is a product failure.

**VUS are surfaced, not suppressed.** Variants of uncertain significance are shown with available population frequency, functional consequence, and published classification context. Honest language about uncertainty is the policy. "The jury is still out" is a valid answer.

**Research tracking (V2).** When new PubMed papers are published that mention a variant in a user's stored profile, a plain-English summary of that paper surfaces in their account. Static results become living documents. This is the subscription feature and the primary revenue driver.

**Condition library.** Sasank's curated spreadsheet provides human-written plain descriptions and specific action guidance for each condition, keyed to OMIM IDs. This is what makes results feel like they were written by a knowledgeable person rather than assembled from a database query.

---

## What it is not

- A diagnostic tool. U4U does not tell users they have or will get a disease.
- A replacement for genetic counseling.
- A platform that makes clinical recommendations (take this drug, have this surgery).
- A sequencing service.
- A 23andMe competitor. It requires a file the user already has.

---

## Business model

**Free tier:** Upload a file, see your results. One-time, session-based. No account required.

**Subscription tier:** Results that update as new research publishes. Requires an account and stored variant profile. Price TBD.

**Hypotheses under test:**
- Consumer subscription (people pay monthly for interpretation that updates)
- Clarity kits (users buy recommended follow-up tests when the platform explains why they matter)
- B2B2C licensing (DTC genomics companies license the interpretation layer, Phase 2+)
- Clinical licensing (genetic counselors pay for an auditable triage tool, Phase 3+)

V1 tests only the consumer subscription hypothesis. Nothing else ships before that is validated.

---

## Long-term vision

The current product is a static genomic interpretation service. The long-term platform is a continuously-updating biological intelligence layer — integrating genome data with blood biomarkers, epigenetic aging clocks, microbiome data, and continuous glucose monitoring into a mechanistic model of the individual. The genomic interpretation layer is the foundation everything else builds on.

V3+ territory. V1 is: upload a file, see your variants explained.

---

## Current state

The annotation pipeline is complete and tested. It handles 23andMe files, VCFs, and CSVs. It annotates against ClinVar, gnomAD, and VEP with retry logic and fallbacks. It produces scored, tiered, plain-English summaries.

What does not yet exist:
- Web interface (Tom)
- FastAPI wrapper (Hampton)
- Postgres database (Hampton)
- Deployed URL (Hampton + Curtis — domain needed)
- Condition library content (Sasank — 81 ACMG genes)
- User accounts (V2)

---

## Architecture (decided)

- **Runtime:** SaaS web app on Hampton's Kubernetes cluster
- **API:** FastAPI wrapping `run_pipeline()`, async workers via thread pool
- **Database:** Postgres — annotation cache, condition library, user profiles (V2), research tracking (V2)
- **Auth:** Authelia (V2 — required for user accounts)
- **CI/CD:** Push to `main` triggers Docker build and auto-deploy
- **LLM use:** Research summarization only (V2). Not variant classification, not pipeline logic.

Architecture details and integration contract in `docs/engine-spec.md` and `docs/team.md`.

---

## Legal

Legal entity: 40 Minute Bioscience. Consumer brand: TBD (Jeran's decision). Incorporation before first paying customer.

---

*Curtis maintains this document. It is the starting point for understanding the project.*
