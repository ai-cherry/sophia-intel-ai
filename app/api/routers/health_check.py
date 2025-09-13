"""
Unified Health Check API Router
Provides comprehensive health status for all services
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from app.core.health_monitor import get_health_monitor, HealthStatus

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    monitor = await get_health_monitor()
    overall_status = monitor.get_overall_status()
    
    status_code = 200
    if overall_status == HealthStatus.UNHEALTHY:
        status_code = 503
    elif overall_status == HealthStatus.DEGRADED:
        status_code = 200  # Still operational, just degraded
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status.value,
            "message": f"System is {overall_status.value}"
        }
    )


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with all service statuses"""
    monitor = await get_health_monitor()
    report = monitor.get_health_report()
    
    overall_status = monitor.get_overall_status()
    status_code = 200
    if overall_status == HealthStatus.UNHEALTHY:
        status_code = 503
    
    return JSONResponse(
        status_code=status_code,
        content=report
    )


@router.get("/service/{service_name}")
async def service_health_check(service_name: str):
    """Health check for specific service"""
    monitor = await get_health_monitor()
    
    if service_name not in monitor.services:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    # Trigger fresh check
    health = await monitor.check_service(service_name)
    
    status_code = 200
    if health.status == HealthStatus.UNHEALTHY:
        status_code = 503
    elif health.status == HealthStatus.DEGRADED:
        status_code = 200
    
    return JSONResponse(
        status_code=status_code,
        content=health.to_dict()
    )


@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    monitor = await get_health_monitor()
    overall_status = monitor.get_overall_status()
    
    # For readiness, we only fail if system is unhealthy
    # Degraded is still ready to serve traffic
    if overall_status == HealthStatus.UNHEALTHY:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "status": overall_status.value}
        )
    
    return JSONResponse(
        status_code=200,
        content={"ready": True, "status": overall_status.value}
    )


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    # Simple liveness check - if we can respond, we're alive
    return JSONResponse(
        status_code=200,
        content={"alive": True}
    )


@router.post("/refresh")
async def refresh_health_checks():
    """Manually trigger health checks for all services"""
    monitor = await get_health_monitor()
    await monitor.check_all_services()
    report = monitor.get_health_report()
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Health checks refreshed",
            "report": report
        }
    )