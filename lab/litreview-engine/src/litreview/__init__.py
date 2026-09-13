"""Canonical literature-formalization engine."""

__version__ = "0.4.0"
ENGINE_VERSION = "0.4.0"
SCHEMA_VERSION = "logic-v0"  # baseline; v1 is additive
SCHEMA_V1 = "logic-v1"
ACCEPTED_SCHEMAS = (SCHEMA_VERSION, SCHEMA_V1)

KINDS = (
    "span",
    "mention",
    "identity_mapping",
    "proposition",
    "selection",
    "evidence_assessment",
    "premise",
    "derivation",
    "evidence_link",
    "law_obligation",
    "rule_candidate",
    "long_row",
    "result_evidence",
)

LINK_KINDS = (
    "cites_precedent",
    "rests_on",
    "fails_to_rest_on",
    "contradicts",
    "justified_by",
    "uses",
    "produced_by",
    "depicts_experiment",
)
ASSESSMENT_VERDICTS = ("supports", "partial", "unsupported", "thin-cite-only")
SELECTION_STATUSES = (
    "selected",
    "deferred",
    "excluded-by-scope",
    "unresolved",
    "rejected-as-unsupported",
)
ACCESS = ("oa", "inbox", "missing")
PROPOSITION_SORTS = (
    "method",
    "method_claim",
    "result",
    "research_question",
    "procedure",
    "experiment",
    "figure",
    "figure_panel",
    "method_operation",
    "claim",
)
EXTRACTION_STATES = ("stated", "inferred", "not_reported", "source_unavailable", "pending")
ARGUMENT_KINDS = ("empirical", "deductive", "transport", "composition")
JUSTIFICATION_ROLES = ("method-development", "method-validation", "mixed")
REVIEW_STATES = ("pending", "accepted", "rejected", "superseded", "stale")
GAP_TYPES = (
    "paywall",
    "no_oa",
    "missing_validation",
    "contradiction",
    "incomplete_search",
    "missing_bridge",
    "cycle",
    "hop_budget",
    "unresolved_id",
    "application_only",
    "transport_unvalidated",
)
METHOD_ORIGINS = ("published", "reconstructed")
METHOD_LIFECYCLES = (
    "proposed",
    "selected-for-planning",
    "authorized-for-pilot",
    "superseded",
)
RULE_CTORS = (
    "ConvertUnit",
    "ConvertUnitAuto",
    "ThresholdToCategory",
    "Scale",
    "Shift",
    "Log2Transform",
    "ToZScore",
    "ForceNonNegative",
    "CtToAbundance",
    "MethylationLogit",
    "NegLog10",
    "AsinhScale",
    "ClampRange",
    "QuantileProbitRule",
    "FamilyPITRule",
)
