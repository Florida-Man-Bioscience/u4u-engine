---
name: lit-review
description: "Use when formalizing papers into a licensed evidence graph or a new-topic engine instance."
---

# Literature-review engine (lab jail)

Canonical engine is `/opt/litreview` (`python3 -m litreview`). Topic instances live under `/data/workspace/<slug>/`. Empty of partner-lab trees.

HTTP tool (Bearer required): `POST /api/v1/tools/paper-decomposition/admit` with `{records:[...]}` or `{jsonl:"..."}`.

## CLI

```bash
PYTHONPATH=/opt/litreview/src python3 -m litreview init-instance --id <slug> --dest /data/workspace/<slug>
PYTHONPATH=/opt/litreview/src python3 -m litreview paper-decomposition admit INSTANCE/data/logic.jsonl
PYTHONPATH=/opt/litreview/src python3 -m litreview validate INSTANCE/data/logic.jsonl
PYTHONPATH=/opt/litreview/src python3 -m litreview method-proof closure INSTANCE/data/logic.jsonl --claim <id>
```

SSoT is instance `data/logic.jsonl`. Complementary producers: `paper-logical-reconstruction` (panels + Methods), `paper-experimental-design` (design matrix), `reconstruct-method`, `method-to-sop`.

Recipes: `references/include-what.md`.

## Cannot

- Partner-lab trees (Yue/ARMH3, Oxford ERV, Harmonia IP)
- Invented PMID/DOI
- Elsevier curl (Firefox/inbox on the customer desk)
- Therapeutic claims / grant submit
