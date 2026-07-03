"""
engine/tracking/evidence_update.py
==================================
Curator CLI for the biomarker evidence registry (``data/biomarker_evidence.json``).

This is the *update mechanism* for the Bayesian response model: when new
research lands, a curator records the citation(s) and the documented effect
magnitude here, and the prior layer (``genetics.derive_prior`` via
``evidence.relative_sd_for``) immediately reflects the new evidence grade —
no code change, no redeploy of the engine logic.

Curator-in-the-loop, by design
-------------------------------
This tool does **not** mine the literature autonomously. The honesty
contract for this project is "never fabricate provenance," so effect sizes
and citations are entered by a human who has actually read (or, via the
scite literature tools, retrieved and confirmed) the paper. A typical loop:

    1. Discover candidate papers (e.g. the scite `search_literature` tools,
       or PubMed) for a peptide -> biomarker effect.
    2. Confirm the DOI, design, and direction by reading the paper.
    3. Record it here::

         python -m engine.tracking.evidence_update set "Serum IGF-1" \
             --max-pct-change 0.55 --grade B \
             --citation doi=10.1056/nejmoa072375 \
                        title="Metabolic Effects of a GRF in HIV" \
                        authors="Falutz et al." year=2007 \
                        journal="NEJM" design=RCT evidence=human \
             --peptides Tesamorelin CJC-1295 \
             --rationale "GH secretagogues raise IGF-1 in human RCTs."

Subcommands
-----------
    list                 Show panel coverage: which markers are cited vs not.
    show   <biomarker>   Print the full evidence entry (with citation links).
    set    <biomarker>   Add or replace an entry (one or more --citation).
    remove <biomarker>   Delete an entry (reverts the marker to uncited).
    validate             Load + validate the whole registry; non-zero exit on error.

Only the registry JSON is touched; ``--out`` overrides the path (tests use a
tmp file). Entries are written with sorted keys and a stamped
``last_reviewed`` so diffs are clean and review dates are auditable.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .evidence import _DEFAULT_PATH, _VALID_GRADES, load_evidence, reset_cache


def _load_doc(path: Path) -> dict[str, Any]:
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {
        "schema_version": 1,
        "description": "Research-backed evidence registry for peptide -> "
                       "biomarker response magnitudes.",
        "grade_default_relative_sd": {"A": 0.10, "B": 0.15, "C": 0.22, "D": 0.30},
        "uncited_relative_sd": 0.20,
        "entries": {},
    }


def _write_doc(path: Path, doc: dict[str, Any]) -> None:
    # Sort entries by biomarker name for stable diffs; keep citations in
    # the order the curator supplied them (chronology is meaningful).
    doc["entries"] = dict(sorted(doc.get("entries", {}).items()))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _parse_kv(tokens: list[str]) -> dict[str, str]:
    """Parse ``key=value`` tokens (value may contain spaces if quoted by the
    shell). Used for --citation field groups."""
    out: dict[str, str] = {}
    for tok in tokens:
        if "=" not in tok:
            raise SystemExit(f"expected key=value, got {tok!r}")
        k, _, v = tok.partition("=")
        out[k.strip()] = v.strip()
    return out


# ── Subcommands ─────────────────────────────────────────────────────────────

def cmd_list(args: argparse.Namespace) -> int:
    from .biomarker_params import BIOMARKER_PARAMS
    reset_cache()
    ev = load_evidence(args.out)
    cited = set(ev)
    all_markers = sorted(set(BIOMARKER_PARAMS) | cited)
    n_cited = 0
    print(f"{'GRADE':6} {'BIOMARKER':45} {'rel_sd':>7}  citations / reviewed")
    print("-" * 88)
    for m in all_markers:
        e = ev.get(m)
        if e is None:
            print(f"{'—':6} {m:45} {'(0.20)':>7}  uncited")
        else:
            n_cited += 1
            n = len(e.citations)
            print(f"{e.grade:6} {m:45} {e.relative_sd:>7.2f}  "
                  f"{n} cite{'s' if n != 1 else ''} · {e.last_reviewed}")
    print("-" * 88)
    print(f"{n_cited} cited / {len(all_markers)} panel markers")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    reset_cache()
    ev = load_evidence(args.out)
    e = ev.get(args.biomarker)
    if e is None:
        print(f"{args.biomarker!r}: uncited (falls back to PANEL_REL_SD = 0.20)")
        return 1
    print(json.dumps(e.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    path = Path(args.out)
    doc = _load_doc(path)

    grade = args.grade.strip().upper()
    if grade not in _VALID_GRADES:
        raise SystemExit(f"grade must be one of {sorted(_VALID_GRADES)}")
    if not args.citation:
        raise SystemExit(
            "at least one --citation is required (honesty contract: no entry "
            "without a real, retrieved citation)"
        )

    citations = []
    for group in args.citation:
        kv = _parse_kv(group)
        if "doi" not in kv:
            raise SystemExit(f"citation missing doi=: {group}")
        citations.append({
            "doi": kv["doi"],
            "title": kv.get("title", ""),
            "authors": kv.get("authors", ""),
            "year": int(kv["year"]) if kv.get("year") else 0,
            "journal": kv.get("journal", ""),
            "design": kv.get("design", ""),
            "evidence": kv.get("evidence", ""),
        })

    entry: dict[str, Any] = {
        "max_pct_change": args.max_pct_change,
        "grade": grade,
        "peptides": args.peptides or [],
        "rationale": args.rationale or "",
        "citations": citations,
        "last_reviewed": args.reviewed,
    }
    if args.relative_sd is not None:
        entry["relative_sd"] = args.relative_sd

    doc.setdefault("entries", {})[args.biomarker] = entry
    _write_doc(path, doc)

    # Re-validate the whole registry so a bad entry fails loudly here, not
    # later inside the prior layer.
    reset_cache()
    load_evidence(path)
    print(f"wrote {args.biomarker!r} (grade {grade}, {len(citations)} citation"
          f"{'s' if len(citations) != 1 else ''}) -> {path}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    path = Path(args.out)
    doc = _load_doc(path)
    if args.biomarker not in doc.get("entries", {}):
        print(f"{args.biomarker!r}: not in registry")
        return 1
    del doc["entries"][args.biomarker]
    _write_doc(path, doc)
    print(f"removed {args.biomarker!r} (now uncited) -> {path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    reset_cache()
    try:
        ev = load_evidence(args.out)
    except Exception as exc:  # noqa: BLE001 — surface the message to the CLI
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {len(ev)} cited entr{'ies' if len(ev) != 1 else 'y'} in {args.out}")
    return 0


# ── Argument parsing ────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="evidence_update",
        description="Curate the biomarker evidence registry.",
    )
    p.add_argument("--out", default=str(_DEFAULT_PATH),
                   help="registry path (default: data/biomarker_evidence.json)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="show cited vs uncited panel coverage").set_defaults(
        func=cmd_list)

    sp = sub.add_parser("show", help="print one evidence entry")
    sp.add_argument("biomarker")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("set", help="add or replace an evidence entry")
    sp.add_argument("biomarker")
    sp.add_argument("--max-pct-change", type=float, required=True,
                    help="asymptotic fractional change (signed), e.g. 0.55")
    sp.add_argument("--grade", required=True, help="evidence grade A/B/C/D")
    sp.add_argument("--relative-sd", type=float, default=None,
                    help="override relative SD (defaults to the grade default)")
    sp.add_argument("--peptides", nargs="*", default=None,
                    help="peptides this evidence covers")
    sp.add_argument("--rationale", default=None)
    sp.add_argument("--reviewed", default=None,
                    help="ISO review date; defaults to --reviewed or today via caller")
    sp.add_argument("--citation", nargs="+", action="append", default=None,
                    metavar="key=value",
                    help="citation field group, repeatable: doi=.. title=.. "
                         "authors=.. year=.. journal=.. design=.. evidence=..")
    sp.set_defaults(func=cmd_set)

    sp = sub.add_parser("remove", help="delete an entry (revert to uncited)")
    sp.add_argument("biomarker")
    sp.set_defaults(func=cmd_remove)

    sub.add_parser("validate", help="validate the whole registry").set_defaults(
        func=cmd_validate)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # ``--reviewed`` defaults to today. We resolve it here (not in argparse)
    # so the module stays import-time pure and tests can pass it explicitly.
    if getattr(args, "cmd", None) == "set" and not args.reviewed:
        from datetime import date
        args.reviewed = date.today().isoformat()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
