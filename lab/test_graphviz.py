import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import graphviz


class GraphvizTests(unittest.TestCase):
    def test_records_to_dot_connects_logic_records(self):
        dot = graphviz.records_to_dot(
            [
                {
                    "record_id": "span:1",
                    "kind": "span",
                    "corpus_id": "demo",
                },
                {
                    "record_id": "prop:1",
                    "kind": "proposition",
                    "predicate": "method_operation",
                    "span_id": "span:1",
                },
            ]
        )
        self.assertIn('"span:1"', dot)
        self.assertIn('"prop:1"', dot)
        self.assertIn('label="supports"', dot)

    def test_jsonl_source_is_converted_to_dot(self):
        source = b'{"record_id":"node:1","kind":"mention"}\n'
        dot = graphviz.source_to_dot(source, ".jsonl")
        self.assertIn("digraph knowledge_graph", dot)
        self.assertIn("node:1", dot)

    def test_rejects_malformed_derivation_record(self):
        with self.assertRaisesRegex(graphviz.GraphvizError, "bad_graph_record"):
            graphviz.records_to_dot(
                [{"record_id": "d:1", "kind": "derivation", "premise_ids": 7}]
            )

    def test_rejects_unsupported_source_format(self):
        with self.assertRaisesRegex(graphviz.GraphvizError, "graph_format_unsupported"):
            graphviz.source_to_dot(b"digraph {}", ".dot")

    @patch("graphviz.subprocess.Popen", side_effect=FileNotFoundError)
    def test_render_reports_missing_graphviz(self, _popen):
        with self.assertRaisesRegex(graphviz.GraphvizError, "graphviz_unavailable"):
            graphviz.render_dot("digraph { a -> b }")

    @patch("graphviz.render_dot", return_value=b"<svg/>")
    def test_workspace_render_reads_only_allowed_file(self, render):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "outputs").mkdir()
            (root / "outputs" / "knowledge.jsonl").write_text(
                '{"record_id":"n:1","kind":"mention"}\n'
            )
            self.assertEqual(
                graphviz.render_workspace_file(root, "outputs/knowledge.jsonl"),
                b"<svg/>",
            )
        render.assert_called_once()

    def test_graph_source_limit(self):
        with self.assertRaisesRegex(graphviz.GraphvizError, "graph_too_large"):
            graphviz.source_to_dot(
                b"x" * (graphviz.MAX_GRAPH_SOURCE_BYTES + 1), ".jsonl"
            )


if __name__ == "__main__":
    unittest.main()
