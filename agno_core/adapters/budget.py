from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Dict, Optional

import yaml


_LOCK = threading.Lock()


@dataclass
class BudgetLimit:
    soft_cap_usd: float
    hard_cap_usd: float


class BudgetManager:
    """Simple in-memory budget manager backed by config/budgets.yaml.

    Note: For production, persist usage in Redis/Postgres and reset daily.
    """

    def __init__(self, yaml_path: Optional[str] = None):
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.yaml_path = yaml_path or os.path.join(root, "config", "budgets.yaml")
        self.limits: Dict[str, BudgetLimit] = {}
        self.usage_usd: Dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.isfile(self.yaml_path):
            return
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        vk_budgets = data.get("vk_budgets", {})
        for vk, lim in vk_budgets.items():
            self.limits[vk] = BudgetLimit(
                soft_cap_usd=float(lim.get("soft_cap_usd", 0.0)),
                hard_cap_usd=float(lim.get("hard_cap_usd", 0.0)),
            )

    def get_usage(self, vk_env: str) -> float:
        return self.usage_usd.get(vk_env, 0.0)

    def add_usage(self, vk_env: str, amount_usd: float) -> None:
        with _LOCK:
            self.usage_usd[vk_env] = self.get_usage(vk_env) + max(0.0, amount_usd)

    def check_and_reserve(self, vk_env: str, estimated_cost_usd: float) -> str:
        """Return 'allow', 'soft_cap', or 'blocked'. Reserve cost on allow/soft_cap."""
        limit = self.limits.get(vk_env)
        if not limit:
            # No limits configured → allow
            self.add_usage(vk_env, estimated_cost_usd)
            return "allow"
        current = self.get_usage(vk_env)
        post = current + estimated_cost_usd
        if post > limit.hard_cap_usd:
            return "blocked"
        if post > limit.soft_cap_usd:
            # soft cap reached → allow but signal downgrade preference
            self.add_usage(vk_env, estimated_cost_usd)
            return "soft_cap"
        self.add_usage(vk_env, estimated_cost_usd)
        return "allow"
