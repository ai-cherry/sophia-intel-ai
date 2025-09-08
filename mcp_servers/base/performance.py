"\nPerformance optimization utilities for MCP servers\n"

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import psutil

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""

    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: float
    operation: str
    success: bool = True
    error: str | None = None

class PerformanceOptimizer:
    """Performance optimization utilities for MCP servers"""

    def __init__(self, server_name: str):
        self.server_name = server_name
        self.metrics_history: list[PerformanceMetrics] = []
        self.performance_thresholds = {
            "execution_time": 5.0,
            "memory_usage": 500.0,
            "cpu_usage": 80.0,
        }

    def set_thresholds(self, **thresholds):
        """Set performance thresholds"""
        self.performance_thresholds.update(thresholds)

    def get_current_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def get_current_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0

    def record_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics"""
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        self._check_performance_thresholds(metrics)

    def _check_performance_thresholds(self, metrics: PerformanceMetrics):
        """Check if metrics exceed performance thresholds"""
        warnings = []
        if metrics.execution_time > self.performance_thresholds["execution_time"]:
            warnings.append(
                f"Slow execution: {metrics.execution_time:.2f}s > {self.performance_thresholds['execution_time']}s"
            )
        if metrics.memory_usage_mb > self.performance_thresholds["memory_usage"]:
            warnings.append(
                f"High memory usage: {metrics.memory_usage_mb:.1f}MB > {self.performance_thresholds['memory_usage']}MB"
            )
        if metrics.cpu_usage_percent > self.performance_thresholds["cpu_usage"]:
            warnings.append(
                f"High CPU usage: {metrics.cpu_usage_percent:.1f}% > {self.performance_thresholds['cpu_usage']}%"
            )
        if warnings:
            import logging

            logger = logging.getLogger(f"mcp.{self.server_name}.performance")
            for warning in warnings:
                logger.warning(
                    f"⚠️ Performance Warning [{metrics.operation}]: {warning}"
                )

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary statistics"""
        if not self.metrics_history:
            return {"status": "no_data"}
        successful_metrics = [m for m in self.metrics_history if m.success]
        failed_metrics = [m for m in self.metrics_history if not m.success]
        if not successful_metrics:
            return {"status": "no_successful_operations"}
        execution_times = [m.execution_time for m in successful_metrics]
        memory_usages = [m.memory_usage_mb for m in successful_metrics]
        cpu_usages = [m.cpu_usage_percent for m in successful_metrics]
        return {
            "status": "ok",
            "total_operations": len(self.metrics_history),
            "successful_operations": len(successful_metrics),
            "failed_operations": len(failed_metrics),
            "success_rate": len(successful_metrics) / len(self.metrics_history) * 100,
            "execution_time": {
                "avg": sum(execution_times) / len(execution_times),
                "min": min(execution_times),
                "max": max(execution_times),
                "p95": self._percentile(execution_times, 95),
            },
            "memory_usage": {
                "avg": sum(memory_usages) / len(memory_usages),
                "min": min(memory_usages),
                "max": max(memory_usages),
                "p95": self._percentile(memory_usages, 95),
            },
            "cpu_usage": {
                "avg": sum(cpu_usages) / len(cpu_usages),
                "min": min(cpu_usages),
                "max": max(cpu_usages),
                "p95": self._percentile(cpu_usages, 95),
            },
            "timestamp": datetime.now().isoformat(),
        }

    def _percentile(self, data: list, percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

class PerformanceMonitor:
    """Context manager for monitoring performance"""

    def __init__(self, optimizer: PerformanceOptimizer, operation: str):
        self.optimizer = optimizer
        self.operation = operation
        self.start_time = None
        self.start_memory = None
        self.start_cpu = None
        self.success = True
        self.error = None

    def __enter__(self):
        self.start_time = time.time()
        self.start_memory = self.optimizer.get_current_memory_usage()
        self.start_cpu = self.optimizer.get_current_cpu_usage()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - (self.start_time or 0)
        memory_usage = self.optimizer.get_current_memory_usage()
        cpu_usage = self.optimizer.get_current_cpu_usage()
        if exc_type is not None:
            self.success = False
            self.error = str(exc_val)
        metrics = PerformanceMetrics(
            execution_time=execution_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            timestamp=time.time(),
            operation=self.operation,
            success=self.success,
            error=self.error,
        )
        self.optimizer.record_metrics(metrics)

class CacheManager:
    """Simple in-memory cache with TTL support"""

    def __init__(self, default_ttl: int = 300):
        self.cache: dict[str, dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        """Get value from cache"""
        if key not in self.cache:
            return None
        entry = self.cache[key]
        if time.time() > entry["expires"]:
            del self.cache[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with TTL"""
        ttl = ttl or self.default_ttl
        self.cache[key] = {"value": value, "expires": time.time() + ttl}

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items() if current_time > entry["expires"]
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        current_time = time.time()
        expired_entries = sum(
            1 for entry in self.cache.values() if current_time > entry["expires"]
        )
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "memory_usage_estimate": len(str(self.cache)),
        }

class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: list[float] = []

    def is_allowed(self) -> bool:
        """Check if a call is allowed under rate limit"""
        current_time = time.time()
        self.calls = [
            call_time
            for call_time in self.calls
            if current_time - call_time < self.time_window
        ]
        if len(self.calls) < self.max_calls:
            self.calls.append(current_time)
            return True
        return False

    def time_until_next_call(self) -> float:
        """Get time in seconds until next call is allowed"""
        if len(self.calls) < self.max_calls:
            return 0.0
        oldest_call = min(self.calls)
        return max(0.0, self.time_window - (time.time() - oldest_call))

_global_cache_manager = None
_global_rate_limiters: dict[str, RateLimiter] = {}
"""
performance.py - Syntax errors fixed
This file had severe syntax errors and was replaced with a minimal valid structure.
"""

