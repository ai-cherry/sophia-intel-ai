#!/usr/bin/env python3
"""
Base MCP Server Contract Interface
Defines the fundamental contract that all MCP servers must implement
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel


class HealthStatus(Enum):
    """Health status for MCP servers"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CapabilityStatus(Enum):
    """Status of individual capabilities"""

    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"


class MCPRequest(BaseModel):
    """Standard MCP request format"""

    request_id: str
    client_id: str
    capability: str
    method: str
    parameters: Dict[str, Any] = {}
    timeout: Optional[int] = 30
    priority: int = 5  # 1-10, where 1 is highest
    metadata: Dict[str, Any] = {}


class MCPResponse(BaseModel):
    """Standard MCP response format"""

    request_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_time: float
    server_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class CapabilityDeclaration(BaseModel):
    """Capability declaration for MCP servers"""

    name: str
    methods: List[str]
    description: str
    status: CapabilityStatus = CapabilityStatus.AVAILABLE
    requirements: List[str] = []
    dependencies: List[str] = []
    configuration: Dict[str, Any] = {}
    performance_metrics: Dict[str, Any] = {}


class HealthCheckResult(BaseModel):
    """Health check result"""

    status: HealthStatus
    timestamp: datetime
    response_time: float
    details: Dict[str, Any] = {}
    capabilities_status: Dict[str, CapabilityStatus] = {}
    error_message: Optional[str] = None


class ConnectionInfo(BaseModel):
    """Connection information"""

    client_id: str
    connected_at: datetime
    last_activity: datetime
    request_count: int = 0
    error_count: int = 0
    client_metadata: Dict[str, Any] = {}


class BaseMCPServerContract(ABC):
    """
    Base contract interface that all MCP servers must implement
    Provides standardized methods for health checks, capability management, and request handling
    """

    def __init__(self, server_id: str, name: str, version: str = "1.0.0"):
        self.server_id = server_id
        self.name = name
        self.version = version
        self.capabilities: Dict[str, CapabilityDeclaration] = {}
        self.active_connections: Dict[str, ConnectionInfo] = {}
        self.server_start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0

    # Core Abstract Methods

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the MCP server and its capabilities"""
        pass

    @abstractmethod
    async def shutdown(self):
        """Gracefully shutdown the MCP server"""
        pass

    @abstractmethod
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an incoming MCP request"""
        pass

    @abstractmethod
    async def get_capabilities(self) -> Dict[str, CapabilityDeclaration]:
        """Get all available capabilities"""
        pass

    @abstractmethod
    async def perform_health_check(self) -> HealthCheckResult:
        """Perform comprehensive health check"""
        pass

    # Connection Management

    async def register_connection(self, client_id: str, metadata: Dict[str, Any] = None) -> bool:
        """Register a new client connection"""
        try:
            self.active_connections[client_id] = ConnectionInfo(
                client_id=client_id,
                connected_at=datetime.now(),
                last_activity=datetime.now(),
                client_metadata=metadata or {},
            )
            return True
        except Exception:
            return False

    async def unregister_connection(self, client_id: str) -> bool:
        """Unregister a client connection"""
        try:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            return True
        except Exception:
            return False

    async def update_connection_activity(self, client_id: str):
        """Update last activity time for a connection"""
        if client_id in self.active_connections:
            self.active_connections[client_id].last_activity = datetime.now()
            self.active_connections[client_id].request_count += 1

    # Capability Management

    async def register_capability(self, capability: CapabilityDeclaration) -> bool:
        """Register a new capability"""
        try:
            self.capabilities[capability.name] = capability
            return True
        except Exception:
            return False

    async def unregister_capability(self, capability_name: str) -> bool:
        """Unregister a capability"""
        try:
            if capability_name in self.capabilities:
                del self.capabilities[capability_name]
            return True
        except Exception:
            return False

    async def update_capability_status(self, capability_name: str, status: CapabilityStatus):
        """Update the status of a capability"""
        if capability_name in self.capabilities:
            self.capabilities[capability_name].status = status

    async def is_capability_available(self, capability_name: str) -> bool:
        """Check if a capability is available"""
        if capability_name not in self.capabilities:
            return False
        return self.capabilities[capability_name].status == CapabilityStatus.AVAILABLE

    # Metrics and Monitoring

    async def get_server_metrics(self) -> Dict[str, Any]:
        """Get comprehensive server metrics"""
        uptime = (datetime.now() - self.server_start_time).total_seconds()

        # Calculate connection metrics
        total_requests = sum(conn.request_count for conn in self.active_connections.values())
        total_errors = sum(conn.error_count for conn in self.active_connections.values())

        return {
            "server_id": self.server_id,
            "name": self.name,
            "version": self.version,
            "uptime_seconds": uptime,
            "start_time": self.server_start_time.isoformat(),
            "active_connections": len(self.active_connections),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / max(total_requests, 1),
            "capabilities_count": len(self.capabilities),
            "available_capabilities": len(
                [c for c in self.capabilities.values() if c.status == CapabilityStatus.AVAILABLE]
            ),
            "timestamp": datetime.now().isoformat(),
        }

    async def get_connection_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics for all connections"""
        return [
            {
                "client_id": conn.client_id,
                "connected_at": conn.connected_at.isoformat(),
                "last_activity": conn.last_activity.isoformat(),
                "connection_duration": (datetime.now() - conn.connected_at).total_seconds(),
                "request_count": conn.request_count,
                "error_count": conn.error_count,
                "client_metadata": conn.client_metadata,
            }
            for conn in self.active_connections.values()
        ]

    # Utility Methods

    async def validate_request(self, request: MCPRequest) -> tuple[bool, Optional[str]]:
        """Validate an incoming request"""

        # Check if capability exists
        if request.capability not in self.capabilities:
            return False, f"Unknown capability: {request.capability}"

        # Check if capability is available
        if not await self.is_capability_available(request.capability):
            return False, f"Capability unavailable: {request.capability}"

        # Check if method is supported
        capability = self.capabilities[request.capability]
        if request.method not in capability.methods:
            return (
                False,
                f"Unsupported method '{request.method}' for capability '{request.capability}'",
            )

        # Validate parameters based on capability requirements
        for req in capability.requirements:
            if req not in request.parameters:
                return False, f"Missing required parameter: {req}"

        return True, None

    async def create_error_response(
        self,
        request: MCPRequest,
        error_message: str,
        error_code: str = "GENERAL_ERROR",
        execution_time: float = 0.0,
    ) -> MCPResponse:
        """Create standardized error response"""
        return MCPResponse(
            request_id=request.request_id,
            success=False,
            error=error_message,
            error_code=error_code,
            execution_time=execution_time,
            server_id=self.server_id,
            timestamp=datetime.now(),
        )

    async def create_success_response(
        self, request: MCPRequest, result: Dict[str, Any], execution_time: float
    ) -> MCPResponse:
        """Create standardized success response"""
        return MCPResponse(
            request_id=request.request_id,
            success=True,
            result=result,
            execution_time=execution_time,
            server_id=self.server_id,
            timestamp=datetime.now(),
        )

    # Server Information

    async def get_server_info(self) -> Dict[str, Any]:
        """Get comprehensive server information"""
        return {
            "server_id": self.server_id,
            "name": self.name,
            "version": self.version,
            "start_time": self.server_start_time.isoformat(),
            "capabilities": {
                name: {
                    "name": cap.name,
                    "methods": cap.methods,
                    "description": cap.description,
                    "status": cap.status.value,
                    "requirements": cap.requirements,
                    "dependencies": cap.dependencies,
                }
                for name, cap in self.capabilities.items()
            },
            "metrics": await self.get_server_metrics(),
            "health": await self.perform_health_check(),
        }
