import os
import unittest

os.environ["LAB_SHARED_TOKEN"] = "test-token"
os.environ.pop("NEURALWATT_API_KEY", None)
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("OPENROUTER_API_KEY", None)
os.environ.pop("NAVIGATOR_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("XAI_API_KEY", None)

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


class TurnAuthTests(unittest.TestCase):
    def test_missing_bearer(self):
        self.assertEqual(server.TOKEN, "test-token")


if __name__ == "__main__":
    unittest.main()
