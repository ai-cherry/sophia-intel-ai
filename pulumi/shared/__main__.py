"""
Shared Infrastructure Components for Sophia Intel AI
Provides reusable ComponentResources following Pulumi 2025 patterns.

Following ADR-006: Configuration Management Standardization
- Uses Pulumi ESC environments for unified configuration
- Hierarchical configuration (base -> dev/staging/prod)
- Encrypted secret management
"""

import pulumi
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pulumi import ComponentResource, ResourceOptions, Output
import pulumi_fly as fly
import os


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
    Neon PostgreSQL database component using ESC configuration.
    Handles database creation and configuration with ADR-006 compliance.
    """
    
    def __init__(self, name: str, database_name: str, opts: Optional[ResourceOptions] = None):
        super().__init__("sophia:infrastructure:NeonDatabase", name, None, opts)
        
        # Get environment name for ESC configuration
        environment = os.getenv("PULUMI_ESC_ENVIRONMENT", "dev")
        
        # Use ESC environment variables (automatically loaded by Pulumi)
        neon_api_key = pulumi.Config().get_secret("NEON_API_KEY")
        neon_project_id = pulumi.Config().get("NEON_PROJECT_ID")
        neon_branch_id = pulumi.Config().get("NEON_BRANCH_ID")
        postgres_password = pulumi.Config().get_secret("POSTGRES_PASSWORD")
        
        # Construct connection string using ESC values
        connection_string = pulumi.Output.secret(
            f"postgresql://sophia:{postgres_password}@app-sparkling-wildflower-99699121.neon.tech:5432/{database_name}?sslmode=require"
        )
        
        self.register_outputs({
            "database_name": database_name,
            "connection_string": connection_string,
            "host": "app-sparkling-wildflower-99699121.neon.tech",
            "port": 5432,
            "ssl_mode": "require",
            "environment": environment,
            "project_id": neon_project_id,
            "branch_id": neon_branch_id
        })


class RedisCache(ComponentResource):
    """
    Redis cache component using ESC configuration.
    Session and application caching with ADR-006 compliance.
    """
    
    def __init__(self, name: str, memory_mb: int = 256, opts: Optional[ResourceOptions] = None):
        super().__init__("sophia:infrastructure:RedisCache", name, None, opts)
        
        # Get environment name for ESC configuration
        environment = os.getenv("PULUMI_ESC_ENVIRONMENT", "dev")
        
        # Use ESC environment variables (automatically loaded by Pulumi)
        redis_url = pulumi.Config().get_secret("REDIS_URL")
        redis_host = pulumi.Config().get("REDIS_HOST")
        redis_port = pulumi.Config().get_int("REDIS_PORT") or 6379
        redis_password = pulumi.Config().get_secret("REDIS_PASSWORD")
        
        self.register_outputs({
            "redis_url": redis_url,
            "redis_host": redis_host,
            "redis_port": redis_port,
            "redis_password": redis_password,
            "memory_mb": memory_mb,
            "max_connections": 200 if environment == "prod" else 100,
            "environment": environment
        })


class WeaviateVector(ComponentResource):
    """
    Weaviate vector database component using ESC configuration.
    Vector storage and search with ADR-006 compliance.
    """
    
    def __init__(self, name: str, opts: Optional[ResourceOptions] = None):
        super().__init__("sophia:infrastructure:WeaviateVector", name, None, opts)
        
        # Get environment name for ESC configuration
        environment = os.getenv("PULUMI_ESC_ENVIRONMENT", "dev")
        
        # Use ESC environment variables (automatically loaded by Pulumi)
        weaviate_url = pulumi.Config().get("WEAVIATE_URL") or "http://localhost:8080"
        weaviate_api_key = pulumi.Config().get_secret("WEAVIATE_API_KEY")
        weaviate_batch_size = pulumi.Config().get_int("WEAVIATE_BATCH_SIZE") or 100
        weaviate_timeout = pulumi.Config().get_int("WEAVIATE_TIMEOUT") or 30
        
        self.register_outputs({
            "weaviate_url": weaviate_url,
            "weaviate_api_key": weaviate_api_key,
            "batch_size": weaviate_batch_size,
            "timeout": weaviate_timeout,
            "collections": {
                "memory_entries": "UnifiedMemoryEntries",
                "code_chunks": "CodeChunks",
                "documents": "Documents",
                "embeddings": "EmbeddingCache"
            },
            "environment": environment,
            "version": "1.32+"
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