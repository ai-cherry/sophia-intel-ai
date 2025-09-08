from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class CBState:
    open_until: float = 0.0
    failures: int = 0


class CircuitBreaker:
    """Per-VK circuit breaker with cooldown window.

    - on_error: increments failures and opens the circuit for cooldown seconds.
    - on_success: resets failures and closes the circuit.
    - is_open: returns True if within cooldown window.
    """

    def __init__(self, cooldown_seconds: int = 120, failure_threshold: int = 1):
        self.cooldown_seconds = cooldown_seconds
        self.failure_threshold = failure_threshold
        self._state: Dict[str, CBState] = {}

    def is_open(self, vk_env: str) -> bool:
        st = self._state.get(vk_env)
        if not st:
            return False
        return time.time() < st.open_until

    def on_error(self, vk_env: str) -> None:
        st = self._state.setdefault(vk_env, CBState())
        st.failures += 1
        if st.failures >= self.failure_threshold:
            st.open_until = time.time() + self.cooldown_seconds

    def on_success(self, vk_env: str) -> None:
        st = self._state.setdefault(vk_env, CBState())
        st.failures = 0
        st.open_until = 0.0

