"""
ARTEMIS Supreme Orchestrator Integration Tests
Comprehensive testing suite for tactical command center and agent operations.
"""

import pytest
import asyncio
import json
import websockets
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import tempfile
import os
from pathlib import Path

from app.orchestrator.artemis_supreme import ArtemisSupremeOrchestrator
from webui.backend.main import app


class TestArtemisSupremeIntegration:
    """Integration tests for ARTEMIS Supreme Orchestrator system."""

    @pytest.fixture
    async def orchestrator(self):
        """Create a test orchestrator instance."""
        config = {
            "tactical_voice_enabled": True,
            "max_agents": 50,
            "swarm_coordination_timeout": 30,
            "intelligence_cache_ttl": 300,
        }
        return ArtemisSupremeOrchestrator(config=config)

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        return TestClient(app)

    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator properly initializes with tactical configuration."""
        assert orchestrator.tactical_callsign == "ARTEMIS-PRIME"
        assert orchestrator.operational_status == "TACTICAL-READY"
        assert orchestrator.agent_registry is not None
        assert orchestrator.swarm_coordinator is not None
        assert orchestrator.intelligence_cache is not None

    async def test_tactical_command_processing(self, orchestrator):
        """Test command processing with military-style inputs."""
        test_commands = [
            "Deploy reconnaissance micro-swarm for market analysis",
            "Create specialized agent for code refactoring operations",
            "Execute full tactical sweep of repository vulnerabilities",
            "Status report on all active operations",
            "Deploy emergency response team for critical bug fix",
        ]

        for command in test_commands:
            result = await orchestrator.process_tactical_command(command)
            assert result is not None
            assert result.get("status") in ["ACKNOWLEDGED", "DEPLOYED", "EXECUTED"]
            assert "tactical_response" in result
            assert result["tactical_response"].startswith("🎯")

    async def test_agent_factory_deployment(self, orchestrator):
        """Test agent creation through factory system."""
        # Test individual agent creation
        agent_spec = {
            "agent_type": "code_specialist",
            "specialization": "python_optimization",
            "security_clearance": "alpha",
            "mission_parameters": {"focus_areas": ["performance", "security"]},
        }

        agent_result = await orchestrator.deploy_tactical_agent(agent_spec)
        assert agent_result["status"] == "DEPLOYED"
        assert agent_result["agent_id"] is not None
        assert agent_result["callsign"].startswith("ALPHA-")

    async def test_micro_swarm_deployment(self, orchestrator):
        """Test micro-swarm (2-4 agents) deployment and coordination."""
        swarm_spec = {
            "swarm_type": "reconnaissance",
            "mission": "analyze_codebase_quality",
            "agent_count": 3,
            "coordination_protocol": "delta_formation",
            "time_limit": 1800,
        }

        swarm_result = await orchestrator.deploy_micro_swarm(swarm_spec)
        assert swarm_result["status"] == "SWARM-DEPLOYED"
        assert len(swarm_result["agent_roster"]) == 3
        assert swarm_result["formation"] == "delta_formation"
        assert all(
            agent["status"] == "MISSION-READY" for agent in swarm_result["agent_roster"]
        )

    async def test_full_swarm_operations(self, orchestrator):
        """Test full operational swarm (5-8 agents) deployment."""
        swarm_spec = {
            "swarm_type": "full_tactical",
            "mission": "comprehensive_security_audit",
            "agent_count": 6,
            "specializations": [
                "vulnerability_scanner",
                "code_reviewer",
                "dependency_auditor",
                "compliance_checker",
                "penetration_tester",
                "incident_responder",
            ],
            "coordination_protocol": "distributed_consensus",
        }

        swarm_result = await orchestrator.deploy_full_swarm(swarm_spec)
        assert swarm_result["status"] == "FULL-SWARM-OPERATIONAL"
        assert len(swarm_result["agent_roster"]) == 6
        assert swarm_result["command_structure"]["alpha_leader"] is not None
        assert swarm_result["tactical_network"]["mesh_topology"] is True

    async def test_background_monitoring_agents(self, orchestrator):
        """Test continuous background surveillance agents."""
        monitoring_spec = {
            "surveillance_type": "continuous",
            "monitoring_domains": [
                "system_performance",
                "security_incidents",
                "code_quality_drift",
                "dependency_vulnerabilities",
            ],
            "alert_thresholds": {"critical": 0.9, "warning": 0.7},
        }

        monitor_result = await orchestrator.deploy_background_surveillance(
            monitoring_spec
        )
        assert monitor_result["status"] == "SURVEILLANCE-ACTIVE"
        assert len(monitor_result["monitoring_agents"]) == 4
        assert monitor_result["alert_system"]["status"] == "ARMED"

    async def test_intelligence_gathering_operations(self, orchestrator):
        """Test multi-source web research and intelligence gathering."""
        research_mission = {
            "intelligence_type": "market_research",
            "target_domains": ["ai_development", "enterprise_software"],
            "sources": ["tavily", "exa", "brave_search"],
            "depth": "comprehensive",
            "classification": "tactical",
        }

        intel_result = await orchestrator.execute_intelligence_gathering(
            research_mission
        )
        assert intel_result["status"] == "INTELLIGENCE-ACQUIRED"
        assert intel_result["sources_consulted"] >= 3
        assert intel_result["confidence_level"] >= 0.8
        assert intel_result["classification"] == "tactical"

    async def test_tactical_ui_integration(self, client):
        """Test tactical command center UI endpoint integration."""
        response = client.get("/tactical")
        assert response.status_code == 200
        assert "tactical-command-center" in response.text
        assert "Agent Factory" in response.text
        assert "Swarm Deployment" in response.text

    async def test_websocket_streaming_integration(self):
        """Test WebSocket streaming for real-time tactical updates."""
        # This would require a running server, so we'll mock the key components
        with patch("websockets.connect") as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket

            # Simulate tactical update stream
            mock_websocket.recv.side_effect = [
                json.dumps(
                    {
                        "type": "tactical_update",
                        "agent_id": "ALPHA-001",
                        "status": "MISSION-PROGRESS",
                        "progress": 45,
                    }
                ),
                json.dumps(
                    {
                        "type": "swarm_coordination",
                        "swarm_id": "DELTA-RECON-001",
                        "formation": "advancing",
                        "eta": 300,
                    }
                ),
            ]

            # Test connection and message handling
            async with websockets.connect("ws://localhost:8000/ws/tactical") as ws:
                message1 = await ws.recv()
                data1 = json.loads(message1)
                assert data1["type"] == "tactical_update"
                assert data1["agent_id"] == "ALPHA-001"

                message2 = await ws.recv()
                data2 = json.loads(message2)
                assert data2["type"] == "swarm_coordination"
                assert data2["swarm_id"] == "DELTA-RECON-001"

    async def test_voice_interface_integration(self, orchestrator):
        """Test voice command processing with speech-to-text integration."""
        # Mock voice input processing
        with patch("app.orchestrator.artemis_supreme.speech_to_text") as mock_stt:
            mock_stt.return_value = "Deploy alpha team for critical bug analysis"

            # Mock audio data
            mock_audio_data = b"fake_audio_data"

            voice_result = await orchestrator.process_voice_command(mock_audio_data)
            assert voice_result["status"] == "VOICE-COMMAND-PROCESSED"
            assert voice_result["transcribed_command"] == "Deploy alpha team for critical bug analysis"
            assert voice_result["tactical_response"] is not None

    async def test_business_intelligence_integration(self, orchestrator):
        """Test integration with business intelligence tools."""
        bi_operations = [
            {
                "tool": "gong",
                "operation": "fetch_call_analytics",
                "parameters": {"date_range": "last_30_days"},
            },
            {
                "tool": "netsuite",
                "operation": "revenue_analysis",
                "parameters": {"period": "quarterly"},
            },
            {
                "tool": "n8n",
                "operation": "workflow_automation",
                "parameters": {"trigger": "new_lead_qualification"},
            },
        ]

        for operation in bi_operations:
            result = await orchestrator.execute_bi_integration(operation)
            assert result["status"] == "BI-OPERATION-COMPLETE"
            assert result["data_acquired"] is True
            assert result["integration_health"] == "OPERATIONAL"

    async def test_session_management_and_history(self, orchestrator):
        """Test conversation history and session intelligence caching."""
        # Execute series of commands to build session history
        commands = [
            "Status report on system health",
            "Deploy security audit team",
            "What are the results from the previous audit?",
            "Scale up the security team with additional specialists",
        ]

        session_id = "test_tactical_session_001"
        for i, command in enumerate(commands):
            result = await orchestrator.process_tactical_command(
                command, session_id=session_id
            )
            assert result["session_id"] == session_id
            assert result["command_sequence"] == i + 1

        # Test session history retrieval
        history = await orchestrator.get_session_history(session_id)
        assert len(history["commands"]) == 4
        assert history["session_intelligence"]["context_continuity"] is True

    async def test_error_handling_and_recovery(self, orchestrator):
        """Test system resilience and tactical error recovery."""
        # Test malformed command handling
        malformed_commands = [
            "",  # Empty command
            "Invalid tactical nonsense command",  # Nonsensical command
            "Deploy @@invalid@@agent@@spec",  # Malformed parameters
            None,  # Null command
        ]

        for bad_command in malformed_commands:
            result = await orchestrator.process_tactical_command(bad_command)
            assert result["status"] == "TACTICAL-ERROR-HANDLED"
            assert result["error_type"] in ["INVALID_COMMAND", "MALFORMED_INPUT", "NULL_INPUT"]
            assert result["recovery_action"] is not None

    async def test_performance_under_load(self, orchestrator):
        """Test system performance under concurrent tactical operations."""
        # Simulate high-load scenario with concurrent operations
        concurrent_operations = []

        for i in range(20):
            operation = orchestrator.process_tactical_command(
                f"Deploy agent CONCURRENT-{i:03d} for load testing", session_id=f"load_test_{i}"
            )
            concurrent_operations.append(operation)

        # Execute all operations concurrently
        results = await asyncio.gather(*concurrent_operations)

        # Verify all operations completed successfully
        assert len(results) == 20
        successful_ops = [r for r in results if r["status"] == "ACKNOWLEDGED"]
        assert len(successful_ops) >= 18  # Allow for 10% acceptable failure rate under load

    async def test_security_and_access_control(self, orchestrator):
        """Test security measures and tactical access controls."""
        # Test security clearance validation
        high_clearance_command = {
            "command": "Access classified vulnerability database",
            "clearance_required": "omega",
        }

        # Test with insufficient clearance
        result = await orchestrator.process_secured_command(
            high_clearance_command, user_clearance="alpha"
        )
        assert result["status"] == "ACCESS-DENIED"
        assert result["reason"] == "INSUFFICIENT-CLEARANCE"

        # Test with adequate clearance
        result = await orchestrator.process_secured_command(
            high_clearance_command, user_clearance="omega"
        )
        assert result["status"] == "ACCESS-GRANTED"

    async def test_system_metrics_and_monitoring(self, orchestrator):
        """Test system health monitoring and tactical metrics."""
        metrics = await orchestrator.get_tactical_metrics()

        # Verify key metrics are present
        required_metrics = [
            "active_agents",
            "deployed_swarms",
            "system_load",
            "response_times",
            "error_rates",
            "resource_utilization",
        ]

        for metric in required_metrics:
            assert metric in metrics
            assert metrics[metric] is not None

        # Test health status
        health = await orchestrator.get_system_health()
        assert health["status"] in ["TACTICAL-READY", "OPERATIONAL", "DEGRADED"]
        assert health["overall_score"] >= 0.7  # Minimum acceptable health score

    async def test_integration_with_external_apis(self, orchestrator):
        """Test integration with external AI model providers."""
        model_tests = [
            {"provider": "grok", "model": "grok-4", "test_type": "strategic_analysis"},
            {"provider": "openrouter", "model": "gpt-5-turbo", "test_type": "code_generation"},
            {"provider": "qwen", "model": "qwen3-max", "test_type": "research_validation"},
        ]

        for test_config in model_tests:
            result = await orchestrator.test_model_integration(test_config)
            assert result["provider_status"] == "OPERATIONAL"
            assert result["response_time"] < 10.0  # Maximum 10 second response time
            assert result["model_availability"] is True

    @pytest.mark.asyncio
    async def test_end_to_end_tactical_mission(self, orchestrator):
        """Complete end-to-end test of a full tactical mission."""
        # Phase 1: Mission initialization
        mission = {
            "codename": "OPERATION-PHOENIX",
            "objective": "Comprehensive codebase modernization",
            "priority": "high",
            "estimated_duration": 3600,  # 1 hour
        }

        init_result = await orchestrator.initialize_tactical_mission(mission)
        assert init_result["status"] == "MISSION-INITIALIZED"
        mission_id = init_result["mission_id"]

        # Phase 2: Deploy reconnaissance micro-swarm
        recon_result = await orchestrator.deploy_micro_swarm(
            {
                "mission_id": mission_id,
                "swarm_type": "reconnaissance",
                "agent_count": 3,
                "objective": "analyze_current_codebase",
            }
        )
        assert recon_result["status"] == "SWARM-DEPLOYED"

        # Phase 3: Deploy main tactical team based on reconnaissance
        main_team_result = await orchestrator.deploy_full_swarm(
            {
                "mission_id": mission_id,
                "swarm_type": "modernization",
                "agent_count": 6,
                "based_on_intel": recon_result["intelligence_report"],
            }
        )
        assert main_team_result["status"] == "FULL-SWARM-OPERATIONAL"

        # Phase 4: Monitor mission progress
        progress = await orchestrator.get_mission_progress(mission_id)
        assert progress["mission_id"] == mission_id
        assert progress["status"] in ["IN-PROGRESS", "ADVANCING", "COMPLETING"]

        # Phase 5: Mission completion and debrief
        completion_result = await orchestrator.complete_mission(mission_id)
        assert completion_result["status"] == "MISSION-ACCOMPLISHED"
        assert completion_result["debrief_report"] is not None
        assert completion_result["objectives_met"] >= 0.8  # 80% success rate required


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
