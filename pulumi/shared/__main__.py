"""
Shared Infrastructure Components for Sophia Intel AI
Provides reusable ComponentResources following Pulumi 2025 patterns.
"""

import pulumi
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pulumi import ComponentResource, ResourceOptions, Output
import pulumi_fly as fly


@dataclass
class FlyAppConfig:
    """Configuration for Fly.io applications."""
    name: str
    image: str
    port: int = 8080
    scale: int = 1
    memory_mb: int = 512
    cpu_cores: float = 0.25
    env_vars: Optional[Dict[str, str]] = None
    volumes: Optional[Dict[str, str]] = None


class FlyApp(ComponentResource):
    """
    Reusable Fly.io application component.
    Follows 2025 best practices for containerized microservices.
    """
    
    def __init__(self, name: str, config: FlyAppConfig, opts: Optional[ResourceOptions] = None):
        super().__init__("sophia:infrastructure:FlyApp", name, None, opts)
        
        # Create Fly.io application
        self.app = fly.App(
            name,
            name=config.name,
            org="sophia-intel-ai",
            opts=ResourceOptions(parent=self)
        )
        
        # Configure application settings
        app_config = {
            "app": config.name,
            "primary_region": "iad",
            "console_command": "/bin/bash",
            
            # HTTP service configuration
            "http_service": {
                "internal_port": config.port,
                "force_https": True,
                "auto_stop_machines": True,
                "auto_start_machines": True,
                "min_machines_running": 1
            },
            
            # Machine configuration
            "vm": [
                {
                    "memory": f"{config.memory_mb}mb",
                    "cpu_kind": "shared",
                    "cpus": config.cpu_cores,
                }
            ],
            
            # Environment variables
            "env": config.env_vars or {},
            
            # Health checks
            "checks": {
                "health": {
                    "type": "http",
                    "port": config.port,
                    "method": "get",
                    "path": "/healthz",
                    "interval": "15s",
                    "timeout": "10s"
                }
            }
        }
        
        # Add volumes if specified
        if config.volumes:
            app_config["mounts"] = [
                {
                    "source": volume_name,
                    "destination": mount_path
                }
                for mount_path, volume_name in config.volumes.items()
            ]
        
        # Deploy machine configuration
        self.machine_config = fly.Machine(
            f"{name}-machine",
            app=self.app.name,
            region="iad",
            config=app_config,
            image=config.image,
            opts=ResourceOptions(parent=self)
        )
        
        # Export important outputs
        self.register_outputs({
            "app_name": self.app.name,
            "app_hostname": self.app.hostname,
            "internal_url": Output.concat("http://", self.app.name, ".internal:", config.port),
            "public_url": Output.concat("https://", self.app.hostname)
        })


class NeonDatabase(ComponentResource):
    """
    Neon PostgreSQL database component.
    Handles database creation and configuration.
    """
    
    def __init__(self, name: str, database_name: str, opts: Optional[ResourceOptions] = None):
        super().__init__("sophia:infrastructure:NeonDatabase", name, None, opts)
        
        # Note: Neon doesn't have official Pulumi provider yet
        # Using dynamic resource or REST API calls
        # For now, we'll export connection configuration
        
        config = pulumi.Config()
        neon_connection_string = config.require_secret("neon_connection_string")
        
        self.register_outputs({
            "database_name": database_name,
            "connection_string": neon_connection_string,
            "host": pulumi.Output.secret("db.neon.tech"),  # Placeholder
            "port": 5432,
            "ssl_mode": "require"
        })


class RedisCache(ComponentResource):
    """
    Redis cache component for session and application caching.
    """
    
    def __init__(self, name: str, memory_mb: int = 256, opts: Optional[ResourceOptions] = None):
        super().__init__("sophia:infrastructure:RedisCache", name, None, opts)
        
        config = pulumi.Config()
        redis_url = config.require_secret("redis_url")
        
        self.register_outputs({
            "redis_url": redis_url,
            "memory_mb": memory_mb,
            "max_connections": 100
        })


class WeaviateVector(ComponentResource):
    """
    Weaviate vector database component.
    Manages vector storage and search capabilities.
    """
    
    def __init__(self, name: str, opts: Optional[ResourceOptions] = None):
        super().__init__("sophia:infrastructure:WeaviateVector", name, None, opts)
        
        config = pulumi.Config()
        weaviate_url = config.get("weaviate_url") or "http://localhost:8080"
        weaviate_api_key = config.get_secret("weaviate_api_key")
        
        self.register_outputs({
            "weaviate_url": weaviate_url,
            "weaviate_api_key": weaviate_api_key,
            "collections": {
                "memory_entries": "MemoryEntries",
                "code_chunks": "CodeChunks", 
                "documents": "Documents"
            }
        })


# Export component classes for reuse
__all__ = [
    "FlyApp",
    "FlyAppConfig", 
    "NeonDatabase",
    "RedisCache",
    "WeaviateVector"
]

# Main program for testing
if __name__ == "__main__":
    # Export configuration for other projects to reference
    config = pulumi.Config()
    
    pulumi.export("shared_components_version", "1.0.0")
    pulumi.export("fly_org", "sophia-intel-ai")
    pulumi.export("primary_region", "iad")
    pulumi.export("environment", config.get("environment") or "dev")