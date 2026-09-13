---
name: reconstruct-method
description: "Use when composing a method from the proof graph."
---

# Reconstruct a method (lab jail)

Proposed method for a new question. Do not harvest papers. Do not write an SOP.

Persist `generalization_assumption` (`taxon|system|assay|io|transfer`) and `bridge_requirement` when the application context differs from the published method.

```bash
PYTHONPATH=/opt/litreview/src python3 -m litreview method-proof reconstruct-check INSTANCE/data/logic.jsonl --method <id>
```
