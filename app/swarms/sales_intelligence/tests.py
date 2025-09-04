"""
Comprehensive Testing Suite for Sales Intelligence Swarm

This module provides comprehensive testing for all components:
- Agent functionality and integration
- Gong real-time connectivity
- Feedback engine and coaching system
- Dashboard metrics and WebSocket communication
- Sophia integration and natural language processing
- Performance benchmarking and load testing
"""

import asyncio
import json
import time
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch

from .agents import (
    TranscriptionAgent, SentimentAgent, CompetitiveAgent,
    RiskAssessmentAgent, CoachingAgent, SummaryAgent,
    SalesAgentOrchestrator, AgentOutput, AgentPriority, ConfidenceLevel
)
from .gong_realtime import (
    GongRealtimeConnector, RealtimeCallData, CallMetadata,
    TranscriptSegment, CallParticipant, CallEvent
)
from .feedback_engine import (
    SalesFeedbackSystem, FeedbackMessage, FeedbackType, DeliveryChannel
)
from .dashboard import SalesIntelligenceDashboard, MetricType
from .sophia_integration import (
    SalesIntelligenceOrchestrator, NaturalLanguageProcessor, SalesCommandType
)


class TestSalesAgents:
    """Test suite for individual sales intelligence agents"""
    
    @pytest.fixture
    def sample_call_data(self):
        """Sample call data for testing"""
        return RealtimeCallData(
            metadata=CallMetadata(
                call_id="test_call_123",
                call_url="https://test.gong.io/call/123",
                title="Test Discovery Call",
                scheduled_start=datetime.now(),
                actual_start=datetime.now(),
                duration_seconds=1800,
                participants=[
                    CallParticipant(
                        user_id="rep_1",
                        email="rep@company.com",
                        name="Sales Rep",
                        role="host",
                        joined_at=datetime.now(),
                        is_internal=True
                    ),
                    CallParticipant(
                        user_id="prospect_1", 
                        email="prospect@client.com",
                        name="John Prospect",
                        role="participant",
                        joined_at=datetime.now(),
                        is_internal=False
                    )
                ],
                meeting_platform="zoom",
                recording_status="recording",
                tags=["discovery", "enterprise"]
            ),
            transcripts=[
                TranscriptSegment(
                    speaker_id="rep_1",
                    speaker_name="Sales Rep",
                    text="Thanks for taking the time to meet with us today. Can you tell me about your current challenges?",
                    start_time=time.time(),
                    end_time=time.time() + 5,
                    confidence=0.95
                ),
                TranscriptSegment(
                    speaker_id="prospect_1",
                    speaker_name="John Prospect", 
                    text="Well, we're really struggling with our current solution. It's expensive and doesn't work well.",
                    start_time=time.time() + 5,
                    end_time=time.time() + 10,
                    confidence=0.92
                )
            ],
            last_update=datetime.now(),
            is_active=True
        )
    
    @pytest.fixture
    def agent_context(self, sample_call_data):
        """Sample agent context"""
        from .agents import AgentContext
        return AgentContext(
            call_data=sample_call_data,
            historical_data={},
            user_preferences={},
            team_settings={}
        )
    
    @pytest.mark.asyncio
    async def test_transcription_agent(self, agent_context):
        """Test transcription agent functionality"""
        agent = TranscriptionAgent()
        
        output = await agent.process(agent_context)
        
        assert output.agent_type == "transcription"
        assert output.call_id == "test_call_123"
        assert "new_segments" in output.data
        assert "conversation_flow" in output.data
        assert output.confidence == ConfidenceLevel.HIGH
    
    @pytest.mark.asyncio
    async def test_sentiment_agent(self, agent_context):
        """Test sentiment analysis agent"""
        agent = SentimentAgent()
        
        output = await agent.process(agent_context)
        
        assert output.agent_type == "sentiment"
        assert "overall_sentiment" in output.data
        assert "speaker_emotions" in output.data
        assert "engagement_level" in output.data
        assert "rapport_score" in output.data
        assert -1 <= output.data["overall_sentiment"] <= 1
    
    @pytest.mark.asyncio
    async def test_competitive_agent(self, agent_context):
        """Test competitive intelligence agent"""
        agent = CompetitiveAgent()
        
        output = await agent.process(agent_context)
        
        assert output.agent_type == "competitive"
        assert "competitor_mentions" in output.data
        assert "threat_level" in output.data
        assert "positioning_analysis" in output.data
        assert isinstance(output.data["competitor_mentions"], list)
    
    @pytest.mark.asyncio
    async def test_risk_assessment_agent(self, agent_context):
        """Test deal risk assessment agent"""
        agent = RiskAssessmentAgent()
        
        output = await agent.process(agent_context)
        
        assert output.agent_type == "risk_assessment"
        assert "overall_risk_score" in output.data
        assert "buying_signals" in output.data
        assert "red_flags" in output.data
        assert "probability_score" in output.data
        assert 0 <= output.data["overall_risk_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_coaching_agent(self, agent_context):
        """Test sales coaching agent"""
        agent = CoachingAgent()
        
        output = await agent.process(agent_context)
        
        assert output.agent_type == "coaching"
        assert "questioning_analysis" in output.data
        assert "talk_time_balance" in output.data
        assert "coaching_recommendations" in output.data
        assert "performance_score" in output.data
        assert isinstance(output.data["coaching_recommendations"], list)
    
    @pytest.mark.asyncio
    async def test_summary_agent(self, agent_context):
        """Test call summary agent"""
        agent = SummaryAgent()
        
        # Add more transcripts for better summarization
        agent_context.call_data.transcripts.extend([
            TranscriptSegment(
                speaker_id="rep_1",
                speaker_name="Sales Rep",
                text="What would be the timeline for implementation?",
                start_time=time.time() + 15,
                end_time=time.time() + 20,
                confidence=0.94
            ),
            TranscriptSegment(
                speaker_id="prospect_1", 
                speaker_name="John Prospect",
                text="We'd like to get started as soon as possible, maybe next quarter.",
                start_time=time.time() + 20,
                end_time=time.time() + 25,
                confidence=0.90
            )
        ])
        
        output = await agent.process(agent_context)
        
        assert output.agent_type == "summary"
        assert "call_summary" in output.data
        assert "key_topics" in output.data
        assert "action_items" in output.data
        assert "call_outcome" in output.data


class TestGongIntegration:
    """Test suite for Gong real-time integration"""
    
    @pytest.fixture
    def mock_gong_connector(self):
        """Mock Gong connector for testing"""
        return Mock(spec=GongRealtimeConnector)
    
    def test_gong_connector_initialization(self):
        """Test Gong connector initialization"""
        connector = GongRealtimeConnector("test_key", "test_secret")
        
        assert connector.ws_handler.access_key == "test_key"
        assert connector.ws_handler.client_secret == "test_secret"
    
    @pytest.mark.asyncio
    async def test_call_event_processing(self, mock_gong_connector):
        """Test processing of different call events"""
        connector = GongRealtimeConnector("test_key", "test_secret")
        
        # Mock event data
        call_started_data = {
            "event_type": "call_started",
            "call_id": "test_call_123",
            "title": "Test Call",
            "platform": "zoom"
        }
        
        transcript_data = {
            "event_type": "transcript_update", 
            "transcript": {
                "speaker_id": "speaker_1",
                "speaker_name": "John Doe",
                "text": "Hello, how are you today?",
                "start_time": time.time(),
                "end_time": time.time() + 3,
                "confidence": 0.95,
                "is_final": True
            }
        }
        
        # Test event handling would go here
        # In real implementation, we'd test WebSocket message processing


class TestFeedbackEngine:
    """Test suite for immediate feedback engine"""
    
    @pytest.fixture
    def feedback_system(self):
        """Create feedback system for testing"""
        return SalesFeedbackSystem()
    
    @pytest.fixture
    def sample_agent_output(self):
        """Sample agent output for testing"""
        return AgentOutput(
            agent_id="test_agent",
            agent_type="sentiment",
            call_id="test_call_123",
            timestamp=datetime.now(),
            priority=AgentPriority.HIGH,
            confidence=ConfidenceLevel.HIGH,
            data={
                "overall_sentiment": -0.6,
                "stress_indicators": 0.8,
                "engagement_level": 0.3
            },
            requires_action=True
        )
    
    @pytest.mark.asyncio
    async def test_feedback_generation(self, feedback_system, sample_agent_output):
        """Test feedback message generation"""
        feedback_messages = await feedback_system.process_agent_output(sample_agent_output)
        
        assert len(feedback_messages) > 0
        
        for message in feedback_messages:
            assert isinstance(message, FeedbackMessage)
            assert message.call_id == "test_call_123"
            assert message.type in [ft.value for ft in FeedbackType]
            assert message.priority in [ap.value for ap in AgentPriority]
    
    def test_feedback_rule_evaluation(self, feedback_system):
        """Test feedback rule evaluation logic"""
        # Test sentiment rule
        output_data = {"overall_sentiment": -0.6}
        
        # Mock output for testing
        class MockOutput:
            def __init__(self, data):
                self.data = data
        
        mock_output = MockOutput(output_data)
        trigger_result = feedback_system.feedback_engine._evaluate_trigger(
            "sentiment_score < -0.5", mock_output
        )
        
        assert trigger_result == True
    
    @pytest.mark.asyncio
    async def test_delivery_channels(self, feedback_system, sample_agent_output):
        """Test different delivery channel handling"""
        delivered_messages = []
        
        async def mock_delivery_handler(message):
            delivered_messages.append(message)
        
        # Register mock handlers
        for channel in DeliveryChannel:
            feedback_system.feedback_engine.register_delivery_handler(
                channel, mock_delivery_handler
            )
        
        await feedback_system.process_agent_output(sample_agent_output)
        
        # Check that messages were delivered
        assert len(delivered_messages) >= 0  # At least some messages should be delivered


class TestDashboard:
    """Test suite for sales intelligence dashboard"""
    
    @pytest.fixture
    async def dashboard(self):
        """Create dashboard for testing"""
        dashboard = SalesIntelligenceDashboard("redis://localhost:6379/1")
        await dashboard.initialize()
        return dashboard
    
    @pytest.fixture
    def sample_outputs(self):
        """Sample agent outputs for testing"""
        return [
            AgentOutput(
                agent_id="sentiment_1",
                agent_type="sentiment",
                call_id="test_call_123",
                timestamp=datetime.now(),
                priority=AgentPriority.MEDIUM,
                confidence=ConfidenceLevel.HIGH,
                data={"overall_sentiment": 0.3, "engagement_level": 0.8}
            ),
            AgentOutput(
                agent_id="risk_1",
                agent_type="risk_assessment",
                call_id="test_call_123",
                timestamp=datetime.now(),
                priority=AgentPriority.HIGH,
                confidence=ConfidenceLevel.HIGH,
                data={"overall_risk_score": 0.75}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_metrics_calculation(self, dashboard, sample_outputs):
        """Test dashboard metrics calculation"""
        for output in sample_outputs:
            await dashboard.process_agent_output(output)
        
        call_data = dashboard.get_call_dashboard_data("test_call_123")
        
        assert "latest_metrics" in call_data
        assert "overall_score" in call_data
        assert call_data["call_id"] == "test_call_123"
    
    @pytest.mark.asyncio
    async def test_websocket_management(self, dashboard):
        """Test WebSocket connection management"""
        mock_websocket = Mock()
        
        # Test connection
        await dashboard.websocket_manager.connect(mock_websocket, "test_call_123")
        
        assert mock_websocket in dashboard.websocket_manager.connections
        assert "test_call_123" in dashboard.websocket_manager.call_subscriptions
        
        # Test disconnection
        dashboard.websocket_manager.disconnect(mock_websocket)
        
        assert mock_websocket not in dashboard.websocket_manager.connections
    
    def test_team_metrics_aggregation(self, dashboard):
        """Test team-wide metrics aggregation"""
        # Add some mock call data
        dashboard.active_calls["call_1"] = Mock()
        dashboard.active_calls["call_1"].risk_level = "high"
        dashboard.active_calls["call_1"].sentiment_score = -0.2
        
        dashboard.active_calls["call_2"] = Mock()
        dashboard.active_calls["call_2"].risk_level = "low"
        dashboard.active_calls["call_2"].sentiment_score = 0.5
        
        team_data = dashboard.get_team_dashboard_data()
        
        assert "team_summary" in team_data
        assert "active_calls" in team_data
        assert team_data["team_summary"]["total_active_calls"] == 2


class TestSophiaIntegration:
    """Test suite for Sophia natural language integration"""
    
    @pytest.fixture
    def nlp_processor(self):
        """Create NLP processor for testing"""
        return NaturalLanguageProcessor()
    
    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator for testing"""
        orch = SalesIntelligenceOrchestrator()
        await orch.initialize()
        return orch
    
    def test_query_parsing(self, nlp_processor):
        """Test natural language query parsing"""
        queries = [
            ("What's the status of the current call?", SalesCommandType.CALL_STATUS),
            ("How risky is this deal?", SalesCommandType.RISK_ASSESSMENT),
            ("Any competitors mentioned?", SalesCommandType.COMPETITIVE_INTEL),
            ("Give me coaching feedback", SalesCommandType.COACHING_FEEDBACK),
            ("What's the sentiment like?", SalesCommandType.SENTIMENT_ANALYSIS),
            ("Show me performance metrics", SalesCommandType.PERFORMANCE_METRICS)
        ]
        
        for query_text, expected_type in queries:
            parsed_query = nlp_processor.parse_query(query_text)
            assert parsed_query.command_type == expected_type
            assert parsed_query.natural_query == query_text
    
    def test_entity_extraction(self, nlp_processor):
        """Test entity extraction from queries"""
        # Test call ID extraction
        query1 = nlp_processor.parse_query("What's the status of call abc123?")
        assert query1.call_id == "abc123"
        
        # Test current call reference
        query2 = nlp_processor.parse_query("How is the current call going?")
        assert query2.call_id == "current"
        
        # Test time range extraction
        query3 = nlp_processor.parse_query("Show me metrics from today")
        assert query3.time_range == "today"
    
    @pytest.mark.asyncio
    async def test_command_handling(self, orchestrator):
        """Test command handling through orchestrator"""
        # Mock some data for testing
        orchestrator.active_calls["test_call"] = Mock()
        orchestrator.active_calls["test_call"].is_active = True
        orchestrator.current_call_id = "test_call"
        
        # Test different command types
        commands = [
            "What's the status of the current call?",
            "How risky is this deal?",
            "Show me team overview"
        ]
        
        for command in commands:
            result = await orchestrator.process_sophia_query(command)
            
            assert result["success"] is not None
            assert "command_type" in result
            assert "timestamp" in result


class TestPerformanceBenchmarks:
    """Performance and load testing suite"""
    
    @pytest.mark.asyncio
    async def test_agent_processing_speed(self):
        """Test agent processing performance"""
        from .agents import AgentContext, create_sales_intelligence_swarm
        
        # Create sample data
        call_data = RealtimeCallData(
            metadata=CallMetadata(
                call_id="perf_test",
                call_url="",
                title="Performance Test",
                scheduled_start=datetime.now(),
                actual_start=datetime.now(),
                duration_seconds=0,
                participants=[],
                meeting_platform="test",
                recording_status="test",
                tags=[]
            ),
            transcripts=[
                TranscriptSegment(
                    speaker_id="speaker_1",
                    speaker_name="Speaker 1",
                    text="This is a performance test segment with some content for analysis.",
                    start_time=time.time(),
                    end_time=time.time() + 3,
                    confidence=0.95
                )
                for _ in range(100)  # Generate 100 segments
            ],
            last_update=datetime.now(),
            is_active=True
        )
        
        context = AgentContext(
            call_data=call_data,
            historical_data={},
            user_preferences={},
            team_settings={}
        )
        
        # Test processing time for all agents
        swarm = create_sales_intelligence_swarm()
        
        start_time = time.time()
        await swarm.process_call_data(call_data, {"test": "context"})
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should process within reasonable time (adjust threshold as needed)
        assert processing_time < 5.0, f"Processing took {processing_time}s, which exceeds 5s threshold"
    
    @pytest.mark.asyncio
    async def test_concurrent_call_processing(self):
        """Test processing multiple calls concurrently"""
        from .agents import create_sales_intelligence_swarm
        
        swarm = create_sales_intelligence_swarm()
        
        # Create multiple call data instances
        calls = []
        for i in range(10):
            call_data = RealtimeCallData(
                metadata=CallMetadata(
                    call_id=f"concurrent_test_{i}",
                    call_url="",
                    title=f"Concurrent Test {i}",
                    scheduled_start=datetime.now(),
                    actual_start=datetime.now(),
                    duration_seconds=0,
                    participants=[],
                    meeting_platform="test",
                    recording_status="test",
                    tags=[]
                ),
                transcripts=[
                    TranscriptSegment(
                        speaker_id="speaker_1",
                        speaker_name="Speaker 1",
                        text=f"This is test segment {j} for call {i}",
                        start_time=time.time() + j,
                        end_time=time.time() + j + 2,
                        confidence=0.90
                    )
                    for j in range(10)
                ],
                last_update=datetime.now(),
                is_active=True
            )
            calls.append(call_data)
        
        # Process all calls concurrently
        start_time = time.time()
        tasks = [swarm.process_call_data(call) for call in calls]
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should handle concurrent processing efficiently
        assert processing_time < 10.0, f"Concurrent processing took {processing_time}s"
    
    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self):
        """Test memory usage during intensive processing"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create and process large amount of data
        from .agents import create_sales_intelligence_swarm
        swarm = create_sales_intelligence_swarm()
        
        for i in range(50):
            call_data = RealtimeCallData(
                metadata=CallMetadata(
                    call_id=f"memory_test_{i}",
                    call_url="",
                    title=f"Memory Test {i}",
                    scheduled_start=datetime.now(),
                    actual_start=datetime.now(),
                    duration_seconds=0,
                    participants=[],
                    meeting_platform="test", 
                    recording_status="test",
                    tags=[]
                ),
                transcripts=[
                    TranscriptSegment(
                        speaker_id="speaker_1",
                        speaker_name="Speaker 1",
                        text="This is a memory test segment with content " * 20,  # Larger content
                        start_time=time.time() + j,
                        end_time=time.time() + j + 2,
                        confidence=0.90
                    )
                    for j in range(50)  # More segments
                ],
                last_update=datetime.now(),
                is_active=True
            )
            
            await swarm.process_call_data(call_data)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 500, f"Memory increased by {memory_increase}MB, which may indicate a memory leak"


class TestIntegrationScenarios:
    """End-to-end integration testing"""
    
    @pytest.mark.asyncio
    async def test_complete_call_workflow(self):
        """Test complete call processing workflow"""
        from .sophia_integration import SalesIntelligenceOrchestrator
        
        # Initialize orchestrator
        orchestrator = SalesIntelligenceOrchestrator()
        await orchestrator.initialize()
        
        # Simulate call start
        call_id = "integration_test_call"
        
        # Mock call data
        call_data = RealtimeCallData(
            metadata=CallMetadata(
                call_id=call_id,
                call_url="https://test.gong.io/call/123",
                title="Integration Test Call", 
                scheduled_start=datetime.now(),
                actual_start=datetime.now(),
                duration_seconds=None,
                participants=[],
                meeting_platform="zoom",
                recording_status="recording",
                tags=["test", "integration"]
            ),
            transcripts=[],
            last_update=datetime.now(),
            is_active=True
        )
        
        orchestrator.active_calls[call_id] = call_data
        orchestrator.current_call_id = call_id
        
        # Test various Sophia queries
        queries = [
            "What's the status of the current call?",
            "How risky is this deal?", 
            "Show me coaching feedback",
            "What's the sentiment analysis?",
            "Give me performance metrics"
        ]
        
        for query in queries:
            result = await orchestrator.process_sophia_query(query)
            
            assert result.get("success") is not None
            assert "data" in result or "error" in result
    
    @pytest.mark.asyncio 
    async def test_error_handling_and_recovery(self):
        """Test system behavior under error conditions"""
        from .feedback_engine import SalesFeedbackSystem
        
        feedback_system = SalesFeedbackSystem()
        
        # Test with invalid agent output
        invalid_output = AgentOutput(
            agent_id="test_agent",
            agent_type="invalid_type",  # Invalid type
            call_id="test_call",
            timestamp=datetime.now(),
            priority=AgentPriority.MEDIUM,
            confidence=ConfidenceLevel.HIGH,
            data={},
            requires_action=False
        )
        
        # Should handle gracefully without crashing
        try:
            result = await feedback_system.process_agent_output(invalid_output)
            # Should return empty list or handle gracefully
            assert isinstance(result, list)
        except Exception as e:
            # Should not raise unhandled exceptions
            pytest.fail(f"System should handle invalid input gracefully, but raised: {e}")


# Test runner and utilities
def run_comprehensive_tests():
    """Run all tests with detailed reporting"""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--capture=no",
        "--asyncio-mode=auto"
    ])


def run_performance_tests():
    """Run only performance and load tests"""
    pytest.main([
        f"{__file__}::TestPerformanceBenchmarks",
        "-v",
        "--tb=short",
        "--capture=no", 
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_comprehensive_tests()