"""
MCP Router Configuration for Sophia-Artemis Consolidated System
Implements domain-aware routing with connection pooling and health checks
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MCPServerType(Enum):
    """MCP Server Types with domain associations"""

    # Technical Domain (Artemis Exclusive)
    FILESYSTEM = "filesystem"
    CODE_ANALYSIS = "code_analysis"
    DESIGN_SERVER = "design_server"

    # Business Domain (Sophia Exclusive)
    WEB_SEARCH = "web_search"
    BUSINESS_ANALYTICS = "business_analytics"
    SALES_INTELLIGENCE = "sales_intelligence"

    # Shared Resources (Both Domains)
    DATABASE = "database"
    KNOWLEDGE_BASE = "knowledge_base"
    INDEXING = "indexing"
    EMBEDDING = "embedding"
    META_TAGGING = "meta_tagging"
    CHUNKING = "chunking"


class MemoryDomain(Enum):
    """Memory domains for routing"""

    ARTEMIS = "artemis"
    SOPHIA = "sophia"
    SHARED = "shared"


@dataclass
class ConnectionPool:
    """Connection pool configuration for an MCP server"""

    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: int = 30
    idle_timeout: int = 300
    retry_attempts: int = 3
    retry_delay: float = 1.0
    health_check_interval: int = 60


@dataclass
class HealthCheckConfig:
    """Health check configuration for MCP servers"""

    enabled: bool = True
    interval_seconds: int = 30
    timeout_seconds: int = 10
    failure_threshold: int = 3
    success_threshold: int = 2
    check_endpoint: str = "/health"


@dataclass
class RoutingRule:
    """Routing rule for MCP server access"""

    server_type: MCPServerType
    allowed_domains: set[MemoryDomain]
    priority: int = 0
    filters: dict[str, Any] = field(default_factory=dict)
    load_balancing: str = "round_robin"  # round_robin, least_connections, random


@dataclass
class MCPServerConfig:
    """Configuration for an individual MCP server"""

    name: str
    server_type: MCPServerType
    endpoint: str
    connection_pool: ConnectionPool
    health_check: HealthCheckConfig
    metadata: dict[str, Any] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)


class MCPRouterConfiguration:
    """
    MCP Router Configuration with domain-aware routing,
    connection pooling, and health monitoring
    """

    def __init__(self):
        self.routing_rules: dict[MCPServerType, RoutingRule] = {}
        self.server_configs: dict[str, MCPServerConfig] = {}
        self.connection_pools: dict[str, Any] = {}
        self.health_status: dict[str, bool] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Initialize routing rules
        self._initialize_routing_rules()

        # Initialize server configurations
        self._initialize_server_configs()

        # Health monitoring will be started later when event loop is available
        self._health_monitoring_task = None

    async def start_health_monitoring(self):
        """Start health monitoring if not already started"""
        if self._health_monitoring_task is None:
            try:
                self._health_monitoring_task = asyncio.create_task(self._health_monitor_loop())
                logger.info("MCP health monitoring started")
            except Exception as e:
                logger.error(f"Failed to start MCP health monitoring: {e}")

    def _initialize_routing_rules(self):
        """Initialize routing rules for each MCP server type"""

        # Artemis Exclusive Servers
        self.routing_rules[MCPServerType.FILESYSTEM] = RoutingRule(
            server_type=MCPServerType.FILESYSTEM,
            allowed_domains={MemoryDomain.ARTEMIS},
            priority=1,
            filters={"operation_types": ["read", "write", "delete", "modify"]},
        )

        self.routing_rules[MCPServerType.CODE_ANALYSIS] = RoutingRule(
            server_type=MCPServerType.CODE_ANALYSIS,
            allowed_domains={MemoryDomain.ARTEMIS},
            priority=1,
            filters={"analysis_types": ["syntax", "security", "performance", "quality"]},
        )

        self.routing_rules[MCPServerType.DESIGN_SERVER] = RoutingRule(
            server_type=MCPServerType.DESIGN_SERVER,
            allowed_domains={MemoryDomain.ARTEMIS},
            priority=2,
            filters={"document_types": ["architecture", "uml", "erd", "flowchart"]},
        )

        # Sophia Exclusive Servers
        self.routing_rules[MCPServerType.WEB_SEARCH] = RoutingRule(
            server_type=MCPServerType.WEB_SEARCH,
            allowed_domains={MemoryDomain.SOPHIA},
            priority=1,
            filters={"search_scope": ["market", "competitors", "trends", "news"]},
        )

        self.routing_rules[MCPServerType.BUSINESS_ANALYTICS] = RoutingRule(
            server_type=MCPServerType.BUSINESS_ANALYTICS,
            allowed_domains={MemoryDomain.SOPHIA},
            priority=1,
            filters={"metrics": ["revenue", "churn", "cac", "ltv", "nps"]},
        )

        # Shared Resources with Domain Filtering
        self.routing_rules[MCPServerType.DATABASE] = RoutingRule(
            server_type=MCPServerType.DATABASE,
            allowed_domains={MemoryDomain.ARTEMIS, MemoryDomain.SOPHIA},
            priority=1,
            filters={
                "artemis": {"schemas": ["code_metrics", "technical_debt", "test_coverage"]},
                "sophia": {"schemas": ["sales_data", "customer_health", "revenue_metrics"]},
            },
            load_balancing="least_connections",
        )

        self.routing_rules[MCPServerType.KNOWLEDGE_BASE] = RoutingRule(
            server_type=MCPServerType.KNOWLEDGE_BASE,
            allowed_domains={MemoryDomain.ARTEMIS, MemoryDomain.SOPHIA},
            priority=2,
            filters={
                "artemis": {"stores": ["code_patterns", "best_practices", "documentation"]},
                "sophia": {
                    "stores": ["business_insights", "market_intelligence", "customer_knowledge"]
                },
            },
        )

        self.routing_rules[MCPServerType.INDEXING] = RoutingRule(
            server_type=MCPServerType.INDEXING,
            allowed_domains={MemoryDomain.ARTEMIS, MemoryDomain.SOPHIA, MemoryDomain.SHARED},
            priority=1,
            filters={"partitioning": "domain_based", "index_strategy": "hybrid"},
        )

        self.routing_rules[MCPServerType.EMBEDDING] = RoutingRule(
            server_type=MCPServerType.EMBEDDING,
            allowed_domains={MemoryDomain.ARTEMIS, MemoryDomain.SOPHIA, MemoryDomain.SHARED},
            priority=1,
            filters={
                "namespaces": {
                    "artemis": "technical_embeddings",
                    "sophia": "business_embeddings",
                    "shared": "common_embeddings",
                }
            },
        )

        self.routing_rules[MCPServerType.META_TAGGING] = RoutingRule(
            server_type=MCPServerType.META_TAGGING,
            allowed_domains={MemoryDomain.ARTEMIS, MemoryDomain.SOPHIA, MemoryDomain.SHARED},
            priority=2,
            filters={
                "tag_domains": {
                    "artemis": ["code", "architecture", "security", "performance"],
                    "sophia": ["business", "customer", "revenue", "market"],
                }
            },
        )

        self.routing_rules[MCPServerType.CHUNKING] = RoutingRule(
            server_type=MCPServerType.CHUNKING,
            allowed_domains={MemoryDomain.ARTEMIS, MemoryDomain.SOPHIA, MemoryDomain.SHARED},
            priority=3,
            filters={
                "strategies": {
                    "artemis": "ast_based",  # Abstract Syntax Tree based for code
                    "sophia": "semantic_based",  # Semantic chunking for business docs
                }
            },
        )

    def _initialize_server_configs(self):
        """Initialize server configurations with connection pools and health checks"""

        # Artemis Technical Servers
        self.server_configs["artemis_filesystem"] = MCPServerConfig(
            name="artemis_filesystem",
            server_type=MCPServerType.FILESYSTEM,
            endpoint="ws://localhost:8010/mcp",
            connection_pool=ConnectionPool(
                min_connections=3, max_connections=10, connection_timeout=30
            ),
            health_check=HealthCheckConfig(interval_seconds=30, failure_threshold=3),
            capabilities=["read", "write", "watch", "delete"],
            metadata={"domain": "artemis", "priority": "high"},
        )

        self.server_configs["artemis_code_analysis"] = MCPServerConfig(
            name="artemis_code_analysis",
            server_type=MCPServerType.CODE_ANALYSIS,
            endpoint="ws://localhost:8011/mcp",
            connection_pool=ConnectionPool(
                min_connections=2, max_connections=8, connection_timeout=60
            ),
            health_check=HealthCheckConfig(interval_seconds=45, timeout_seconds=15),
            capabilities=["analyze", "lint", "format", "refactor"],
            metadata={"domain": "artemis", "compute_intensive": True},
        )

        self.server_configs["artemis_design"] = MCPServerConfig(
            name="artemis_design",
            server_type=MCPServerType.DESIGN_SERVER,
            endpoint="ws://localhost:8012/mcp",
            connection_pool=ConnectionPool(
                min_connections=1, max_connections=5, connection_timeout=45
            ),
            health_check=HealthCheckConfig(interval_seconds=60),
            capabilities=["generate_diagram", "parse_architecture", "validate_design"],
            metadata={"domain": "artemis"},
        )

        # Sophia Business Servers
        self.server_configs["sophia_web_search"] = MCPServerConfig(
            name="sophia_web_search",
            server_type=MCPServerType.WEB_SEARCH,
            endpoint="ws://localhost:8020/mcp",
            connection_pool=ConnectionPool(
                min_connections=2, max_connections=10, connection_timeout=30, retry_attempts=5
            ),
            health_check=HealthCheckConfig(
                interval_seconds=30, failure_threshold=5  # More tolerant for external service
            ),
            capabilities=["search", "scrape", "monitor"],
            metadata={"domain": "sophia", "external": True},
        )

        self.server_configs["sophia_analytics"] = MCPServerConfig(
            name="sophia_analytics",
            server_type=MCPServerType.BUSINESS_ANALYTICS,
            endpoint="ws://localhost:8021/mcp",
            connection_pool=ConnectionPool(
                min_connections=3, max_connections=10, connection_timeout=45
            ),
            health_check=HealthCheckConfig(interval_seconds=30),
            capabilities=["calculate_metrics", "generate_reports", "forecast"],
            metadata={"domain": "sophia", "priority": "high"},
        )

        # Shared Infrastructure Servers
        self.server_configs["shared_database"] = MCPServerConfig(
            name="shared_database",
            server_type=MCPServerType.DATABASE,
            endpoint="ws://localhost:8030/mcp",
            connection_pool=ConnectionPool(
                min_connections=5, max_connections=10, connection_timeout=30, idle_timeout=600
            ),
            health_check=HealthCheckConfig(interval_seconds=20, failure_threshold=2),
            capabilities=["query", "insert", "update", "delete", "transaction"],
            metadata={"domain": "shared", "critical": True},
        )

        self.server_configs["shared_indexing"] = MCPServerConfig(
            name="shared_indexing",
            server_type=MCPServerType.INDEXING,
            endpoint="ws://localhost:8031/mcp",
            connection_pool=ConnectionPool(
                min_connections=3, max_connections=10, connection_timeout=30
            ),
            health_check=HealthCheckConfig(interval_seconds=30),
            capabilities=["index", "search", "update_index", "delete_index"],
            metadata={"domain": "shared", "partitioned": True},
        )

        self.server_configs["shared_embedding"] = MCPServerConfig(
            name="shared_embedding",
            server_type=MCPServerType.EMBEDDING,
            endpoint="ws://localhost:8032/mcp",
            connection_pool=ConnectionPool(
                min_connections=2, max_connections=8, connection_timeout=60
            ),
            health_check=HealthCheckConfig(interval_seconds=45, timeout_seconds=20),
            capabilities=["generate_embedding", "similarity_search", "batch_embed"],
            metadata={"domain": "shared", "compute_intensive": True},
        )

        self.server_configs["shared_meta_tagging"] = MCPServerConfig(
            name="shared_meta_tagging",
            server_type=MCPServerType.META_TAGGING,
            endpoint="ws://localhost:8033/mcp",
            connection_pool=ConnectionPool(
                min_connections=2, max_connections=8, connection_timeout=30
            ),
            health_check=HealthCheckConfig(interval_seconds=40),
            capabilities=["tag", "classify", "extract_metadata"],
            metadata={"domain": "shared"},
        )

        self.server_configs["shared_chunking"] = MCPServerConfig(
            name="shared_chunking",
            server_type=MCPServerType.CHUNKING,
            endpoint="ws://localhost:8034/mcp",
            connection_pool=ConnectionPool(
                min_connections=2, max_connections=6, connection_timeout=45
            ),
            health_check=HealthCheckConfig(interval_seconds=50),
            capabilities=["chunk_document", "chunk_code", "merge_chunks"],
            metadata={"domain": "shared", "strategy_aware": True},
        )

    async def route_request(
        self, server_type: MCPServerType, domain: MemoryDomain, request: dict[str, Any]
    ) -> Optional[str]:
        """
        Route a request to the appropriate MCP server based on domain and type

        Args:
            server_type: Type of MCP server needed
            domain: Domain making the request
            request: Request details

        Returns:
            Server name to route to, or None if not allowed
        """
        rule = self.routing_rules.get(server_type)
        if not rule:
            logger.error(f"No routing rule for server type: {server_type}")
            return None

        # Check domain access
        if domain not in rule.allowed_domains:
            logger.warning(f"Domain {domain} not allowed to access {server_type}")
            return None

        # Apply domain-specific filters
        if domain.value in rule.filters:
            domain_filters = rule.filters[domain.value]
            # Apply filters to request
            request["domain_filters"] = domain_filters

        # Find healthy servers of this type
        healthy_servers = [
            name
            for name, config in self.server_configs.items()
            if config.server_type == server_type and self.health_status.get(name, False)
        ]

        if not healthy_servers:
            logger.error(f"No healthy servers available for {server_type}")
            return None

        # Apply load balancing strategy
        if rule.load_balancing == "round_robin":
            # Simple round-robin (would need state tracking in production)
            return healthy_servers[0]
        elif rule.load_balancing == "least_connections":
            # Return server with least active connections
            return min(healthy_servers, key=lambda s: self._get_active_connections(s))
        else:  # random
            import random

            return random.choice(healthy_servers)

    def _get_active_connections(self, server_name: str) -> int:
        """Get number of active connections for a server"""
        pool = self.connection_pools.get(server_name)
        if pool:
            return pool.get("active_connections", 0)
        return 0

    async def _health_monitor_loop(self):
        """Continuous health monitoring loop for all servers"""
        while True:
            for name, config in self.server_configs.items():
                if config.health_check.enabled:
                    asyncio.create_task(self._check_server_health(name, config))

            # Wait for next health check interval
            await asyncio.sleep(30)

    async def _check_server_health(self, server_name: str, config: MCPServerConfig) -> bool:
        """
        Check health of a specific MCP server

        Args:
            server_name: Name of the server
            config: Server configuration

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Implement actual health check logic here
            # This is a placeholder implementation
            logger.debug(f"Health check for {server_name}")

            # In production, would make actual health check request
            # For now, simulate with basic check
            self.health_status[server_name] = True
            return True

        except Exception as e:
            logger.error(f"Health check failed for {server_name}: {e}")
            self.health_status[server_name] = False
            return False

    def get_server_config(self, server_name: str) -> Optional[MCPServerConfig]:
        """Get configuration for a specific server"""
        return self.server_configs.get(server_name)

    def get_servers_by_domain(self, domain: MemoryDomain) -> list[MCPServerConfig]:
        """Get all servers accessible by a domain"""
        servers = []
        for server_type, rule in self.routing_rules.items():
            if domain in rule.allowed_domains:
                # Find configs for this server type
                for config in self.server_configs.values():
                    if config.server_type == server_type:
                        servers.append(config)
        return servers

    def validate_connection_limits(self) -> dict[str, bool]:
        """Validate that connection pools are within limits"""
        validation_results = {}
        for name, config in self.server_configs.items():
            pool = config.connection_pool
            current = self._get_active_connections(name)
            validation_results[name] = current <= pool.max_connections
        return validation_results

    def get_routing_summary(self) -> dict[str, Any]:
        """Get summary of routing configuration"""
        return {
            "total_servers": len(self.server_configs),
            "artemis_exclusive": [
                s for s in self.server_configs.values() if s.metadata.get("domain") == "artemis"
            ],
            "sophia_exclusive": [
                s for s in self.server_configs.values() if s.metadata.get("domain") == "sophia"
            ],
            "shared_servers": [
                s for s in self.server_configs.values() if s.metadata.get("domain") == "shared"
            ],
            "health_status": self.health_status,
            "routing_rules": len(self.routing_rules),
        }
