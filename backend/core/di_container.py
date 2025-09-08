"\nDependency Injection Container\nPrevents circular dependencies by providing a central service registry\n"

import inspect
from typing import Any, TypeVar

T = TypeVar("T")

class ServiceContainer:
    """Simple dependency injection container"""

    def __init__(self):
        self._services: dict[str, Any] = {}
        self._factories: dict[str, callable] = {}

    def register(self, service_class: type[T], instance: T | None = None) -> None:
        """Register a service instance or factory"""
        service_name = service_class.__name__
        if instance is not None:
            self._services[service_name] = instance
        else:
            self._factories[service_name] = service_class

    def get(self, service_class: type[T]) -> T:
        """Get a service instance"""
        service_name = service_class.__name__
        if service_name in self._services:
            return self._services[service_name]
        if service_name in self._factories:
            factory = self._factories[service_name]
            sig = inspect.signature(factory.__init__)
            params = {}
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                if param.annotation and param.annotation != inspect.Parameter.empty:
                    try:
                        params[param_name] = self.get(param.annotation)
                    except KeyError:
                        pass
            instance = factory(**params)
            self._services[service_name] = instance
            return instance
        raise KeyError(f"Service {service_name} not registered")

container = ServiceContainer()
