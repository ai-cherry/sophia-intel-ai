"""
Unit tests for Sophia Unified Factory
Tests business agent creation, mythology swarm patterns, KPI tracking, and wisdom-based reasoning
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import WebSocket
from app.sophia.unified_factory import (
    BusinessAgentProfile,
    BusinessAgentRole,
    BusinessDomain,
    BusinessPersonality,
    MemoryDomain,
    MythologyArchetype,
    SophiaUnifiedFactory,
    SwarmType,
)
class TestSophiaUnifiedFactory:
    """Test suite for Sophia Unified Factory"""
    @pytest.fixture
    def factory(self):
        """Create a fresh factory instance for each test"""
        return SophiaUnifiedFactory()
    @pytest.fixture
    def mock_memory(self):
        """Mock memory system calls"""
        with (
            patch("app.sophia.unified_factory.store_memory") as mock_store,
            patch("app.sophia.unified_factory.search_memory") as mock_search,
        ):
            mock_store.return_value = asyncio.Future()
            mock_store.return_value.set_result(True)
            mock_search.return_value = asyncio.Future()
            mock_search.return_value.set_result([])
            yield mock_store, mock_search
    # ==============================================================================
    # CONFIGURATION TESTS
    # ==============================================================================
    def test_unified_config_initialization(self, factory):
        """Test that unified configuration is properly initialized"""
        config = factory.config
        assert config.max_concurrent_tasks == 8
        assert config.domain == MemoryDomain.SOPHIA
        assert "business_intelligence" in config.capabilities
        assert "mythology_wisdom" in config.capabilities
        assert "okr_tracking" in config.capabilities
        assert config.enable_memory_integration is True
        assert config.enable_mythology_agents is True
        assert config.enable_kpi_tracking is True
    def test_factory_initialization(self, factory):
        """Test factory initialization with all components"""
        # Check business templates
        assert "sales_pipeline_analyst" in factory.business_templates
        assert "revenue_forecaster" in factory.business_templates
        assert "client_success_manager" in factory.business_templates
        assert "market_research_specialist" in factory.business_templates
        assert "competitive_intelligence" in factory.business_templates
        # Check mythology agents
        assert "hermes" in factory.mythology_agents
        assert "asclepius" in factory.mythology_agents
        assert "athena" in factory.mythology_agents
        assert "odin" in factory.mythology_agents
        assert "minerva" in factory.mythology_agents
        # Check team templates
        assert "sales_intelligence" in factory.business_teams
        assert "client_success" in factory.business_teams
        assert "mythology_council" in factory.business_teams
        assert "business_intelligence" in factory.business_teams
        # Check OKR tracker initialization
        assert factory.okr_tracker.target_revenue_per_employee == 500000.0
        assert factory.okr_tracker.total_revenue == 0.0
        assert factory.okr_tracker.employee_count == 0
    # ==============================================================================
    # BUSINESS AGENT CREATION TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_create_business_agent_with_personality(self, factory, mock_memory):
        """Test creation of business agent with personality traits"""
        agent_id = await factory.create_business_agent("sales_pipeline_analyst")
        assert agent_id.startswith("sophia_sales_pipeline_analyst_")
        assert agent_id in factory.active_agents
        agent = factory.active_agents[agent_id]
        assert agent.name == "Sales Pipeline Analyst"
        assert agent.role == BusinessAgentRole.SALES_ANALYST
        assert agent.personality == BusinessPersonality.ANALYTICAL
        assert agent.domain == BusinessDomain.SALES_INTELLIGENCE
        assert "Pipeline Analysis" in agent.capabilities
        assert "Pipeline Velocity" in agent.kpis
        assert agent.temperature == 0.3
    @pytest.mark.asyncio
    async def test_create_revenue_forecaster(self, factory, mock_memory):
        """Test creation of revenue forecaster with strategic personality"""
        agent_id = await factory.create_business_agent("revenue_forecaster")
        agent = factory.active_agents[agent_id]
        assert agent.role == BusinessAgentRole.REVENUE_FORECASTER
        assert agent.personality == BusinessPersonality.STRATEGIC
        assert agent.domain == BusinessDomain.REVENUE_OPERATIONS
        assert "Financial Modeling" in agent.capabilities
        assert "Forecast Accuracy" in agent.kpis
        assert agent.model == "anthropic/claude-3-5-sonnet-20241022"
    @pytest.mark.asyncio
    async def test_create_business_agent_with_custom_config(self, factory, mock_memory):
        """Test creating business agent with custom configuration"""
        custom_config = {
            "temperature": 0.7,
            "kpis": ["custom_kpi_1", "custom_kpi_2"],
            "capabilities": ["custom_capability"],
        }
        agent_id = await factory.create_business_agent(
            "client_success_manager", custom_config
        )
        agent = factory.active_agents[agent_id]
        assert agent.temperature == 0.7
        assert "custom_kpi_1" in agent.kpis
        assert "custom_kpi_2" in agent.kpis
        assert "custom_capability" in agent.capabilities
        assert agent.personality == BusinessPersonality.RELATIONSHIP_FOCUSED
    @pytest.mark.asyncio
    async def test_create_business_agent_invalid_template(self, factory):
        """Test error handling for invalid agent template"""
        with pytest.raises(
            ValueError, match="Agent template 'invalid_template' not found"
        ):
            await factory.create_business_agent("invalid_template")
    # ==============================================================================
    # MYTHOLOGY AGENT TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_create_mythology_agent_hermes(self, factory, mock_memory):
        """Test creation of Hermes mythology agent"""
        agent_id = await factory.create_mythology_agent(MythologyArchetype.HERMES)
        assert agent_id.startswith("sophia_hermes_")
        assert agent_id in factory.active_agents
        agent = factory.active_agents[agent_id]
        assert agent.name == "Hermes - Divine Messenger & Market Intelligence"
        assert agent.archetype == MythologyArchetype.HERMES
        assert agent.personality == BusinessPersonality.WISDOM_BASED
        assert agent.domain == BusinessDomain.DIVINE_WISDOM
        assert "market_intelligence" in agent.capabilities
        assert agent.wisdom_traits["speed"] == "divine"
        assert agent.wisdom_traits["insight"] == "penetrating"
        assert "market_analysis" in agent.specialized_prompts
    @pytest.mark.asyncio
    async def test_create_mythology_agent_athena(self, factory, mock_memory):
        """Test creation of Athena mythology agent for strategic wisdom"""
        agent_id = await factory.create_mythology_agent(MythologyArchetype.ATHENA)
        agent = factory.active_agents[agent_id]
        assert agent.archetype == MythologyArchetype.ATHENA
        assert "strategic_planning" in agent.capabilities
        assert "wisdom_based_decisions" in agent.capabilities
        assert agent.wisdom_traits["wisdom"] == "divine"
        assert agent.wisdom_traits["strategy"] == "infallible"
        assert agent.temperature == 0.1  # Very low for strategic precision
    @pytest.mark.asyncio
    async def test_create_mythology_agent_odin(self, factory, mock_memory):
        """Test creation of Odin visionary agent"""
        agent_id = await factory.create_mythology_agent(MythologyArchetype.ODIN)
        agent = factory.active_agents[agent_id]
        assert agent.archetype == MythologyArchetype.ODIN
        assert "high_level_strategy" in agent.capabilities
        assert "sacrifice_analysis" in agent.capabilities
        assert agent.wisdom_traits["vision"] == "all-seeing"
        assert agent.wisdom_traits["knowledge"] == "infinite"
    @pytest.mark.asyncio
    async def test_create_mythology_agent_with_custom_config(
        self, factory, mock_memory
    ):
        """Test creating mythology agent with custom configuration"""
        custom_config = {
            "temperature": 0.5,
            "wisdom_traits": {"custom_trait": "enhanced"},
        }
        agent_id = await factory.create_mythology_agent(
            MythologyArchetype.MINERVA, custom_config
        )
        agent = factory.active_agents[agent_id]
        assert agent.temperature == 0.5
        assert agent.wisdom_traits["custom_trait"] == "enhanced"
        assert (
            agent.wisdom_traits["analysis"] == "systematic"
        )  # Original trait preserved
    # ==============================================================================
    # BUSINESS TEAM TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_create_sales_intelligence_team(self, factory, mock_memory):
        """Test creation of sales intelligence team"""
        team_id = await factory.create_business_team("sales_intelligence")
        assert team_id.startswith("team_sales_intelligence_")
        assert team_id in factory.active_teams
        team = factory.active_teams[team_id]
        assert team["name"] == "Sales Intelligence Team"
        assert team["team_type"] == SwarmType.SALES_INTELLIGENCE
        assert team["strategy"] == "balanced"
        assert "revenue_growth" in team["okr_focus"]
        assert "pipeline_velocity" in team["okr_focus"]
        assert len(team["agents"]) == 3
        # Verify agents were created
        for agent in team["agents"]:
            assert agent.id in factory.active_agents
    @pytest.mark.asyncio
    async def test_create_mythology_council(self, factory, mock_memory):
        """Test creation of mythology council for strategic wisdom"""
        team_id = await factory.create_business_team("mythology_council")
        team = factory.active_teams[team_id]
        assert team["name"] == "Divine Strategic Council"
        assert team["team_type"] == SwarmType.MYTHOLOGY_COUNCIL
        assert team["strategy"] == "debate"
        assert team["consensus_threshold"] == 0.88
        assert team["enable_debate"] is True
        assert "strategic_alignment" in team["okr_focus"]
        assert "wisdom_based_decisions" in team["okr_focus"]
        assert len(team["agents"]) == 3  # Athena, Odin, Minerva
    @pytest.mark.asyncio
    async def test_create_client_success_team(self, factory, mock_memory):
        """Test creation of client success team"""
        team_id = await factory.create_business_team("client_success")
        team = factory.active_teams[team_id]
        assert team["team_type"] == SwarmType.CUSTOMER_SUCCESS
        assert team["strategy"] == "consensus"
        assert team["consensus_threshold"] == 0.9
        assert "net_revenue_retention" in team["okr_focus"]
        assert "customer_health" in team["okr_focus"]
        assert len(team["agents"]) == 2
    @pytest.mark.asyncio
    async def test_create_team_with_custom_config(self, factory, mock_memory):
        """Test creating team with custom configuration"""
        custom_config = {
            "strategy": "sequential",
            "consensus_threshold": 0.95,
            "enable_debate": False,
        }
        team_id = await factory.create_business_team(
            "business_intelligence", custom_config
        )
        team = factory.active_teams[team_id]
        assert team["strategy"] == "sequential"
        assert team["consensus_threshold"] == 0.95
        assert team["enable_debate"] is False
    @pytest.mark.asyncio
    async def test_create_team_invalid_template(self, factory):
        """Test error handling for invalid team template"""
        with pytest.raises(ValueError, match="Team template 'invalid_team' not found"):
            await factory.create_business_team("invalid_team")
    # ==============================================================================
    # ANALYTICAL SWARM TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_create_strategic_planning_swarm(self, factory, mock_memory):
        """Test creation of strategic planning swarm with mythology agents"""
        swarm_config = {"focus": "Q1 2025 Strategy", "timeframe": "quarterly"}
        with patch.object(
            factory, "create_mythology_agent", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = lambda archetype: f"mock_{archetype.value}_id"
            swarm_id = await factory.create_analytical_swarm(
                SwarmType.STRATEGIC_PLANNING, swarm_config
            )
        assert swarm_id.startswith("strategic_planning_")
        assert swarm_id in factory.analytical_swarms
        swarm = factory.analytical_swarms[swarm_id]
        assert swarm["type"] == SwarmType.STRATEGIC_PLANNING
        assert swarm["config"]["focus"] == "Q1 2025 Strategy"
        assert swarm["status"] == "ready"
        assert "okr_metrics" in swarm
        # Verify mythology agents were created
        assert mock_create.call_count == 2
        mock_create.assert_any_call(MythologyArchetype.ATHENA)
        mock_create.assert_any_call(MythologyArchetype.ODIN)
    @pytest.mark.asyncio
    async def test_create_market_research_swarm(self, factory, mock_memory):
        """Test creation of market research swarm"""
        swarm_config = {
            "market": "enterprise_saas",
            "competitors": ["competitor_a", "competitor_b"],
        }
        with patch.object(
            factory, "create_business_agent", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = lambda template: f"mock_{template}_id"
            swarm_id = await factory.create_analytical_swarm(
                SwarmType.MARKET_RESEARCH, swarm_config
            )
        assert swarm_id.startswith("market_research_")
        swarm = factory.analytical_swarms[swarm_id]
        assert swarm["config"]["market"] == "enterprise_saas"
        # Verify correct agents were created
        assert mock_create.call_count == 2
        mock_create.assert_any_call("market_research_specialist")
        mock_create.assert_any_call("competitive_intelligence")
    # ==============================================================================
    # KPI AND OKR TRACKING TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_calculate_okr_metrics(self, factory):
        """Test OKR metrics calculation and tracking"""
        financial_data = {
            "total_revenue": 10000000.0,
            "employee_count": 25,
            "previous_revenue_per_employee": 350000.0,
        }
        result = await factory.calculate_okr_metrics(financial_data)
        assert result["current_metrics"]["total_revenue"] == 10000000.0
        assert result["current_metrics"]["employee_count"] == 25
        assert result["current_metrics"]["revenue_per_employee"] == 400000.0
        assert result["current_metrics"]["target_revenue_per_employee"] == 500000.0
        # Calculate growth rate: (400000 - 350000) / 350000 = 0.1428...
        assert abs(result["current_metrics"]["growth_rate"] - 0.1428) < 0.01
        # Efficiency score: 400000 / 500000 = 0.8
        assert result["current_metrics"]["efficiency_score"] == 0.8
        assert "last_updated" in result
    @pytest.mark.asyncio
    async def test_calculate_okr_metrics_with_zero_employees(self, factory):
        """Test OKR calculation handles zero employees gracefully"""
        financial_data = {"total_revenue": 1000000.0, "employee_count": 0}
        result = await factory.calculate_okr_metrics(financial_data)
        assert result["current_metrics"]["revenue_per_employee"] == 0.0
        assert result["current_metrics"]["efficiency_score"] == 0.0
    @pytest.mark.asyncio
    async def test_okr_metrics_tracking_over_time(self, factory):
        """Test that OKR metrics are properly tracked over time"""
        # First update
        financial_data1 = {"total_revenue": 5000000.0, "employee_count": 15}
        await factory.calculate_okr_metrics(financial_data1)
        assert factory.okr_tracker.total_revenue == 5000000.0
        assert factory.okr_tracker.revenue_per_employee == 333333.33  # Approximately
        # Second update
        financial_data2 = {
            "total_revenue": 7500000.0,
            "employee_count": 18,
            "previous_revenue_per_employee": 333333.33,
        }
        result = await factory.calculate_okr_metrics(financial_data2)
        assert factory.okr_tracker.total_revenue == 7500000.0
        assert factory.okr_tracker.employee_count == 18
        assert factory.okr_tracker.growth_rate > 0  # Should show growth
    # ==============================================================================
    # BUSINESS TASK EXECUTION TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_execute_business_task_with_agent(self, factory, mock_memory):
        """Test executing business task with a single agent"""
        # Create an agent first
        agent_id = await factory.create_business_agent("sales_pipeline_analyst")
        task = "Analyze Q4 pipeline and identify bottlenecks"
        context = {"quarter": "Q4", "focus": "conversion_rates"}
        result = await factory.execute_business_task(agent_id, task, context)
        assert result["success"] is True
        assert result["executor"] == agent_id
        assert result["type"] == "agent"
        assert result["agent_name"] == "Sales Pipeline Analyst"
        assert result["agent_role"] == BusinessAgentRole.SALES_ANALYST
        assert "Pipeline Velocity" in result["kpis_tracked"]
        assert result["context"]["quarter"] == "Q4"
        assert "execution_time" in result
        # Verify metrics updated
        assert factory.business_metrics["analyses_completed"] == 1
    @pytest.mark.asyncio
    async def test_execute_business_task_with_mythology_agent(
        self, factory, mock_memory
    ):
        """Test executing task with mythology agent shows wisdom traits"""
        agent_id = await factory.create_mythology_agent(MythologyArchetype.ATHENA)
        task = "Develop strategic plan for market expansion"
        result = await factory.execute_business_task(agent_id, task)
        assert result["success"] is True
        assert "divine_wisdom" in result
        assert result["divine_wisdom"]["wisdom"] == "divine"
        assert result["divine_wisdom"]["strategy"] == "infallible"
    @pytest.mark.asyncio
    async def test_execute_business_task_with_team(self, factory, mock_memory):
        """Test executing business task with a team"""
        team_id = await factory.create_business_team("sales_intelligence")
        task = "Comprehensive sales analysis for board presentation"
        result = await factory.execute_business_task(team_id, task)
        assert result["success"] is True
        assert result["type"] == "team"
        assert result["team_name"] == "Sales Intelligence Team"
        assert result["team_strategy"] == "balanced"
        assert "revenue_growth" in result["okr_focus"]
        assert len(result["agents_involved"]) == 3
    @pytest.mark.asyncio
    async def test_execute_task_invalid_executor(self, factory):
        """Test error handling for invalid executor ID"""
        result = await factory.execute_business_task("invalid_id", "task")
        assert result["success"] is False
        assert "Agent or team 'invalid_id' not found" in result["error"]
    @pytest.mark.asyncio
    async def test_execute_task_at_capacity(self, factory):
        """Test task execution when at capacity"""
        # Fill up all task slots
        for _ in range(8):
            await factory._acquire_task_slot()
        result = await factory.execute_business_task("any_id", "task")
        assert result["success"] is False
        assert result["reason"] == "Task limit reached"
        assert result["queued"] is True
        assert "queue_id" in result
    # ==============================================================================
    # CONCURRENT TASK MANAGEMENT TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_concurrent_task_limit_enforcement(self, factory):
        """Test that 8 concurrent task limit is properly enforced"""
        # Acquire all 8 slots
        for i in range(8):
            acquired = await factory._acquire_task_slot()
            assert acquired is True
        assert factory._concurrent_tasks == 8
        # Try to acquire 9th slot
        acquired = await factory._acquire_task_slot()
        assert acquired is False
        # Release and reacquire
        await factory._release_task_slot()
        assert factory._concurrent_tasks == 7
        acquired = await factory._acquire_task_slot()
        assert acquired is True
        assert factory._concurrent_tasks == 8
    @pytest.mark.asyncio
    async def test_task_queueing(self, factory):
        """Test task queueing mechanism"""
        task = {
            "type": "business_analysis",
            "executor": "test_agent",
            "task": "Analyze metrics",
        }
        task_id = await factory.queue_task(task)
        assert task_id.startswith("queued_")
        assert len(factory._task_queue) == 1
        assert factory._task_queue[0]["id"] == task_id
        assert "queued_at" in factory._task_queue[0]
    # ==============================================================================
    # PERFORMANCE METRICS TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, factory, mock_memory):
        """Test that performance metrics are properly tracked"""
        agent_id = await factory.create_business_agent("revenue_forecaster")
        # Check initial metrics
        assert agent_id in factory.performance_metrics
        metrics = factory.performance_metrics[agent_id]
        assert metrics["tasks_completed"] == 0
        assert metrics["avg_response_time"] == 0.0
        assert metrics["success_rate"] == 1.0
        # Execute a task
        await factory.execute_business_task(agent_id, "Forecast Q1 revenue")
        # Check updated metrics
        metrics = factory.performance_metrics[agent_id]
        assert metrics["tasks_completed"] == 1
        assert metrics["avg_response_time"] > 0
        assert metrics["last_used"] is not None
    def test_get_performance_metrics(self, factory):
        """Test retrieving overall performance metrics"""
        metrics = factory.get_performance_metrics()
        assert "total_agents_created" in metrics
        assert "total_teams_created" in metrics
        assert "total_tasks_completed" in metrics
        assert "average_response_time" in metrics
        assert "agent_performance" in metrics
        assert "most_used_agents" in metrics
        assert "domain_distribution" in metrics
    @pytest.mark.asyncio
    async def test_most_used_agents_tracking(self, factory, mock_memory):
        """Test tracking of most frequently used agents"""
        # Create agents and execute tasks
        agent1_id = await factory.create_business_agent("sales_pipeline_analyst")
        agent2_id = await factory.create_business_agent("revenue_forecaster")
        # Execute more tasks with agent1
        for _ in range(3):
            await factory.execute_business_task(agent1_id, "task")
        await factory.execute_business_task(agent2_id, "task")
        metrics = factory.get_performance_metrics()
        most_used = metrics["most_used_agents"]
        assert len(most_used) > 0
        assert most_used[0]["tasks_completed"] == 3
        assert most_used[0]["name"] == "Sales Pipeline Analyst"
    # ==============================================================================
    # WEBSOCKET TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_websocket_connection_management(self, factory):
        """Test WebSocket connection management"""
        mock_websocket = MagicMock(spec=WebSocket)
        await factory.add_websocket_connection(mock_websocket)
        assert mock_websocket in factory.websocket_connections
        await factory.remove_websocket_connection(mock_websocket)
        assert mock_websocket not in factory.websocket_connections
    @pytest.mark.asyncio
    async def test_broadcast_task_update(self, factory):
        """Test broadcasting task updates via WebSocket"""
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        factory.websocket_connections.add(mock_ws)
        result = {"success": True, "executor": "test_agent", "task": "test_task"}
        await factory._broadcast_task_update(result)
        assert mock_ws.send_json.called
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "task_update"
        assert call_args["result"] == result
        assert "timestamp" in call_args
        assert "active_tasks" in call_args
    # ==============================================================================
    # QUERY AND STATUS TESTS
    # ==============================================================================
    def test_get_business_templates(self, factory):
        """Test retrieving business templates"""
        templates = factory.get_business_templates()
        assert "business_agents" in templates
        assert "mythology_agents" in templates
        # Check business agents
        assert "sales_pipeline_analyst" in templates["business_agents"]
        assert (
            templates["business_agents"]["sales_pipeline_analyst"]["personality"]
            == BusinessPersonality.ANALYTICAL
        )
        # Check mythology agents
        assert "hermes" in templates["mythology_agents"]
        assert templates["mythology_agents"]["hermes"]["archetype"] == "hermes"
        assert (
            templates["mythology_agents"]["hermes"]["wisdom_traits"]["speed"]
            == "divine"
        )
    def test_get_team_templates(self, factory):
        """Test retrieving team templates"""
        templates = factory.get_team_templates()
        assert "sales_intelligence" in templates
        assert templates["sales_intelligence"]["team_type"] == "sales_intelligence"
        assert templates["sales_intelligence"]["strategy"] == "balanced"
        assert templates["sales_intelligence"]["agents_count"] == 3
        assert "mythology_council" in templates
        assert templates["mythology_council"]["strategy"] == "debate"
    def test_get_factory_metrics(self, factory):
        """Test factory metrics reporting"""
        metrics = factory.get_factory_metrics()
        assert "business_metrics" in metrics
        assert "okr_metrics" in metrics
        assert metrics["domain"] == "SOPHIA"
        assert "business_intelligence" in metrics["capabilities"]
        assert metrics["task_status"]["max_concurrent"] == 8
        # Check OKR metrics
        assert metrics["okr_metrics"]["target_revenue_per_employee"] == 500000.0
    @pytest.mark.asyncio
    async def test_list_active_agents(self, factory, mock_memory):
        """Test listing active agents"""
        await factory.create_business_agent("sales_pipeline_analyst")
        await factory.create_mythology_agent(MythologyArchetype.HERMES)
        agents = factory.list_active_agents()
        assert len(agents) == 2
        assert any(agent["role"] == BusinessAgentRole.SALES_ANALYST for agent in agents)
        assert any(agent["archetype"] == "hermes" for agent in agents)
    @pytest.mark.asyncio
    async def test_list_active_teams(self, factory, mock_memory):
        """Test listing active teams"""
        await factory.create_business_team("sales_intelligence")
        teams = factory.list_active_teams()
        assert len(teams) == 1
        assert teams[0]["name"] == "Sales Intelligence Team"
        assert teams[0]["team_type"] == "sales_intelligence"
        assert teams[0]["agents_count"] == 3
    def test_domain_distribution(self, factory):
        """Test domain distribution tracking"""
        # Create some agents to populate domains
        factory.active_agents["agent1"] = BusinessAgentProfile(
            id="agent1",
            name="Test Agent 1",
            role="test",
            model="test",
            description="test",
            domain=BusinessDomain.SALES_INTELLIGENCE,
        )
        factory.active_agents["agent2"] = BusinessAgentProfile(
            id="agent2",
            name="Test Agent 2",
            role="test",
            model="test",
            description="test",
            domain=BusinessDomain.SALES_INTELLIGENCE,
        )
        factory.active_agents["agent3"] = BusinessAgentProfile(
            id="agent3",
            name="Test Agent 3",
            role="test",
            model="test",
            description="test",
            domain=BusinessDomain.DIVINE_WISDOM,
        )
        distribution = factory._get_domain_distribution()
        assert distribution["sales_intelligence"] == 2
        assert distribution["divine_wisdom"] == 1
    # ==============================================================================
    # EDGE CASES AND ERROR HANDLING
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_concurrent_agent_creation(self, factory, mock_memory):
        """Test concurrent creation of multiple agents"""
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                factory.create_business_agent("sales_pipeline_analyst")
            )
            tasks.append(task)
        agent_ids = await asyncio.gather(*tasks)
        assert len(agent_ids) == 5
        assert len(set(agent_ids)) == 5  # All unique
        assert len(factory.active_agents) == 5
    @pytest.mark.asyncio
    async def test_memory_integration_failure_handling(self, factory):
        """Test graceful handling of memory system failures"""
        with patch("app.sophia.unified_factory.store_memory") as mock_store:
            mock_store.side_effect = Exception("Memory system unavailable")
            # Should still create agent even if memory fails
            agent_id = await factory.create_business_agent("revenue_forecaster")
            assert agent_id.startswith("sophia_revenue_forecaster_")
            assert agent_id in factory.active_agents
    @pytest.mark.asyncio
    async def test_websocket_disconnection_handling(self, factory):
        """Test handling of disconnected WebSocket clients"""
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        factory.websocket_connections.add(mock_ws)
        result = {"success": True, "task": "test"}
        await factory._broadcast_task_update(result)
        # Disconnected websocket should be removed
        assert mock_ws not in factory.websocket_connections
    def test_domain_specific_capabilities(self, factory):
        """Test that Sophia domain-specific capabilities are properly configured"""
        config = factory.config
        # Verify Sophia-specific capabilities
        sophia_capabilities = [
            "business_intelligence",
            "sales_analytics",
            "customer_insights",
            "market_research",
            "strategic_planning",
            "mythology_wisdom",
            "okr_tracking",
        ]
        for capability in sophia_capabilities:
            assert capability in config.capabilities
        # Verify no  capabilities
        _capabilities = [
            "code_generation",
            "code_review",
            "security_scanning",
            "tactical_operations",
        ]
        for capability in _capabilities:
            assert capability not in config.capabilities
    def test_wisdom_based_reasoning_preserved(self, factory):
        """Test that wisdom-based reasoning is preserved in mythology agents"""
        for name, agent in factory.mythology_agents.items():
            assert agent.personality == BusinessPersonality.WISDOM_BASED
            assert agent.domain == BusinessDomain.DIVINE_WISDOM
            assert agent.archetype is not None
            assert len(agent.wisdom_traits) > 0
            assert len(agent.specialized_prompts) > 0
