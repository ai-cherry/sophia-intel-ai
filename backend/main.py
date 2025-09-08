"""
Sophia AI Platform - Main API Entry Point
Consolidated from multiple services into single entry point
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure structured logging
from backend.core.logging import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info("🚀 Starting Sophia AI Platform")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

    # Initialize database
    try:
        from backend.core.database import init_db

        await init_db()
        logger.info("✓ Database connected")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")

    # Initialize Redis
    try:
        from backend.core.cache import init_redis

        await init_redis()
        logger.info("✓ Redis connected")
    except Exception as e:
        logger.warning(f"Redis initialization skipped: {e}")

    yield

    # Cleanup
    logger.info("Shutting down Sophia AI Platform")


# Create FastAPI application
app = FastAPI(
    title="Sophia AI Platform",
    description="Unified AI orchestration platform - Post Vercel migration",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"{time.time()}")
    start_time = time.time()

    # Add request ID to request state
    request.state.request_id = request_id

    # Log request
    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    # Process request
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"[{request_id}] Error: {e}")
        response = JSONResponse(
            status_code=500, content={"error": "Internal server error", "request_id": request_id}
        )

    # Log response
    process_time = time.time() - start_time
    logger.info(f"[{request_id}] {response.status_code} in {process_time:.3f}s")

    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Health endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint - always returns 200 if service is running"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check - verifies all dependencies are ready"""
    checks = {}

    # Check database
    try:
        from backend.core.database import check_connection

        checks["database"] = await check_connection()
    except:
        checks["database"] = False

    # Check Redis
    try:
        from backend.core.cache import check_connection

        checks["redis"] = await check_connection()
    except:
        checks["redis"] = False

    all_ready = all(checks.values()) if checks else True

    return {"ready": all_ready, "checks": checks, "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with API information"""
    return {
        "name": "Sophia AI Platform API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs",
            "redoc": "/redoc",
            "metrics": "/metrics",
            "api": {
                "chat": "/api/chat",
                "orchestration": "/api/orchestration",
                "memory": "/api/memory",
            },
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import Response
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Import routers
try:
    from backend.routers import chat, memory, orchestration

    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(orchestration.router, prefix="/api/orchestration", tags=["orchestration"])
    app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
    logger.info("✓ All routers loaded")
except ImportError as e:
    logger.warning(f"Some routers not available: {e}")

    # Create placeholder endpoints
    @app.post("/api/chat")
    async def placeholder_chat(message: dict):
        return {"response": f"Echo: {message.get('text', 'Hello')}", "status": "placeholder"}

    @app.post("/api/orchestration")
    async def placeholder_orchestration(request: dict):
        return {"result": "Orchestration placeholder", "agents": [], "status": "placeholder"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="${BIND_IP}",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info",
    )
