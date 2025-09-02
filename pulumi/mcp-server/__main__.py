"""
MCP Server Infrastructure for Sophia Intel AI
Deploys unified memory service with Model Context Protocol support.
Consolidates enhanced_memory.py, supermemory_mcp.py, and enhanced_mcp_server.py
"""

import os
import sys

import pulumi
from pulumi import StackReference

# Add shared components to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from shared import FlyApp, FlyAppConfig


def main():
    """Deploy MCP server infrastructure."""

    config = pulumi.Config()
    environment = config.get("environment") or "dev"
    memory_pool_size = config.get_int("memory_pool_size") or 20
    enable_mcp = config.get_bool("enable_mcp_protocol") or True

    # Reference other stacks
    shared_stack = StackReference(f"shared-{environment}")
    database_stack = StackReference(f"database-{environment}")
    vector_stack = StackReference(f"vector-store-{environment}")

    # MCP Server Configuration (Unified Memory Service)
    mcp_server_config = FlyAppConfig(
        name=f"sophia-mcp-server-{environment}",
        image="ghcr.io/sophia-intel-ai/mcp-server:latest",
        port=8080,
        scale=2,  # Multiple instances for reliability
        memory_mb=2048,  # High memory for caching and connection pooling
        cpu_cores=2.0,   # High CPU for memory operations
        env_vars={
            "ENVIRONMENT": environment,
            "LOG_LEVEL": "INFO" if environment == "prod" else "DEBUG",

            # Database connections (from consolidated strategy)
            "POSTGRES_URL": database_stack.get_output("postgres_connection_string"),
            "REDIS_URL": database_stack.get_output("redis_url"),
            "WEAVIATE_URL": vector_stack.get_output("weaviate_url"),

            # Unified Memory Configuration
            "MEMORY_BACKEND": "hybrid",  # SQLite FTS5 + Weaviate + Redis
            "SQLITE_PATH": "/data/unified_memory.db",
            "ENABLE_VECTOR_SEARCH": "true",
            "ENABLE_FTS_SEARCH": "true",
            "ENABLE_RERANKING": "true",

            # Connection Pooling (from enhanced_mcp_server.py)
            "CONNECTION_POOL_SIZE": str(memory_pool_size),
            "CONNECTION_TIMEOUT": "30.0",
            "RETRY_ATTEMPTS": "3",
            "RETRY_DELAY": "0.5",
            "ENABLE_METRICS": "true",

            # MCP Protocol Support (from supermemory_mcp.py)
            "ENABLE_MCP_PROTOCOL": str(enable_mcp).lower(),
            "MCP_PORT": "8081",
            "MCP_MAX_CONNECTIONS": "100",
            "MCP_TIMEOUT_SECONDS": "30",

            # Memory Types and Patterns
            "SUPPORTED_MEMORY_TYPES": "episodic,semantic,procedural",
            "ENABLE_DEDUPLICATION": "true",
            "DEDUP_STRATEGY": "hash_based",
            "MAX_MEMORY_ENTRIES": "100000",

            # Search and Retrieval Configuration
            "MAX_SEARCH_RESULTS": "50",
            "SEARCH_TIMEOUT_SECONDS": "5.0",
            "HYBRID_SEARCH_WEIGHTS": "vector:0.65,fts:0.35",
            "ENABLE_SEARCH_CACHE": "true",
            "CACHE_TTL_SECONDS": "3600",

            # Performance Tuning
            "EMBEDDING_BATCH_SIZE": "100",
            "ASYNC_PROCESSING": "true",
            "MAX_CONCURRENT_REQUESTS": "50",
            "WORKER_PROCESSES": "4",

            # Integration with other services
            "VECTOR_STORE_URL": vector_stack.get_output("vector_store_internal_url"),
            "ENABLE_CROSS_SERVICE_SEARCH": "true",

            # Health and Monitoring
            "HEALTH_CHECK_INTERVAL": "15",
            "METRICS_PORT": "9090",
            "ENABLE_PROMETHEUS_METRICS": "true"
        },
        volumes={
            "/data": "mcp-server-data"  # Persistent volume for SQLite
        }
    )

    # Deploy MCP Server
    mcp_server = FlyApp("mcp-server", mcp_server_config)

    # Export outputs for other stacks
    pulumi.export("mcp_server_url", mcp_server.public_url)
    pulumi.export("mcp_server_internal_url", mcp_server.internal_url)

    # Memory service configuration
    pulumi.export("unified_memory_config", {
        "backends": {
            "sqlite": {
                "enabled": True,
                "features": ["fts5", "metadata", "deduplication"],
                "path": "/data/unified_memory.db"
            },
            "weaviate": {
                "enabled": True,
                "features": ["vector_search", "semantic_similarity"],
                "collections": ["MemoryEntries", "CodeChunks", "Documents"]
            },
            "redis": {
                "enabled": True,
                "features": ["caching", "session_storage"],
                "key_prefix": f"sophia:{environment}:memory:"
            }
        },
        "search_capabilities": {
            "hybrid_search": True,
            "vector_similarity": True,
            "full_text_search": True,
            "semantic_reranking": True,
            "filtered_search": True,
            "aggregated_search": True
        },
        "memory_patterns": {
            "decision_memory": {
                "template": "Decision: {decision}\nRationale: {rationale}\nAlternatives: {alternatives}",
                "tags": ["decision", "architecture"]
            },
            "pattern_memory": {
                "template": "Pattern: {name}\nImplementation: {code}\nUse cases: {use_cases}",
                "tags": ["pattern", "reusable"]
            },
            "edge_case_memory": {
                "template": "Issue: {issue}\nSolution: {solution}\nPrevention: {prevention}",
                "tags": ["edge-case", "gotcha"]
            }
        }
    })

    # MCP Protocol Configuration
    if enable_mcp:
        pulumi.export("mcp_protocol", {
            "enabled": True,
            "version": "1.0",
            "endpoints": {
                "add_to_memory": "/mcp/memory/add",
                "search_memory": "/mcp/memory/search",
                "get_stats": "/mcp/stats",
                "health_check": "/mcp/health"
            },
            "supported_methods": [
                "add_to_memory",
                "search_memory",
                "update_memory",
                "delete_memory",
                "get_stats",
                "list_memory_types"
            ],
            "authentication": {
                "type": "api_key",
                "header": "X-MCP-API-Key"
            }
        })

    # Tool management configuration
    pulumi.export("tool_management", {
        "supported_tools": {
            "memory": {
                "operations": ["add", "search", "update", "delete"],
                "formats": ["json", "markdown", "plain_text"]
            },
            "search": {
                "types": ["semantic", "keyword", "hybrid"],
                "filters": ["type", "source", "date", "tags"]
            },
            "analytics": {
                "metrics": ["usage", "performance", "accuracy"],
                "reports": ["daily", "weekly", "monthly"]
            }
        },
        "integration": {
            "vscode_extension": True,
            "cli_tools": True,
            "api_clients": True,
            "webhook_support": True
        }
    })

    # Performance and reliability metrics
    pulumi.export("reliability_config", {
        "connection_pooling": {
            "pool_size": memory_pool_size,
            "max_connections": memory_pool_size * 2,
            "timeout": 30,
            "retry_attempts": 3,
            "circuit_breaker": True
        },
        "caching": {
            "levels": ["memory", "redis", "disk"],
            "ttl_default": 3600,
            "max_cache_size": "1GB",
            "eviction_policy": "lru"
        },
        "monitoring": {
            "health_checks": True,
            "performance_metrics": True,
            "error_tracking": True,
            "usage_analytics": True
        },
        "scalability": {
            "horizontal_scaling": True,
            "auto_scaling": True,
            "load_balancing": True,
            "data_partitioning": True
        }
    })

    pulumi.export("environment", environment)

if __name__ == "__main__":
    main()
