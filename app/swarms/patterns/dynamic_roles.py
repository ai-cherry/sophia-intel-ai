"""
Dynamic Roles Pattern for adaptive agent specialization.
"""

import logging
from dataclasses import dataclass
from typing import Any

from .base import PatternConfig, PatternResult, SwarmPattern

logger = logging.getLogger(__name__)


@dataclass
class DynamicRolesConfig(PatternConfig):
    """Configuration for dynamic roles pattern."""
    role_types: list[str] = None
    performance_threshold: float = 0.7
    rotation_frequency: int = 3
    specialization_bonus: float = 0.1

    def __post_init__(self):
        if self.role_types is None:
            self.role_types = ["leader", "analyzer", "executor", "validator"]


class DynamicRolesPattern(SwarmPattern):
    """
    Dynamically assigns and rotates agent roles based on performance.
    """

    def __init__(self, config: DynamicRolesConfig | None = None):
        super().__init__(config or DynamicRolesConfig())
        self.role_assignments = {}
        self.performance_history = {}

    async def _setup(self) -> None:
        """Initialize role system."""
        logger.info("Initializing Dynamic Roles")

    async def _teardown(self) -> None:
        """Cleanup role system."""

    async def execute(self, context: dict[str, Any], agents: list[Any]) -> PatternResult:
        """Execute with dynamic role assignment."""
        # Assign initial roles
        self._assign_roles(agents, context)

        # Execute with roles
        result = await self._execute_with_roles(context, agents)

        # Update performance metrics
        self._update_performance(agents, result)

        # Rotate if needed
        if self._should_rotate():
            self._rotate_roles(agents)

        return PatternResult(
            success=True,
            data=result,
            metrics={"role_assignments": self.role_assignments},
            pattern_name="dynamic_roles"
        )

    def _assign_roles(self, agents: list, context: dict) -> None:
        """Assign roles to agents."""
        for i, agent in enumerate(agents):
            role = self.config.role_types[i % len(self.config.role_types)]
            self.role_assignments[str(agent)] = role

    async def _execute_with_roles(self, context: dict, agents: list) -> dict:
        """Execute task with role-specific behaviors."""
        return {"roles": self.role_assignments}

    def _update_performance(self, agents: list, result: dict) -> None:
        """Update agent performance metrics."""
        for agent in agents:
            if str(agent) not in self.performance_history:
                self.performance_history[str(agent)] = []
            self.performance_history[str(agent)].append(0.8)  # Simulated

    def _should_rotate(self) -> bool:
        """Check if roles should be rotated."""
        return len(self.execution_history) % self.config.rotation_frequency == 0

    def _rotate_roles(self, agents: list) -> None:
        """Rotate agent roles."""
        roles = list(self.role_assignments.values())
        roles = roles[1:] + [roles[0]]  # Rotate
        for agent, role in zip(agents, roles, strict=False):
            self.role_assignments[str(agent)] = role
