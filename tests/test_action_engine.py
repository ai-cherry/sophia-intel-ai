"""
Unit tests for SOPHIA ActionEngine

Tests the core functionality of the unified action orchestration framework.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from sophia.core.action_engine import ActionEngine, ActionResult, ActionStatus, ResearchResult

class TestActionEngine:
    """Test suite for ActionEngine"""
    
    @pytest.fixture
    def action_engine(self):
        """Create ActionEngine instance for testing"""
        return ActionEngine()
    
    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client for testing"""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": "test query",
            "sources": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "snippet": "Test snippet",
                    "content": "Test content",
                    "name": "serper",
                    "relevance_score": 0.8
                }
            ],
            "summary": "Test summary",
            "total_sources": 1
        }
        mock_client.post.return_value = mock_response
        return mock_client
    
    def test_load_action_schemas(self, action_engine):
        """Test that action schemas are loaded correctly"""
        assert "research.search" in action_engine.schemas
        assert "business.create_task" in action_engine.schemas
        assert "code.pr_open" in action_engine.schemas
        
        # Test schema structure
        research_schema = action_engine.schemas["research.search"]
        assert research_schema["name"] == "research.search"
        assert "parameters" in research_schema
        assert "handler" in research_schema
    
    def test_get_action_schema(self, action_engine):
        """Test schema retrieval"""
        schema = action_engine.get_action_schema("research.search")
        assert schema is not None
        assert schema["name"] == "research.search"
        
        # Test unknown schema
        unknown_schema = action_engine.get_action_schema("unknown.action")
        assert unknown_schema is None
    
    def test_validate_parameters_success(self, action_engine):
        """Test successful parameter validation"""
        schema = action_engine.get_action_schema("research.search")
        parameters = {"query": "test query"}
        
        validated = action_engine.validate_parameters(parameters, schema)
        assert validated["query"] == "test query"
        assert "sources" in validated  # Should have default value
        assert validated["sources"] == ["serper", "tavily"]
    
    def test_validate_parameters_missing_required(self, action_engine):
        """Test parameter validation with missing required parameter"""
        schema = action_engine.get_action_schema("research.search")
        parameters = {}  # Missing required 'query'
        
        with pytest.raises(ValueError, match="Missing required parameter: query"):
            action_engine.validate_parameters(parameters, schema)
    
    @pytest.mark.asyncio
    async def test_execute_action_success(self, action_engine, mock_httpx_client):
        """Test successful action execution"""
        # Mock the HTTP client
        action_engine.mcp_clients["sophia-research"] = mock_httpx_client
        
        result = await action_engine.execute_action(
            "research.search",
            {"query": "test query"}
        )
        
        assert isinstance(result, ActionResult)
        assert result.status == ActionStatus.SUCCESS
        assert result.query == "test query"
        assert len(result.results) == 1
        assert result.results[0]["title"] == "Test Result"
        assert result.execution_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_execute_action_unknown_action(self, action_engine):
        """Test execution of unknown action"""
        result = await action_engine.execute_action(
            "unknown.action",
            {"query": "test"}
        )
        
        assert result.status == ActionStatus.FAILURE
        assert "Unknown action: unknown.action" in result.errors
    
    @pytest.mark.asyncio
    async def test_execute_action_service_error(self, action_engine):
        """Test action execution with service error"""
        # Mock HTTP client to raise an exception
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Service unavailable")
        action_engine.mcp_clients["sophia-research"] = mock_client
        
        result = await action_engine.execute_action(
            "research.search",
            {"query": "test query"}
        )
        
        assert result.status == ActionStatus.FAILURE
        assert len(result.errors) > 0
        assert "Service unavailable" in str(result.errors[0])
    
    def test_normalize_research_result(self, action_engine):
        """Test research result normalization"""
        raw_result = {
            "query": "test query",
            "sources": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "snippet": "Test snippet",
                    "content": "Test content",
                    "name": "serper",
                    "relevance_score": 0.8
                }
            ],
            "summary": "Test summary"
        }
        
        parameters = {"query": "test query"}
        normalized = action_engine._normalize_research_result(raw_result, parameters)
        
        assert normalized.status == ActionStatus.SUCCESS
        assert normalized.query == "test query"
        assert len(normalized.results) == 1
        assert normalized.results[0]["title"] == "Test Result"
        assert normalized.summary is not None
        assert normalized.summary.text == "Test summary"
    
    def test_normalize_research_result_no_summary(self, action_engine):
        """Test research result normalization without summary"""
        raw_result = {
            "query": "test query",
            "sources": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "snippet": "Test snippet",
                    "name": "serper",
                    "relevance_score": 0.8
                }
            ],
            "summary": "Summary generation failed"
        }
        
        parameters = {"query": "test query"}
        normalized = action_engine._normalize_research_result(raw_result, parameters)
        
        assert normalized.summary is None
    
    def test_normalize_research_result_empty_sources(self, action_engine):
        """Test research result normalization with empty sources"""
        raw_result = {
            "query": "test query",
            "sources": [],
            "summary": "No results found"
        }
        
        parameters = {"query": "test query"}
        normalized = action_engine._normalize_research_result(raw_result, parameters)
        
        assert normalized.status == ActionStatus.PARTIAL
        assert len(normalized.results) == 0
    
    @pytest.mark.asyncio
    async def test_close(self, action_engine):
        """Test closing HTTP clients"""
        # Mock clients
        mock_client = AsyncMock()
        action_engine.mcp_clients["test"] = mock_client
        
        await action_engine.close()
        mock_client.aclose.assert_called_once()

@pytest.mark.asyncio
async def test_get_action_engine():
    """Test global action engine instance"""
    from sophia.core.action_engine import get_action_engine
    
    engine1 = await get_action_engine()
    engine2 = await get_action_engine()
    
    # Should return the same instance
    assert engine1 is engine2

@pytest.mark.asyncio
async def test_execute_action_convenience_function():
    """Test convenience function for action execution"""
    from sophia.core.action_engine import execute_action
    
    with patch('sophia.core.action_engine.get_action_engine') as mock_get_engine:
        mock_engine = AsyncMock()
        mock_result = ActionResult(
            status=ActionStatus.SUCCESS,
            query="test",
            results=[]
        )
        mock_engine.execute_action.return_value = mock_result
        mock_get_engine.return_value = mock_engine
        
        result = await execute_action("research.search", {"query": "test"})
        
        assert result.status == ActionStatus.SUCCESS
        mock_engine.execute_action.assert_called_once_with("research.search", {"query": "test"})

if __name__ == "__main__":
    pytest.main([__file__])

