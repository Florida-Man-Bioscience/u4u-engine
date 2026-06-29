# Interpretation

---

## Tiers

| Tier | Emoji | Score | Trigger |
|------|-------|-------|---------|
| Critical | 🔴 | 1000 | `clinvar = "pathogenic"`[^pathogenic] |
| High | 🟠 | ≥ 100 | Likely pathogenic or high-impact consequence without benign signal[^benign] |
| Medium / VUS | 🟡 | ≥ 30 | VUS[^vus] or moderate consequence without clinical classification |
| Low | 🟢 | < 30 | Benign, likely benign, or gnomAD AF ≥ 5%[^gnomad] |
| Carrier | 🔵 | any (halved) | Heterozygous[^heterozygous] in a recessive[^recessive] gene |

Low-tier findings hidden by default. Users can toggle on.

---

## Consumer categories

| Category | V1 |
|----------|----|
| Hereditary Conditions — pathogenic + likely pathogenic | Yes |
| Uncertain Findings — VUS with population + functional data | Yes |
| Carrier Status — heterozygous in recessive genes | Yes |
| Medication Response — CYP2C19, CYP2D6, VKORC1, etc.[^pgxgenes] | No (V2) |
| Wellness Insights — trait associations | No (V2) |

---

## ACMG floor

Every variant in the ACMG SF v3.2 gene list (81 genes)[^acmgsf] must appear in results regardless of score. A pathogenic ACMG SF variant missing from output is a product failure.

Reference: https://www.gimjournal.org/article/S1098-3600(22)00887-2/fulltext

---

## VUS policy

VUS findings are surfaced, not hidden. Card shows: population frequency, functional consequence, any published classification context.

Default language: "This variant is classified as having uncertain significance (VUS). The scientific community has not reached consensus on whether this variant affects health."

`[SASANK REVIEW: revise this language]`

---

## Carrier policy

Default card text: "As a carrier of a recessive variant, you typically will not be affected. This may be relevant for family planning."

`[SASANK REVIEW: list genes needing condition-specific carrier language — CFTR, HBB, GJB2, HEXA]`[^carriergenes]

---

## Condition library

Keyed by `condition_key` (OMIM[^omim] preferred, MedGen[^medgen] fallback, ClinVar[^clinvar] UID last resort). The API layer looks up `condition_key` from each engine result in Postgres and merges the curated fields into the response.

**Status: schema done, content missing.**

**How content gets built:**
- Curtis auto-generates base rows from ClinVar/OMIM bulk data (structured fields: `condition_key`, `condition_display_name`, `gene_symbols`, `inheritance_pattern`, `acmg_sf`)
- Sasank reviews and writes the consumer-facing text fields: `plain_description`, `action_guidance`, `vus_notes`, `carrier_note_override`

Sasank is the clinical communication layer, not the data entry layer.

### Schema

| Column | Who fills it | Description |
|--------|-------------|-------------|
| `condition_key` | Curtis (auto) | OMIM ID, MedGen ID, or ClinVar disease ID |
| `condition_display_name` | Curtis (auto) | Clean UI name |
| `gene_symbols` | Curtis (auto) | Associated genes, comma-separated |
| `inheritance_pattern` | Curtis (auto) | Autosomal dominant / recessive / X-linked / Mitochondrial[^inheritance] |
| `acmg_sf` | Curtis (auto) | On ACMG SF v3.2 list? (boolean) |
| `plain_description` | **Sasank** | 2-3 sentences for a non-scientist |
| `action_guidance` | **Sasank** | One concrete next step |
| `vus_notes` | **Sasank** | Gene-specific VUS language |
| `carrier_note_override` | **Sasank** | Override default carrier text where needed (CFTR, HBB, GJB2, HEXA, etc.) |
| `prevalence` | Curtis (auto) | Approximate population prevalence |
| `last_reviewed` | Sasank | Date of last clinical review |

Priority: all 81 ACMG SF genes before launch. Start with BRCA1, TP53, LDLR, RYR1.[^examplegenes]

---

## Next steps

1. **Curtis** — auto-generate the base condition library CSV from ClinVar/OMIM for all 81 ACMG SF genes (structured fields only); share with Sasank so he has a pre-filled sheet to write into, not a blank one
2. **Sasank** — write `plain_description` and `action_guidance` for BRCA1, TP53, LDLR, RYR1; focus on clarity and not scaring people — a user who reads this should understand what it means and have one concrete thing to do next
3. **Sasank** — write the VUS and carrier interpretation guidelines as a short markdown doc (can live in `docs/interpretation.md` or a new `docs/clinical-voice.md`): how should findings be framed, what language avoids panic, how do we handle "the jury is out" findings

---

## Footnotes

[^pathogenic]: **Pathogenic** — an ACMG/AMP classification tier meaning there is strong evidence a variant causes disease. "Likely pathogenic" is the slightly weaker adjacent tier (>90% certainty by convention).
[^benign]: **Benign / likely benign** — the opposite end of the ACMG/AMP scale: strong (benign) or suggestive (likely benign) evidence that a variant does *not* cause disease.
[^vus]: **VUS (Variant of Uncertain Significance)** — a variant for which the available evidence is insufficient to classify it as either pathogenic or benign. The clinical community has not reached consensus.
[^gnomad]: **gnomAD AF** — allele frequency (the fraction of chromosomes in a population carrying the variant) as reported by the Genome Aggregation Database (gnomAD), a large public reference catalog of human variation. A high AF (e.g. ≥ 5%) argues against a variant being a rare disease cause.
[^heterozygous]: **Heterozygous** — carrying one copy of the variant allele and one copy of the reference allele at a site (as opposed to homozygous, two copies of the same allele).
[^recessive]: **Recessive gene/condition** — a condition that manifests only when *both* gene copies are affected; a single (heterozygous) variant typically makes the person an unaffected carrier.
[^pgxgenes]: **CYP2C19 / CYP2D6 / VKORC1** — pharmacogenes whose variants alter drug metabolism or response (CYP2C19 and CYP2D6 are drug-metabolizing enzymes; VKORC1 affects warfarin dosing). Used for "medication response" reporting.
[^acmgsf]: **ACMG SF v3.2** — the American College of Medical Genetics and Genomics "Secondary Findings" list, version 3.2: 81 genes for which laboratories are recommended to report pathogenic findings even when unrelated to the original test reason.
[^omim]: **OMIM** — Online Mendelian Inheritance in Man, a curated catalog of human genes and genetic disorders; OMIM IDs are stable identifiers for conditions.
[^medgen]: **MedGen** — NCBI's catalog of medical genetics terms and conditions, used here as a fallback identifier when no OMIM ID exists.
[^clinvar]: **ClinVar** — NCBI's public archive of reported relationships between human variants and phenotypes, including clinical significance classifications. A "ClinVar UID" is its internal record identifier.
[^inheritance]: **Inheritance pattern** — how a trait is transmitted: *autosomal dominant* (one affected copy suffices), *autosomal recessive* (both copies must be affected), *X-linked* (gene on the X chromosome), or *mitochondrial* (maternally inherited via mitochondrial DNA).
[^examplegenes]: **BRCA1, TP53, LDLR, RYR1** — high-priority example genes: BRCA1 (hereditary breast/ovarian cancer), TP53 (Li-Fraumeni cancer syndrome), LDLR (familial hypercholesterolemia), RYR1 (malignant hyperthermia susceptibility).
[^carriergenes]: **CFTR, HBB, GJB2, HEXA** — common recessive carrier genes: CFTR (cystic fibrosis), HBB (sickle cell / beta-thalassemia), GJB2 (hereditary hearing loss), HEXA (Tay-Sachs disease).
