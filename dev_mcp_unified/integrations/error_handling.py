"""
Error Handling and Fallback Strategies for Business Intelligence Integrations

This module provides comprehensive error handling, retry logic, circuit breakers,
and fallback strategies for all BI platform integrations.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, Union, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from contextlib import asynccontextmanager
import json
import httpx
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationStatus(Enum):
    """Integration health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    DOWN = "down"
    MAINTENANCE = "maintenance"

class ErrorType(Enum):
    """Types of integration errors"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"  
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    SERVICE_UNAVAILABLE = "service_unavailable"
    DATA_CORRUPTION = "data_corruption"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_backoff: bool = True
    jitter: bool = True
    
@dataclass 
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: type = Exception

@dataclass
class FallbackConfig:
    """Configuration for fallback strategies"""
    enable_cache: bool = True
    cache_ttl: int = 300  # seconds
    enable_mock_data: bool = True
    enable_degraded_mode: bool = True
    
@dataclass
class IntegrationError:
    """Structured integration error information"""
    error_type: ErrorType
    platform: str
    endpoint: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    retry_after: Optional[int] = None
    recoverable: bool = True
    context: Dict[str, Any] = field(default_factory=dict)

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    def can_execute(self) -> bool:
        """Check if circuit breaker allows execution"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True
    
    def record_success(self):
        """Record successful execution"""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout

class IntegrationCache:
    """Simple in-memory cache for integration responses"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry["expires_at"]:
                logger.info(f"Cache HIT for key: {key}")
                return entry["data"]
            else:
                del self.cache[key]
                logger.info(f"Cache EXPIRED for key: {key}")
        return None
    
    def set(self, key: str, data: Any, ttl: int = 300):
        """Set cached value with TTL"""
        self.cache[key] = {
            "data": data,
            "expires_at": time.time() + ttl,
            "cached_at": time.time()
        }
        logger.info(f"Cache SET for key: {key}, TTL: {ttl}s")
    
    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()
        logger.info("Cache cleared")

class BIIntegrationErrorHandler:
    """Main error handling and fallback coordinator"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.cache = IntegrationCache()
        self.error_history: List[IntegrationError] = []
        self.platform_status: Dict[str, IntegrationStatus] = {}
        
        # Default configurations
        self.default_retry_config = RetryConfig()
        self.default_circuit_config = CircuitBreakerConfig()
        self.default_fallback_config = FallbackConfig()
    
    def get_circuit_breaker(self, platform: str) -> CircuitBreaker:
        """Get or create circuit breaker for platform"""
        if platform not in self.circuit_breakers:
            self.circuit_breakers[platform] = CircuitBreaker(self.default_circuit_config)
        return self.circuit_breakers[platform]
    
    def classify_error(self, exception: Exception, response: Optional[httpx.Response] = None) -> ErrorType:
        """Classify error type based on exception and response"""
        
        # HTTP status code based classification
        if response:
            status_code = response.status_code
            if status_code == 401:
                return ErrorType.AUTHENTICATION
            elif status_code == 403:
                return ErrorType.AUTHORIZATION
            elif status_code == 429:
                return ErrorType.RATE_LIMIT
            elif status_code >= 500:
                return ErrorType.SERVICE_UNAVAILABLE
        
        # Exception type based classification
        if isinstance(exception, httpx.TimeoutException):
            return ErrorType.TIMEOUT
        elif isinstance(exception, httpx.ConnectError):
            return ErrorType.CONNECTION
        elif isinstance(exception, httpx.HTTPStatusError):
            if exception.response.status_code == 429:
                return ErrorType.RATE_LIMIT
            elif exception.response.status_code >= 500:
                return ErrorType.SERVICE_UNAVAILABLE
        elif isinstance(exception, (json.JSONDecodeError, ValueError)):
            return ErrorType.DATA_CORRUPTION
        
        return ErrorType.UNKNOWN
    
    def create_error(self, error_type: ErrorType, platform: str, endpoint: str, 
                    message: str, response: Optional[httpx.Response] = None) -> IntegrationError:
        """Create structured integration error"""
        
        retry_after = None
        if response and "retry-after" in response.headers:
            try:
                retry_after = int(response.headers["retry-after"])
            except ValueError:
                pass
        
        recoverable = error_type not in [ErrorType.AUTHENTICATION, ErrorType.AUTHORIZATION, ErrorType.CONFIGURATION]
        
        context = {}
        if response:
            context["status_code"] = response.status_code
            context["response_headers"] = dict(response.headers)
        
        return IntegrationError(
            error_type=error_type,
            platform=platform,
            endpoint=endpoint, 
            message=message,
            retry_after=retry_after,
            recoverable=recoverable,
            context=context
        )
    
    def record_error(self, error: IntegrationError):
        """Record error in history and update platform status"""
        self.error_history.append(error)
        
        # Keep only recent errors (last 100)
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
        
        # Update platform status
        self._update_platform_status(error.platform)
        
        # Record failure in circuit breaker
        circuit_breaker = self.get_circuit_breaker(error.platform)
        circuit_breaker.record_failure()
        
        logger.error(f"Integration error recorded: {error.platform} - {error.error_type.value} - {error.message}")
    
    def _update_platform_status(self, platform: str):
        """Update platform status based on recent errors"""
        recent_errors = [e for e in self.error_history 
                        if e.platform == platform and 
                        e.timestamp > datetime.now() - timedelta(minutes=10)]
        
        if len(recent_errors) >= 5:
            self.platform_status[platform] = IntegrationStatus.DOWN
        elif len(recent_errors) >= 2:
            self.platform_status[platform] = IntegrationStatus.DEGRADED
        else:
            self.platform_status[platform] = IntegrationStatus.HEALTHY
    
    def should_retry(self, error: IntegrationError, attempt: int, config: RetryConfig) -> bool:
        """Determine if operation should be retried"""
        
        if attempt >= config.max_attempts:
            return False
        
        if not error.recoverable:
            return False
        
        # Don't retry authentication/authorization errors
        if error.error_type in [ErrorType.AUTHENTICATION, ErrorType.AUTHORIZATION]:
            return False
        
        # Respect retry-after header for rate limits
        if error.error_type == ErrorType.RATE_LIMIT and error.retry_after:
            return error.retry_after < 300  # Only retry if less than 5 minutes
        
        return True
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay before next retry attempt"""
        
        if config.exponential_backoff:
            delay = min(config.base_delay * (2 ** attempt), config.max_delay)
        else:
            delay = config.base_delay
        
        # Add jitter to prevent thundering herd
        if config.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    async def with_retry(self, func: Callable, platform: str, endpoint: str,
                        retry_config: Optional[RetryConfig] = None,
                        fallback_config: Optional[FallbackConfig] = None) -> Any:
        """Execute function with retry logic and fallbacks"""
        
        retry_config = retry_config or self.default_retry_config
        fallback_config = fallback_config or self.default_fallback_config
        
        circuit_breaker = self.get_circuit_breaker(platform)
        
        # Check circuit breaker
        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker OPEN for {platform}, trying fallback")
            return await self._execute_fallback(platform, endpoint, fallback_config)
        
        # Try cache first
        cache_key = f"{platform}:{endpoint}"
        if fallback_config.enable_cache:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        last_error = None
        
        for attempt in range(retry_config.max_attempts):
            try:
                result = await func()
                
                # Record success
                circuit_breaker.record_success()
                
                # Cache successful result
                if fallback_config.enable_cache:
                    self.cache.set(cache_key, result, fallback_config.cache_ttl)
                
                return result
                
            except Exception as e:
                # Classify and create error
                error_type = self.classify_error(e, getattr(e, 'response', None))
                error = self.create_error(error_type, platform, endpoint, str(e), getattr(e, 'response', None))
                last_error = error
                
                # Record error
                self.record_error(error)
                
                # Check if should retry
                if not self.should_retry(error, attempt, retry_config):
                    logger.error(f"Not retrying {platform}/{endpoint}: {error.error_type.value}")
                    break
                
                # Calculate delay
                delay = self.calculate_delay(attempt, retry_config)
                
                # Handle rate limiting with retry-after
                if error.error_type == ErrorType.RATE_LIMIT and error.retry_after:
                    delay = min(error.retry_after, 300)  # Cap at 5 minutes
                
                logger.info(f"Retrying {platform}/{endpoint} in {delay:.2f}s (attempt {attempt + 1}/{retry_config.max_attempts})")
                await asyncio.sleep(delay)
        
        # All retries exhausted, try fallback
        logger.error(f"All retries exhausted for {platform}/{endpoint}, trying fallback")
        return await self._execute_fallback(platform, endpoint, fallback_config, last_error)
    
    async def _execute_fallback(self, platform: str, endpoint: str, 
                               fallback_config: FallbackConfig,
                               error: Optional[IntegrationError] = None) -> Any:
        """Execute fallback strategy when main integration fails"""
        
        # Try cache even if expired (stale data is better than no data)
        if fallback_config.enable_cache:
            cache_key = f"{platform}:{endpoint}"
            if cache_key in self.cache.cache:
                logger.info(f"Using stale cache data for {platform}/{endpoint}")
                return self.cache.cache[cache_key]["data"]
        
        # Use mock data if enabled
        if fallback_config.enable_mock_data:
            logger.info(f"Using mock data for {platform}/{endpoint}")
            return await self._get_mock_data(platform, endpoint)
        
        # Degraded mode - return minimal/empty response
        if fallback_config.enable_degraded_mode:
            logger.info(f"Using degraded mode for {platform}/{endpoint}")
            return self._get_degraded_response(platform, endpoint)
        
        # All fallbacks exhausted
        raise Exception(f"All fallback strategies exhausted for {platform}/{endpoint}: {error.message if error else 'Unknown error'}")
    
    async def _get_mock_data(self, platform: str, endpoint: str) -> Dict[str, Any]:
        """Get mock data for fallback"""
        # Import mock data generator
        try:
            from tests.integration.business_intelligence.mock_data_generator import BIMockDataGenerator, MockDataConfig
            
            generator = BIMockDataGenerator()
            
            # Map endpoints to mock data types
            endpoint_mapping = {
                "/business/gong/recent": ("gong", "calls"),
                "/api/business/crm/contacts": ("hubspot", "contacts"),
                "/api/business/crm/pipeline": ("hubspot", "pipeline"),
                "/api/business/calls/recent": ("gong", "calls"),
                "/api/business/projects/overview": ("asana", "projects"),
                "/api/business/dashboard": ("dashboard", "overview")
            }
            
            if endpoint in endpoint_mapping:
                platform_type, data_type = endpoint_mapping[endpoint]
                config = MockDataConfig(platform=platform_type, scenario="success", record_count=10)
                return generator.generate_mock_data(platform_type, data_type, config)
            
        except ImportError:
            logger.warning("Mock data generator not available")
        
        return {"error": "Fallback mock data not available", "platform": platform, "endpoint": endpoint}
    
    def _get_degraded_response(self, platform: str, endpoint: str) -> Dict[str, Any]:
        """Get minimal response for degraded mode"""
        
        degraded_responses = {
            "/business/gong/recent": {"fromDate": datetime.now().strftime("%Y-%m-%d"), "count": 0, "calls": []},
            "/api/business/crm/contacts": {"contacts": [], "count": 0, "ai_summary": {}},
            "/api/business/crm/pipeline": {"pipeline": [], "ai_insights": {}},
            "/api/business/calls/recent": {"calls": [], "ai_summary": {}},
            "/api/business/projects/overview": {"projects": [], "ai_summary": {}},
            "/api/business/dashboard": {
                "overview": {"leads_this_week": 0, "deals_in_pipeline": 0, "active_projects": 0},
                "ai_insights": {"revenue_forecast": 0},
                "recommended_actions": [],
                "agent_performance": {"total_deployments": 0, "success_rate": 0.0}
            }
        }
        
        return degraded_responses.get(endpoint, {
            "error": "Service temporarily unavailable",
            "platform": platform,
            "status": "degraded",
            "message": "Using degraded mode with minimal data"
        })
    
    # ==============================================================================
    # MONITORING AND REPORTING
    # ==============================================================================
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours"""
        
        since = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_history if e.timestamp > since]
        
        # Group by platform
        by_platform = {}
        for error in recent_errors:
            if error.platform not in by_platform:
                by_platform[error.platform] = []
            by_platform[error.platform].append(error)
        
        # Group by error type
        by_type = {}
        for error in recent_errors:
            error_type = error.error_type.value
            if error_type not in by_type:
                by_type[error_type] = 0
            by_type[error_type] += 1
        
        return {
            "time_window_hours": hours,
            "total_errors": len(recent_errors),
            "by_platform": {platform: len(errors) for platform, errors in by_platform.items()},
            "by_type": by_type,
            "platform_status": {platform: status.value for platform, status in self.platform_status.items()},
            "circuit_breaker_status": {
                platform: {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "last_failure": cb.last_failure_time
                }
                for platform, cb in self.circuit_breakers.items()
            }
        }
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self._calculate_overall_health(),
            "platform_status": {platform: status.value for platform, status in self.platform_status.items()},
            "error_summary": self.get_error_summary(),
            "cache_stats": {
                "total_entries": len(self.cache.cache),
                "cache_keys": list(self.cache.cache.keys())
            },
            "circuit_breakers": {
                platform: {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "can_execute": cb.can_execute()
                }
                for platform, cb in self.circuit_breakers.items()
            }
        }
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall system health"""
        if not self.platform_status:
            return "unknown"
        
        statuses = list(self.platform_status.values())
        
        if all(s == IntegrationStatus.HEALTHY for s in statuses):
            return "healthy"
        elif any(s == IntegrationStatus.DOWN for s in statuses):
            return "critical"
        elif any(s == IntegrationStatus.DEGRADED for s in statuses):
            return "degraded"
        else:
            return "healthy"

# ==============================================================================
# DECORATORS AND UTILITIES
# ==============================================================================

def with_integration_error_handling(platform: str, endpoint: str = "", 
                                   retry_config: Optional[RetryConfig] = None,
                                   fallback_config: Optional[FallbackConfig] = None):
    """Decorator for automatic error handling on integration functions"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            handler = BIIntegrationErrorHandler()
            
            async def execute():
                return await func(*args, **kwargs)
            
            return await handler.with_retry(execute, platform, endpoint, retry_config, fallback_config)
        
        return wrapper
    return decorator

# Global error handler instance
global_error_handler = BIIntegrationErrorHandler()

# ==============================================================================
# USAGE EXAMPLE
# ==============================================================================

async def example_integration_with_error_handling():
    """Example of how to use the error handling system"""
    
    @with_integration_error_handling("gong", "/business/gong/recent")
    async def get_gong_calls():
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:3333/business/gong/recent")
            response.raise_for_status()
            return response.json()
    
    try:
        result = await get_gong_calls()
        print("Success:", result)
    except Exception as e:
        print("Final error:", e)
    
    # Check health
    health = global_error_handler.get_health_report()
    print("Health report:", json.dumps(health, indent=2))

if __name__ == "__main__":
    asyncio.run(example_integration_with_error_handling())