from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .model_factory import ModelFactory, ConfigError
from .budget import BudgetManager
from .circuit_breaker import CircuitBreaker
from .telemetry import Telemetry


@dataclass
class TaskSpec:
    task_type: str  # e.g., 'code_generation', 'analysis', 'research', 'creative', 'general'
    urgency_ms: Optional[int] = None
    context_tokens: Optional[int] = None
    creative: bool = False
    strict_quality: bool = False


@dataclass
class SelectedRoute:
    category: str  # logical category from models.yaml (e.g., 'coding') or 'specialized.maverick'
    primary_spec: Dict[str, Any]
    fallback_specs: List[Dict[str, Any]]


class ModelRouter:
    """Rule-based router with fallback chain assembly from models.yaml.

    This class does not perform network calls; it only constructs call specs for Portkey.
    """

    def __init__(
        self,
        factory: Optional[ModelFactory] = None,
        budget: Optional[BudgetManager] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        telemetry: Optional[Telemetry] = None,
    ):
        self.factory = factory or ModelFactory()
        self.cfg = self.factory._cfg.get("model_routing", {})
        self.budget = budget or BudgetManager()
        self.cb = circuit_breaker or CircuitBreaker()
        self.telemetry = telemetry or Telemetry(echo_stdout=False)

    def route(self, spec: TaskSpec) -> SelectedRoute:
        # Category selection
        category, subkey = self._select_category(spec)

        # Build candidate specs: primary + fallbacks
        primary_client = (
            self.factory.create(category, subkey=subkey)
            if subkey is None
            else self.factory.create("specialized", subkey=subkey)
        )
        primary_spec = primary_client.build_call_spec()
        fallback_specs: List[Dict[str, Any]] = self._build_fallbacks(category)
        candidates: List[Dict[str, Any]] = [primary_spec, *fallback_specs]

        evaluated: List[Dict[str, Any]] = []
        chosen: Optional[Dict[str, Any]] = None

        for idx, call_spec in enumerate(candidates):
            decision, selected_vk_env = self._assess_spec(call_spec, spec)
            call_spec = dict(call_spec)
            if selected_vk_env:
                call_spec["selected_vk_env"] = selected_vk_env
            call_spec["budget_decision"] = decision
            self.telemetry.emit({
                "type": "route_candidate",
                "category": category if subkey is None else f"{category}.{subkey}",
                "order": idx,
                "provider_model": call_spec.get("provider_model"),
                "decision": decision,
                "vk_env": selected_vk_env,
            })
            if decision in ("allow", "soft_cap") and chosen is None:
                chosen = call_spec
            else:
                evaluated.append(call_spec)

        if chosen is None:
            # Nothing allowed; pick the original primary but mark blocked
            chosen = dict(primary_spec)
            chosen["selected_vk_env"] = self._first_vk_env(primary_spec)
            chosen["budget_decision"] = "blocked"

        # Remaining allowed candidates become fallbacks (preserve order)
        fallbacks_filtered = [e for e in evaluated if e.get("budget_decision") in ("allow", "soft_cap")]

        self.telemetry.emit({
            "type": "route_decision",
            "category": category if subkey is None else f"{category}.{subkey}",
            "primary_provider_model": chosen.get("provider_model"),
            "primary_vk_env": chosen.get("selected_vk_env"),
            "fallback_count": len(fallbacks_filtered),
        })

        return SelectedRoute(category if subkey is None else f"{category}.{subkey}", chosen, fallbacks_filtered)

    def _select_category(self, spec: TaskSpec) -> Tuple[str, Optional[str]]:
        # Urgent tasks route to fast operations
        if spec.urgency_ms is not None and spec.urgency_ms <= 500:
            return "fast_operations", None

        # Large context tasks
        if spec.context_tokens and spec.context_tokens >= 500_000:
            return "advanced_context", None

        # Creative tasks
        if spec.creative and spec.task_type in {"creative", "ideation", "design"}:
            return "specialized", "maverick"

        # Code tasks
        if spec.task_type in {"code_generation", "refactor", "fix", "test"}:
            return "coding", None

        # Deep analysis / reasoning
        if spec.task_type in {"analysis", "architecture", "decision", "reasoning"} or spec.strict_quality:
            return "reasoning", None

        # Exploration/research preference
        if spec.task_type in {"research", "exploration"}:
            return "specialized", "scout"

        # Default
        return "general", None

    def _build_fallbacks(self, category: str) -> List[Dict[str, Any]]:
        fallbacks: List[Dict[str, Any]] = []
        if category == "reasoning":
            entry = self.cfg.get("reasoning", {})
            chain = entry.get("fallback_chain", [])
            for model_name in chain:
                try:
                    fb = self.factory.create_for_model(model_name).build_call_spec()
                    fallbacks.append(fb)
                except Exception as e:
                    fallbacks.append({"error": str(e), "provider_model": model_name})
        elif category == "coding":
            entry = self.cfg.get("coding", {})
            secondary = entry.get("secondary")
            if secondary:
                try:
                    fb = self.factory.create_for_model(secondary).build_call_spec()
                    fallbacks.append(fb)
                except Exception as e:
                    fallbacks.append({"error": str(e), "provider_model": secondary})
        elif category == "general":
            entry = self.cfg.get("general", {})
            fb_model = entry.get("fallback")
            if fb_model:
                try:
                    fallbacks.append(self.factory.create_for_model(fb_model).build_call_spec())
                except Exception as e:
                    fallbacks.append({"error": str(e), "provider_model": fb_model})
        # specialized categories do not add fallbacks by default
        return fallbacks

    # ----- Internal helpers -----
    def _first_vk_env(self, call_spec: Dict[str, Any]) -> Optional[str]:
        if "vk_env" in call_spec:
            return call_spec["vk_env"]
        vk_envs = call_spec.get("vk_envs")
        if isinstance(vk_envs, list) and vk_envs:
            return vk_envs[0]
        return None

    def _vk_env_candidates(self, call_spec: Dict[str, Any]) -> List[str]:
        if "vk_env" in call_spec:
            return [call_spec["vk_env"]]
        vk_envs = call_spec.get("vk_envs")
        return list(vk_envs) if isinstance(vk_envs, list) else []

    def _estimate_cost_usd(self, category: str, task: TaskSpec) -> float:
        # Very rough heuristic cost estimator.
        cpm_usd = {
            "fast_operations": 0.1,
            "coding": 0.6,
            "reasoning": 1.2,
            "general": 0.3,
            "advanced_context": 5.0,
            "specialized": 0.4,
        }
        expected_tokens = 1000
        if category == "fast_operations":
            expected_tokens = 500
        elif category == "coding":
            expected_tokens = 3000
        elif category == "reasoning":
            expected_tokens = 4000
        elif category == "advanced_context":
            expected_tokens = max(task.context_tokens or 100000, 100000)
        elif category.startswith("specialized"):
            expected_tokens = 2000
        elif category == "general":
            expected_tokens = 1500
        rate = cpm_usd.get(category.split(".")[0], 0.5)
        return (expected_tokens / 1000.0) * rate

    def _assess_spec(self, call_spec: Dict[str, Any], task: TaskSpec) -> Tuple[str, Optional[str]]:
        """Return (decision, selected_vk_env). decision ∈ {allow, soft_cap, blocked}.

        Applies circuit breaker first, then budgets. For multi-VK specs, pick the
        first that is not open and not blocked by budget.
        """
        category_hint = "general"
        # Derive category from task
        category_hint, _ = self._select_category(task)
        est_cost = self._estimate_cost_usd(category_hint, task)
        for vk_env in self._vk_env_candidates(call_spec):
            if self.cb.is_open(vk_env):
                self.telemetry.emit({
                    "type": "cb_open",
                    "vk_env": vk_env,
                    "provider_model": call_spec.get("provider_model"),
                })
                continue
            decision = self.budget.check_and_reserve(vk_env, est_cost)
            if decision == "blocked":
                self.telemetry.emit({
                    "type": "budget_blocked",
                    "vk_env": vk_env,
                    "estimated_cost_usd": round(est_cost, 4),
                })
                continue
            if decision in ("allow", "soft_cap"):
                return decision, vk_env
        return "blocked", None
