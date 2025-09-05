"""
Memory System Configuration
===========================
Handles configuration for both local and cloud deployments
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any


class DeploymentMode(Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


class MemoryConfig:
    """Configuration for memory system with local/cloud support"""

    def __init__(self):
        # Detect deployment mode
        self.deployment_mode = self._detect_deployment_mode()

        # Redis configuration
        self.redis_url = self._get_redis_url()

        # Storage paths
        self.storage_config = self._get_storage_config()

        # Vector store configuration
        self.vector_store_config = self._get_vector_store_config()

        # Cache configuration
        self.cache_config = self._get_cache_config()

    def _detect_deployment_mode(self) -> DeploymentMode:
        """Detect if running locally or in cloud"""
        # Check for cloud provider environment variables
        if (
            os.getenv("FLY_APP_NAME")
            or os.getenv("RAILWAY_ENVIRONMENT")
            or os.getenv("AWS_EXECUTION_ENV")
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("VERCEL")
            or os.getenv("NETLIFY")
        ):
            return DeploymentMode.CLOUD
        else:
            return DeploymentMode.LOCAL

    def _get_redis_url(self) -> str:
        """Get Redis URL based on deployment"""
        if self.deployment_mode == DeploymentMode.CLOUD:
            # Try various cloud Redis providers
            redis_url = (
                os.getenv("REDIS_URL")
                or os.getenv("REDIS_TLS_URL")
                or os.getenv("REDISCLOUD_URL")
                or os.getenv("REDIS_ENDPOINT_URL")
                or os.getenv("FLY_REDIS_CACHE_URL")
            )

            if redis_url:
                # Handle TLS if needed
                if "rediss://" in redis_url:
                    return redis_url
                elif redis_url.startswith("redis://") and os.getenv("REDIS_TLS_ENABLED"):
                    return redis_url.replace("redis://", "rediss://")
                return redis_url

        # Default to local Redis
        return get_config().get("REDIS_URL", "redis://localhost:6379/0")

    def _get_storage_config(self) -> dict[str, Any]:
        """Get storage configuration"""
        if self.deployment_mode == DeploymentMode.CLOUD:
            # Cloud storage configuration
            return {
                "type": "cloud",
                "provider": self._detect_cloud_storage_provider(),
                "bucket": get_config().get("STORAGE_BUCKET", "ai-memory-storage"),
                "region": get_config().get("AWS_REGION", "us-east-1"),
                "local_cache": "/tmp/ai_memory_cache",
                "use_cdn": True,
            }
        else:
            # Local storage configuration
            home = Path.home()
            return {
                "type": "local",
                "base_path": os.getenv("MEMORY_STORAGE_PATH", str(home / ".ai_memory")),
                "project_cache": ".ai_memory",
                "global_path": str(home / ".ai_global_memory"),
                "use_compression": False,
            }

    def _detect_cloud_storage_provider(self) -> str:
        """Detect cloud storage provider"""
        if os.getenv("AWS_ACCESS_KEY_ID"):
            return "s3"
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            return "gcs"
        elif os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
            return "azure"
        else:
            return "local"  # Fallback to local even in cloud

    def _get_vector_store_config(self) -> dict[str, Any]:
        """Get vector store configuration"""
        if self.deployment_mode == DeploymentMode.CLOUD:
            # Cloud vector store (Pinecone, Weaviate Cloud, etc.)
            return {
                "provider": get_config().get("VECTOR_STORE_PROVIDER", "pinecone"),
                "api_key": get_config().get("PINECONE_API_KEY", ""),
                "environment": get_config().get("PINECONE_ENV", "us-east-1"),
                "index_name": get_config().get("PINECONE_INDEX", "ai-memory"),
                "dimension": 1536,  # OpenAI embedding dimension
                "metric": "cosine",
            }
        else:
            # Local vector store (ChromaDB, Qdrant local, etc.)
            return {
                "provider": "chromadb",
                "persist_directory": os.getenv(
                    "CHROMA_PERSIST_DIR", str(Path.home() / ".ai_memory" / "chroma")
                ),
                "collection_name": "ai_memory",
                "embedding_function": "openai",  # or "sentence-transformers"
                "distance_metric": "cosine",
            }

    def _get_cache_config(self) -> dict[str, Any]:
        """Get cache configuration"""
        return {
            "enabled": True,
            "ttl": {
                "working": 3600,  # 1 hour
                "session": 86400,  # 24 hours
                "project": 604800,  # 7 days
                "global": 2592000,  # 30 days
            },
            "max_size": {"working": 100, "session": 500, "project": 1000, "global": 5000},  # MB
            "compression": self.deployment_mode == DeploymentMode.CLOUD,
        }

    def get_redis_config(self) -> dict[str, Any]:
        """Get Redis configuration with retry and pool settings"""
        return {
            "url": self.redis_url,
            "max_connections": 50 if self.deployment_mode == DeploymentMode.CLOUD else 10,
            "socket_keepalive": True,
            "socket_keepalive_options": {
                1: 1,  # TCP_KEEPIDLE
                2: 1,  # TCP_KEEPINTVL
                3: 3,  # TCP_KEEPCNT
            },
            "retry_on_timeout": True,
            "retry_on_error": [ConnectionError, TimeoutError],
            "health_check_interval": 30,
        }

    def is_cloud_deployment(self) -> bool:
        """Check if running in cloud"""
        return self.deployment_mode == DeploymentMode.CLOUD

    def is_local_deployment(self) -> bool:
        """Check if running locally"""
        return self.deployment_mode == DeploymentMode.LOCAL

    def get_deployment_info(self) -> dict[str, Any]:
        """Get deployment information"""
        return {
            "mode": self.deployment_mode.value,
            "redis_available": bool(self.redis_url),
            "storage_type": self.storage_config["type"],
            "vector_store": self.vector_store_config["provider"],
            "environment": {
                "fly_app": os.getenv("FLY_APP_NAME"),
                "railway": os.getenv("RAILWAY_ENVIRONMENT"),
                "aws": bool(os.getenv("AWS_EXECUTION_ENV")),
                "gcp": bool(os.getenv("GOOGLE_CLOUD_PROJECT")),
                "vercel": bool(os.getenv("VERCEL")),
                "local": self.deployment_mode == DeploymentMode.LOCAL,
            },
        }


# Global config instance
memory_config = MemoryConfig()
