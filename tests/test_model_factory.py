import os
import unittest

from agno_core.adapters.model_factory import ModelFactory


class TestModelFactory(unittest.TestCase):
    def setUp(self):
        # Snapshot env
        self._env = dict(os.environ)
        # Minimal VKs for success path
        os.environ.setdefault("PORTKEY_API_KEY", "pk_test_1234")
        for vk in [
            "PORTKEY_VK_XAI",
            "PORTKEY_VK_OPENAI",
            "PORTKEY_VK_ANTHROPIC",
            "PORTKEY_VK_OPENROUTER",
            "PORTKEY_VK_GOOGLE",
            "PORTKEY_VK_DEEPSEEK",
            "PORTKEY_VK_QWEN",
            "PORTKEY_VK_META",
        ]:
            os.environ.setdefault(vk, f"vk_{vk.lower()}_redacted")

    def tearDown(self):
        # Restore env
        os.environ.clear()
        os.environ.update(self._env)

    def test_build_fast_operations_spec(self):
        fac = ModelFactory()
        spec = fac.create("fast_operations").build_call_spec()
        self.assertIn("provider_model", spec)
        self.assertIn("portkey_api_key", spec)
        self.assertIn("params", spec)
        self.assertTrue(spec["provider_model"].startswith("x-ai/"))

    def test_build_reasoning_spec_with_multiple_vks(self):
        fac = ModelFactory()
        spec = fac.create("reasoning").build_call_spec()
        self.assertIn("virtual_keys", spec)
        self.assertGreaterEqual(len(spec["virtual_keys"]), 1)

    def test_build_specialized_scout(self):
        fac = ModelFactory()
        spec = fac.create("specialized", subkey="scout").build_call_spec()
        self.assertIn("provider_model", spec)
        self.assertIn("virtual_key", spec)


if __name__ == "__main__":
    unittest.main()

