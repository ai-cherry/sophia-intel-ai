from __future__ import annotations

from typing import Dict, List

from agno_core.agents.base_agent import BaseAgent, AgentResult
from agno_core.adapters.telemetry import Telemetry


class AgentCoordinator:
    """Minimal coordinator that invokes agents sequentially (extensible)."""

    def __init__(self, agents: List[BaseAgent], telemetry: Telemetry | None = None):
        self.agents = agents
        self.telemetry = telemetry or Telemetry(echo_stdout=False)

    def run_sequence(self, prompt: str) -> Dict[str, AgentResult]:
        results: Dict[str, AgentResult] = {}
        for agent in self.agents:
            res = agent.plan(prompt=prompt)
            results[agent.name] = res
            self.telemetry.emit({
                "type": "coordination.step",
                "agent": agent.name,
                "primary_model": res.route.primary_spec.get("provider_model"),
            })
        return results

