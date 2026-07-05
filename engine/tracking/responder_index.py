"""
engine/tracking/responder_index.py
==================================
Hierarchical Bayesian Responder Index (HBRI) — Phase 0 core.

This module generalises the scalar "responder strength" ``r`` used by
:mod:`engine.tracking.genetics` into a regularised, multi-feature index η:

    η_{p,k} = 1 + Δ · tanh( βᵀ x_{p,k} )        Δ = R_DELTA_SCALE (=0.72)

bounded to ``[1 - Δ, 1 + Δ]``. ``x`` is a feature vector assembled from
registered *feature adapters*; each adapter contributes one or more
``Feature`` records (a standardised value ``x_j``, a coefficient ``β_j`` and
a variance ``var_j`` on that value). The genetics adapter is the anchored
reference feature: it emits ``x_g = w`` (today's summed genetic weight) with
``β_g = 1``, so with genetics alone ``βᵀx = w`` and η is byte-for-byte the
old ``1 + Δ·tanh(w)``.

Feature uncertainty propagates into ``Var(η)`` by the delta method::

    dη/d(βᵀx) = Δ · sech²(βᵀx)
    Var(η)    = (Δ · sech²(βᵀx))² · Var(βᵀx)
              = (Δ · sech²(βᵀx))² · Σ_j β_j² · var_j        (features independent)

so a feature only moves the responder as much as its certainty warrants.

Behaviour-preservation contract
-------------------------------
With **only** the genetics adapter firing and ``β_g = 1`` the index must
reproduce today's ``derive_responder_prior`` numbers exactly (to floating
point). The genetics adapter achieves this by reporting a feature-space
variance ``var_g = today_sd² / (Δ·sech²(w))²`` so that the delta-method
propagation cancels back to ``today_sd²``. See
:mod:`engine.tracking.feature_adapters.genetics_adapter` and
``docs/models/peptide-response-model.md`` for the frozen composition rule
that governs how the genetics contribution re-evaluates once *other*
adapters shift the operating point (a Phase-1 concern; no other adapters
exist yet in this PR).

Auto-discovering registry
-------------------------
Adapters live in the :mod:`engine.tracking.feature_adapters` package and
self-register with the ``@register_adapter`` decorator. The package's
``__init__`` imports every submodule via :mod:`pkgutil`, so a Phase-1 unit
adds an adapter file with **zero edits to shared files**.

Pure stdlib (``math``) — matches the surrounding bayes/pooling code.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

# Δ is owned by genetics.py — single source of truth. This is a one-way
# import (genetics.py imports *us* lazily, inside functions, so there is no
# cycle at module-load time).
from .genetics import R_DELTA_SCALE

if TYPE_CHECKING:  # avoid any runtime coupling beyond the Δ constant
    from .genetics import GeneticProfile

log = logging.getLogger(__name__)

# Clamp the linear predictor before evaluating sech² so ``math.cosh`` cannot
# overflow (it raises OverflowError past ~710). In practice ``|βᵀx|`` is well
# under 2 for genetics, so this never binds; it is purely defensive. The same
# clamp is applied on both sides of the var_g back-out and the Var(η)
# propagation, so the delta-method cancellation is exact regardless.
_LINEAR_CLAMP = 30.0


def _deta_dlinear(linear: float) -> float:
    """dη/d(βᵀx) = Δ · sech²(βᵀx). Shared by the genetics adapter's
    variance back-out and the index's Var(η) so the two cancel exactly."""
    x = max(-_LINEAR_CLAMP, min(_LINEAR_CLAMP, linear))
    cosh = math.cosh(x)
    return R_DELTA_SCALE / (cosh * cosh)


# ── Feature + index datatypes ───────────────────────────────────────────────

@dataclass(frozen=True)
class Feature:
    """One standardised feature contributing to the responder index.

    ``value`` is the (standardised) feature value ``x_j``; the genetics
    reference feature passes the raw summed weight ``w`` through unstandardised
    with ``beta = 1``. ``variance`` is the variance of the *feature value*
    estimate — propagated into ``Var(η)`` via the delta method.
    """
    name: str
    value: float
    beta: float
    variance: float
    source: str = ""          # adapter name, for provenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": round(self.value, 6),
            "beta": round(self.beta, 6),
            "variance": round(self.variance, 8),
            "source": self.source,
        }


@dataclass(frozen=True)
class FeatureVector:
    """The assembled, peptide-scoped feature vector for one prediction."""
    peptide_name: str
    features: tuple[Feature, ...] = ()

    @property
    def linear(self) -> float:
        """βᵀx."""
        return sum(f.beta * f.value for f in self.features)

    @property
    def var_linear(self) -> float:
        """Var(βᵀx) = Σ β_j² var_j (features treated as independent)."""
        return sum((f.beta ** 2) * f.variance for f in self.features)


@dataclass(frozen=True)
class ResponderIndex:
    """Result of :func:`responder_index`."""
    eta: float                       # responder index (centred at 1.0)
    var_eta: float                   # Var(η) from the delta method
    linear: float                    # βᵀx
    features: tuple[Feature, ...]    # provenance: which features fired

    @property
    def sd(self) -> float:
        return math.sqrt(max(self.var_eta, 0.0))

    def to_dict(self) -> dict[str, Any]:
        return {
            "eta": round(self.eta, 6),
            "var_eta": round(self.var_eta, 8),
            "sd": round(self.sd, 6),
            "linear": round(self.linear, 6),
            "features": [f.to_dict() for f in self.features],
        }


# ── Adapter context ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PatientHandle:
    """Minimal, de-identified patient handle passed to adapters.

    Kept deliberately small (opaque id + coarse demographics) so adapters can
    key covariates without the context carrying PHI.
    """
    id: str | None = None
    sex: str | None = None
    birth_year: int | None = None


@dataclass(frozen=True)
class ResponderContext:
    """Everything an adapter may need to compute its features.

    Frozen interface: future adapters (PRS, BPC-157, HealthKit, covariates)
    pull what they need from here without changing the ``FeatureAdapter``
    protocol. ``conn`` is an optional live DB handle for adapters that must
    query (e.g. a HealthKit behavioural-covariate adapter); genetics needs
    only ``profile``.
    """
    peptide_name: str
    profile: GeneticProfile | None = None
    patient: PatientHandle | None = None
    conn: Any = None
    extra: dict[str, Any] = field(default_factory=dict)


# ── Adapter protocol + registry ─────────────────────────────────────────────

@runtime_checkable
class FeatureAdapter(Protocol):
    """A pluggable source of responder features.

    ``name``            unique adapter id (registry key).
    ``required``        if True, an exception from ``features`` propagates
                        (preserves legacy error semantics for the anchored
                        genetics adapter); optional adapters (the Phase-1
                        default) are isolated so one bad adapter can't sink
                        the whole index. Checked via ``getattr(..., False)``
                        so optional adapters need not declare it.
    ``peptide_mask``    True iff this adapter contributes for ``peptide_name``.
    ``features``        map of feature-name → :class:`Feature` for a context.
    """
    name: str
    required: bool

    def peptide_mask(self, peptide_name: str) -> bool: ...

    def features(self, context: ResponderContext) -> dict[str, Feature]: ...


_REGISTRY: dict[str, FeatureAdapter] = {}


def register_adapter(cls):
    """Class decorator: instantiate ``cls`` and register the instance.

    Idempotent by ``name`` — re-importing an adapter module (common across
    test runs) simply replaces the prior instance rather than duplicating it.
    """
    inst = cls()
    _REGISTRY[inst.name] = inst
    return cls


def registered_adapters() -> dict[str, FeatureAdapter]:
    """Return the live registry (after ensuring adapters are discovered)."""
    _ensure_adapters_loaded()
    return dict(_REGISTRY)


_adapters_loaded = False


def _ensure_adapters_loaded() -> None:
    """Import the feature_adapters package on first use so its submodules
    self-register. Done lazily to keep module import order cycle-free."""
    global _adapters_loaded
    if _adapters_loaded:
        return
    # Importing the package runs its pkgutil auto-discovery.
    from . import feature_adapters  # noqa: F401  (import side effect)
    _adapters_loaded = True


# ── Public entry point ──────────────────────────────────────────────────────

def build_feature_vector(context: ResponderContext) -> FeatureVector:
    """Collect features from every registered adapter whose ``peptide_mask``
    matches ``context.peptide_name``."""
    _ensure_adapters_loaded()
    collected: list[Feature] = []
    for adapter in _REGISTRY.values():
        try:
            if not adapter.peptide_mask(context.peptide_name):
                continue
            feats = adapter.features(context)
        except Exception:  # noqa: BLE001 — isolate optional adapters
            # A `required` adapter (the anchored genetics one) preserves legacy
            # error semantics: its failure propagates rather than silently
            # degrading the prior to the degenerate η=1, Var(η)=0. Optional
            # adapters — the Phase-1 default — are isolated so one bad adapter
            # can't sink the whole index, but never silently: log for triage.
            if getattr(adapter, "required", False):
                raise
            log.warning(
                "feature adapter %r failed for peptide %r; skipping",
                getattr(adapter, "name", adapter), context.peptide_name,
                exc_info=True,
            )
            continue
        for f in feats.values():
            collected.append(f)
    return FeatureVector(peptide_name=context.peptide_name, features=tuple(collected))


def responder_index(context: ResponderContext) -> ResponderIndex:
    """Compute the responder index η, its variance, and provenance.

    η       = 1 + Δ · tanh(βᵀx)
    Var(η)  = (Δ · sech²(βᵀx))² · Σ_j β_j² var_j
    """
    fv = build_feature_vector(context)
    linear = fv.linear
    slope = _deta_dlinear(linear)
    eta = 1.0 + R_DELTA_SCALE * math.tanh(linear)
    var_eta = (slope * slope) * fv.var_linear
    return ResponderIndex(
        eta=eta,
        var_eta=var_eta,
        linear=linear,
        features=fv.features,
    )
