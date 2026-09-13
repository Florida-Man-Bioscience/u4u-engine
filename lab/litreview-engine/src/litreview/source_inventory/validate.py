"""Deterministic inventory validation. Admission/bookkeeping only."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from litreview.source_inventory.ids import sha256_file, unit_id
from litreview.source_inventory.load import BUNDLE_FILES, SCHEMA, load_bundle, load_jsonl
from litreview.validate import validate_batch

ACCESS_LOCAL = {"open_access", "authorized_access"}
INTAKE = {"oa", "harvest_desk", "manual"}
ACCESS = {"open_access", "authorized_access", "paywalled", "unavailable", "unknown"}
ROLES = {"main", "supplement", "correction", "other"}
INTAKE_STATE = {"local", "not_acquired", "unavailable"}
PAGE_STATUS = {"parsed", "blank", "unreadable", "unavailable", "failed"}
CTX_KIND = {"page", "section", "figure", "table", "supplement"}
UNIT_KIND = {"prose", "caption", "panel", "table_cell", "footnote", "supplement"}
DISP = {"container", "mapped", "context_only", "excluded", "unreadable", "pending"}
SCOPE = {"include", "exclude", "unresolved"}
TARGET_KIND = {"source", "page", "unit"}


def _err(errors: list, code: str, file: str | None, line: int | None, target: str | None, detail: str) -> None:
    errors.append(
        {"code": code, "file": file, "line": line, "target_id": target, "detail": detail}
    )


def validate_inventory(
    bundle_dir: str | Path,
    ledger_path: str | Path | None = None,
    allow_fixture_qa: bool = False,
) -> dict[str, Any]:
    root = Path(bundle_dir)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    missing = [n for n in BUNDLE_FILES if not (root / n).is_file()]
    for n in missing:
        _err(errors, "MISSING_FILE", n, None, None, f"required file missing: {n}")
    if missing:
        return {"schema_version": SCHEMA, "valid": False, "errors": errors, "warnings": warnings}

    bundle = load_bundle(root)
    for name, rows in bundle.items():
        for line, rec in rows:
            if rec.get("schema_version") != SCHEMA:
                _err(errors, "SCHEMA", name, line, rec.get("source_id"), "schema_version")

    manifests = [r for _, r in bundle["source_manifest.jsonl"]]
    sources = {r["source_id"]: r for r in manifests if "source_id" in r}
    if len(sources) != len(manifests):
        _err(errors, "DUP_SOURCE", "source_manifest.jsonl", None, None, "duplicate source_id")

    _check_manifests(bundle["source_manifest.jsonl"], errors)
    _check_receipts(bundle, sources, errors)
    _check_contexts(bundle, sources, errors)
    _check_units(bundle, sources, errors)
    _check_policy_dispositions(bundle, sources, errors)
    _check_qa(bundle, sources, root, allow_fixture_qa, errors)
    if ledger_path:
        _check_links(bundle, sources, Path(ledger_path), errors)

    errors.sort(key=lambda e: (e["code"], e["file"] or "", e["line"] or 0, e["detail"]))
    return {"schema_version": SCHEMA, "valid": not errors, "errors": errors, "warnings": warnings}


def _check_manifests(rows: list[tuple[int, dict]], errors: list) -> None:
    ids = {r["source_id"] for _, r in rows if "source_id" in r}
    for line, r in rows:
        sid = r.get("source_id")
        ac = r.get("access_class")
        st = r.get("intake_state")
        if ac not in ACCESS:
            _err(errors, "ENUM", "source_manifest.jsonl", line, sid, "access_class")
        if st not in INTAKE_STATE:
            _err(errors, "ENUM", "source_manifest.jsonl", line, sid, "intake_state")
        if r.get("source_role") not in ROLES:
            _err(errors, "ENUM", "source_manifest.jsonl", line, sid, "source_role")
        if r.get("intake_route") not in INTAKE:
            _err(errors, "ENUM", "source_manifest.jsonl", line, sid, "intake_route")
        rel = r.get("related_source_id")
        if rel and rel not in ids:
            _err(errors, "DANGLING", "source_manifest.jsonl", line, sid, f"related_source_id {rel}")
        if r.get("source_role") == "supplement" and not rel:
            _err(errors, "RELATED", "source_manifest.jsonl", line, sid, "supplement needs related_source_id")
        pmid = r.get("pmid")
        if pmid is not None and (not isinstance(pmid, str) or not pmid.isdigit()):
            _err(errors, "PMID", "source_manifest.jsonl", line, sid, "pmid must be digit string or null")
        if st == "local":
            if ac not in ACCESS_LOCAL:
                _err(errors, "ACCESS", "source_manifest.jsonl", line, sid, "local intake needs OA or authorized_access")
            if not r.get("revision_sha256"):
                _err(errors, "REVISION", "source_manifest.jsonl", line, sid, "local source needs revision_sha256")
            pages = r.get("expected_pages")
            if not pages:
                _err(errors, "UNKNOWN_EXTENT", "source_manifest.jsonl", line, sid, "local source needs expected_pages")
        else:
            if r.get("revision_sha256") is not None:
                _err(errors, "REVISION", "source_manifest.jsonl", line, sid, "nonlocal revision_sha256 must be null")


def _check_receipts(bundle, sources, errors) -> None:
    local_pages: dict[str, set[str]] = {}
    for sid, src in sources.items():
        if src.get("intake_state") != "local":
            continue
        local_pages[sid] = {p["page_key"] for p in (src.get("expected_pages") or [])}
    seen: dict[tuple[str, str], int] = {}
    for line, r in bundle["page_receipts.jsonl"]:
        sid, pk = r.get("source_id"), r.get("page_key")
        if sid not in local_pages or pk not in local_pages.get(sid, set()):
            _err(errors, "UNDECLARED_PAGE", "page_receipts.jsonl", line, f"{sid}:{pk}", "page not in expected_pages")
        key = (sid, pk)
        if key in seen:
            _err(errors, "DUP_RECEIPT", "page_receipts.jsonl", line, f"{sid}:{pk}", "duplicate receipt")
        seen[key] = line
        st = r.get("status")
        if st not in PAGE_STATUS:
            _err(errors, "ENUM", "page_receipts.jsonl", line, f"{sid}:{pk}", "status")
        if st == "parsed" and not r.get("unit_ids"):
            _err(errors, "EMPTY_PARSE", "page_receipts.jsonl", line, f"{sid}:{pk}", "parsed page has no units")
        if st in {"blank", "unreadable", "unavailable", "failed"} and not r.get("reason"):
            _err(errors, "REASON", "page_receipts.jsonl", line, f"{sid}:{pk}", "exception needs reason")
        if st == "blank" and r.get("unit_ids"):
            _err(errors, "BLANK_UNITS", "page_receipts.jsonl", line, f"{sid}:{pk}", "blank page cannot have units")
    for sid, pages in local_pages.items():
        for pk in pages:
            if (sid, pk) not in seen:
                _err(errors, "MISSING_PAGE", "page_receipts.jsonl", None, f"{sid}:{pk}", "declared page has no receipt")


def _check_contexts(bundle, sources, errors) -> None:
    ctxs = {r["context_id"]: r for _, r in bundle["contexts.jsonl"] if "context_id" in r}
    for line, r in bundle["contexts.jsonl"]:
        cid = r.get("context_id")
        if r.get("kind") not in CTX_KIND:
            _err(errors, "ENUM", "contexts.jsonl", line, cid, "kind")
        parent = r.get("parent_context_id")
        if r.get("kind") == "page":
            if parent is not None:
                _err(errors, "PAGE_PARENT", "contexts.jsonl", line, cid, "page context parent must be null")
        else:
            if parent not in ctxs:
                _err(errors, "DANGLING", "contexts.jsonl", line, cid, "parent_context_id")
            elif ctxs[parent].get("source_id") != r.get("source_id"):
                _err(errors, "CROSS_SOURCE", "contexts.jsonl", line, cid, "parent different source")
            elif ctxs[parent].get("page_key") != r.get("page_key"):
                _err(errors, "CROSS_PAGE", "contexts.jsonl", line, cid, "parent different page")
        slots = r.get("slots") or []
        keys = [s.get("slot_key") for s in slots]
        if len(keys) != len(set(keys)):
            _err(errors, "DUP_SLOT", "contexts.jsonl", line, cid, "duplicate slot_key")
        for s in slots:
            if s.get("unit_kind") not in UNIT_KIND:
                _err(errors, "ENUM", "contexts.jsonl", line, cid, "slot unit_kind")
    # one root page context per local page
    receipts = {(r["source_id"], r["page_key"]) for _, r in bundle["page_receipts.jsonl"]}
    roots = {(r["source_id"], r["page_key"]) for r in ctxs.values() if r.get("kind") == "page"}
    for key in receipts:
        if key not in roots:
            _err(errors, "MISSING_PAGE_CONTEXT", "contexts.jsonl", None, f"{key[0]}:{key[1]}", "no root page context")


def _check_units(bundle, sources, errors) -> None:
    ctxs = {r["context_id"]: r for _, r in bundle["contexts.jsonl"] if "context_id" in r}
    units = []
    loc_seen: set[tuple] = set()
    for line, r in bundle["units.jsonl"]:
        uid = r.get("unit_id")
        sid = r.get("source_id")
        src = sources.get(sid) or {}
        kind = r.get("kind")
        loc = r.get("locator") or {}
        parent = r.get("parent_context_id")
        if kind not in UNIT_KIND:
            _err(errors, "ENUM", "units.jsonl", line, uid, "kind")
        if parent not in ctxs:
            _err(errors, "DANGLING", "units.jsonl", line, uid, "parent_context_id")
        elif loc.get("object_key") != parent:
            _err(errors, "LOCATOR", "units.jsonl", line, uid, "object_key must equal parent_context_id")
        rev = src.get("revision_sha256") or ""
        expected = unit_id(sid, rev, kind, loc)
        if uid != expected:
            _err(errors, "UNSTABLE_ID", "units.jsonl", line, uid, f"expected {expected}")
        tup = (sid, kind, loc.get("page_key"), loc.get("object_key"), loc.get("slot_key"))
        if tup in loc_seen:
            _err(errors, "DUP_LOCATOR", "units.jsonl", line, uid, "duplicate locator")
        loc_seen.add(tup)
        if r.get("readability") == "readable":
            if not r.get("text"):
                _err(errors, "TEXT", "units.jsonl", line, uid, "readable needs nonempty text")
        elif r.get("readability") == "unreadable":
            if r.get("text") is not None:
                _err(errors, "TEXT", "units.jsonl", line, uid, "unreadable text must be null")
            if not r.get("context_reason"):
                _err(errors, "REASON", "units.jsonl", line, uid, "unreadable needs context_reason")
        if kind == "table_cell":
            if not r.get("cell"):
                _err(errors, "CELL", "units.jsonl", line, uid, "table_cell needs cell")
        elif r.get("cell") is not None:
            _err(errors, "CELL", "units.jsonl", line, uid, "cell only for table_cell")
        # slot must exist
        ctx = ctxs.get(parent) or {}
        slot_keys = {s.get("slot_key") for s in (ctx.get("slots") or [])}
        if loc.get("slot_key") not in slot_keys:
            _err(errors, "DETACHED", "units.jsonl", line, uid, "slot not declared on parent context")
        units.append(r)
    # every slot has a unit
    have = {(u.get("parent_context_id"), (u.get("locator") or {}).get("slot_key")) for u in units}
    for cid, ctx in ctxs.items():
        for s in ctx.get("slots") or []:
            if (cid, s.get("slot_key")) not in have:
                _err(errors, "EMPTY_OBJECT", "units.jsonl", None, cid, f"missing unit for slot {s.get('slot_key')}")
    # context_unit_ids resolve
    uids = {u.get("unit_id") for u in units}
    for line, r in bundle["units.jsonl"]:
        for dep in r.get("context_unit_ids") or []:
            if dep not in uids:
                _err(errors, "DANGLING", "units.jsonl", line, r.get("unit_id"), f"context_unit_ids {dep}")
        if r.get("kind") == "table_cell" and (r.get("cell") or {}).get("role") == "data":
            if r.get("context_status") == "unresolved":
                _err(errors, "MISSING_HEADER", "units.jsonl", line, r.get("unit_id"), "data cell headers unresolved")


def _check_policy_dispositions(bundle, sources, errors) -> None:
    pol_rows = bundle["scope_policy.jsonl"]
    if len(pol_rows) != 1:
        _err(errors, "POLICY", "scope_policy.jsonl", None, None, "exactly one scope_policy row")
        return
    _, pol = pol_rows[0]
    rules = {x["rule_id"]: x for x in pol.get("rules") or [] if "rule_id" in x}
    if len(rules) != len(pol.get("rules") or []):
        _err(errors, "DUP_RULE", "scope_policy.jsonl", 1, None, "duplicate rule_id")

    expected: set[tuple[str, str]] = set()
    for sid, src in sources.items():
        expected.add(("source", sid))
        if src.get("intake_state") == "local":
            for p in src.get("expected_pages") or []:
                expected.add(("page", f"{sid}:{p['page_key']}"))
    for _, u in bundle["units.jsonl"]:
        expected.add(("unit", u["unit_id"]))

    seen: set[tuple[str, str]] = set()
    for line, r in bundle["dispositions.jsonl"]:
        tk, tid = r.get("target_kind"), r.get("target_id")
        key = (tk, tid if tk != "page" else tid)
        if tk == "page":
            # target_id is page_key only per spec... "target_id is respectively source_id, page_key, or unit_id"
            # That's ambiguous with multiple sources. We'll use page_key and source_id field.
            sid = r.get("source_id")
            key = ("page", f"{sid}:{tid}")
        elif tk == "source":
            key = ("source", tid)
            r.setdefault("source_id", tid)
        else:
            key = ("unit", tid)
        if key in seen:
            _err(errors, "DUP_DISP", "dispositions.jsonl", line, tid, "duplicate target")
        seen.add(key)
        if r.get("scope") not in SCOPE:
            _err(errors, "ENUM", "dispositions.jsonl", line, tid, "scope")
        if r.get("disposition") not in DISP:
            _err(errors, "ENUM", "dispositions.jsonl", line, tid, "disposition")
        if r.get("scope") == "unresolved":
            if r.get("disposition") != "pending" or r.get("rule_id") is not None:
                _err(errors, "PENDING", "dispositions.jsonl", line, tid, "unresolved needs pending and null rule_id")
        else:
            rid = r.get("rule_id")
            if rid not in rules:
                _err(errors, "RULE", "dispositions.jsonl", line, tid, "missing rule_id")
            elif rules[rid].get("decision") != r.get("scope"):
                _err(errors, "RULE", "dispositions.jsonl", line, tid, "rule decision mismatch")
            if not r.get("decided_by"):
                _err(errors, "AUTHOR", "dispositions.jsonl", line, tid, "resolved needs decided_by")
        if r.get("scope") == "include" and tk == "unit":
            if r.get("disposition") not in {"mapped", "context_only", "unreadable", "pending"}:
                _err(errors, "DISP", "dispositions.jsonl", line, tid, "included unit disposition")
        if r.get("scope") == "exclude" and r.get("disposition") != "excluded":
            _err(errors, "DISP", "dispositions.jsonl", line, tid, "excluded target must be excluded")
        if r.get("disposition") == "mapped":
            # need span link — checked later if links present; flag if none
            pass
    for key in expected:
        if key not in seen:
            _err(errors, "MISSING_DISP", "dispositions.jsonl", None, key[1], f"missing disposition for {key[0]}")


def _check_qa(bundle, sources, root: Path, allow_fixture_qa: bool, errors) -> None:
    qa_by = {r["source_id"]: (line, r) for line, r in bundle["source_qa.jsonl"] if "source_id" in r}
    hashes = {n: sha256_file(root / n) for n in (
        "source_manifest.jsonl", "page_receipts.jsonl", "contexts.jsonl", "units.jsonl"
    )}
    for sid, src in sources.items():
        if sid not in qa_by:
            _err(errors, "MISSING_QA", "source_qa.jsonl", None, sid, "one QA row per source")
            continue
        line, qa = qa_by[sid]
        if qa.get("revision_sha256") != src.get("revision_sha256"):
            _err(errors, "STALE_QA", "source_qa.jsonl", line, sid, "revision mismatch")
        inp = qa.get("input_sha256") or {}
        for n, key in (
            ("source_manifest.jsonl", "source_manifest"),
            ("page_receipts.jsonl", "page_receipts"),
            ("contexts.jsonl", "contexts"),
            ("units.jsonl", "units"),
        ):
            if inp.get(key) != hashes.get(n):
                _err(errors, "STALE_QA", "source_qa.jsonl", line, sid, f"hash {key}")
        if qa.get("method") == "fixture" and not allow_fixture_qa:
            _err(errors, "FIXTURE_QA", "source_qa.jsonl", line, sid, "fixture QA requires --allow-fixture-qa")
        checks = qa.get("checks") or {}
        for k in ("extent", "prose", "figures", "tables", "supplements", "provenance"):
            ch = checks.get(k) or {}
            if ch.get("status") not in {"pass", "fail", "na"}:
                _err(errors, "QA_CHECK", "source_qa.jsonl", line, sid, k)
            if ch.get("status") in {"fail", "na"} and not ch.get("reason"):
                _err(errors, "QA_CHECK", "source_qa.jsonl", line, sid, f"{k} needs reason")
        for iss in qa.get("issues") or []:
            if iss.get("blocking"):
                _err(errors, "QA_BLOCKING", "source_qa.jsonl", line, sid, iss.get("detail") or "blocking issue")


def _check_links(bundle, sources, ledger: Path, errors) -> None:
    if not ledger.is_file():
        _err(errors, "LEDGER", None, None, None, "ledger missing")
        return
    digest = sha256_file(ledger)
    raw = ledger.read_text().splitlines()
    recs = []
    for i, line in enumerate(raw, 1):
        if not line.strip():
            recs.append((i, None))
            continue
        recs.append((i, __import__("json").loads(line)))
    objs = [r for _, r in recs if r]
    verr = validate_batch(objs)
    if verr:
        _err(errors, "LEDGER_INVALID", str(ledger.name), None, None, verr[0])
        return
    span_lines = {i for i, r in recs if r and r.get("kind") == "span"}
    mapped = {d["target_id"] for _, d in bundle["dispositions.jsonl"] if d.get("disposition") == "mapped"}
    units = {u["unit_id"]: u for _, u in bundle["units.jsonl"]}
    seen = set()
    for line, r in bundle["span_links.jsonl"]:
        tup = (r.get("unit_id"), r.get("ledger_sha256"), r.get("span_line"))
        if tup in seen:
            _err(errors, "DUP_LINK", "span_links.jsonl", line, r.get("unit_id"), "duplicate link")
        seen.add(tup)
        if r.get("ledger_sha256") != digest:
            _err(errors, "STALE_LEDGER", "span_links.jsonl", line, r.get("unit_id"), "ledger hash")
        sl = r.get("span_line")
        if sl not in span_lines:
            _err(errors, "NON_SPAN", "span_links.jsonl", line, r.get("unit_id"), "span_line is not a span")
            continue
        uid = r.get("unit_id")
        if uid not in mapped and uid not in units:
            _err(errors, "UNMAPPED_LINK", "span_links.jsonl", line, uid, "unknown unit")
        u = units.get(uid)
        if u:
            src = sources.get(u.get("source_id")) or {}
            span = recs[sl - 1][1]
            if src.get("pmid") != span.get("pmid"):
                _err(errors, "PMID_MISMATCH", "span_links.jsonl", line, uid, "unit pmid != span pmid")
