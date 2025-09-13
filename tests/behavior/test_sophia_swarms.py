"""
Behavior tests for Sophia Swarm Patterns
Tests mythology-based coordination, wisdom accumulation, and business strategy formation
"""
import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from app.sophia.unified_factory import (
    BusinessDomain,
    BusinessPersonality,
    MythologyArchetype,
    SophiaUnifiedFactory,
    SwarmType,
)
class TestSophiaSwarmBehavior:
    """Test suite for Sophia swarm behavior patterns"""
    @pytest.fixture
    def factory(self):
        """Create factory with mocked memory"""
        with patch("app.sophia.unified_factory.store_memory"):
            return SophiaUnifiedFactory()
    @pytest.fixture
    async def mythology_council(self, factory):
        """Create a mythology council"""
        team_id = await factory.create_business_team("mythology_council")
        return team_id, factory.active_teams[team_id]
    @pytest.fixture
    async def sales_intelligence_team(self, factory):
        """Create a sales intelligence team"""
        team_id = await factory.create_business_team("sales_intelligence")
        return team_id, factory.active_teams[team_id]
    # ==============================================================================
    # MYTHOLOGY-BASED COORDINATION TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_mythology_council_divine_hierarchy(self, factory):
        """Test mythology council follows divine wisdom hierarchy"""
        team_id = await factory.create_business_team("mythology_council")
        team = factory.active_teams[team_id]
        # Verify divine council composition
        assert team["name"] == "Divine Strategic Council"
        assert team["team_type"] == SwarmType.MYTHOLOGY_COUNCIL
        assert len(team["agents"]) == 3  # Athena, Odin, Minerva
        # Check divine agents
        agent_names = [agent.name for agent in team["agents"]]
        assert any("Athena" in name for name in agent_names)
        assert any("Odin" in name for name in agent_names)
        assert any("Minerva" in name for name in agent_names)
        # Verify debate strategy for council
        assert team["strategy"] == "debate"
        assert team["enable_debate"] is True
        assert (
            team["consensus_threshold"] == 0.88
        )  # High threshold for divine consensus
    @pytest.mark.asyncio
    async def test_hermes_market_intelligence_coordination(self, factory):
        """Test Hermes agent's market intelligence gathering"""
        hermes_id = await factory.create_mythology_agent(MythologyArchetype.HERMES)
        hermes = factory.active_agents[hermes_id]
        # Verify Hermes characteristics
        assert hermes.archetype == MythologyArchetype.HERMES
        assert hermes.personality == BusinessPersonality.WISDOM_BASED
        assert hermes.domain == BusinessDomain.DIVINE_WISDOM
        # Check wisdom traits for swift intelligence
        assert hermes.wisdom_traits["speed"] == "divine"
        assert hermes.wisdom_traits["insight"] == "penetrating"
        assert hermes.wisdom_traits["communication"] == "eloquent"
        # Verify market intelligence capabilities
        assert "market_intelligence" in hermes.capabilities
        assert "competitive_analysis" in hermes.capabilities
        assert "information_synthesis" in hermes.capabilities
    @pytest.mark.asyncio
    async def test_athena_strategic_wisdom_application(self, factory):
        """Test Athena's strategic wisdom in decision making"""
        athena_id = await factory.create_mythology_agent(MythologyArchetype.ATHENA)
        athena = factory.active_agents[athena_id]
        # Verify strategic attributes
        assert athena.wisdom_traits["wisdom"] == "divine"
        assert athena.wisdom_traits["strategy"] == "infallible"
        assert athena.wisdom_traits["justice"] == "righteous"
        # Check low temperature for precision
        assert athena.temperature == 0.1  # Very low for strategic precision
        # Verify strategic capabilities
        assert "strategic_planning" in athena.capabilities
        assert "wisdom_based_decisions" in athena.capabilities
        assert "long_term_vision" in athena.capabilities
    @pytest.mark.asyncio
    async def test_odin_visionary_sacrifice_analysis(self, factory):
        """Test Odin's visionary leadership and sacrifice analysis"""
        odin_id = await factory.create_mythology_agent(MythologyArchetype.ODIN)
        odin = factory.active_agents[odin_id]
        # Verify Odin's unique traits
        assert odin.wisdom_traits["vision"] == "all-seeing"
        assert odin.wisdom_traits["sacrifice"] == "willing"
        assert odin.wisdom_traits["knowledge"] == "infinite"
        # Check sacrifice analysis capability
        assert "sacrifice_analysis" in odin.capabilities
        assert "high_level_strategy" in odin.capabilities
        assert "leadership_decisions" in odin.capabilities
    @pytest.mark.asyncio
    async def test_mythology_council_consensus_building(self, factory):
        """Test consensus building in mythology council"""
        team_id, team = await mythology_council(factory)
        # Simulate task execution with mythology council
        task = "Develop 10-year strategic vision"
        result = await factory.execute_business_task(team_id, task)
        assert result["success"] is True
        assert result["type"] == "team"
        assert result["team_strategy"] == "debate"
        # Verify all divine perspectives are involved
        assert len(result["agents_involved"]) == 3
        assert "strategic_alignment" in result["okr_focus"]
        assert "wisdom_based_decisions" in result["okr_focus"]
    # ==============================================================================
    # WISDOM ACCUMULATION TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_wisdom_accumulation_through_experience(self, factory):
        """Test that agents accumulate wisdom through task execution"""
        athena_id = await factory.create_mythology_agent(MythologyArchetype.ATHENA)
        # Track performance metrics as proxy for wisdom accumulation
        initial_metrics = factory.performance_metrics[athena_id]
        assert initial_metrics["tasks_completed"] == 0
        # Execute multiple tasks
        for i in range(3):
            await factory.execute_business_task(
                athena_id, f"Strategic analysis task {i}"
            )
        # Check wisdom accumulation (represented by metrics)
        updated_metrics = factory.performance_metrics[athena_id]
        assert updated_metrics["tasks_completed"] == 3
        assert updated_metrics["last_used"] is not None
        assert updated_metrics["avg_response_time"] > 0
    @pytest.mark.asyncio
    async def test_collective_wisdom_in_business_intelligence_swarm(self, factory):
        """Test collective wisdom gathering in business intelligence swarm"""
        team_id = await factory.create_business_team("business_intelligence")
        team = factory.active_teams[team_id]
        # Verify swarm composition includes divine wisdom
        assert team["team_type"] == SwarmType.BUSINESS_TEAM
        agent_names = [agent.name for agent in team["agents"]]
        # Should include Hermes (intelligence), Athena (strategy), Minerva (validation)
        assert any("Hermes" in name for name in agent_names)
        assert any("Athena" in name for name in agent_names)
        assert any("Minerva" in name for name in agent_names)
        # Sequential strategy for wisdom flow
        assert team["strategy"] == "sequential"
    @pytest.mark.asyncio
    async def test_asclepius_business_health_diagnosis(self, factory):
        """Test Asclepius' business health diagnostic wisdom"""
        asclepius_id = await factory.create_mythology_agent(
            MythologyArchetype.ASCLEPIUS
        )
        asclepius = factory.active_agents[asclepius_id]
        # Verify diagnostic wisdom traits
        assert asclepius.wisdom_traits["diagnosis"] == "divine"
        assert asclepius.wisdom_traits["healing"] == "comprehensive"
        assert asclepius.wisdom_traits["compassion"] == "infinite"
        # Check business health capabilities
        assert "business_diagnostics" in asclepius.capabilities
        assert "organizational_health" in asclepius.capabilities
        assert "operational_healing" in asclepius.capabilities
        # Low temperature for accurate diagnosis
        assert asclepius.temperature == 0.2
    @pytest.mark.asyncio
    async def test_minerva_systematic_validation_wisdom(self, factory):
        """Test Minerva's systematic validation and quality assurance"""
        minerva_id = await factory.create_mythology_agent(MythologyArchetype.MINERVA)
        minerva = factory.active_agents[minerva_id]
        # Verify systematic analysis traits
        assert minerva.wisdom_traits["analysis"] == "systematic"
        assert minerva.wisdom_traits["validation"] == "rigorous"
        assert minerva.wisdom_traits["creativity"] == "divine"
        # Check validation capabilities
        assert "systematic_analysis" in minerva.capabilities
        assert "strategic_validation" in minerva.capabilities
        assert "quality_assurance" in minerva.capabilities
    # ==============================================================================
    # BUSINESS STRATEGY FORMATION TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_sales_intelligence_strategy_formation(self, factory):
        """Test sales intelligence team strategy formation"""
        team_id, team = await sales_intelligence_team(factory)
        # Verify team composition for sales strategy
        assert team["team_type"] == SwarmType.SALES_INTELLIGENCE
        assert len(team["agents"]) == 3
        # Check balanced strategy for sales intelligence
        assert team["strategy"] == "balanced"
        # Verify OKR focus aligns with sales strategy
        assert "revenue_growth" in team["okr_focus"]
        assert "pipeline_velocity" in team["okr_focus"]
        assert "win_rate" in team["okr_focus"]
    @pytest.mark.asyncio
    async def test_revenue_forecasting_strategic_planning(self, factory):
        """Test revenue forecasting agent's strategic capabilities"""
        forecaster_id = await factory.create_business_agent("revenue_forecaster")
        forecaster = factory.active_agents[forecaster_id]
        # Verify strategic personality
        assert forecaster.personality == BusinessPersonality.STRATEGIC
        assert forecaster.domain == BusinessDomain.REVENUE_OPERATIONS
        # Check forecasting capabilities
        assert "Revenue Forecasting" in forecaster.capabilities
        assert "Financial Modeling" in forecaster.capabilities
        assert "Scenario Planning" in forecaster.capabilities
        assert "Growth Strategy" in forecaster.capabilities
        # Check KPIs for strategy measurement
        assert "Forecast Accuracy" in forecaster.kpis
        assert "Revenue Growth Rate" in forecaster.kpis
    @pytest.mark.asyncio
    async def test_client_success_relationship_strategy(self, factory):
        """Test client success team's relationship-focused strategy"""
        team_id = await factory.create_business_team("client_success")
        team = factory.active_teams[team_id]
        # Verify consensus strategy for client decisions
        assert team["strategy"] == "consensus"
        assert team["consensus_threshold"] == 0.9  # High threshold for client decisions
        # Check relationship-focused OKRs
        assert "net_revenue_retention" in team["okr_focus"]
        assert "customer_health" in team["okr_focus"]
        assert "expansion_revenue" in team["okr_focus"]
    @pytest.mark.asyncio
    async def test_competitive_intelligence_strategy_adaptation(self, factory):
        """Test competitive intelligence agent's strategic adaptation"""
        ci_agent_id = await factory.create_business_agent("competitive_intelligence")
        ci_agent = factory.active_agents[ci_agent_id]
        # Verify innovative personality for adaptation
        assert ci_agent.personality == BusinessPersonality.INNOVATIVE
        assert ci_agent.domain == BusinessDomain.COMPETITIVE_ANALYSIS
        # Check strategic capabilities
        assert "Competitive Monitoring" in ci_agent.capabilities
        assert "Strategic Analysis" in ci_agent.capabilities
        assert "Threat Assessment" in ci_agent.capabilities
        assert "Differentiation Strategy" in ci_agent.capabilities
        # Higher temperature for creative insights
        assert ci_agent.temperature == 0.7
    # ==============================================================================
    # OKR AND KPI TRACKING TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_okr_metrics_calculation_and_tracking(self, factory):
        """Test OKR metrics calculation and tracking"""
        financial_data = {
            "total_revenue": 15000000.0,
            "employee_count": 30,
            "previous_revenue_per_employee": 400000.0,
        }
        result = await factory.calculate_okr_metrics(financial_data)
        # Verify OKR calculations
        assert result["current_metrics"]["revenue_per_employee"] == 500000.0
        assert result["current_metrics"]["efficiency_score"] == 1.0  # At target
        assert result["current_metrics"]["growth_rate"] == 0.25  # 25% growth
        # Check analysis summary
        assert "analysis_summary" in result
        assert result["analysis_summary"]["total_analyses"] >= 0
    @pytest.mark.asyncio
    async def test_kpi_tracking_by_agent_role(self, factory):
        """Test that each agent tracks role-specific KPIs"""
        # Sales analyst KPIs
        sales_agent_id = await factory.create_business_agent("sales_pipeline_analyst")
        sales_agent = factory.active_agents[sales_agent_id]
        assert "Pipeline Velocity" in sales_agent.kpis
        assert "Conversion Rates" in sales_agent.kpis
        # Client success KPIs
        cs_agent_id = await factory.create_business_agent("client_success_manager")
        cs_agent = factory.active_agents[cs_agent_id]
        assert "Customer Health Score" in cs_agent.kpis
        assert "Net Revenue Retention" in cs_agent.kpis
        # Market research KPIs
        mr_agent_id = await factory.create_business_agent("market_research_specialist")
        mr_agent = factory.active_agents[mr_agent_id]
        assert "Market Share Analysis" in mr_agent.kpis
        assert "Research Coverage" in mr_agent.kpis
    # ==============================================================================
    # SWARM COLLABORATION PATTERNS TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_strategic_planning_swarm_collaboration(self, factory):
        """Test strategic planning swarm collaboration patterns"""
        swarm_config = {
            "planning_horizon": "3_years",
            "focus_areas": ["market_expansion", "product_innovation"],
        }
        with patch.object(
            factory, "create_mythology_agent", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = lambda arch: f"divine_{arch.value}_id"
            swarm_id = await factory.create_analytical_swarm(
                SwarmType.STRATEGIC_PLANNING, swarm_config
            )
        swarm = factory.analytical_swarms[swarm_id]
        # Verify strategic planning composition
        assert swarm["type"] == SwarmType.STRATEGIC_PLANNING
        assert len(swarm["agents"]) == 2  # Athena + Odin
        # Verify divine strategists were created
        mock_create.assert_any_call(MythologyArchetype.ATHENA)
        mock_create.assert_any_call(MythologyArchetype.ODIN)
    @pytest.mark.asyncio
    async def test_market_research_swarm_integration(self, factory):
        """Test market research swarm integration"""
        swarm_config = {
            "research_scope": "global_markets",
            "competitors": ["comp_a", "comp_b", "comp_c"],
        }
        with patch.object(
            factory, "create_business_agent", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = lambda t: f"agent_{t}_id"
            swarm_id = await factory.create_analytical_swarm(
                SwarmType.MARKET_RESEARCH, swarm_config
            )
        swarm = factory.analytical_swarms[swarm_id]
        # Verify market research composition
        assert swarm["config"]["research_scope"] == "global_markets"
        assert len(swarm["config"]["competitors"]) == 3
        # Verify specialists were created
        mock_create.assert_any_call("market_research_specialist")
        mock_create.assert_any_call("competitive_intelligence")
    @pytest.mark.asyncio
    async def test_cross_functional_team_collaboration(self, factory):
        """Test cross-functional team collaboration"""
        # Create teams with different specializations
        sales_team_id = await factory.create_business_team("sales_intelligence")
        client_team_id = await factory.create_business_team("client_success")
        # Both teams should exist and be operational
        assert sales_team_id in factory.active_teams
        assert client_team_id in factory.active_teams
        sales_team = factory.active_teams[sales_team_id]
        client_team = factory.active_teams[client_team_id]
        # Teams should have different strategies
        assert sales_team["strategy"] == "balanced"
        assert client_team["strategy"] == "consensus"
        # But share business domain focus
        assert all(
            agent.domain
            in [
                BusinessDomain.SALES_INTELLIGENCE,
                BusinessDomain.REVENUE_OPERATIONS,
                BusinessDomain.COMPETITIVE_ANALYSIS,
            ]
            for agent in sales_team["agents"]
        )
    # ==============================================================================
    # CONCURRENT OPERATIONS TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_concurrent_business_task_execution(self, factory):
        """Test concurrent execution of business tasks"""
        # Create multiple agents
        agent_ids = []
        for template in ["sales_pipeline_analyst", "revenue_forecaster"]:
            agent_id = await factory.create_business_agent(template)
            agent_ids.append(agent_id)
        # Execute tasks concurrently
        tasks = [
            factory.execute_business_task(agent_id, f"Task for {agent_id}")
            for agent_id in agent_ids
        ]
        results = await asyncio.gather(*tasks)
        # All tasks should succeed
        assert all(r["success"] for r in results)
        assert factory.business_metrics["analyses_completed"] == 2
    @pytest.mark.asyncio
    async def test_mythology_council_parallel_wisdom_gathering(self, factory):
        """Test parallel wisdom gathering by mythology council"""
        team_id, team = await mythology_council(factory)
        # Execute multiple wisdom-based tasks
        tasks = [
            "Analyze market disruption potential",
            "Evaluate strategic partnerships",
            "Assess organizational readiness",
        ]
        results = []
        for task in tasks:
            result = await factory.execute_business_task(team_id, task)
            results.append(result)
        # All should succeed with divine wisdom
        assert all(r["success"] for r in results)
        assert all(r["team_strategy"] == "debate" for r in results)
    @pytest.mark.asyncio
    async def test_swarm_task_queueing_at_capacity(self, factory):
        """Test task queueing when at concurrent limit"""
        # Fill up all task slots
        for _ in range(8):
            await factory._acquire_task_slot()
        assert factory._concurrent_tasks == 8
        # Try to create team - should be queued
        result = await factory.create_business_team("sales_intelligence")
        assert result.startswith("queued_")
        assert len(factory._task_queue) == 1
    # ==============================================================================
    # PERFORMANCE AND WISDOM METRICS TESTS
    # ==============================================================================
    @pytest.mark.asyncio
    async def test_agent_performance_tracking(self, factory):
        """Test tracking of agent performance metrics"""
        agent_id = await factory.create_business_agent("sales_pipeline_analyst")
        # Execute tasks to generate metrics
        for _ in range(3):
            await factory.execute_business_task(agent_id, "Analyze pipeline")
        # Check performance metrics
        metrics = factory.performance_metrics[agent_id]
        assert metrics["tasks_completed"] == 3
        assert metrics["avg_response_time"] > 0
        assert metrics["success_rate"] == 1.0
    @pytest.mark.asyncio
    async def test_domain_distribution_tracking(self, factory):
        """Test tracking of agent distribution across domains"""
        # Create agents across different domains
        await factory.create_business_agent(
            "sales_pipeline_analyst"
        )  # SALES_INTELLIGENCE
        await factory.create_business_agent("revenue_forecaster")  # REVENUE_OPERATIONS
        await factory.create_mythology_agent(MythologyArchetype.ATHENA)  # DIVINE_WISDOM
        distribution = factory._get_domain_distribution()
        assert BusinessDomain.SALES_INTELLIGENCE.value in distribution
        assert BusinessDomain.REVENUE_OPERATIONS.value in distribution
        assert BusinessDomain.DIVINE_WISDOM.value in distribution
    @pytest.mark.asyncio
    async def test_wisdom_based_decision_quality(self, factory):
        """Test that wisdom-based agents produce higher quality decisions"""
        # Create wisdom-based agent
        athena_id = await factory.create_mythology_agent(MythologyArchetype.ATHENA)
        # Execute strategic decision task
        result = await factory.execute_business_task(
            athena_id, "Make strategic decision on market entry"
        )
        assert result["success"] is True
        assert "divine_wisdom" in result
        assert result["divine_wisdom"]["strategy"] == "infallible"
        # Wisdom-based decision should have high confidence
        # (represented by low temperature and divine traits)
        athena = factory.active_agents[athena_id]
        assert athena.temperature == 0.1  # Very low = high confidence
