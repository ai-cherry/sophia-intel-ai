"""
MCP Domain Models - Lambda Labs server and MCP management
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ServerStatus(str, Enum):
    """Server status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


class MCPServerType(str, Enum):
    """MCP server type enumeration"""
    LAMBDA_INFERENCE = "lambda_inference"
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    MEMORY = "memory"
    PERSONA = "persona"


class MCPServer(BaseModel):
    """MCP server configuration and status"""
    server_id: str = Field(..., description="Unique server identifier")
    name: str = Field(..., description="Human-readable server name")
    server_type: MCPServerType = Field(..., description="Server type")
    
    # Connection details
    host: str = Field(..., description="Server host/IP address")
    port: int = Field(..., description="Server port")
    endpoint: str = Field(..., description="Health check endpoint")
    
    # Status
    status: ServerStatus = Field(ServerStatus.UNKNOWN, description="Current server status")
    last_health_check: Optional[datetime] = Field(None, description="Last health check timestamp")
    health_check_interval: int = Field(30, description="Health check interval in seconds")
    
    # Performance metrics
    response_time: Optional[float] = Field(None, description="Last response time in seconds")
    uptime: Optional[float] = Field(None, description="Server uptime in seconds")
    error_count: int = Field(0, description="Error count since last reset")
    
    # Configuration
    auto_restart: bool = Field(True, description="Auto-restart on failure")
    max_retries: int = Field(3, description="Maximum restart retries")
    timeout: int = Field(30, description="Request timeout in seconds")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list, description="Server tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LambdaServer(MCPServer):
    """Lambda Labs GH200 server specific configuration"""
    # Lambda Labs specific fields
    instance_id: str = Field(..., description="Lambda Labs instance ID")
    instance_type: str = Field("gpu_1x_h100", description="Instance type")
    region: str = Field(..., description="Server region")
    
    # GPU information
    gpu_type: str = Field("GH200", description="GPU type")
    gpu_memory: int = Field(97871, description="GPU memory in MB")
    gpu_utilization: Optional[float] = Field(None, description="GPU utilization percentage")
    gpu_temperature: Optional[float] = Field(None, description="GPU temperature in Celsius")
    
    # System resources
    cpu_count: int = Field(64, description="CPU core count")
    ram_gb: int = Field(432, description="RAM in GB")
    storage_gb: int = Field(4000, description="Storage in GB")
    
    # Inference specific
    loaded_models: List[str] = Field(default_factory=list, description="Currently loaded models")
    max_concurrent_requests: int = Field(10, description="Maximum concurrent requests")
    current_requests: int = Field(0, description="Current active requests")
    
    # Custom domain
    custom_domain: Optional[str] = Field(None, description="Custom domain name")


class MCPServerStatus(BaseModel):
    """Detailed server status information"""
    server_id: str = Field(..., description="Server identifier")
    status: ServerStatus = Field(..., description="Current status")
    
    # Health information
    is_healthy: bool = Field(..., description="Overall health status")
    health_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed health info")
    last_error: Optional[str] = Field(None, description="Last error message")
    
    # Performance metrics
    response_time: float = Field(..., description="Response time in seconds")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    requests_per_minute: float = Field(0.0, description="Requests per minute")
    error_rate: float = Field(0.0, description="Error rate percentage")
    
    # Resource usage (for Lambda servers)
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(None, description="Memory usage percentage")
    gpu_usage: Optional[float] = Field(None, description="GPU usage percentage")
    
    # Timestamps
    status_timestamp: datetime = Field(default_factory=datetime.now)
    last_restart: Optional[datetime] = Field(None, description="Last restart timestamp")


class MCPOperation(BaseModel):
    """MCP server operation request/response"""
    operation_id: str = Field(..., description="Unique operation identifier")
    server_id: str = Field(..., description="Target server identifier")
    operation_type: str = Field(..., description="Operation type: start, stop, restart, health")
    
    # Request details
    requested_at: datetime = Field(default_factory=datetime.now)
    requested_by: Optional[str] = Field(None, description="User who requested operation")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    
    # Response details
    status: str = Field("pending", description="Operation status: pending, running, completed, failed")
    result: Optional[Dict[str, Any]] = Field(None, description="Operation result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Timing
    started_at: Optional[datetime] = Field(None, description="Operation start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Operation completion timestamp")
    duration: Optional[float] = Field(None, description="Operation duration in seconds")


class MCPHealthCheck(BaseModel):
    """Health check result"""
    server_id: str = Field(..., description="Server identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Health status
    is_healthy: bool = Field(..., description="Overall health status")
    response_time: float = Field(..., description="Response time in seconds")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    
    # Detailed checks
    connectivity: bool = Field(..., description="Network connectivity")
    service_running: bool = Field(..., description="Service is running")
    dependencies_ok: bool = Field(True, description="Dependencies are healthy")
    
    # Resource checks (for Lambda servers)
    gpu_available: Optional[bool] = Field(None, description="GPU is available")
    models_loaded: Optional[bool] = Field(None, description="Models are loaded")
    inference_ready: Optional[bool] = Field(None, description="Ready for inference")
    
    # Error details
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")


class MCPDashboardData(BaseModel):
    """Dashboard data for MCP servers"""
    # Server summary
    total_servers: int = Field(..., description="Total number of servers")
    healthy_servers: int = Field(..., description="Number of healthy servers")
    unhealthy_servers: int = Field(..., description="Number of unhealthy servers")
    
    # Server details
    servers: List[MCPServerStatus] = Field(..., description="Detailed server status list")
    
    # Performance metrics
    average_response_time: float = Field(..., description="Average response time across all servers")
    total_requests_per_minute: float = Field(..., description="Total requests per minute")
    overall_error_rate: float = Field(..., description="Overall error rate percentage")
    
    # Lambda Labs specific
    lambda_servers: List[LambdaServer] = Field(default_factory=list, description="Lambda Labs servers")
    total_gpu_utilization: Optional[float] = Field(None, description="Total GPU utilization")
    available_models: List[str] = Field(default_factory=list, description="Available models across all servers")
    
    # Recent operations
    recent_operations: List[MCPOperation] = Field(default_factory=list, description="Recent operations")
    
    # Alerts
    active_alerts: List[str] = Field(default_factory=list, description="Active alert messages")
    
    # Timestamp
    generated_at: datetime = Field(default_factory=datetime.now)


class MCPServerConfig(BaseModel):
    """MCP server configuration for creation/update"""
    name: str = Field(..., description="Server name")
    server_type: MCPServerType = Field(..., description="Server type")
    host: str = Field(..., description="Server host")
    port: int = Field(..., description="Server port")
    
    # Optional configuration
    endpoint: str = Field("/health", description="Health check endpoint")
    health_check_interval: int = Field(30, description="Health check interval")
    auto_restart: bool = Field(True, description="Enable auto-restart")
    max_retries: int = Field(3, description="Maximum restart retries")
    timeout: int = Field(30, description="Request timeout")
    
    # Tags and metadata
    tags: List[str] = Field(default_factory=list, description="Server tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LambdaServerConfig(MCPServerConfig):
    """Lambda Labs server specific configuration"""
    instance_id: str = Field(..., description="Lambda Labs instance ID")
    instance_type: str = Field("gpu_1x_h100", description="Instance type")
    region: str = Field(..., description="Server region")
    custom_domain: Optional[str] = Field(None, description="Custom domain name")
    
    # GPU configuration
    gpu_type: str = Field("GH200", description="GPU type")
    max_concurrent_requests: int = Field(10, description="Maximum concurrent requests")

