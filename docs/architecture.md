# Architecture

U4U takes a raw genome file, annotates each variant against clinical and population databases, scores and ranks findings, and returns a list of plain-English interpretations.

The core pipeline (`engine/`) is complete. The web layer does not exist yet.

---

## System Diagram

```mermaid
flowchart TD
    subgraph INPUT["Input"]
        A1["23andMe .txt"]
        A2["VCF / .vcf.gz"]
        A3["CSV"]
        A4["rsID list"]
    end

    subgraph ENGINE["engine/  (exists)"]
        B1["validate + parse"]
        B2["quality filter + whitelist"]
        B3["rsID resolution + deduplicate"]
        B4["annotate"]
        B5["score + summarize + sort"]
        B1 --> B2 --> B3 --> B4 --> B5
    end

    subgraph APIS["External APIs  (called per variant during annotation)"]
        C1["Ensembl VEP\nfunctional consequence"]
        C2["NCBI ClinVar\nclinical classification"]
        C3["gnomAD\npopulation frequency"]
        C4["MyVariant.info\nfallback aggregator"]
    end

    subgraph OUTPUT["Output"]
        D1["list[dict]\nscored + ranked variants"]
    end

    subgraph MISSING["Not built yet"]
        E1["FastAPI\n/analyze endpoint"]
        E2["Postgres\nannotation cache\ncondition library"]
        E3["Condition library\nSasank — content missing"]
        E4["Frontend\nupload + results"]
    end

    INPUT --> B1
    B4 <-->|"per variant"| C1
    B4 <-->|"per variant"| C2
    B4 <-->|"per variant"| C3
    B4 <-->|"fallback only"| C4
    B5 --> D1
    D1 -->|"wraps engine"| E1
    E1 <-->|"cache lookup"| E2
    E2 <-->|"condition_key lookup"| E3
    E1 --> E4
```

---

## Stack

| Component | Technology | Status |
|-----------|-----------|--------|
| Annotation pipeline | Python 3.11+ | Working |
| API layer | FastAPI + thread pool | Not built |
| Database | Postgres | Not built |
| Auth | Authelia | Not built (V2) |
| Frontend | React | Not built |
| Container | Docker | Not built |
| Hosting | Hampton's K8s cluster | Not deployed |
| CI | GitHub Actions | Running |

---

## Data flow

1. File uploaded via POST /analyze (not yet built)
2. FastAPI reads bytes, calls `run_pipeline(file_bytes, filename, filters)`
3. Engine annotates each variant by calling VEP, ClinVar, gnomAD sequentially
4. Engine returns `list[dict]` sorted by score
5. FastAPI checks `condition_key` in each result against Postgres condition library
6. Merged result returned to frontend

The annotation cache (Postgres) intercepts step 3: if a variant's coordinates are already cached, the external API call is skipped.

---

## Entry point

```python
from engine import run_pipeline

results = run_pipeline(
    file_bytes,          # bytes — never written to disk
    filename,            # used for format detection only
    filters=["acmg81_rsids.txt"]  # empty = all variants
)
# returns list[dict], score descending
```

Full pipeline spec: `docs/pipeline.md`
External APIs: `docs/integrations.md`
Interpretation logic: `docs/interpretation.md`
Current build status: `docs/project-status.md`
