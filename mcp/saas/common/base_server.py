"""
Base MCP Server with Swarm Integration
Provides standardized foundation for all MCP services with Swarm system awareness
"""
from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from typing import Callable, Dict, Any, Optional, Type, List, Union
from pydantic import BaseModel, Field
import time
import os
import asyncio
import json
from pathlib import Path

class ContextRequest(BaseModel):
    """Base model for context storage requests"""
    session_id: str = Field(..., description="Session identifier")
    content: str = Field(..., description="Content to store")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    context_type: str = Field(default="general", description="Type of context")
    swarm_stage: Optional[str] = Field(None, description="Current swarm stage if applicable")

class ContextResponse(BaseModel):
    """Standard response for context operations"""
    status: str
    id: str
    timestamp: Optional[float] = None

class SearchRequest(BaseModel):
    """Base model for context search requests"""
    query: str = Field(..., description="Search query")
    session_id: Optional[str] = Field(None, description="Session to search within")
    limit: int = Field(default=10, description="Maximum number of results")
    filters: Dict[str, Any] = Field(default={}, description="Additional search filters")
    swarm_stage: Optional[str] = Field(None, description="Current swarm stage if applicable")

class SearchResponse(BaseModel):
    """Standard response for search operations"""
    results: List[Dict[str, Any]]
    count: int
    query: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: Optional[str] = None
    uptime: Optional[float] = None

class SwarmHandoffRequest(BaseModel):
    """Request model for Swarm handoffs"""
    session_id: str
    from_stage: str
    to_stage: str
    artifact: str
    metadata: Dict[str, Any] = Field(default={})

class BaseMCPServer:
    """
    Base MCP Server with standardized patterns and Swarm integration
    
    Features:
    - FastAPI application setup with CORS and middleware
    - Health check and readiness endpoints
    - Swarm integration for agent workflows
    - Standardized error handling and logging
    - Telemetry recording for performance monitoring
    """
    
    def __init__(self, title: str, description: str, version: str = "0.1.0"):
        self.title = title
        self.description = description
        self.version = version
        self.start_time = time.time()
        
        self.app = FastAPI(
            title=title,
            description=description,
            version=version,
        )
        
        self._setup_middleware()
        self._setup_routes()
        self._setup_exception_handlers()
        self._setup_swarm_integration()
        
    def _setup_middleware(self):
        """Setup CORS, logging, and metrics middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @self.app.middleware("http")
        async def logging_middleware(request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log the request
            logger.info(
                f"{request.method} {request.url.path} "
                f"completed in {process_time:.4f}s with status {response.status_code}"
            )
            
            # Add to swarm telemetry if available
            if hasattr(self, 'swarm_telemetry') and callable(self.swarm_telemetry):
                try:
                    await self.swarm_telemetry({
                        "type": "http_request",
                        "endpoint": request.url.path,
                        "method": request.method,
                        "duration": process_time,
                        "status_code": response.status_code,
                        "timestamp": time.time(),
                        "service": self.title
                    })
                except Exception as e:
                    logger.warning(f"Failed to record telemetry: {e}")
                    
            return response
            
    def _setup_routes(self):
        """Setup standard health check routes"""
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint"""
            return HealthResponse(
                status="ok", 
                service=self.title,
                version=self.version,
                uptime=time.time() - self.start_time
            )
            
        @self.app.get("/ready", response_model=HealthResponse)
        async def readiness_check():
            """Readiness check endpoint - override in subclasses for dependency checks"""
            # Subclasses can override this to check dependencies (DB, external services, etc.)
            return HealthResponse(
                status="ready", 
                service=self.title,
                version=self.version
            )
    
    def _setup_exception_handlers(self):
        """Setup standardized exception handling"""
        
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            logger.error(f"HTTP error on {request.url.path}: {exc.detail}")
            
            # Record in swarm telemetry
            if hasattr(self, 'swarm_telemetry') and callable(self.swarm_telemetry):
                try:
                    await self.swarm_telemetry({
                        "type": "http_error",
                        "error": exc.detail,
                        "status_code": exc.status_code,
                        "endpoint": request.url.path,
                        "timestamp": time.time(),
                        "service": self.title
                    })
                except:
                    pass
                    
            return {
                "error": exc.detail, 
                "status_code": exc.status_code,
                "service": self.title,
                "timestamp": time.time()
            }
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}")
            
            # Record in swarm telemetry
            if hasattr(self, 'swarm_telemetry') and callable(self.swarm_telemetry):
                try:
                    await self.swarm_telemetry({
                        "type": "exception",
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                        "endpoint": request.url.path,
                        "timestamp": time.time(),
                        "service": self.title
                    })
                except:
                    pass
                    
            return {
                "error": "Internal server error", 
                "status_code": 500,
                "service": self.title,
                "timestamp": time.time()
            }
    
    def _setup_swarm_integration(self):
        """Setup Swarm integration if enabled"""
        swarm_enabled = os.getenv("USE_SWARM", "1") == "1"
        
        if swarm_enabled:
            try:
                from mcp.saas.common.swarm_integration import SwarmIntegration
                self.swarm = SwarmIntegration()
                self.swarm_telemetry = self.swarm.record_telemetry
                
                # Add Swarm-specific endpoints
                @self.app.post("/swarm/handoff")
                async def swarm_handoff(request: SwarmHandoffRequest):
                    """Handle handoffs between Swarm agents"""
                    return await self.swarm.process_handoff({
                        "session_id": request.session_id,
                        "from_stage": request.from_stage,
                        "to_stage": request.to_stage,
                        "artifact": request.artifact,
                        "metadata": request.metadata,
                        "service": self.title
                    })
                
                @self.app.get("/swarm/status/{session_id}")
                async def swarm_status(session_id: str):
                    """Get current status of a Swarm session"""
                    return await self.swarm.get_status(session_id)
                
                @self.app.get("/swarm/telemetry/{session_id}")
                async def swarm_telemetry_history(session_id: str, limit: int = 100):
                    """Get telemetry history for a Swarm session"""
                    return await self.swarm.get_telemetry_history(session_id, limit)
                
                logger.info(f"Swarm integration enabled for {self.title}")
                
            except ImportError as e:
                logger.warning(f"Swarm integration requested but module not found: {e}")
                # Create a no-op telemetry function
                async def noop_telemetry(data: Dict[str, Any]) -> None:
                    pass
                self.swarm_telemetry = noop_telemetry
        else:
            logger.info(f"Swarm integration disabled for {self.title}")
            # Create a no-op telemetry function
            async def noop_telemetry(data: Dict[str, Any]) -> None:
                pass
            self.swarm_telemetry = noop_telemetry
    
    def register_route(
        self, 
        path: str, 
        method: str, 
        handler: Callable, 
        response_model: Optional[Type] = None, 
        dependencies: Optional[List] = None,
        **kwargs
    ):
        """Register a new route with the FastAPI application"""
        route_params = kwargs.copy()
        
        if response_model:
            route_params["response_model"] = response_model
        if dependencies:
            route_params["dependencies"] = dependencies
            
        self.app.add_api_route(
            path, 
            handler, 
            methods=[method.upper()], 
            **route_params
        )
        
        logger.info(f"Registered {method.upper()} {path} for {self.title}")
    
    def add_startup_handler(self, handler: Callable):
        """Add a startup event handler"""
        self.app.add_event_handler("startup", handler)
    
    def add_shutdown_handler(self, handler: Callable):
        """Add a shutdown event handler"""
        self.app.add_event_handler("shutdown", handler)
    
    async def record_metrics(self, metrics: Dict[str, Any]):
        """Record custom metrics through Swarm telemetry"""
        if hasattr(self, 'swarm_telemetry') and callable(self.swarm_telemetry):
            metrics.update({
                "type": "custom_metrics",
                "service": self.title,
                "timestamp": time.time()
            })
            await self.swarm_telemetry(metrics)