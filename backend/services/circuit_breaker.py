"""
Circuit Breaker Implementation for SOPHIA Intel
Real fault tolerance pattern with actual state management and recovery logic
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 60          # Seconds before trying half-open
    success_threshold: int = 3          # Successes to close from half-open
    timeout: float = 30.0               # Request timeout in seconds
    expected_exception: tuple = (Exception,)  # Exceptions that count as failures

@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0

class CircuitBreakerError(Exception):
    """Circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Real circuit breaker implementation with actual state management
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {self.config}")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            self.stats.total_requests += 1
            
            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                else:
                    logger.warning(f"Circuit breaker '{self.name}' is OPEN, blocking request")
                    raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")
        
        # Execute the function
        try:
            # Apply timeout
            result = await asyncio.wait_for(
                self._execute_function(func, *args, **kwargs),
                timeout=self.config.timeout
            )
            
            await self._on_success()
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Circuit breaker '{self.name}' timeout after {self.config.timeout}s")
            await self._on_failure()
            raise
            
        except self.config.expected_exception as e:
            logger.error(f"Circuit breaker '{self.name}' caught expected exception: {e}")
            await self._on_failure()
            raise
            
        except Exception as e:
            logger.error(f"Circuit breaker '{self.name}' caught unexpected exception: {e}")
            await self._on_failure()
            raise
    
    async def _execute_function(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function (async or sync)"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)
    
    async def _on_success(self):
        """Handle successful execution"""
        async with self._lock:
            self.stats.success_count += 1
            self.stats.total_successes += 1
            self.stats.last_success_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.stats.failure_count = 0
                    logger.info(f"Circuit breaker '{self.name}' closed after {self.stats.success_count} successes")
    
    async def _on_failure(self):
        """Handle failed execution"""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.total_failures += 1
            self.stats.last_failure_time = time.time()
            self.stats.success_count = 0  # Reset success count
            
            if (self.state == CircuitState.CLOSED and 
                self.stats.failure_count >= self.config.failure_threshold):
                self.state = CircuitState.OPEN
                logger.error(f"Circuit breaker '{self.name}' opened after {self.stats.failure_count} failures")
            
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.error(f"Circuit breaker '{self.name}' reopened due to failure in HALF_OPEN state")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.stats.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.stats.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_requests": self.stats.total_requests,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "failure_rate": (
                self.stats.total_failures / self.stats.total_requests 
                if self.stats.total_requests > 0 else 0
            ),
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    async def reset(self):
        """Manually reset circuit breaker to closed state"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.stats.failure_count = 0
            self.stats.success_count = 0
            logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")

# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Get or create circuit breaker instance"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]

def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator for circuit breaker protection"""
    def decorator(func):
        cb = get_circuit_breaker(name, config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)
        
        return wrapper
    return decorator

# Pre-configured circuit breakers for SOPHIA Intel services
LAMBDA_LABS_CONFIG = CircuitBreakerConfig(
    failure_threshold=3,
    recovery_timeout=30,
    success_threshold=2,
    timeout=10.0
)

OPENROUTER_CONFIG = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=60,
    success_threshold=3,
    timeout=30.0
)

ELEVENLABS_CONFIG = CircuitBreakerConfig(
    failure_threshold=3,
    recovery_timeout=45,
    success_threshold=2,
    timeout=15.0
)

DATABASE_CONFIG = CircuitBreakerConfig(
    failure_threshold=2,
    recovery_timeout=10,
    success_threshold=1,
    timeout=5.0
)

# Initialize service circuit breakers
lambda_labs_cb = get_circuit_breaker("lambda_labs", LAMBDA_LABS_CONFIG)
openrouter_cb = get_circuit_breaker("openrouter", OPENROUTER_CONFIG)
elevenlabs_cb = get_circuit_breaker("elevenlabs", ELEVENLABS_CONFIG)
database_cb = get_circuit_breaker("database", DATABASE_CONFIG)

def get_all_circuit_breaker_states() -> Dict[str, Dict[str, Any]]:
    """Get states of all circuit breakers"""
    return {name: cb.get_state() for name, cb in _circuit_breakers.items()}

async def reset_all_circuit_breakers():
    """Reset all circuit breakers"""
    for cb in _circuit_breakers.values():
        await cb.reset()
    logger.info("All circuit breakers reset")

