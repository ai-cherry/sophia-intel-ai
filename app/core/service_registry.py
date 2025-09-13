"""
Sophia Intel AI - Centralized Service Registry

This module provides the foundational service registry for the centralized
service management system, defining all services, their configurations,
and port allocations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """Classification of services by their role in the system."""
    CORE = "core"        # Essential services required for basic functionality
    OPTIONAL = "optional"  # Enhanced features that can gracefully degrade
    DEV = "dev"         # Development-only services


@dataclass
class ServiceDefinition:
    """Complete definition of a service in the Sophia Intel AI ecosystem."""
    
    # Identity
    name: str
    description: str
    service_type: ServiceType
    
    # Network configuration
    port: int
    host: str = "localhost"
    protocol: str = "http"
    
    # Service behavior
    health_endpoint: str = "/health"
    startup_timeout: int = 30  # seconds
    shutdown_timeout: int = 10  # seconds
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    optional_depends: List[str] = field(default_factory=list)
    
    # Environment
    env_prefix: str = ""
    required_env_vars: List[str] = field(default_factory=list)
    
    # Metadata
    version: str = "1.0.0"
    maintainer: str = "Sophia Intel AI Team"
    tags: List[str] = field(default_factory=list)
    
    def get_url(self) -> str:
        """Get the full URL for this service."""
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def get_health_url(self) -> str:
        """Get the health check URL for this service."""
        return f"{self.get_url()}{self.health_endpoint}"


class ServiceRegistry:
    """
    Centralized registry for all Sophia Intel AI services.
    
    This registry maintains the canonical list of all services,
    their configurations, and provides utilities for service
    discovery and management.
    """
    
    # Canonical service definitions
    SERVICES: Dict[str, ServiceDefinition] = {
        # =====================================
        # CORE SERVICES
        # =====================================
        "unified_api": ServiceDefinition(
            name="unified_api",
            description="Main Sophia Intel AI API server",
            service_type=ServiceType.CORE,
            port=8003,
            health_endpoint="/api/health",
            env_prefix="SOPHIA_API_",
            required_env_vars=["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
            tags=["api", "core", "fastapi"]
        ),
        
        "agent_ui": ServiceDefinition(
            name="agent_ui",
            description="Sophia Agent User Interface (React/Vite)",
            service_type=ServiceType.CORE,
            port=3000,
            health_endpoint="/",
            startup_timeout=45,
            depends_on=["unified_api"],
            env_prefix="SOPHIA_UI_",
            tags=["ui", "react", "vite"]
        ),
        
        "postgres": ServiceDefinition(
            name="postgres",
            description="PostgreSQL database server",
            service_type=ServiceType.CORE,
            port=5432,
            health_endpoint="/",  # Custom health check needed
            startup_timeout=60,
            env_prefix="POSTGRES_",
            required_env_vars=["DATABASE_URL"],
            tags=["database", "postgres"]
        ),
        
        "redis": ServiceDefinition(
            name="redis",
            description="Redis cache and message broker",
            service_type=ServiceType.CORE,
            port=6379,
            health_endpoint="/ping",  # Custom health check needed
            startup_timeout=30,
            env_prefix="REDIS_",
            required_env_vars=["REDIS_URL"],
            tags=["cache", "redis", "pubsub"]
        ),
        
        # =====================================
        # MCP SERVICES
        # =====================================
        "mcp_memory": ServiceDefinition(
            name="mcp_memory",
            description="MCP Memory Management Server",
            service_type=ServiceType.CORE,
            port=8081,
            depends_on=["redis", "postgres"],
            env_prefix="MCP_MEMORY_",
            tags=["mcp", "memory", "vector"]
        ),
        
        "mcp_filesystem": ServiceDefinition(
            name="mcp_filesystem",
            description="MCP Filesystem Operations Server",
            service_type=ServiceType.CORE,
            port=8082,
            env_prefix="MCP_FS_",
            required_env_vars=["WORKSPACE_PATH"],
            tags=["mcp", "filesystem", "io"]
        ),
        
        "mcp_web": ServiceDefinition(
            name="mcp_web",
            description="MCP Web Interaction Server",
            service_type=ServiceType.OPTIONAL,
            port=8083,
            env_prefix="MCP_WEB_",
            tags=["mcp", "web", "scraping"]
        ),
        
        "mcp_git": ServiceDefinition(
            name="mcp_git",
            description="MCP Git Operations Server",
            service_type=ServiceType.CORE,
            port=8084,
            env_prefix="MCP_GIT_",
            required_env_vars=["WORKSPACE_PATH"],
            tags=["mcp", "git", "vcs"]
        ),
        
        # =====================================
        # VECTOR DATABASES
        # =====================================
        "weaviate": ServiceDefinition(
            name="weaviate",
            description="Weaviate vector database",
            service_type=ServiceType.CORE,
            port=8080,
            health_endpoint="/v1/.well-known/ready",
            startup_timeout=90,
            env_prefix="WEAVIATE_",
            required_env_vars=["WEAVIATE_URL"],
            tags=["vector", "database", "weaviate"]
        ),
        
        "neo4j": ServiceDefinition(
            name="neo4j",
            description="Neo4j graph database",
            service_type=ServiceType.OPTIONAL,
            port=7687,
            protocol="bolt",
            health_endpoint="/",  # Custom health check needed
            startup_timeout=120,
            env_prefix="NEO4J_",
            required_env_vars=["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"],
            tags=["graph", "database", "neo4j"]
        ),
        
        # =====================================
        # DEVELOPMENT SERVICES
        # =====================================
        "jupyter": ServiceDefinition(
            name="jupyter",
            description="Jupyter notebook server for development",
            service_type=ServiceType.DEV,
            port=8888,
            health_endpoint="/api/status",
            startup_timeout=60,
            env_prefix="JUPYTER_",
            tags=["dev", "jupyter", "notebook"]
        ),
        
        "prometheus": ServiceDefinition(
            name="prometheus",
            description="Prometheus metrics server",
            service_type=ServiceType.DEV,
            port=9090,
            health_endpoint="/-/healthy",
            startup_timeout=45,
            env_prefix="PROMETHEUS_",
            tags=["monitoring", "metrics", "prometheus"]
        ),
        
        "grafana": ServiceDefinition(
            name="grafana",
            description="Grafana dashboard server",
            service_type=ServiceType.DEV,
            port=3001,
            health_endpoint="/api/health",
            startup_timeout=60,
            depends_on=["prometheus"],
            env_prefix="GRAFANA_",
            tags=["monitoring", "dashboard", "grafana"]
        ),
        
        # =====================================
        # PROXY SERVICES
        # =====================================
        "nginx_proxy": ServiceDefinition(
            name="nginx_proxy",
            description="Nginx reverse proxy",
            service_type=ServiceType.OPTIONAL,
            port=80,
            health_endpoint="/nginx_status",
            startup_timeout=30,
            depends_on=["unified_api", "agent_ui"],
            env_prefix="NGINX_",
            tags=["proxy", "nginx", "loadbalancer"]
        ),
        
        "traefik": ServiceDefinition(
            name="traefik",
            description="Traefik reverse proxy and load balancer",
            service_type=ServiceType.OPTIONAL,
            port=8088,  # Dashboard port, proxy is typically 80/443
            health_endpoint="/ping",
            startup_timeout=30,
            env_prefix="TRAEFIK_",
            tags=["proxy", "traefik", "loadbalancer"]
        ),
    }
    
    @classmethod
    def get_service(cls, name: str) -> Optional[ServiceDefinition]:
        """Get a service definition by name."""
        return cls.SERVICES.get(name)
    
    @classmethod
    def get_port(cls, service_name: str) -> Optional[int]:
        """Get the port for a specific service."""
        service = cls.get_service(service_name)
        return service.port if service else None
    
    @classmethod
    def get_all_ports(cls) -> Dict[str, int]:
        """Get all service ports as a mapping."""
        return {name: service.port for name, service in cls.SERVICES.items()}
    
    @classmethod
    def check_conflicts(cls) -> List[Tuple[str, str, int]]:
        """
        Check for port conflicts between services.
        
        Returns:
            List of tuples (service1, service2, port) representing conflicts
        """
        conflicts = []
        port_map = {}
        
        for name, service in cls.SERVICES.items():
            if service.port in port_map:
                conflicts.append((port_map[service.port], name, service.port))
            else:
                port_map[service.port] = name
        
        return conflicts
    
    @classmethod
    def get_services_by_type(cls, service_type: ServiceType) -> Dict[str, ServiceDefinition]:
        """Get all services of a specific type."""
        return {
            name: service 
            for name, service in cls.SERVICES.items() 
            if service.service_type == service_type
        }
    
    @classmethod
    def get_core_services(cls) -> Dict[str, ServiceDefinition]:
        """Get all core services."""
        return cls.get_services_by_type(ServiceType.CORE)
    
    @classmethod
    def get_optional_services(cls) -> Dict[str, ServiceDefinition]:
        """Get all optional services."""
        return cls.get_services_by_type(ServiceType.OPTIONAL)
    
    @classmethod
    def get_dev_services(cls) -> Dict[str, ServiceDefinition]:
        """Get all development services."""
        return cls.get_services_by_type(ServiceType.DEV)
    
    @classmethod
    def get_services_by_tag(cls, tag: str) -> Dict[str, ServiceDefinition]:
        """Get all services with a specific tag."""
        return {
            name: service 
            for name, service in cls.SERVICES.items() 
            if tag in service.tags
        }
    
    @classmethod
    def get_dependency_order(cls) -> List[str]:
        """
        Get services in dependency order (services with no deps first).
        
        Returns:
            List of service names in startup order
        """
        # Simple topological sort
        remaining = set(cls.SERVICES.keys())
        ordered = []
        
        while remaining:
            # Find services with no unresolved dependencies
            ready = []
            for service_name in remaining:
                service = cls.SERVICES[service_name]
                if all(dep in ordered or dep not in cls.SERVICES for dep in service.depends_on):
                    ready.append(service_name)
            
            if not ready:
                # Circular dependency or missing dependency
                logger.warning(f"Circular dependency detected or missing services. Remaining: {remaining}")
                # Add all remaining services
                ordered.extend(sorted(remaining))
                break
            
            # Sort ready services for consistent ordering
            ready.sort()
            ordered.extend(ready)
            remaining -= set(ready)
        
        return ordered
    
    @classmethod
    def validate_dependencies(cls) -> List[str]:
        """
        Validate that all service dependencies exist.
        
        Returns:
            List of error messages for missing dependencies
        """
        errors = []
        
        for name, service in cls.SERVICES.items():
            for dep in service.depends_on:
                if dep not in cls.SERVICES:
                    errors.append(f"Service '{name}' depends on missing service '{dep}'")
            
            for dep in service.optional_depends:
                if dep not in cls.SERVICES:
                    logger.warning(f"Service '{name}' optionally depends on missing service '{dep}'")
        
        return errors
    
    @classmethod
    def get_service_urls(cls) -> Dict[str, str]:
        """Get all service URLs."""
        return {name: service.get_url() for name, service in cls.SERVICES.items()}
    
    @classmethod
    def get_health_check_urls(cls) -> Dict[str, str]:
        """Get all health check URLs."""
        return {name: service.get_health_url() for name, service in cls.SERVICES.items()}


# Validation on module import
def _validate_registry():
    """Validate the service registry on import."""
    conflicts = ServiceRegistry.check_conflicts()
    if conflicts:
        logger.error(f"Port conflicts detected in service registry: {conflicts}")
    
    dep_errors = ServiceRegistry.validate_dependencies()
    if dep_errors:
        for error in dep_errors:
            logger.error(error)


# Run validation when module is imported
_validate_registry()