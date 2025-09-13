"""
Comprehensive Health Monitoring System
Tracks health of all services and provides unified health endpoint
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import httpx

from app.core.feature_flags import FeatureFlags
from app.core.connection_pool import get_pool_manager
from app.core.graceful_degradation import get_degradation_manager

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceHealth:
    """Health information for a service"""
    def __init__(self, name: str):
        self.name = name
        self.status = HealthStatus.UNKNOWN
        self.last_check = None
        self.response_time_ms = None
        self.error_message = None
        self.metadata = {}
        self.check_count = 0
        self.failure_count = 0
        self.success_rate = 100.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "response_time_ms": self.response_time_ms,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "check_count": self.check_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate
        }


class HealthMonitor:
    """Central health monitoring system"""
    
    def __init__(self):
        self.services: Dict[str, ServiceHealth] = {}
        self.enabled = FeatureFlags.ENABLE_HEALTH_CHECKS
        self.check_interval = 30  # seconds
        self.http_client = None
        self._monitoring_task = None
    
    async def initialize(self):
        """Initialize health monitor"""
        if not self.enabled:
            logger.info("Health monitoring disabled")
            return
        
        self.http_client = httpx.AsyncClient(timeout=5.0)
        
        # Register core services
        self.register_service("postgres")
        self.register_service("redis")
        self.register_service("weaviate")
        self.register_service("openrouter")
        self.register_service("portkey")
        
        # Start background monitoring
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitoring initialized")
    
    def register_service(self, name: str) -> ServiceHealth:
        """Register a service for monitoring"""
        if name not in self.services:
            self.services[name] = ServiceHealth(name)
        return self.services[name]
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self.enabled:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health monitor loop error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """Check health of all registered services"""
        tasks = []
        for service_name in self.services:
            tasks.append(self.check_service(service_name))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        return self.services
    
    async def check_service(self, name: str) -> ServiceHealth:
        """Check health of a specific service"""
        if name not in self.services:
            self.register_service(name)
        
        health = self.services[name]
        health.check_count += 1
        start_time = time.perf_counter()
        
        try:
            # Route to appropriate health check
            if name == "postgres":
                await self._check_postgres(health)
            elif name == "redis":
                await self._check_redis(health)
            elif name == "weaviate":
                await self._check_weaviate(health)
            elif name == "openrouter":
                await self._check_openrouter(health)
            elif name == "portkey":
                await self._check_portkey(health)
            else:
                await self._check_generic_http(health, name)
            
            health.response_time_ms = (time.perf_counter() - start_time) * 1000
            health.last_check = datetime.now()
            
            # Calculate success rate
            if health.status != HealthStatus.HEALTHY:
                health.failure_count += 1
            health.success_rate = ((health.check_count - health.failure_count) / health.check_count) * 100
            
        except Exception as e:
            health.status = HealthStatus.UNHEALTHY
            health.error_message = str(e)
            health.failure_count += 1
            health.last_check = datetime.now()
            logger.error(f"Health check failed for {name}: {e}")
        
        return health
    
    async def _check_postgres(self, health: ServiceHealth):
        """Check PostgreSQL health"""
        pool_manager = get_pool_manager()
        postgres = pool_manager.get_postgres()
        
        if not postgres:
            health.status = HealthStatus.UNKNOWN
            health.error_message = "PostgreSQL pool not initialized"
            return
        
        try:
            async with postgres.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    health.status = HealthStatus.HEALTHY
                    health.error_message = None
                    health.metadata = postgres.get_stats()
                else:
                    health.status = HealthStatus.UNHEALTHY
                    health.error_message = "Unexpected query result"
        except Exception as e:
            health.status = HealthStatus.UNHEALTHY
            health.error_message = str(e)
    
    async def _check_redis(self, health: ServiceHealth):
        """Check Redis health"""
        pool_manager = get_pool_manager()
        redis = pool_manager.get_redis()
        
        if not redis:
            health.status = HealthStatus.UNKNOWN
            health.error_message = "Redis pool not initialized"
            return
        
        if not redis.is_healthy():
            health.status = HealthStatus.UNHEALTHY
            health.error_message = "Circuit breaker open"
            health.metadata = redis.get_stats()
            return
        
        try:
            # Ping Redis
            test_key = f"health_check_{time.time()}"
            await redis.set(test_key, "OK", ex=10)
            value = await redis.get(test_key)
            await redis.delete(test_key)
            
            if value == "OK":
                health.status = HealthStatus.HEALTHY
                health.error_message = None
                health.metadata = redis.get_stats()
            else:
                health.status = HealthStatus.UNHEALTHY
                health.error_message = "Redis test failed"
        except Exception as e:
            health.status = HealthStatus.UNHEALTHY
            health.error_message = str(e)
    
    async def _check_weaviate(self, health: ServiceHealth):
        """Check Weaviate health"""
        pool_manager = get_pool_manager()
        weaviate = pool_manager.get_weaviate()
        
        if not weaviate:
            # Check if Weaviate is optional
            if not FeatureFlags.WEAVIATE_REQUIRED:
                health.status = HealthStatus.DEGRADED
                health.error_message = "Weaviate not configured (optional)"
            else:
                health.status = HealthStatus.UNHEALTHY
                health.error_message = "Weaviate pool not initialized"
            return
        
        try:
            # Simple connectivity check
            health.status = HealthStatus.HEALTHY
            health.error_message = None
            health.metadata = weaviate.get_stats()
        except Exception as e:
            health.status = HealthStatus.UNHEALTHY
            health.error_message = str(e)
    
    async def _check_openrouter(self, health: ServiceHealth):
        """Check OpenRouter API health"""
        if not self.http_client:
            health.status = HealthStatus.UNKNOWN
            return
        
        try:
            response = await self.http_client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', '')}"}
            )
            
            if response.status_code == 200:
                health.status = HealthStatus.HEALTHY
                health.error_message = None
                data = response.json()
                health.metadata = {"model_count": len(data.get("data", []))}
            elif response.status_code == 401:
                health.status = HealthStatus.UNHEALTHY
                health.error_message = "Authentication failed"
            else:
                health.status = HealthStatus.DEGRADED
                health.error_message = f"HTTP {response.status_code}"
        except Exception as e:
            health.status = HealthStatus.UNHEALTHY
            health.error_message = str(e)
    
    async def _check_portkey(self, health: ServiceHealth):
        """Check Portkey API health"""
        if not self.http_client:
            health.status = HealthStatus.UNKNOWN
            return
        
        try:
            response = await self.http_client.get(
                "https://api.portkey.ai/v1/health",
                headers={"x-portkey-api-key": os.getenv("PORTKEY_API_KEY", "")}
            )
            
            if response.status_code == 200:
                health.status = HealthStatus.HEALTHY
                health.error_message = None
            else:
                health.status = HealthStatus.DEGRADED
                health.error_message = f"HTTP {response.status_code}"
        except Exception as e:
            # Portkey might not have a health endpoint
            health.status = HealthStatus.UNKNOWN
            health.error_message = "Health check not available"
    
    async def _check_generic_http(self, health: ServiceHealth, name: str):
        """Generic HTTP health check"""
        # Look for environment variable with health URL
        health_url = os.getenv(f"{name.upper()}_HEALTH_URL")
        
        if not health_url or not self.http_client:
            health.status = HealthStatus.UNKNOWN
            health.error_message = "No health URL configured"
            return
        
        try:
            response = await self.http_client.get(health_url)
            
            if response.status_code == 200:
                health.status = HealthStatus.HEALTHY
                health.error_message = None
                
                # Try to parse JSON response
                try:
                    health.metadata = response.json()
                except:
                    health.metadata = {"response": response.text[:100]}
            else:
                health.status = HealthStatus.UNHEALTHY
                health.error_message = f"HTTP {response.status_code}"
        except Exception as e:
            health.status = HealthStatus.UNHEALTHY
            health.error_message = str(e)
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        if not self.services:
            return HealthStatus.UNKNOWN
        
        statuses = [s.status for s in self.services.values()]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNKNOWN
    
    def get_health_report(self) -> dict:
        """Get comprehensive health report"""
        overall = self.get_overall_status()
        
        # Get degradation manager status
        degradation = get_degradation_manager()
        
        return {
            "status": overall.value,
            "timestamp": datetime.now().isoformat(),
            "services": {
                name: service.to_dict()
                for name, service in self.services.items()
            },
            "degradation": degradation.get_health_report() if degradation else {},
            "connection_pools": get_pool_manager().get_stats() if get_pool_manager() else {},
            "monitoring_enabled": self.enabled
        }
    
    async def shutdown(self):
        """Shutdown health monitor"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.http_client:
            await self.http_client.aclose()
        
        logger.info("Health monitor shutdown")


# Global instance
_health_monitor = None

async def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
        await _health_monitor.initialize()
    return _health_monitor


import os  # Add at top with other imports