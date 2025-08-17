"""
Core architecture foundation for SOPHIA Intel
Provides base classes and dependency injection framework
"""

from .base_service import BaseService
from .dependency_container import DependencyContainer
from .service_registry import ServiceRegistry

__all__ = [
    "BaseService",
    "DependencyContainer", 
    "ServiceRegistry"
]

