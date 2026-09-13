"""Deterministic admission for logic-v0 JSONL. Not a prover."""

from __future__ import annotations

from typing import Any, Iterable

from litreview import (
    ACCESS,
    ACCEPTED_SCHEMAS,
    ARGUMENT_KINDS,
    ASSESSMENT_VERDICTS,
    EXTRACTION_STATES,
    GAP_TYPES,
    JUSTIFICATION_ROLES,
    KINDS,
    LINK_KINDS,
    METHOD_LIFECYCLES,
    METHOD_ORIGINS,
    PROPOSITION_SORTS,
    REVIEW_STATES,
    RULE_CTORS,
    SCHEMA_V1,
    SELECTION_STATUSES,
)
from litreview.revisions import revision_matches
from litreview.paper_decomposition import (
    GENERALIZATION_DIMENSIONS,
    GENERALIZATION_SOURCE_BASES,
    methods_slots,
    panel_slots,
    slot_state,
)

COMMON = ("record_id", "corpus_id", "schema_version", "kind")

REQUIRED: dict[str, tuple[str, ...]] = {
    "span": (*COMMON, "pmid", "locator", "sha256", "access"),
    "mention": (*COMMON, "text"),
    "identity_mapping": (*COMMON, "raw", "candidates"),
    "proposition": (*COMMON, "predicate", "args", "context", "span_id"),
    "selection": (*COMMON, "span_id", "status"),
    "evidence_assessment": (*COMMON, "target_id", "verdict", "source"),
    "premise": (*COMMON, "proposition_id", "assessment_id"),
    "derivation": (*COMMON, "premise_ids", "conclusion_id", "rule_names", "span_ids"),
    "evidence_link": (*COMMON, "src_id", "dst_id", "link_kind"),
    "law_obligation": (*COMMON, "proposition_id", "scope"),
    "rule_candidate": (*COMMON, "constructor", "scope"),
    "long_row": (*COMMON, "feature", "sample", "value", "assay", "unit"),
    "result_evidence": (*COMMON, "target_id", "source", "run_id", "role"),
}


class AdmissionError(ValueError):
    pass


def _need(rec: dict[str, Any], fields: Iterable[str]) -> list[str]:
    miss = []
    for f in fields:
        if f not in rec:
            miss.append(f)
            continue
        v = rec[f]
        if f == "pmid" and v is None:
            continue
        if v in ("", []):
            miss.append(f)
    return miss


def validate_record(rec: dict[str, Any], index: dict[str, dict[str, Any]] | None = None) -> list[str]:
    errors: list[str] = []
    rid = rec.get("record_id", "<no-id>")
    kind = rec.get("kind")
    if kind not in KINDS:
        return [f"{rid}: unknown kind {kind!r}"]
    if rec.get("schema_version") not in ACCEPTED_SCHEMAS:
        errors.append(f"{rid}: schema_version must be one of {ACCEPTED_SCHEMAS}")
    required = REQUIRED[kind]
    if kind == "premise" and rec.get("origin") == "assumption":
        required = (*COMMON, "subject_refs", "dimension", "proposition", "source_basis")
    missing = _need(rec, required)
    if missing:
        errors.append(f"{rid}: missing {missing}")

    if kind == "proposition":
        sort = rec.get("sort")
        if sort is not None and sort not in PROPOSITION_SORTS:
            errors.append(f"{rid}: unknown proposition sort {sort!r}")
        if sort == "method":
            if rec.get("revision") in (None, ""):
                errors.append(f"{rid}: method requires revision")
            origin = rec.get("origin")
            if origin in (None, ""):
                errors.append(f"{rid}: method requires origin")
            elif origin not in METHOD_ORIGINS:
                errors.append(f"{rid}: unknown method origin {origin!r}")
            lifecycle = rec.get("lifecycle")
            if lifecycle is not None and lifecycle not in METHOD_LIFECYCLES:
                errors.append(f"{rid}: unknown method lifecycle {lifecycle!r}")
        elif sort == "procedure":
            if not any(rec.get(field) not in (None, "", []) for field in ("operationalizes_id", "method_id")):
                errors.append(f"{rid}: procedure requires operationalizes_id or method_id")
            if not any(rec.get(field) not in (None, "", []) for field in ("operationalizes_revision", "method_revision")):
                errors.append(f"{rid}: procedure requires operationalizes_revision or method_revision")

    if rec.get("argument_kind") is not None and rec.get("argument_kind") not in ARGUMENT_KINDS:
        errors.append(f"{rid}: unknown argument_kind {rec.get('argument_kind')!r}")
    if rec.get("gap_type") is not None and rec.get("gap_type") not in GAP_TYPES:
        errors.append(f"{rid}: unknown gap_type {rec.get('gap_type')!r}")

    if kind == "premise" and rec.get("origin") == "assumption":
        subject_refs = rec.get("subject_refs")
        if not isinstance(subject_refs, list) or not subject_refs or any(
            not isinstance(ref, str) or not ref.strip() for ref in subject_refs
        ):
            errors.append(f"{rid}: subject_refs must be a non-empty list of record ids")
        dimension = rec.get("dimension")
        if dimension not in GENERALIZATION_DIMENSIONS:
            errors.append(
                f"{rid}: dimension must be one of {GENERALIZATION_DIMENSIONS}"
            )
        proposition = rec.get("proposition")
        if not isinstance(proposition, str) or not proposition.strip():
            errors.append(f"{rid}: proposition must be a non-empty string")
        source_basis = rec.get("source_basis")
        if source_basis not in GENERALIZATION_SOURCE_BASES:
            errors.append(
                f"{rid}: source_basis must be one of {GENERALIZATION_SOURCE_BASES}"
            )

    if kind == "evidence_assessment" and rec.get("gap_type") == "missing_bridge":
        recipe = rec.get("resolution_recipe")
        if recipe in (None, "", [], {}):
            errors.append(f"{rid}: missing_bridge requires resolution_recipe")

    if kind == "span" and rec.get("access") not in ACCESS:
        errors.append(f"{rid}: access must be one of {ACCESS}")

    if kind == "identity_mapping":
        cands = rec.get("candidates") or []
        if not isinstance(cands, list):
            errors.append(f"{rid}: candidates must be a list")

    if kind == "selection" and rec.get("status") not in SELECTION_STATUSES:
        errors.append(f"{rid}: bad selection status")

    if kind == "evidence_assessment" and rec.get("verdict") not in ASSESSMENT_VERDICTS:
        errors.append(f"{rid}: bad verdict")

    if kind == "evidence_link" and rec.get("link_kind") not in LINK_KINDS:
        errors.append(f"{rid}: bad link_kind")

    if kind == "rule_candidate":
        ctor = rec.get("constructor")
        if ctor == "Custom" or ctor not in RULE_CTORS:
            errors.append(f"{rid}: constructor {ctor!r} is not serializable")

    if kind == "law_obligation":
        scope = rec.get("scope") or {}
        if not isinstance(scope, dict) or not scope:
            errors.append(f"{rid}: scope is mandatory (no silent universalization)")

    if kind == "result_evidence":
        if rec.get("role") == "prediction" and rec.get("evidence") == "supported":
            errors.append(f"{rid}: a prediction cannot confirm itself")

    if rec.get("schema_version") == SCHEMA_V1 and kind == "evidence_assessment":
        if rec.get("logic") == "entailed":
            errors.append(f"{rid}: critic supported cannot set logic=entailed")

    if index is not None:
        errors.extend(_referential(rec, index))
    return errors


def _referential(rec: dict[str, Any], index: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    rid = rec["record_id"]
    kind = rec["kind"]
    corpus = rec.get("corpus_id")

    def resolve(ref: str, expect: str | tuple[str, ...] | None = None) -> dict[str, Any] | None:
        tgt = index.get(ref)
        if tgt is None:
            errors.append(f"{rid}: dangling ref {ref}")
            return None
        if tgt.get("corpus_id") != corpus:
            errors.append(f"{rid}: cross-corpus ref {ref} ({tgt.get('corpus_id')} ≠ {corpus})")
            return None
        if expect:
            allowed = (expect,) if isinstance(expect, str) else expect
            if tgt.get("kind") not in allowed:
                errors.append(f"{rid}: {ref} is {tgt.get('kind')}, expected {allowed}")
                return None
        return tgt

    if kind == "proposition":
        sp = resolve(rec.get("span_id", ""), "span")
        if sp is not None and sp.get("access") != "oa" and sp.get("access") != "inbox":
            errors.append(f"{rid}: proposition licensed to non-inspectable span")

    if kind == "selection":
        resolve(rec.get("span_id", ""), "span")

    if kind == "evidence_assessment":
        resolve(rec.get("target_id", ""))

    if kind == "premise" and rec.get("origin") == "assumption":
        for ref in rec.get("subject_refs") or []:
            if isinstance(ref, str) and ref.strip():
                resolve(ref)

    if kind == "premise" and rec.get("origin") != "assumption":
        resolve(rec.get("proposition_id", ""), "proposition")
        ass = resolve(rec.get("assessment_id", ""), "evidence_assessment")
        if ass is not None and ass.get("verdict") == "partial":
            errors.append(f"{rid}: critic partial cannot be a derivation premise")

    if kind == "derivation":
        premise_records: list[dict[str, Any]] = []
        premise_props: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for pid in rec.get("premise_ids") or []:
            premise = resolve(pid, "premise")
            if premise is not None:
                premise_records.append(premise)
                premise_prop = resolve(premise.get("proposition_id", ""), "proposition")
                if premise_prop is not None:
                    premise_props.append((premise, premise_prop))
            if rec.get("logic") == "entailed" and premise is not None:
                quarantined = False
                for target_id in (premise.get("proposition_id"), premise.get("assessment_id")):
                    if not target_id:
                        continue
                    target = resolve(target_id)
                    if target is not None and (
                        target.get("admission") == "quarantined"
                        or (
                            target.get("schema_version") == "logic-v0"
                            and "admission" not in target
                        )
                    ):
                        quarantined = True
                if quarantined:
                    errors.append(f"{rid}: quarantined premise {pid}")
        conclusion_id = rec.get("conclusion_id", "")
        conclusion = resolve(conclusion_id, "proposition")
        for sid in rec.get("span_ids") or []:
            resolve(sid, "span")
        argument_kind = rec.get("argument_kind")
        if argument_kind == "transport" and conclusion is not None:
            conclusion_taxon = (conclusion.get("context") or {}).get("taxon")
            premise_taxa = {
                (prop.get("context") or {}).get("taxon")
                for premise, prop in premise_props
                if premise.get("origin") != "axiom"
                and prop.get("sort") in ("method_claim", "result")
                and (prop.get("context") or {}).get("taxon") is not None
            }
            has_transfer_axiom = any(
                premise.get("origin") == "axiom" and premise.get("transfer") is True
                for premise in premise_records
            )
            if (
                conclusion_taxon is not None
                and premise_taxa
                and conclusion_taxon not in premise_taxa
                and rec.get("transfer") is not True
                and not has_transfer_axiom
            ):
                errors.append(f"{rid}: transport requires explicit transfer")

        if argument_kind in {"transport", "composition"} and rec.get("logic") == "entailed":
            supported = any(
                assessment.get("kind") == "evidence_assessment"
                and assessment.get("target_id") == conclusion_id
                and assessment.get("evidence") == "supported"
                for assessment in index.values()
            )
            if supported and conclusion is not None:
                has_empirical_justification = False
                for link in index.values():
                    if (
                        link.get("kind") != "evidence_link"
                        or link.get("link_kind") != "justified_by"
                        or link.get("claim_ref") != conclusion_id
                    ):
                        continue
                    claim = index.get(link.get("claim_ref", ""))
                    argument = index.get(link.get("argument_ref", ""))
                    if (
                        claim is not None
                        and argument is not None
                        and claim.get("sort") == "method_claim"
                        and (claim.get("context") or {}).get("taxon")
                        == (conclusion.get("context") or {}).get("taxon")
                        and argument.get("sort") == "method_argument"
                        and argument.get("argument_kind") == "empirical"
                    ):
                        has_empirical_justification = True
                        break
                if not has_empirical_justification:
                    message = (
                        "transport does not inherit empirical support"
                        if argument_kind == "transport"
                        else "composition does not inherit empirical support"
                    )
                    errors.append(f"{rid}: {message}")

        if rec.get("logic") == "entailed":
            for link in index.values():
                if (
                    link.get("kind") == "evidence_link"
                    and link.get("link_kind") == "justified_by"
                    and link.get("argument_ref") == rid
                    and link.get("review_state") == "stale"
                ):
                    errors.append(f"{rid}: stale justification")

    if kind == "evidence_link":
        src = resolve(rec.get("src_id", ""), "proposition")
        dst = resolve(rec.get("dst_id", ""), "proposition")
        link_kind = rec.get("link_kind")
        if link_kind == "uses":
            if src is not None and src.get("sort") != "experiment":
                errors.append(f"{rid}: uses src must be sort=experiment")
            if dst is not None and dst.get("sort") != "method":
                errors.append(f"{rid}: uses dst must be sort=method")
        elif link_kind == "justified_by":
            required = (
                "method_revision",
                "claim_ref",
                "claim_revision",
                "argument_ref",
                "argument_revision",
                "publication_ref",
                "justification_role",
                "review_state",
                "span_id",
            )
            missing = [
                field
                for field in required
                if field not in rec or rec[field] in (None, "", [])
            ]
            if missing:
                errors.append(f"{rid}: justified_by requires {', '.join(missing)}")

            if src is not None and src.get("sort") != "method":
                errors.append(f"{rid}: justified_by src must be sort=method")
            if src is not None and src.get("origin") != "published":
                errors.append(f"{rid}: justified_by src origin must be published")
            if src is not None and "method_revision" in rec:
                if not revision_matches(rec.get("method_revision"), src.get("revision")):
                    errors.append(f"{rid}: revision mismatch")
            if dst is not None and dst.get("sort") != "result":
                errors.append(f"{rid}: justified_by dst must be sort=result")
            if dst is not None and dst.get("sort") == "result" and dst.get("temporal") == "planned":
                errors.append(f"{rid}: justified_by cannot target planned result")

            if rec.get("admission") == "stale":
                errors.append(f"{rid}: stale justification")

            claim = None
            claim_ref = rec.get("claim_ref")
            if claim_ref:
                claim = resolve(claim_ref, "proposition")
                if claim is not None and claim.get("sort") != "method_claim":
                    errors.append(f"{rid}: justified_by claim_ref must be sort=method_claim")
                if claim is not None and src is not None:
                    if not (
                        claim.get("method_id") == src.get("record_id")
                        or claim.get("claim_about") == src.get("record_id")
                    ):
                        errors.append(f"{rid}: claim method binding mismatch")
                    if not revision_matches(claim.get("method_revision"), rec.get("method_revision")):
                        errors.append(f"{rid}: revision mismatch")
                    claim_revision = claim.get("revision", 1)
                    if not revision_matches(rec.get("claim_revision"), claim_revision):
                        errors.append(f"{rid}: revision mismatch")

            argument = None
            argument_ref = rec.get("argument_ref")
            if argument_ref:
                argument = resolve(argument_ref, "derivation")
                target = index.get(argument_ref)
                if target is not None and target.get("kind") != "derivation":
                    errors.append(f"{rid}: justified_by requires empirical argument")
                if argument is not None and (
                    argument.get("sort") != "method_argument"
                    or argument.get("argument_kind") != "empirical"
                ):
                    errors.append(f"{rid}: justified_by requires empirical argument")
                if argument is not None and claim_ref and argument.get("conclusion_id") != claim_ref:
                    errors.append(f"{rid}: justified_by argument must conclude claim")
                if argument is not None and rec.get("dst_id"):
                    premises_result = False
                    for premise_id in argument.get("premise_ids") or []:
                        premise = resolve(premise_id, "premise")
                        if premise is not None and premise.get("proposition_id") == rec.get("dst_id"):
                            premises_result = True
                    if not premises_result:
                        errors.append(f"{rid}: justified_by argument must premise result")
                if argument is not None:
                    argument_revision = argument.get("argument_revision", 1)
                    if not revision_matches(rec.get("argument_revision"), argument_revision):
                        errors.append(f"{rid}: revision mismatch")

            span_id = rec.get("span_id")
            if span_id:
                span = resolve(span_id, "span")
                if span is not None and (
                    span.get("access") not in ("oa", "inbox")
                    or not (span.get("locator") or "").strip()
                ):
                    errors.append(f"{rid}: justified_by requires inspectable span")

            if rec.get("justification_role") not in JUSTIFICATION_ROLES:
                errors.append(f"{rid}: justified_by invalid justification_role")
            if rec.get("review_state") not in REVIEW_STATES:
                errors.append(f"{rid}: justified_by invalid review_state")

            raw_src = index.get(rec.get("src_id", ""))
            raw_dst = index.get(rec.get("dst_id", ""))
            if any(
                node is not None and node.get("origin") == "axiom"
                for node in (raw_src, raw_dst)
            ):
                errors.append(f"{rid}: justified_by forbidden on axiom")
            if argument is not None:
                for premise_id in argument.get("premise_ids") or []:
                    premise = resolve(premise_id, "premise")
                    if premise is not None and premise.get("origin") == "axiom":
                        errors.append(f"{rid}: justified_by forbidden on axiom")

        if link_kind == "cites_precedent":
            sid = rec.get("span_id")
            if not sid:
                errors.append(f"{rid}: cites_precedent requires span_id")
            else:
                sp = resolve(sid, "span")
                if sp is not None and sp.get("access") != "oa":
                    errors.append(f"{rid}: cites_precedent requires access=oa span")
                if sp is not None and not (sp.get("locator") or "").strip():
                    errors.append(f"{rid}: cites_precedent requires verbatim locator")
                if rec.get("schema_version") == SCHEMA_V1 and sp is not None:
                    quote = rec.get("quote")
                    if quote is not None and quote != sp.get("locator"):
                        errors.append(f"{rid}: quote must match span locator")
        if rec.get("schema_version") == SCHEMA_V1 and src and dst and rec.get("link_kind") == "cites_precedent":
            if (src.get("context") or {}).get("taxon") != (dst.get("context") or {}).get("taxon"):
                if not rec.get("transfer"):
                    errors.append(f"{rid}: context taxon mismatch; no silent transfer")
        if rec.get("schema_version") == SCHEMA_V1:
            for node in (src, dst):
                if not node:
                    continue
                mid = node.get("mapping_id")
                if not mid:
                    continue
                mp = index.get(mid)
                if mp and len(mp.get("candidates") or []) > 1 and not mp.get("chosen"):
                    errors.append(f"{rid}: ambiguous identity mapping {mid}")

    if kind == "law_obligation":
        resolve(rec.get("proposition_id", ""), "proposition")

    return errors


def _panel_slot_errors(rec: dict[str, Any]) -> list[str]:
    rid = rec.get("record_id", "<no-id>")
    slots = rec.get("slots")
    if not isinstance(slots, dict):
        missing = list(panel_slots())
    else:
        missing = [name for name in panel_slots() if name not in slots]

    errors: list[str] = []
    if missing:
        errors.append(f"{rid}: missing panel slots {missing}")

    if isinstance(slots, dict):
        for name in panel_slots():
            if name not in slots:
                continue
            state = slot_state(slots[name])
            if state not in EXTRACTION_STATES:
                errors.append(
                    f"{rid}: panel slot {name} state must be one of {EXTRACTION_STATES}"
                )
    return errors


def _methods_operation_slot_errors(rec: dict[str, Any]) -> list[str]:
    rid = rec.get("record_id", "<no-id>")
    slots = rec.get("slots")
    if not isinstance(slots, dict):
        missing = list(methods_slots())
    else:
        missing = [name for name in methods_slots() if name not in slots]

    errors: list[str] = []
    if missing:
        errors.append(f"{rid}: missing Methods operation slots {missing}")

    if isinstance(slots, dict):
        for name in methods_slots():
            if name not in slots:
                continue
            state = slot_state(slots[name])
            if state not in EXTRACTION_STATES:
                errors.append(
                    f"{rid}: Methods operation slot {name} state must be one of {EXTRACTION_STATES}"
                )
    return errors


_METHODS_SECTION_FIELDS = (
    "section",
    "section_name",
    "section_label",
    "source_section",
    "span_type",
    "unit_kind",
    "heading",
)
_METHODS_SECTION_LABELS = (
    "methods",
    "materials and methods",
)
_MANIFEST_MARKER_FIELDS = (
    "selection_type",
    "selection_kind",
    "manifest_type",
    "manifest_kind",
    "purpose",
    "type",
)
_MANIFEST_CONTEXTS = {"reagents", "equipment", "software"}
_MANIFEST_CONTEXT_ALIASES = {"reagent": "reagents"}
_MANIFEST_FIELDS = ("methods_span_manifest", "manifest", "span_map", "mappings")


def _normalize_manifest_context(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.casefold()
    if normalized in _MANIFEST_CONTEXTS:
        return normalized
    return _MANIFEST_CONTEXT_ALIASES.get(normalized)


def _is_methods_section_label(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = " ".join(value.casefold().replace("&", "and").split())
    return normalized.strip(" .,;:").startswith(_METHODS_SECTION_LABELS)


def _is_methods_span(rec: dict[str, Any]) -> bool:
    if rec.get("kind") != "span":
        return False
    if rec.get("is_methods_span") is True or rec.get("methods_span") is True:
        return True
    values: list[Any] = [rec.get(field) for field in _METHODS_SECTION_FIELDS]
    context = rec.get("context")
    if isinstance(context, dict):
        values.extend(context.get(field) for field in _METHODS_SECTION_FIELDS)
    return any(_is_methods_section_label(value) for value in values)


def _is_methods_span_manifest(rec: dict[str, Any]) -> bool:
    if rec.get("kind") != "selection":
        return False
    if "methods_span_manifest" in rec:
        return True
    return any(rec.get(field) == "methods_span_manifest" for field in _MANIFEST_MARKER_FIELDS)


def _manifest_entries(rec: dict[str, Any]) -> list[Any]:
    value = next((rec[field] for field in _MANIFEST_FIELDS if field in rec), None)
    if isinstance(value, dict):
        if isinstance(value.get("entries"), list):
            return value["entries"]
        # A mapping keyed by span id is a compact equivalent of an entries list.
        return [
            {
                "span_id": span_id,
                **(
                    target
                    if isinstance(target, dict)
                    else {"mapped_to": target}
                ),
            }
            for span_id, target in value.items()
        ]
    return value if isinstance(value, list) else []


def _manifest_mapping(entry: Any) -> tuple[str | None, str | None, str | None]:
    if not isinstance(entry, dict):
        return None, None, None
    raw_span_id = entry.get("span_id", entry.get("source_span_id"))
    span_id = raw_span_id if isinstance(raw_span_id, str) and raw_span_id else None
    nested = entry.get("mapped_to", entry.get("mapping"))
    if isinstance(nested, dict):
        entry = {**entry, **nested}
    operation_id = next(
        (
            value
            for field in ("operation_id", "operation_ref", "operation", "target_id")
            for value in (entry.get(field),)
            if isinstance(value, str) and value
        ),
        None,
    )
    mapped_to = entry.get("mapped_to")
    mapped_context = _normalize_manifest_context(mapped_to)
    if mapped_context is not None:
        return span_id, None, mapped_context
    context = entry.get(
        "context",
        entry.get("context_type", entry.get("typed_context")),
    )
    if isinstance(context, dict):
        context = context.get("type", context.get("kind"))
    normalized_context = _normalize_manifest_context(context)
    if normalized_context is not None:
        return span_id, operation_id, normalized_context
    if operation_id is None:
        operation_id = next(
            (
                value
                for value in (mapped_to, entry.get("target"), entry.get("map_to"))
                if isinstance(value, str) and value
            ),
            None,
        )
    return span_id, operation_id, None


def methods_span_ids(records: list[dict[str, Any]]) -> set[str]:
    """Return record IDs classified as Methods spans by admission validation."""
    return {
        rec["record_id"]
        for rec in records
        if rec.get("record_id") and _is_methods_span(rec)
    }


def _methods_span_manifest_errors(
    records: list[dict[str, Any]], index: dict[str, dict[str, Any]]
) -> list[str]:
    errors: list[str] = []
    methods_span_set = methods_span_ids(records)
    methods_spans = {
        rec["record_id"]: rec
        for rec in records
        if rec.get("record_id") in methods_span_set
    }
    manifests = [rec for rec in records if _is_methods_span_manifest(rec)]
    covered: set[str] = set()

    if methods_spans and not manifests:
        errors.append("methods_span_manifest required for every Methods span")
        return errors

    for manifest in manifests:
        rid = manifest.get("record_id", "<no-id>")
        if manifest.get("status") != "selected":
            errors.append(f"{rid}: methods_span_manifest must have status=selected")
        entries = _manifest_entries(manifest)
        if not entries:
            errors.append(f"{rid}: methods_span_manifest must list span mappings")
        for entry in entries:
            span_id, operation_id, context = _manifest_mapping(entry)
            if not span_id:
                errors.append(f"{rid}: methods_span_manifest entry requires span_id")
                continue
            span = index.get(span_id)
            if span is None:
                errors.append(f"{rid}: methods_span_manifest dangling span {span_id}")
            elif span.get("kind") != "span":
                errors.append(f"{rid}: methods_span_manifest target {span_id} is not a span")
            elif not _is_methods_span(span):
                errors.append(f"{rid}: manifest span {span_id} is not a Methods span")
            else:
                covered.add(span_id)

            if context is None and not operation_id:
                errors.append(
                    f"{rid}: manifest span {span_id} requires operation_id or context"
                )
            if context is not None:
                continue
            operation = index.get(operation_id or "")
            if operation is None:
                errors.append(f"{rid}: manifest operation {operation_id} is dangling")
            elif not (
                operation.get("kind") == "proposition"
                and operation.get("sort") == "method_operation"
            ):
                errors.append(
                    f"{rid}: manifest operation {operation_id} must be sort=method_operation"
                )

    for span_id in sorted(set(methods_spans) - covered):
        errors.append(f"methods_span_manifest uncovered Methods span {span_id}")
    return errors


def validate_batch(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    corpora = {r.get("corpus_id") for r in records if r.get("corpus_id")}
    if len(corpora) > 1:
        errors.append(f"cross-corpus batch: {sorted(corpora)}")
        return errors
    ids = [r.get("record_id") for r in records]
    if len(ids) != len(set(ids)):
        errors.append("duplicate record_id")
    index = {r["record_id"]: r for r in records if "record_id" in r}
    for r in records:
        errors.extend(validate_record(r, index))
        if r.get("kind") == "proposition" and r.get("sort") == "figure_panel":
            errors.extend(_panel_slot_errors(r))
        if r.get("kind") == "proposition" and r.get("sort") == "method_operation":
            errors.extend(_methods_operation_slot_errors(r))
    errors.extend(_methods_span_manifest_errors(records, index))
    return errors
