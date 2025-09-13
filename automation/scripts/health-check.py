#!/usr/bin/env python3
"""
Comprehensive Health Check System for Sophia Intel AI
Provides detailed health monitoring for all system components
"""
import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
import aiohttp
import asyncpg
import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest
# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    response_time: float
    message: str
    last_checked: datetime
    metadata: Dict[str, Any] = None
    def to_dict(self):
        return {
            **asdict(self),
            "status": self.status.value,
            "last_checked": self.last_checked.isoformat(),
            "metadata": self.metadata or {},
        }
@dataclass
class SystemHealth:
    overall_status: HealthStatus
    components: List[ComponentHealth]
    last_updated: datetime
    system_info: Dict[str, Any]
    performance_metrics: Dict[str, float]
    def to_dict(self):
        return {
            "overall_status": self.overall_status.value,
            "components": [comp.to_dict() for comp in self.components],
            "last_updated": self.last_updated.isoformat(),
            "system_info": self.system_info,
            "performance_metrics": self.performance_metrics,
            "summary": {
                "healthy_components": sum(
                    1 for c in self.components if c.status == HealthStatus.HEALTHY
                ),
                "degraded_components": sum(
                    1 for c in self.components if c.status == HealthStatus.DEGRADED
                ),
                "unhealthy_components": sum(
                    1 for c in self.components if c.status == HealthStatus.UNHEALTHY
                ),
                "total_components": len(self.components),
            },
        }
class HealthChecker:
    def __init__(self):
        self.registry = CollectorRegistry()
        self.metrics = {
            "health_status": Gauge(
                "sophia_component_health_status",
                "Component health status (1=healthy, 0.5=degraded, 0=unhealthy)",
                ["component"],
                registry=self.registry,
            ),
            "response_time": Gauge(
                "sophia_component_response_time_seconds",
                "Component response time in seconds",
                ["component"],
                registry=self.registry,
            ),
            "check_total": Counter(
                "sophia_health_checks_total",
                "Total number of health checks",
                ["component", "status"],
                registry=self.registry,
            ),
        }
    async def check_redis_health(self, url: str) -> ComponentHealth:
        """Check Redis health"""
        start_time = time.time()
        try:
            r = redis.from_url(url, decode_responses=True)
            # Basic connectivity test
            await r.ping()
            # Performance test
            test_key = f"health_check_{int(time.time())}"
            await r.set(test_key, "test_value", ex=60)
            value = await r.get(test_key)
            await r.delete(test_key)
            if value != "test_value":
                raise Exception("Redis read/write test failed")
            # Get Redis info
            info = await r.info()
            memory_usage = info.get("used_memory_human", "unknown")
            connected_clients = info.get("connected_clients", 0)
            response_time = time.time() - start_time
            await r.aclose()
            status = HealthStatus.HEALTHY
            if response_time > 1.0:
                status = HealthStatus.DEGRADED
            return ComponentHealth(
                name="redis",
                status=status,
                response_time=response_time,
                message=f"Redis operational - Memory: {memory_usage}, Clients: {connected_clients}",
                last_checked=datetime.utcnow(),
                metadata={
                    "memory_usage": memory_usage,
                    "connected_clients": connected_clients,
                    "version": info.get("redis_version", "unknown"),
                },
            )
        except Exception as e:
            response_time = time.time() - start_time
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=f"Redis check failed: {str(e)}",
                last_checked=datetime.utcnow(),
            )
    async def check_postgres_health(self, url: str) -> ComponentHealth:
        """Check PostgreSQL health"""
        start_time = time.time()
        try:
            conn = await asyncpg.connect(url)
            # Basic connectivity test
            result = await conn.fetchval("SELECT 1")
            if result != 1:
                raise Exception("PostgreSQL basic query failed")
            # Performance test
            await conn.execute("SELECT pg_sleep(0.001)")
            # Get database info
            db_size = await conn.fetchval("SELECT pg_database_size(current_database())")
            active_connections = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity"
            )
            version = await conn.fetchval("SELECT version()")
            response_time = time.time() - start_time
            await conn.close()
            status = HealthStatus.HEALTHY
            if response_time > 2.0:
                status = HealthStatus.DEGRADED
            return ComponentHealth(
                name="postgres",
                status=status,
                response_time=response_time,
                message=f"PostgreSQL operational - Size: {db_size} bytes, Connections: {active_connections}",
                last_checked=datetime.utcnow(),
                metadata={
                    "database_size_bytes": db_size,
                    "active_connections": active_connections,
                    "version": version.split("\n")[0] if version else "unknown",
                },
            )
        except Exception as e:
            response_time = time.time() - start_time
            return ComponentHealth(
                name="postgres",
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=f"PostgreSQL check failed: {str(e)}",
                last_checked=datetime.utcnow(),
            )
    async def check_weaviate_health(self, url: str) -> ComponentHealth:
        """Check Weaviate health"""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                # Check readiness
                async with session.get(
                    f"{url}/v1/.well-known/ready", timeout=10
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Weaviate not ready: HTTP {resp.status}")
                # Check liveness
                async with session.get(
                    f"{url}/v1/.well-known/live", timeout=10
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Weaviate not live: HTTP {resp.status}")
                # Get system info
                async with session.get(f"{url}/v1/meta", timeout=10) as resp:
                    if resp.status == 200:
                        meta = await resp.json()
                        version = meta.get("version", "unknown")
                        modules = meta.get("modules", {})
                    else:
                        version = "unknown"
                        modules = {}
                response_time = time.time() - start_time
                status = HealthStatus.HEALTHY
                if response_time > 2.0:
                    status = HealthStatus.DEGRADED
                return ComponentHealth(
                    name="weaviate",
                    status=status,
                    response_time=response_time,
                    message=f"Weaviate operational - Version: {version}",
                    last_checked=datetime.utcnow(),
                    metadata={
                        "version": version,
                        "modules": list(modules.keys()) if modules else [],
                    },
                )
        except Exception as e:
            response_time = time.time() - start_time
            return ComponentHealth(
                name="weaviate",
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=f"Weaviate check failed: {str(e)}",
                last_checked=datetime.utcnow(),
            )
    async def check_service_health(
        self, service_name: str, url: str, health_path: str = "/healthz"
    ) -> ComponentHealth:
        """Check application service health"""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                full_url = f"{url.rstrip('/')}{health_path}"
                async with session.get(full_url, timeout=10) as resp:
                    response_time = time.time() - start_time
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                            service_status = data.get("status", "unknown")
                            service_info = data.get("info", {})
                        except:
                            data = await resp.text()
                            service_status = (
                                "healthy" if "ok" in data.lower() else "unknown"
                            )
                            service_info = {}
                        status = HealthStatus.HEALTHY
                        if response_time > 3.0 or service_status.lower() in [
                            "degraded",
                            "warning",
                        ]:
                            status = HealthStatus.DEGRADED
                        return ComponentHealth(
                            name=service_name,
                            status=status,
                            response_time=response_time,
                            message=f"{service_name} operational - Status: {service_status}",
                            last_checked=datetime.utcnow(),
                            metadata=service_info,
                        )
                    else:
                        return ComponentHealth(
                            name=service_name,
                            status=HealthStatus.UNHEALTHY,
                            response_time=response_time,
                            message=f"{service_name} returned HTTP {resp.status}",
                            last_checked=datetime.utcnow(),
                        )
        except Exception as e:
            response_time = time.time() - start_time
            return ComponentHealth(
                name=service_name,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=f"{service_name} check failed: {str(e)}",
                last_checked=datetime.utcnow(),
            )
    async def check_system_health(self) -> SystemHealth:
        """Check overall system health"""
        components = []
        # Configuration from environment
        checks = {
            "redis": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "postgres": os.getenv(
                "POSTGRES_URL", "postgresql://sophia:sophia123@localhost:5432/sophia"
            ),
            "weaviate": os.getenv("WEAVIATE_URL", "http://localhost:8080"),
            "unified-api": os.getenv("UNIFIED_API_URL", "http://localhost:8003"),
            "sophia-orchestrator": os.getenv(
                "SOPHIA_ORCHESTRATOR_URL", "http://localhost:8006"
            ),
            "-orchestrator": os.getenv(
                "_ORCHESTRATOR_URL", "http://localhost:8007"
            ),
        }
        # Run health checks concurrently
        tasks = []
        for name, url in checks.items():
            if name == "redis":
                tasks.append(self.check_redis_health(url))
            elif name == "postgres":
                tasks.append(self.check_postgres_health(url))
            elif name == "weaviate":
                tasks.append(self.check_weaviate_health(url))
            else:
                tasks.append(self.check_service_health(name, url))
        components = await asyncio.gather(*tasks, return_exceptions=True)
        # Handle exceptions
        valid_components = []
        for i, comp in enumerate(components):
            if isinstance(comp, Exception):
                service_name = list(checks.keys())[i]
                valid_components.append(
                    ComponentHealth(
                        name=service_name,
                        status=HealthStatus.UNKNOWN,
                        response_time=0.0,
                        message=f"Health check exception: {str(comp)}",
                        last_checked=datetime.utcnow(),
                    )
                )
            else:
                valid_components.append(comp)
        # Update metrics
        for comp in valid_components:
            status_value = {
                HealthStatus.HEALTHY: 1.0,
                HealthStatus.DEGRADED: 0.5,
                HealthStatus.UNHEALTHY: 0.0,
                HealthStatus.UNKNOWN: 0.0,
            }.get(comp.status, 0.0)
            self.metrics["health_status"].labels(component=comp.name).set(status_value)
            self.metrics["response_time"].labels(component=comp.name).set(
                comp.response_time
            )
            self.metrics["check_total"].labels(
                component=comp.name, status=comp.status.value
            ).inc()
        # Determine overall status
        unhealthy_count = sum(
            1 for c in valid_components if c.status == HealthStatus.UNHEALTHY
        )
        degraded_count = sum(
            1 for c in valid_components if c.status == HealthStatus.DEGRADED
        )
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        # System info
        system_info = {
            "hostname": os.uname().nodename,
            "environment": os.getenv("SOPHIA_ENVIRONMENT", "unknown"),
            "version": os.getenv("SOPHIA_VERSION", "1.0.0"),
            "uptime_seconds": (
                time.time() - os.path.getmtime("/proc/self/stat")
                if os.path.exists("/proc/self/stat")
                else 0
            ),
        }
        # Performance metrics
        performance_metrics = {
            "total_response_time": sum(c.response_time for c in valid_components),
            "average_response_time": (
                sum(c.response_time for c in valid_components) / len(valid_components)
                if valid_components
                else 0
            ),
            "max_response_time": max(
                (c.response_time for c in valid_components), default=0
            ),
            "health_check_duration": sum(c.response_time for c in valid_components),
        }
        return SystemHealth(
            overall_status=overall_status,
            components=valid_components,
            last_updated=datetime.utcnow(),
            system_info=system_info,
            performance_metrics=performance_metrics,
        )
# FastAPI app for health endpoints
app = FastAPI(title="Sophia Intel AI Health Monitor", version="1.0.0")
health_checker = HealthChecker()
@app.get("/health")
@app.get("/healthz")
async def health_check():
    """Basic health check endpoint"""
    try:
        health = await health_checker.check_system_health()
        status_code = 200 if health.overall_status != HealthStatus.UNHEALTHY else 503
        return JSONResponse(content=health.to_dict(), status_code=status_code)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "overall_status": "unhealthy",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat(),
            },
            status_code=503,
        )
@app.get("/health/ready")
@app.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    try:
        health = await health_checker.check_system_health()
        # Ready if no components are unhealthy
        ready = health.overall_status != HealthStatus.UNHEALTHY
        status_code = 200 if ready else 503
        return JSONResponse(
            content={
                "ready": ready,
                "status": health.overall_status.value,
                "components_summary": {
                    "healthy": sum(
                        1 for c in health.components if c.status == HealthStatus.HEALTHY
                    ),
                    "degraded": sum(
                        1
                        for c in health.components
                        if c.status == HealthStatus.DEGRADED
                    ),
                    "unhealthy": sum(
                        1
                        for c in health.components
                        if c.status == HealthStatus.UNHEALTHY
                    ),
                },
            },
            status_code=status_code,
        )
    except Exception as e:
        return JSONResponse(content={"ready": False, "error": str(e)}, status_code=503)
@app.get("/health/live")
@app.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return JSONResponse(
        content={"alive": True, "timestamp": datetime.utcnow().isoformat()}
    )
@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    # Ensure metrics are updated
    await health_checker.check_system_health()
    return PlainTextResponse(generate_latest(health_checker.registry))
@app.get("/health/detailed")
async def detailed_health():
    """Detailed health information"""
    health = await health_checker.check_system_health()
    return health.to_dict()
@app.get("/health/component/{component_name}")
async def component_health(component_name: str):
    """Health check for specific component"""
    health = await health_checker.check_system_health()
    component = next((c for c in health.components if c.name == component_name), None)
    if not component:
        raise HTTPException(
            status_code=404, detail=f"Component {component_name} not found"
        )
    return component.to_dict()
async def main():
    """Main function for standalone health checker"""
    parser = argparse.ArgumentParser(description="Sophia Intel AI Health Checker")
    parser.add_argument("--service", default="health-monitor", help="Service name")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument(
        "--check-only", action="store_true", help="Run single health check and exit"
    )
    parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )
    args = parser.parse_args()
    if args.check_only:
        # Single health check
        checker = HealthChecker()
        health = await checker.check_system_health()
        if args.format == "json":
            print(json.dumps(health.to_dict(), indent=2))
        else:
            print(f"Overall Status: {health.overall_status.value}")
            for component in health.components:
                status_icon = (
                    "✅"
                    if component.status == HealthStatus.HEALTHY
                    else "⚠️" if component.status == HealthStatus.DEGRADED else "❌"
                )
                print(
                    f"{status_icon} {component.name}: {component.message} ({component.response_time:.3f}s)"
                )
        sys.exit(0 if health.overall_status != HealthStatus.UNHEALTHY else 1)
    else:
        # Run as web server
        config = uvicorn.Config(
            app, host=args.host, port=args.port, log_level="info", access_log=False
        )
        server = uvicorn.Server(config)
        await server.serve()
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Health checker stopped")
    except Exception as e:
        logger.error(f"Health checker failed: {e}")
        sys.exit(1)
