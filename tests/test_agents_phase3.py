import unittest

from agno_core.agents.coder_agent import CoderAgent
from agno_core.agents.architect_agent import ArchitectAgent
from agno_core.agents.reviewer_agent import ReviewerAgent
from agno_core.agents.researcher_agent import ResearcherAgent
from agno_core.agents.coordinator import AgentCoordinator


class TestAgentsPhase3(unittest.TestCase):
    def setUp(self):
        import os
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
    def test_agents_plan_routes(self):
        coder = CoderAgent()
        arch = ArchitectAgent()
        review = ReviewerAgent()
        research = ResearcherAgent()

        for agent, prompt in [
            (coder, "Write a Python function"),
            (arch, "Design a scalable API"),
            (review, "Review this code for bugs"),
            (research, "Find best practices for retries"),
        ]:
            res = agent.plan(prompt=prompt)
            self.assertTrue(res.success)
            self.assertIn("provider_model", res.route.primary_spec)

    def test_coordinator_sequence(self):
        agents = [CoderAgent(), ArchitectAgent()]
        coord = AgentCoordinator(agents)
        out = coord.run_sequence("Implement and design a feature")
        self.assertIn("CoderAgent", out)
        self.assertIn("ArchitectAgent", out)


if __name__ == "__main__":
    unittest.main()
