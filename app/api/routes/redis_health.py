"""
Redis Health Monitoring API Endpoints
Provides health status, metrics, and monitoring for Redis infrastructure.
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.core.redis_config import RedisNamespaces
from app.core.redis_health_monitor import (
    HealthStatus,
    redis_health_monitor,
)
from app.core.redis_manager import redis_manager

router = APIRouter(prefix="/redis", tags=["Redis Health"])


@router.get("/health", summary="Get Redis Health Status")
async def get_redis_health() -> dict[str, Any]:
    """
    Get comprehensive Redis health status including:
    - Overall system health
    - Memory usage and performance metrics
    - Connection pool status
    - Pay Ready business cycle awareness
    - Stream health and bounds
    - Recent alerts and recommendations
    """
    try:
        health_data = await redis_health_monitor.comprehensive_health_check()
        return health_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/health/summary", summary="Get Redis Health Summary")
async def get_redis_health_summary() -> dict[str, Any]:
    """
    Get concise Redis health summary with key metrics and critical alerts.
    """
    try:
        summary = await redis_health_monitor.get_health_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health summary failed: {str(e)}")


@router.get("/metrics", summary="Get Redis Metrics")
async def get_redis_metrics() -> dict[str, Any]:
    """
    Get detailed Redis metrics including memory, performance, and connection pool stats.
    """
    try:
        # Get manager metrics
        manager_metrics = await redis_manager.get_metrics()

        # Get memory stats
        memory_stats = await redis_manager.get_memory_stats()

        # Get health metrics
        health_summary = await redis_health_monitor.get_health_summary()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "manager_metrics": manager_metrics,
            "memory_stats": memory_stats,
            "health_metrics": health_summary["key_metrics"],
            "status": health_summary["status"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Metrics collection failed: {str(e)}"
        )


@router.get("/streams", summary="Get Redis Streams Status")
async def get_streams_status() -> dict[str, Any]:
    """
    Get status of Redis streams including length, capacity, and health.
    """
    try:
        health_data = await redis_health_monitor.comprehensive_health_check()
        streams_data = health_data.get("components", {}).get("streams", {})

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "streams_status": streams_data.get("status", HealthStatus.HEALTHY),
            "streams_info": streams_data.get("streams", {}),
            "metrics": streams_data.get("metrics", {}),
            "alerts": streams_data.get("alerts", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streams status failed: {str(e)}")


@router.get("/alerts", summary="Get Redis Health Alerts")
async def get_redis_alerts(
    level: Optional[str] = Query(None, description="Filter by alert level"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of alerts"),
) -> dict[str, Any]:
    """
    Get recent Redis health alerts with optional filtering.
    """
    try:
        alerts = redis_health_monitor.alerts

        # Filter by level if specified
        if level:
            try:
                level_enum = HealthStatus(level.lower())
                alerts = [alert for alert in alerts if alert.level == level_enum]
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid alert level: {level}"
                )

        # Limit results
        alerts = alerts[-limit:] if alerts else []

        # Format for response
        formatted_alerts = [
            {
                "level": alert.level.value,
                "component": alert.component,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metrics": alert.metrics,
                "suggested_actions": alert.suggested_actions,
            }
            for alert in alerts
        ]

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_alerts": len(formatted_alerts),
            "alerts": formatted_alerts,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Alerts retrieval failed: {str(e)}"
        )


@router.get("/pay-ready", summary="Get Pay Ready Redis Status")
async def get_pay_ready_status() -> dict[str, Any]:
    """
    Get Pay Ready business cycle specific Redis monitoring status.
    """
    try:
        health_data = await redis_health_monitor.comprehensive_health_check()
        pay_ready_data = health_data.get("pay_ready_status", {})

        return {"timestamp": datetime.utcnow().isoformat(), **pay_ready_data}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Pay Ready status failed: {str(e)}"
        )


@router.post("/monitoring/start", summary="Start Redis Health Monitoring")
async def start_monitoring(
    background_tasks: BackgroundTasks,
    interval: float = Query(
        30.0, ge=10.0, le=300.0, description="Monitoring interval in seconds"
    ),
) -> dict[str, str]:
    """
    Start continuous Redis health monitoring with specified interval.
    """
    try:
        if redis_health_monitor.monitoring_active:
            return {
                "status": "already_active",
                "message": "Health monitoring is already active",
            }

        # Start monitoring in background
        background_tasks.add_task(redis_health_monitor.start_monitoring, interval)

        return {
            "status": "started",
            "message": f"Health monitoring started with {interval}s interval",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start monitoring: {str(e)}"
        )


@router.post("/monitoring/stop", summary="Stop Redis Health Monitoring")
async def stop_monitoring() -> dict[str, str]:
    """
    Stop continuous Redis health monitoring.
    """
    try:
        await redis_health_monitor.stop_monitoring()
        return {"status": "stopped", "message": "Health monitoring stopped"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to stop monitoring: {str(e)}"
        )


@router.get("/monitoring/status", summary="Get Monitoring Status")
async def get_monitoring_status() -> dict[str, Any]:
    """
    Get current status of Redis health monitoring.
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "monitoring_active": redis_health_monitor.monitoring_active,
        "total_alerts": len(redis_health_monitor.alerts),
        "alert_callbacks": len(redis_health_monitor.alert_callbacks),
    }


@router.post("/cache/cleanup", summary="Cleanup Expired Redis Keys")
async def cleanup_expired_keys(
    pattern: str = Query("*", description="Key pattern to cleanup"),
    scan_count: int = Query(100, ge=10, le=1000, description="Scan batch size"),
) -> dict[str, Any]:
    """
    Cleanup expired Redis keys matching pattern.
    """
    try:
        cleaned_count = await redis_manager.cleanup_expired_keys(pattern, scan_count)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "pattern": pattern,
            "keys_processed": cleaned_count,
            "status": "completed",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache cleanup failed: {str(e)}")


@router.get("/memory/usage", summary="Get Detailed Memory Usage")
async def get_memory_usage() -> dict[str, Any]:
    """
    Get detailed Redis memory usage by namespace and pattern.
    """
    try:
        memory_stats = await redis_manager.get_memory_stats()

        # Get namespace memory usage
        namespace_usage = {}

        async with redis_manager.get_connection() as redis:
            for namespace in [
                ns for ns in dir(RedisNamespaces) if not ns.startswith("_")
            ]:
                namespace_value = getattr(RedisNamespaces, namespace)
                if isinstance(namespace_value, str):
                    pattern = f"{namespace_value}:*"
                    keys = []
                    async for key in redis.scan_iter(match=pattern, count=100):
                        keys.append(key)
                        if len(keys) >= 100:  # Limit for performance
                            break

                    total_memory = 0
                    for key in keys:
                        try:
                            key_memory = await redis.memory_usage(key)
                            if key_memory:
                                total_memory += key_memory
                        except Exception:
                            continue

                    namespace_usage[namespace.lower()] = {
                        "keys_count": len(keys),
                        "memory_bytes": total_memory,
                        "memory_mb": total_memory / (1024 * 1024),
                    }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_memory_stats": memory_stats,
            "namespace_usage": namespace_usage,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Memory usage analysis failed: {str(e)}"
        )


@router.post("/test/connection", summary="Test Redis Connection")
async def test_redis_connection() -> dict[str, Any]:
    """
    Test Redis connection and basic operations.
    """
    try:
        start_time = datetime.utcnow()

        # Test basic operations
        async with redis_manager.get_connection() as redis:
            # Test PING
            await redis.ping()

            # Test SET/GET
            test_key = f"test:{int(start_time.timestamp())}"
            await redis.set(test_key, "test_value", ex=60)
            await redis.get(test_key)
            await redis.delete(test_key)

            # Test stream operation
            stream_key = f"test_stream:{int(start_time.timestamp())}"
            await redis.xadd(stream_key, {"test": "data"}, maxlen=1)
            await redis.delete(stream_key)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        return {
            "status": "success",
            "timestamp": end_time.isoformat(),
            "response_time": duration,
            "tests_passed": ["ping", "set_get", "stream_operations"],
            "message": "All Redis connection tests passed",
        }

    except Exception as e:
        return {
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "message": "Redis connection test failed",
        }
