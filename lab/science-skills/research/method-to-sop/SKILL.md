---
name: method-to-sop
description: "Use when turning a method revision into a traceable SOP."
---

# Method to SOP (lab jail)

One selected revision → versioned SOP. Unbound critical params stay draft.

```bash
PYTHONPATH=/opt/litreview/src python3 -m litreview method-proof sop-check INSTANCE/data/logic.jsonl --procedure <id>
```

No invented concentrations, spacers, or safety. Draft ≠ bench commit.
