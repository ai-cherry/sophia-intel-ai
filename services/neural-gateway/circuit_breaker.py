"""
Enhanced Circuit Breaker with configurable thresholds and adaptive behavior
"""

import os
import time
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Optional

from prometheus_client import Counter, Gauge


class CircuitState(IntEnum):
    """Circuit breaker states"""
    CLOSED = 0
    OPEN = 1
    HALF_OPEN = 2


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    
    def __init__(self):
        # Load from environment with defaults
        self.failure_threshold = int(os.getenv("CB_FAILURE_THRESHOLD", "3"))
        self.success_threshold = int(os.getenv("CB_SUCCESS_THRESHOLD", "2"))
        self.timeout_seconds = float(os.getenv("CB_TIMEOUT_SECONDS", "10"))
        self.half_open_max_requests = int(os.getenv("CB_HALF_OPEN_MAX", "1"))
        self.failure_rate_threshold = float(os.getenv("CB_FAILURE_RATE", "0.5"))
        self.window_size = int(os.getenv("CB_WINDOW_SIZE", "10"))
        
    def should_open(self, failures: int, total: int) -> bool:
        """Determine if circuit should open based on failures"""
        if total == 0:
            return False
            
        # Check absolute threshold
        if failures >= self.failure_threshold:
            return True
            
        # Check failure rate if we have enough samples
        if total >= self.window_size:
            failure_rate = failures / total
            return failure_rate >= self.failure_rate_threshold
            
        return False


class EnhancedCircuitBreaker:
    """
    Enhanced circuit breaker with adaptive thresholds and monitoring
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.total_requests = 0
        self.last_failure_time = 0.0
        self.opened_at = 0.0
        self.half_open_requests = 0
        
        # Request history for sliding window
        self.request_history: list[tuple[float, bool]] = []  # (timestamp, success)
        
        # Metrics
        self.state_gauge = Gauge(
            f'circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=open, 2=half_open)',
            ['name']
        )
        self.open_counter = Counter(
            f'circuit_breaker_opened_total',
            'Times circuit opened',
            ['name']
        )
        self.failure_counter = Counter(
            f'circuit_breaker_failures_total',
            'Failures recorded',
            ['name']
        )
        self.success_counter = Counter(
            f'circuit_breaker_successes_total',
            'Successes recorded',
            ['name']
        )
        
        # Initialize metrics
        self.state_gauge.labels(name=self.name).set(0)
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        # Check and update state
        self._update_state()
        
        if self.state == CircuitState.OPEN:
            raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_requests >= self.config.half_open_max_requests:
                raise Exception(f"Circuit breaker '{self.name}' is HALF_OPEN (max requests reached)")
            self.half_open_requests += 1
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    async def async_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        # Check and update state
        self._update_state()
        
        if self.state == CircuitState.OPEN:
            raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_requests >= self.config.half_open_max_requests:
                raise Exception(f"Circuit breaker '{self.name}' is HALF_OPEN (max requests reached)")
            self.half_open_requests += 1
        
        # Execute async function
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def _update_state(self):
        """Update circuit breaker state based on current conditions"""
        now = time.time()
        
        # Clean old history entries
        self._clean_history(now)
        
        # Check state transitions
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed for half-open transition
            if now - self.opened_at >= self.config.timeout_seconds:
                self._transition_to_half_open()
                
        elif self.state == CircuitState.CLOSED:
            # Check if we should open
            recent_failures = self._count_recent_failures()
            recent_total = len(self.request_history)
            
            if self.config.should_open(recent_failures, recent_total):
                self._transition_to_open()
    
    def _record_success(self):
        """Record successful execution"""
        now = time.time()
        self.successes += 1
        self.total_requests += 1
        self.request_history.append((now, True))
        self.success_counter.labels(name=self.name).inc()
        
        # Handle state transitions on success
        if self.state == CircuitState.HALF_OPEN:
            # Check if we have enough successes to close
            recent_successes = sum(1 for _, success in self.request_history[-self.config.success_threshold:] if success)
            if recent_successes >= self.config.success_threshold:
                self._transition_to_closed()
    
    def _record_failure(self):
        """Record failed execution"""
        now = time.time()
        self.failures += 1
        self.total_requests += 1
        self.last_failure_time = now
        self.request_history.append((now, False))
        self.failure_counter.labels(name=self.name).inc()
        
        # Handle state transitions on failure
        if self.state == CircuitState.HALF_OPEN:
            # Single failure in half-open returns to open
            self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.opened_at = time.time()
        self.half_open_requests = 0
        self.state_gauge.labels(name=self.name).set(1)
        self.open_counter.labels(name=self.name).inc()
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.half_open_requests = 0
        self.failures = 0  # Reset failure count for testing
        self.state_gauge.labels(name=self.name).set(2)
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.half_open_requests = 0
        self.state_gauge.labels(name=self.name).set(0)
    
    def _clean_history(self, now: float):
        """Remove old entries from request history"""
        cutoff = now - (self.config.window_size * 2)  # Keep 2x window for analysis
        self.request_history = [(t, s) for t, s in self.request_history if t > cutoff]
    
    def _count_recent_failures(self) -> int:
        """Count failures in recent window"""
        if not self.request_history:
            return 0
        
        # Count failures in last N requests
        window = self.request_history[-self.config.window_size:]
        return sum(1 for _, success in window if not success)
    
    def get_stats(self) -> dict:
        """Get current circuit breaker statistics"""
        recent_failures = self._count_recent_failures()
        recent_total = min(len(self.request_history), self.config.window_size)
        failure_rate = recent_failures / recent_total if recent_total > 0 else 0
        
        return {
            "name": self.name,
            "state": self.state.name,
            "total_requests": self.total_requests,
            "total_failures": self.failures,
            "total_successes": self.successes,
            "recent_failures": recent_failures,
            "recent_total": recent_total,
            "failure_rate": failure_rate,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "failure_rate_threshold": self.config.failure_rate_threshold
            }
        }
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.total_requests = 0
        self.last_failure_time = 0.0
        self.opened_at = 0.0
        self.half_open_requests = 0
        self.request_history.clear()
        self.state_gauge.labels(name=self.name).set(0)