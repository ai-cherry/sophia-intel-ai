from __future__ import annotations

"""
Sophia BI Agent Factory (Agno 2.0)

Builds BI-focused agents that use only BI tools (e.g., MCP memory,
integration APIs). No filesystem/git access here to preserve domain
separation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Any, Dict


def _try_import_agno():
    try:
        import agno  # type: ignore

        return agno
    except Exception:
        return None


@dataclass
class BIConsultantSpec:
    id: str = "sophia_bi_consultant"
    instructions: List[str] = field(
        default_factory=lambda: [
            "Provide clear, executive-ready insights.",
            "Use business integrations for context.",
            "Never access code or repository tools.",
        ]
    )
    model_policy: str = "balanced"


class SophiaAgentFactory:
    def __init__(self, registry_dir: Path):
        self.registry_dir = registry_dir
        self._agno = _try_import_agno()
        try:
            from .tools.bi_adapters import BIToolFactory  # type: ignore
            self._bi_factory = BIToolFactory()
        except Exception:
            self._bi_factory = None

    def has_agno_v2(self) -> bool:
        return self._agno is not None and hasattr(self._agno, "Agent")

    def build_bi_agent(self, spec: BIConsultantSpec):
        if self.has_agno_v2():
            Agent = getattr(self._agno, "Agent")
            tools = []
            if self._bi_factory:
                for t in getattr(spec, "tools", []) or []:
                    tools.append(self._bi_factory.map_tool(t))
            return Agent(name=spec.id, role="bi_consultant", instructions=spec.instructions, model=spec.model_policy, tools=tools)
        return {
            "id": spec.id,
            "role": "bi_consultant",
            "instructions": spec.instructions,
            "model": spec.model_policy,
        }

    # Registry helpers for parity with Builder
    def load_agent_spec(self, agent_id: str) -> Dict[str, Any]:
        import json
        path = self.registry_dir / f"{agent_id}.json"
        with path.open() as f:
            return json.load(f)

    def load_team_spec(self, team_id: str) -> Dict[str, Any]:
        import json
        path = self.registry_dir / f"team.{team_id}.json"
        with path.open() as f:
            return json.load(f)

