"""
Database Infrastructure for Sophia Intel AI
Manages Neon PostgreSQL and Redis instances with connection pooling.
"""

import pulumi
from pulumi import StackReference, Output
import sys
import os

# Add shared components to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from shared import NeonDatabase, RedisCache

def main():
    """Deploy database infrastructure."""
    
    config = pulumi.Config()
    environment = config.get("environment") or "dev"
    postgres_db_name = config.get("postgres_db_name") or "sophia_intel_ai"
    redis_memory_mb = config.get_int("redis_memory_mb") or 256
    
    # Reference shared components
    shared_stack = StackReference(f"shared-{environment}")
    
    # Deploy Neon PostgreSQL
    postgres_db = NeonDatabase(
        "postgres-main",
        database_name=f"{postgres_db_name}_{environment}"
    )
    
    # Deploy Redis Cache
    redis_cache = RedisCache(
        "redis-cache",
        memory_mb=redis_memory_mb
    )
    
    # Database configuration for services
    database_config = {
        "postgres": {
            "max_connections": 100,
            "connection_timeout": 30,
            "idle_timeout": 600,
            "pool_size": 20,
            "ssl_mode": "require"
        },
        "redis": {
            "max_connections": 50,
            "connection_timeout": 5,
            "idle_timeout": 300,
            "key_prefix": f"sophia:{environment}:",
            "default_ttl": 3600
        }
    }
    
    # Export database outputs for other stacks
    pulumi.export("postgres_connection_string", postgres_db.connection_string)
    pulumi.export("postgres_host", postgres_db.host)
    pulumi.export("postgres_port", postgres_db.port)
    pulumi.export("postgres_database", postgres_db.database_name)
    pulumi.export("postgres_ssl_mode", postgres_db.ssl_mode)
    
    pulumi.export("redis_url", redis_cache.redis_url)
    pulumi.export("redis_memory_mb", redis_cache.memory_mb)
    pulumi.export("redis_max_connections", redis_cache.max_connections)
    
    pulumi.export("database_config", database_config)
    pulumi.export("environment", environment)
    
    # Database schemas for different services
    pulumi.export("schemas", {
        "memory_service": {
            "tables": [
                "memory_entries",
                "memory_cache", 
                "access_logs"
            ],
            "indexes": [
                "idx_memory_hash_id",
                "idx_memory_type",
                "idx_created_at"
            ]
        },
        "agent_service": {
            "tables": [
                "agent_sessions",
                "swarm_executions",
                "model_usage"
            ],
            "indexes": [
                "idx_session_id",
                "idx_execution_status",
                "idx_model_usage_date"
            ]
        },
        "observability": {
            "tables": [
                "metrics",
                "logs",
                "traces"
            ],
            "indexes": [
                "idx_metric_timestamp",
                "idx_log_level",
                "idx_trace_id"
            ]
        }
    })

if __name__ == "__main__":
    main()