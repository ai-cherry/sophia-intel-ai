import time
import unittest

from agno_core.adapters.budget import BudgetManager
from agno_core.adapters.circuit_breaker import CircuitBreaker


class TestBudgetAndCircuitBreaker(unittest.TestCase):
    def test_budget_manager(self):
        bm = BudgetManager()
        vk = "PORTKEY_VK_OPENAI"
        # Large request near soft cap
        decision1 = bm.check_and_reserve(vk, 49.0)
        self.assertEqual(decision1, "allow")
        # Push past soft cap
        decision2 = bm.check_and_reserve(vk, 2.0)
        self.assertEqual(decision2, "soft_cap")
        # Push past hard cap
        decision3 = bm.check_and_reserve(vk, 60.0)
        self.assertEqual(decision3, "blocked")

    def test_circuit_breaker(self):
        cb = CircuitBreaker(cooldown_seconds=1, failure_threshold=1)
        vk = "PORTKEY_VK_ANTHROPIC"
        self.assertFalse(cb.is_open(vk))
        cb.on_error(vk)
        self.assertTrue(cb.is_open(vk))
        time.sleep(1.1)
        self.assertFalse(cb.is_open(vk))
        cb.on_success(vk)
        self.assertFalse(cb.is_open(vk))


if __name__ == "__main__":
    unittest.main()

