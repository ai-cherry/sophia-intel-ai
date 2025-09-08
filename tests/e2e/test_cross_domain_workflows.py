"""
End-to-End tests for Cross-Domain Workflows
Tests complete workflows that span both domains, domain boundary enforcement in practice,
and shared service access patterns
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.artemis.unified_factory import ArtemisUnifiedFactory
from app.core.domain_enforcer import (
    DomainEnforcer,
    OperationType,
    UserRole,
    request_cross_domain_access,
    validate_domain_request,
)
from app.mcp.connection_manager import MCPConnectionManager
from app.mcp.router_config import MCPRouterConfiguration, MCPServerType, MemoryDomain
from app.memory.unified_memory_router import MemoryDomain as MemDomain
from app.sophia.unified_factory import SophiaUnifiedFactory


class TestCrossDomainWorkflows:
    """Test suite for workflows spanning both Artemis and Sophia domains"""

    @pytest.fixture
    def artemis_factory(self):
        """Create Artemis factory"""
        with patch("app.artemis.unified_factory.store_memory"):
            return ArtemisUnifiedFactory()

    @pytest.fixture
    def sophia_factory(self):
        """Create Sophia factory"""
        with patch("app.sophia.unified_factory.store_memory"):
            return SophiaUnifiedFactory()

    @pytest.fixture
    def domain_enforcer(self):
        """Create domain enforcer"""
        return DomainEnforcer()

    @pytest.fixture
    def mcp_router(self):
        """Create MCP router"""
        with patch("asyncio.create_task"):
            return MCPRouterConfiguration()

    @pytest.fixture
    def connection_manager(self):
        """Create connection manager"""
        with patch("asyncio.create_task"):
            return MCPConnectionManager()

    # ==============================================================================
    # COMPLETE WORKFLOW TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_technical_to_business_insight_workflow(
        self, artemis_factory, sophia_factory, domain_enforcer
    ):
        """Test workflow from technical analysis to business insights"""
        # Step 1: Artemis performs code analysis
        artemis_agent_id = await artemis_factory.create_technical_agent("code_reviewer")
        assert artemis_agent_id.startswith("artemis_code_reviewer_")

        # Step 2: Request cross-domain access for business context
        cross_domain_request = domain_enforcer.create_cross_domain_request(
            source_domain=MemDomain.ARTEMIS,
            target_domain=MemDomain.SOPHIA,
            operation=OperationType.BUSINESS_ANALYSIS,
            requestor_id=artemis_agent_id,
            requestor_role=UserRole.DEVELOPER,
            justification="Need business context for API design decisions",
            data={"analysis_type": "api_impact", "code_metrics": {"complexity": 8}},
        )

        assert cross_domain_request.approved is False

        # Step 3: Admin approves cross-domain request
        approval_success = domain_enforcer.approve_cross_domain_request(
            request_id=cross_domain_request.id,
            approver_id="admin_user",
            approver_role=UserRole.ADMIN,
        )

        assert approval_success is True
        assert domain_enforcer.check_cross_domain_approval(cross_domain_request.id)

        # Step 4: Sophia provides business context
        sophia_agent_id = await sophia_factory.create_business_agent(
            "sales_pipeline_analyst"
        )

        # Step 5: Execute business analysis with technical context
        business_result = await sophia_factory.execute_business_task(
            sophia_agent_id,
            "Analyze API impact on sales pipeline",
            context={"code_metrics": {"complexity": 8}, "api_changes": True},
        )

        assert business_result["success"] is True
        assert business_result["type"] == "agent"
        assert "Pipeline Analysis" in business_result["kpis_tracked"]

    @pytest.mark.asyncio
    async def test_business_requirement_to_technical_implementation_workflow(
        self, artemis_factory, sophia_factory, domain_enforcer
    ):
        """Test workflow from business requirements to technical implementation"""
        # Step 1: Sophia generates business requirements
        sophia_team_id = await sophia_factory.create_business_team("sales_intelligence")

        business_requirements = {
            "feature": "real_time_analytics",
            "revenue_impact": 500000,
            "customer_priority": "high",
            "timeline": "Q1_2025",
        }

        # Step 2: Execute business analysis
        business_result = await sophia_factory.execute_business_task(
            sophia_team_id,
            "Define technical requirements for real-time analytics",
            context=business_requirements,
        )

        assert business_result["success"] is True

        # Step 3: Request cross-domain for technical implementation
        cross_domain_request = domain_enforcer.create_cross_domain_request(
            source_domain=MemDomain.SOPHIA,
            target_domain=MemDomain.ARTEMIS,
            operation=OperationType.ARCHITECTURE_DESIGN,
            requestor_id=sophia_team_id,
            requestor_role=UserRole.BUSINESS_ANALYST,
            justification="Need technical architecture for business feature",
            data=business_requirements,
        )

        # Step 4: Admin approves
        domain_enforcer.approve_cross_domain_request(
            cross_domain_request.id, "admin_user", UserRole.ADMIN
        )

        # Step 5: Artemis implements technical solution
        with patch.object(
            artemis_factory, "_execute_mission_phase", new_callable=AsyncMock
        ) as mock_phase:
            mock_phase.return_value = {
                "success": True,
                "deliverables": ["architecture_design", "implementation_plan"],
            }

            technical_result = await artemis_factory.execute_mission(
                "rapid_response",
                target="real_time_analytics_feature",
                parameters=business_requirements,
            )

        assert technical_result["success"] is True
        assert technical_result["mission_name"] == "Rapid Response Protocol"

    @pytest.mark.asyncio
    async def test_mythology_wisdom_to_tactical_execution_workflow(
        self, artemis_factory, sophia_factory
    ):
        """Test workflow from mythology-based wisdom to tactical execution"""
        # Step 1: Mythology council provides strategic wisdom
        council_id = await sophia_factory.create_business_team("mythology_council")

        wisdom_result = await sophia_factory.execute_business_task(
            council_id,
            "Divine strategic guidance for system architecture",
            context={"scale": "enterprise", "timeline": "5_years"},
        )

        assert wisdom_result["success"] is True
        assert wisdom_result["team_strategy"] == "debate"

        # Step 2: Convert wisdom to tactical operations
        with patch.object(
            artemis_factory, "_execute_mission_phase", new_callable=AsyncMock
        ) as mock_phase:
            mock_phase.return_value = {
                "success": True,
                "tactical_plan": "phased_implementation",
            }

            tactical_result = await artemis_factory.execute_mission(
                "operation_clean_sweep",
                target="/enterprise/architecture",
                parameters={"wisdom_guidance": "divine_strategy"},
            )

        assert tactical_result["success"] is True
        assert len(tactical_result["phases_completed"]) == 3

    # ==============================================================================
    # DOMAIN BOUNDARY ENFORCEMENT TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_domain_boundary_enforcement_in_workflow(
        self, artemis_factory, sophia_factory, domain_enforcer
    ):
        """Test that domain boundaries are enforced during workflows"""
        # Artemis agent tries to access Sophia operation without approval
        artemis_agent_id = await artemis_factory.create_technical_agent(
            "security_auditor"
        )

        # Attempt direct access to Sophia domain - should fail
        validation_result = validate_domain_request(
            user_id=artemis_agent_id,
            user_role=UserRole.DEVELOPER,
            target_domain=MemDomain.SOPHIA,
            operation=OperationType.SALES_ANALYTICS,  # Sophia-only operation
            resource_path="/sales/data",
        )

        assert validation_result.allowed is False
        assert (
            "Operation sales_analytics not allowed in SOPHIA domain"
            in validation_result.reason
        )

        # Sophia agent tries to access Artemis operation without approval
        sophia_agent_id = await sophia_factory.create_business_agent(
            "revenue_forecaster"
        )

        validation_result = validate_domain_request(
            user_id=sophia_agent_id,
            user_role=UserRole.BUSINESS_ANALYST,
            target_domain=MemDomain.ARTEMIS,
            operation=OperationType.CODE_GENERATION,  # Artemis-only operation
            resource_path="/src/main.py",
        )

        assert validation_result.allowed is False
        assert "Insufficient access level" in validation_result.reason

    @pytest.mark.asyncio
    async def test_approved_cross_domain_access_workflow(self, domain_enforcer):
        """Test workflow with approved cross-domain access"""
        # Create and approve cross-domain request
        request = request_cross_domain_access(
            source=MemDomain.ARTEMIS,
            target=MemDomain.SOPHIA,
            operation=OperationType.BUSINESS_ANALYSIS,
            user_id="dev_user",
            user_role=UserRole.DEVELOPER,
            justification="Need market data for feature prioritization",
        )

        # Initially not approved
        assert not domain_enforcer.check_cross_domain_approval(request.id)

        # Admin approves
        success = domain_enforcer.approve_cross_domain_request(
            request.id, "admin_user", UserRole.ADMIN
        )

        assert success is True
        assert domain_enforcer.check_cross_domain_approval(request.id)

        # Now developer can access with approved request
        approved_request = domain_enforcer.approved_cross_domain_requests[request.id]
        assert approved_request.approved is True
        assert approved_request.approver_id == "admin_user"

    # ==============================================================================
    # SHARED SERVICE ACCESS TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_shared_database_access_from_both_domains(self, mcp_router):
        """Test that both domains can access shared database with proper filters"""
        # Mock health status
        mcp_router.health_status["shared_database"] = True

        # Artemis accesses database
        artemis_request = {"query": "SELECT * FROM code_metrics"}
        artemis_server = await mcp_router.route_request(
            MCPServerType.DATABASE, MemoryDomain.ARTEMIS, artemis_request
        )

        assert artemis_server == "shared_database"
        assert "domain_filters" in artemis_request
        assert "code_metrics" in artemis_request["domain_filters"]["schemas"]

        # Sophia accesses database
        sophia_request = {"query": "SELECT * FROM revenue_data"}
        sophia_server = await mcp_router.route_request(
            MCPServerType.DATABASE, MemoryDomain.SOPHIA, sophia_request
        )

        assert sophia_server == "shared_database"
        assert "domain_filters" in sophia_request
        assert "sales_data" in sophia_request["domain_filters"]["schemas"]

    @pytest.mark.asyncio
    async def test_shared_embedding_service_workflow(self, mcp_router):
        """Test workflow using shared embedding service with namespace isolation"""
        mcp_router.health_status["shared_embedding"] = True

        # Artemis embeds technical documentation
        artemis_request = {
            "text": "async def process_data():",
            "operation": "embed",
            "context": "code_documentation",
        }

        artemis_result = await mcp_router.route_request(
            MCPServerType.EMBEDDING, MemoryDomain.ARTEMIS, artemis_request
        )

        assert artemis_result == "shared_embedding"
        assert artemis_request["domain_filters"] == "technical_embeddings"

        # Sophia embeds business reports
        sophia_request = {
            "text": "Q4 revenue exceeded targets by 15%",
            "operation": "embed",
            "context": "business_report",
        }

        sophia_result = await mcp_router.route_request(
            MCPServerType.EMBEDDING, MemoryDomain.SOPHIA, sophia_request
        )

        assert sophia_result == "shared_embedding"
        assert sophia_request["domain_filters"] == "business_embeddings"

    @pytest.mark.asyncio
    async def test_shared_indexing_with_partitioning(self, mcp_router):
        """Test shared indexing service with domain-based partitioning"""
        mcp_router.health_status["shared_indexing"] = True

        # Both domains can access indexing
        for domain in [MemoryDomain.ARTEMIS, MemoryDomain.SOPHIA]:
            request = {
                "operation": "index",
                "documents": ["doc1", "doc2"],
                "domain": domain.value,
            }

            result = await mcp_router.route_request(
                MCPServerType.INDEXING, domain, request
            )

            assert result == "shared_indexing"
            assert "domain_filters" in request

    # ==============================================================================
    # COMPLEX MULTI-STAGE WORKFLOW TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_complete_feature_development_workflow(
        self, artemis_factory, sophia_factory, domain_enforcer, mcp_router
    ):
        """Test complete feature development workflow from business to deployment"""
        workflow_steps = []

        # Stage 1: Business identifies opportunity
        sophia_team = await sophia_factory.create_business_team("sales_intelligence")
        workflow_steps.append(("business_identification", sophia_team))

        business_analysis = await sophia_factory.execute_business_task(
            sophia_team,
            "Identify high-value feature opportunities",
            context={"market": "enterprise", "revenue_target": 1000000},
        )

        assert business_analysis["success"] is True
        workflow_steps.append(("business_analysis_complete", business_analysis))

        # Stage 2: Strategic planning with mythology council
        council_id = await sophia_factory.create_business_team("mythology_council")

        strategic_plan = await sophia_factory.execute_business_task(
            council_id,
            "Divine wisdom for feature strategy",
            context={"opportunity": "real_time_analytics"},
        )

        assert strategic_plan["success"] is True
        workflow_steps.append(("strategic_planning_complete", strategic_plan))

        # Stage 3: Cross-domain approval for technical design
        cross_domain = domain_enforcer.create_cross_domain_request(
            source_domain=MemDomain.SOPHIA,
            target_domain=MemDomain.ARTEMIS,
            operation=OperationType.ARCHITECTURE_DESIGN,
            requestor_id=sophia_team,
            requestor_role=UserRole.BUSINESS_ANALYST,
            justification="Technical implementation of strategic feature",
            data={"feature": "real_time_analytics", "priority": "high"},
        )

        domain_enforcer.approve_cross_domain_request(
            cross_domain.id, "admin_user", UserRole.ADMIN
        )

        workflow_steps.append(("cross_domain_approved", cross_domain.id))

        # Stage 4: Technical implementation
        with patch.object(
            artemis_factory, "_execute_mission_phase", new_callable=AsyncMock
        ) as mock_phase:
            mock_phase.return_value = {"success": True, "implementation": "complete"}

            technical_impl = await artemis_factory.execute_mission(
                "operation_clean_sweep", target="/features/real_time_analytics"
            )

        assert technical_impl["success"] is True
        workflow_steps.append(("technical_implementation_complete", technical_impl))

        # Stage 5: Access shared services for deployment
        mcp_router.health_status["shared_database"] = True

        deployment_request = {"operation": "deploy", "feature": "real_time_analytics"}
        db_server = await mcp_router.route_request(
            MCPServerType.DATABASE, MemoryDomain.ARTEMIS, deployment_request
        )

        assert db_server == "shared_database"
        workflow_steps.append(("deployment_complete", db_server))

        # Verify complete workflow
        assert len(workflow_steps) == 6
        assert workflow_steps[0][0] == "business_identification"
        assert workflow_steps[-1][0] == "deployment_complete"

    @pytest.mark.asyncio
    async def test_incident_response_workflow(
        self, artemis_factory, sophia_factory, connection_manager
    ):
        """Test incident response workflow spanning both domains"""
        # Stage 1: Technical detection by Artemis
        security_agent = await artemis_factory.create_technical_agent(
            "security_auditor"
        )

        # Stage 2: Rapid response mission
        with patch.object(
            artemis_factory, "_execute_mission_phase", new_callable=AsyncMock
        ) as mock_phase:
            mock_phase.return_value = {
                "success": True,
                "threat_level": "high",
                "business_impact": "potential_data_breach",
            }

            incident_response = await artemis_factory.execute_mission(
                "rapid_response",
                target="/security/incident",
                parameters={"severity": "CRITICAL"},
            )

        assert incident_response["success"] is True

        # Stage 3: Business impact assessment by Sophia
        cs_manager = await sophia_factory.create_business_agent(
            "client_success_manager"
        )

        business_impact = await sophia_factory.execute_business_task(
            cs_manager,
            "Assess customer impact from security incident",
            context={"incident_type": "potential_data_breach", "severity": "high"},
        )

        assert business_impact["success"] is True
        assert "Customer Health Score" in business_impact["kpis_tracked"]

        # Stage 4: Connection manager handles resilient communications
        mock_connection = MagicMock()
        mock_connection.server_name = "shared_database"

        connection_manager.pools["shared_database"].acquire = AsyncMock(
            return_value=mock_connection
        )

        # Get connection with resilience
        conn = await connection_manager.get_connection("shared_database")
        assert conn is not None

        # Stage 5: Update both technical and business systems
        await connection_manager.release_connection(conn)

    # ==============================================================================
    # ERROR HANDLING AND ROLLBACK TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_workflow_rollback_on_domain_violation(
        self, artemis_factory, domain_enforcer
    ):
        """Test workflow rollback when domain violation occurs"""
        # Start workflow
        agent_id = await artemis_factory.create_technical_agent("code_reviewer")

        # Attempt unauthorized cross-domain access
        validation = validate_domain_request(
            user_id=agent_id,
            user_role=UserRole.DEVELOPER,
            target_domain=MemDomain.SOPHIA,
            operation=OperationType.REVENUE_FORECASTING,  # Not allowed
            resource_path="/financial/data",
        )

        assert validation.allowed is False

        # Check violation was logged
        audit_logs = domain_enforcer.get_audit_logs(allowed=False)
        assert len(audit_logs) > 0

        # Verify violation statistics
        stats = domain_enforcer.get_validation_statistics()
        assert stats["violations_detected"] > 0

    @pytest.mark.asyncio
    async def test_workflow_recovery_from_service_failure(self, connection_manager):
        """Test workflow recovery when shared service fails"""
        # Simulate service failure
        connection_manager.health_status["shared_database"] = False

        # Attempt to get connection - should fail
        with pytest.raises(Exception) as exc_info:
            await connection_manager.get_connection("shared_database")

        assert "shared_database is unhealthy" in str(exc_info.value)

        # Service recovers
        connection_manager.health_status["shared_database"] = True

        # Mock successful connection
        mock_connection = MagicMock()
        mock_connection.server_name = "shared_database"
        connection_manager.pools["shared_database"].acquire = AsyncMock(
            return_value=mock_connection
        )

        # Should now succeed
        conn = await connection_manager.get_connection("shared_database")
        assert conn is not None
