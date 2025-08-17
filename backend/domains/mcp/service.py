"""
MCP Service - Lambda Labs GH200 server management and MCP operations
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
from loguru import logger

from .models import (
    MCPServer, LambdaServer, MCPServerStatus, MCPOperation, 
    MCPHealthCheck, MCPDashboardData, ServerStatus, MCPServerType
)
from .lambda_manager import LambdaServerManager


class MCPService:
    """
    MCP Service for managing Lambda Labs GH200 servers and MCP operations
    Provides dashboard data, health monitoring, and server control
    """
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.lambda_manager = LambdaServerManager()
        self.health_check_tasks: Dict[str, asyncio.Task] = {}
        self.operations: Dict[str, MCPOperation] = {}
        
        # Performance tracking
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize with Lambda Labs servers
        self._initialize_lambda_servers()
        
        logger.info("MCPService initialized")
    
    def _initialize_lambda_servers(self):
        """Initialize Lambda Labs GH200 servers"""
        # Primary Lambda Labs server
        primary_server = LambdaServer(
            server_id="lambda_primary",
            name="SOPHIA GH200 Primary",
            server_type=MCPServerType.LAMBDA_INFERENCE,
            host="192.222.51.223",
            port=8000,
            endpoint="/health",
            instance_id="07c099ae5ceb48ffaccd5c91b0560c0e",
            region="us-east-3",
            custom_domain="inference-primary.sophia-intel.ai",
            tags=["primary", "gh200", "inference"]
        )
        
        # Secondary Lambda Labs server
        secondary_server = LambdaServer(
            server_id="lambda_secondary",
            name="SOPHIA GH200 Secondary",
            server_type=MCPServerType.LAMBDA_INFERENCE,
            host="192.222.50.242",
            port=8000,
            endpoint="/health",
            instance_id="9095c29b3292440fb81136810b0785a3",
            region="us-east-3",
            custom_domain="inference-secondary.sophia-intel.ai",
            tags=["secondary", "gh200", "inference"]
        )
        
        self.servers[primary_server.server_id] = primary_server
        self.servers[secondary_server.server_id] = secondary_server
        
        # Start health monitoring
        self._start_health_monitoring()
    
    async def get_dashboard_data(self) -> MCPDashboardData:
        """Get comprehensive dashboard data for MCP servers"""
        try:
            # Get current server statuses
            server_statuses = []
            lambda_servers = []
            
            for server in self.servers.values():
                status = await self._get_server_status(server)
                server_statuses.append(status)
                
                if isinstance(server, LambdaServer):
                    lambda_servers.append(server)
            
            # Calculate summary metrics
            total_servers = len(self.servers)
            healthy_servers = sum(1 for status in server_statuses if status.is_healthy)
            unhealthy_servers = total_servers - healthy_servers
            
            # Performance metrics
            response_times = [s.response_time for s in server_statuses if s.response_time > 0]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            total_rpm = sum(s.requests_per_minute for s in server_statuses)
            error_rates = [s.error_rate for s in server_statuses if s.error_rate >= 0]
            overall_error_rate = sum(error_rates) / len(error_rates) if error_rates else 0
            
            # Lambda Labs specific metrics
            gpu_utilizations = [s.gpu_usage for s in server_statuses if s.gpu_usage is not None]
            total_gpu_utilization = sum(gpu_utilizations) / len(gpu_utilizations) if gpu_utilizations else None
            
            # Available models across all Lambda servers
            available_models = []
            for server in lambda_servers:
                available_models.extend(server.loaded_models)
            available_models = list(set(available_models))  # Remove duplicates
            
            # Recent operations (last 10)
            recent_operations = sorted(
                self.operations.values(),
                key=lambda x: x.requested_at,
                reverse=True
            )[:10]
            
            # Active alerts
            active_alerts = []
            for status in server_statuses:
                if not status.is_healthy:
                    active_alerts.append(f"Server {status.server_id} is unhealthy: {status.last_error}")
                if status.error_rate > 5.0:
                    active_alerts.append(f"Server {status.server_id} has high error rate: {status.error_rate:.1f}%")
                if status.response_time > 5.0:
                    active_alerts.append(f"Server {status.server_id} has slow response time: {status.response_time:.2f}s")
            
            return MCPDashboardData(
                total_servers=total_servers,
                healthy_servers=healthy_servers,
                unhealthy_servers=unhealthy_servers,
                servers=server_statuses,
                average_response_time=avg_response_time,
                total_requests_per_minute=total_rpm,
                overall_error_rate=overall_error_rate,
                lambda_servers=lambda_servers,
                total_gpu_utilization=total_gpu_utilization,
                available_models=available_models,
                recent_operations=recent_operations,
                active_alerts=active_alerts
            )
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            raise
    
    async def get_server_status(self, server_id: str) -> Optional[MCPServerStatus]:
        """Get detailed status for a specific server"""
        server = self.servers.get(server_id)
        if not server:
            return None
        
        return await self._get_server_status(server)
    
    async def perform_operation(self, server_id: str, operation_type: str, parameters: Optional[Dict[str, Any]] = None) -> MCPOperation:
        """Perform operation on MCP server"""
        server = self.servers.get(server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")
        
        # Create operation record
        operation_id = f"op_{int(time.time() * 1000)}"
        operation = MCPOperation(
            operation_id=operation_id,
            server_id=server_id,
            operation_type=operation_type,
            parameters=parameters or {}
        )
        
        self.operations[operation_id] = operation
        
        try:
            operation.status = "running"
            operation.started_at = datetime.now()
            
            # Perform the operation
            if operation_type == "start":
                result = await self._start_server(server)
            elif operation_type == "stop":
                result = await self._stop_server(server)
            elif operation_type == "restart":
                result = await self._restart_server(server)
            elif operation_type == "health":
                result = await self._health_check_server(server)
            else:
                raise ValueError(f"Unknown operation type: {operation_type}")
            
            operation.status = "completed"
            operation.result = result
            
        except Exception as e:
            operation.status = "failed"
            operation.error_message = str(e)
            logger.error(f"Operation {operation_id} failed: {e}")
        
        finally:
            operation.completed_at = datetime.now()
            if operation.started_at:
                operation.duration = (operation.completed_at - operation.started_at).total_seconds()
        
        return operation
    
    async def add_server(self, server_config: Dict[str, Any]) -> MCPServer:
        """Add new MCP server"""
        server_id = server_config.get("server_id") or f"server_{int(time.time())}"
        
        if server_config.get("server_type") == MCPServerType.LAMBDA_INFERENCE:
            server = LambdaServer(server_id=server_id, **server_config)
        else:
            server = MCPServer(server_id=server_id, **server_config)
        
        self.servers[server_id] = server
        
        # Start health monitoring for new server
        await self._start_server_health_monitoring(server)
        
        logger.info(f"Added server {server_id}: {server.name}")
        return server
    
    async def remove_server(self, server_id: str) -> bool:
        """Remove MCP server"""
        if server_id not in self.servers:
            return False
        
        # Stop health monitoring
        if server_id in self.health_check_tasks:
            self.health_check_tasks[server_id].cancel()
            del self.health_check_tasks[server_id]
        
        # Remove server
        del self.servers[server_id]
        
        # Clean up performance history
        if server_id in self.performance_history:
            del self.performance_history[server_id]
        
        logger.info(f"Removed server {server_id}")
        return True
    
    async def get_server_performance_history(self, server_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance history for a server"""
        if server_id not in self.performance_history:
            return []
        
        # Filter by time range
        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = self.performance_history[server_id]
        
        return [
            entry for entry in history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
    
    # Private methods
    
    async def _get_server_status(self, server: MCPServer) -> MCPServerStatus:
        """Get detailed status for a server"""
        try:
            # Perform health check
            health_check = await self._health_check_server(server)
            
            # Calculate uptime
            uptime_seconds = 0
            if server.last_health_check:
                uptime_seconds = (datetime.now() - server.created_at).total_seconds()
            
            # Get performance metrics from history
            history = self.performance_history.get(server.server_id, [])
            recent_history = history[-60:]  # Last 60 checks (30 minutes if every 30s)
            
            requests_per_minute = 0
            error_rate = 0
            
            if recent_history:
                # Calculate requests per minute (simulated)
                requests_per_minute = len([h for h in recent_history if h.get("healthy", False)]) * 2
                
                # Calculate error rate
                errors = len([h for h in recent_history if not h.get("healthy", True)])
                error_rate = (errors / len(recent_history)) * 100
            
            # GPU usage for Lambda servers
            gpu_usage = None
            cpu_usage = None
            memory_usage = None
            
            if isinstance(server, LambdaServer) and health_check.is_healthy:
                # Simulate GPU usage (in real implementation, get from server)
                gpu_usage = server.gpu_utilization or 0.0
                cpu_usage = 25.0  # Simulated
                memory_usage = 45.0  # Simulated
            
            return MCPServerStatus(
                server_id=server.server_id,
                status=server.status,
                is_healthy=health_check.is_healthy,
                health_details={"connectivity": health_check.connectivity, "service_running": health_check.service_running},
                last_error=health_check.error_message,
                response_time=health_check.response_time,
                uptime_seconds=uptime_seconds,
                requests_per_minute=requests_per_minute,
                error_rate=error_rate,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                gpu_usage=gpu_usage,
                last_restart=None  # Would track actual restarts
            )
            
        except Exception as e:
            logger.error(f"Failed to get status for server {server.server_id}: {e}")
            return MCPServerStatus(
                server_id=server.server_id,
                status=ServerStatus.ERROR,
                is_healthy=False,
                health_details={},
                last_error=str(e),
                response_time=0.0,
                uptime_seconds=0.0
            )
    
    async def _health_check_server(self, server: MCPServer) -> MCPHealthCheck:
        """Perform health check on server"""
        start_time = time.time()
        
        try:
            # Use custom domain if available (for Lambda servers)
            host = server.host
            if isinstance(server, LambdaServer) and server.custom_domain:
                host = server.custom_domain
            
            url = f"http://{host}:{server.port}{server.endpoint}"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=server.timeout)) as session:
                async with session.get(url) as response:
                    response_time = time.time() - start_time
                    
                    is_healthy = response.status == 200
                    
                    # Update server status
                    server.status = ServerStatus.ACTIVE if is_healthy else ServerStatus.ERROR
                    server.last_health_check = datetime.now()
                    server.response_time = response_time
                    
                    # For Lambda servers, check additional details
                    gpu_available = None
                    models_loaded = None
                    inference_ready = None
                    
                    if isinstance(server, LambdaServer) and is_healthy:
                        try:
                            data = await response.json()
                            gpu_available = data.get("gpu_available", True)
                            models_loaded = len(data.get("models", [])) > 0
                            inference_ready = data.get("inference_ready", True)
                            
                            # Update server model info
                            server.loaded_models = data.get("models", [])
                            server.gpu_utilization = data.get("gpu_utilization", 0.0)
                            
                        except Exception as e:
                            logger.warning(f"Failed to parse health response for {server.server_id}: {e}")
                    
                    health_check = MCPHealthCheck(
                        server_id=server.server_id,
                        is_healthy=is_healthy,
                        response_time=response_time,
                        status_code=response.status,
                        connectivity=True,
                        service_running=is_healthy,
                        gpu_available=gpu_available,
                        models_loaded=models_loaded,
                        inference_ready=inference_ready
                    )
                    
                    # Record performance history
                    self._record_performance(server.server_id, {
                        "timestamp": datetime.now().isoformat(),
                        "healthy": is_healthy,
                        "response_time": response_time,
                        "status_code": response.status
                    })
                    
                    return health_check
                    
        except Exception as e:
            response_time = time.time() - start_time
            
            # Update server status
            server.status = ServerStatus.ERROR
            server.last_health_check = datetime.now()
            server.response_time = response_time
            server.error_count += 1
            
            error_message = str(e)
            logger.warning(f"Health check failed for {server.server_id}: {error_message}")
            
            health_check = MCPHealthCheck(
                server_id=server.server_id,
                is_healthy=False,
                response_time=response_time,
                connectivity=False,
                service_running=False,
                error_message=error_message
            )
            
            # Record performance history
            self._record_performance(server.server_id, {
                "timestamp": datetime.now().isoformat(),
                "healthy": False,
                "response_time": response_time,
                "error": error_message
            })
            
            return health_check
    
    def _record_performance(self, server_id: str, data: Dict[str, Any]):
        """Record performance data for server"""
        if server_id not in self.performance_history:
            self.performance_history[server_id] = []
        
        history = self.performance_history[server_id]
        history.append(data)
        
        # Keep only last 24 hours of data (assuming 30s intervals = 2880 entries)
        if len(history) > 2880:
            self.performance_history[server_id] = history[-2880:]
    
    async def _start_server(self, server: MCPServer) -> Dict[str, Any]:
        """Start server (Lambda Labs specific)"""
        if isinstance(server, LambdaServer):
            return await self.lambda_manager.start_instance(server.instance_id)
        else:
            return {"message": "Start operation not supported for this server type"}
    
    async def _stop_server(self, server: MCPServer) -> Dict[str, Any]:
        """Stop server (Lambda Labs specific)"""
        if isinstance(server, LambdaServer):
            return await self.lambda_manager.stop_instance(server.instance_id)
        else:
            return {"message": "Stop operation not supported for this server type"}
    
    async def _restart_server(self, server: MCPServer) -> Dict[str, Any]:
        """Restart server (Lambda Labs specific)"""
        if isinstance(server, LambdaServer):
            return await self.lambda_manager.restart_instance(server.instance_id)
        else:
            return {"message": "Restart operation not supported for this server type"}
    
    def _start_health_monitoring(self):
        """Start health monitoring for all servers"""
        for server in self.servers.values():
            asyncio.create_task(self._start_server_health_monitoring(server))
    
    async def _start_server_health_monitoring(self, server: MCPServer):
        """Start health monitoring for a specific server"""
        async def health_monitor():
            while server.server_id in self.servers:
                try:
                    await self._health_check_server(server)
                    await asyncio.sleep(server.health_check_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitoring error for {server.server_id}: {e}")
                    await asyncio.sleep(server.health_check_interval)
        
        task = asyncio.create_task(health_monitor())
        self.health_check_tasks[server.server_id] = task
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for MCP service"""
        return {
            "status": "healthy",
            "total_servers": len(self.servers),
            "active_health_monitors": len(self.health_check_tasks),
            "total_operations": len(self.operations)
        }

