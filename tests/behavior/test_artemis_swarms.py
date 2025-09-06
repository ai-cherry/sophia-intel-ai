"""
Behavior tests for Artemis Swarm Patterns
Tests military coordination patterns, chain-of-command hierarchy, and tactical decision making
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.artemis.unified_factory import (
    AgentProfile,
    ArtemisUnifiedFactory,
    MilitaryUnitType,
    MissionStatus,
    MissionTemplate,
    SwarmType,
    TechnicalAgentRole,
)


class TestArtemisSwarmBehavior:
    """Test suite for Artemis swarm behavior patterns"""

    @pytest.fixture
    def factory(self):
        """Create factory with mocked memory"""
        with patch("app.artemis.unified_factory.store_memory"):
            return ArtemisUnifiedFactory()

    @pytest.fixture
    async def recon_squad(self, factory):
        """Create a reconnaissance squad"""
        with patch.object(factory, "_execute_mission_phase", new_callable=AsyncMock) as mock_phase:
            mock_phase.return_value = {"success": True, "data": "recon_data"}
            squad_id = await factory.create_military_squad("recon_battalion")
            return squad_id, factory.active_swarms[squad_id]

    @pytest.fixture
    async def strike_force(self, factory):
        """Create a strike force squad"""
        squad_id = await factory.create_military_squad("strike_force")
        return squad_id, factory.active_swarms[squad_id]

    # ==============================================================================
    # MILITARY COORDINATION PATTERN TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_military_chain_of_command_hierarchy(self, factory):
        """Test that military squads follow proper chain of command"""
        squad_id = await factory.create_military_squad("recon_battalion")
        squad = factory.active_swarms[squad_id]

        # Verify chain of command structure
        assert squad["communication_protocol"] == "RECON-NET-SECURE"

        # Check agent hierarchy
        agents = squad["agents"]
        assert len(agents) == 2

        # SCOUT-1 should be the lead
        scout_1 = next(a for a in agents if a.callsign == "SCOUT-1")
        scout_2 = next(a for a in agents if a.callsign == "SCOUT-2")

        assert scout_1.rank == "Reconnaissance Lead"
        assert scout_2.rank == "Architecture Analyst"
        assert scout_1.clearance_level > scout_2.clearance_level

    @pytest.mark.asyncio
    async def test_coordinated_mission_execution(self, factory):
        """Test coordinated execution across multiple squads"""
        with patch.object(factory, "_execute_mission_phase", new_callable=AsyncMock) as mock_phase:
            mock_phase.return_value = {
                "success": True,
                "deliverables": ["scan_complete", "analysis_done"],
            }

            # Execute full mission
            result = await factory.execute_mission(
                "operation_clean_sweep", target="/critical/system", parameters={"priority": "HIGH"}
            )

            assert result["success"] is True
            assert len(result["phases_completed"]) == 3
            assert "Reconnaissance" in result["phases_completed"]
            assert "Analysis" in result["phases_completed"]
            assert "Execution" in result["phases_completed"]

            # Verify squads were deployed in correct order
            active_mission = factory.active_missions[result["mission_id"]]
            assert "recon_battalion" in active_mission["units_deployed"]
            assert "qc_division" in active_mission["units_deployed"]
            assert "strike_force" in active_mission["units_deployed"]

    @pytest.mark.asyncio
    async def test_parallel_strike_coordination(self, factory):
        """Test parallel strike force coordination"""
        squad_id = await factory.create_military_squad("strike_force")
        squad = factory.active_swarms[squad_id]

        # Verify parallel execution configuration
        operational_params = squad["operational_parameters"]
        assert operational_params["execution_mode"] == "parallel_strike"
        assert operational_params["rollback_capability"] is True

        # Verify strike team composition
        agents = squad["agents"]
        leader = next(a for a in agents if a.callsign == "OPERATOR-LEAD")
        assert leader.clearance_level == 5  # Highest clearance for leader
        assert "Advanced code generation and refactoring" in leader.specialty

    @pytest.mark.asyncio
    async def test_mission_priority_handling(self, factory):
        """Test handling of different mission priorities"""
        # Create normal priority mission
        normal_result = await factory.execute_mission(
            "operation_clean_sweep", target="/normal/target"
        )

        # Create high priority mission
        high_priority_result = await factory.execute_mission(
            "rapid_response", target="/critical/bug"
        )

        # Rapid response should be marked as HIGH priority
        rapid_template = factory.mission_templates["rapid_response"]
        assert rapid_template.priority == "HIGH"

        # Verify rapid response is more streamlined
        assert len(high_priority_result["phases_completed"]) == 2  # Fewer phases
        assert factory.technical_metrics["missions_completed"] == 2

    @pytest.mark.asyncio
    async def test_squad_communication_protocols(self, factory):
        """Test different communication protocols for different squads"""
        recon_id = await factory.create_military_squad("recon_battalion")
        strike_id = await factory.create_military_squad("strike_force")
        qc_id = await factory.create_military_squad("qc_division")

        recon_squad = factory.active_swarms[recon_id]
        strike_squad = factory.active_swarms[strike_id]
        qc_squad = factory.active_swarms[qc_id]

        # Each squad should have unique secure communication protocol
        assert recon_squad["communication_protocol"] == "RECON-NET-SECURE"
        assert strike_squad["communication_protocol"] == "STRIKE-SECURE-OPS"
        assert qc_squad["communication_protocol"] == "QC-SECURE-CHANNEL"

        # All protocols should be different
        protocols = [
            recon_squad["communication_protocol"],
            strike_squad["communication_protocol"],
            qc_squad["communication_protocol"],
        ]
        assert len(set(protocols)) == 3

    # ==============================================================================
    # TACTICAL DECISION MAKING TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_tactical_agent_personality_influence(self, factory):
        """Test that tactical personalities influence agent behavior"""
        # Create agents with different tactical personalities
        reviewer_id = await factory.create_technical_agent("code_reviewer")
        auditor_id = await factory.create_technical_agent("security_auditor")
        optimizer_id = await factory.create_technical_agent("performance_optimizer")

        reviewer = factory.active_agents[reviewer_id]
        auditor = factory.active_agents[auditor_id]
        optimizer = factory.active_agents[optimizer_id]

        # Check tactical traits
        assert reviewer.tactical_traits["precision_level"] == "surgical"
        assert reviewer.tactical_traits["communication_style"] == "direct_tactical"

        assert auditor.tactical_traits["paranoia_level"] == "maximum"
        assert auditor.tactical_traits["threat_awareness"] == "constant"

        assert optimizer.tactical_traits["speed_obsession"] == "maximum"
        assert optimizer.tactical_traits["metrics_driven"] == "always"

    @pytest.mark.asyncio
    async def test_mission_phase_decision_flow(self, factory):
        """Test decision flow through mission phases"""
        phase_decisions = []

        async def mock_phase_execution(mission_id, phase, units):
            decision = {
                "phase": phase["name"],
                "units": list(units.keys()),
                "decision": "proceed" if phase["phase"] < 3 else "complete",
            }
            phase_decisions.append(decision)
            return {"success": True, "decision": decision["decision"]}

        with patch.object(factory, "_execute_mission_phase", side_effect=mock_phase_execution):
            result = await factory.execute_mission("operation_clean_sweep")

        # Verify decision flow
        assert len(phase_decisions) == 3
        assert phase_decisions[0]["decision"] == "proceed"
        assert phase_decisions[1]["decision"] == "proceed"
        assert phase_decisions[2]["decision"] == "complete"

    @pytest.mark.asyncio
    async def test_adaptive_tactical_response(self, factory):
        """Test adaptive response based on mission conditions"""
        # Simulate mission with changing conditions
        conditions = {"threat_level": "low", "complexity": "medium", "time_constraint": "normal"}

        squad_id = await factory.create_military_squad(
            "recon_battalion", mission_parameters=conditions
        )

        squad = factory.active_swarms[squad_id]
        assert squad["mission_parameters"]["threat_level"] == "low"

        # Update conditions to high threat
        conditions["threat_level"] = "high"

        # Create new squad with high threat conditions
        high_threat_squad_id = await factory.create_military_squad(
            "strike_force", mission_parameters=conditions
        )

        high_threat_squad = factory.active_swarms[high_threat_squad_id]
        assert high_threat_squad["mission_parameters"]["threat_level"] == "high"

        # Strike force is more appropriate for high threat
        assert high_threat_squad["unit_type"] == MilitaryUnitType.STRIKE

    @pytest.mark.asyncio
    async def test_quality_control_validation_loop(self, factory):
        """Test QC division validation in mission workflow"""
        validation_results = []

        async def mock_qc_validation(mission_id, phase, units):
            if "qc_division" in units:
                validation = {
                    "validated": True,
                    "quality_score": 0.95,
                    "issues_found": 2,
                    "issues_resolved": 2,
                }
                validation_results.append(validation)
                return {"success": True, "validation": validation}
            return {"success": True}

        with patch.object(factory, "_execute_mission_phase", side_effect=mock_qc_validation):
            result = await factory.execute_mission("operation_clean_sweep")

        # QC should have validated
        assert len(validation_results) > 0
        assert validation_results[0]["quality_score"] == 0.95
        assert validation_results[0]["issues_resolved"] == validation_results[0]["issues_found"]

    # ==============================================================================
    # SWARM COORDINATION TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_refactoring_swarm_coordination(self, factory):
        """Test refactoring swarm agent coordination"""
        swarm_config = {
            "target": "/src/legacy",
            "refactoring_type": "architectural",
            "preserve_functionality": True,
        }

        with patch.object(factory, "create_technical_agent", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = lambda t: f"agent_{t}_{uuid4().hex[:4]}"

            swarm_id = await factory.create_specialized_swarm(
                SwarmType.REFACTORING_SWARM, swarm_config
            )

        swarm = factory.specialized_swarms[swarm_id]

        # Verify swarm composition for refactoring
        assert swarm["type"] == SwarmType.REFACTORING_SWARM
        assert len(swarm["agents"]) == 2  # reviewer + optimizer
        assert swarm["config"]["preserve_functionality"] is True

        # Verify correct specialists were created
        mock_create.assert_any_call("code_reviewer")
        mock_create.assert_any_call("performance_optimizer")

    @pytest.mark.asyncio
    async def test_domain_team_specialization(self, factory):
        """Test domain-specific team creation and specialization"""
        domain_config = {
            "domain": "security",
            "focus_areas": ["vulnerability_scanning", "penetration_testing"],
            "compliance_standards": ["OWASP", "PCI-DSS"],
        }

        with patch.object(factory, "create_technical_agent", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = lambda t: f"agent_{t}_{uuid4().hex[:4]}"

            swarm_id = await factory.create_specialized_swarm(SwarmType.DOMAIN_TEAM, domain_config)

        swarm = factory.specialized_swarms[swarm_id]

        # Security domain team should have security specialists
        assert swarm["config"]["domain"] == "security"
        mock_create.assert_any_call("security_auditor")

    @pytest.mark.asyncio
    async def test_technical_team_formation_strategies(self, factory):
        """Test different technical team formation strategies"""
        # Code analysis team
        code_team_id = await factory.create_technical_team(
            {"type": "code_analysis", "name": "Code Quality Squad"}
        )

        code_team = factory.active_swarms[code_team_id]
        assert code_team["type"] == "code_analysis"
        assert len(code_team["agents"]) == 3  # reviewer, auditor, optimizer

        # Full technical team
        full_team_id = await factory.create_technical_team(
            {"type": "full_technical", "name": "Complete Technical Force"}
        )

        full_team = factory.active_swarms[full_team_id]
        assert full_team["type"] == "full_technical"
        assert len(full_team["agents"]) == len(factory.agent_templates)

    @pytest.mark.asyncio
    async def test_swarm_status_transitions(self, factory):
        """Test swarm status transitions during mission execution"""
        squad_id = await factory.create_military_squad("recon_battalion")
        squad = factory.active_swarms[squad_id]

        # Initial status should be PENDING
        assert squad["status"] == MissionStatus.PENDING

        # Simulate mission start - status would change to ACTIVE
        squad["status"] = MissionStatus.ACTIVE
        assert squad["status"] == MissionStatus.ACTIVE

        # Simulate completion
        squad["status"] = MissionStatus.COMPLETE
        assert squad["status"] == MissionStatus.COMPLETE

    # ==============================================================================
    # CONCURRENT SWARM OPERATIONS TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_concurrent_swarm_task_limit(self, factory):
        """Test that swarms respect the 8 concurrent task limit"""
        # Fill up task slots
        for _ in range(8):
            await factory._acquire_task_slot()

        assert factory._concurrent_tasks == 8

        # Try to create a swarm - should be queued
        result = await factory.create_military_squad("recon_battalion")

        assert result.startswith("queued_")
        assert len(factory._task_queue) == 1

    @pytest.mark.asyncio
    async def test_multiple_swarm_coordination(self, factory):
        """Test coordination between multiple active swarms"""
        # Create multiple swarms
        recon_id = await factory.create_military_squad("recon_battalion")
        strike_id = await factory.create_military_squad("strike_force")
        qc_id = await factory.create_military_squad("qc_division")

        # All swarms should be active
        assert len(factory.active_swarms) == 3
        assert recon_id in factory.active_swarms
        assert strike_id in factory.active_swarms
        assert qc_id in factory.active_swarms

        # Each swarm should have unique agents
        all_agent_ids = set()
        for swarm in factory.active_swarms.values():
            for agent in swarm["agents"]:
                assert agent.id not in all_agent_ids
                all_agent_ids.add(agent.id)

    @pytest.mark.asyncio
    async def test_swarm_resource_sharing(self, factory):
        """Test resource sharing and isolation between swarms"""
        # Create two squads
        squad1_id = await factory.create_military_squad("recon_battalion")
        squad2_id = await factory.create_military_squad("strike_force")

        squad1 = factory.active_swarms[squad1_id]
        squad2 = factory.active_swarms[squad2_id]

        # Squads should have different operational parameters
        assert squad1["operational_parameters"] != squad2["operational_parameters"]

        # But share the same factory metrics
        initial_squads = factory.technical_metrics["squads_deployed"]
        assert initial_squads == 2

    # ==============================================================================
    # MISSION SUCCESS CRITERIA TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_mission_success_criteria_evaluation(self, factory):
        """Test evaluation of mission success criteria"""
        template = factory.mission_templates["operation_clean_sweep"]

        # Check success criteria
        assert template.success_criteria["issues_resolved"] == ">90%"
        assert template.success_criteria["test_coverage"] == ">85%"
        assert template.success_criteria["quality_score"] == ">95%"

        # Simulate mission with results
        with patch.object(factory, "_execute_mission_phase", new_callable=AsyncMock) as mock_phase:
            mock_phase.return_value = {
                "success": True,
                "metrics": {"issues_resolved": 0.92, "test_coverage": 0.87, "quality_score": 0.96},
            }

            result = await factory.execute_mission("operation_clean_sweep")
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_rapid_response_time_constraints(self, factory):
        """Test rapid response protocol time constraints"""
        template = factory.mission_templates["rapid_response"]

        # Verify rapid response characteristics
        assert template.priority == "HIGH"
        assert template.total_duration == "7-15 minutes"
        assert len(template.phases) == 2  # Streamlined phases

        # Check critical success criteria
        assert template.success_criteria["critical_issues_fixed"] == "100%"
        assert template.success_criteria["deployment_ready"] is True

    # ==============================================================================
    # WEBSOCKET REAL-TIME UPDATES TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_mission_progress_broadcasting(self, factory):
        """Test real-time mission progress broadcasting"""
        mock_ws = MagicMock()
        mock_ws.send_json = AsyncMock()
        factory.websocket_connections.add(mock_ws)

        # Simulate mission update
        await factory._broadcast_mission_update(
            "mission_123",
            {
                "status": MissionStatus.ACTIVE,
                "current_phase": 2,
                "phases_completed": ["Reconnaissance"],
            },
        )

        # Verify broadcast was sent
        mock_ws.send_json.assert_called_once()
        sent_data = mock_ws.send_json.call_args[0][0]
        assert sent_data["type"] == "mission_update"
        assert sent_data["mission_id"] == "mission_123"
        assert sent_data["current_phase"] == 2
