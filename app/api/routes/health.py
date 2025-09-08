"""
Health check endpoints for monitoring
"""

from __future__ import annotations

import os
from datetime import datetime

import psutil
from fastapi import APIRouter, Depends

from app.api.middleware.auth import get_current_user
from app.core.ai_logger import logger
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """
    Basic health check endpoint

    Returns 200 OK if service is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Sophia Foundational Knowledge System",
        "version": "1.0.0",
    }


@router.get("/detailed")
async def detailed_health_check(user: str = Depends(get_current_user)):
    """
    Detailed health check with system metrics

    Requires authentication in production
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Sophia Foundational Knowledge System",
        "version": "1.0.0",
        "environment": settings.environment,
        "components": {},
        "metrics": {},
        "config": {},
    }

    # Check database connectivity
    try:
        from app.knowledge.foundational_manager import FoundationalKnowledgeManager

        manager = FoundationalKnowledgeManager()
        stats = await manager.get_statistics()
        health_status["components"]["database"] = {
            "status": "connected",
            "total_entries": stats.get("total_entries", 0),
            "foundational_count": stats.get("foundational_count", 0),
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["components"]["database"] = {
            "status": "error",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check Redis connectivity (if configured)
    try:
        if settings.redis_url and settings.redis_url != "redis://localhost:6379":
            import redis

            r = redis.from_url(settings.redis_url)
            r.ping()
            health_status["components"]["redis"] = {
                "status": "connected",
                "url": settings.redis_url,
            }
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "error",
            "error": str(e),
        }

    # Check Airtable connectivity
    try:
        if os.getenv("AIRTABLE_API_KEY"):
            health_status["components"]["airtable"] = {
                "status": "configured",
                "base_id": os.getenv("AIRTABLE_BASE_ID", "not_set"),
            }
        else:
            health_status["components"]["airtable"] = {
                "status": "not_configured",
            }
    except Exception as e:
        health_status["components"]["airtable"] = {
            "status": "error",
            "error": str(e),
        }

    # System metrics
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        health_status["metrics"]["cpu_usage_percent"] = cpu_percent

        # Memory usage
        memory = psutil.virtual_memory()
        health_status["metrics"]["memory"] = {
            "total_mb": memory.total // (1024 * 1024),
            "available_mb": memory.available // (1024 * 1024),
            "percent_used": memory.percent,
        }

        # Disk usage
        disk = psutil.disk_usage("/")
        health_status["metrics"]["disk"] = {
            "total_gb": disk.total // (1024 * 1024 * 1024),
            "free_gb": disk.free // (1024 * 1024 * 1024),
            "percent_used": disk.percent,
        }

        # Process info
        process = psutil.Process(os.getpid())
        health_status["metrics"]["process"] = {
            "pid": process.pid,
            "memory_mb": process.memory_info().rss // (1024 * 1024),
            "threads": process.num_threads(),
            "connections": len(process.connections(kind="inet")),
        }

    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")
        health_status["metrics"]["error"] = str(e)

    # Configuration status
    health_status["config"] = {
        "auth_enabled": settings.require_auth,
        "environment": settings.environment,
        "debug_mode": settings.debug,
        "rate_limiting": {
            "enabled": settings.rate_limit_enabled,
            "max_requests": settings.max_concurrent_requests,
        },
        "features": {
            "graphrag": settings.graphrag_enabled,
            "hybrid_search": settings.hybrid_search_enabled,
            "evaluation_gates": settings.evaluation_gates_enabled,
        },
    }

    # Determine overall health
    if any(
        comp.get("status") == "error" for comp in health_status["components"].values()
    ):
        health_status["status"] = "unhealthy"
    elif any(
        comp.get("status") == "degraded"
        for comp in health_status["components"].values()
    ):
        health_status["status"] = "degraded"

    return health_status


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe for Kubernetes/container orchestration

    Returns 200 if service is ready to accept traffic
    """
    try:
        # Quick database check
        from app.knowledge.foundational_manager import FoundationalKnowledgeManager

        manager = FoundationalKnowledgeManager()
        await manager.storage.list_knowledge(limit=1)

        return {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@router.get("/live")
async def liveness_check():
    """
    Liveness probe for Kubernetes/container orchestration

    Returns 200 if service is alive (doesn't check dependencies)
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
        "pid": os.getpid(),
    }
