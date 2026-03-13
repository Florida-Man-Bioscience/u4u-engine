# Architecture

U4U takes a raw genome file, annotates each variant against clinical and population databases, scores findings, and returns plain-English interpretations.

**Engine (`engine/`) is complete. The web layer does not exist yet.**

---

## System Diagram

```mermaid
flowchart TD
    subgraph INPUT["Input"]
        A1["23andMe .txt"]
        A2["VCF / .vcf.gz"]
        A3["CSV / rsID list"]
    end

    subgraph ENGINE["engine/  (exists)"]
        B1["validate + parse"]
        B2["quality filter + whitelist"]
        B3["rsID resolution + deduplicate"]
        B4["annotate"]
        B5["score + summarize + sort"]
        B1 --> B2 --> B3 --> B4 --> B5
    end

    subgraph APIS["External APIs"]
        C1["Ensembl VEP"]
        C2["NCBI ClinVar"]
        C3["gnomAD"]
        C4["MyVariant.info (fallback)"]
    end

    subgraph OUTPUT["Output"]
        D1["list[dict] — scored + ranked"]
    end

    subgraph MISSING["Not built yet"]
        E1["FastAPI /analyze"]
        E2["Postgres cache + condition library"]
        E3["Frontend upload + results"]
    end

    INPUT --> B1
    B4 <-->|"per variant"| C1
    B4 <-->|"per variant"| C2
    B4 <-->|"per variant"| C3
    B4 <-->|"fallback"| C4
    B5 --> D1
    D1 -->|"wraps engine"| E1
    E1 <--> E2
    E1 --> E3
```

---

## Stack

| Component | Technology | Status |
|-----------|-----------|--------|
| Annotation pipeline | Python 3.11+ | **Working** |
| API layer | FastAPI | Not built |
| Database | Postgres | Not built |
| Frontend | React | Not built |
| Container | Docker | Not built |
| Hosting | Hampton's K8s cluster | Not deployed |
| CI | GitHub Actions | Running |

---

## Data flow

1. `POST /analyze` receives file bytes
2. FastAPI calls `run_pipeline(file_bytes, filename, filters)`
3. Engine annotates each variant via VEP → ClinVar → gnomAD (Postgres cache intercepts if warm)
4. Engine returns `list[dict]` sorted by score
5. API layer merges `condition_key` results from Postgres condition library
6. Response returned to frontend

---

## Entry point

```python
from engine import run_pipeline

results = run_pipeline(
    file_bytes,          # bytes — never written to disk
    filename,            # format detection only
    filters=["acmg81_rsids.txt"]
)
# returns list[dict], score descending
```

Full pipeline spec: `docs/pipeline.md`
External APIs: `docs/integrations.md`
Interpretation logic: `docs/interpretation.md`
Build status + UI spec: `docs/project-status.md`

---

## Next steps

1. **Hampton** — create `api/main.py`: `POST /analyze` reads uploaded file bytes, calls `run_pipeline(await file.read(), file.filename, filters=["acmg81_rsids.txt"])`, returns JSON
2. **Hampton** — write `Dockerfile`: `FROM python:3.11-slim`, copy `engine/`, `RUN pip install -e engine/`, `CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0"]`, deploy to K8s
3. **Curtis** — register domain; point DNS A record at Hampton's cluster IP so there's a real URL before Phase 2 work starts
