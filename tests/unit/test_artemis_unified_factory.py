"""
Unit tests for Artemis Unified Factory
Tests agent creation, military swarm configurations, concurrent task limits, and domain capabilities
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket

from app.artemis.unified_factory import (
    ArtemisUnifiedFactory,
    MilitaryUnitType,
    MissionStatus,
    SwarmType,
    TechnicalAgentRole,
    TechnicalPersonality,
)


class TestArtemisUnifiedFactory:
    """Test suite for Artemis Unified Factory"""

    @pytest.fixture
    def factory(self):
        """Create a fresh factory instance for each test"""
        return ArtemisUnifiedFactory()

    @pytest.fixture
    def mock_memory(self):
        """Mock memory system calls"""
        with (
            patch("app.artemis.unified_factory.store_memory") as mock_store,
            patch("app.artemis.unified_factory.search_memory") as mock_search,
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
        assert config.domain == "ARTEMIS"
        assert "code_generation" in config.capabilities
        assert "tactical_operations" in config.capabilities
        assert config.tactical_mode_enabled is True
        assert config.enable_memory_integration is True
        assert config.enable_websocket_updates is True

    def test_factory_initialization(self, factory):
        """Test factory initialization with all components"""
        # Check agent templates
        assert "code_reviewer" in factory.agent_templates
        assert "security_auditor" in factory.agent_templates
        assert "performance_optimizer" in factory.agent_templates

        # Check military units
        assert "recon_battalion" in factory.military_units
        assert "strike_force" in factory.military_units
        assert "qc_division" in factory.military_units

        # Check mission templates
        assert "operation_clean_sweep" in factory.mission_templates
        assert "rapid_response" in factory.mission_templates

        # Check metrics initialization
        assert factory.technical_metrics["security_scans"] == 0
        assert factory.technical_metrics["missions_completed"] == 0
        assert factory._concurrent_tasks == 0

    # ==============================================================================
    # AGENT CREATION TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_create_technical_agent_with_tactical_personality(self, factory, mock_memory):
        """Test creation of technical agent with tactical personality traits"""
        agent_id = await factory.create_technical_agent("code_reviewer")

        assert agent_id.startswith("artemis_code_reviewer_")
        assert agent_id in factory.active_agents

        agent = factory.active_agents[agent_id]
        assert agent.name == "Code Review Specialist"
        assert agent.role == TechnicalAgentRole.CODE_REVIEWER
        assert agent.personality == TechnicalPersonality.CRITICAL_ANALYTICAL
        assert agent.clearance_level == 4
        assert "static_code_analysis" in agent.capabilities
        assert agent.tactical_traits["precision_level"] == "surgical"
        assert agent.tactical_traits["communication_style"] == "direct_tactical"

    @pytest.mark.asyncio
    async def test_create_technical_agent_with_custom_config(self, factory, mock_memory):
        """Test creating technical agent with custom configuration"""
        custom_config = {"clearance_level": 5, "mission_count": 10, "success_rate": 0.95}

        agent_id = await factory.create_technical_agent("security_auditor", custom_config)
        agent = factory.active_agents[agent_id]

        assert agent.clearance_level == 5
        assert agent.mission_count == 10
        assert agent.success_rate == 0.95
        assert agent.personality == TechnicalPersonality.SECURITY_PARANOID
        assert agent.tactical_traits["paranoia_level"] == "maximum"

    @pytest.mark.asyncio
    async def test_create_technical_agent_invalid_template(self, factory):
        """Test error handling for invalid agent template"""
        with pytest.raises(ValueError, match="Technical template 'invalid_template' not found"):
            await factory.create_technical_agent("invalid_template")

    # ==============================================================================
    # MILITARY SWARM TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_create_military_squad_configuration(self, factory, mock_memory):
        """Test military squad creation with proper configuration"""
        squad_id = await factory.create_military_squad("recon_battalion")

        assert squad_id.startswith("squad_recon_battalion_")
        assert squad_id in factory.active_swarms

        squad = factory.active_swarms[squad_id]
        assert squad["designation"] == "1st Reconnaissance Battalion 'Pathfinders'"
        assert squad["unit_type"] == MilitaryUnitType.RECON
        assert squad["motto"] == "First to Know, First to Strike"
        assert squad["status"] == MissionStatus.PENDING
        assert len(squad["agents"]) == 2  # Scout-1 and Scout-2

        # Check individual agents
        for agent in squad["agents"]:
            assert agent.id in factory.active_agents
            assert agent.callsign in ["SCOUT-1", "SCOUT-2"]
            assert agent.clearance_level >= 3

    @pytest.mark.asyncio
    async def test_create_strike_force_squad(self, factory, mock_memory):
        """Test strike force squad creation"""
        mission_params = {"target": "critical_vulnerability", "priority": "HIGH"}

        squad_id = await factory.create_military_squad("strike_force", mission_params)
        squad = factory.active_swarms[squad_id]

        assert squad["unit_type"] == MilitaryUnitType.STRIKE
        assert squad["mission_parameters"]["target"] == "critical_vulnerability"
        assert squad["operational_parameters"]["execution_mode"] == "parallel_strike"
        assert squad["operational_parameters"]["code_quality_threshold"] == 0.9

        # Verify squad metrics updated
        assert factory.technical_metrics["squads_deployed"] == 1

    @pytest.mark.asyncio
    async def test_create_military_squad_invalid_unit(self, factory):
        """Test error handling for invalid military unit"""
        with pytest.raises(ValueError, match="Military unit 'invalid_unit' not found"):
            await factory.create_military_squad("invalid_unit")

    # ==============================================================================
    # CONCURRENT TASK LIMIT TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_concurrent_task_limit_enforcement(self, factory, mock_memory):
        """Test that 8 concurrent task limit is properly enforced"""
        # Create 8 tasks to reach the limit
        tasks = []
        for i in range(8):
            acquired = await factory._acquire_task_slot()
            assert acquired is True
            tasks.append(i)

        assert factory._concurrent_tasks == 8

        # Try to acquire 9th slot - should fail
        acquired = await factory._acquire_task_slot()
        assert acquired is False
        assert factory._concurrent_tasks == 8

        # Release one slot
        await factory._release_task_slot()
        assert factory._concurrent_tasks == 7

        # Now should be able to acquire again
        acquired = await factory._acquire_task_slot()
        assert acquired is True
        assert factory._concurrent_tasks == 8

        # Clean up
        for _ in range(8):
            await factory._release_task_slot()
        assert factory._concurrent_tasks == 0

    @pytest.mark.asyncio
    async def test_task_queueing_when_at_capacity(self, factory, mock_memory):
        """Test task queueing when concurrent limit is reached"""
        # Fill up all slots
        for _ in range(8):
            await factory._acquire_task_slot()

        # Queue a task
        task = {"type": "create_agent", "template": "code_reviewer"}

        task_id = await factory.queue_task(task)

        assert task_id.startswith("queued_")
        assert len(factory._task_queue) == 1
        assert factory._task_queue[0]["id"] == task_id
        assert "queued_at" in factory._task_queue[0]

    @pytest.mark.asyncio
    async def test_task_status_reporting(self, factory):
        """Test task status reporting"""
        # Acquire some slots
        for _ in range(5):
            await factory._acquire_task_slot()

        # Queue some tasks
        for _ in range(3):
            await factory.queue_task({"type": "test"})

        status = factory.get_task_status()

        assert status["active_tasks"] == 5
        assert status["max_concurrent"] == 8
        assert status["queued_tasks"] == 3
        assert status["capacity_available"] is True
        assert status["utilization"] == 5 / 8

    # ==============================================================================
    # SPECIALIZED SWARM TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_create_refactoring_swarm(self, factory, mock_memory):
        """Test creation of refactoring swarm"""
        swarm_config = {
            "target_directory": "/src",
            "refactoring_type": "performance",
            "metrics_focus": ["speed", "memory"],
        }

        # Mock the create_technical_agent to avoid infinite recursion
        with patch.object(factory, "create_technical_agent", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = lambda template: f"mock_{template}_id"

            swarm_id = await factory.create_specialized_swarm(
                SwarmType.REFACTORING_SWARM, swarm_config
            )

        assert swarm_id.startswith("refactoring_swarm_")
        assert swarm_id in factory.specialized_swarms

        swarm = factory.specialized_swarms[swarm_id]
        assert swarm["type"] == SwarmType.REFACTORING_SWARM
        assert swarm["config"]["target_directory"] == "/src"
        assert swarm["status"] == "ready"

        # Verify agents were created
        assert mock_create.call_count == 2
        mock_create.assert_any_call("code_reviewer")
        mock_create.assert_any_call("performance_optimizer")

    @pytest.mark.asyncio
    async def test_create_domain_team(self, factory, mock_memory):
        """Test creation of domain-specific team"""
        swarm_config = {
            "domain": "security",
            "focus_areas": ["vulnerability_scanning", "threat_detection"],
        }

        with patch.object(factory, "create_technical_agent", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = lambda template: f"mock_{template}_id"

            swarm_id = await factory.create_specialized_swarm(SwarmType.DOMAIN_TEAM, swarm_config)

        assert swarm_id.startswith("domain_team_")
        swarm = factory.specialized_swarms[swarm_id]
        assert swarm["config"]["domain"] == "security"

    # ==============================================================================
    # MISSION EXECUTION TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_execute_mission_operation_clean_sweep(self, factory, mock_memory):
        """Test execution of Operation Clean Sweep mission"""
        with (
            patch.object(factory, "create_military_squad", new_callable=AsyncMock) as mock_squad,
            patch.object(factory, "_execute_mission_phase", new_callable=AsyncMock) as mock_phase,
            patch.object(
                factory, "_broadcast_mission_update", new_callable=AsyncMock
            ) as mock_broadcast,
        ):

            mock_squad.side_effect = lambda unit, params: f"squad_{unit}_test"
            mock_phase.return_value = {
                "phase": 1,
                "name": "Reconnaissance",
                "success": True,
                "deliverables": ["scan_report"],
            }

            result = await factory.execute_mission(
                "operation_clean_sweep", target="/src", parameters={"depth": "comprehensive"}
            )

        assert result["success"] is True
        assert result["mission_name"] == "Operation Clean Sweep"
        assert result["mission_id"].startswith("mission_operation_clean_sweep_")
        assert "Reconnaissance" in result["phases_completed"]
        assert "Analysis" in result["phases_completed"]
        assert "Execution" in result["phases_completed"]

        # Verify squads were created for each unit
        assert mock_squad.call_count == 3

        # Verify metrics updated
        assert factory.technical_metrics["missions_completed"] == 1

    @pytest.mark.asyncio
    async def test_execute_mission_rapid_response(self, factory, mock_memory):
        """Test rapid response mission execution"""
        with (
            patch.object(factory, "create_military_squad", new_callable=AsyncMock) as mock_squad,
            patch.object(factory, "_execute_mission_phase", new_callable=AsyncMock) as mock_phase,
        ):

            mock_squad.side_effect = lambda unit, params: f"squad_{unit}_test"
            mock_phase.return_value = {"success": True}

            result = await factory.execute_mission(
                "rapid_response", target="critical_bug", parameters={"severity": "CRITICAL"}
            )

        template = factory.mission_templates["rapid_response"]
        assert template.priority == "HIGH"
        assert len(result["phases_completed"]) == 2  # Quick Scan and Strike

    @pytest.mark.asyncio
    async def test_execute_mission_invalid_template(self, factory):
        """Test error handling for invalid mission template"""
        result = await factory.execute_mission("invalid_mission")

        assert result["success"] is False
        assert "error" in result
        assert "invalid_mission" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_mission_with_queue(self, factory, mock_memory):
        """Test mission execution when at capacity"""
        # Fill up all task slots
        for _ in range(8):
            await factory._acquire_task_slot()

        result = await factory.execute_mission("rapid_response")

        assert result["success"] is False
        assert result["reason"] == "Task limit reached"
        assert result["queued"] is True
        assert "queue_id" in result

    # ==============================================================================
    # TEAM MANAGEMENT TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_create_technical_team(self, factory, mock_memory):
        """Test technical team creation"""
        with patch.object(factory, "create_technical_agent", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = lambda template: f"agent_{template}_id"

            team_config = {"name": "Elite Code Review Team", "type": "code_analysis"}

            team_id = await factory.create_technical_team(team_config)

        assert team_id.startswith("team_")
        assert team_id in factory.active_swarms

        team = factory.active_swarms[team_id]
        assert team["name"] == "Elite Code Review Team"
        assert team["type"] == "code_analysis"
        assert team["status"] == "operational"
        assert team["tactical_readiness"] == "maximum"
        assert len(team["agents"]) == 3  # code_reviewer, security_auditor, performance_optimizer

    @pytest.mark.asyncio
    async def test_create_full_technical_team(self, factory, mock_memory):
        """Test creation of full technical team with all templates"""
        with patch.object(factory, "create_technical_agent", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = lambda template: f"agent_{template}_id"

            team_config = {"type": "full_technical"}

            team_id = await factory.create_technical_team(team_config)
            team = factory.active_swarms[team_id]

        # Should create all available agent templates
        assert len(team["agents"]) == len(factory.agent_templates)

    # ==============================================================================
    # WEBSOCKET TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_websocket_connection_management(self, factory):
        """Test WebSocket connection management"""
        mock_websocket = MagicMock(spec=WebSocket)

        await factory.add_websocket_connection(mock_websocket)
        assert mock_websocket in factory.websocket_connections
        assert len(factory.websocket_connections) == 1

        await factory.remove_websocket_connection(mock_websocket)
        assert mock_websocket not in factory.websocket_connections
        assert len(factory.websocket_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_mission_update(self, factory):
        """Test broadcasting mission updates via WebSocket"""
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws2 = MagicMock(spec=WebSocket)
        mock_ws1.send_json = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        factory.websocket_connections.add(mock_ws1)
        factory.websocket_connections.add(mock_ws2)

        mission_data = {
            "status": MissionStatus.ACTIVE,
            "current_phase": 2,
            "phases_completed": ["Reconnaissance"],
        }

        await factory._broadcast_mission_update("mission_123", mission_data)

        # Both websockets should receive the update
        assert mock_ws1.send_json.called
        assert mock_ws2.send_json.called

        # Check update structure
        call_args = mock_ws1.send_json.call_args[0][0]
        assert call_args["type"] == "mission_update"
        assert call_args["mission_id"] == "mission_123"
        assert call_args["status"] == MissionStatus.ACTIVE

    # ==============================================================================
    # QUERY AND STATUS TESTS
    # ==============================================================================

    def test_get_technical_templates(self, factory):
        """Test retrieving technical templates"""
        templates = factory.get_technical_templates()

        assert "code_reviewer" in templates
        assert templates["code_reviewer"]["name"] == "Code Review Specialist"
        assert templates["code_reviewer"]["personality"] == TechnicalPersonality.CRITICAL_ANALYTICAL
        assert "static_code_analysis" in templates["code_reviewer"]["capabilities"]

    def test_get_military_units(self, factory):
        """Test retrieving military unit configurations"""
        units = factory.get_military_units()

        assert "recon_battalion" in units
        assert (
            units["recon_battalion"]["designation"] == "1st Reconnaissance Battalion 'Pathfinders'"
        )
        assert units["recon_battalion"]["unit_type"] == "reconnaissance"
        assert units["recon_battalion"]["squad_size"] == 2

    def test_get_mission_templates(self, factory):
        """Test retrieving mission templates"""
        missions = factory.get_mission_templates()

        assert "operation_clean_sweep" in missions
        assert missions["operation_clean_sweep"]["name"] == "Operation Clean Sweep"
        assert missions["operation_clean_sweep"]["phases"] == 3
        assert missions["rapid_response"]["priority"] == "HIGH"

    def test_get_factory_metrics(self, factory):
        """Test factory metrics reporting"""
        metrics = factory.get_factory_metrics()

        assert "technical_metrics" in metrics
        assert "task_status" in metrics
        assert metrics["domain"] == "ARTEMIS"
        assert "code_generation" in metrics["capabilities"]
        assert metrics["tactical_readiness"] == "maximum"
        assert metrics["total_operations"] == 0  # No operations yet

    @pytest.mark.asyncio
    async def test_list_active_agents(self, factory, mock_memory):
        """Test listing active agents"""
        # Create some agents
        await factory.create_technical_agent("code_reviewer")
        await factory.create_technical_agent("security_auditor")

        agents = factory.list_active_agents()

        assert len(agents) == 2
        assert all("id" in agent for agent in agents)
        assert all("name" in agent for agent in agents)
        assert all("clearance_level" in agent for agent in agents)

    @pytest.mark.asyncio
    async def test_list_active_swarms(self, factory, mock_memory):
        """Test listing active swarms"""
        # Create a squad
        await factory.create_military_squad("recon_battalion")

        swarms = factory.list_active_swarms()

        assert len(swarms) == 1
        assert swarms[0]["type"] == "military_squad"
        assert swarms[0]["agents_count"] == 2
        assert swarms[0]["status"] == MissionStatus.PENDING

    # ==============================================================================
    # EDGE CASES AND ERROR HANDLING
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_concurrent_agent_creation(self, factory, mock_memory):
        """Test concurrent creation of multiple agents"""
        tasks = []
        for i in range(5):
            task = asyncio.create_task(factory.create_technical_agent("code_reviewer"))
            tasks.append(task)

        agent_ids = await asyncio.gather(*tasks)

        assert len(agent_ids) == 5
        assert len(set(agent_ids)) == 5  # All unique IDs
        assert len(factory.active_agents) == 5

    @pytest.mark.asyncio
    async def test_memory_integration_failure_handling(self, factory):
        """Test graceful handling of memory system failures"""
        with patch("app.artemis.unified_factory.store_memory") as mock_store:
            mock_store.side_effect = Exception("Memory system unavailable")

            # Should still create agent even if memory fails
            agent_id = await factory.create_technical_agent("code_reviewer")

            assert agent_id.startswith("artemis_code_reviewer_")
            assert agent_id in factory.active_agents

    @pytest.mark.asyncio
    async def test_websocket_disconnection_handling(self, factory):
        """Test handling of disconnected WebSocket clients"""
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock(side_effect=Exception("Connection closed"))

        factory.websocket_connections.add(mock_ws)

        mission_data = {"status": MissionStatus.ACTIVE, "current_phase": 1, "phases_completed": []}

        await factory._broadcast_mission_update("mission_123", mission_data)

        # Disconnected websocket should be removed
        assert mock_ws not in factory.websocket_connections

    def test_domain_specific_capabilities(self, factory):
        """Test that Artemis domain-specific capabilities are properly configured"""
        config = factory.config

        # Verify Artemis-specific capabilities
        artemis_capabilities = [
            "code_generation",
            "code_review",
            "refactoring",
            "security_scanning",
            "architecture_design",
            "tactical_operations",
            "military_coordination",
        ]

        for capability in artemis_capabilities:
            assert capability in config.capabilities

        # Verify no Sophia capabilities
        sophia_capabilities = ["business_intelligence", "sales_analytics", "customer_insights"]

        for capability in sophia_capabilities:
            assert capability not in config.capabilities
