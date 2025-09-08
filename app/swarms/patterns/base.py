"""
Base classes and interfaces for swarm patterns.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class PatternConfig:
    """Base configuration for swarm patterns."""

    enabled: bool = True
    max_retries: int = 3
    timeout_seconds: float = 300.0
    logging_enabled: bool = True
    metrics_enabled: bool = True
    custom_params: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback to custom params."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.custom_params.get(key, default)


@dataclass
class PatternResult(Generic[T]):
    """Result from pattern execution."""

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metrics: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    pattern_name: str = ""
    execution_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "pattern_name": self.pattern_name,
            "execution_time": self.execution_time,
        }


class SwarmPattern(ABC):
    """Abstract base class for swarm patterns."""

    def __init__(self, config: Optional[PatternConfig] = None):
        """Initialize pattern with configuration."""
        self.config = config or PatternConfig()
        self.execution_history: list[PatternResult] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize pattern resources."""
        if not self._initialized:
            await self._setup()
            self._initialized = True
        return None  # Explicit return for proper async/await behavior

    async def cleanup(self) -> None:
        """Cleanup pattern resources."""
        if self._initialized:
            await self._teardown()
            self._initialized = False
        return None  # Explicit return for proper async/await behavior

    @abstractmethod
    async def execute(
        self, context: dict[str, Any], agents: list[Any]
    ) -> PatternResult:
        """
        Execute the pattern with given context and agents.

        Args:
            context: Execution context containing problem, constraints, etc.
            agents: List of available agents

        Returns:
            PatternResult containing execution outcome
        """

    @abstractmethod
    async def _setup(self) -> None:
        """Setup pattern-specific resources."""

    @abstractmethod
    async def _teardown(self) -> None:
        """Teardown pattern-specific resources."""

    def get_metrics(self) -> dict[str, Any]:
        """Get pattern execution metrics."""
        if not self.execution_history:
            return {}

        successful = sum(1 for r in self.execution_history if r.success)
        total = len(self.execution_history)
        avg_time = (
            sum(r.execution_time for r in self.execution_history) / total
            if total > 0
            else 0
        )

        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": successful / total if total > 0 else 0,
            "average_execution_time": avg_time,
            "last_execution": (
                self.execution_history[-1].timestamp if self.execution_history else None
            ),
        }

    def reset_history(self) -> None:
        """Reset execution history."""
        self.execution_history.clear()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
