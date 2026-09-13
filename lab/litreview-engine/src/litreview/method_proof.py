"""Claim closure and readiness summaries for method-proof records."""

from __future__ import annotations

from typing import Any

from litreview.revisions import revision_matches as _revision_matches


def _index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["record_id"]: record for record in records if record.get("record_id")}


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _is_inspectable_span(record: dict[str, Any] | None) -> bool:
    return bool(
        record
        and record.get("kind") == "span"
        and record.get("access") in {"oa", "inbox"}
        and str(record.get("locator") or "").strip()
    )


def closure(records: list[dict], claim_id: str, *, hop_limit: int = 8) -> dict:
    """Walk a claim's required method-proof branches to A, B, or C stops."""
    by_id = _index(records)
    report: dict[str, Any] = {
        "claim_id": claim_id,
        "closed": False,
        "empirically_ready": False,
        "routes": [],
        "stops": [],
        "cycles": [],
        "axioms": [],
        "gaps": [],
    }
    stop_keys: set[tuple[Any, ...]] = set()
    route_keys: set[tuple[str, ...]] = set()
    cycle_keys: set[tuple[str, ...]] = set()

    def add_route(route: list[str]) -> None:
        key = tuple(route)
        if key not in route_keys:
            route_keys.add(key)
            report["routes"].append(list(route))

    def add_stop(
        branch: str,
        kind: str,
        record_id: str,
        route: list[str],
        gap_type: str | None = None,
    ) -> None:
        key = (branch, kind, record_id, gap_type)
        if key in stop_keys:
            return
        stop_keys.add(key)
        stop: dict[str, Any] = {"branch": branch, "kind": kind, "record_id": record_id}
        if gap_type is not None:
            stop["gap_type"] = gap_type
        report["stops"].append(stop)
        add_route(route if route and route[-1] == record_id else route + [record_id])
        if kind == "axiom":
            report["axioms"] = _unique([*report["axioms"], record_id])
        if kind == "gap":
            report["gaps"] = _unique([*report["gaps"], record_id])

    def add_gap(branch: str, record_id: str, route: list[str], gap_type: str) -> None:
        add_stop(branch, "gap", record_id, route, gap_type)

    def walk(node_id: str, route: list[str], depth: int, stack: list[str]) -> bool:
        if node_id in stack:
            cycle = stack[stack.index(node_id) :] + [node_id]
            cycle_key = tuple(cycle)
            if cycle_key not in cycle_keys:
                cycle_keys.add(cycle_key)
                report["cycles"].append(cycle)
            add_gap(node_id, node_id, route, "cycle")
            return False

        node = by_id.get(node_id)
        if node is None:
            add_gap(node_id, node_id, route, "unresolved_id")
            return False
        if node.get("kind") != "proposition" or node.get("sort") != "method_claim":
            add_gap(node_id, node_id, route, "unresolved_id")
            return False

        current_route = route + [node_id]
        next_stack = stack + [node_id]
        branch_had_stop = False
        branch_blocked = False

        # Explicit residual assessments are blocking C stops for this claim.
        claim_gaps = [
            record
            for record in by_id.values()
            if record.get("kind") == "evidence_assessment"
            and record.get("target_id") == node_id
            and record.get("gap_type")
        ]
        for gap in claim_gaps:
            branch_had_stop = True
            branch_blocked = True
            add_gap(node_id, gap["record_id"], current_route, str(gap["gap_type"]))

        # An accepted, inspectable justified_by edge is a founding boundary.
        founding_links = [
            record
            for record in by_id.values()
            if record.get("kind") == "evidence_link"
            and record.get("link_kind") == "justified_by"
            and record.get("claim_ref") == node_id
            and record.get("review_state") == "accepted"
            and record.get("admission") != "stale"
            and _is_inspectable_span(by_id.get(record.get("span_id", "")))
        ]
        for link in founding_links:
            branch_had_stop = True
            add_stop(node_id, "founding", link["record_id"], current_route)

        # A founding link discharges its own reviewed argument boundary.  Its
        # argument is provenance for that boundary, but any other derivation
        # remains a required branch and must still be walked.
        founding_argument_ids = {
            link.get("argument_ref") for link in founding_links if link.get("argument_ref")
        }

        # A zero budget may inspect a stop already attached to this claim, but
        # cannot spend a hop looking for a derivation or premise.
        if depth >= hop_limit and not branch_had_stop:
            branch_blocked = True
            add_gap(node_id, node_id, current_route, "hop_budget")
            return False

        derivations = [
            record
            for record in by_id.values()
            if record.get("kind") == "derivation"
            and record.get("conclusion_id") == node_id
            and record.get("record_id") not in founding_argument_ids
        ]
        if derivations:
            for derivation in derivations:
                premises = derivation.get("premise_ids") or []
                if not premises:
                    branch_blocked = True
                    add_gap(node_id, derivation["record_id"], current_route, "missing_bridge")
                    continue
                derivation_closed = True
                for premise_id in premises:
                    premise = by_id.get(premise_id)
                    if premise is None or premise.get("kind") != "premise":
                        derivation_closed = False
                        branch_blocked = True
                        add_gap(node_id, premise_id, current_route, "unresolved_id")
                        continue
                    premise_route = current_route + [derivation["record_id"], premise_id]
                    if premise.get("origin") == "axiom":
                        if premise.get("admission") == "admitted":
                            branch_had_stop = True
                            add_stop(node_id, "axiom", premise_id, premise_route)
                        else:
                            derivation_closed = False
                            branch_blocked = True
                            add_gap(node_id, premise_id, premise_route, "unadmitted_axiom")
                        continue
                    proposition_id = premise.get("proposition_id")
                    if not proposition_id:
                        derivation_closed = False
                        branch_blocked = True
                        add_gap(node_id, premise_id, premise_route, "unresolved_id")
                        continue
                    child_closed = walk(
                        proposition_id,
                        premise_route,
                        depth + 1,
                        next_stack,
                    )
                    derivation_closed = derivation_closed and child_closed
                    branch_blocked = branch_blocked or not child_closed
                branch_had_stop = branch_had_stop or derivation_closed
        elif not branch_had_stop:
            branch_blocked = True
            add_gap(node_id, node_id, current_route, "missing_validation")

        # No required branch may be hidden by a direct foundation.
        return branch_had_stop and not branch_blocked

    walk(claim_id, [], 0, [])
    report["closed"] = bool(
        report["stops"]
        and not report["gaps"]
        and not report["cycles"]
        and all(stop.get("kind") in {"founding", "axiom"} for stop in report["stops"])
    )
    report["empirically_ready"] = bool(
        report["closed"]
        and any(
            stop.get("kind") == "founding"
            and _is_current_founding_link(by_id.get(stop.get("record_id")), by_id, claim_id)
            for stop in report["stops"]
        )
    )
    return report


def _is_current_founding_link(
    link: dict[str, Any] | None,
    by_id: dict[str, dict[str, Any]],
    claim_id: str,
) -> bool:
    """Check the full scoped revision binding for empirical readiness."""
    if (
        link is None
        or link.get("kind") != "evidence_link"
        or link.get("link_kind") != "justified_by"
        or link.get("claim_ref") != claim_id
        or link.get("review_state") != "accepted"
        or link.get("admission") == "stale"
    ):
        return False
    if not _is_inspectable_span(by_id.get(link.get("span_id", ""))):
        return False

    method = by_id.get(link.get("src_id", ""))
    claim = by_id.get(link.get("claim_ref", ""))
    result = by_id.get(link.get("dst_id", ""))
    argument = by_id.get(link.get("argument_ref", ""))
    if method is None or claim is None or result is None or argument is None:
        return False
    if method.get("kind") != "proposition" or method.get("sort") != "method":
        return False
    if claim.get("kind") != "proposition" or claim.get("sort") != "method_claim":
        return False
    if result.get("kind") != "proposition" or result.get("sort") != "result":
        return False
    if argument.get("kind") != "derivation" or argument.get("sort") != "method_argument":
        return False
    if not (
        claim.get("method_id") == method.get("record_id")
        or claim.get("claim_about") == method.get("record_id")
    ):
        return False
    if not _revision_matches(claim.get("method_revision"), method.get("revision")):
        return False
    if argument.get("conclusion_id") != claim.get("record_id"):
        return False
    if not any(
        by_id.get(premise_id, {}).get("kind") == "premise"
        and by_id.get(premise_id, {}).get("proposition_id") == result.get("record_id")
        for premise_id in (argument.get("premise_ids") or [])
    ):
        return False
    if argument.get("argument_kind") != "empirical":
        return False

    claim_revision = claim.get("revision", 1)
    argument_revision = argument.get("argument_revision", 1)
    return (
        _revision_matches(link.get("method_revision"), method.get("revision"))
        and _revision_matches(link.get("claim_revision"), claim_revision)
        and _revision_matches(link.get("argument_revision"), argument_revision)
    )


def _method_claim_ids(by_id: dict[str, dict[str, Any]], method_id: str) -> set[str]:
    claim_ids = {
        record["record_id"]
        for record in by_id.values()
        if record.get("kind") == "proposition"
        and record.get("sort") == "method_claim"
        and (
            record.get("method_id") == method_id
            or record.get("claim_about") == method_id
            or record.get("about_id") == method_id
        )
    }
    method = by_id.get(method_id, {})
    for claim_id in method.get("claim_refs") or []:
        if claim_id in by_id:
            claim_ids.add(claim_id)
    return claim_ids


def _has_crispr_lock_without_selection(
    records: list[dict[str, Any]], method: dict[str, Any], method_id: str
) -> bool:
    operations = method.get("operations") or []
    locked = bool(
        method.get("locked") is True
        or method.get("crispr_locked")
        or (method.get("crispr") or {}).get("locked")
    )
    for operation in operations:
        if not isinstance(operation, dict):
            continue
        kind = str(operation.get("kind") or operation.get("tool") or "").lower()
        if "crispr" in kind and operation.get("locked") is True:
            locked = True
    if not locked:
        return False
    selections = [record for record in records if record.get("kind") == "selection"]
    return not any(
        record.get("status") == "selected"
        and (
            record.get("method_id") == method_id
            or record.get("target_id") == method_id
            or record.get("method_ref") == method_id
            or record.get("option_for") == method_id
        )
        for record in selections
    )


def _ref_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item]
    return []


_RESOLVED_BRIDGE_STATES = {"resolved", "discharged", "satisfied", "verified", "accepted"}


def _is_resolved_bridge(record: dict[str, Any]) -> bool:
    state = record.get("resolution_state") or record.get("resolution_status")
    return state in _RESOLVED_BRIDGE_STATES


def _bridge_subject_refs(
    bridge: dict[str, Any], by_id: dict[str, dict[str, Any]]
) -> set[str]:
    refs: set[str] = set()
    for field in (
        "target_id",
        "assumption_ref",
        "subject_ref",
        "affected_subject",
        "affected_subject_id",
        "revision_ref",
        "revision_id",
        "procedure_ref",
        "procedure_id",
        "sop_ref",
        "sop_id",
    ):
        refs.update(_ref_values(bridge.get(field)))
    for field in ("subject_refs", "affected_subject_refs", "affected_subjects"):
        refs.update(_ref_values(bridge.get(field)))
    assumption = by_id.get(bridge.get("assumption_ref", ""))
    if assumption is not None:
        refs.update(_ref_values(assumption.get("subject_refs")))
    return refs


def _method_related_ids(
    by_id: dict[str, dict[str, Any]],
    method_id: str,
    claim_ids: set[str],
    method: dict[str, Any],
) -> set[str]:
    """Collect method-linked claims, results, operations, revisions, and SOPs."""
    relevant_ids = {method_id, *claim_ids}

    for field in (
        "result_refs",
        "operation_refs",
        "method_operation_refs",
        "revision_refs",
        "procedure_refs",
        "sop_refs",
    ):
        relevant_ids.update(_ref_values(method.get(field)))
    for operation in method.get("operations") or []:
        if isinstance(operation, str):
            relevant_ids.add(operation)
        elif isinstance(operation, dict):
            for field in ("record_id", "id", "operation_id", "operation_ref"):
                relevant_ids.update(_ref_values(operation.get(field)))

    association_fields = (
        "method_id",
        "method_ref",
        "operationalizes_id",
        "operationalizes",
        "revision_id",
        "revision_ref",
        "procedure_id",
        "procedure_ref",
        "sop_id",
        "sop_ref",
        "claim_about",
        "about_id",
        "about_ref",
        "subject_id",
        "subject_ref",
    )
    changed = True
    while changed:
        changed = False
        for record in by_id.values():
            record_id = record.get("record_id")
            if not isinstance(record_id, str) or record_id in relevant_ids:
                continue
            refs = {
                ref
                for field in association_fields
                for ref in _ref_values(record.get(field))
            }
            args = set(_ref_values(record.get("args")))
            if refs.intersection(relevant_ids) or args.intersection(relevant_ids):
                relevant_ids.add(record_id)
                changed = True

        for link in by_id.values():
            if link.get("kind") != "evidence_link":
                continue
            endpoints = {
                ref
                for field in ("src_id", "dst_id", "claim_ref", "argument_ref")
                for ref in _ref_values(link.get(field))
            }
            if not endpoints.intersection(relevant_ids):
                continue
            for ref in endpoints:
                if ref in by_id and ref not in relevant_ids:
                    relevant_ids.add(ref)
                    changed = True

        for derivation in by_id.values():
            if derivation.get("kind") != "derivation":
                continue
            if derivation.get("conclusion_id") not in relevant_ids:
                continue
            for ref in _ref_values(derivation.get("premise_ids")):
                if ref in by_id and ref not in relevant_ids:
                    relevant_ids.add(ref)
                    changed = True
                premise = by_id.get(ref)
                if premise is not None:
                    proposition_id = premise.get("proposition_id")
                    if proposition_id in by_id and proposition_id not in relevant_ids:
                        relevant_ids.add(proposition_id)
                        changed = True

    return relevant_ids


def _has_unresolved_required_bridge(
    records: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
    method_id: str,
    claim_ids: set[str],
    method: dict[str, Any],
) -> bool:
    relevant_ids = _method_related_ids(by_id, method_id, claim_ids, method)
    relevant_ids.update(
        value
        for field in ("gap_refs", "bridge_requirement_refs", "generalization_assumption_refs")
        for value in _ref_values(method.get(field))
    )
    explicit_assumption_ids = {
        value
        for value in _ref_values(method.get("generalization_assumption_refs"))
        if (
            by_id.get(value, {}).get("kind") == "premise"
            and by_id.get(value, {}).get("origin") == "assumption"
        )
    }
    relevant_assumptions = explicit_assumption_ids | {
        record.get("record_id")
        for record in by_id.values()
        if record.get("kind") == "premise"
        and record.get("origin") == "assumption"
        and isinstance(record.get("record_id"), str)
        and relevant_ids.intersection(_ref_values(record.get("subject_refs")))
    }
    explicit_bridge_ids = set(_ref_values(method.get("bridge_requirement_refs")))
    for assumption_id in relevant_assumptions:
        if not isinstance(assumption_id, str):
            continue
        assumption = by_id.get(assumption_id, {})
        explicit_bridge_ids.update(_ref_values(assumption.get("bridge_requirement_refs")))

    for bridge in records:
        if (
            bridge.get("kind") != "evidence_assessment"
            or bridge.get("gap_type") != "missing_bridge"
            or bridge.get("required", True) is False
            or _is_resolved_bridge(bridge)
        ):
            continue
        bridge_refs = _bridge_subject_refs(bridge, by_id)
        if (
            bridge.get("record_id") in explicit_bridge_ids
            or relevant_ids.intersection(bridge_refs)
            or relevant_assumptions.intersection(bridge_refs)
        ):
            return True
    return False


def reconstruct_status(records: list[dict], method_id: str) -> str:
    """Return designable, blocked, or eligible-for-authorized-pilot."""
    by_id = _index(records)
    method = by_id.get(method_id)
    if method is None:
        raise KeyError(method_id)
    lifecycle = method.get("lifecycle")
    if lifecycle == "superseded":
        return "blocked"

    claim_ids = _method_claim_ids(by_id, method_id)
    blocking_gap = False
    for record in by_id.values():
        if record.get("kind") != "evidence_assessment" or not record.get("gap_type"):
            continue
        target_id = record.get("target_id")
        if (
            target_id in claim_ids
            and record.get("verdict") == "unsupported"
            and not (
                record.get("gap_type") == "missing_bridge"
                and _is_resolved_bridge(record)
            )
        ):
            blocking_gap = True
            break

    if not blocking_gap:
        gap_refs = set(method.get("gap_refs") or [])
        required_ops = [
            operation
            for operation in method.get("operations") or []
            if isinstance(operation, dict) and operation.get("required", True)
        ]
        required_op_ids = {
            operation.get("record_id") or operation.get("id")
            for operation in required_ops
        }
        for record in by_id.values():
            if record.get("kind") != "evidence_assessment" or not record.get("gap_type"):
                continue
            if record.get("record_id") in gap_refs:
                if record.get("gap_type") == "missing_bridge" and _is_resolved_bridge(record):
                    continue
                blocking_gap = True
                break
            if record.get("target_id") in required_op_ids and record.get("verdict") == "unsupported":
                if record.get("gap_type") == "missing_bridge" and _is_resolved_bridge(record):
                    continue
                blocking_gap = True
                break

    if _has_unresolved_required_bridge(records, by_id, method_id, claim_ids, method):
        blocking_gap = True
    if _has_crispr_lock_without_selection(records, method, method_id):
        blocking_gap = True
    if blocking_gap:
        return "blocked"
    if lifecycle == "authorized-for-pilot":
        return "eligible-for-authorized-pilot"
    if lifecycle in {"proposed", "selected-for-planning"}:
        return "designable"
    return "blocked"


def _procedure_method_id(procedure: dict[str, Any]) -> str | None:
    for field in ("operationalizes_id", "operationalizes", "method_id"):
        value = procedure.get(field)
        if isinstance(value, str):
            return value
    return None


def sop_readiness(records: list[dict], procedure_id: str) -> str:
    """Return draft, execution-ready, authorized-pilot, or stale."""
    by_id = _index(records)
    procedure = by_id.get(procedure_id)
    if procedure is None:
        raise KeyError(procedure_id)
    method_id = _procedure_method_id(procedure)
    method = by_id.get(method_id) if method_id else None
    if method is None:
        return "stale"

    # A procedure may pin an earlier stable method id while replay exposes a
    # replacement record through supersedes.  Read the current revision before
    # comparing the procedure's pin.
    current_method = method
    seen_method_ids = {method.get("record_id")}
    while current_method is not None:
        replacement = next(
            (
                record
                for record in records
                if record.get("supersedes") == current_method.get("record_id")
                and record.get("record_id") not in seen_method_ids
            ),
            None,
        )
        if replacement is None:
            break
        current_method = replacement
        seen_method_ids.add(current_method.get("record_id"))
    method = current_method

    procedure_revision = procedure.get("operationalizes_revision")
    if procedure_revision in (None, ""):
        procedure_revision = procedure.get("method_revision")
    if method.get("revision") in (None, "") or procedure_revision in (None, ""):
        return "stale"
    if not _revision_matches(procedure_revision, method.get("revision")):
        return "stale"

    critical_params = procedure.get("critical_params") or []
    if any(
        not isinstance(param, dict) or param.get("bound") in (None, "missing")
        for param in critical_params
    ):
        return "draft"
    if method.get("lifecycle") == "authorized-for-pilot":
        return "authorized-pilot"
    return "execution-ready"
