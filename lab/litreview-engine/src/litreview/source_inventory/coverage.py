"""Completeness gates A / S / D over an inventory bundle."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from litreview.source_inventory.ids import sha256_file
from litreview.source_inventory.load import BUNDLE_FILES, SCHEMA, load_bundle
from litreview.source_inventory.validate import validate_inventory


def coverage_report(
    bundle_dir: str | Path,
    ledger_path: str | Path | None = None,
    allow_fixture_qa: bool = False,
) -> dict[str, Any]:
    root = Path(bundle_dir)
    validation = validate_inventory(root, ledger_path=ledger_path, allow_fixture_qa=allow_fixture_qa)
    codes = {e["code"] for e in validation["errors"]}
    bundle = load_bundle(root) if validation["valid"] or (root / "source_manifest.jsonl").is_file() else {}

    blockers_a: list[str] = []
    blockers_s: list[str] = []
    blockers_d: list[str] = []

    v = validation["valid"]
    if not v:
        blockers_a.extend(sorted(codes))
        if "MISSING_PAGE" in codes:
            blockers_a.append("MISSING_PAGE")
        if "EMPTY_PARSE" in codes:
            blockers_a.append("EMPTY_PARSE")

    a = v and not blockers_a
    # extra A checks if valid
    if v:
        manifests = [r for _, r in bundle["source_manifest.jsonl"]]
        if not manifests:
            a = False
            blockers_a.append("EMPTY_MANIFEST")
        if "MISSING_PAGE" in codes or "EMPTY_PARSE" in codes:
            a = False

    s = a
    if a:
        for _, d in bundle["dispositions.jsonl"]:
            if d.get("scope") == "unresolved" or d.get("disposition") == "pending":
                s = False
                blockers_s.append("PENDING")
                break

    d = s
    if s:
        units = {u["unit_id"]: u for _, u in bundle["units.jsonl"]}
        disps = list(bundle["dispositions.jsonl"])
        included_units = [
            d for _, d in disps if d.get("target_kind") == "unit" and d.get("scope") == "include"
        ]
        if not included_units:
            d = False
            blockers_d.append("NO_INCLUDED_UNIT")
        for _, drow in disps:
            if drow.get("target_kind") != "unit" or drow.get("scope") != "include":
                continue
            u = units.get(drow["target_id"])
            if drow.get("disposition") == "unreadable" or (u and u.get("readability") == "unreadable"):
                d = False
                blockers_d.append("UNREADABLE_UNIT")
            if drow.get("disposition") == "mapped":
                links = [x for _, x in bundle["span_links.jsonl"] if x.get("unit_id") == drow["target_id"]]
                if not links:
                    d = False
                    blockers_d.append("UNREADABLE_UNIT")
        if not ledger_path:
            d = False
            blockers_d.append("NO_LEDGER")
        else:
            from litreview.source_inventory.ids import sha256_file as _h
            import json as _json
            raw = Path(ledger_path).read_text().splitlines()
            span_lines = set()
            for i, line in enumerate(raw, 1):
                if not line.strip():
                    continue
                rec = _json.loads(line)
                if rec.get("kind") == "span":
                    span_lines.add(i)
            linked = {x.get("span_line") for _, x in bundle["span_links.jsonl"]}
            if span_lines - linked:
                d = False
                blockers_d.append("UNMAPPED_SPAN")
            mapped = {
                dr["target_id"]
                for _, dr in disps
                if dr.get("disposition") == "mapped"
            }
            have = {x.get("unit_id") for _, x in bundle["span_links.jsonl"]}
            if mapped - have:
                d = False
                blockers_d.append("UNREADABLE_UNIT")
        if not allow_fixture_qa:
            for _, qa in bundle["source_qa.jsonl"]:
                if qa.get("method") == "fixture":
                    d = False
                    blockers_d.append("FIXTURE_QA")
        # included sources must be local
        srcs = {r["source_id"]: r for _, r in bundle["source_manifest.jsonl"]}
        for _, drow in disps:
            if drow.get("target_kind") == "source" and drow.get("scope") == "include":
                src = srcs.get(drow["target_id"])
                if src and src.get("intake_state") != "local":
                    d = False
                    blockers_d.append("NONLOCAL_INCLUDED")

    if not a:
        s = False
        d = False
        if not blockers_s:
            blockers_s = list(blockers_a)
        if not blockers_d:
            blockers_d = list(blockers_a)
    elif not s:
        d = False
        if not blockers_d:
            blockers_d = list(blockers_s)

    def gate(ok: bool, blockers: list[str]) -> dict[str, Any]:
        uniq = sorted(set(blockers))
        return {"pass": ok, "blockers": uniq}

    digests = {}
    for n in BUNDLE_FILES:
        p = root / n
        if p.is_file():
            digests[n] = sha256_file(p)

    policy_id = None
    pol = bundle.get("scope_policy.jsonl") or []
    if pol:
        policy_id = pol[0][1].get("policy_id")

    return {
        "schema_version": SCHEMA,
        "validation": validation,
        "gates": {
            "accounting_complete": gate(a, blockers_a),
            "scope_resolved": gate(s, blockers_s),
            "data_test_ready": gate(d, blockers_d),
        },
        "input_digests": digests,
        "scope_policy_id": policy_id,
    }
