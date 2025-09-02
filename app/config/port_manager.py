"""
Centralized Port Configuration Manager
Single Source of Truth for All Service Ports

This module provides centralized port management for the entire Sophia Intel AI system.
All services MUST use this configuration to avoid conflicts.
"""

import os
from typing import Dict, Optional, List, Tuple
from enum import Enum
import json
from pathlib import Path

class ServiceType(Enum):
    """Service categories for port allocation"""
    FRONTEND = "frontend"      # 3000-3999
    DATABASE = "database"      # 6000-6999  
    MCP = "mcp"               # 8000-8099
    API = "api"               # 8000-8099
    MONITORING = "monitoring"  # 8000-8099
    STORAGE = "storage"       # 8000-8099
    DEV = "dev"              # 8000-8099
    ALTERNATIVE_UI = "alt_ui" # 8500-8599

class PortConfig:
    """
    Centralized port configuration - SINGLE SOURCE OF TRUTH
    
    All services must use this configuration:
    ```python
    from app.config.port_manager import PortConfig
    
    config = PortConfig()
    my_port = config.get_port("unified_api")
    ```
    """
    
    # MASTER PORT REGISTRY - DO NOT MODIFY WITHOUT UPDATING PORT_ASSIGNMENTS.md
    _PORTS = {
        # Frontend Services (3000-3999)
        "nextjs_ui": {
            "port": 3000,
            "type": ServiceType.FRONTEND,
            "description": "Next.js UI",
            "health": "/",
            "required": True
        },
        
        # Database Services (6000-6999)
        "redis": {
            "port": 6379,
            "type": ServiceType.DATABASE,
            "description": "Redis Server",
            "health": None,  # TCP connection
            "required": True
        },
        
        # MCP Services (8000-8099)
        "mcp_memory_alt": {
            "port": 8000,
            "type": ServiceType.MCP,
            "description": "MCP Memory Alternative",
            "health": "/health",
            "required": False
        },
        "mcp_memory": {
            "port": 8001,
            "type": ServiceType.MCP,
            "description": "MCP Memory Server",
            "health": "/health",
            "required": True
        },
        "monitoring": {
            "port": 8002,
            "type": ServiceType.MONITORING,
            "description": "Monitoring Dashboard",
            "health": "/",
            "required": True
        },
        "mcp_code_review": {
            "port": 8003,
            "type": ServiceType.MCP,
            "description": "MCP Code Review Server",
            "health": "/health",
            "required": True
        },
        "vector_store": {
            "port": 8004,
            "type": ServiceType.STORAGE,
            "description": "Vector Store Service",
            "health": "/health",
            "required": False
        },
        "unified_api": {
            "port": 8005,
            "type": ServiceType.API,
            "description": "Unified API Server",
            "health": "/",
            "required": True,
            "websockets": ["/ws/bus", "/ws/swarm", "/ws/teams"]
        },
        "backup_test": {
            "port": 8006,
            "type": ServiceType.DEV,
            "description": "Backup/Testing",
            "health": "/health",
            "required": False
        },
        "dev1": {
            "port": 8007,
            "type": ServiceType.DEV,
            "description": "Development 1",
            "health": "/health",
            "required": False
        },
        "dev2": {
            "port": 8008,
            "type": ServiceType.DEV,
            "description": "Development 2",
            "health": "/health",
            "required": False
        },
        "weaviate": {
            "port": 8080,
            "type": ServiceType.DATABASE,
            "description": "Weaviate Vector DB",
            "health": "/v1",
            "required": False
        },
        
        # Alternative UIs (8500-8599)
        "streamlit": {
            "port": 8501,
            "type": ServiceType.ALTERNATIVE_UI,
            "description": "Streamlit UI",
            "health": "/",
            "required": True
        }
    }
    
    def __init__(self):
        """Initialize port configuration"""
        self._load_overrides()
        self._validate_configuration()
    
    def _load_overrides(self):
        """Load environment variable overrides"""
        # Allow environment variables to override ports
        for service_name in self._PORTS:
            env_var = f"{service_name.upper()}_PORT"
            if env_var in os.environ:
                try:
                    override_port = int(os.environ[env_var])
                    self._PORTS[service_name]["port"] = override_port
                    print(f"Port override: {service_name} -> {override_port}")
                except ValueError:
                    print(f"Invalid port override for {env_var}: {os.environ[env_var]}")
    
    def _validate_configuration(self):
        """Validate no port conflicts exist"""
        port_map = {}
        for service_name, config in self._PORTS.items():
            port = config["port"]
            if port in port_map:
                raise ValueError(
                    f"Port conflict detected: {service_name} and {port_map[port]} "
                    f"both configured for port {port}"
                )
            port_map[port] = service_name
    
    def get_port(self, service_name: str) -> int:
        """
        Get port for a service
        
        Args:
            service_name: Name of the service (e.g., "unified_api", "redis")
            
        Returns:
            Port number
            
        Raises:
            KeyError: If service not found
        """
        if service_name not in self._PORTS:
            raise KeyError(f"Unknown service: {service_name}. Available: {list(self._PORTS.keys())}")
        return self._PORTS[service_name]["port"]
    
    def get_service_url(self, service_name: str, host: str = "localhost") -> str:
        """
        Get full URL for a service
        
        Args:
            service_name: Name of the service
            host: Hostname (default: localhost)
            
        Returns:
            Full URL (e.g., "http://localhost:8005")
        """
        port = self.get_port(service_name)
        
        # Redis uses redis:// protocol
        if service_name == "redis":
            return f"redis://{host}:{port}"
        
        return f"http://{host}:{port}"
    
    def get_health_endpoint(self, service_name: str) -> Optional[str]:
        """Get health check endpoint for a service"""
        if service_name not in self._PORTS:
            return None
        return self._PORTS[service_name].get("health")
    
    def get_websocket_endpoints(self, service_name: str) -> List[str]:
        """Get WebSocket endpoints for a service"""
        if service_name not in self._PORTS:
            return []
        return self._PORTS[service_name].get("websockets", [])
    
    def get_required_services(self) -> List[str]:
        """Get list of required services that must be running"""
        return [
            name for name, config in self._PORTS.items()
            if config.get("required", False)
        ]
    
    def get_available_ports(self, service_type: Optional[ServiceType] = None) -> List[int]:
        """Get list of available (not required) ports"""
        available = []
        for name, config in self._PORTS.items():
            if not config.get("required", False):
                if service_type is None or config["type"] == service_type:
                    available.append(config["port"])
        return sorted(available)
    
    def export_config(self, output_path: Optional[str] = None) -> Dict:
        """Export configuration to JSON"""
        config = {
            "version": "1.0.0",
            "timestamp": os.environ.get("BUILD_TIMESTAMP", ""),
            "services": {}
        }
        
        for name, service_config in self._PORTS.items():
            config["services"][name] = {
                "port": service_config["port"],
                "type": service_config["type"].value,
                "description": service_config["description"],
                "health": service_config.get("health"),
                "websockets": service_config.get("websockets", []),
                "required": service_config.get("required", False),
                "url": self.get_service_url(name)
            }
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(config, f, indent=2)
        
        return config
    
    def validate_runtime(self) -> Tuple[bool, List[str]]:
        """
        Validate runtime configuration
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for port conflicts
        port_map = {}
        for name, config in self._PORTS.items():
            port = config["port"]
            if port in port_map:
                errors.append(
                    f"Port conflict: {name} and {port_map[port]} both on port {port}"
                )
            port_map[port] = name
        
        # Check port ranges
        for name, config in self._PORTS.items():
            port = config["port"]
            service_type = config["type"]
            
            # Validate port ranges by type
            if service_type == ServiceType.FRONTEND and not (3000 <= port < 4000):
                errors.append(f"{name}: Frontend service port {port} not in range 3000-3999")
            elif service_type == ServiceType.DATABASE and port not in [6379, 8080] and not (6000 <= port < 7000):
                # Exception for Redis (6379) and Weaviate (8080) which use standard ports
                errors.append(f"{name}: Database service port {port} not in standard range")
            elif service_type in [ServiceType.MCP, ServiceType.API, ServiceType.MONITORING] and not (8000 <= port < 8100):
                errors.append(f"{name}: API/MCP service port {port} not in range 8000-8099")
            elif service_type == ServiceType.ALTERNATIVE_UI and not (8500 <= port < 8600):
                errors.append(f"{name}: Alternative UI port {port} not in range 8500-8599")
        
        return (len(errors) == 0, errors)
    
    def __str__(self) -> str:
        """String representation of port configuration"""
        lines = ["Port Configuration:"]
        for name, config in sorted(self._PORTS.items(), key=lambda x: x[1]["port"]):
            status = "REQUIRED" if config.get("required") else "optional"
            lines.append(
                f"  {config['port']:5} | {name:20} | {config['description']:25} | {status}"
            )
        return "\n".join(lines)


# Singleton instance
_port_config = None

def get_port_config() -> PortConfig:
    """Get singleton port configuration instance"""
    global _port_config
    if _port_config is None:
        _port_config = PortConfig()
    return _port_config


# Convenience functions for common services
def get_redis_url() -> str:
    """Get Redis connection URL"""
    return get_port_config().get_service_url("redis")

def get_unified_api_url() -> str:
    """Get Unified API URL"""
    return get_port_config().get_service_url("unified_api")

def get_mcp_memory_url() -> str:
    """Get MCP Memory Server URL"""
    return get_port_config().get_service_url("mcp_memory")

def get_monitoring_url() -> str:
    """Get Monitoring Dashboard URL"""
    return get_port_config().get_service_url("monitoring")


if __name__ == "__main__":
    # Test configuration when run directly
    config = get_port_config()
    print(config)
    print("\nValidation:")
    is_valid, errors = config.validate_runtime()
    if is_valid:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    
    # Export configuration
    config.export_config("port_config_export.json")
    print("\n📄 Configuration exported to port_config_export.json")