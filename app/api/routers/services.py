"""
Sophia Intel AI - Service Management API

This module provides FastAPI endpoints for managing services through the
Service Orchestrator, including status monitoring, service control, and
dependency management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from app.core.service_orchestrator import get_orchestrator, ServiceStatus
from app.core.service_registry import ServiceType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/services", tags=["Service Management"])


# Response Models
class ServiceStatusResponse(BaseModel):
    """Response model for service status."""
    name: str
    status: str
    type: str
    port: int
    url: str
    health_status: bool
    pid: Optional[int] = None
    uptime: Optional[float] = None
    restart_count: int = 0
    error_message: Optional[str] = None
    dependencies: List[str] = []
    tags: List[str] = []


class ServiceSummaryResponse(BaseModel):
    """Response model for service summary."""
    running: int = 0
    stopped: int = 0
    error: int = 0
    starting: int = 0
    stopping: int = 0


class StatusReportResponse(BaseModel):
    """Response model for comprehensive status report."""
    timestamp: float
    total_services: int
    services: Dict[str, ServiceStatusResponse]
    summary: ServiceSummaryResponse


class PortMappingResponse(BaseModel):
    """Response model for port mappings."""
    ports: Dict[str, int]


class HealthResponse(BaseModel):
    """Response model for aggregated health status."""
    overall_health: str
    healthy_services: int
    total_services: int
    unhealthy_services: List[str] = []
    health_checks: Dict[str, bool] = {}


class DependencyGraphResponse(BaseModel):
    """Response model for dependency graph."""
    dependencies: Dict[str, List[str]]
    startup_order: List[str]


class ServiceOperationResponse(BaseModel):
    """Response model for service operations."""
    success: bool
    message: str
    service_name: str
    new_status: Optional[str] = None


# Endpoints

@router.get("/status", response_model=StatusReportResponse)
async def get_services_status():
    """
    Get comprehensive status report for all services.
    
    Returns detailed information about all registered services including
    their current status, health, uptime, and other metadata.
    """
    try:
        orchestrator = get_orchestrator()
        report = orchestrator.get_status_report()
        
        # Convert to Pydantic models
        services = {}
        for name, service_info in report["services"].items():
            services[name] = ServiceStatusResponse(**service_info)
        
        summary = ServiceSummaryResponse(**report["summary"])
        
        return StatusReportResponse(
            timestamp=report["timestamp"],
            total_services=report["total_services"],
            services=services,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")


@router.get("/status/{service_name}", response_model=ServiceStatusResponse)
async def get_service_status(
    service_name: str = Path(..., description="Name of the service")
):
    """
    Get status for a specific service.
    
    Args:
        service_name: Name of the service to check
        
    Returns:
        Detailed status information for the specified service
    """
    try:
        orchestrator = get_orchestrator()
        service_info = orchestrator.get_service_status(service_name)
        
        if not service_info:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        return ServiceStatusResponse(**service_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")


@router.get("/ports", response_model=PortMappingResponse)
async def get_port_mappings():
    """
    Get port mappings for all services.
    
    Returns a mapping of service names to their assigned ports.
    """
    try:
        orchestrator = get_orchestrator()
        ports = orchestrator.get_ports_mapping()
        
        return PortMappingResponse(ports=ports)
        
    except Exception as e:
        logger.error(f"Error getting port mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get port mappings: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def get_aggregated_health():
    """
    Get aggregated health status for all services.
    
    Performs health checks on all running services and returns an
    overall health assessment.
    """
    try:
        orchestrator = get_orchestrator()
        health_checks = await orchestrator.health_check_all()
        
        healthy_count = sum(1 for healthy in health_checks.values() if healthy)
        total_count = len(health_checks)
        unhealthy_services = [name for name, healthy in health_checks.items() if not healthy]
        
        # Determine overall health
        if total_count == 0:
            overall_health = "unknown"
        elif healthy_count == total_count:
            overall_health = "healthy"
        elif healthy_count > 0:
            overall_health = "degraded"
        else:
            overall_health = "unhealthy"
        
        return HealthResponse(
            overall_health=overall_health,
            healthy_services=healthy_count,
            total_services=total_count,
            unhealthy_services=unhealthy_services,
            health_checks=health_checks
        )
        
    except Exception as e:
        logger.error(f"Error getting aggregated health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")


@router.post("/{service_name}/start", response_model=ServiceOperationResponse)
async def start_service(
    service_name: str = Path(..., description="Name of the service to start"),
    wait_for_health: bool = Query(True, description="Wait for health check to pass")
):
    """
    Start a specific service.
    
    Args:
        service_name: Name of the service to start
        wait_for_health: Whether to wait for health check to pass before returning
        
    Returns:
        Operation result with success status and new service status
    """
    try:
        orchestrator = get_orchestrator()
        
        logger.info(f"Starting service {service_name} via API")
        success = await orchestrator.start_service(service_name, wait_for_health=wait_for_health)
        
        if success:
            status_info = orchestrator.get_service_status(service_name)
            new_status = status_info["status"] if status_info else "unknown"
            
            return ServiceOperationResponse(
                success=True,
                message=f"Service {service_name} started successfully",
                service_name=service_name,
                new_status=new_status
            )
        else:
            status_info = orchestrator.get_service_status(service_name)
            error_msg = status_info.get("error_message", "Unknown error") if status_info else "Service not found"
            
            return ServiceOperationResponse(
                success=False,
                message=f"Failed to start service {service_name}: {error_msg}",
                service_name=service_name,
                new_status=status_info["status"] if status_info else "error"
            )
        
    except Exception as e:
        logger.error(f"Error starting service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start service: {str(e)}")


@router.post("/{service_name}/stop", response_model=ServiceOperationResponse)
async def stop_service(
    service_name: str = Path(..., description="Name of the service to stop"),
    force: bool = Query(False, description="Force stop the service if graceful stop fails")
):
    """
    Stop a specific service.
    
    Args:
        service_name: Name of the service to stop
        force: Whether to force stop if graceful stop fails
        
    Returns:
        Operation result with success status and new service status
    """
    try:
        orchestrator = get_orchestrator()
        
        logger.info(f"Stopping service {service_name} via API (force={force})")
        success = await orchestrator.stop_service(service_name, force=force)
        
        if success:
            return ServiceOperationResponse(
                success=True,
                message=f"Service {service_name} stopped successfully",
                service_name=service_name,
                new_status="stopped"
            )
        else:
            status_info = orchestrator.get_service_status(service_name)
            error_msg = status_info.get("error_message", "Unknown error") if status_info else "Service not found"
            
            return ServiceOperationResponse(
                success=False,
                message=f"Failed to stop service {service_name}: {error_msg}",
                service_name=service_name,
                new_status=status_info["status"] if status_info else "error"
            )
        
    except Exception as e:
        logger.error(f"Error stopping service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop service: {str(e)}")


@router.post("/{service_name}/restart", response_model=ServiceOperationResponse)
async def restart_service(
    service_name: str = Path(..., description="Name of the service to restart")
):
    """
    Restart a specific service.
    
    Args:
        service_name: Name of the service to restart
        
    Returns:
        Operation result with success status and new service status
    """
    try:
        orchestrator = get_orchestrator()
        
        logger.info(f"Restarting service {service_name} via API")
        success = await orchestrator.restart_service(service_name)
        
        if success:
            status_info = orchestrator.get_service_status(service_name)
            new_status = status_info["status"] if status_info else "unknown"
            
            return ServiceOperationResponse(
                success=True,
                message=f"Service {service_name} restarted successfully",
                service_name=service_name,
                new_status=new_status
            )
        else:
            status_info = orchestrator.get_service_status(service_name)
            error_msg = status_info.get("error_message", "Unknown error") if status_info else "Service not found"
            
            return ServiceOperationResponse(
                success=False,
                message=f"Failed to restart service {service_name}: {error_msg}",
                service_name=service_name,
                new_status=status_info["status"] if status_info else "error"
            )
        
    except Exception as e:
        logger.error(f"Error restarting service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart service: {str(e)}")


@router.get("/dependencies", response_model=DependencyGraphResponse)
async def get_dependency_graph():
    """
    Get the service dependency graph.
    
    Returns the dependency relationships between services and the
    recommended startup order.
    """
    try:
        orchestrator = get_orchestrator()
        dependencies = orchestrator.get_dependency_graph()
        startup_order = orchestrator.startup_order
        
        return DependencyGraphResponse(
            dependencies=dependencies,
            startup_order=startup_order
        )
        
    except Exception as e:
        logger.error(f"Error getting dependency graph: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dependency graph: {str(e)}")


@router.post("/start-all")
async def start_all_services(
    service_types: Optional[List[str]] = Query(None, description="Service types to start (core, optional, dev)")
):
    """
    Start all services or services of specific types.
    
    Args:
        service_types: Optional list of service types to start. If not provided, starts all enabled services.
        
    Returns:
        Results of starting each service
    """
    try:
        orchestrator = get_orchestrator()
        
        # Convert string service types to enum
        types_to_start = None
        if service_types:
            try:
                types_to_start = [ServiceType(t) for t in service_types]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid service type: {str(e)}")
        
        logger.info(f"Starting all services via API (types: {service_types})")
        results = await orchestrator.start_all(service_types=types_to_start)
        
        return {
            "success": all(results.values()),
            "message": f"Started {sum(results.values())} of {len(results)} services",
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting all services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start services: {str(e)}")


@router.post("/stop-all")
async def stop_all_services(
    force: bool = Query(False, description="Force stop all services")
):
    """
    Stop all running services.
    
    Args:
        force: Whether to force stop services that don't stop gracefully
        
    Returns:
        Results of stopping each service
    """
    try:
        orchestrator = get_orchestrator()
        
        logger.info(f"Stopping all services via API (force={force})")
        results = await orchestrator.stop_all(force=force)
        
        return {
            "success": all(results.values()),
            "message": f"Stopped {sum(results.values())} of {len(results)} services",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error stopping all services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop services: {str(e)}")


@router.get("/types/{service_type}")
async def get_services_by_type(
    service_type: str = Path(..., description="Service type (core, optional, dev)")
):
    """
    Get all services of a specific type.
    
    Args:
        service_type: Type of services to retrieve
        
    Returns:
        List of services matching the specified type
    """
    try:
        # Validate service type
        try:
            svc_type = ServiceType(service_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid service type: {service_type}")
        
        orchestrator = get_orchestrator()
        
        # Filter services by type
        services = {}
        for name, service_def in orchestrator.services.items():
            if service_def.service_type == svc_type:
                status_info = orchestrator.get_service_status(name)
                if status_info:
                    services[name] = ServiceStatusResponse(**status_info)
        
        return {
            "service_type": service_type,
            "count": len(services),
            "services": services
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting services by type {service_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get services by type: {str(e)}")


# Health check endpoint for the services API itself
@router.get("/health-check")
async def services_api_health_check():
    """Health check for the services API itself."""
    return {
        "status": "healthy",
        "service": "services_api",
        "timestamp": __import__("time").time()
    }