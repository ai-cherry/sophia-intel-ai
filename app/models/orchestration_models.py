"""
Production Pydantic Models for AI Orchestration System
Comprehensive validation models for requests, responses, and internal data structures
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, root_validator, validator

# ============================================
# Core Enums
# ============================================


class TaskType(str, Enum):
    """Task type enumeration"""

    CHAT = "chat"
    COMMAND = "command"
    QUERY = "query"
    AGENT = "agent"
    ORCHESTRATION = "orchestration"
    WEB_RESEARCH = "web_research"
    CODE_ANALYSIS = "code_analysis"
    BUSINESS_ANALYSIS = "business_analysis"


class TaskPriority(str, Enum):
    """Task priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SystemStatus(str, Enum):
    """System health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class OrchestratorType(str, Enum):
    """Types of orchestrators"""

    SUPER = "super"
    SOPHIA = "sophia"
    ARTEMIS = "artemis"
    HYBRID = "hybrid"


# ============================================
# Request Models
# ============================================


class BaseRequest(BaseModel):
    """Base request model with common fields"""

    request_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique request identifier"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="Request timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timeout_seconds: Optional[int] = Field(
        default=300, ge=1, le=3600, description="Request timeout"
    )

    class Config:
        use_enum_values = True
        validate_assignment = True


class ChatRequest(BaseRequest):
    """Chat interaction request"""

    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation identifier")
    model_preference: Optional[str] = Field(default=None, description="Preferred model")
    temperature: Optional[float] = Field(
        default=0.7, ge=0.0, le=2.0, description="Model temperature"
    )
    max_tokens: Optional[int] = Field(default=4000, ge=1, le=32000, description="Maximum tokens")

    @validator("message")
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v.strip()


class CommandRequest(BaseRequest):
    """System command request"""

    command: str = Field(..., min_length=1, description="Command to execute")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    require_confirmation: bool = Field(
        default=False, description="Whether command requires confirmation"
    )

    @validator("command")
    def validate_command(cls, v):
        # Validate command against allowed list
        allowed_commands = {
            "deploy",
            "scale",
            "optimize",
            "analyze",
            "heal",
            "status",
            "restart",
            "backup",
            "restore",
            "migrate",
            "clean",
        }
        if v.lower() not in allowed_commands:
            raise ValueError(f"Command '{v}' not in allowed commands: {allowed_commands}")
        return v.lower()


class QueryRequest(BaseRequest):
    """Data query request"""

    query_type: str = Field(..., description="Type of query")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    filters: dict[str, Any] = Field(default_factory=dict, description="Query filters")
    limit: Optional[int] = Field(default=100, ge=1, le=10000, description="Result limit")
    offset: Optional[int] = Field(default=0, ge=0, description="Result offset")

    @validator("query_type")
    def validate_query_type(cls, v):
        allowed_types = {"metrics", "state", "tasks", "insights", "logs", "performance"}
        if v.lower() not in allowed_types:
            raise ValueError(f"Query type '{v}' not in allowed types: {allowed_types}")
        return v.lower()


class AgentRequest(BaseRequest):
    """Agent management request"""

    action: str = Field(..., description="Agent action")
    agent_config: dict[str, Any] = Field(default_factory=dict, description="Agent configuration")
    agent_id: Optional[str] = Field(default=None, description="Target agent ID")

    @validator("action")
    def validate_action(cls, v):
        allowed_actions = {"create", "destroy", "update", "status", "restart", "scale"}
        if v.lower() not in allowed_actions:
            raise ValueError(f"Action '{v}' not in allowed actions: {allowed_actions}")
        return v.lower()


class OrchestrationRequest(BaseRequest):
    """General orchestration request"""

    type: TaskType = Field(..., description="Request type")
    content: str = Field(..., min_length=1, description="Request content")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="Task priority")
    orchestrator: OrchestratorType = Field(
        default=OrchestratorType.SUPER, description="Target orchestrator"
    )
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    budget: dict[str, Union[int, float]] = Field(
        default_factory=dict, description="Resource budget"
    )


# ============================================
# Response Models
# ============================================


class BaseResponse(BaseModel):
    """Base response model"""

    request_id: str = Field(..., description="Request identifier")
    status: str = Field(..., description="Response status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    processing_time_ms: Optional[float] = Field(
        default=None, description="Processing time in milliseconds"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Response metadata")

    class Config:
        use_enum_values = True


class ChatResponse(BaseResponse):
    """Chat response model"""

    message: str = Field(..., description="AI response message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation identifier")
    model_used: Optional[str] = Field(default=None, description="Model that generated response")
    tokens_used: Optional[int] = Field(default=None, description="Tokens consumed")
    confidence_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Confidence score"
    )
    citations: list[dict[str, Any]] = Field(default_factory=list, description="Source citations")
    needs_confirmation: bool = Field(
        default=False, description="Whether response needs user confirmation"
    )


class CommandResponse(BaseResponse):
    """Command execution response"""

    command: str = Field(..., description="Executed command")
    result: dict[str, Any] = Field(..., description="Command execution result")
    success: bool = Field(..., description="Whether command succeeded")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    affected_resources: list[str] = Field(
        default_factory=list, description="Resources affected by command"
    )


class QueryResponse(BaseResponse):
    """Query response model"""

    query_type: str = Field(..., description="Query type")
    data: Union[dict[str, Any], list[Any]] = Field(..., description="Query result data")
    total_count: Optional[int] = Field(default=None, description="Total available results")
    page_info: Optional[dict[str, Any]] = Field(default=None, description="Pagination information")


class OrchestrationResponse(BaseResponse):
    """Orchestration response model"""

    task_id: str = Field(..., description="Task identifier")
    type: TaskType = Field(..., description="Task type")
    status: TaskStatus = Field(..., description="Task status")
    result: Optional[dict[str, Any]] = Field(default=None, description="Task result")
    orchestrator_used: str = Field(..., description="Orchestrator that handled the task")
    confidence_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Result confidence"
    )
    citations: list[dict[str, Any]] = Field(default_factory=list, description="Source citations")
    cost_estimate: Optional[dict[str, float]] = Field(default=None, description="Cost breakdown")


class ErrorResponse(BaseResponse):
    """Error response model"""

    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    error_details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error details"
    )
    retry_after: Optional[int] = Field(default=None, description="Retry after seconds")
    support_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Support reference ID"
    )


# ============================================
# Internal Models
# ============================================


class Task(BaseModel):
    """Internal task model"""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Task ID")
    type: TaskType = Field(..., description="Task type")
    content: str = Field(..., description="Task content")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="Task priority")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Task metadata")
    budget: dict[str, Union[int, float]] = Field(
        default_factory=dict, description="Resource budget"
    )
    retries: int = Field(default=0, description="Number of retries")
    max_retries: int = Field(default=3, description="Maximum retries allowed")

    @root_validator
    def validate_timestamps(cls, values):
        created = values.get("created_at")
        updated = values.get("updated_at")
        started = values.get("started_at")
        completed = values.get("completed_at")

        if updated and created and updated < created:
            raise ValueError("Updated timestamp cannot be before created timestamp")

        if started and created and started < created:
            raise ValueError("Started timestamp cannot be before created timestamp")

        if completed and started and completed < started:
            raise ValueError("Completed timestamp cannot be before started timestamp")

        return values


class ExecutionResult(BaseModel):
    """Task execution result"""

    task_id: str = Field(..., description="Task ID")
    success: bool = Field(..., description="Whether execution succeeded")
    content: Optional[Any] = Field(default=None, description="Result content")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Result metadata")
    tokens_used: Optional[int] = Field(default=None, description="Tokens consumed")
    cost: Optional[float] = Field(default=None, description="Execution cost")
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Result confidence"
    )
    citations: list[dict[str, Any]] = Field(default_factory=list, description="Source citations")
    processing_time_ms: Optional[float] = Field(default=None, description="Processing time")


class SystemHealth(BaseModel):
    """System health status model"""

    status: SystemStatus = Field(..., description="Overall system status")
    components: dict[str, dict[str, Any]] = Field(..., description="Component health details")
    metrics: dict[str, Union[int, float]] = Field(..., description="System metrics")
    last_check: datetime = Field(default_factory=datetime.now, description="Last health check")
    uptime_seconds: Optional[int] = Field(default=None, description="System uptime")
    version: str = Field(default="2.1.0", description="System version")


class ConnectionMetrics(BaseModel):
    """Connection pool metrics"""

    redis_connections: dict[str, int] = Field(
        default_factory=dict, description="Redis connection stats"
    )
    http_connections: dict[str, int] = Field(
        default_factory=dict, description="HTTP connection stats"
    )
    websocket_connections: dict[str, int] = Field(
        default_factory=dict, description="WebSocket connection stats"
    )
    total_active: int = Field(default=0, description="Total active connections")
    total_idle: int = Field(default=0, description="Total idle connections")
    errors_last_hour: int = Field(default=0, description="Errors in the last hour")


# ============================================
# Validation Helpers
# ============================================


def validate_task_budget(budget: dict[str, Union[int, float]]) -> dict[str, Union[int, float]]:
    """Validate task budget constraints"""
    if not budget:
        return {}

    # Set reasonable defaults and limits
    defaults = {"tokens": 4000, "cost_usd": 5.0, "timeout_seconds": 300}

    limits = {"tokens": (1, 50000), "cost_usd": (0.01, 100.0), "timeout_seconds": (1, 3600)}

    validated = {}
    for key, value in budget.items():
        if key in limits:
            min_val, max_val = limits[key]
            if not min_val <= value <= max_val:
                raise ValueError(f"Budget {key} must be between {min_val} and {max_val}")
        validated[key] = value

    # Apply defaults for missing values
    for key, default in defaults.items():
        if key not in validated:
            validated[key] = default

    return validated


def sanitize_content(content: str, max_length: int = 10000) -> str:
    """Sanitize and validate content strings"""
    if not isinstance(content, str):
        raise ValueError("Content must be a string")

    # Remove potential harmful content
    content = content.strip()

    if len(content) > max_length:
        raise ValueError(f"Content too long: {len(content)} > {max_length}")

    if not content:
        raise ValueError("Content cannot be empty")

    return content


# ============================================
# Factory Functions
# ============================================


def create_error_response(
    request_id: str,
    error_code: str,
    error_message: str,
    error_details: dict[str, Any] = None,
    retry_after: Optional[int] = None,
) -> ErrorResponse:
    """Factory function to create standardized error responses"""
    return ErrorResponse(
        request_id=request_id,
        status="error",
        error_code=error_code,
        error_message=error_message,
        error_details=error_details or {},
        retry_after=retry_after,
    )


def create_orchestration_task(
    content: str,
    task_type: TaskType,
    priority: TaskPriority = TaskPriority.NORMAL,
    budget: dict[str, Union[int, float]] = None,
    metadata: dict[str, Any] = None,
) -> Task:
    """Factory function to create orchestration tasks"""
    validated_budget = validate_task_budget(budget or {})
    sanitized_content = sanitize_content(content)

    return Task(
        type=task_type,
        content=sanitized_content,
        priority=priority,
        budget=validated_budget,
        metadata=metadata or {},
    )
