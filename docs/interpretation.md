# Interpretation

---

## Tiers

| Tier | Emoji | Score | Trigger |
|------|-------|-------|---------|
| Critical | 🔴 | 1000 | `clinvar = "pathogenic"` |
| High | 🟠 | ≥ 100 | Likely pathogenic or high-impact consequence without benign signal |
| Medium / VUS | 🟡 | ≥ 30 | VUS or moderate consequence without clinical classification |
| Low | 🟢 | < 30 | Benign, likely benign, or gnomAD AF ≥ 5% |
| Carrier | 🔵 | any (halved) | Heterozygous in a recessive gene |

Low-tier findings hidden by default. Users can toggle on.

---

## Consumer categories

| Category | V1 |
|----------|----|
| Hereditary Conditions — pathogenic + likely pathogenic | Yes |
| Uncertain Findings — VUS with population + functional data | Yes |
| Carrier Status — heterozygous in recessive genes | Yes |
| Medication Response — CYP2C19, CYP2D6, VKORC1, etc. | No (V2) |
| Wellness Insights — trait associations | No (V2) |

---

## ACMG floor

Every variant in the ACMG SF v3.2 gene list (81 genes) must appear in results regardless of score. A pathogenic ACMG SF variant missing from output is a product failure.

Reference: https://www.gimjournal.org/article/S1098-3600(22)00887-2/fulltext

---

## VUS policy

VUS findings are surfaced, not hidden. Card shows: population frequency, functional consequence, any published classification context.

Default language: "This variant is classified as having uncertain significance (VUS). The scientific community has not reached consensus on whether this variant affects health."

`[SASANK REVIEW: revise this language]`

---

## Carrier policy

Default card text: "As a carrier of a recessive variant, you typically will not be affected. This may be relevant for family planning."

`[SASANK REVIEW: list genes needing condition-specific carrier language — CFTR, HBB, GJB2, HEXA]`

---

## Condition library

Keyed by `condition_key` (OMIM preferred, MedGen fallback, ClinVar UID last resort). The API layer looks up `condition_key` from each engine result in Postgres and merges the curated fields into the response.

**Status: schema done, content missing. Sasank owns this.**

### Required columns

| Column | Description |
|--------|-------------|
| `condition_key` | OMIM ID, MedGen ID, or ClinVar disease ID |
| `condition_display_name` | Clean UI name |
| `gene_symbols` | Associated genes, comma-separated |
| `inheritance_pattern` | Autosomal dominant / recessive / X-linked / Mitochondrial |
| `plain_description` | 2-3 sentences for a non-scientist |
| `action_guidance` | One concrete next step |
| `acmg_sf` | On ACMG SF v3.2 list? (boolean) |

### Optional columns

| Column | Description |
|--------|-------------|
| `prevalence` | Approximate population prevalence |
| `carrier_note_override` | Override default carrier text (CFTR, HBB, GJB2, HEXA, etc.) |
| `vus_notes` | Gene-specific VUS language |
| `last_reviewed` | Date of last Sasank review |

Priority: all 81 ACMG SF genes before launch. Start with BRCA1, TP53, LDLR, RYR1.

---

## Next steps

1. **Sasank** — create the condition library CSV with the schema above; fill in 4 rows: BRCA1 (OMIM:604370), TP53 (OMIM:191170), LDLR (OMIM:606945), RYR1 (OMIM:180901) — each needs `plain_description`, `action_guidance`, and `inheritance_pattern` at minimum
2. **Sasank** — finalize VUS display language and write `carrier_note_override` text for CFTR, HBB, GJB2, HEXA; replace all `[SASANK REVIEW]` markers in this doc with the agreed text
3. **Hampton** — once Sasank's CSV exists, write `scripts/load_condition_library.py` that reads the CSV and upserts rows into the Postgres `condition_library` table keyed by `condition_key`
