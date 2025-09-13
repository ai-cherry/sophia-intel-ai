from shared.core.common_functions import get_container
"\nSophia AI Dependency Injection Container\nBreaks circular dependencies and provides clean service resolution\n"
import asyncio
import logging
from collections.abc import Callable
from typing import Any, TypeVar
logger = logging.getLogger(__name__)
T = TypeVar("T")
class ServiceContainer:
    """Sophisticated DI container with async support and circular dependency detection"""
    def __init__(self):
        self._services: dict[type, Any] = {}
        self._factories: dict[type, Callable] = {}
        self._singletons: dict[type, Any] = {}
        self._initialization_stack: set = set()
        self._initialized: set = set()
    def register(
        self, interface: type, factory: Callable[[], Any], singleton: bool = True
    ):
        """Register a service with its factory"""
        self._factories[interface] = factory
        if singleton:
            self._singletons[interface] = None
    def register_instance(self, interface: type, instance: Any):
        """Register a pre-initialized instance"""
        self._services[interface] = instance
        self._singletons[interface] = instance
        self._initialized.add(interface)
    async def resolve(self, interface: type[T]) -> T:
        """Resolve a service with circular dependency detection"""
        if interface in self._services:
            return self._services[interface]
        if interface in self._initialization_stack:
            raise CircularDependencyError(
                f"Circular dependency detected: {interface} -> {list(self._initialization_stack)}"
            )
        if interface not in self._factories:
            raise ServiceNotFoundError(f"No factory registered for {interface}")
        self._initialization_stack.add(interface)
        try:
            factory = self._factories[interface]
            if asyncio.iscoroutinefunction(factory):
                instance = await factory()
            else:
                instance = factory()
            self._services[interface] = instance
            self._initialized.add(interface)
            if interface in self._singletons:
                self._singletons[interface] = instance
            logger.info(f"✅ Service initialized: {interface.__name__}")
            return instance
        finally:
            self._initialization_stack.remove(interface)
    async def resolve_all(self, *interfaces: type) -> tuple:
        """Resolve multiple services at once"""
        return await asyncio.gather(*[self.resolve(iface) for iface in interfaces])
    def is_initialized(self, interface: type) -> bool:
        """Check if a service is already initialized"""
        return interface in self._initialized
    def clear(self):
        """Clear all services (for testing)"""
        self._services.clear()
        self._singletons.clear()
        self._initialized.clear()
        self._initialization_stack.clear()
    async def shutdown(self):
        """Gracefully shutdown all services"""
        for service in list(self._services.values()):
            if hasattr(service, "close") or hasattr(service, "shutdown"):
                try:
                    if hasattr(service, "close"):
                        if asyncio.iscoroutinefunction(service.close):
                            await service.close()
                        else:
                            service.close()
                    elif hasattr(service, "shutdown"):
                        if asyncio.iscoroutinefunction(service.shutdown):
                            await service.shutdown()
                        else:
                            service.shutdown()
                    logger.info(f"🛑 Service shutdown: {type(service).__name__}")
                except Exception as e:
                    logger.error(
                        f"❌ Error shutting down {type(service).__name__}: {e}"
                    )
class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected"""
class ServiceNotFoundError(Exception):
    """Raised when a requested service is not found"""
_container = ServiceContainer()
async def resolve_service(interface: type[T]) -> T:
    """Resolve a service from the global container"""
    return await get_container().resolve(interface)
