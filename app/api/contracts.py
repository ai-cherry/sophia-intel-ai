"""
API Contracts and Interfaces
Formal API contracts with versioning support for backward compatibility
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, Protocol, Union

from pydantic import BaseModel, Field, validator

# ==================== API Versioning ====================


class APIVersion(str, Enum):
    """Supported API versions"""

    V1 = "v1"
    V2 = "v2"
    LATEST = "v2"


# ==================== Base Models ====================


class VersionedRequest(BaseModel):
    """Base class for versioned requests"""

    api_version: APIVersion = Field(
        default=APIVersion.LATEST, description="API version"
    )
    request_id: Optional[str] = Field(
        default=None, description="Unique request ID for tracking"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Request timestamp"
    )


class VersionedResponse(BaseModel):
    """Base class for versioned responses"""

    api_version: APIVersion = Field(description="API version used")
    request_id: Optional[str] = Field(
        default=None, description="Request ID from original request"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class APIResponse(BaseModel):
    """Generic API response model"""

    success: bool = Field(description="Whether the request was successful")
    data: Any = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if any")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


def create_api_response(
    success: bool, data: Any = None, error: Optional[str] = None
) -> APIResponse:
    """Helper function to create API responses"""
    return APIResponse(success=success, data=data, error=error)


def create_error_response(error: str, data: Any = None) -> APIResponse:
    """Helper function to create error responses"""
    return APIResponse(success=False, data=data, error=error)


# ==================== V1 API Models ====================


class ChatRequestV1(VersionedRequest):
    """Version 1 chat request"""

    api_version: APIVersion = APIVersion.V1
    message: str = Field(min_length=1, max_length=10000, description="User message")
    session_id: str = Field(
        min_length=1, max_length=100, description="Session identifier"
    )
    client_id: Optional[str] = Field(
        default=None, max_length=100, description="Client identifier"
    )
    user_context: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="User context data"
    )
    stream: bool = Field(default=True, description="Enable streaming response")
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @validator("message")
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v


class ChatResponseV1(VersionedResponse):
    """Version 1 chat response"""

    api_version: APIVersion = APIVersion.V1
    session_id: str = Field(description="Session identifier")
    response: Any = Field(description="Response data")
    execution_mode: str = Field(description="Execution mode used")
    execution_time: float = Field(ge=0, description="Execution time in seconds")
    quality_score: float = Field(ge=0, le=1, description="Response quality score")
    success: bool = Field(description="Request success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Response metadata"
    )


class StreamTokenV1(BaseModel):
    """Version 1 stream token"""

    type: str = Field(description="Token type: token, status, error, complete, manager")
    content: Optional[str] = Field(default=None, description="Token content")
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Token metadata"
    )
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ==================== V2 API Models (Extended) ====================


class OptimizationMode(str, Enum):
    """Optimization modes for V2"""

    LITE = "lite"
    BALANCED = "balanced"
    QUALITY = "quality"
    AUTO = "auto"


class SwarmType(str, Enum):
    """Swarm types for V2"""

    CODING_DEBATE = "coding-debate"
    IMPROVED_SOLVE = "improved-solve"
    SIMPLE_AGENTS = "simple-agents"
    MCP_COORDINATED = "mcp-coordinated"
    AUTO_SELECT = "auto-select"


class ChatRequestV2(ChatRequestV1):
    """Version 2 chat request with enhanced features"""

    api_version: APIVersion = APIVersion.V2
    optimization_mode: Optional[OptimizationMode] = Field(
        default=OptimizationMode.AUTO, description="Optimization mode"
    )
    swarm_type: Optional[SwarmType] = Field(
        default=None, description="Specific swarm type to use"
    )
    use_memory: bool = Field(default=True, description="Enable memory context")
    max_response_tokens: Optional[int] = Field(
        default=None, ge=1, le=100000, description="Max response tokens"
    )
    temperature: Optional[float] = Field(
        default=None, ge=0, le=2, description="LLM temperature"
    )
    optimization_hints: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Optimization hints"
    )


class ChatResponseV2(ChatResponseV1):
    """Version 2 chat response with enhanced features"""

    api_version: APIVersion = APIVersion.V2
    manager_response: Optional[str] = Field(
        default=None, description="AI manager response"
    )
    intent: Optional[str] = Field(default=None, description="Detected intent")
    confidence: Optional[float] = Field(
        default=None, ge=0, le=1, description="Intent confidence"
    )
    swarm_used: Optional[str] = Field(default=None, description="Swarm type used")
    tokens_used: Optional[int] = Field(
        default=None, ge=0, description="Tokens consumed"
    )


# ==================== WebSocket Messages ====================


class WebSocketMessageType(str, Enum):
    """WebSocket message types"""

    CHAT = "chat"
    COMMAND = "command"
    CONTROL = "control"
    STREAM_TOKEN = "stream_token"
    STATUS = "status"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    TIMEOUT = "timeout"


class WebSocketMessage(BaseModel):
    """WebSocket message format"""

    type: WebSocketMessageType = Field(description="Message type")
    data: dict[str, Any] = Field(description="Message data")
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    correlation_id: Optional[str] = Field(
        default=None, description="Correlation ID for tracking"
    )


class WebSocketChatData(BaseModel):
    """Data for WebSocket chat messages"""

    message: str = Field(min_length=1, max_length=10000)
    context: Optional[dict[str, Any]] = Field(default_factory=dict)
    swarm_type: Optional[str] = Field(default=None)
    optimization_mode: Optional[str] = Field(default="balanced")


# ==================== Health Check Models ====================


class HealthStatus(str, Enum):
    """Health status enum"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Component health status"""

    status: HealthStatus = Field(description="Component health status")
    details: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Health details"
    )
    last_check: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response"""

    status: HealthStatus = Field(description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: dict[str, ComponentHealth] = Field(description="Component health checks")
    version: str = Field(default="1.0.0", description="Service version")


# ==================== Component Interfaces (Protocols) ====================


class ChatOrchestratorInterface(Protocol):
    """Interface for ChatOrchestrator"""

    async def initialize(self) -> None:
        """Initialize the orchestrator"""
        ...

    async def handle_chat(
        self, request: Union[ChatRequestV1, ChatRequestV2]
    ) -> Union[ChatResponseV1, ChatResponseV2]:
        """Handle chat request"""
        ...

    async def stream_tokens(
        self,
        message: str,
        session_id: str,
        user_context: Optional[dict[str, Any]] = None,
        swarm_type: Optional[str] = None,
        optimization_mode: str = "balanced",
    ):
        """Stream response tokens"""
        ...

    async def get_metrics(self) -> dict[str, Any]:
        """Get orchestrator metrics"""
        ...

    async def shutdown(self) -> None:
        """Shutdown the orchestrator"""
        ...


class CommandDispatcherInterface(Protocol):
    """Interface for CommandDispatcher"""

    async def process_command(
        self, text: str, session_id: str, user_context: Optional[dict[str, Any]] = None
    ) -> Any:
        """Process a command"""
        ...

    async def get_session_status(self, session_id: str) -> dict[str, Any]:
        """Get session status"""
        ...

    async def shutdown(self) -> None:
        """Shutdown dispatcher"""
        ...


class ManagerInterface(Protocol):
    """Interface for Orchestra Manager"""

    def interpret_intent(self, message: str, context: Any) -> tuple:
        """Interpret user intent"""
        ...

    def generate_response(
        self,
        intent: str,
        parameters: dict[str, Any],
        context: Any,
        result: Optional[Any] = None,
    ) -> str:
        """Generate response"""
        ...

    def get_status(self) -> dict[str, Any]:
        """Get manager status"""
        ...


# ==================== Request/Response Factories ====================


class APIContractFactory:
    """Factory for creating versioned API contracts"""

    @staticmethod
    def create_chat_request(
        data: dict[str, Any],
    ) -> Union[ChatRequestV1, ChatRequestV2]:
        """
        Create appropriate chat request based on API version

        Args:
            data: Request data

        Returns:
            Versioned chat request
        """
        version = data.get("api_version", APIVersion.LATEST)

        if version == APIVersion.V1:
            return ChatRequestV1(**data)
        elif version == APIVersion.V2:
            return ChatRequestV2(**data)
        else:
            # Default to latest version
            return ChatRequestV2(**data)

    @staticmethod
    def create_chat_response(
        version: APIVersion, data: dict[str, Any]
    ) -> Union[ChatResponseV1, ChatResponseV2]:
        """
        Create appropriate chat response based on API version

        Args:
            version: API version
            data: Response data

        Returns:
            Versioned chat response
        """
        if version == APIVersion.V1:
            # Filter out V2-only fields for backward compatibility
            v1_data = {
                k: v
                for k, v in data.items()
                if k
                not in [
                    "manager_response",
                    "intent",
                    "confidence",
                    "swarm_used",
                    "tokens_used",
                ]
            }
            return ChatResponseV1(**v1_data)
        else:
            return ChatResponseV2(**data)


# ==================== Backward Compatibility Adapter ====================


class BackwardCompatibilityAdapter:
    """
    Adapter for maintaining backward compatibility across API versions
    """

    def __init__(self):
        self.factory = APIContractFactory()

    def adapt_request(
        self, raw_data: dict[str, Any]
    ) -> Union[ChatRequestV1, ChatRequestV2]:
        """
        Adapt raw request data to appropriate version

        Args:
            raw_data: Raw request data

        Returns:
            Adapted request object
        """
        return self.factory.create_chat_request(raw_data)

    def adapt_response(
        self, request_version: APIVersion, response_data: dict[str, Any]
    ) -> Union[ChatResponseV1, ChatResponseV2]:
        """
        Adapt response data to match request version

        Args:
            request_version: Original request API version
            response_data: Response data

        Returns:
            Adapted response object
        """
        return self.factory.create_chat_response(request_version, response_data)

    def is_compatible(self, version: str) -> bool:
        """
        Check if a version is supported

        Args:
            version: Version string

        Returns:
            True if version is supported
        """
        try:
            APIVersion(version)
            return True
        except ValueError:
            return False


# ==================== Validation Middleware ====================


class RequestValidationMiddleware:
    """Middleware for validating API requests"""

    def __init__(self):
        self.adapter = BackwardCompatibilityAdapter()

    async def validate_request(
        self, request_data: dict[str, Any]
    ) -> Union[ChatRequestV1, ChatRequestV2]:
        """
        Validate and parse request data

        Args:
            request_data: Raw request data

        Returns:
            Validated request object

        Raises:
            ValueError: If request is invalid
        """
        try:
            return self.adapter.adapt_request(request_data)
        except Exception as e:
            raise ValueError(f"Invalid request: {str(e)}")

    async def validate_response(
        self,
        request: Union[ChatRequestV1, ChatRequestV2],
        response_data: dict[str, Any],
    ) -> Union[ChatResponseV1, ChatResponseV2]:
        """
        Validate and format response data

        Args:
            request: Original request
            response_data: Raw response data

        Returns:
            Validated response object
        """
        response_data["api_version"] = request.api_version
        response_data["request_id"] = request.request_id

        return self.adapter.adapt_response(request.api_version, response_data)


# ==================== Export ====================

__all__ = [
    # Enums
    "APIVersion",
    "OptimizationMode",
    "SwarmType",
    "WebSocketMessageType",
    "HealthStatus",
    # V1 Models
    "ChatRequestV1",
    "ChatResponseV1",
    "StreamTokenV1",
    # V2 Models
    "ChatRequestV2",
    "ChatResponseV2",
    # WebSocket Models
    "WebSocketMessage",
    "WebSocketChatData",
    # Health Models
    "ComponentHealth",
    "HealthCheckResponse",
    # Interfaces
    "ChatOrchestratorInterface",
    "CommandDispatcherInterface",
    "ManagerInterface",
    # Utilities
    "APIContractFactory",
    "BackwardCompatibilityAdapter",
    "RequestValidationMiddleware",
]
