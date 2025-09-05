"""
Standardized LLM Response Models
Provides consistent response structure across all LLM interactions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ResponseStatus(Enum):
    """Status of the LLM response."""

    SUCCESS = "success"
    FALLBACK = "fallback"
    CACHED = "cached"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


@dataclass
class TokenStats:
    """Token usage statistics for a request."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0

    @property
    def cost_estimate(self) -> float:
        """Estimate cost in USD based on token usage."""
        # Rough estimates per 1M tokens (adjust based on actual model pricing)
        prompt_cost = self.prompt_tokens * 0.01 / 1000  # $10 per 1M prompt tokens
        completion_cost = self.completion_tokens * 0.03 / 1000  # $30 per 1M completion tokens
        return prompt_cost + completion_cost


@dataclass
class LLMResponse:
    """
    Standardized response from LLM operations.
    Ensures consistent structure for all LLM interactions.
    """

    # Core response data
    content: str
    success: bool
    status: ResponseStatus

    # Model information
    model: str = "unknown"
    provider: str = "unknown"
    task_type: Optional[str] = None

    # Timing information
    timestamp: datetime = field(default_factory=datetime.now)
    latency_ms: float = 0.0

    # Token and cost tracking
    token_stats: Optional[TokenStats] = None
    estimated_cost: float = 0.0

    # Error handling
    error: Optional[str] = None
    error_code: Optional[str] = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    session_id: Optional[str] = None

    # Fallback chain information
    attempts: list[dict[str, Any]] = field(default_factory=list)
    final_model: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary for JSON serialization."""
        return {
            "content": self.content,
            "success": self.success,
            "status": self.status.value,
            "model": self.model,
            "provider": self.provider,
            "task_type": self.task_type,
            "timestamp": self.timestamp.isoformat(),
            "latency_ms": self.latency_ms,
            "token_stats": {
                "prompt_tokens": self.token_stats.prompt_tokens if self.token_stats else 0,
                "completion_tokens": self.token_stats.completion_tokens if self.token_stats else 0,
                "total_tokens": self.token_stats.total_tokens if self.token_stats else 0,
                "cached_tokens": self.token_stats.cached_tokens if self.token_stats else 0,
            }
            if self.token_stats
            else None,
            "estimated_cost": self.estimated_cost,
            "error": self.error,
            "error_code": self.error_code,
            "metadata": self.metadata,
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "attempts": self.attempts,
            "final_model": self.final_model,
        }

    @classmethod
    def from_error(cls, error: str, error_code: Optional[str] = None) -> "LLMResponse":
        """Create an error response."""
        return cls(
            content="",
            success=False,
            status=ResponseStatus.ERROR,
            error=error,
            error_code=error_code,
        )

    @classmethod
    def from_cache(cls, content: str, original_model: str) -> "LLMResponse":
        """Create a response from cache."""
        return cls(
            content=content,
            success=True,
            status=ResponseStatus.CACHED,
            model=original_model,
            metadata={"source": "cache"},
        )
