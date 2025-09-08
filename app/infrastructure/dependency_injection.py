"""
Dependency Injection Container and Service Configuration
Provides centralized dependency management for the AI Orchestra system
"""

import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Protocol, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ==================== Service Configuration ====================


@dataclass
class ServiceConfig:
    """Central configuration for all services"""

    # Service URLs
    ollama_url: str = "http://localhost:11434"
    redis_url: str = "redis://localhost:6379"
    mcp_server_url: str = "http://localhost:8004"
    n8n_url: str = "http://localhost:5678"

    # Connection settings
    max_websocket_connections: int = 1000
    connection_idle_timeout_seconds: int = 300
    connection_check_interval_seconds: int = 30

    # Session settings
    max_session_history: int = 100
    session_memory_ttl_seconds: int = 3600

    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60

    # Feature flags
    enable_structured_logging: bool = True
    enable_distributed_tracing: bool = False
    enable_health_checks: bool = True
    enable_graceful_degradation: bool = True

    # Performance settings
    default_request_timeout_seconds: int = 30
    max_concurrent_requests: int = 100

    @classmethod
    def from_env(cls) -> "ServiceConfig":
        """Create configuration from environment variables"""

        return cls(
            ollama_url=get_config().get("OLLAMA_URL", "cls.ollama_url"),
            redis_url=get_config().get("REDIS_URL", "cls.redis_url"),
            mcp_server_url=get_config().get("MCP_SERVER_URL", "cls.mcp_server_url"),
            n8n_url=get_config().get("N8N_URL", "cls.n8n_url"),
            max_websocket_connections=int(
                get_config().get(
                    "MAX_WEBSOCKET_CONNECTIONS", cls.max_websocket_connections
                )
            ),
            connection_idle_timeout_seconds=int(
                get_config().get(
                    "CONNECTION_IDLE_TIMEOUT", cls.connection_idle_timeout_seconds
                )
            ),
        )


# ==================== Service Interfaces ====================


class ChatOrchestratorProtocol(Protocol):
    """Protocol defining ChatOrchestrator interface"""

    async def initialize(self) -> None: ...

    async def handle_chat(self, request: Any) -> Any: ...

    async def stream_tokens(self, message: str, session_id: str) -> Any: ...

    async def get_metrics(self) -> dict[str, Any]: ...

    async def shutdown(self) -> None: ...


class ManagerProtocol(Protocol):
    """Protocol defining Orchestra Manager interface"""

    def interpret_intent(self, message: str, context: Any) -> tuple: ...

    def generate_response(self, intent: str, parameters: dict, context: Any) -> str: ...

    def get_status(self) -> dict[str, Any]: ...


# ==================== Dependency Injection Container ====================


class DIContainer:
    """
    Dependency Injection Container
    Manages service lifecycle and dependency resolution
    """

    def __init__(self, config: Optional[ServiceConfig] = None):
        self.config = config or ServiceConfig()
        self._services: dict[type, Any] = {}
        self._factories: dict[type, Callable] = {}
        self._singletons: dict[type, Any] = {}
        self._scoped_services: dict[str, dict[type, Any]] = {}
        self._lock = asyncio.Lock()

        # Register config as a service
        self.register_singleton(ServiceConfig, lambda: self.config)

        logger.info("DIContainer initialized")

    def register(
        self,
        service_type: type[T],
        factory: Callable[..., T],
        lifetime: str = "transient",
    ):
        """
        Register a service factory

        Args:
            service_type: Type of service to register
            factory: Factory function to create service
            lifetime: Service lifetime - 'transient', 'singleton', or 'scoped'
        """
        if lifetime not in ["transient", "singleton", "scoped"]:
            raise ValueError(f"Invalid lifetime: {lifetime}")

        self._factories[service_type] = (factory, lifetime)
        logger.debug(f"Registered {service_type.__name__} with {lifetime} lifetime")

    def register_singleton(self, service_type: type[T], factory: Callable[..., T]):
        """Register a singleton service"""
        self.register(service_type, factory, "singleton")

    def register_scoped(self, service_type: type[T], factory: Callable[..., T]):
        """Register a scoped service"""
        self.register(service_type, factory, "scoped")

    async def resolve(self, service_type: type[T], scope: Optional[str] = None) -> T:
        """
        Resolve a service instance

        Args:
            service_type: Type of service to resolve
            scope: Optional scope for scoped services

        Returns:
            Service instance
        """
        async with self._lock:
            if service_type not in self._factories:
                raise ValueError(f"Service {service_type.__name__} not registered")

            factory, lifetime = self._factories[service_type]

            if lifetime == "singleton":
                if service_type not in self._singletons:
                    instance = await self._create_instance(factory)
                    self._singletons[service_type] = instance
                return self._singletons[service_type]

            elif lifetime == "scoped":
                if not scope:
                    raise ValueError(
                        f"Scope required for scoped service {service_type.__name__}"
                    )

                if scope not in self._scoped_services:
                    self._scoped_services[scope] = {}

                if service_type not in self._scoped_services[scope]:
                    instance = await self._create_instance(factory)
                    self._scoped_services[scope][service_type] = instance

                return self._scoped_services[scope][service_type]

            else:  # transient
                return await self._create_instance(factory)

    async def _create_instance(self, factory: Callable):
        """Create service instance, handling async factories"""
        if asyncio.iscoroutinefunction(factory):
            return await factory()
        return factory()

    def create_scope(self, scope_id: str) -> "ServiceScope":
        """Create a new service scope"""
        return ServiceScope(self, scope_id)

    def dispose_scope(self, scope_id: str):
        """Dispose of a service scope"""
        if scope_id in self._scoped_services:
            # Clean up scoped services
            for service in self._scoped_services[scope_id].values():
                if hasattr(service, "dispose"):
                    service.dispose()
            del self._scoped_services[scope_id]
            logger.debug(f"Disposed scope {scope_id}")

    async def dispose(self):
        """Dispose of all services"""
        # Dispose singletons
        for service in self._singletons.values():
            if hasattr(service, "dispose"):
                if asyncio.iscoroutinefunction(service.dispose):
                    await service.dispose()
                else:
                    service.dispose()

        # Dispose scoped services
        for scope_id in list(self._scoped_services.keys()):
            self.dispose_scope(scope_id)

        self._singletons.clear()
        self._services.clear()
        logger.info("DIContainer disposed")


# ==================== Service Scope ====================


class ServiceScope:
    """Scoped service resolution context"""

    def __init__(self, container: DIContainer, scope_id: str):
        self.container = container
        self.scope_id = scope_id
        self.created_at = datetime.utcnow()

    async def resolve(self, service_type: type[T]) -> T:
        """Resolve service within this scope"""
        return await self.container.resolve(service_type, self.scope_id)

    def dispose(self):
        """Dispose of this scope"""
        self.container.dispose_scope(self.scope_id)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.dispose()


# ==================== Connection Pool Manager ====================


class WebSocketConnectionPool:
    """
    Manages WebSocket connections with pooling and limits
    """

    def __init__(self, config: ServiceConfig):
        self.max_connections = config.max_websocket_connections
        self.connections: dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._eviction_queue: asyncio.Queue = asyncio.Queue()
        self.metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "evicted_connections": 0,
            "rejected_connections": 0,
        }
        logger.info(
            f"WebSocketConnectionPool initialized with max {self.max_connections} connections"
        )

    async def acquire_connection(self, key: str, connection: Any) -> bool:
        """
        Acquire a connection slot

        Returns:
            True if connection was added, False if pool is full
        """
        async with self._lock:
            if len(self.connections) >= self.max_connections:
                # Try to evict oldest connection
                if not await self._evict_oldest():
                    self.metrics["rejected_connections"] += 1
                    logger.warning(f"Connection pool full, rejecting {key}")
                    return False

            self.connections[key] = connection
            self.metrics["total_connections"] += 1
            self.metrics["active_connections"] = len(self.connections)
            logger.debug(f"Added connection {key} to pool")
            return True

    async def release_connection(self, key: str):
        """Release a connection"""
        async with self._lock:
            if key in self.connections:
                del self.connections[key]
                self.metrics["active_connections"] = len(self.connections)
                logger.debug(f"Released connection {key} from pool")

    async def _evict_oldest(self) -> bool:
        """
        Evict the oldest connection

        Returns:
            True if a connection was evicted
        """
        if not self.connections:
            return False

        # Find oldest connection (simple FIFO for now)
        oldest_key = next(iter(self.connections))
        oldest_conn = self.connections[oldest_key]

        # Close the connection
        try:
            if hasattr(oldest_conn, "websocket"):
                await oldest_conn.websocket.close()
        except:
            pass

        del self.connections[oldest_key]
        self.metrics["evicted_connections"] += 1
        logger.info(f"Evicted connection {oldest_key} from pool")
        return True

    def get_metrics(self) -> dict[str, Any]:
        """Get pool metrics"""
        return {
            **self.metrics,
            "utilization": (
                len(self.connections) / self.max_connections
                if self.max_connections > 0
                else 0
            ),
        }


# ==================== Session State Manager ====================


class SessionStateManager:
    """
    Manages session state with configurable limits
    """

    def __init__(self, config: ServiceConfig):
        self.max_history = config.max_session_history
        self.ttl_seconds = config.session_memory_ttl_seconds
        self.sessions: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(
            f"SessionStateManager initialized with max history {self.max_history}"
        )

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Get or create session state"""
        async with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    "id": session_id,
                    "created_at": datetime.utcnow(),
                    "last_activity": datetime.utcnow(),
                    "history": [],
                    "metadata": {},
                }
            else:
                self.sessions[session_id]["last_activity"] = datetime.utcnow()

            return self.sessions[session_id]

    async def add_to_history(self, session_id: str, entry: dict[str, Any]):
        """Add entry to session history"""
        session = await self.get_session(session_id)

        async with self._lock:
            session["history"].append(
                {**entry, "timestamp": datetime.utcnow().isoformat()}
            )

            # Trim history if needed
            if len(session["history"]) > self.max_history:
                session["history"] = session["history"][-self.max_history :]

    async def update_metadata(self, session_id: str, metadata: dict[str, Any]):
        """Update session metadata"""
        session = await self.get_session(session_id)

        async with self._lock:
            session["metadata"].update(metadata)

    async def _cleanup_loop(self):
        """Periodic cleanup of expired sessions"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")

    async def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.utcnow()
        expired = []

        async with self._lock:
            for session_id, session in self.sessions.items():
                age = (now - session["last_activity"]).total_seconds()
                if age > self.ttl_seconds:
                    expired.append(session_id)

            for session_id in expired:
                del self.sessions[session_id]
                logger.debug(f"Expired session {session_id}")

    async def dispose(self):
        """Clean up manager"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task


# ==================== Service Registration ====================


def register_services(container: DIContainer):
    """Register all services with the DI container"""

    # Import here to avoid circular dependencies
    from app.embeddings.agno_embedding_service import AgnoEmbeddingService
    from app.embeddings.portkey_integration import PortkeyGateway
    from app.nl_interface.command_dispatcher import SmartCommandDispatcher
    from app.orchestration.unified_facade import UnifiedOrchestratorFacade
    from app.ui.unified.chat_orchestrator import ChatOrchestrator

    # Get config
    config = container.config

    # Register infrastructure services
    container.register_singleton(
        WebSocketConnectionPool, lambda: WebSocketConnectionPool(config)
    )

    container.register_singleton(
        SessionStateManager, lambda: SessionStateManager(config)
    )

    # Register embedding services
    container.register_singleton(PortkeyGateway, lambda: PortkeyGateway())

    container.register_singleton(AgnoEmbeddingService, lambda: AgnoEmbeddingService())

    # Register core services
    container.register_singleton(
        SmartCommandDispatcher,
        lambda: SmartCommandDispatcher(
            ollama_url=config.ollama_url,
            redis_url=config.redis_url,
            mcp_server_url=config.mcp_server_url,
            n8n_url=config.n8n_url,
        ),
    )

    container.register_singleton(
        UnifiedOrchestratorFacade, lambda: UnifiedOrchestratorFacade()
    )

    # OrchestraManager removed - functionality integrated into SuperOrchestrator

    # Register ChatOrchestrator with dependencies
    async def create_chat_orchestrator():
        await container.resolve(SmartCommandDispatcher)
        await container.resolve(UnifiedOrchestratorFacade)
        pool = await container.resolve(WebSocketConnectionPool)
        sessions = await container.resolve(SessionStateManager)

        # Create orchestrator with injected dependencies
        orchestrator = ChatOrchestrator(
            ollama_url=config.ollama_url,
            redis_url=config.redis_url,
            mcp_server_url=config.mcp_server_url,
            n8n_url=config.n8n_url,
        )

        # Inject additional dependencies
        orchestrator.connection_pool = pool
        orchestrator.session_manager = sessions

        await orchestrator.initialize()
        return orchestrator

    container.register_singleton(ChatOrchestrator, create_chat_orchestrator)

    logger.info("All services registered with DI container")


# ==================== Global Container Instance ====================

# Create global container (will be replaced by proper initialization)
_global_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get the global DI container"""
    global _global_container
    if not _global_container:
        config = ServiceConfig.from_env()
        _global_container = DIContainer(config)
        register_services(_global_container)
    return _global_container


async def initialize_container(config: Optional[ServiceConfig] = None) -> DIContainer:
    """Initialize the global DI container"""
    global _global_container
    if _global_container:
        await _global_container.dispose()

    _global_container = DIContainer(config or ServiceConfig.from_env())
    register_services(_global_container)
    return _global_container


# ==================== Export ====================

__all__ = [
    "DIContainer",
    "ServiceConfig",
    "ServiceScope",
    "WebSocketConnectionPool",
    "SessionStateManager",
    "ChatOrchestratorProtocol",
    "ManagerProtocol",
    "get_container",
    "initialize_container",
    "register_services",
]
