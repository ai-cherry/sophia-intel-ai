"""
Global service registry for SOPHIA Intel
Provides singleton access to the dependency container
"""

from typing import Optional
from .dependency_container import DependencyContainer
from .base_service import BaseService


class ServiceRegistry:
    """Global service registry singleton"""
    
    _instance: Optional['ServiceRegistry'] = None
    _container: Optional[DependencyContainer] = None
    
    def __new__(cls) -> 'ServiceRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, container: DependencyContainer) -> None:
        """Initialize the registry with a container"""
        instance = cls()
        instance._container = container
    
    @classmethod
    def get_service(cls, name: str) -> BaseService:
        """Get a service by name"""
        instance = cls()
        if instance._container is None:
            raise RuntimeError("ServiceRegistry not initialized")
        return instance._container.get_service(name)
    
    @classmethod
    def has_service(cls, name: str) -> bool:
        """Check if service exists"""
        instance = cls()
        if instance._container is None:
            return False
        return instance._container.has_service(name)
    
    @classmethod
    def get_container(cls) -> DependencyContainer:
        """Get the dependency container"""
        instance = cls()
        if instance._container is None:
            raise RuntimeError("ServiceRegistry not initialized")
        return instance._container
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if registry is initialized"""
        instance = cls()
        return instance._container is not None and instance._container.is_initialized

