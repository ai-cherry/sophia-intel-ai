# SOPHIA Intel - Cloud-Native Production Configuration
# CEO Requirements: lynn@payready.com / Huskers2025$
# Approved Cloud Stack: Neon, Qdrant, Redis, Mem0, Lambda Labs, Weaviate

import os
from typing import Optional

class CloudConfig:
    """Production cloud configuration for SOPHIA Intel"""
    
    def __init__(self):
        # Database Configuration - Neon PostgreSQL
        self.database_url = os.getenv(
            "NEON_DATABASE_URL",
            "postgresql://username:password@ep-example.us-east-1.aws.neon.tech/sophia_intel"
        )
        
        # Vector Database - Qdrant Cloud
        self.qdrant_url = os.getenv("QDRANT_CLOUD_URL", "https://your-cluster.qdrant.tech")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        # Alternative Vector Database - Weaviate Cloud
        self.weaviate_url = os.getenv("WEAVIATE_CLOUD_URL", "https://your-cluster.weaviate.network")
        self.weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
        
        # Cache - Redis Cloud
        self.redis_url = os.getenv(
            "REDIS_CLOUD_URL",
            "redis://username:password@redis-cluster.cloud.redislabs.com:port"
        )
        
        # Memory System - Mem0
        self.mem0_api_key = os.getenv("MEM0_API_KEY")
        self.mem0_base_url = os.getenv("MEM0_BASE_URL", "https://api.mem0.ai")
        
        # GPU Compute - Lambda Labs
        self.lambda_labs_api_key = os.getenv("LAMBDA_LABS_API_KEY")
        self.lambda_labs_base_url = os.getenv("LAMBDA_LABS_BASE_URL", "https://cloud.lambdalabs.com/api/v1")
        
        # OpenRouter (AI Models)
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        # CEO Authentication
        self.ceo_email = "lynn@payready.com"
        self.ceo_password_hash = self._hash_password("Huskers2025$")
        
        # Production Settings
        self.environment = "production"
        self.debug = False
        self.cors_origins = [
            "https://www.sophia-intel.ai",
            "https://sophia-intel.ai",
            "https://sophia-intel.fly.dev"
        ]
        
    def _hash_password(self, password: str) -> str:
        """Hash password for secure storage"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_config(self) -> bool:
        """Validate all required cloud services are configured"""
        required_vars = [
            self.database_url,
            self.qdrant_api_key,
            self.redis_url,
            self.mem0_api_key,
            self.openrouter_api_key
        ]
        
        missing = [var for var in required_vars if not var]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        
        return True

# Production Environment Variables Template
PRODUCTION_ENV_TEMPLATE = """
# SOPHIA Intel Production Environment
# Cloud-Native Configuration - NO LOCAL DEPENDENCIES

# Database - Neon PostgreSQL
NEON_DATABASE_URL=postgresql://username:password@ep-example.us-east-1.aws.neon.tech/sophia_intel

# Vector Database - Qdrant Cloud
QDRANT_CLOUD_URL=https://your-cluster.qdrant.tech
QDRANT_API_KEY=your_qdrant_api_key

# Alternative Vector Database - Weaviate Cloud
WEAVIATE_CLOUD_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=your_weaviate_api_key

# Cache - Redis Cloud
REDIS_CLOUD_URL=redis://username:password@redis-cluster.cloud.redislabs.com:port

# Memory System - Mem0
MEM0_API_KEY=your_mem0_api_key
MEM0_BASE_URL=https://api.mem0.ai

# GPU Compute - Lambda Labs
LAMBDA_LABS_API_KEY=your_lambda_labs_api_key
LAMBDA_LABS_BASE_URL=https://cloud.lambdalabs.com/api/v1

# AI Models - OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key

# Security
JWT_SECRET_KEY=your_jwt_secret_key
ENCRYPTION_KEY=your_encryption_key

# Monitoring
SENTRY_DSN=your_sentry_dsn

# Production Settings
ENVIRONMENT=production
DEBUG=false
"""

# Cloud Service Clients
class CloudServices:
    """Initialize all cloud service clients"""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self._init_database()
        self._init_vector_db()
        self._init_cache()
        self._init_memory()
        
    def _init_database(self):
        """Initialize Neon PostgreSQL connection"""
        try:
            import asyncpg
            # Connection will be established in async context
            self.database_pool = None
        except ImportError:
            raise ImportError("asyncpg required for Neon PostgreSQL")
    
    def _init_vector_db(self):
        """Initialize Qdrant Cloud connection"""
        try:
            from qdrant_client import QdrantClient
            self.qdrant_client = QdrantClient(
                url=self.config.qdrant_url,
                api_key=self.config.qdrant_api_key
            )
        except ImportError:
            raise ImportError("qdrant-client required for Qdrant Cloud")
    
    def _init_cache(self):
        """Initialize Redis Cloud connection"""
        try:
            import redis
            self.redis_client = redis.from_url(self.config.redis_url)
        except ImportError:
            raise ImportError("redis required for Redis Cloud")
    
    def _init_memory(self):
        """Initialize Mem0 connection"""
        try:
            import httpx
            self.mem0_client = httpx.AsyncClient(
                base_url=self.config.mem0_base_url,
                headers={"Authorization": f"Bearer {self.config.mem0_api_key}"}
            )
        except ImportError:
            raise ImportError("httpx required for Mem0")

if __name__ == "__main__":
    # Validate production configuration
    config = CloudConfig()
    try:
        config.validate_config()
        print("✅ Cloud configuration validated successfully")
        print(f"Environment: {config.environment}")
        print(f"Database: {config.database_url[:50]}...")
        print(f"Vector DB: {config.qdrant_url}")
        print(f"Cache: {config.redis_url[:50]}...")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nRequired environment variables:")
        print(PRODUCTION_ENV_TEMPLATE)

