"""
Enhanced MCP Server Registry with Domain-Aware Routing
Extends basic registry with domain partitioning and intelligent allocation
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.mcp.router_config import (
    MCPRouterConfiguration,
    MCPServerConfig,
    MCPServerType,
    MemoryDomain,
)

logger = logging.getLogger(__name__)


@dataclass
class ServerAllocation:
    """Represents server allocation to a domain"""

    server_name: str
    server_type: MCPServerType
    domain: MemoryDomain
    access_level: str  # "exclusive", "shared", "read_only"
    priority: int = 0
    filters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainPartition:
    """Represents a partitioned resource within a domain"""

    domain: MemoryDomain
    resource_type: str
    partition_key: str
    partition_config: dict[str, Any]
    access_rules: dict[str, Any] = field(default_factory=dict)


class MCPServerRegistry:
    """
    Enhanced MCP Server Registry with domain-aware routing,
    connection allocation, and intelligent partitioning
    """

    def __init__(self):
        # Core registry components
        self.servers: dict[str, MCPServerConfig] = {}
        self.allocations: dict[MemoryDomain, list[ServerAllocation]] = defaultdict(list)
        self.partitions: dict[str, list[DomainPartition]] = defaultdict(list)
        self.active_connections: dict[str, int] = defaultdict(int)

        # Router configuration
        self.router = MCPRouterConfiguration()

        # Connection tracking
        self.connection_history: list[dict[str, Any]] = []
        self.domain_metrics: dict[MemoryDomain, dict[str, Any]] = defaultdict(dict)

        # Initialize registry
        self._initialize_registry()

    def _initialize_registry(self):
        """Initialize the registry with domain allocations"""

        # Register all servers from router configuration
        for server_name, server_config in self.router.server_configs.items():
            self.register_server(server_name, server_config)

        # Setup domain allocations
        self._setup_artemis_allocations()
        self._setup_sophia_allocations()
        self._setup_shared_allocations()

        # Initialize partitioning strategies
        self._initialize_partitions()

    def _setup_artemis_allocations(self):
        """Setup Artemis domain server allocations"""

        # Exclusive Artemis servers
        self.allocations[MemoryDomain.ARTEMIS].extend(
            [
                ServerAllocation(
                    server_name="artemis_filesystem",
                    server_type=MCPServerType.FILESYSTEM,
                    domain=MemoryDomain.ARTEMIS,
                    access_level="exclusive",
                    priority=1,
                    metadata={"critical": True, "ops": ["read", "write", "watch"]},
                ),
                ServerAllocation(
                    server_name="artemis_code_analysis",
                    server_type=MCPServerType.CODE_ANALYSIS,
                    domain=MemoryDomain.ARTEMIS,
                    access_level="exclusive",
                    priority=1,
                    metadata={"compute_intensive": True},
                ),
                ServerAllocation(
                    server_name="artemis_design",
                    server_type=MCPServerType.DESIGN_SERVER,
                    domain=MemoryDomain.ARTEMIS,
                    access_level="exclusive",
                    priority=2,
                    metadata={"document_types": ["architecture", "uml", "erd"]},
                ),
            ]
        )

        # Shared servers with Artemis-specific configurations
        self.allocations[MemoryDomain.ARTEMIS].extend(
            [
                ServerAllocation(
                    server_name="shared_database",
                    server_type=MCPServerType.DATABASE,
                    domain=MemoryDomain.ARTEMIS,
                    access_level="shared",
                    priority=1,
                    filters={
                        "schemas": ["code_metrics", "technical_debt", "test_coverage"],
                        "tables_prefix": "artemis_",
                    },
                ),
                ServerAllocation(
                    server_name="shared_indexing",
                    server_type=MCPServerType.INDEXING,
                    domain=MemoryDomain.ARTEMIS,
                    access_level="shared",
                    priority=1,
                    filters={
                        "index_partitions": ["code", "tests", "documentation"],
                        "index_prefix": "artemis_",
                    },
                ),
                ServerAllocation(
                    server_name="shared_embedding",
                    server_type=MCPServerType.EMBEDDING,
                    domain=MemoryDomain.ARTEMIS,
                    access_level="shared",
                    priority=1,
                    filters={
                        "namespaces": ["technical_embeddings", "code_embeddings"],
                        "model": "code-embedding-v2",
                    },
                ),
                ServerAllocation(
                    server_name="shared_meta_tagging",
                    server_type=MCPServerType.META_TAGGING,
                    domain=MemoryDomain.ARTEMIS,
                    access_level="shared",
                    priority=2,
                    filters={
                        "tag_categories": ["code", "architecture", "security", "performance"],
                        "auto_tag": True,
                    },
                ),
                ServerAllocation(
                    server_name="shared_chunking",
                    server_type=MCPServerType.CHUNKING,
                    domain=MemoryDomain.ARTEMIS,
                    access_level="shared",
                    priority=3,
                    filters={"strategy": "ast_based", "chunk_size": 512, "overlap": 50},
                ),
            ]
        )

    def _setup_sophia_allocations(self):
        """Setup Sophia domain server allocations"""

        # Exclusive Sophia servers
        self.allocations[MemoryDomain.SOPHIA].extend(
            [
                ServerAllocation(
                    server_name="sophia_web_search",
                    server_type=MCPServerType.WEB_SEARCH,
                    domain=MemoryDomain.SOPHIA,
                    access_level="exclusive",
                    priority=1,
                    metadata={"external": True, "rate_limited": True},
                ),
                ServerAllocation(
                    server_name="sophia_analytics",
                    server_type=MCPServerType.BUSINESS_ANALYTICS,
                    domain=MemoryDomain.SOPHIA,
                    access_level="exclusive",
                    priority=1,
                    metadata={"critical": True, "real_time": True},
                ),
            ]
        )

        # Shared servers with Sophia-specific configurations
        self.allocations[MemoryDomain.SOPHIA].extend(
            [
                ServerAllocation(
                    server_name="shared_database",
                    server_type=MCPServerType.DATABASE,
                    domain=MemoryDomain.SOPHIA,
                    access_level="shared",
                    priority=1,
                    filters={
                        "schemas": ["sales_data", "customer_health", "revenue_metrics"],
                        "tables_prefix": "sophia_",
                    },
                ),
                ServerAllocation(
                    server_name="shared_indexing",
                    server_type=MCPServerType.INDEXING,
                    domain=MemoryDomain.SOPHIA,
                    access_level="shared",
                    priority=1,
                    filters={
                        "index_partitions": ["business", "customers", "market"],
                        "index_prefix": "sophia_",
                    },
                ),
                ServerAllocation(
                    server_name="shared_embedding",
                    server_type=MCPServerType.EMBEDDING,
                    domain=MemoryDomain.SOPHIA,
                    access_level="shared",
                    priority=1,
                    filters={
                        "namespaces": ["business_embeddings", "market_embeddings"],
                        "model": "business-embedding-v2",
                    },
                ),
                ServerAllocation(
                    server_name="shared_meta_tagging",
                    server_type=MCPServerType.META_TAGGING,
                    domain=MemoryDomain.SOPHIA,
                    access_level="shared",
                    priority=2,
                    filters={
                        "tag_categories": ["business", "customer", "revenue", "market"],
                        "auto_tag": True,
                    },
                ),
                ServerAllocation(
                    server_name="shared_chunking",
                    server_type=MCPServerType.CHUNKING,
                    domain=MemoryDomain.SOPHIA,
                    access_level="shared",
                    priority=3,
                    filters={"strategy": "semantic_based", "chunk_size": 1024, "overlap": 100},
                ),
            ]
        )

    def _setup_shared_allocations(self):
        """Setup shared domain allocations"""

        # Common shared resources
        self.allocations[MemoryDomain.SHARED].extend(
            [
                ServerAllocation(
                    server_name="shared_knowledge_base",
                    server_type=MCPServerType.KNOWLEDGE_BASE,
                    domain=MemoryDomain.SHARED,
                    access_level="shared",
                    priority=2,
                    filters={
                        "stores": ["common_knowledge", "glossary", "standards"],
                        "access": "read_write",
                    },
                )
            ]
        )

    def _initialize_partitions(self):
        """Initialize resource partitioning strategies"""

        # Database partitions
        self.partitions["database"] = [
            DomainPartition(
                domain=MemoryDomain.ARTEMIS,
                resource_type="database",
                partition_key="schema",
                partition_config={
                    "schemas": ["code_metrics", "technical_debt", "test_coverage"],
                    "isolation_level": "read_committed",
                },
            ),
            DomainPartition(
                domain=MemoryDomain.SOPHIA,
                resource_type="database",
                partition_key="schema",
                partition_config={
                    "schemas": ["sales_data", "customer_health", "revenue_metrics"],
                    "isolation_level": "read_committed",
                },
            ),
        ]

        # Indexing partitions
        self.partitions["indexing"] = [
            DomainPartition(
                domain=MemoryDomain.ARTEMIS,
                resource_type="indexing",
                partition_key="index_name",
                partition_config={
                    "indices": ["artemis_code", "artemis_tests", "artemis_docs"],
                    "sharding": True,
                    "replicas": 2,
                },
            ),
            DomainPartition(
                domain=MemoryDomain.SOPHIA,
                resource_type="indexing",
                partition_key="index_name",
                partition_config={
                    "indices": ["sophia_business", "sophia_customers", "sophia_market"],
                    "sharding": True,
                    "replicas": 2,
                },
            ),
        ]

        # Embedding namespaces
        self.partitions["embedding"] = [
            DomainPartition(
                domain=MemoryDomain.ARTEMIS,
                resource_type="embedding",
                partition_key="namespace",
                partition_config={
                    "namespaces": ["technical_embeddings", "code_embeddings"],
                    "model": "code-embedding-v2",
                    "dimensions": 768,
                },
            ),
            DomainPartition(
                domain=MemoryDomain.SOPHIA,
                resource_type="embedding",
                partition_key="namespace",
                partition_config={
                    "namespaces": ["business_embeddings", "market_embeddings"],
                    "model": "business-embedding-v2",
                    "dimensions": 768,
                },
            ),
        ]

    def register_server(self, server_name: str, server_config: MCPServerConfig) -> bool:
        """
        Register a new MCP server

        Args:
            server_name: Unique server identifier
            server_config: Server configuration

        Returns:
            True if registered successfully
        """
        if server_name in self.servers:
            logger.warning(f"Server {server_name} already registered")
            return False

        self.servers[server_name] = server_config
        self.active_connections[server_name] = 0
        logger.info(f"Registered MCP server: {server_name}")
        return True

    def get_servers_for_domain(
        self, domain: MemoryDomain, server_type: Optional[MCPServerType] = None
    ) -> list[ServerAllocation]:
        """
        Get all servers allocated to a domain

        Args:
            domain: Domain to query
            server_type: Optional filter by server type

        Returns:
            List of server allocations
        """
        allocations = self.allocations.get(domain, [])

        if server_type:
            allocations = [a for a in allocations if a.server_type == server_type]

        # Sort by priority
        return sorted(allocations, key=lambda x: x.priority)

    def allocate_connection(
        self,
        domain: MemoryDomain,
        server_type: MCPServerType,
        request_metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[tuple[str, dict[str, Any]]]:
        """
        Allocate a connection for a domain and server type

        Args:
            domain: Requesting domain
            server_type: Type of server needed
            request_metadata: Optional request metadata

        Returns:
            Tuple of (server_name, connection_config) or None
        """
        # Get valid allocations
        allocations = self.get_servers_for_domain(domain, server_type)

        if not allocations:
            logger.error(f"No servers available for domain {domain} and type {server_type}")
            return None

        # Find the best available server
        for allocation in allocations:
            server_config = self.servers.get(allocation.server_name)
            if not server_config:
                continue

            # Check connection limits
            current_connections = self.active_connections[allocation.server_name]
            max_connections = server_config.connection_pool.max_connections

            if current_connections < max_connections:
                # Allocate connection
                self.active_connections[allocation.server_name] += 1

                # Track allocation
                self._track_allocation(domain, allocation, request_metadata)

                # Build connection config with filters
                connection_config = {
                    "endpoint": server_config.endpoint,
                    "timeout": server_config.connection_pool.connection_timeout,
                    "filters": allocation.filters,
                    "metadata": {**server_config.metadata, **allocation.metadata},
                }

                return allocation.server_name, connection_config

        logger.warning(f"All servers at capacity for domain {domain} and type {server_type}")
        return None

    def release_connection(self, server_name: str, domain: MemoryDomain) -> bool:
        """
        Release a connection back to the pool

        Args:
            server_name: Server to release connection from
            domain: Domain releasing the connection

        Returns:
            True if released successfully
        """
        if server_name not in self.servers:
            logger.error(f"Unknown server: {server_name}")
            return False

        if self.active_connections[server_name] > 0:
            self.active_connections[server_name] -= 1
            logger.debug(f"Released connection for {server_name} from domain {domain}")
            return True
        else:
            logger.warning(f"No active connections to release for {server_name}")
            return False

    def get_partition_config(
        self, resource_type: str, domain: MemoryDomain
    ) -> Optional[DomainPartition]:
        """
        Get partition configuration for a resource and domain

        Args:
            resource_type: Type of resource (database, indexing, etc.)
            domain: Domain requesting partition info

        Returns:
            Partition configuration or None
        """
        partitions = self.partitions.get(resource_type, [])

        for partition in partitions:
            if partition.domain == domain:
                return partition

        return None

    def _track_allocation(
        self,
        domain: MemoryDomain,
        allocation: ServerAllocation,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Track connection allocation for metrics"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "domain": domain.value,
            "server_name": allocation.server_name,
            "server_type": allocation.server_type.value,
            "access_level": allocation.access_level,
            "metadata": metadata or {},
        }

        self.connection_history.append(event)

        # Update domain metrics
        if domain not in self.domain_metrics:
            self.domain_metrics[domain] = {
                "total_allocations": 0,
                "active_connections": 0,
                "server_usage": defaultdict(int),
            }

        self.domain_metrics[domain]["total_allocations"] += 1
        self.domain_metrics[domain]["active_connections"] += 1
        self.domain_metrics[domain]["server_usage"][allocation.server_name] += 1

    def get_metrics(self) -> dict[str, Any]:
        """Get registry metrics"""
        return {
            "total_servers": len(self.servers),
            "active_connections": sum(self.active_connections.values()),
            "domain_metrics": {
                domain.value: metrics for domain, metrics in self.domain_metrics.items()
            },
            "server_utilization": {
                server_name: {
                    "active": connections,
                    "max": self.servers[server_name].connection_pool.max_connections,
                    "utilization": connections
                    / self.servers[server_name].connection_pool.max_connections,
                }
                for server_name, connections in self.active_connections.items()
                if server_name in self.servers
            },
            "partition_count": sum(len(p) for p in self.partitions.values()),
        }

    def validate_domain_access(self, domain: MemoryDomain, server_type: MCPServerType) -> bool:
        """
        Validate if a domain can access a server type

        Args:
            domain: Domain to validate
            server_type: Server type to check

        Returns:
            True if access is allowed
        """
        # Check routing rules
        routing_rule = self.router.routing_rules.get(server_type)
        if not routing_rule:
            return False

        return domain in routing_rule.allowed_domains

    def get_connection_summary(self) -> dict[str, Any]:
        """Get summary of all connections and allocations"""
        summary = {
            "artemis": {"exclusive_servers": [], "shared_servers": [], "total_connections": 0},
            "sophia": {"exclusive_servers": [], "shared_servers": [], "total_connections": 0},
            "shared": {"servers": [], "total_connections": 0},
        }

        for domain in [MemoryDomain.ARTEMIS, MemoryDomain.SOPHIA]:
            allocations = self.allocations.get(domain, [])
            for allocation in allocations:
                if allocation.access_level == "exclusive":
                    summary[domain.value]["exclusive_servers"].append(allocation.server_name)
                else:
                    summary[domain.value]["shared_servers"].append(allocation.server_name)

                connections = self.active_connections.get(allocation.server_name, 0)
                summary[domain.value]["total_connections"] += connections

        # Add shared domain servers
        shared_allocations = self.allocations.get(MemoryDomain.SHARED, [])
        for allocation in shared_allocations:
            summary["shared"]["servers"].append(allocation.server_name)
            connections = self.active_connections.get(allocation.server_name, 0)
            summary["shared"]["total_connections"] += connections

        return summary
