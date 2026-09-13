"""CLI: validate JSONL, walk a chain, init an instance."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

from litreview import ENGINE_VERSION, EXTRACTION_STATES, SCHEMA_V1
from litreview.chain import chain
from litreview.method_proof import closure, reconstruct_status, sop_readiness
from litreview.paper_decomposition import panel_slots, slot_state
from litreview.source_inventory.cli import run_coverage, run_validate
from litreview.validate import methods_span_ids, validate_batch


def _load_jsonl(path: Path) -> list[dict]:
    recs = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        recs.append(json.loads(line))
    return recs


def cmd_paper_admit(args: argparse.Namespace) -> int:
    recs = _load_jsonl(Path(args.jsonl))
    errors = validate_batch(recs)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    counts = Counter(rec.get("sort") for rec in recs if rec.get("sort"))
    print(f"admitted {len(recs)} records")
    for sort, count in sorted(counts.items()):
        print(f"{sort}: {count}")
    return 0


def _empty_state_counts() -> dict[str, int]:
    return {state: 0 for state in EXTRACTION_STATES}


def _count_state(counts: dict[str, int], state: object) -> None:
    # Missing extraction state is an unresolved recipe item, not stated content.
    normalized = state if isinstance(state, str) else "pending"
    if normalized not in counts:
        normalized = "pending"
    counts[normalized] += 1


def paper_decomposition_coverage(records: list[dict]) -> dict[str, dict[str, int]]:
    """Count panel recipe slots and Methods spans by extraction state."""
    panel_counts = _empty_state_counts()
    for rec in records:
        if rec.get("kind") != "proposition" or rec.get("sort") != "figure_panel":
            continue
        slots = rec.get("slots")
        if not isinstance(slots, dict):
            for _ in panel_slots():
                _count_state(panel_counts, "pending")
            continue
        for name in panel_slots():
            if name in slots:
                _count_state(panel_counts, slot_state(slots[name]))
            else:
                _count_state(panel_counts, "pending")

    methods_counts = _empty_state_counts()
    methods_ids = methods_span_ids(records)
    for rec in records:
        if rec.get("record_id") not in methods_ids:
            continue
        state = rec.get("extraction_state", rec.get("state"))
        _count_state(methods_counts, state)

    return {"panel_slots": panel_counts, "methods_spans": methods_counts}


def cmd_validate(args: argparse.Namespace) -> int:
    recs = _load_jsonl(Path(args.jsonl))
    errors = validate_batch(recs)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    print(f"admitted {len(recs)} records")
    return 0


def cmd_chain(args: argparse.Namespace) -> int:
    recs = _load_jsonl(Path(args.jsonl))
    errors = validate_batch(recs)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    print("\n".join(chain(recs, args.start)))
    return 0


def cmd_method_proof_closure(args: argparse.Namespace) -> int:
    recs = _load_jsonl(Path(args.jsonl))
    errors = validate_batch(recs)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    report = closure(recs, args.claim, hop_limit=args.hop_limit)
    print(json.dumps(report, sort_keys=True))
    return 0


def cmd_method_proof_reconstruct(args: argparse.Namespace) -> int:
    recs = _load_jsonl(Path(args.jsonl))
    errors = validate_batch(recs)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(reconstruct_status(recs, args.method))
    return 0


def cmd_method_proof_sop(args: argparse.Namespace) -> int:
    recs = _load_jsonl(Path(args.jsonl))
    errors = validate_batch(recs)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(sop_readiness(recs, args.procedure))
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    engine = Path(__file__).resolve().parents[2]
    template = engine / "instances" / "template"
    dest = Path(args.dest).resolve()
    if dest.exists() and any(dest.iterdir()) and not args.force:
        print(f"{dest} is not empty (pass --force)", file=sys.stderr)
        return 1
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(template / "instance.yaml", dest / "instance.yaml")
    text = (dest / "instance.yaml").read_text().replace("corpus_id: example", f"corpus_id: {args.id}")
    if "engine_version:" not in text:
        text += f"\nengine_version: {ENGINE_VERSION}\nschema_version: {SCHEMA_V1}\n"
    (dest / "instance.yaml").write_text(text)
    (dest / "data").mkdir(exist_ok=True)
    (dest / "data" / "logic.jsonl").write_text("")
    (dest / "data" / "seed-pmids.txt").write_text("# empty until you add OA PMIDs\n")
    print(f"instance {args.id} at {dest}")
    return 0


def cmd_extract_pdf(args: argparse.Namespace) -> int:
    from litreview.extract import extract_pdf

    out = extract_pdf(args.pdf)
    text = json.dumps({"n_pages": out["n_pages"], "n_sentences": len(out["sentences"]), "sha256": out["sha256"], "title": out["title"]}, sort_keys=True)
    if args.out:
        Path(args.out).write_text(json.dumps(out))
    print(text)
    return 0


def cmd_timeline(args: argparse.Namespace) -> int:
    from litreview.timeline import timeline

    recs = _load_jsonl(Path(args.jsonl))
    for e in timeline(recs):
        print(f"{e.get('year')}\t{e.get('source_id')}\t{(e.get('text') or '')[:160]}")
    return 0


def cmd_inv_validate(args: argparse.Namespace) -> int:
    ledger = Path(args.ledger) if args.ledger else None
    code, text = run_validate(Path(args.bundle), ledger, args.allow_fixture_qa)
    print(text)
    return code


def cmd_cov_report(args: argparse.Namespace) -> int:
    bundle = Path(args.bundle) if args.bundle else None
    logic = Path(args.logic) if args.logic else None
    # Accept a logic JSONL path through --bundle for a compact decomposition-only report.
    if bundle is not None and bundle.is_file() and logic is None:
        logic = bundle
        bundle = None

    if bundle is None and logic is None:
        print("coverage report requires --bundle or --logic", file=sys.stderr)
        return 2

    if bundle is not None:
        ledger = Path(args.ledger) if args.ledger else None
        code, text = run_coverage(bundle, ledger, args.allow_fixture_qa, args.require)
        report = json.loads(text)
    else:
        code = 0
        report = {"validation": {"valid": True, "errors": []}}

    if logic is not None:
        records = _load_jsonl(logic)
        errors = validate_batch(records)
        report["paper_decomposition"] = paper_decomposition_coverage(records)
        report["paper_decomposition_validation"] = {
            "valid": not errors,
            "errors": errors,
        }
        if errors:
            code = 1

    print(json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return code


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="litreview")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("jsonl")
    v.set_defaults(func=cmd_validate)
    c = sub.add_parser("chain")
    c.add_argument("jsonl")
    c.add_argument("start")
    c.set_defaults(func=cmd_chain)
    i = sub.add_parser("init-instance")
    i.add_argument("--id", required=True)
    i.add_argument("--dest", required=True)
    i.add_argument("--force", action="store_true")
    i.set_defaults(func=cmd_init)
    pd = sub.add_parser("paper-decomposition")
    pd_sub = pd.add_subparsers(dest="paper_decomposition_cmd", required=True)
    pda = pd_sub.add_parser("admit")
    pda.add_argument("jsonl")
    pda.set_defaults(func=cmd_paper_admit)
    inv = sub.add_parser("inventory")
    inv_sub = inv.add_subparsers(dest="inv_cmd", required=True)
    iv = inv_sub.add_parser("validate")
    iv.add_argument("--bundle", required=True)
    iv.add_argument("--ledger")
    iv.add_argument("--allow-fixture-qa", action="store_true")
    iv.set_defaults(func=cmd_inv_validate)
    cov = sub.add_parser("coverage")
    cov_sub = cov.add_subparsers(dest="cov_cmd", required=True)
    cr = cov_sub.add_parser("report")
    cr.add_argument("--bundle")
    cr.add_argument("--logic")
    cr.add_argument("--ledger")
    cr.add_argument("--require")
    cr.add_argument("--allow-fixture-qa", action="store_true")
    cr.set_defaults(func=cmd_cov_report)
    ex = sub.add_parser("extract-pdf")
    ex.add_argument("--pdf", required=True)
    ex.add_argument("--out")
    ex.set_defaults(func=cmd_extract_pdf)
    tl = sub.add_parser("timeline")
    tl.add_argument("jsonl")
    tl.set_defaults(func=cmd_timeline)
    mp = sub.add_parser("method-proof")
    mp_sub = mp.add_subparsers(dest="method_proof_cmd", required=True)
    mpc = mp_sub.add_parser("closure")
    mpc.add_argument("jsonl")
    mpc.add_argument("--claim", required=True)
    mpc.add_argument("--hop-limit", type=int, default=8)
    mpc.set_defaults(func=cmd_method_proof_closure)
    mpr = mp_sub.add_parser("reconstruct-check")
    mpr.add_argument("jsonl")
    mpr.add_argument("--method", required=True)
    mpr.set_defaults(func=cmd_method_proof_reconstruct)
    mps = mp_sub.add_parser("sop-check")
    mps.add_argument("jsonl")
    mps.add_argument("--procedure", required=True)
    mps.set_defaults(func=cmd_method_proof_sop)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
