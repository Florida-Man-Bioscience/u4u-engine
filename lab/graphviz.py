"""Bounded Graphviz rendering for workspace knowledge-graph artifacts."""
from __future__ import annotations

import json
import os
import selectors
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, BinaryIO, cast

import file_io

MAX_GRAPH_SOURCE_BYTES = 1 * 1024 * 1024
MAX_GRAPH_RECORDS = 4000
MAX_GRAPH_NODES = 2500
MAX_GRAPH_EDGES = 6000
MAX_GRAPH_OUTPUT_BYTES = 8 * 1024 * 1024
GRAPHVIZ_TIMEOUT_SECONDS = 8
SUPPORTED_EXTENSIONS = {".json", ".jsonl", ".ndjson"}


class GraphvizError(ValueError):
    """A client-safe graph rendering error."""

    def __init__(self, code: str, message: str | None = None):
        self.code = code
        super().__init__(message or code)


def _dot_string(value: object, limit: int = 240) -> str:
    text = str(value or "").replace("\x00", " ").replace("\r", " ")[:limit]
    text = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return '"' + text + '"'


def _record_label(record: dict[str, Any]) -> str:
    kind = str(record.get("kind") or "record")
    rid = str(record.get("record_id") or "unknown")
    detail = record.get("predicate") or record.get("sort") or record.get("link_kind")
    return f"{kind}\n{rid}" + (f"\n{detail}" if detail else "")


def _node_kind_style(kind: str) -> tuple[str, str]:
    if kind in {"span", "mention"}:
        return "box", "#e7f0ea"
    if kind in {"proposition", "premise", "derivation"}:
        return "ellipse", "#e9eef8"
    if kind in {"evidence_assessment", "evidence_link", "result_evidence"}:
        return "diamond", "#f5ead8"
    return "box", "#f1eee9"


def records_to_dot(records: list[dict[str, Any]]) -> str:
    """Build a deterministic, safe DOT graph from logic-v0 JSONL records."""
    if len(records) > MAX_GRAPH_RECORDS:
        raise GraphvizError("graph_too_large")
    node_records: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = record.get("record_id")
        if not isinstance(record_id, str) or not record_id.strip():
            continue
        if len(record_id) > 240:
            raise GraphvizError("record_id_too_long")
        if len(node_records) >= MAX_GRAPH_NODES and record_id not in node_records:
            raise GraphvizError("graph_too_large")
        node_records[record_id] = record
    if not node_records:
        raise GraphvizError("graph_empty")

    edges: set[tuple[str, str, str]] = set()

    def edge(source: object, target: object, label: object = "") -> None:
        if isinstance(source, str) and isinstance(target, str):
            if source in node_records and target in node_records:
                edges.add((source, target, str(label or "")))

    for record in node_records.values():
        rid = record["record_id"]
        kind = record.get("kind")
        if kind == "evidence_link":
            edge(record.get("src_id"), record.get("dst_id"), record.get("link_kind"))
        elif kind in {"proposition", "selection"}:
            edge(record.get("span_id"), rid, "supports")
        elif kind in {"evidence_assessment", "result_evidence"}:
            edge(record.get("target_id"), rid, record.get("verdict") or record.get("role"))
        elif kind == "premise":
            edge(record.get("proposition_id"), rid, "premise")
            edge(record.get("assessment_id"), rid, "assessed by")
        elif kind == "derivation":
            premise_ids = record.get("premise_ids") or []
            if not isinstance(premise_ids, list) or any(not isinstance(item, str) for item in premise_ids):
                raise GraphvizError("bad_graph_record")
            for premise_id in premise_ids:
                edge(premise_id, rid, "premise")
            edge(rid, record.get("conclusion_id"), "concludes")
        elif kind == "law_obligation":
            edge(record.get("proposition_id"), rid, "obligation")

    if len(edges) > MAX_GRAPH_EDGES:
        raise GraphvizError("graph_too_large")

    lines = [
        "digraph knowledge_graph {",
        '  graph [rankdir=LR, bgcolor="transparent", pad="0.2"];',
        '  node [fontname="Arial", fontsize=10, style="filled", color="#9c9286"];',
        '  edge [fontname="Arial", fontsize=8, color="#85796c"];',
    ]
    for record_id, record in node_records.items():
        shape, fill = _node_kind_style(str(record.get("kind") or "record"))
        lines.append(
            f"  {_dot_string(record_id)} [label={_dot_string(_record_label(record))}, "
            f"shape={shape}, fillcolor={_dot_string(fill)}];"
        )
    for source, target, label in sorted(edges):
        attrs = f" [label={_dot_string(label)}]" if label else ""
        lines.append(f"  {_dot_string(source)} -> {_dot_string(target)}{attrs};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _json_records(source: bytes, suffix: str) -> list[dict[str, Any]]:
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GraphvizError("graph_not_utf8") from exc

    records: list[dict[str, Any]] = []
    if suffix in {".jsonl", ".ndjson"}:
        lines = text.splitlines()
        if len(lines) > MAX_GRAPH_RECORDS:
            raise GraphvizError("graph_too_large")
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except (json.JSONDecodeError, RecursionError, ValueError) as exc:
                raise GraphvizError(f"bad_graph_jsonl:{line_number}") from exc
            if not isinstance(value, dict):
                raise GraphvizError(f"bad_graph_jsonl:{line_number}")
            records.append(value)
        return records

    try:
        value = json.loads(text)
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise GraphvizError("bad_graph_json") from exc
    if isinstance(value, dict) and isinstance(value.get("records"), list):
        value = value["records"]
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise GraphvizError("graph_json_records_required")
    return value


def source_to_dot(source: bytes, suffix: str) -> str:
    if len(source) > MAX_GRAPH_SOURCE_BYTES:
        raise GraphvizError("graph_too_large")
    suffix = suffix.lower()
    if suffix not in {".json", ".jsonl", ".ndjson"}:
        raise GraphvizError("graph_format_unsupported")
    return records_to_dot(_json_records(source, suffix))


def render_dot(dot_source: str) -> bytes:
    source = dot_source.encode("utf-8")
    with tempfile.TemporaryFile() as input_file:
        input_file.write(source)
        input_file.seek(0)
        try:
            proc = subprocess.Popen(
                ["dot", "-Tsvg"],
                stdin=input_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "LC_ALL": "C"},
            )
        except FileNotFoundError as exc:
            raise GraphvizError("graphviz_unavailable") from exc

        selector = selectors.DefaultSelector()
        assert proc.stdout is not None
        assert proc.stderr is not None
        selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
        selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
        stdout = bytearray()
        stderr_size = 0
        deadline = time.monotonic() + GRAPHVIZ_TIMEOUT_SECONDS
        try:
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    proc.kill()
                    proc.wait()
                    raise GraphvizError("graphviz_timeout")
                events = selector.select(remaining)
                if not events:
                    proc.kill()
                    proc.wait()
                    raise GraphvizError("graphviz_timeout")
                for key, _ in events:
                    stream = key.fileobj
                    fd = stream if isinstance(stream, int) else stream.fileno()
                    data = os.read(fd, 64 * 1024)
                    if not data:
                        selector.unregister(stream)
                        if not isinstance(stream, int):
                            cast(BinaryIO, stream).close()
                        continue
                    if key.data == "stdout":
                        stdout.extend(data)
                        if len(stdout) > MAX_GRAPH_OUTPUT_BYTES:
                            proc.kill()
                            proc.wait()
                            raise GraphvizError("graph_output_too_large")
                    else:
                        stderr_size += len(data)
                        if stderr_size > 64 * 1024:
                            proc.kill()
                            proc.wait()
                            raise GraphvizError("graphviz_failed")
            try:
                returncode = proc.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired as exc:
                proc.kill()
                proc.wait()
                raise GraphvizError("graphviz_timeout") from exc
            if returncode != 0:
                raise GraphvizError("invalid_graph")
        finally:
            selector.close()
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            if proc.stdout is not None and not proc.stdout.closed:
                proc.stdout.close()
            if proc.stderr is not None and not proc.stderr.closed:
                proc.stderr.close()
    return bytes(stdout)


def render_workspace_file(workspace: Path, relative_path: str) -> bytes:
    suffix = Path(relative_path).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise GraphvizError("graph_format_unsupported")
    fd, _record = file_io.open_workspace_file(workspace, relative_path)
    try:
        with os.fdopen(fd, "rb") as handle:
            source = handle.read(MAX_GRAPH_SOURCE_BYTES + 1)
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
    return render_dot(source_to_dot(source, suffix))
