import os
import unittest

from agno_core.adapters.router import ModelRouter, TaskSpec


class TestModelRouter(unittest.TestCase):
    def setUp(self):
        # Ensure VKs exist to avoid ConfigErrors when building specs
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

    def test_fast_route(self):
        router = ModelRouter()
        route = router.route(TaskSpec(task_type="general", urgency_ms=200))
        self.assertTrue(route.category.startswith("fast_operations"))
        self.assertIn("provider_model", route.primary_spec)

    def test_coding_route_and_fallback(self):
        router = ModelRouter()
        route = router.route(TaskSpec(task_type="code_generation"))
        self.assertEqual(route.category, "coding")
        # May have at least one fallback (qwen)
        self.assertIsInstance(route.fallback_specs, list)

    def test_advanced_context_route(self):
        router = ModelRouter()
        route = router.route(TaskSpec(task_type="analysis", context_tokens=1_000_000))
        self.assertEqual(route.category, "advanced_context")

    def test_reasoning_with_fallback_chain(self):
        router = ModelRouter()
        route = router.route(TaskSpec(task_type="analysis"))
        self.assertEqual(route.category, "reasoning")
        # Should attempt to construct fallbacks from config (errors allowed in entries)
        self.assertIsInstance(route.fallback_specs, list)

    def test_creative_routes_to_maverick(self):
        router = ModelRouter()
        route = router.route(TaskSpec(task_type="creative", creative=True))
        self.assertEqual(route.category, "specialized.maverick")


if __name__ == "__main__":
    unittest.main()

