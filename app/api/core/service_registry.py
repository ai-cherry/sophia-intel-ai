from shared.core.common_functions import get_service_registry

"\nSophia AI Service Registry\nRegisters all services with the dependency injection container\n"
import logging
from typing import Any

from container import register_service
from orchestration.state_manager import StateManager
from orchestration.task_analyzer import TaskAnalyzer
from orchestration.tool_registry import ToolRegistry
from orchestration.workflow_engine import SophiaWorkflowEngine
from orchestration.workflow_monitor import WorkflowMonitor
from protocols import (
    MemoryRouterProtocol,
    MemoryServiceProtocol,
    MetricsCollectorProtocol,
    StateManagerProtocol,
    TaskAnalyzerProtocol,
    ToolRegistryProtocol,
    WorkflowEngineProtocol,
)

from services.memory_service import RealMemoryService
from services.shared.enhanced_memory_router import EnhancedMemoryRouter

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Centralized service registration and initialization"""

    def __init__(self):
        self._registered = False
        self._services: dict[str, Any] = {}

    async def register_all(self) -> None:
        """Register all services with the DI container"""
        if self._registered:
            logger.warning("Services already registered")
            return
        logger.info("🚀 Registering all services with DI container...")
        register_service(StateManagerProtocol, lambda: StateManager(), singleton=True)
        register_service(ToolRegistryProtocol, lambda: ToolRegistry(), singleton=True)
        register_service(TaskAnalyzerProtocol, lambda: TaskAnalyzer(), singleton=True)
        register_service(
            MetricsCollectorProtocol, lambda: WorkflowMonitor(), singleton=True
        )
        register_service(
            MemoryServiceProtocol, lambda: RealMemoryService(), singleton=True
        )
        register_service(
            MemoryRouterProtocol, lambda: EnhancedMemoryRouter(), singleton=True
        )

        async def create_workflow_engine():
            from core.container import resolve_service

            state_manager = await resolve_service(StateManagerProtocol)
            tool_registry = await resolve_service(ToolRegistryProtocol)
            task_analyzer = await resolve_service(TaskAnalyzerProtocol)
            monitor = await resolve_service(MetricsCollectorProtocol)
            await state_manager.initialize()
            await tool_registry.initialize()
            return SophiaWorkflowEngine(
                state_manager=state_manager,
                tool_registry=tool_registry,
                task_analyzer=task_analyzer,
                monitor=monitor,
            )

        register_service(WorkflowEngineProtocol, create_workflow_engine, singleton=True)
        self._registered = True
        logger.info("✅ All services registered successfully")

    async def initialize_services(self) -> None:
        """Initialize all registered services"""
        from core.container import get_container

        logger.info("🔧 Initializing all services...")
        services_to_init = [
            StateManagerProtocol,
            ToolRegistryProtocol,
            TaskAnalyzerProtocol,
            MetricsCollectorProtocol,
            MemoryServiceProtocol,
            MemoryRouterProtocol,
            WorkflowEngineProtocol,
        ]
        for service_type in services_to_init:
            try:
                service = await get_container().resolve(service_type)
                if hasattr(service, "initialize"):
                    await service.initialize()
                logger.info(f"✅ Initialized: {service_type.__name__}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {service_type.__name__}: {e}")
                raise

    async def shutdown_services(self) -> None:
        """Shutdown all services gracefully"""
        from core.container import get_container

        logger.info("🛑 Shutting down all services...")
        await get_container().shutdown()

    def get_service(self, service_type: type) -> Any:
        """Get a service instance (for testing)"""
        return self._services.get(service_type.__name__)


_registry = ServiceRegistry()


async def bootstrap_services() -> None:
    """Bootstrap the entire service layer"""
    registry = get_service_registry()
    await registry.register_all()
    await registry.initialize_services()


async def shutdown_services() -> None:
    """Shutdown all services"""
    registry = get_service_registry()
    await registry.shutdown_services()


class ServiceLocator:
    """Convenient service locator for common services"""

    @staticmethod
    async def get_workflow_engine() -> WorkflowEngineProtocol:
        """Get the workflow engine"""
        from core.container import resolve_service

        return await resolve_service(WorkflowEngineProtocol)

    @staticmethod
    async def get_state_manager() -> StateManagerProtocol:
        """Get the state manager"""
        from core.container import resolve_service

        return await resolve_service(StateManagerProtocol)

    @staticmethod
    async def get_tool_registry() -> ToolRegistryProtocol:
        """Get the tool registry"""
        from core.container import resolve_service

        return await resolve_service(ToolRegistryProtocol)

    @staticmethod
    async def get_memory_service() -> MemoryServiceProtocol:
        """Get the memory service"""
        from core.container import resolve_service

        return await resolve_service(MemoryServiceProtocol)

    @staticmethod
    async def get_memory_router() -> MemoryRouterProtocol:
        """Get the memory router"""
        from core.container import resolve_service

        return await resolve_service(MemoryRouterProtocol)
