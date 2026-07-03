# Project Status

---

## MVP scope

VCF upload → annotation engine → interactive dashboard. No genome storage. Email capture for future research updates. Target: 4 weeks.

---

## What works

- Parses VCF / `.vcf.gz` (MVP primary), 23andMe `.txt`, CSV, rsID lists
- 10-step pipeline: validate → parse → quality filter → whitelist → rsID resolution → deduplicate → annotate → score → summarize → sort
- Annotates against ClinVar, gnomAD, Ensembl VEP[^vep] (retry + fallback)
- Returns plain-English headline, consequence, rarity, action hint per variant
- FastAPI job queue (`api.py`) — `POST /analyze` → 202 + `job_id`, `GET /jobs/:id` for polling
- Postgres schema (`db/schema.sql`) — jobs, results, condition_library, annotation_cache
- CI on push via GitHub Actions (Python 3.11 and 3.12)

### PeptidIQ V3[^peptidiq] — Peptide Response Interpretation Engine ✅

Added April 2026. Extends the genomics pipeline into a clinically actionable peptide and hormone response system.

**Peptide Condition Library** (`db/migrations/003_peptide_condition_library.sql`, `db/models/peptide_models.py`, `db/seeds/peptide_seed_data.sql`)
- Two new Postgres tables: `peptide_condition_library` and `peptide_trade_offs`
- SQLAlchemy 2.0 ORM[^orm] models with async[^async] helpers (`get_peptide_responses`, `get_trade_off`, `get_contraindicated_peptides`)
- 12 seeded rows covering AR, ESR1, ESR2, OXTR, MC4R, GLP1R, RET, TP53, BRCA1[^peptidegenes] with clinically detailed genotype–peptide response data
- JSON Schema 2020-12[^jsonschema] for scoring engine input/output format (`data/peptidiq_engine_schema.json`)

**ExpansionHunter[^expansionhunter] STR[^str] Calling** (`engine/repeat_callers/expansion_hunter.py`)
- Wraps Illumina ExpansionHunter binary to call AR CAG repeat[^arcag] directly from BAM/CRAM[^bam] files
- Clinical interpretation with 6 sensitivity tiers (VERY_LOW_PATHOLOGIC → VERY_HIGH) and severity flags
- Ancestry-adjusted[^ancestry] reference ranges (African, Caucasian, Hispanic, Asian)
- Graceful degradation: operates from VCF-only when no BAM is available
- 58 unit tests — all passing (`tests/test_engine/test_expansion_hunter.py`)

**KEGG Pathway Mapper**[^kegg] (`engine/annotators/kegg_mapper.py`)
- Maps patient variant gene symbols to 8 priority KEGG pathways: Estrogen signalling, GnRH signalling, Serotonergic synapse, MAPK, PI3K-AKT, Adipocytokine, Melanocortin/MC4R, Steroid hormone biosynthesis[^pathways]
- Fully offline via hardcoded gene membership; optional KEGG REST API refresh with SQLite caching
- Per-gene clinical implication generation (~50 curated gene–pathway notes)
- Cross-pathway combination notes for 7 clinically relevant co-hit[^cohit] pairs
- 53 unit tests — all passing (`tests/test_engine/test_kegg_mapper.py`)

**Predictive Logic Architecture** — spec documented in Notion[^notion] (Predictive Logic Architecture page); 4-layer scoring engine (Input → Evidence [35/25/20/20 weights] → Outcome → Logic Flow).

**Bayesian Biomarker Tracking & Evidence Registry** (`engine/tracking/`) ✅
- Longitudinal biomarker tracking with a Normal–Normal conjugate model (`bayes.py`): `analysis.predict_response` fuses a genetics-derived prior (`genetics.derive_prior`), leave-one-out cohort pooling (`pooling.py`), and the measurement likelihood into a posterior with 95% credible intervals and a forward predictive curve. REST API at `/tracking/...`; the generative model is documented in-app at `/tracking/model`.
- **Research-backed evidence registry** (`engine/tracking/evidence.py` + `data/biomarker_evidence.json`): citation-anchored, grade-tagged (A–D) per-biomarker effect entries. The evidence grade sets the prior's `relative_sd` — tighter for well-evidenced markers, flat `PANEL_REL_SD` fallback for the (still majority) uncited markers. Honesty contract: an entry requires ≥1 real, retrieved citation (DOI); curate via `python -m engine.tracking.evidence_update`.
- **GLP-1 / incretin class** (Semaglutide, Tirzepatide, Liraglutide) integrated as first-class, grade-A evidence-backed peptides, with class-qualified marker names (e.g. `Body weight (GLP-1 RA)`) so their large, well-evidenced effects do not bleed onto the smaller generic markers shared by weaker peptides (AOD-9604, MOTS-c).

---

## Repo

```
engine/
  annotators/       ClinVar, gnomAD, VEP, MyVariant, kegg_mapper modules
  repeat_callers/   ExpansionHunter STR caller (AR CAG repeat)
  tracking/         Bayesian biomarker tracking + research-backed evidence registry
  pipeline.py       run_pipeline() entry point
  scoring.py        scoring + tier logic
  summary.py        plain-English text generation
api.py              FastAPI job queue
db/
  schema.sql        base Postgres schema (jobs, results, condition_library)
  migrations/       incremental migration files (003 = Peptide Condition Library)
  models/           SQLAlchemy ORM models (peptide_models.py)
  seeds/            seed data SQL (peptide_seed_data.sql)
data/
  acmg81_rsids.txt
  condition_library_for_sasank.xlsx
  peptidiq_engine_schema.json     ← JSON Schema 2020-12 for scoring engine I/O
tests/test_engine/  all unit + integration tests
docs/               documentation (this file, architecture, roadmap, etc.)
.github/            CI, issue templates, PR template
```

---

## What doesn't exist

| Area | Status |
|------|--------|
| Docker build + K8s deployment | Not deployed |
| Postgres instance running | Schema exists — not wired |
| Condition library content | 81 ACMG SF rows needed |
| Frontend | Not built — spec in `docs/frontend.md` |
| Domain + DNS | Not registered |
| Security audit | Not started — plan in `U4U_Cybersecurity_Execution_Plan.docx` |
| PeptidIQ scoring engine (Layer 3 Outcome) | Architecture spec done, implementation pending |
| FastAPI endpoints for peptide response | Not yet wired to new ORM models |
| ExpansionHunter binary + reference FASTA[^fasta] | Must be installed in deployment environment |

---

## UI spec

Full spec in `docs/frontend.md`.

Three screens: Upload → Processing → Results.

Results screen is a **prioritized findings report** — single column, expandable rows with a colored left border (tier color). Two sections: "Needs Attention" (critical + high) and "For Your Records" (medium + low + carrier, collapsed by default).

**Tier visual treatment:**

| `tier` | Border | Emoji |
|--------|--------|-------|
| critical | red | 🔴 |
| high | orange | 🟠 |
| medium | yellow | 🟡 |
| low | green | 🟢 |
| carrier | blue | 🔵 |

**Error states:**

| State | Behavior |
|-------|----------|
| File too large / unsupported format | Inline error before submit |
| Invalid VCF header | Error screen after submit |
| All variants filtered | Results page with explanation |
| Zero ACMG findings | Message, not blank |
| Network error | Error screen with retry |
| Partial results | Show succeeded, note how many failed |

---

## Not in V1

User accounts, saved results, email delivery, pharmacogenomics, research tracking, PRS[^prs], mobile, API access for external developers.

---

## Footnotes

[^vep]: **Ensembl VEP (Variant Effect Predictor)** — Ensembl's tool/API that annotates variants with predicted molecular consequences and affected genes.
[^peptidiq]: **PeptidIQ V3** — the project's peptide-response interpretation layer (version 3), extending the genomics pipeline to predict how a person's genotype affects their response to peptide/hormone therapies.
[^orm]: **ORM (Object-Relational Mapper)** — a library (here SQLAlchemy 2.0) that maps database tables to Python objects, so queries are written in Python instead of raw SQL.
[^async]: **async helpers** — non-blocking functions (Python `async`/`await`) that let the server handle other work while waiting on database I/O.
[^peptidegenes]: **AR, ESR1, ESR2, OXTR, MC4R, GLP1R, RET, TP53, BRCA1** — genes seeded in the peptide library: androgen receptor (AR), estrogen receptors α/β (ESR1/ESR2), oxytocin receptor (OXTR), melanocortin-4 receptor (MC4R), GLP-1 receptor (GLP1R), the RET proto-oncogene, and the tumor-suppressors TP53/BRCA1.
[^jsonschema]: **JSON Schema 2020-12** — a versioned standard (draft 2020-12) for formally describing and validating the structure of JSON documents; used to lock the scoring engine's input/output format.
[^expansionhunter]: **ExpansionHunter** — an Illumina open-source tool that estimates the size of short tandem repeat expansions directly from aligned sequencing reads.
[^str]: **STR (Short Tandem Repeat)** — a stretch of DNA where a short motif repeats many times (e.g. `CAG CAG CAG…`); the number of repeats can be disease-relevant.
[^arcag]: **AR CAG repeat** — the polyglutamine (CAG)ₙ repeat in the androgen receptor (AR) gene; its length modulates receptor activity and is clinically significant (e.g. in spinal-bulbar muscular atrophy and androgen sensitivity).
[^bam]: **BAM / CRAM** — compressed binary formats for aligned sequencing reads. BAM is the classic format; CRAM is a more compressed, reference-based successor. Repeat calling needs the actual reads, not just a variant list.
[^ancestry]: **Ancestry-adjusted reference ranges** — "normal" repeat-length distributions differ by genetic ancestry, so the interpretation thresholds are calibrated per population group to avoid mis-flagging.
[^kegg]: **KEGG (Kyoto Encyclopedia of Genes and Genomes)** — a public database of biological pathways; a "pathway" is a known network of interacting genes/proteins carrying out a cellular process.
[^pathways]: **The 8 pathways** — biological signalling/metabolic networks: estrogen signalling, GnRH (gonadotropin-releasing hormone) signalling, serotonergic synapse (serotonin neurotransmission), MAPK and PI3K-AKT (core cell-growth cascades), adipocytokine (fat-tissue signalling), melanocortin/MC4R (appetite/energy), and steroid-hormone biosynthesis.
[^cohit]: **Co-hit** — when a patient carries variants in two genes that fall in related pathways at once; such combinations can carry extra clinical meaning beyond either gene alone.
[^notion]: **Notion** — a collaborative documentation/wiki app where the predictive-logic spec is maintained.
[^fasta]: **FASTA** — a plain-text format for reference DNA/protein sequences; ExpansionHunter needs the reference genome FASTA to interpret read alignments.
[^prs]: **PRS (Polygenic Risk Score)** — a single score aggregating the small effects of many variants to estimate genetic predisposition to a trait or disease.

Roadmap: `docs/roadmap.md`
