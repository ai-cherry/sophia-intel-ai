from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from agno_core.adapters.router import ModelRouter, TaskSpec, SelectedRoute
from agno_core.adapters.telemetry import Telemetry


@dataclass
class AgentResult:
    success: bool
    route: SelectedRoute
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class BaseAgent:
    """Base class that selects a model route via ModelRouter and emits telemetry.

    This class intentionally does not perform network calls. It returns the
    chosen Portkey call spec so the caller can execute it using the runtime.
    """

    category: str = "general"
    creative: bool = False
    strict_quality: bool = False

    def __init__(self, name: str, router: Optional[ModelRouter] = None, telemetry: Optional[Telemetry] = None):
        self.name = name
        self.router = router or ModelRouter()
        self.telemetry = telemetry or Telemetry(echo_stdout=False)

    def build_task_spec(self, *, prompt: str, urgency_ms: Optional[int] = None, context_tokens: Optional[int] = None) -> TaskSpec:
        return TaskSpec(
            task_type=self.category,
            urgency_ms=urgency_ms,
            context_tokens=context_tokens,
            creative=self.creative,
            strict_quality=self.strict_quality,
        )

    def plan(self, *, prompt: str, urgency_ms: Optional[int] = None, context_tokens: Optional[int] = None) -> AgentResult:
        spec = self.build_task_spec(prompt=prompt, urgency_ms=urgency_ms, context_tokens=context_tokens)
        route = self.router.route(spec)
        self.telemetry.emit({
            "type": "agent.plan",
            "agent": self.name,
            "category": self.category,
            "primary_provider_model": route.primary_spec.get("provider_model"),
            "vk_env": route.primary_spec.get("selected_vk_env") or route.primary_spec.get("vk_env"),
        })
        # No network execution here. Return the planned route.
        return AgentResult(success=True, route=route, meta={"prompt_preview": prompt[:80]})

