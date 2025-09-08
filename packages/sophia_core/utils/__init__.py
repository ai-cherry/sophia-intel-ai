"""
Utilities Module

Provides utility functions and classes for reliability, resilience, and data protection
including retry mechanisms, circuit breakers, and sensitive data redaction.
"""

from .cbreaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerState,
    async_circuit_breaker,
    circuit_breaker,
)
from .redaction import (
    DataRedactor,
    RedactionConfig,
    RedactionRule,
    SensitivePattern,
    create_redaction_patterns,
    is_sensitive_field,
    redact_dict,
    redact_json,
    redact_text,
)
from .retry import (
    ExponentialBackoff,
    FixedDelay,
    LinearBackoff,
    NonRetryableError,
    RetryableError,
    RetryConfig,
    RetryContext,
    RetryStrategy,
    async_retry,
    retry,
)

__all__ = [
    # Retry mechanisms
    "RetryConfig",
    "RetryStrategy",
    "ExponentialBackoff",
    "LinearBackoff",
    "FixedDelay",
    "RetryableError",
    "NonRetryableError",
    "retry",
    "async_retry",
    "RetryContext",
    # Circuit breakers
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "circuit_breaker",
    "async_circuit_breaker",
    # Data redaction
    "RedactionConfig",
    "SensitivePattern",
    "RedactionRule",
    "DataRedactor",
    "redact_text",
    "redact_dict",
    "redact_json",
    "create_redaction_patterns",
    "is_sensitive_field",
]
