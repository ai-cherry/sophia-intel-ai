# ADR-002: Circuit Breaker Pattern for External Service Calls

## Status

Accepted

## Context

The AI Orchestra system integrates with multiple external services (Orchestra Manager, Memory System, Swarm Intelligence). These services can fail or become slow, potentially causing:

- Cascade failures throughout the system
- Resource exhaustion from pending requests
- Poor user experience from long timeouts
- Difficulty identifying root cause of failures

## Decision

We will implement the Circuit Breaker pattern for all external service calls with the following states:

- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Service is failing, requests fail immediately
- **HALF-OPEN**: Testing if service has recovered

Configuration:

- Failure threshold: 5 failures within 60 seconds
- Timeout duration: 30 seconds in OPEN state
- Success threshold: 3 consecutive successes to close circuit

## Consequences

### Positive

- **Fail Fast**: Immediate failure response when service is down
- **Resource Protection**: Prevents resource exhaustion from pending requests
- **System Resilience**: Prevents cascade failures
- **Recovery Detection**: Automatic detection when service recovers
- **Observability**: Clear metrics on service health

### Negative

- **Complexity**: Additional state management
- **False Positives**: May open circuit on temporary issues
- **Configuration**: Requires tuning thresholds per service

## Implementation

```python
class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5):
        self.name = name
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None

    async def call(self, func: Callable):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF-OPEN"
            else:
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")

        try:
            result = await func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

## Monitoring

- Metrics: circuit_breaker_state, circuit_breaker_failures, circuit_breaker_successes
- Alerts: Circuit opened, Circuit recovery failed
- Dashboard: Real-time circuit state visualization

## References

- Michael Nygard's "Release It!" - Circuit Breaker pattern
- Netflix Hystrix documentation
- Martin Fowler's Circuit Breaker article
