# Validation artifacts

This directory holds **executable validation packages** that implement slices of
the umbrella Validation Master Plan (`docs/clinical-validation-plan.md`).

## Packages

| Package | Path | Purpose |
|---|---|---|
| **Prediction Efficacy Audit Program (PEAP)** | [`prediction-efficacy-audit/`](prediction-efficacy-audit/) | Pre-trial audit of the HBRI peptide-response predictor and related surfaces — freeze, claims, SAP, gates A–C |

## Status legend (gate colors)

| Color | Meaning |
|---|---|
| **GREEN** | Criterion met with evidence on this commit |
| **YELLOW** | Partial / mitigated / requires human ratification |
| **RED** | Blocks Gate C (enrollment with locked primary predictor) unless formally de-scoped |
| **N/A** | Out of package scope |

## Relationship to IRB / clinical ops

Human-subjects process (UF sIRB, consent, BAA/DUA, reliance) is owned by
`docs/irb-plan-glp1.md` / `docs/irb-plan.md`. PEAP supplies scientific readiness
for the **predictor**, not clinic contracting.

**Enrollment operations** (how the prospective observational cohort reaches its
ops headcount — clinic network, funnel, strata, gates):  
[`docs/enrollment-strategy.md`](../enrollment-strategy.md).  
Ops target (~1,000 enrolled) ≠ powered primary completer N until SAP §6 is locked.

## Non-claims

Nothing in this directory asserts that the software is clinically validated or
that any peptide is efficacious. Simulation calibration ≠ clinical validity.
