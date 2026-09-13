import json
import os
import unittest
from pathlib import Path

os.environ["LAB_SHARED_TOKEN"] = "test-token"
os.environ.pop("NEURALWATT_API_KEY", None)
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("OPENROUTER_API_KEY", None)
os.environ.pop("NAVIGATOR_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("XAI_API_KEY", None)

import paper_decomp_api  # noqa: E402
import providers  # noqa: E402
import server  # noqa: E402


class HealthTests(unittest.TestCase):
    def test_health_shape(self):
        h = server.health()
        self.assertTrue(h["ok"])
        self.assertEqual(h["profile"], "lab")
        self.assertEqual(h["class"], "lab-jail")
        self.assertTrue(h["token_configured"])
        self.assertIn("bioskills_count", h)
        self.assertGreaterEqual(h["bioskills_count"], 0)
        ids = [p["id"] for p in h["providers"]]
        self.assertEqual(
            ids,
            ["neuralwatt", "openai", "openrouter", "navigator", "anthropic", "xai"],
        )
        self.assertFalse(any(p["key_configured"] for p in h["providers"]))


class ResolveTurnTests(unittest.TestCase):
    def test_unknown_provider(self):
        got, err = providers.resolve_turn({"provider": "nope", "model": "x"})
        self.assertIsNone(got)
        assert err is not None
        self.assertEqual(err["error"], "unknown_provider")

    def test_unknown_model(self):
        got, err = providers.resolve_turn(
            {"provider": "openai", "model": "not-a-model"}
        )
        self.assertIsNone(got)
        assert err is not None
        self.assertEqual(err["error"], "unknown_model")

    def test_missing_key(self):
        got, err = providers.resolve_turn(
            {"provider": "openai", "model": "gpt-4o"}
        )
        self.assertIsNone(got)
        assert err is not None
        self.assertEqual(err["error"], "key_not_configured")

    def test_ok_when_key_set(self):
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            got, err = providers.resolve_turn(
                {"provider": "openai", "model": "gpt-4o"}
            )
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        self.assertIsNone(err)
        assert got is not None
        self.assertEqual(got["hermes_provider"], "custom:openai")
        self.assertEqual(got["model"], "gpt-4o")
        self.assertNotIn("guest_key", got)

    def test_guest_key_without_jail_key(self):
        got, err = providers.resolve_turn(
            {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "sk-user-secret",
            }
        )
        self.assertIsNone(err)
        assert got is not None
        self.assertEqual(got["guest_key"], "sk-user-secret")
        self.assertEqual(got["key_env"], "OPENAI_API_KEY")

    def test_guest_key_too_long(self):
        got, err = providers.resolve_turn(
            {"provider": "openai", "model": "gpt-4o", "api_key": "x" * 513}
        )
        self.assertIsNone(got)
        assert err is not None
        self.assertEqual(err["error"], "key_too_long")

    def test_default_model(self):
        os.environ["NAVIGATOR_API_KEY"] = "sk-g"
        try:
            got, err = providers.resolve_turn({"provider": "navigator"})
        finally:
            os.environ.pop("NAVIGATOR_API_KEY", None)
        self.assertIsNone(err)
        assert got is not None
        self.assertEqual(got["model"], "gemma-4-31b-it")
        self.assertEqual(got["hermes_provider"], "custom:navigator")


class OpenAICompatTests(unittest.TestCase):
    def test_parse_provider_slash_model(self):
        self.assertEqual(
            providers.parse_openai_model("openrouter/openai/gpt-4o"),
            ("openrouter", "openai/gpt-4o"),
        )

    def test_parse_bare_unique_model(self):
        self.assertEqual(providers.parse_openai_model("grok-4.6"), ("xai", "grok-4.6"))

    def test_messages_to_prompt(self):
        prompt = providers.messages_to_prompt(
            [
                {"role": "system", "content": "Be brief."},
                {"role": "user", "content": "Ping"},
            ]
        )
        self.assertEqual(prompt, "system: Be brief.\nuser: Ping")

    def test_turn_prompt_one_shot(self):
        self.assertEqual(providers.turn_prompt({"message": " Ping "}), "Ping")

    def test_turn_prompt_messages_win(self):
        prompt = providers.turn_prompt(
            {
                "message": "ignored",
                "messages": [
                    {"role": "user", "content": "A"},
                    {"role": "assistant", "content": "B"},
                    {"role": "user", "content": "C"},
                ],
            }
        )
        self.assertEqual(prompt, "user: A\nassistant: B\nuser: C")

    def test_turn_prompt_empty(self):
        self.assertEqual(providers.turn_prompt({}), "")

    def test_openai_models_ids(self):
        ids = [row["id"] for row in providers.openai_models()["data"]]
        self.assertIn("xai/grok-4.6", ids)
        self.assertIn("openrouter/openai/gpt-4o", ids)

    def test_completion_json_not_stream(self):
        ctype, body = server.openai_completion("xai/grok-4.6", "PONG", False)
        self.assertEqual(ctype, "application/json")
        payload = json.loads(body)
        self.assertEqual(payload["choices"][0]["message"]["content"], "PONG")

    def test_completion_sse(self):
        ctype, body = server.openai_completion("xai/grok-4.6", "PONG", True)
        self.assertEqual(ctype, "text/event-stream")
        self.assertIn("data: [DONE]", body)
        self.assertIn("PONG", body)


class TurnAuthTests(unittest.TestCase):
    def test_missing_bearer(self):
        self.assertEqual(server.TOKEN, "test-token")


class HermesCmdTests(unittest.TestCase):
    def test_preloads_lit_review(self):
        cmd = server.hermes_cmd(
            "hi",
            {"hermes_provider": "custom:openai", "model": "gpt-4o"},
        )
        self.assertIn("-s", cmd)
        self.assertEqual(cmd[cmd.index("-s") + 1], "lit-review")
        self.assertIn("chat", cmd)
        self.assertIn("-q", cmd)
        self.assertIn("hi", cmd)

    def test_index_is_multishot(self):
        html = server.INDEX_HTML
        self.assertIn("messages: thread.slice()", html)
        self.assertIn("New thread", html)
        self.assertIn("lit-review", html)


class PaperDecompositionToolTests(unittest.TestCase):
    def test_health_lists_tool(self):
        h = server.health()
        ids = [t["id"] for t in h["tools"]]
        self.assertIn("paper-decomposition", ids)
        self.assertEqual(h["tools"][0]["engine_version"], "0.4.0")

    def test_admit_fixture(self):
        fixture = Path(__file__).resolve().parent / "litreview-engine" / "fixtures" / "syn-logic.jsonl"
        code, body = paper_decomp_api.admit({"jsonl": fixture.read_text()})
        self.assertEqual(code, 200)
        self.assertTrue(body["ok"])
        self.assertGreaterEqual(body["admitted"], 1)
        self.assertIn("figure_panel", body["sorts"])

    def test_admit_needs_payload(self):
        code, body = paper_decomp_api.admit({})
        self.assertEqual(code, 400)
        self.assertEqual(body["error"], "need_records_or_jsonl")


if __name__ == "__main__":
    unittest.main()
