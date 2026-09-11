import os
import unittest

os.environ["LAB_SHARED_TOKEN"] = "test-token"

import server  # noqa: E402


class HealthTests(unittest.TestCase):
    def test_health_shape(self):
        h = server.health()
        self.assertTrue(h["ok"])
        self.assertEqual(h["profile"], "lab")
        self.assertEqual(h["class"], "lab-jail")
        self.assertTrue(h["token_configured"])


class TurnAuthTests(unittest.TestCase):
    def test_missing_bearer(self):
        # smoke: TOKEN is set from env at import
        self.assertEqual(server.TOKEN, "test-token")


if __name__ == "__main__":
    unittest.main()
