"""
Integration tests for MCP Domain-Aware Routing
Tests routing rules, domain-exclusive servers, and shared server access with filtering
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.mcp.router_config import (
    ConnectionPool,
    HealthCheckConfig,
    MCPRouterConfiguration,
    MCPServerConfig,
    MCPServerType,
    MemoryDomain,
    RoutingRule,
)


class TestMCPRouterConfiguration:
    """Test suite for MCP Router Configuration"""

    @pytest.fixture
    def router(self):
        """Create a router configuration instance"""
        # Patch asyncio.create_task to avoid background tasks
        with patch("asyncio.create_task"):
            return MCPRouterConfiguration()

    @pytest.fixture
    def sample_artemis_request(self):
        """Create a sample Artemis domain request"""
        return {
            "operation": "code_analysis",
            "target": "/src/main.py",
            "type": "security_scan",
            "metadata": {"priority": "high"},
        }

    @pytest.fixture
    def sample_sophia_request(self):
        """Create a sample Sophia domain request"""
        return {
            "operation": "market_research",
            "query": "competitive analysis",
            "scope": "competitors",
            "metadata": {"quarter": "Q4"},
        }

    # ==============================================================================
    # ROUTING RULES TESTS
    # ==============================================================================

    def test_routing_rules_initialization(self, router):
        """Test that routing rules are properly initialized"""
        # Check Artemis-exclusive servers
        assert MCPServerType.FILESYSTEM in router.routing_rules
        assert MCPServerType.CODE_ANALYSIS in router.routing_rules
        assert MCPServerType.DESIGN_SERVER in router.routing_rules

        filesystem_rule = router.routing_rules[MCPServerType.FILESYSTEM]
        assert MemoryDomain.ARTEMIS in filesystem_rule.allowed_domains
        assert MemoryDomain.SOPHIA not in filesystem_rule.allowed_domains

        # Check Sophia-exclusive servers
        assert MCPServerType.WEB_SEARCH in router.routing_rules
        assert MCPServerType.BUSINESS_ANALYTICS in router.routing_rules

        websearch_rule = router.routing_rules[MCPServerType.WEB_SEARCH]
        assert MemoryDomain.SOPHIA in websearch_rule.allowed_domains
        assert MemoryDomain.ARTEMIS not in websearch_rule.allowed_domains

        # Check shared servers
        assert MCPServerType.DATABASE in router.routing_rules
        assert MCPServerType.INDEXING in router.routing_rules
        assert MCPServerType.EMBEDDING in router.routing_rules

        database_rule = router.routing_rules[MCPServerType.DATABASE]
        assert MemoryDomain.ARTEMIS in database_rule.allowed_domains
        assert MemoryDomain.SOPHIA in database_rule.allowed_domains

    def test_domain_specific_filters_in_routing_rules(self, router):
        """Test that domain-specific filters are properly configured"""
        # Check Artemis filters
        filesystem_rule = router.routing_rules[MCPServerType.FILESYSTEM]
        assert "operation_types" in filesystem_rule.filters
        assert "read" in filesystem_rule.filters["operation_types"]
        assert "write" in filesystem_rule.filters["operation_types"]

        code_analysis_rule = router.routing_rules[MCPServerType.CODE_ANALYSIS]
        assert "analysis_types" in code_analysis_rule.filters
        assert "security" in code_analysis_rule.filters["analysis_types"]
        assert "performance" in code_analysis_rule.filters["analysis_types"]

        # Check Sophia filters
        websearch_rule = router.routing_rules[MCPServerType.WEB_SEARCH]
        assert "search_scope" in websearch_rule.filters
        assert "market" in websearch_rule.filters["search_scope"]
        assert "competitors" in websearch_rule.filters["search_scope"]

        # Check shared server filters
        database_rule = router.routing_rules[MCPServerType.DATABASE]
        assert "artemis" in database_rule.filters
        assert "sophia" in database_rule.filters
        assert "code_metrics" in database_rule.filters["artemis"]["schemas"]
        assert "sales_data" in database_rule.filters["sophia"]["schemas"]

    def test_load_balancing_strategies(self, router):
        """Test that load balancing strategies are properly set"""
        database_rule = router.routing_rules[MCPServerType.DATABASE]
        assert database_rule.load_balancing == "least_connections"

        filesystem_rule = router.routing_rules[MCPServerType.FILESYSTEM]
        assert filesystem_rule.load_balancing == "round_robin"

    # ==============================================================================
    # ARTEMIS-EXCLUSIVE SERVER TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_artemis_filesystem_server_exclusive_access(self, router):
        """Test that FILESYSTEM server is exclusive to Artemis"""
        # Mock health status
        router.health_status["artemis_filesystem"] = True

        # Artemis should be able to route to filesystem
        result = await router.route_request(
            MCPServerType.FILESYSTEM, MemoryDomain.ARTEMIS, {"operation": "read", "path": "/src"}
        )

        assert result is not None
        assert result == "artemis_filesystem"

        # Sophia should NOT be able to route to filesystem
        result = await router.route_request(
            MCPServerType.FILESYSTEM, MemoryDomain.SOPHIA, {"operation": "read", "path": "/src"}
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_artemis_code_analysis_server_exclusive_access(self, router):
        """Test that CODE_ANALYSIS server is exclusive to Artemis"""
        router.health_status["artemis_code_analysis"] = True

        # Artemis should be able to route
        result = await router.route_request(
            MCPServerType.CODE_ANALYSIS,
            MemoryDomain.ARTEMIS,
            {"analysis_type": "security", "target": "/src/main.py"},
        )

        assert result is not None
        assert result == "artemis_code_analysis"

        # Sophia should NOT be able to route
        result = await router.route_request(
            MCPServerType.CODE_ANALYSIS,
            MemoryDomain.SOPHIA,
            {"analysis_type": "security", "target": "/src/main.py"},
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_artemis_design_server_exclusive_access(self, router):
        """Test that DESIGN_SERVER is exclusive to Artemis"""
        router.health_status["artemis_design"] = True

        # Artemis should be able to route
        result = await router.route_request(
            MCPServerType.DESIGN_SERVER,
            MemoryDomain.ARTEMIS,
            {"document_type": "architecture", "format": "uml"},
        )

        assert result is not None
        assert result == "artemis_design"

        # Sophia should NOT be able to route
        result = await router.route_request(
            MCPServerType.DESIGN_SERVER,
            MemoryDomain.SOPHIA,
            {"document_type": "architecture", "format": "uml"},
        )

        assert result is None

    # ==============================================================================
    # SOPHIA-EXCLUSIVE SERVER TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_sophia_web_search_server_exclusive_access(self, router):
        """Test that WEB_SEARCH server is exclusive to Sophia"""
        router.health_status["sophia_web_search"] = True

        # Sophia should be able to route
        result = await router.route_request(
            MCPServerType.WEB_SEARCH,
            MemoryDomain.SOPHIA,
            {"search": "market trends", "scope": "competitors"},
        )

        assert result is not None
        assert result == "sophia_web_search"

        # Artemis should NOT be able to route
        result = await router.route_request(
            MCPServerType.WEB_SEARCH,
            MemoryDomain.ARTEMIS,
            {"search": "market trends", "scope": "competitors"},
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_sophia_business_analytics_server_exclusive_access(self, router):
        """Test that BUSINESS_ANALYTICS server is exclusive to Sophia"""
        router.health_status["sophia_analytics"] = True

        # Sophia should be able to route
        result = await router.route_request(
            MCPServerType.BUSINESS_ANALYTICS,
            MemoryDomain.SOPHIA,
            {"metrics": "revenue", "period": "Q4"},
        )

        assert result is not None
        assert result == "sophia_analytics"

        # Artemis should NOT be able to route
        result = await router.route_request(
            MCPServerType.BUSINESS_ANALYTICS,
            MemoryDomain.ARTEMIS,
            {"metrics": "revenue", "period": "Q4"},
        )

        assert result is None

    # ==============================================================================
    # SHARED SERVER ACCESS WITH FILTERING TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_shared_database_access_with_domain_filters(self, router):
        """Test that shared DATABASE server applies domain-specific filters"""
        router.health_status["shared_database"] = True

        # Artemis request should get Artemis-specific filters
        artemis_request = {"query": "SELECT * FROM code_metrics"}
        result = await router.route_request(
            MCPServerType.DATABASE, MemoryDomain.ARTEMIS, artemis_request
        )

        assert result is not None
        assert result == "shared_database"
        assert "domain_filters" in artemis_request
        assert "code_metrics" in artemis_request["domain_filters"]["schemas"]
        assert "sales_data" not in artemis_request["domain_filters"]["schemas"]

        # Sophia request should get Sophia-specific filters
        sophia_request = {"query": "SELECT * FROM sales_data"}
        result = await router.route_request(
            MCPServerType.DATABASE, MemoryDomain.SOPHIA, sophia_request
        )

        assert result is not None
        assert result == "shared_database"
        assert "domain_filters" in sophia_request
        assert "sales_data" in sophia_request["domain_filters"]["schemas"]
        assert "code_metrics" not in sophia_request["domain_filters"]["schemas"]

    @pytest.mark.asyncio
    async def test_shared_knowledge_base_access_with_domain_stores(self, router):
        """Test that KNOWLEDGE_BASE server provides domain-specific stores"""
        # Create a knowledge base server config (not in default setup)
        router.server_configs["shared_knowledge"] = MCPServerConfig(
            name="shared_knowledge",
            server_type=MCPServerType.KNOWLEDGE_BASE,
            endpoint="ws://localhost:8035/mcp",
            connection_pool=ConnectionPool(),
            health_check=HealthCheckConfig(),
            metadata={"domain": "shared"},
        )
        router.health_status["shared_knowledge"] = True

        # Artemis request
        artemis_request = {"operation": "search", "query": "best practices"}
        result = await router.route_request(
            MCPServerType.KNOWLEDGE_BASE, MemoryDomain.ARTEMIS, artemis_request
        )

        assert result is not None
        assert "domain_filters" in artemis_request
        assert "code_patterns" in artemis_request["domain_filters"]["stores"]
        assert "business_insights" not in artemis_request["domain_filters"]["stores"]

        # Sophia request
        sophia_request = {"operation": "search", "query": "market insights"}
        result = await router.route_request(
            MCPServerType.KNOWLEDGE_BASE, MemoryDomain.SOPHIA, sophia_request
        )

        assert result is not None
        assert "domain_filters" in sophia_request
        assert "business_insights" in sophia_request["domain_filters"]["stores"]
        assert "code_patterns" not in sophia_request["domain_filters"]["stores"]

    @pytest.mark.asyncio
    async def test_shared_embedding_namespace_partitioning(self, router):
        """Test that EMBEDDING server uses namespace partitioning"""
        router.health_status["shared_embedding"] = True

        # Check routing rule has namespace configuration
        embedding_rule = router.routing_rules[MCPServerType.EMBEDDING]
        assert "namespaces" in embedding_rule.filters
        assert embedding_rule.filters["namespaces"]["artemis"] == "technical_embeddings"
        assert embedding_rule.filters["namespaces"]["sophia"] == "business_embeddings"
        assert embedding_rule.filters["namespaces"]["shared"] == "common_embeddings"

        # Test Artemis routing
        artemis_request = {"text": "code snippet", "operation": "embed"}
        result = await router.route_request(
            MCPServerType.EMBEDDING, MemoryDomain.ARTEMIS, artemis_request
        )

        assert result is not None
        assert "domain_filters" in artemis_request
        assert artemis_request["domain_filters"] == "technical_embeddings"

        # Test Sophia routing
        sophia_request = {"text": "business report", "operation": "embed"}
        result = await router.route_request(
            MCPServerType.EMBEDDING, MemoryDomain.SOPHIA, sophia_request
        )

        assert result is not None
        assert "domain_filters" in sophia_request
        assert sophia_request["domain_filters"] == "business_embeddings"

    @pytest.mark.asyncio
    async def test_shared_chunking_strategy_selection(self, router):
        """Test that CHUNKING server uses domain-specific strategies"""
        router.health_status["shared_chunking"] = True

        # Check routing rule has strategy configuration
        chunking_rule = router.routing_rules[MCPServerType.CHUNKING]
        assert "strategies" in chunking_rule.filters
        assert chunking_rule.filters["strategies"]["artemis"] == "ast_based"
        assert chunking_rule.filters["strategies"]["sophia"] == "semantic_based"

        # Test Artemis gets AST-based chunking
        artemis_request = {"document": "source_code.py", "operation": "chunk"}
        result = await router.route_request(
            MCPServerType.CHUNKING, MemoryDomain.ARTEMIS, artemis_request
        )

        assert result is not None
        assert "domain_filters" in artemis_request
        assert artemis_request["domain_filters"] == "ast_based"

        # Test Sophia gets semantic-based chunking
        sophia_request = {"document": "business_report.pdf", "operation": "chunk"}
        result = await router.route_request(
            MCPServerType.CHUNKING, MemoryDomain.SOPHIA, sophia_request
        )

        assert result is not None
        assert "domain_filters" in sophia_request
        assert sophia_request["domain_filters"] == "semantic_based"

    # ==============================================================================
    # SERVER CONFIGURATION TESTS
    # ==============================================================================

    def test_server_configs_initialization(self, router):
        """Test that server configurations are properly initialized"""
        # Check Artemis servers
        assert "artemis_filesystem" in router.server_configs
        assert "artemis_code_analysis" in router.server_configs
        assert "artemis_design" in router.server_configs

        filesystem_config = router.server_configs["artemis_filesystem"]
        assert filesystem_config.server_type == MCPServerType.FILESYSTEM
        assert filesystem_config.endpoint == "ws://localhost:8010/mcp"
        assert filesystem_config.connection_pool.min_connections == 3
        assert filesystem_config.connection_pool.max_connections == 10
        assert "read" in filesystem_config.capabilities
        assert "write" in filesystem_config.capabilities
        assert filesystem_config.metadata["domain"] == "artemis"

        # Check Sophia servers
        assert "sophia_web_search" in router.server_configs
        assert "sophia_analytics" in router.server_configs

        websearch_config = router.server_configs["sophia_web_search"]
        assert websearch_config.server_type == MCPServerType.WEB_SEARCH
        assert websearch_config.connection_pool.retry_attempts == 5
        assert websearch_config.metadata["external"] is True

        # Check shared servers
        assert "shared_database" in router.server_configs
        assert "shared_indexing" in router.server_configs
        assert "shared_embedding" in router.server_configs

        database_config = router.server_configs["shared_database"]
        assert database_config.connection_pool.min_connections == 5
        assert database_config.connection_pool.idle_timeout == 600
        assert database_config.metadata["critical"] is True

    def test_health_check_configurations(self, router):
        """Test that health check configurations are properly set"""
        filesystem_config = router.server_configs["artemis_filesystem"]
        assert filesystem_config.health_check.interval_seconds == 30
        assert filesystem_config.health_check.failure_threshold == 3

        code_analysis_config = router.server_configs["artemis_code_analysis"]
        assert code_analysis_config.health_check.interval_seconds == 45
        assert code_analysis_config.health_check.timeout_seconds == 15

        websearch_config = router.server_configs["sophia_web_search"]
        assert websearch_config.health_check.failure_threshold == 5  # More tolerant for external

        database_config = router.server_configs["shared_database"]
        assert database_config.health_check.interval_seconds == 20  # More frequent for critical
        assert database_config.health_check.failure_threshold == 2

    # ==============================================================================
    # LOAD BALANCING TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_round_robin_load_balancing(self, router):
        """Test round-robin load balancing strategy"""
        # Set up multiple healthy servers of same type
        router.server_configs["artemis_filesystem_2"] = MCPServerConfig(
            name="artemis_filesystem_2",
            server_type=MCPServerType.FILESYSTEM,
            endpoint="ws://localhost:8010/mcp",
            connection_pool=ConnectionPool(),
            health_check=HealthCheckConfig(),
            metadata={"domain": "artemis"},
        )

        router.health_status["artemis_filesystem"] = True
        router.health_status["artemis_filesystem_2"] = True

        # Multiple requests should distribute (in simple implementation, always first)
        result1 = await router.route_request(
            MCPServerType.FILESYSTEM, MemoryDomain.ARTEMIS, {"operation": "read"}
        )

        assert result1 in ["artemis_filesystem", "artemis_filesystem_2"]

    @pytest.mark.asyncio
    async def test_least_connections_load_balancing(self, router):
        """Test least-connections load balancing strategy"""
        # Mock connection pools
        router.connection_pools = {
            "shared_database": {"active_connections": 5},
            "shared_database_2": {"active_connections": 2},
        }

        # Add second database server
        router.server_configs["shared_database_2"] = MCPServerConfig(
            name="shared_database_2",
            server_type=MCPServerType.DATABASE,
            endpoint="ws://localhost:8030/mcp",
            connection_pool=ConnectionPool(),
            health_check=HealthCheckConfig(),
            metadata={"domain": "shared"},
        )

        router.health_status["shared_database"] = True
        router.health_status["shared_database_2"] = True

        # Should route to server with fewer connections
        result = await router.route_request(
            MCPServerType.DATABASE, MemoryDomain.ARTEMIS, {"query": "SELECT 1"}
        )

        assert result == "shared_database_2"  # Has fewer connections

    # ==============================================================================
    # HEALTH STATUS TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_unhealthy_server_not_routed(self, router):
        """Test that unhealthy servers are not selected for routing"""
        # Set one server as unhealthy
        router.health_status["artemis_filesystem"] = False

        result = await router.route_request(
            MCPServerType.FILESYSTEM, MemoryDomain.ARTEMIS, {"operation": "read"}
        )

        assert result is None  # No healthy servers available

    @pytest.mark.asyncio
    async def test_fallback_to_healthy_server(self, router):
        """Test fallback to healthy server when primary is down"""
        # Add backup server
        router.server_configs["artemis_filesystem_backup"] = MCPServerConfig(
            name="artemis_filesystem_backup",
            server_type=MCPServerType.FILESYSTEM,
            endpoint="ws://localhost:8011/mcp",
            connection_pool=ConnectionPool(),
            health_check=HealthCheckConfig(),
            metadata={"domain": "artemis"},
        )

        # Primary unhealthy, backup healthy
        router.health_status["artemis_filesystem"] = False
        router.health_status["artemis_filesystem_backup"] = True

        result = await router.route_request(
            MCPServerType.FILESYSTEM, MemoryDomain.ARTEMIS, {"operation": "read"}
        )

        assert result == "artemis_filesystem_backup"

    # ==============================================================================
    # UTILITY METHOD TESTS
    # ==============================================================================

    def test_get_server_config(self, router):
        """Test retrieving server configuration"""
        config = router.get_server_config("artemis_filesystem")

        assert config is not None
        assert config.name == "artemis_filesystem"
        assert config.server_type == MCPServerType.FILESYSTEM

        # Non-existent server
        config = router.get_server_config("non_existent")
        assert config is None

    def test_get_servers_by_domain(self, router):
        """Test retrieving servers accessible by domain"""
        # Get Artemis servers
        artemis_servers = router.get_servers_by_domain(MemoryDomain.ARTEMIS)
        artemis_names = [s.name for s in artemis_servers]

        assert "artemis_filesystem" in artemis_names
        assert "artemis_code_analysis" in artemis_names
        assert "shared_database" in artemis_names
        assert "sophia_web_search" not in artemis_names

        # Get Sophia servers
        sophia_servers = router.get_servers_by_domain(MemoryDomain.SOPHIA)
        sophia_names = [s.name for s in sophia_servers]

        assert "sophia_web_search" in sophia_names
        assert "sophia_analytics" in sophia_names
        assert "shared_database" in sophia_names
        assert "artemis_filesystem" not in sophia_names

    def test_validate_connection_limits(self, router):
        """Test connection limit validation"""
        # Mock connection pools
        router.connection_pools = {
            "artemis_filesystem": {"active_connections": 5},
            "artemis_code_analysis": {"active_connections": 12},  # Over limit
        }

        validation = router.validate_connection_limits()

        assert validation["artemis_filesystem"] is True  # Within limits
        assert validation["artemis_code_analysis"] is False  # Over max of 10

    def test_get_routing_summary(self, router):
        """Test routing summary generation"""
        summary = router.get_routing_summary()

        assert summary["total_servers"] == len(router.server_configs)
        assert len(summary["artemis_exclusive"]) > 0
        assert len(summary["sophia_exclusive"]) > 0
        assert len(summary["shared_servers"]) > 0
        assert "health_status" in summary
        assert summary["routing_rules"] == len(router.routing_rules)

    # ==============================================================================
    # ERROR HANDLING TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_route_request_with_unknown_server_type(self, router):
        """Test routing with unknown server type"""
        result = await router.route_request(
            "UNKNOWN_TYPE", MemoryDomain.ARTEMIS, {"test": "data"}  # Invalid server type
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_route_request_logs_domain_violation(self, router):
        """Test that domain violations are logged"""
        with patch("app.mcp.router_config.logger") as mock_logger:
            result = await router.route_request(
                MCPServerType.FILESYSTEM,
                MemoryDomain.SOPHIA,  # Wrong domain!
                {"operation": "read"},
            )

            assert result is None
            mock_logger.warning.assert_called()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "SOPHIA" in warning_msg
            assert "not allowed" in warning_msg
            assert "FILESYSTEM" in warning_msg
