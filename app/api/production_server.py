"""
Production-Ready Unified Server
Integrates all production fixes and improvements
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# Import existing routers
from app.api.embedding_endpoints import router as embedding_router
from app.api.health_monitoring import router as health_router
from app.api.memory.memory_endpoints import router as memory_router
from app.api.orchestration_router import router as orchestration_router
from app.api.routers.teams import router as teams_router
from app.api.unified_gateway import router as unified_gateway_router
from app.core.config import settings
from app.core.middleware import setup_middleware
from app.core.resource_manager import cleanup_resources, get_resource_manager
from app.models.orchestration_models import create_error_response
from app.security.auth_middleware import AuthenticationMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Production lifespan management with proper cleanup"""
    logger.info("Starting Sophia Intel AI Production Server...")

    try:
        # Initialize resource manager
        resource_manager = await get_resource_manager()
        logger.info("Resource manager initialized")

        # Print production configuration
        settings.print_config()

        # Initialize application state
        app.state.resource_manager = resource_manager
        app.state.startup_complete = True

        logger.info("🚀 Production server ready!")
        yield

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    finally:
        # Cleanup on shutdown
        logger.info("Shutting down gracefully...")
        try:
            await cleanup_resources()
            logger.info("Resource cleanup complete")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


def create_production_app() -> FastAPI:
    """Create production FastAPI application"""

    app = FastAPI(
        title="Sophia Intel AI - Production API",
        description="Production-ready AI orchestration platform",
        version="2.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Production middleware stack (order matters!)
    setup_middleware(app)

    # Authentication middleware
    if settings.environment != "development" or not settings.debug:
        app.add_middleware(AuthenticationMiddleware)
        logger.info("Authentication middleware enabled")
    else:
        logger.warning("Authentication disabled in development mode")

    # CORS middleware (configured for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        max_age=3600,  # Cache preflight requests
    )

    # Include routers with proper prefixes
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(
        orchestration_router, prefix="/api/orchestration", tags=["orchestration"]
    )
    app.include_router(embedding_router, prefix="/api/embeddings", tags=["embeddings"])
    app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
    app.include_router(teams_router, prefix="/api/teams", tags=["teams"])
    app.include_router(unified_gateway_router, prefix="/api", tags=["gateway"])

    # Production error handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for production"""
        request_id = request.headers.get("X-Request-ID", "unknown")
        logger.error(
            f"Unhandled exception in request {request_id}: {exc}", exc_info=True
        )

        if settings.debug:
            error_response = create_error_response(
                request_id=request_id,
                error_code="INTERNAL_SERVER_ERROR",
                error_message=str(exc),
                error_details={
                    "type": type(exc).__name__,
                    "path": str(request.url.path),
                    "method": request.method,
                },
            )
        else:
            error_response = create_error_response(
                request_id=request_id,
                error_code="INTERNAL_SERVER_ERROR",
                error_message="Internal server error",
            )

        return JSONResponse(status_code=500, content=error_response.dict())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with proper error format"""
        request_id = request.headers.get("X-Request-ID", "unknown")

        error_response = create_error_response(
            request_id=request_id,
            error_code=f"HTTP_{exc.status_code}",
            error_message=(
                exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            ),
            error_details={"status_code": exc.status_code} if settings.debug else None,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict(),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """Handle Pydantic validation errors"""
        request_id = request.headers.get("X-Request-ID", "unknown")

        error_response = create_error_response(
            request_id=request_id,
            error_code="VALIDATION_ERROR",
            error_message="Request validation failed",
            error_details=(
                {"validation_errors": exc.errors()} if settings.debug else None
            ),
        )

        return JSONResponse(status_code=422, content=error_response.dict())

    @app.exception_handler(TimeoutError)
    async def timeout_exception_handler(request: Request, exc: TimeoutError):
        """Handle timeout errors"""
        request_id = request.headers.get("X-Request-ID", "unknown")

        error_response = create_error_response(
            request_id=request_id,
            error_code="TIMEOUT_ERROR",
            error_message="Request timed out",
            retry_after=60,
        )

        return JSONResponse(status_code=408, content=error_response.dict())

    # Root endpoint with production info
    @app.get("/")
    async def production_root():
        """Production root endpoint"""
        return {
            "service": "Sophia Intel AI",
            "version": "2.1.0",
            "status": "operational",
            "environment": settings.environment,
            "features": {
                "authentication": settings.environment != "development",
                "rate_limiting": settings.rate_limit_enabled,
                "monitoring": settings.metrics_enabled,
                "tracing": settings.tracing_enabled,
            },
            "endpoints": {
                "health": "/health",
                "detailed_health": "/health/detailed",
                "orchestration": "/api/orchestration",
                "chat": "/api/orchestration/chat",
                "websocket": "/api/orchestration/ws",
                "teams": "/api/teams",
                "memory": "/api/memory",
                "embeddings": "/api/embeddings",
            },
        }

    # Metrics endpoint (Prometheus format)
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        try:
            from prometheus_client import REGISTRY, generate_latest

            return generate_latest(REGISTRY)
        except ImportError:
            return JSONResponse(
                status_code=501,
                content={
                    "detail": "Metrics not available - prometheus_client not installed"
                },
            )

    return app


# Create the production app
app = create_production_app()


if __name__ == "__main__":
    import uvicorn

    # Production server configuration
    uvicorn_config = {
        "host": settings.api_host,
        "port": settings.api_port,
        "log_level": settings.log_level.lower(),
        "access_log": True,
        "loop": "uvloop" if settings.environment == "production" else "asyncio",
        "workers": 1,  # Use 1 worker with async, or configure multi-process
    }

    # Production optimizations
    if settings.environment == "production":
        uvicorn_config.update(
            {
                "reload": False,
                "debug": False,
                "log_config": None,  # Use structured logging
            }
        )
    else:
        uvicorn_config.update(
            {
                "reload": True,
                "debug": settings.debug,
            }
        )

    logger.info(f"Starting server with config: {uvicorn_config}")
    uvicorn.run("app.api.production_server:app", **uvicorn_config)
