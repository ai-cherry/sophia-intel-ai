"""
SOPHIA Performance Monitor
Monitors and tracks performance metrics for models and services.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Callable
import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import json
from contextlib import asynccontextmanager
import aiohttp
from functools import wraps

from .api_manager import SOPHIAAPIManager

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    timestamp: datetime
    service: str
    operation: str
    duration_ms: float
    tokens_used: Optional[int] = None
    success: bool = True
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ServiceStats:
    """Service performance statistics."""
    service: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    average_duration_ms: float
    total_tokens: int
    error_rate: float
    uptime_percentage: float
    last_call: Optional[datetime] = None

class SOPHIAPerformanceMonitor:
    """
    Performance monitoring system for tracking model and service performance.
    Provides metrics collection, analysis, and export capabilities.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.api_manager = SOPHIAAPIManager()
        self.metrics: List[PerformanceMetric] = []
        self.max_metrics = 10000  # Keep last 10k metrics in memory
        
        # Configuration
        self.prometheus_pushgateway_url = os.getenv("PROMETHEUS_PUSHGATEWAY_URL")
        self.arize_api_key = os.getenv("ARIZE_API_KEY")
        self.arize_space_key = os.getenv("ARIZE_SPACE_KEY")
        
        # Service tracking
        self.service_stats: Dict[str, ServiceStats] = {}
        
        logger.info("Initialized SOPHIAPerformanceMonitor")
    
    def monitor_call(self, service: str, operation: str = "default"):
        """
        Decorator to monitor function calls and collect performance metrics.
        
        Args:
            service: Service name (e.g., 'openai', 'anthropic', 'github')
            operation: Operation name (e.g., 'chat_completion', 'create_branch')
        """
        def decorator(func: Callable):
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    return await self._monitor_async_call(service, operation, func, *args, **kwargs)
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    return self._monitor_sync_call(service, operation, func, *args, **kwargs)
                return sync_wrapper
        return decorator
    
    async def _monitor_async_call(self, service: str, operation: str, func: Callable, *args, **kwargs):
        """Monitor an async function call."""
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)
        success = True
        error_type = None
        error_message = None
        tokens_used = None
        
        try:
            result = await func(*args, **kwargs)
            
            # Extract token usage if available
            if isinstance(result, dict):
                if 'usage' in result:
                    tokens_used = result['usage'].get('total_tokens')
                elif 'token_count' in result:
                    tokens_used = result['token_count']
            
            return result
            
        except Exception as e:
            success = False
            error_type = type(e).__name__
            error_message = str(e)
            logger.error(f"Error in {service}.{operation}: {e}")
            raise
            
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            metric = PerformanceMetric(
                timestamp=timestamp,
                service=service,
                operation=operation,
                duration_ms=duration_ms,
                tokens_used=tokens_used,
                success=success,
                error_type=error_type,
                error_message=error_message
            )
            
            await self.log_metric(metric)
    
    def _monitor_sync_call(self, service: str, operation: str, func: Callable, *args, **kwargs):
        """Monitor a sync function call."""
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)
        success = True
        error_type = None
        error_message = None
        tokens_used = None
        
        try:
            result = func(*args, **kwargs)
            
            # Extract token usage if available
            if isinstance(result, dict):
                if 'usage' in result:
                    tokens_used = result['usage'].get('total_tokens')
                elif 'token_count' in result:
                    tokens_used = result['token_count']
            
            return result
            
        except Exception as e:
            success = False
            error_type = type(e).__name__
            error_message = str(e)
            logger.error(f"Error in {service}.{operation}: {e}")
            raise
            
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            metric = PerformanceMetric(
                timestamp=timestamp,
                service=service,
                operation=operation,
                duration_ms=duration_ms,
                tokens_used=tokens_used,
                success=success,
                error_type=error_type,
                error_message=error_message
            )
            
            # Use asyncio to log metric if in async context
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.log_metric(metric))
            except RuntimeError:
                # No event loop, store metric directly
                self._store_metric(metric)
    
    async def log_metric(self, metric: PerformanceMetric):
        """
        Log a performance metric.
        
        Args:
            metric: Performance metric to log
        """
        try:
            self._store_metric(metric)
            self._update_service_stats(metric)
            
            # Send to external monitoring systems
            await self._send_to_prometheus(metric)
            await self._send_to_arize(metric)
            
            logger.debug(f"Logged metric: {metric.service}.{metric.operation} - {metric.duration_ms:.2f}ms")
            
        except Exception as e:
            logger.error(f"Failed to log metric: {e}")
    
    def _store_metric(self, metric: PerformanceMetric):
        """Store metric in memory with rotation."""
        self.metrics.append(metric)
        
        # Rotate metrics if we exceed max size
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
    
    def _update_service_stats(self, metric: PerformanceMetric):
        """Update service statistics with new metric."""
        service = metric.service
        
        if service not in self.service_stats:
            self.service_stats[service] = ServiceStats(
                service=service,
                total_calls=0,
                successful_calls=0,
                failed_calls=0,
                average_duration_ms=0.0,
                total_tokens=0,
                error_rate=0.0,
                uptime_percentage=100.0
            )
        
        stats = self.service_stats[service]
        stats.total_calls += 1
        stats.last_call = metric.timestamp
        
        if metric.success:
            stats.successful_calls += 1
        else:
            stats.failed_calls += 1
        
        if metric.tokens_used:
            stats.total_tokens += metric.tokens_used
        
        # Update average duration (running average)
        stats.average_duration_ms = (
            (stats.average_duration_ms * (stats.total_calls - 1) + metric.duration_ms) / stats.total_calls
        )
        
        # Update error rate
        stats.error_rate = (stats.failed_calls / stats.total_calls) * 100
        
        # Update uptime percentage
        stats.uptime_percentage = (stats.successful_calls / stats.total_calls) * 100
    
    async def _send_to_prometheus(self, metric: PerformanceMetric):
        """Send metric to Prometheus pushgateway."""
        if not self.prometheus_pushgateway_url:
            return
        
        try:
            # Format metric for Prometheus
            prometheus_data = f"""
# HELP sophia_operation_duration_ms Duration of operations in milliseconds
# TYPE sophia_operation_duration_ms histogram
sophia_operation_duration_ms{{service="{metric.service}",operation="{metric.operation}",success="{metric.success}"}} {metric.duration_ms}

# HELP sophia_operation_total Total number of operations
# TYPE sophia_operation_total counter
sophia_operation_total{{service="{metric.service}",operation="{metric.operation}",success="{metric.success}"}} 1
"""
            
            if metric.tokens_used:
                prometheus_data += f"""
# HELP sophia_tokens_used_total Total tokens used
# TYPE sophia_tokens_used_total counter
sophia_tokens_used_total{{service="{metric.service}",operation="{metric.operation}"}} {metric.tokens_used}
"""
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.prometheus_pushgateway_url}/metrics/job/sophia/instance/{metric.service}"
                async with session.post(url, data=prometheus_data) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to send metric to Prometheus: {response.status}")
                        
        except Exception as e:
            logger.warning(f"Failed to send metric to Prometheus: {e}")
    
    async def _send_to_arize(self, metric: PerformanceMetric):
        """Send metric to Arize AI monitoring platform."""
        if not self.arize_api_key or not self.arize_space_key:
            return
        
        try:
            # Format metric for Arize
            arize_data = {
                "space_key": self.arize_space_key,
                "model_id": f"sophia-{metric.service}",
                "model_version": "1.0.0",
                "prediction_id": f"{metric.timestamp.isoformat()}-{metric.service}-{metric.operation}",
                "prediction_timestamp": metric.timestamp.isoformat(),
                "features": {
                    "service": metric.service,
                    "operation": metric.operation,
                    "duration_ms": metric.duration_ms
                },
                "tags": {
                    "success": str(metric.success),
                    "environment": "production"
                }
            }
            
            if metric.tokens_used:
                arize_data["features"]["tokens_used"] = metric.tokens_used
            
            if not metric.success:
                arize_data["tags"]["error_type"] = metric.error_type or "unknown"
            
            headers = {
                "Authorization": f"Bearer {self.arize_api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.arize.com/v1/log",
                    json=arize_data,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to send metric to Arize: {response.status}")
                        
        except Exception as e:
            logger.warning(f"Failed to send metric to Arize: {e}")
    
    def get_service_stats(self, service: Optional[str] = None) -> Dict[str, ServiceStats]:
        """
        Get performance statistics for services.
        
        Args:
            service: Specific service name, or None for all services
            
        Returns:
            Service statistics
        """
        if service:
            return {service: self.service_stats.get(service)} if service in self.service_stats else {}
        return self.service_stats.copy()
    
    def get_metrics(
        self,
        service: Optional[str] = None,
        operation: Optional[str] = None,
        limit: int = 100
    ) -> List[PerformanceMetric]:
        """
        Get performance metrics with optional filtering.
        
        Args:
            service: Filter by service name
            operation: Filter by operation name
            limit: Maximum number of metrics to return
            
        Returns:
            List of performance metrics
        """
        filtered_metrics = self.metrics
        
        if service:
            filtered_metrics = [m for m in filtered_metrics if m.service == service]
        
        if operation:
            filtered_metrics = [m for m in filtered_metrics if m.operation == operation]
        
        # Return most recent metrics first
        return sorted(filtered_metrics, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance summary for the last N hours.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Performance summary
        """
        cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        recent_metrics = [
            m for m in self.metrics 
            if m.timestamp.timestamp() > cutoff_time
        ]
        
        if not recent_metrics:
            return {
                "time_period": f"Last {hours} hours",
                "total_calls": 0,
                "services": {},
                "overall_stats": {}
            }
        
        # Calculate overall stats
        total_calls = len(recent_metrics)
        successful_calls = sum(1 for m in recent_metrics if m.success)
        failed_calls = total_calls - successful_calls
        average_duration = sum(m.duration_ms for m in recent_metrics) / total_calls
        total_tokens = sum(m.tokens_used or 0 for m in recent_metrics)
        
        # Calculate per-service stats
        service_breakdown = {}
        for metric in recent_metrics:
            service = metric.service
            if service not in service_breakdown:
                service_breakdown[service] = {
                    "calls": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_duration": 0,
                    "total_tokens": 0,
                    "operations": set()
                }
            
            stats = service_breakdown[service]
            stats["calls"] += 1
            stats["total_duration"] += metric.duration_ms
            stats["operations"].add(metric.operation)
            
            if metric.success:
                stats["successful"] += 1
            else:
                stats["failed"] += 1
            
            if metric.tokens_used:
                stats["total_tokens"] += metric.tokens_used
        
        # Format service stats
        for service, stats in service_breakdown.items():
            stats["average_duration_ms"] = stats["total_duration"] / stats["calls"]
            stats["error_rate"] = (stats["failed"] / stats["calls"]) * 100
            stats["operations"] = list(stats["operations"])
            del stats["total_duration"]  # Remove intermediate calculation
        
        return {
            "time_period": f"Last {hours} hours",
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": (successful_calls / total_calls) * 100,
            "average_duration_ms": average_duration,
            "total_tokens_used": total_tokens,
            "services": service_breakdown,
            "overall_stats": {
                "fastest_call_ms": min(m.duration_ms for m in recent_metrics),
                "slowest_call_ms": max(m.duration_ms for m in recent_metrics),
                "unique_services": len(service_breakdown),
                "unique_operations": len(set(m.operation for m in recent_metrics))
            }
        }
    
    def export_metrics(self, format: str = "json") -> Dict[str, Any]:
        """
        Export performance metrics for analysis.
        
        Args:
            format: Export format (json, prometheus)
            
        Returns:
            Exported metrics data
        """
        if format == "json":
            return {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_metrics": len(self.metrics),
                "service_stats": {k: asdict(v) for k, v in self.service_stats.items()},
                "recent_metrics": [asdict(m) for m in self.get_metrics(limit=1000)]
            }
        elif format == "prometheus":
            # Generate Prometheus format
            prometheus_data = []
            
            for service, stats in self.service_stats.items():
                prometheus_data.extend([
                    f'sophia_service_total_calls{{service="{service}"}} {stats.total_calls}',
                    f'sophia_service_successful_calls{{service="{service}"}} {stats.successful_calls}',
                    f'sophia_service_failed_calls{{service="{service}"}} {stats.failed_calls}',
                    f'sophia_service_average_duration_ms{{service="{service}"}} {stats.average_duration_ms}',
                    f'sophia_service_total_tokens{{service="{service}"}} {stats.total_tokens}',
                    f'sophia_service_error_rate{{service="{service}"}} {stats.error_rate}',
                    f'sophia_service_uptime_percentage{{service="{service}"}} {stats.uptime_percentage}'
                ])
            
            return {"prometheus_metrics": "\n".join(prometheus_data)}
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    @asynccontextmanager
    async def monitor_operation(self, service: str, operation: str):
        """
        Context manager for monitoring operations.
        
        Usage:
            async with monitor.monitor_operation("openai", "chat_completion"):
                result = await openai_call()
        """
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)
        success = True
        error_type = None
        error_message = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_type = type(e).__name__
            error_message = str(e)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            metric = PerformanceMetric(
                timestamp=timestamp,
                service=service,
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                error_type=error_type,
                error_message=error_message
            )
            
            await self.log_metric(metric)
    
    def clear_metrics(self):
        """Clear all stored metrics (useful for testing)."""
        self.metrics.clear()
        self.service_stats.clear()
        logger.info("Cleared all performance metrics")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of monitored services."""
        health_status = {
            "overall_health": "healthy",
            "services": {},
            "alerts": []
        }
        
        for service, stats in self.service_stats.items():
            service_health = "healthy"
            
            # Check error rate
            if stats.error_rate > 10:
                service_health = "degraded"
                health_status["alerts"].append(f"{service} has high error rate: {stats.error_rate:.1f}%")
            
            if stats.error_rate > 25:
                service_health = "unhealthy"
            
            # Check average response time
            if stats.average_duration_ms > 5000:  # 5 seconds
                service_health = "degraded"
                health_status["alerts"].append(f"{service} has slow response time: {stats.average_duration_ms:.0f}ms")
            
            health_status["services"][service] = {
                "status": service_health,
                "error_rate": stats.error_rate,
                "average_duration_ms": stats.average_duration_ms,
                "uptime_percentage": stats.uptime_percentage,
                "last_call": stats.last_call.isoformat() if stats.last_call else None
            }
        
        # Determine overall health
        service_statuses = [s["status"] for s in health_status["services"].values()]
        if "unhealthy" in service_statuses:
            health_status["overall_health"] = "unhealthy"
        elif "degraded" in service_statuses:
            health_status["overall_health"] = "degraded"
        
        return health_status

