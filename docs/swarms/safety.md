---
title: Swarm Safety Boundaries
type: reference
status: active
version: 1.0.0
last_updated: 2025-09-01
ai_context: high
tags: [swarms, safety, constraints, boundaries]
---

# 🛡️ Swarm Safety Boundaries

This document defines the safety boundaries and constraints for all agent swarms in Sophia Intel AI, following Anthropic's safety patterns and industry best practices.

## 🎯 Purpose

Ensure all agent swarms operate safely within defined boundaries, preventing unintended behaviors, resource exhaustion, and security vulnerabilities.

## 📋 Prerequisites

- Understanding of agent definitions in `agents.yaml`
- Familiarity with orchestration standards
- Knowledge of system security requirements

## 🔒 Core Safety Principles

### 1. Defense in Depth

Multiple layers of safety checks at different levels:

- Agent level
- Swarm level
- Orchestrator level
- System level

### 2. Fail-Safe Defaults

When in doubt, agents default to the safest action:

- No code execution without explicit approval
- No external API calls without validation
- No sensitive data exposure
- Conservative resource usage

### 3. Least Privilege

Agents only have the minimum permissions required:

- Read-only access by default
- Write access requires justification
- Execution rights are exceptional

## 🛡️ Safety Boundary Implementation

### Agent-Level Boundaries

```python
from typing import List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class SafetyLevel(Enum):
    CRITICAL = "critical"  # Highest restrictions
    HIGH = "high"         # Strong restrictions
    MEDIUM = "medium"     # Balanced restrictions
    LOW = "low"          # Minimal restrictions

@dataclass
class SafetyBoundary:
    """Define safety constraints for an agent"""

    # Resource limits
    max_tokens: int = 4000
    max_execution_time: int = 30  # seconds
    max_memory_mb: int = 512
    max_api_calls: int = 10

    # Operational constraints
    no_code_execution: bool = True
    no_file_system_write: bool = True
    no_external_api: bool = False
    no_sensitive_data: bool = True

    # Rate limiting
    max_requests_per_minute: int = 60
    max_tokens_per_minute: int = 100000

    # Output validation
    require_output_validation: bool = True
    max_output_length: int = 10000
    allowed_output_formats: List[str] = None

    def __post_init__(self):
        if self.allowed_output_formats is None:
            self.allowed_output_formats = ["text", "json", "markdown"]

class AgentSafetyValidator:
    """Validate agent actions against safety boundaries"""

    def __init__(self, boundary: SafetyBoundary):
        self.boundary = boundary
        self.violation_count = 0
        self.violations = []

    def validate_action(self, action: Any) -> bool:
        """Validate an agent action against boundaries"""
        violations = []

        # Check code execution
        if self.boundary.no_code_execution and self._contains_code_execution(action):
            violations.append("Code execution attempted")

        # Check file system access
        if self.boundary.no_file_system_write and self._contains_file_write(action):
            violations.append("File system write attempted")

        # Check external API calls
        if self.boundary.no_external_api and self._contains_external_api(action):
            violations.append("External API call attempted")

        # Check sensitive data
        if self.boundary.no_sensitive_data and self._contains_sensitive_data(action):
            violations.append("Sensitive data exposure detected")

        if violations:
            self.violation_count += len(violations)
            self.violations.extend(violations)
            return False

        return True

    def _contains_code_execution(self, action: Any) -> bool:
        """Check if action contains code execution"""
        dangerous_patterns = [
            "exec(", "eval(", "__import__",
            "subprocess", "os.system", "compile("
        ]
        action_str = str(action)
        return any(pattern in action_str for pattern in dangerous_patterns)

    def _contains_file_write(self, action: Any) -> bool:
        """Check if action contains file system writes"""
        write_patterns = [
            "open(", "write(", "w'", 'w"',
            "mkdir", "rmdir", "remove", "unlink"
        ]
        action_str = str(action)
        return any(pattern in action_str for pattern in write_patterns)

    def _contains_external_api(self, action: Any) -> bool:
        """Check if action contains external API calls"""
        api_patterns = [
            "requests.", "urllib", "http://", "https://",
            "api.", "webhook", "POST", "GET"
        ]
        action_str = str(action)
        return any(pattern in action_str for pattern in api_patterns)

    def _contains_sensitive_data(self, action: Any) -> bool:
        """Check if action contains sensitive data patterns"""
        sensitive_patterns = [
            r"[A-Za-z0-9+/]{40,}",  # API keys
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{16}\b",  # Credit card
            "password", "secret", "token", "key"
        ]
        action_str = str(action).lower()
        return any(pattern in action_str for pattern in sensitive_patterns)
```

### Swarm-Level Safety

```python
class SwarmSafetyBoundary:
    """Safety boundaries for entire swarms"""

    def __init__(self):
        self.constraints = {
            # Swarm composition limits
            "max_agents": 50,
            "max_concurrent_agents": 10,
            "max_nested_depth": 3,

            # Resource pooling
            "max_total_tokens": 1000000,
            "max_total_memory_gb": 4,
            "max_execution_time_minutes": 10,

            # Consensus requirements
            "min_consensus_for_critical": 0.9,
            "min_consensus_for_high": 0.7,
            "min_consensus_for_medium": 0.5,

            # Circuit breaker thresholds
            "max_consecutive_failures": 3,
            "failure_rate_threshold": 0.5,
            "circuit_breaker_timeout": 60
        }

    def validate_swarm_composition(self, agents: List[Agent]) -> bool:
        """Validate swarm composition against boundaries"""
        if len(agents) > self.constraints["max_agents"]:
            raise SwarmSafetyViolation(
                f"Swarm exceeds max agents: {len(agents)} > {self.constraints['max_agents']}"
            )

        # Check for circular dependencies
        if self._has_circular_dependencies(agents):
            raise SwarmSafetyViolation("Circular dependencies detected in swarm")

        # Validate agent compatibility
        if not self._agents_compatible(agents):
            raise SwarmSafetyViolation("Incompatible agents in swarm")

        return True

    def _has_circular_dependencies(self, agents: List[Agent]) -> bool:
        """Check for circular dependencies in agent handoffs"""
        # Build dependency graph
        graph = {}
        for agent in agents:
            graph[agent.id] = agent.handoff_agents

        # DFS to detect cycles
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True

        return False
```

### Output Validation

```python
class OutputValidator:
    """Validate agent outputs for safety"""

    def __init__(self):
        self.validators = [
            self.validate_no_code_injection,
            self.validate_no_sensitive_data,
            self.validate_format_compliance,
            self.validate_length_limits,
            self.validate_content_appropriateness
        ]

    def validate(self, output: Any, boundary: SafetyBoundary) -> bool:
        """Run all validators on output"""
        for validator in self.validators:
            if not validator(output, boundary):
                return False
        return True

    def validate_no_code_injection(self, output: Any, boundary: SafetyBoundary) -> bool:
        """Check for code injection attempts"""
        if not boundary.no_code_execution:
            return True

        dangerous_patterns = [
            "<script", "javascript:", "onclick=",
            "onerror=", "eval(", "exec("
        ]
        output_str = str(output).lower()
        return not any(pattern in output_str for pattern in dangerous_patterns)

    def validate_no_sensitive_data(self, output: Any, boundary: SafetyBoundary) -> bool:
        """Check for sensitive data in output"""
        if not boundary.no_sensitive_data:
            return True

        # Redact potential sensitive data
        import re
        output_str = str(output)

        # Check for API key patterns
        if re.search(r'[A-Za-z0-9+/]{40,}', output_str):
            return False

        # Check for credit card patterns
        if re.search(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', output_str):
            return False

        return True

    def validate_format_compliance(self, output: Any, boundary: SafetyBoundary) -> bool:
        """Ensure output format compliance"""
        if isinstance(output, dict):
            output_format = "json"
        elif isinstance(output, str):
            if output.startswith("#") or output.startswith("##"):
                output_format = "markdown"
            else:
                output_format = "text"
        else:
            output_format = "unknown"

        return output_format in boundary.allowed_output_formats
```

### Circuit Breaker Pattern

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Blocking calls
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Prevent cascading failures in swarms"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Reset failure count on success"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Increment failure count and open circuit if threshold reached"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
```

### Rate Limiting

```python
import time
from collections import deque

class RateLimiter:
    """Rate limiting for agent actions"""

    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.requests = deque()

    def allow_request(self) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()

        # Remove old requests outside time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()

        # Check if under limit
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True

        return False

    def wait_time(self) -> float:
        """Calculate wait time until next request allowed"""
        if len(self.requests) < self.max_requests:
            return 0

        oldest_request = self.requests[0]
        now = time.time()
        wait = self.time_window - (now - oldest_request)
        return max(0, wait)
```

## 📊 Safety Metrics

```python
class SafetyMetrics:
    """Track safety boundary violations and compliance"""

    def __init__(self):
        self.metrics = {
            "total_validations": 0,
            "violations": 0,
            "violation_types": {},
            "circuit_breaker_trips": 0,
            "rate_limit_hits": 0,
            "safety_score": 1.0
        }

    def record_violation(self, violation_type: str):
        """Record a safety violation"""
        self.metrics["violations"] += 1
        self.metrics["violation_types"][violation_type] = (
            self.metrics["violation_types"].get(violation_type, 0) + 1
        )
        self._update_safety_score()

    def _update_safety_score(self):
        """Update overall safety score"""
        if self.metrics["total_validations"] > 0:
            self.metrics["safety_score"] = 1 - (
                self.metrics["violations"] / self.metrics["total_validations"]
            )
```

## ✅ Validation

To validate safety boundary implementation:

```bash
# Run safety tests
pytest tests/test_safety_boundaries.py

# Check boundary compliance
python scripts/validate_safety.py

# Monitor safety metrics
python scripts/monitor_safety.py
```

## 🚨 Common Issues

1. **Boundary Too Restrictive**: Agents unable to complete tasks
   - Solution: Adjust boundaries based on task requirements
2. **Circular Dependencies**: Agents in infinite handoff loop
   - Solution: Use dependency checker before swarm execution
3. **Rate Limit Exhaustion**: Too many requests in time window
   - Solution: Implement request batching or increase limits

## 📚 Related

- [Orchestration Standards](../../.ai-instructions/orchestration-standards.md)
- [Agent Definitions](agents.yaml)
- [Communication Protocols](protocols.md)
- [Anthropic Safety Guidelines](https://anthropic.com/building-effective-agents)
