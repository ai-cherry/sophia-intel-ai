"""SOPHIA Intel API Gateway - Single Front Door with Production Hardening"""
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routers import health, orchestration, speech
from core.env_schema import validate_environment
from core.middleware import RequestMiddleware, limiter

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Validate environment on startup (fail-fast)
config = validate_environment()
logger.info("sophia_api_gateway_starting", env=config.env, debug=config.debug)

app = FastAPI(
    title="SOPHIA Intel API Gateway",
    description="Single front door for orchestration, voice, and health - Production Hardened",
    version="1.0.0"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add request middleware (must be first)
app.add_middleware(RequestMiddleware)

# CORS middleware with production security
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=config.cors_allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=config.cors_max_age,
)

# Include routers
app.include_router(health.router)
app.include_router(orchestration.router)
app.include_router(speech.router)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("sophia_api_gateway_ready", 
                endpoints=["health", "orchestration", "speech"],
                cors_origins=config.cors_origins)

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    from core.http_client import http_client
    await http_client.close()
    logger.info("sophia_api_gateway_shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug,
        log_config=None  # Use structlog instead
    )
