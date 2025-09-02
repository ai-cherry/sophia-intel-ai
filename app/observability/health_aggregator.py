"""
Health Check Aggregator
Aggregates health status from all system components and external services.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import aiohttp
import json
import os

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Health status for a single service."""
    name: str
    status: HealthStatus
    url: Optional[str] = None
    response_time_ms: Optional[float] = None
    last_checked: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "url": self.url,
            "response_time_ms": self.response_time_ms,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


@dataclass
class AggregatedHealth:
    """Aggregated health status for all services."""
    overall_status: HealthStatus
    services: List[ServiceHealth] = field(default_factory=list)
    healthy_count: int = 0
    degraded_count: int = 0
    unhealthy_count: int = 0
    unknown_count: int = 0
    total_services: int = 0
    check_timestamp: datetime = field(default_factory=datetime.now)
    response_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall_status": self.overall_status.value,
            "services": [s.to_dict() for s in self.services],
            "healthy_count": self.healthy_count,
            "degraded_count": self.degraded_count,
            "unhealthy_count": self.unhealthy_count,
            "unknown_count": self.unknown_count,
            "total_services": self.total_services,
            "check_timestamp": self.check_timestamp.isoformat(),
            "response_time_ms": self.response_time_ms
        }


class HealthAggregator:
    """
    Aggregates health checks from multiple services and components.
    Provides a unified view of system health.
    """
    
    def __init__(self):
        self.timeout_seconds = 5.0
        self._last_check: Optional[AggregatedHealth] = None
        self._check_interval = 30  # seconds
        self._running = False
        self._background_task: Optional[asyncio.Task] = None
        
        # Define services to monitor
        self.services = [
            {
                "name": "API Server",
                "url": f"http://localhost:{os.getenv('AGENT_API_PORT', '8003')}/healthz",
                "timeout": 3.0
            },
            {
                "name": "Frontend",
                "url": f"http://localhost:{os.getenv('FRONTEND_PORT', '3000')}",
                "timeout": 3.0
            },
            {
                "name": "Cost Tracking API",
                "url": f"http://localhost:{os.getenv('AGENT_API_PORT', '8003')}/costs/summary",
                "timeout": 5.0
            },
            {
                "name": "Embedding Service",
                "url": f"http://localhost:{os.getenv('AGENT_API_PORT', '8003')}/embeddings/models",
                "timeout": 5.0
            }
        ]
        
        # Add external service checks
        external_services = [
            {
                "name": "OpenRouter API",
                "url": "https://openrouter.ai/api/v1/models",
                "timeout": 10.0,
                "headers": {
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', 'dummy')}",
                    "HTTP-Referer": "https://sophia-intel.ai",
                    "X-Title": "Sophia Intel AI"
                }
            },
            {
                "name": "Portkey Gateway",
                "url": "https://api.portkey.ai/v1/models",
                "timeout": 10.0,
                "headers": {
                    "x-portkey-api-key": os.getenv('PORTKEY_API_KEY', 'dummy'),
                    "x-portkey-provider": "openai"
                }
            }
        ]
        
        # Only add external services if API keys are available
        if os.getenv('OPENROUTER_API_KEY') and os.getenv('OPENROUTER_API_KEY') != 'dummy':
            self.services.extend(external_services)
    
    async def check_service_health(self, service: Dict[str, Any]) -> ServiceHealth:
        """Check health of a single service."""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=service.get('timeout', self.timeout_seconds))
            headers = service.get('headers', {})
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(service['url'], headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    # Parse response if possible
                    metadata = {}
                    try:
                        if response.content_type and 'json' in response.content_type:
                            response_data = await response.json()
                            # Extract useful metadata
                            if isinstance(response_data, dict):
                                if 'status' in response_data:
                                    metadata['service_status'] = response_data['status']
                                if 'version' in response_data:
                                    metadata['version'] = response_data['version']
                                if 'timestamp' in response_data:
                                    metadata['service_timestamp'] = response_data['timestamp']
                    except Exception:
                        pass  # Ignore JSON parsing errors
                    
                    # Determine health status based on response code
                    if response.status == 200:
                        status = HealthStatus.HEALTHY
                        error_message = None
                    elif 200 <= response.status < 400:
                        status = HealthStatus.DEGRADED
                        error_message = f"Non-optimal status code: {response.status}"
                    else:
                        status = HealthStatus.UNHEALTHY
                        error_message = f"HTTP {response.status}: {response.reason}"
                    
                    return ServiceHealth(
                        name=service['name'],
                        status=status,
                        url=service['url'],
                        response_time_ms=response_time,
                        last_checked=datetime.now(),
                        error_message=error_message,
                        metadata=metadata
                    )
                    
        except asyncio.TimeoutError:
            return ServiceHealth(
                name=service['name'],
                status=HealthStatus.UNHEALTHY,
                url=service['url'],
                response_time_ms=(time.time() - start_time) * 1000,
                last_checked=datetime.now(),
                error_message="Request timeout"
            )
        except aiohttp.ClientError as e:
            return ServiceHealth(
                name=service['name'],
                status=HealthStatus.UNHEALTHY,
                url=service['url'],
                response_time_ms=(time.time() - start_time) * 1000,
                last_checked=datetime.now(),
                error_message=f"Connection error: {str(e)}"
            )
        except Exception as e:
            return ServiceHealth(
                name=service['name'],
                status=HealthStatus.UNKNOWN,
                url=service['url'],
                response_time_ms=(time.time() - start_time) * 1000,
                last_checked=datetime.now(),
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _check_system_resources(self) -> List[ServiceHealth]:
        """Check system resource health."""
        resource_checks = []
        
        try:
            import psutil
            
            # CPU usage check
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_status = HealthStatus.HEALTHY
            if cpu_percent > 90:
                cpu_status = HealthStatus.UNHEALTHY
            elif cpu_percent > 70:
                cpu_status = HealthStatus.DEGRADED
            
            resource_checks.append(ServiceHealth(
                name="System CPU",
                status=cpu_status,
                last_checked=datetime.now(),
                metadata={"cpu_percent": cpu_percent}
            ))
            
            # Memory usage check
            memory = psutil.virtual_memory()
            memory_status = HealthStatus.HEALTHY
            if memory.percent > 95:
                memory_status = HealthStatus.UNHEALTHY
            elif memory.percent > 80:
                memory_status = HealthStatus.DEGRADED
            
            resource_checks.append(ServiceHealth(
                name="System Memory",
                status=memory_status,
                last_checked=datetime.now(),
                metadata={
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "memory_total_gb": round(memory.total / (1024**3), 2)
                }
            ))
            
            # Disk usage check
            disk = psutil.disk_usage('/')
            disk_status = HealthStatus.HEALTHY
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 95:
                disk_status = HealthStatus.UNHEALTHY
            elif disk_percent > 85:
                disk_status = HealthStatus.DEGRADED
            
            resource_checks.append(ServiceHealth(
                name="System Disk",
                status=disk_status,
                last_checked=datetime.now(),
                metadata={
                    "disk_percent": round(disk_percent, 1),
                    "disk_free_gb": round(disk.free / (1024**3), 2),
                    "disk_total_gb": round(disk.total / (1024**3), 2)
                }
            ))
            
        except ImportError:
            # psutil not available
            resource_checks.append(ServiceHealth(
                name="System Resources",
                status=HealthStatus.UNKNOWN,
                last_checked=datetime.now(),
                error_message="psutil not available for system monitoring"
            ))
        except Exception as e:
            resource_checks.append(ServiceHealth(
                name="System Resources",
                status=HealthStatus.UNKNOWN,
                last_checked=datetime.now(),
                error_message=f"System check error: {str(e)}"
            ))
        
        return resource_checks
    
    async def aggregate_health(self) -> AggregatedHealth:
        """Perform health checks on all services and aggregate results."""
        start_time = time.time()
        
        # Run service health checks concurrently
        tasks = [self.check_service_health(service) for service in self.services]
        service_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to ServiceHealth objects
        services = []
        for result in service_results:
            if isinstance(result, ServiceHealth):
                services.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Health check error: {result}")
                services.append(ServiceHealth(
                    name="Unknown Service",
                    status=HealthStatus.UNKNOWN,
                    error_message=str(result)
                ))
        
        # Add system resource checks
        system_checks = self._check_system_resources()
        services.extend(system_checks)
        
        # Calculate aggregated metrics
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        for service in services:
            status_counts[service.status] += 1
        
        # Determine overall status
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.DEGRADED] > 0:
            overall_status = HealthStatus.DEGRADED
        elif status_counts[HealthStatus.UNKNOWN] > 0 and status_counts[HealthStatus.HEALTHY] == 0:
            overall_status = HealthStatus.UNKNOWN
        else:
            overall_status = HealthStatus.HEALTHY
        
        total_time = (time.time() - start_time) * 1000
        
        aggregated = AggregatedHealth(
            overall_status=overall_status,
            services=services,
            healthy_count=status_counts[HealthStatus.HEALTHY],
            degraded_count=status_counts[HealthStatus.DEGRADED],
            unhealthy_count=status_counts[HealthStatus.UNHEALTHY],
            unknown_count=status_counts[HealthStatus.UNKNOWN],
            total_services=len(services),
            check_timestamp=datetime.now(),
            response_time_ms=total_time
        )
        
        self._last_check = aggregated
        
        # Log health status changes
        logger.info(
            f"Health check complete: {overall_status.value} "
            f"({status_counts[HealthStatus.HEALTHY]}H/{status_counts[HealthStatus.DEGRADED]}D/"
            f"{status_counts[HealthStatus.UNHEALTHY]}U/{status_counts[HealthStatus.UNKNOWN]}?)"
        )
        
        return aggregated
    
    def get_last_health_check(self) -> Optional[AggregatedHealth]:
        """Get the most recent health check results."""
        return self._last_check
    
    async def start_background_monitoring(self, check_interval: int = 30):
        """Start background health monitoring."""
        self._check_interval = check_interval
        self._running = True
        
        async def monitor_loop():
            while self._running:
                try:
                    await self.aggregate_health()
                    await asyncio.sleep(self._check_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Background health check error: {e}")
                    await asyncio.sleep(self._check_interval)
        
        self._background_task = asyncio.create_task(monitor_loop())
        logger.info(f"Started background health monitoring (interval: {check_interval}s)")
    
    def stop_background_monitoring(self):
        """Stop background health monitoring."""
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            logger.info("Stopped background health monitoring")


# Global singleton instance
_health_aggregator: Optional[HealthAggregator] = None


def get_health_aggregator() -> HealthAggregator:
    """Get or create global health aggregator instance."""
    global _health_aggregator
    if _health_aggregator is None:
        _health_aggregator = HealthAggregator()
    return _health_aggregator