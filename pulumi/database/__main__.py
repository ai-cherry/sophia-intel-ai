"""
Database Infrastructure for Sophia Intel AI
Manages Neon PostgreSQL and Redis instances with connection pooling.

Following ADR-006: Configuration Management Standardization
- Uses Pulumi ESC environments for unified configuration
- Environment-specific database configurations
- Encrypted secret management for database credentials
"""

import os
import sys

import pulumi
from pulumi import StackReference

# Add shared components to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from shared import NeonDatabase, RedisCache


def main():
    """Deploy database infrastructure using ESC configuration."""

    # Get environment from ESC
    environment = os.getenv("PULUMI_ESC_ENVIRONMENT", "dev")

    # Use ESC environment variables (loaded automatically by Pulumi)
    postgres_db_name = pulumi.Config().get("postgres_db_name") or f"sophia_intel_ai_{environment}"

    # Environment-specific memory allocation
    if environment == "prod":
        redis_memory_mb = 2048
        postgres_max_connections = 200
    elif environment == "staging":
        redis_memory_mb = 512
        postgres_max_connections = 100
    else:  # dev
        redis_memory_mb = 256
        postgres_max_connections = 50

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

    # Environment-aware database configuration
    database_config = {
        "postgres": {
            "max_connections": postgres_max_connections,
            "connection_timeout": 30 if environment == "prod" else 10,
            "idle_timeout": 600,
            "pool_size": postgres_max_connections // 4,
            "ssl_mode": "require",
            "backup_retention_days": 30 if environment == "prod" else 7,
            "read_replicas": 2 if environment == "prod" else 0
        },
        "redis": {
            "max_connections": redis_memory_mb // 4,  # Scale with memory
            "connection_timeout": 5,
            "idle_timeout": 300,
            "key_prefix": f"sophia:{environment}:",
            "default_ttl": 3600,
            "cluster_mode": environment == "prod",
            "persistence": environment != "dev",
            "backup_enabled": environment == "prod"
        }
    }

    # Export database outputs for other stacks (ESC-enhanced)
    pulumi.export("postgres_connection_string", postgres_db.connection_string)
    pulumi.export("postgres_host", postgres_db.host)
    pulumi.export("postgres_port", postgres_db.port)
    pulumi.export("postgres_database", postgres_db.database_name)
    pulumi.export("postgres_ssl_mode", postgres_db.ssl_mode)
    pulumi.export("postgres_project_id", postgres_db.project_id)
    pulumi.export("postgres_branch_id", postgres_db.branch_id)

    pulumi.export("redis_url", redis_cache.redis_url)
    pulumi.export("redis_host", redis_cache.redis_host)
    pulumi.export("redis_port", redis_cache.redis_port)
    pulumi.export("redis_memory_mb", redis_cache.memory_mb)
    pulumi.export("redis_max_connections", redis_cache.max_connections)

    pulumi.export("database_config", database_config)
    pulumi.export("environment", environment)
    pulumi.export("esc_environment", environment)

    # Export ESC integration status
    pulumi.export("configuration_management", {
        "system": "pulumi_esc",
        "environment": environment,
        "adr_compliance": "ADR-006",
        "hierarchical_config": True,
        "secret_encryption": True
    })

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
