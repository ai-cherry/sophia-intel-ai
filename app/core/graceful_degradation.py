"""
Graceful Degradation Manager
Provides fallback mechanisms for service failures
"""
import asyncio
import logging
from typing import Any, Callable, Optional, TypeVar, Union
from functools import wraps
from datetime import datetime, timedelta

from app.core.feature_flags import FeatureFlags

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceStatus:
    """Track service health status"""
    def __init__(self, name: str):
        self.name = name
        self.is_healthy = True
        self.last_check = datetime.now()
        self.failure_count = 0
        self.last_failure = None
        self.recovery_time = timedelta(seconds=30)
    
    def mark_failure(self):
        """Mark service as failed"""
        self.failure_count += 1
        self.last_failure = datetime.now()
        if self.failure_count >= 3:
            self.is_healthy = False
            logger.warning(f"Service {self.name} marked unhealthy after {self.failure_count} failures")
    
    def mark_success(self):
        """Mark service as successful"""
        self.failure_count = 0
        self.is_healthy = True
    
    def should_retry(self) -> bool:
        """Check if service should be retried"""
        if self.is_healthy:
            return True
        if self.last_failure:
            time_since_failure = datetime.now() - self.last_failure
            if time_since_failure >= self.recovery_time:
                self.is_healthy = True
                self.failure_count = 0
                return True
        return False


class GracefulDegradation:
    """Manage graceful degradation for services"""
    
    def __init__(self):
        self.services = {}
        self.fallback_handlers = {}
        self.enabled = FeatureFlags.GRACEFUL_DEGRADATION
    
    def register_service(self, name: str, fallback: Optional[Callable] = None):
        """Register a service with optional fallback"""
        self.services[name] = ServiceStatus(name)
        if fallback:
            self.fallback_handlers[name] = fallback
    
    def get_service_status(self, name: str) -> ServiceStatus:
        """Get or create service status"""
        if name not in self.services:
            self.services[name] = ServiceStatus(name)
        return self.services[name]
    
    async def execute_with_fallback(
        self,
        service_name: str,
        operation: Callable,
        fallback: Optional[Callable] = None,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with fallback on failure"""
        if not self.enabled:
            # If graceful degradation is disabled, just run the operation
            return await operation(*args, **kwargs) if asyncio.iscoroutinefunction(operation) else operation(*args, **kwargs)
        
        status = self.get_service_status(service_name)
        
        # Check if service should be attempted
        if not status.should_retry():
            logger.info(f"Service {service_name} is in recovery period, using fallback")
            return await self._execute_fallback(service_name, fallback, *args, **kwargs)
        
        try:
            # Try the main operation
            result = await operation(*args, **kwargs) if asyncio.iscoroutinefunction(operation) else operation(*args, **kwargs)
            status.mark_success()
            return result
        except Exception as e:
            logger.error(f"Service {service_name} failed: {e}")
            status.mark_failure()
            return await self._execute_fallback(service_name, fallback, *args, **kwargs)
    
    async def _execute_fallback(self, service_name: str, fallback: Optional[Callable], *args, **kwargs):
        """Execute fallback handler"""
        # Use provided fallback or registered one
        fallback_handler = fallback or self.fallback_handlers.get(service_name)
        
        if fallback_handler:
            logger.info(f"Executing fallback for {service_name}")
            if asyncio.iscoroutinefunction(fallback_handler):
                return await fallback_handler(*args, **kwargs)
            return fallback_handler(*args, **kwargs)
        else:
            logger.warning(f"No fallback available for {service_name}")
            return None
    
    def with_fallback(self, service_name: str, fallback: Optional[Callable] = None):
        """Decorator for adding graceful degradation to functions"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.execute_with_fallback(service_name, func, fallback, *args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(self.execute_with_fallback(service_name, func, fallback, *args, **kwargs))
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        return decorator
    
    def get_health_report(self) -> dict:
        """Get health status of all services"""
        return {
            name: {
                "healthy": status.is_healthy,
                "failure_count": status.failure_count,
                "last_failure": status.last_failure.isoformat() if status.last_failure else None,
                "last_check": status.last_check.isoformat()
            }
            for name, status in self.services.items()
        }


# Global instance
_degradation_manager = None

def get_degradation_manager() -> GracefulDegradation:
    """Get global degradation manager"""
    global _degradation_manager
    if _degradation_manager is None:
        _degradation_manager = GracefulDegradation()
    return _degradation_manager


# Convenience decorators
def with_fallback(service_name: str, fallback: Optional[Callable] = None):
    """Decorator to add graceful degradation to a function"""
    return get_degradation_manager().with_fallback(service_name, fallback)


# Example fallback handlers
def mock_embedding_fallback(texts: list[str], **kwargs) -> list[list[float]]:
    """Generate mock embeddings as fallback"""
    import numpy as np
    logger.warning("Using mock embeddings as fallback")
    return [np.random.randn(768).tolist() for _ in texts]


def cache_only_fallback(query: str, **kwargs) -> list:
    """Return cached results only as fallback"""
    logger.warning(f"Database unavailable, returning cached results for: {query}")
    # Would integrate with Redis cache here
    return []


def empty_response_fallback(**kwargs) -> dict:
    """Return empty but valid response structure"""
    return {
        "data": [],
        "status": "degraded",
        "message": "Service temporarily unavailable, operating in degraded mode"
    }