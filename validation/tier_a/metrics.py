"""
validation/tier_a/metrics.py
============================
Pure concordance metrics for Tier A analytical validation.

These functions take *already-extracted* observed/expected values and compute
accuracy statistics. They contain no I/O and no pipeline or network calls, so
they are deterministic and unit-testable offline — which is where the
correctness of the validation evidence actually lives. The runner
(`validation/tier_a/run.py`) is responsible for turning a reference sample into
the (observed, expected) pairs these functions consume.

Two concordance tracks are supported:

1. Categorical concordance (PGx diplotype / phenotype): for each
   (sample, gene) the observed call is compared to a reference consensus call.
   Reported as exact-match concordance rate with a per-category breakdown and an
   itemized discordance list.

2. Variant genotype concordance (GIAB-style): observed vs. expected genotype at
   a set of sites, reduced to a confusion matrix and the standard
   sensitivity / specificity / precision / F1 derived from it.

Nothing here fabricates a denominator: if there are no comparisons, rates are
reported as ``None`` (undefined), never as a misleading 0.0 or 1.0.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Hashable, Optional


# ──────────────────────────────────────────────────────────────────────────
# 1. Categorical concordance (PGx diplotype / phenotype, or any label match)
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class Discordance:
    """A single observed≠expected comparison, kept for the audit trail."""
    sample: str
    key: str               # e.g. gene name "CYP2C19"
    expected: Optional[str]
    observed: Optional[str]


@dataclass
class CategoricalConcordance:
    """Result of comparing observed vs. expected categorical labels."""
    n_compared: int
    n_concordant: int
    discordances: list[Discordance] = field(default_factory=list)
    # per-key (e.g. per-gene) tallies: key -> (concordant, compared)
    by_key: dict[str, tuple[int, int]] = field(default_factory=dict)
    # comparisons skipped because observed or expected was missing
    n_skipped_missing: int = 0

    @property
    def concordance_rate(self) -> Optional[float]:
        """Fraction exactly concordant, or None if nothing was compared."""
        if self.n_compared == 0:
            return None
        return self.n_concordant / self.n_compared

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_compared": self.n_compared,
            "n_concordant": self.n_concordant,
            "n_skipped_missing": self.n_skipped_missing,
            "concordance_rate": self.concordance_rate,
            "by_key": {
                k: {
                    "concordant": c,
                    "compared": n,
                    "rate": (c / n) if n else None,
                }
                for k, (c, n) in sorted(self.by_key.items())
            },
            "discordances": [
                {
                    "sample": d.sample,
                    "key": d.key,
                    "expected": d.expected,
                    "observed": d.observed,
                }
                for d in self.discordances
            ],
        }


def _norm(value: Optional[str]) -> Optional[str]:
    """Normalize a label for comparison: strip, collapse case. None stays None."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def compare_categorical(
    observed: dict[tuple[str, str], Optional[str]],
    expected: dict[tuple[str, str], Optional[str]],
    *,
    case_sensitive: bool = False,
) -> CategoricalConcordance:
    """Compare two ``{(sample, key): label}`` maps.

    Only keys present in ``expected`` are scored (the reference defines the
    denominator). A comparison is *skipped* — not counted as discordant — when
    either side is missing a value, so that "the pipeline made no call" is not
    silently scored as a wrong call; skips are tallied separately.
    """
    result = CategoricalConcordance(n_compared=0, n_concordant=0)

    for ref_key, exp_raw in expected.items():
        sample, key = ref_key
        exp = _norm(exp_raw)
        obs = _norm(observed.get(ref_key))

        if exp is None or obs is None:
            result.n_skipped_missing += 1
            continue

        cmp_exp, cmp_obs = (exp, obs) if case_sensitive else (exp.lower(), obs.lower())
        is_match = cmp_exp == cmp_obs

        result.n_compared += 1
        prev_c, prev_n = result.by_key.get(key, (0, 0))
        result.by_key[key] = (prev_c + (1 if is_match else 0), prev_n + 1)

        if is_match:
            result.n_concordant += 1
        else:
            result.discordances.append(
                Discordance(sample=sample, key=key, expected=exp, observed=obs)
            )

    return result


# ──────────────────────────────────────────────────────────────────────────
# 2. Variant genotype concordance (confusion-matrix style)
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class ConfusionMatrix:
    """Counts for a binary "variant present and correctly genotyped" decision.

    - tp: site is a true variant AND observed genotype matches truth
    - fp: pipeline reports a variant the truth set says is absent (ref/ref)
    - fn: truth has a variant the pipeline did not report (or reported as ref)
    - tn: site is truly ref/ref and pipeline also reports no variant
    - genotype_mismatch: variant detected at a true-variant site but the
          genotype (e.g. het vs hom-alt) disagrees — tracked separately because
          it is "detected but miscalled", distinct from a clean TP or a miss.
    """
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0
    genotype_mismatch: int = 0

    @staticmethod
    def _ratio(num: int, den: int) -> Optional[float]:
        return (num / den) if den else None

    @property
    def sensitivity(self) -> Optional[float]:
        # recall for variant detection
        return self._ratio(self.tp, self.tp + self.fn)

    @property
    def specificity(self) -> Optional[float]:
        return self._ratio(self.tn, self.tn + self.fp)

    @property
    def precision(self) -> Optional[float]:
        # positive predictive value
        return self._ratio(self.tp, self.tp + self.fp)

    @property
    def f1(self) -> Optional[float]:
        p, r = self.precision, self.sensitivity
        if p is None or r is None or (p + r) == 0:
            return None
        return 2 * p * r / (p + r)

    @property
    def genotype_concordance(self) -> Optional[float]:
        """Of detected true-variant sites, fraction with the correct genotype.

        Every detected true-variant site is counted in ``tp`` (detection),
        whether or not the genotype matched; ``genotype_mismatch`` is the subset
        of those whose genotype disagreed. So detected == tp and the correctly
        genotyped count is ``tp - genotype_mismatch``.
        """
        return self._ratio(self.tp - self.genotype_mismatch, self.tp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "tn": self.tn,
            "genotype_mismatch": self.genotype_mismatch,
            "sensitivity": self.sensitivity,
            "specificity": self.specificity,
            "precision": self.precision,
            "f1": self.f1,
            "genotype_concordance": self.genotype_concordance,
        }


# Genotype sentinel meaning "no variant call at this site" (reference/reference).
REF = "ref"


def compare_genotypes(
    observed: dict[Hashable, Optional[str]],
    expected: dict[Hashable, Optional[str]],
) -> ConfusionMatrix:
    """Build a confusion matrix from observed vs. expected genotype-by-site maps.

    Each value is a normalized genotype string (e.g. ``"0/1"``, ``"1/1"``) or
    the :data:`REF` sentinel for a confidently-called reference site. A key
    absent from ``observed`` is treated as "pipeline made no call" → reference
    for the purpose of detection (a miss against a true variant).

    The denominator is the union of sites in ``expected`` and ``observed`` so
    that false positives (pipeline-only sites) are counted, not dropped.
    """
    cm = ConfusionMatrix()
    all_sites = set(expected) | set(observed)

    for site in all_sites:
        exp = _norm(expected.get(site)) or REF
        obs = _norm(observed.get(site)) or REF

        exp_is_var = exp != REF
        obs_is_var = obs != REF

        if exp_is_var and obs_is_var:
            if exp == obs:
                cm.tp += 1
            else:
                # detected the variant but called the wrong genotype
                cm.genotype_mismatch += 1
                cm.tp += 1  # still a true detection; genotype error tracked separately
        elif exp_is_var and not obs_is_var:
            cm.fn += 1
        elif not exp_is_var and obs_is_var:
            cm.fp += 1
        else:
            cm.tn += 1

    return cm
