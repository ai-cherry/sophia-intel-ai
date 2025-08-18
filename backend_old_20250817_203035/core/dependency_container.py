"""
Dependency injection container for SOPHIA Intel
Manages service lifecycle and dependencies
"""

from typing import Dict, Any, Type, Optional, List
import asyncio
import logging
from .base_service import BaseService

logger = logging.getLogger(__name__)


class DependencyContainer:
    """Dependency injection container"""
    
    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._service_configs: Dict[str, Dict[str, Any]] = {}
        self._initialization_order: List[str] = []
        self._initialized = False
    
    def register_service(
        self, 
        name: str, 
        service_class: Type[BaseService], 
        dependencies: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a service with its dependencies"""
        self._service_configs[name] = {
            "class": service_class,
            "dependencies": dependencies or [],
            "config": config or {}
        }
        logger.info(f"Registered service: {name}")
    
    async def initialize_all(self) -> None:
        """Initialize all services in dependency order"""
        if self._initialized:
            return
        
        try:
            # Resolve dependency order
            self._resolve_initialization_order()
            
            # Create and initialize services
            for service_name in self._initialization_order:
                await self._create_and_initialize_service(service_name)
            
            self._initialized = True
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            await self.shutdown_all()
            raise
    
    async def shutdown_all(self) -> None:
        """Shutdown all services in reverse order"""
        shutdown_order = list(reversed(self._initialization_order))
        
        for service_name in shutdown_order:
            if service_name in self._services:
                try:
                    await self._services[service_name].shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down service {service_name}: {e}")
        
        self._services.clear()
        self._initialized = False
        logger.info("All services shutdown")
    
    def get_service(self, name: str) -> BaseService:
        """Get a service by name"""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not found or not initialized")
        return self._services[name]
    
    def has_service(self, name: str) -> bool:
        """Check if service exists and is initialized"""
        return name in self._services
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        results = {}
        
        for name, service in self._services.items():
            try:
                results[name] = await service.health_check()
            except Exception as e:
                results[name] = {
                    "service": name,
                    "status": "error",
                    "error": str(e)
                }
        
        # Overall system health
        healthy_count = sum(1 for r in results.values() if r.get("status") == "healthy")
        total_count = len(results)
        
        return {
            "overall_status": "healthy" if healthy_count == total_count else "degraded",
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": results
        }
    
    def _resolve_initialization_order(self) -> None:
        """Resolve service initialization order based on dependencies"""
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {service_name}")
            if service_name in visited:
                return
            
            temp_visited.add(service_name)
            
            # Visit dependencies first
            config = self._service_configs.get(service_name, {})
            for dep in config.get("dependencies", []):
                if dep not in self._service_configs:
                    raise ValueError(f"Dependency '{dep}' not registered for service '{service_name}'")
                visit(dep)
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)
        
        # Visit all services
        for service_name in self._service_configs:
            visit(service_name)
        
        self._initialization_order = order
        logger.info(f"Service initialization order: {order}")
    
    async def _create_and_initialize_service(self, service_name: str) -> None:
        """Create and initialize a single service"""
        config = self._service_configs[service_name]
        service_class = config["class"]
        
        # Resolve dependencies
        dependencies = {}
        for dep_name in config.get("dependencies", []):
            dependencies[dep_name] = self.get_service(dep_name)
        
        # Add configuration
        dependencies.update(config.get("config", {}))
        
        # Create service
        service = service_class(service_name, dependencies)
        
        # Initialize service
        await service.initialize()
        
        # Store service
        self._services[service_name] = service
        
        logger.info(f"Service '{service_name}' created and initialized")
    
    @property
    def is_initialized(self) -> bool:
        """Check if container is initialized"""
        return self._initialized

