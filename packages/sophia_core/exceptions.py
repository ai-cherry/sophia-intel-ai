"""Core exception classes for Sophia AI framework.

Provides a hierarchy of exceptions for consistent error handling across
all components of the system.
"""

from typing import Any, Dict, Optional


class SophiaException(Exception):
    """Base exception class for all Sophia-related errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "SOPHIA_ERROR"
        self.context = context or {}


class ConfigurationError(SophiaException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)


class ModelError(SophiaException):
    """Base class for model-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="MODEL_ERROR", **kwargs)


class ProviderUnavailableError(ModelError):
    """Raised when an LLM provider is unavailable."""

    def __init__(self, provider: str, reason: str = "Service unavailable", **kwargs):
        message = f"Provider {provider} unavailable: {reason}"
        super().__init__(message, error_code="PROVIDER_UNAVAILABLE", **kwargs)


class RateLimitError(ModelError):
    """Raised when rate limits are exceeded."""

    def __init__(
        self,
        provider: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        message = f"Rate limit exceeded for {provider}"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        super().__init__(message, error_code="RATE_LIMIT", **kwargs)
        self.retry_after = retry_after


class MemoryError(SophiaException):
    """Base class for memory-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="MEMORY_ERROR", **kwargs)


class VectorStoreError(MemoryError):
    """Raised when vector store operations fail."""

    def __init__(self, store: str, operation: str, reason: str, **kwargs):
        message = f"Vector store {store} failed during {operation}: {reason}"
        super().__init__(message, error_code="VECTOR_STORE_ERROR", **kwargs)


class ToolError(SophiaException):
    """Base class for tool-related errors."""

    def __init__(self, tool_name: str, message: str, **kwargs):
        full_message = f"Tool {tool_name}: {message}"
        super().__init__(full_message, error_code="TOOL_ERROR", **kwargs)
        self.tool_name = tool_name


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""

    def __init__(self, tool_name: str, reason: str, **kwargs):
        super().__init__(tool_name, f"Execution failed: {reason}", **kwargs)


class ToolTimeoutError(ToolError):
    """Raised when tool execution times out."""

    def __init__(self, tool_name: str, timeout: int, **kwargs):
        super().__init__(tool_name, f"Timed out after {timeout}s", **kwargs)


class AgentError(SophiaException):
    """Base class for agent-related errors."""

    def __init__(self, agent_id: str, message: str, **kwargs):
        full_message = f"Agent {agent_id}: {message}"
        super().__init__(full_message, error_code="AGENT_ERROR", **kwargs)
        self.agent_id = agent_id


class SwarmError(SophiaException):
    """Base class for swarm-related errors."""

    def __init__(self, swarm_id: str, message: str, **kwargs):
        full_message = f"Swarm {swarm_id}: {message}"
        super().__init__(full_message, error_code="SWARM_ERROR", **kwargs)
        self.swarm_id = swarm_id


class CoordinationError(SwarmError):
    """Raised when swarm coordination fails."""

    def __init__(self, swarm_id: str, reason: str, **kwargs):
        super().__init__(swarm_id, f"Coordination failed: {reason}", **kwargs)


class ValidationError(SophiaException):
    """Raised when input validation fails."""

    def __init__(self, field: str, reason: str, **kwargs):
        message = f"Validation failed for {field}: {reason}"
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)


class CircuitBreakerError(SophiaException):
    """Raised when circuit breaker is open."""

    def __init__(self, service: str, **kwargs):
        message = f"Circuit breaker open for {service}"
        super().__init__(message, error_code="CIRCUIT_BREAKER_OPEN", **kwargs)
        self.service = service
