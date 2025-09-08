import asyncio

"\nSophia AI Service Protocols\nDefines interfaces to break circular dependencies and enable clean architecture\n"

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Protocol

class MemoryServiceProtocol(Protocol):
    """Protocol for memory storage services"""

    async def store(self, key: str, value: Any, namespace: str = "default") -> str:
        """Store a value in memory"""
        ...

    async def retrieve(self, key: str, namespace: str = "default") -> Any | None:
        """Retrieve a value from memory"""
        ...

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete a value from memory"""
        ...

    async def list_keys(self, namespace: str = "default") -> list[str]:
        """List all keys in a namespace"""
        ...

class StateManagerProtocol(Protocol):
    """Protocol for workflow state management"""

    async def save_state(self, task_id: str, state: dict[str, Any]) -> None:
        """Save workflow state"""
        ...

    async def get_state(self, task_id: str) -> dict[str, Any] | None:
        """Retrieve workflow state"""
        ...

    async def list_tasks(
        self, status: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List all tasks"""
        ...

    async def get_task_history(self, task_id: str) -> list[dict[str, Any]]:
        """Get task execution history"""
        ...

    async def get_analytics_summary(self) -> dict[str, Any]:
        """Get analytics summary"""
        ...

    async def close(self) -> None:
        """Close connections"""
        ...

class ToolProtocol(Protocol):
    """Protocol for tools"""

    name: str
    description: str

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the tool with given parameters"""
        ...

class ToolRegistryProtocol(Protocol):
    """Protocol for tool registry"""

    async def initialize(self) -> None:
        """Initialize the tool registry"""
        ...

    async def execute_tool(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a specific tool"""
        ...

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools"""
        ...

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """Get information about a specific tool"""
        ...

    def get_execution_stats(self) -> dict[str, Any]:
        """Get execution statistics"""
        ...

class TaskAnalysisResult(Protocol):
    """Protocol for task analysis results"""

    task_type: str
    complexity: str
    required_tools: list[str]
    estimated_hours: float
    confidence: float

class TaskAnalyzerProtocol(Protocol):
    """Protocol for task analysis"""

    async def analyze(self, task_description: str) -> TaskAnalysisResult:
        """Analyze a task description"""
        ...

class WorkflowState(Protocol):
    """Protocol for workflow state"""

    task_id: str
    description: str
    status: str
    progress: dict[str, Any]
    results: list[dict[str, Any]]
    error: str | None

class WorkflowEngineProtocol(Protocol):
    """Protocol for workflow engines"""

    async def execute(
        self, task_id: str, initial_state: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a workflow"""
        ...

    async def get_status(self, task_id: str) -> WorkflowState | None:
        """Get workflow status"""
        ...

class MetricsCollectorProtocol(Protocol):
    """Protocol for metrics collection"""

    def track_task(self, task_id: str, task_type: str) -> None:
        """Track task execution"""
        ...

    def track_tool_usage(self, tool_name: str, success: bool = True) -> None:
        """Track tool usage"""
        ...

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get metrics summary"""
        ...

class MemoryTier(Enum):
    """Memory tier enumeration"""

    L0_GPU_CACHE = "l0_gpu_cache"
    L1_REDIS = "l1_redis"
    L2_QDRANT = "l2_qdrant"
    L3_POSTGRESQL = "l3_postgresql"
    L4_MEM0 = "l4_mem0"
    L5_LEGACY = "l5_legacy"

class MemoryRouterProtocol(Protocol):
    """Protocol for memory routing"""

    async def route_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Route a memory request to appropriate tier"""
        ...

    async def get_tier_stats(self) -> dict[str, Any]:
        """Get statistics for all memory tiers"""
        ...

class ConfigProviderProtocol(Protocol):
    """Protocol for configuration providers"""

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        ...

    def has(self, key: str) -> bool:
        """Check if configuration key exists"""
        ...

class DatabaseConnectionProtocol(Protocol):
    """Protocol for database connections"""

    async def execute(self, query: str, *args) -> Any:
        """Execute a database query"""
        ...

    async def fetch_one(self, query: str, *args) -> dict[str, Any] | None:
        """Fetch one row"""
        ...

    async def fetch_all(self, query: str, *args) -> list[dict[str, Any]]:
        """Fetch all rows"""
        ...

    async def close(self) -> None:
        """Close the connection"""
        ...

class CacheProtocol(Protocol):
    """Protocol for caching services"""

    async def get(self, key: str) -> Any | None:
        """Get value from cache"""
        ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache"""
        ...

    async def delete(self, key: str) -> bool:
        """Delete from cache"""
        ...

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        ...

class EventProtocol(Protocol):
    """Protocol for events"""

    name: str
    data: dict[str, Any]
    timestamp: datetime

class EventBusProtocol(Protocol):
    """Protocol for event bus"""

    async def publish(self, event: EventProtocol) -> None:
        """Publish an event"""
        ...

    async def subscribe(self, event_name: str, handler: Callable) -> None:
        """Subscribe to events"""
        ...

    async def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """Unsubscribe from events"""
        ...

class BaseService(ABC):
    """Base class for all services"""

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the service"""
        if not self._initialized:
            await self._do_initialize()
            self._initialized = True

    async def close(self) -> None:
        """Close the service"""
        if self._initialized:
            await self._do_close()
            self._initialized = False

    @abstractmethod
    async def _do_initialize(self) -> None:
        """Service-specific initialization"""

    @abstractmethod
    async def _do_close(self) -> None:
        """Service-specific cleanup"""

    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized

class BaseRepository(ABC):
    """Base class for repositories"""

    @abstractmethod
    async def save(self, entity: Any) -> str:
        """Save an entity"""

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Any | None:
        """Get entity by ID"""

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete entity by ID"""
