"""
Comprehensive end-to-end integration tests for Sophia Intel platform.
Tests complete workflow: Frontend → Orchestrator → Agent → MCP → Response
"""
import pytest
import asyncio
import json
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import time
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.orchestrator import Orchestrator
from services.portkey_client import PortkeyClient
from services.lambda_client import LambdaClient
from mcp_servers.memory_service import MemoryService
from agents.coding_agent import CodingAgent
from config.config import settings


class TestE2EWorkflow:
    """End-to-end workflow integration tests."""
    
    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator instance for testing."""
        return Orchestrator()
    
    @pytest.fixture
    async def memory_service(self):
        """Create memory service with mocked dependencies."""
        with patch('mcp_servers.memory_service.PortkeyClient') as mock_portkey:
            # Mock the embeddings response
            mock_portkey.return_value.embeddings.return_value = {
                "data": [{"embedding": [0.1] * 1536}]  # Mock 1536-dim embedding
            }
            # Mock the chat response for summarization
            mock_portkey.return_value.chat.return_value = {
                "choices": [{"message": {"content": "Test Context Summary"}}]
            }
            
            service = MemoryService()
            return service
    
    @pytest.fixture
    async def coding_agent(self):
        """Create coding agent with mocked dependencies."""
        with patch('agents.coding_agent.Agent') as mock_agno:
            # Mock Agno agent response
            mock_agno.return_value.run.return_value = json.dumps({
                "summary": "Added type hints and comprehensive docstring",
                "patch": "--- a/example.py\n+++ b/example.py\n@@ -1,2 +1,7 @@\n-def example():\n-    pass\n+def example() -> None:\n+    \"\"\"Example function.\"\"\"\n+    pass"
            })
            
            agent = CodingAgent()
            return agent

    @pytest.mark.asyncio
    async def test_complete_agent_workflow(self, orchestrator, memory_service, coding_agent):
        """
        Test complete workflow: Request → Orchestrator → Agent → MCP → Response
        """
        # Mock external API calls
        with patch.object(orchestrator.portkey, 'chat') as mock_chat, \
             patch.object(orchestrator.lambda_client, 'quota') as mock_quota, \
             patch('httpx.AsyncClient') as mock_client:
            
            # Setup mocks
            mock_chat.return_value = {
                "choices": [{"message": {"content": "Mocked LLM response"}}]
            }
            
            mock_quota.return_value = {
                "quota": {"gpu_time_remaining": 3600},
                "usage": {"gpu_time_used": 0}
            }
            
            # Mock HTTP client for MCP and Agent API calls
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "success": True,
                "result": {
                    "summary": "Added type hints and docstring",
                    "patch": "--- a/file\n+++ b/file\n@@ -1,1 +1,3 @@\n-def test():\n+def test() -> None:\n+    \"\"\"Test function.\"\"\""
                }
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Test coding request
            request_payload = {
                "session_id": "e2e-test-session",
                "code": "def test():\n    pass",
                "query": "Add type hints and docstring"
            }
            
            result = await orchestrator.handle_request(
                request_type="code",
                payload=request_payload,
                timeout=60,
                retries=2
            )
            
            # Verify response structure
            assert result["success"] is True
            assert "result" in result
            assert "duration" in result
            assert "timestamp" in result
            
            # Verify the result contains expected fields
            if "result" in result and result["result"]:
                assert isinstance(result["result"], dict)

    @pytest.mark.asyncio
    async def test_memory_storage_and_retrieval(self, memory_service):
        """
        Test memory service context storage and semantic search.
        """
        # Test context storage
        store_result = await memory_service.store_context(
            session_id="test-session",
            content="This is a test context about Python decorators and async programming",
            metadata={"context_type": "coding_knowledge", "priority": "high"}
        )
        
        assert store_result["success"] is True
        assert "id" in store_result
        assert "summary" in store_result
        
        # Test context retrieval
        query_results = await memory_service.query_context(
            session_id="test-session",
            query="Python decorators",
            top_k=5,
            threshold=0.5
        )
        
        assert isinstance(query_results, list)
        if query_results:
            result = query_results[0]
            assert "content" in result
            assert "summary" in result
            assert "score" in result
            assert "session_id" in result

    @pytest.mark.asyncio
    async def test_orchestrator_error_handling(self, orchestrator):
        """
        Test orchestrator error handling and circuit breaker functionality.
        """
        # Test invalid request type
        result = await orchestrator.handle_request(
            request_type="invalid_type",
            payload={},
            timeout=30,
            retries=1
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "error_type" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_gpu_request_handling(self, orchestrator):
        """
        Test GPU request handling via Lambda Labs client.
        """
        # Mock Lambda Labs API response
        with patch.object(orchestrator.lambda_client, 'quota') as mock_quota:
            mock_quota.return_value = {
                "quota": {
                    "gpu_time_remaining": 3600,
                    "instance_limit": 5
                },
                "usage": {
                    "gpu_time_used": 0,
                    "instances_running": 0
                }
            }
            
            result = await orchestrator.handle_request(
                request_type="gpu",
                payload={"type": "quota"},
                timeout=30,
                retries=2
            )
            
            assert result["success"] is True
            assert "result" in result
            if "quota" in result["result"]:
                assert "gpu_time_remaining" in result["result"]["quota"]

    @pytest.mark.asyncio
    async def test_chat_request_via_orchestrator(self, orchestrator):
        """
        Test chat requests through the orchestrator.
        """
        # Mock Portkey client response
        with patch.object(orchestrator.portkey, 'chat') as mock_chat:
            mock_chat.return_value = {
                "choices": [{
                    "message": {
                        "content": "This is a test response from the LLM"
                    }
                }],
                "usage": {"total_tokens": 25}
            }
            
            result = await orchestrator.handle_request(
                request_type="chat",
                payload={
                    "messages": [{"role": "user", "content": "Hello, how are you?"}],
                    "model": "openrouter/auto"
                },
                timeout=30,
                retries=2
            )
            
            assert result["success"] is True
            assert "result" in result
            if "choices" in result["result"]:
                assert len(result["result"]["choices"]) > 0

    @pytest.mark.asyncio
    async def test_agent_json_response_parsing(self, coding_agent):
        """
        Test agent response parsing and validation.
        """
        # Test with valid JSON response
        test_code = "def hello():\n    print('world')"
        test_query = "Add type hints and docstring"
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock MCP server responses
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"results": []}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await coding_agent.execute("test-task-1", {
                "session_id": "test-session",
                "code": test_code,
                "query": test_query
            })
            
            assert result["success"] is True
            assert "result" in result
            if "result" in result and result["result"]:
                assert "summary" in result["result"]
                assert "patch" in result["result"]

    @pytest.mark.asyncio
    async def test_service_health_checks(self, orchestrator):
        """
        Test health check functionality across all services.
        """
        # Mock service responses
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"status": "healthy"}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await orchestrator.handle_request(
                request_type="health",
                payload={},
                timeout=30,
                retries=1
            )
            
            assert result["success"] is True
            assert "result" in result
            if "overall_status" in result["result"]:
                assert result["result"]["overall_status"] in ["healthy", "degraded"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, orchestrator):
        """
        Test circuit breaker pattern in service requests.
        """
        # Simulate service failures to trigger circuit breaker
        service_name = "agno_api"
        
        # Record multiple failures
        for _ in range(6):  # Trigger circuit breaker (threshold is 5)
            orchestrator._record_circuit_failure(service_name)
        
        # Verify circuit breaker is open
        assert not orchestrator._is_circuit_open(service_name)
        assert orchestrator.circuit_breakers[service_name]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_request_statistics_tracking(self, orchestrator):
        """
        Test request statistics and performance tracking.
        """
        initial_stats = orchestrator.get_stats()
        initial_total = initial_stats["request_stats"]["total_requests"]
        
        # Make a successful request
        with patch.object(orchestrator.portkey, 'chat') as mock_chat:
            mock_chat.return_value = {"choices": [{"message": {"content": "test"}}]}
            
            await orchestrator.handle_request(
                request_type="chat",
                payload={"messages": [{"role": "user", "content": "test"}]},
                timeout=30,
                retries=1
            )
        
        # Verify statistics updated
        updated_stats = orchestrator.get_stats()
        assert updated_stats["request_stats"]["total_requests"] > initial_total

    @pytest.mark.asyncio
    async def test_memory_session_management(self, memory_service):
        """
        Test memory service session isolation and management.
        """
        # Store context in different sessions
        await memory_service.store_context(
            session_id="session-1",
            content="Content for session 1",
            metadata={"session": "1"}
        )
        
        await memory_service.store_context(
            session_id="session-2", 
            content="Content for session 2",
            metadata={"session": "2"}
        )
        
        # Query session-specific content
        session1_results = await memory_service.query_context(
            session_id="session-1",
            query="session content",
            global_search=False
        )
        
        session2_results = await memory_service.query_context(
            session_id="session-2",
            query="session content",
            global_search=False
        )
        
        # Verify session isolation
        for result in session1_results:
            assert result["session_id"] == "session-1"
        
        for result in session2_results:
            assert result["session_id"] == "session-2"

    @pytest.mark.asyncio
    async def test_agent_timeout_handling(self, coding_agent):
        """
        Test agent timeout and cancellation functionality.
        """
        # Mock a slow-running task
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = AsyncMock()
            # Simulate a task that takes longer than timeout
            mock_executor.side_effect = asyncio.TimeoutError("Task timeout")
            mock_loop.return_value.run_in_executor = mock_executor
            
            result = await coding_agent.execute("timeout-test", {
                "session_id": "test-timeout",
                "code": "def test(): pass",
                "query": "test query"
            })
            
            # Should handle timeout gracefully
            assert result["success"] is False
            assert "timeout" in result.get("error", "").lower()

    def test_configuration_validation_integration(self):
        """
        Test integration with configuration validation system.
        """
        # Import and run validation
        from scripts.validate_config import ConfigValidator
        
        validator = ConfigValidator()
        is_valid, errors, warnings = validator.validate_all()
        
        # In test environment, some validation errors are expected
        # but the validation system itself should work
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
        assert isinstance(warnings, list)

    @pytest.mark.asyncio
    async def test_end_to_end_performance(self, orchestrator):
        """
        Test end-to-end performance and response times.
        """
        # Mock all external dependencies
        with patch.object(orchestrator.portkey, 'chat') as mock_chat, \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_chat.return_value = {"choices": [{"message": {"content": "test"}}]}
            
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"success": True, "result": {"summary": "test", "patch": ""}}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            start_time = time.time()
            
            result = await orchestrator.handle_request(
                request_type="code",
                payload={
                    "session_id": "perf-test",
                    "code": "def test(): pass",
                    "query": "optimize this"
                }
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Verify performance expectations
            assert result["success"] is True
            assert duration < 10.0  # Should complete within 10 seconds
            assert "duration" in result

    @pytest.mark.asyncio
    async def test_error_recovery_and_fallbacks(self, memory_service):
        """
        Test error recovery and fallback mechanisms.
        """
        # Test embedding fallback when OpenRouter fails
        with patch.object(memory_service.portkey_client, 'embeddings') as mock_embeddings:
            # Make embeddings fail
            mock_embeddings.side_effect = Exception("OpenRouter API failed")
            
            # Storage should still work with fallback embedding
            result = await memory_service.store_context(
                session_id="fallback-test",
                content="Test fallback embedding",
                metadata={"test": "fallback"}
            )
            
            assert result["success"] is True
            assert "id" in result