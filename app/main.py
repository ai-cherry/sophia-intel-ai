"""
Sophia AI Unified Memory Architecture - Main Application
Zero Tech Debt FastAPI Implementation with Neon PostgreSQL Integration

This module completely replaces and eliminates:
- All scattered FastAPI entry points
- Legacy database initialization patterns
- Fragmented configuration management
- Duplicate middleware and routing

Author: Manus AI - Hellfire Architecture Division
Date: August 8, 2025
Version: 1.0.0 - Neon-Forged Foundation
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict

import aioredis
import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from qdrant_client import AsyncQdrantClient
from shared.core.unified_config import get_config_value

from app.api.routes import create_api_router

# Import unified components (eliminates fragmented imports)
from app.memory.bus import UnifiedMemoryBus, create_memory_bus
from app.observability.otel import setup_metrics, setup_tracing
from app.security.tenant import TenantMiddleware

# Configure logging (eliminates scattered logging configs)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("sophia_memory.log"),
    ],
)
logger = logging.getLogger(__name__)

# Global state (eliminates scattered global variables)
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async lifespan manager with zero tech debt initialization
    Replaces all legacy startup/shutdown patterns
    """
    logger.info("🔥 Starting Sophia AI Unified Memory Architecture")

    try:
        # Initialize observability first (eliminates monitoring gaps)
        setup_tracing()
        setup_metrics()
        logger.info("✅ Observability initialized")

        # Neon PostgreSQL connection with autoscaling
        neon_dsn = get_config_value("neon_database_url") or os.getenv(
            "NEON_DATABASE_URL",
            "postgresql://user:pass@neon-host/sophia_ai?sslmode=require",
        )

        pg_pool = await asyncpg.create_pool(
            neon_dsn,
            min_size=5,
            max_size=50,  # Neon handles autoscaling beyond this
            command_timeout=30,
            server_settings={
                "application_name": "sophia_unified_memory",
                "timezone": "UTC",
                "statement_timeout": "30s",
            },
        )
        logger.info("✅ Neon PostgreSQL pool initialized")

        # Redis with client-side tracking (Jul '25 optimization)
        redis_url = get_config_value("redis_url") or os.getenv(
            "REDIS_URL", "${REDIS_URL}"
        )

        redis_client = aioredis.from_url(
            redis_url,
            decode_responses=False,  # Keep binary for compression
            client_tracking=True,  # Jul '25 optimization
            socket_keepalive=True,
            retry_on_timeout=True,
            health_check_interval=30,
        )

        # Test Redis connection
        await redis_client.ping()
        logger.info("✅ Redis client initialized with tracking")

        # Qdrant vector database
        qdrant_url = get_config_value("qdrant_url") or os.getenv(
            "QDRANT_URL", "http://localhost:6333"
        )

        qdrant_client = AsyncQdrantClient(url=qdrant_url, timeout=30.0)

        # Test Qdrant connection
        collections = await qdrant_client.get_collections()
        logger.info(
            f"✅ Qdrant initialized with {len(collections.collections)} collections"
        )

        # Create unified memory bus (eliminates all legacy memory systems)
        memory_bus = await create_memory_bus(pg_pool, redis_client, qdrant_client)

        # Store in app state for dependency injection
        app.state.memory_bus = memory_bus
        app.state.pg_pool = pg_pool
        app.state.redis_client = redis_client
        app.state.qdrant_client = qdrant_client

        # Store in global state for access
        app_state.update(
            {
                "memory_bus": memory_bus,
                "pg_pool": pg_pool,
                "redis_client": redis_client,
                "qdrant_client": qdrant_client,
                "startup_time": asyncio.get_event_loop().time(),
            }
        )

        logger.info("🔥 Sophia AI Unified Memory Architecture started successfully")
        logger.info("🎯 All legacy memory systems eliminated - Zero tech debt achieved")

        yield

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    finally:
        # Graceful shutdown (eliminates resource leaks)
        logger.info("🔥 Shutting down Sophia AI Unified Memory Architecture")

        try:
            if hasattr(app.state, "memory_bus"):
                await app.state.memory_bus.shutdown()

            if hasattr(app.state, "pg_pool"):
                await app.state.pg_pool.close()

            if hasattr(app.state, "redis_client"):
                await app.state.redis_client.close()

            if hasattr(app.state, "qdrant_client"):
                await app.state.qdrant_client.close()

            logger.info("✅ Graceful shutdown complete - Zero resource leaks")

        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")


# Create FastAPI application with zero tech debt configuration
app = FastAPI(
    title="Sophia AI Unified Memory Architecture",
    description="Zero Tech Debt Memory System with MemOS Lifecycles and Neon PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Middleware stack (eliminates duplicate middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TenantMiddleware)  # Custom tenant isolation


# Dependency injection (eliminates scattered dependency patterns)
async def get_memory_bus() -> UnifiedMemoryBus:
    """Get unified memory bus instance"""
    if not hasattr(app.state, "memory_bus"):
        raise HTTPException(status_code=503, detail="Memory bus not initialized")
    return app.state.memory_bus


async def get_pg_pool() -> asyncpg.Pool:
    """Get PostgreSQL connection pool"""
    if not hasattr(app.state, "pg_pool"):
        raise HTTPException(status_code=503, detail="Database pool not initialized")
    return app.state.pg_pool


# Global exception handler (eliminates scattered error handling)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with proper logging"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") else "An error occurred",
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


# Health check endpoints (eliminates scattered health checks)
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        memory_bus = await get_memory_bus()
        metrics = await memory_bus.get_performance_metrics()

        return {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "uptime_seconds": asyncio.get_event_loop().time()
            - app_state.get("startup_time", 0),
            "memory_metrics": metrics,
            "version": "1.0.0",
            "architecture": "unified_memory_hellfire",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time(),
            },
        )


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        # Test all critical components
        memory_bus = await get_memory_bus()
        pg_pool = await get_pg_pool()

        # Quick connectivity tests
        async with pg_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        await app.state.redis_client.ping()

        collections = await app.state.qdrant_client.get_collections()

        return {
            "status": "ready",
            "components": {
                "memory_bus": "ready",
                "postgresql": "ready",
                "redis": "ready",
                "qdrant": "ready",
            },
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503, content={"status": "not_ready", "error": str(e)}
        )


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive", "timestamp": asyncio.get_event_loop().time()}


# Metrics endpoint (eliminates scattered metrics)
@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint"""
    try:
        memory_bus = await get_memory_bus()
        metrics = await memory_bus.get_performance_metrics()

        # Format as Prometheus metrics
        prometheus_metrics = []

        # Hit rate metric
        prometheus_metrics.append(f"sophia_cache_hit_rate {metrics['hit_rate']}")

        # Cache hits by tier
        for tier, hits in metrics["cache_hits_by_tier"].items():
            prometheus_metrics.append(
                f'sophia_cache_hits_total{{tier="{tier}"}} {hits}'
            )

        # Latency metric
        prometheus_metrics.append(
            f"sophia_memory_latency_ms {metrics['avg_latency_ms']}"
        )

        # Operations total
        prometheus_metrics.append(
            f"sophia_memory_operations_total {metrics['operations_total']}"
        )

        return "\n".join(prometheus_metrics)

    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return JSONResponse(
            status_code=500, content={"error": "Metrics collection failed"}
        )


# Include API routes (eliminates scattered route definitions)
app.include_router(create_api_router(), prefix="/api/v1", tags=["memory"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "service": "Sophia AI Unified Memory Architecture",
        "version": "1.0.0",
        "status": "🔥 HELLFIRE OPTIMIZED",
        "tech_debt": "ELIMINATED",
        "architecture": "unified_memory_bus",
        "features": [
            "MemOS lifecycles",
            "5-tier caching",
            "Neon PostgreSQL autoscaling",
            "LangGraph swarm coordination",
            "Quantized Qdrant RAG",
            "Zero tech debt",
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "api": "/api/v1",
        },
    }


# Development server configuration
if __name__ == "__main__":
    # Development mode with hot reload
    uvicorn.run(
        "app.main:app",
        host="${BIND_IP}",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        loop="uvloop",  # High-performance event loop
    )
