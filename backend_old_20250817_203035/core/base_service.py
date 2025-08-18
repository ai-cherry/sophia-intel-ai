"""
Base service class for dependency injection and lifecycle management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base class for all services with dependency injection support"""
    
    def __init__(self, name: str, dependencies: Optional[Dict[str, Any]] = None):
        self.name = name
        self.dependencies = dependencies or {}
        self._initialized = False
        self._healthy = True
        self._last_health_check = None
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    async def initialize(self) -> None:
        """Initialize the service - called after dependency injection"""
        try:
            await self._initialize()
            self._initialized = True
            self.logger.info(f"Service {self.name} initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize service {self.name}: {e}")
            self._healthy = False
            raise
    
    @abstractmethod
    async def _initialize(self) -> None:
        """Service-specific initialization logic"""
        pass
    
    async def shutdown(self) -> None:
        """Shutdown the service gracefully"""
        try:
            await self._shutdown()
            self._initialized = False
            self.logger.info(f"Service {self.name} shutdown successfully")
        except Exception as e:
            self.logger.error(f"Error during service {self.name} shutdown: {e}")
    
    async def _shutdown(self) -> None:
        """Service-specific shutdown logic"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            service_health = await self._health_check()
            self._last_health_check = datetime.utcnow()
            
            return {
                "service": self.name,
                "status": "healthy" if self._healthy else "unhealthy",
                "initialized": self._initialized,
                "last_check": self._last_health_check.isoformat(),
                "details": service_health
            }
        except Exception as e:
            self._healthy = False
            return {
                "service": self.name,
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _health_check(self) -> Dict[str, Any]:
        """Service-specific health check logic"""
        return {"status": "ok"}
    
    def get_dependency(self, name: str) -> Any:
        """Get a dependency by name"""
        if name not in self.dependencies:
            raise ValueError(f"Dependency '{name}' not found for service '{self.name}'")
        return self.dependencies[name]
    
    def has_dependency(self, name: str) -> bool:
        """Check if dependency exists"""
        return name in self.dependencies
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized
    
    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy"""
        return self._healthy

