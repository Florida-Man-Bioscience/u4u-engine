# Interpretation

The engine produces raw annotations. This document defines how those annotations map to findings a user sees.

---

## Finding tiers

| Tier | Emoji | Score | Trigger |
|------|-------|-------|---------|
| Critical | 🔴 | 1000 | `clinvar = "pathogenic"` (short-circuit) |
| High | 🟠 | >= 100 | Likely pathogenic, or high-impact consequence without benign signal |
| Medium / VUS | 🟡 | >= 30 | VUS classification, or moderate consequence without clinical classification |
| Low | 🟢 | < 30 | Benign, likely benign, or common variant (gnomAD AF >= 5%) |
| Carrier | 🔵 | any (halved) | Heterozygous variant in a recessive gene |

Low-tier findings are hidden by default in the UI. Users can toggle them on.

---

## Consumer categories

The UI groups findings into five categories. The tier is the severity signal; the category tells the user what kind of finding it is.

| Category | Covers | V1 |
|----------|--------|-----|
| Hereditary Conditions | Pathogenic and likely pathogenic variants. ACMG SF genes always included. | Yes |
| Uncertain Findings | VUS with available population and functional data. | Yes |
| Carrier Status | Heterozygous variants in recessive genes. | Yes |
| Medication Response | Pharmacogenomics (CYP2C19, CYP2D6, VKORC1, etc.) | No (V2) |
| Wellness Insights | Non-actionable trait associations | No (V2) |

---

## ACMG floor policy

Every variant in the ACMG SF v3.2 gene list (81 genes) must appear in results. No score threshold can suppress it. A pathogenic ACMG SF variant that does not appear is a product failure.

Reference: https://www.gimjournal.org/article/S1098-3600(22)00887-2/fulltext

---

## VUS policy

VUS findings are surfaced, not hidden. The results card shows:
- Population frequency
- Functional consequence
- Any published classification context

Language: "This variant is classified as having uncertain significance (VUS). The scientific community has not reached consensus on whether this variant affects health. Below is what the available data shows."

`[SASANK REVIEW: revise this language]`

---

## Carrier policy

Carrier findings use blue styling and a separate card layout. Default text:

"As a carrier of a recessive variant, you typically will not be affected by this condition. This may be relevant for family planning."

`[SASANK REVIEW: list genes where condition-specific carrier language is needed (CFTR, HBB, GJB2, HEXA, etc.)]`

---

## Auto-generated text (engine produces these, no curation needed)

**Consequence descriptions** (`engine/summary.py`):
- `stop_gained` - "creates a premature stop signal in the protein, typically breaking its function"
- `missense_variant` - "changes a single building block (amino acid) in the protein"
- `frameshift_variant` - "disrupts the way the gene is read, heavily altering the resulting protein"

**Rarity descriptions** (`engine/summary.py`):
- AF = 0 - "extremely rare, allele frequency is effectively zero in public databases"
- AF < 0.0001 - "ultra-rare (seen in less than 1 in 10,000 people)"
- AF < 0.001 - "very rare (seen in roughly 1 in 1,000 people)"
- AF >= 0.05 - "common (seen in about X% of people)"

---

## Condition library

Curated content keyed by `condition_key` (OMIM ID preferred, MedGen fallback, ClinVar UID last resort).

The engine returns `condition_key` in each result. The API layer looks up that key in Postgres and merges the curated fields into the response.

**Status: schema exists, content missing. Sasank builds this.**

### Required columns

| Column | Type | Description |
|--------|------|-------------|
| `condition_key` | string | OMIM ID, MedGen ID, or ClinVar disease ID |
| `condition_display_name` | string | Clean UI name (not the raw ClinVar string) |
| `gene_symbols` | comma-separated | Associated genes |
| `inheritance_pattern` | string | Autosomal dominant / recessive / X-linked / Mitochondrial |
| `plain_description` | string | 2-3 sentences for a non-scientist |
| `action_guidance` | string | Concrete next step |
| `acmg_sf` | boolean | On ACMG SF v3.2 list? |
| `acmg_url` | string | URL to ACMG guideline |

### Optional columns

| Column | Description |
|--------|-------------|
| `prevalence` | Approximate population prevalence |
| `penetrance_note` | Brief note if penetrance is incomplete |
| `vus_notes` | Gene-specific VUS language |
| `carrier_note_override` | Override for genes where default carrier text is insufficient |
| `last_reviewed` | Date of last Sasank review |

### Scope

Start with all 81 ACMG SF v3.2 genes. Every gene on that list needs a complete row before launch.

Carrier screening genes (CFTR, HBB, GJB2, HEXA) are second priority if time allows. Pharmacogenomics is not in scope for V1.
