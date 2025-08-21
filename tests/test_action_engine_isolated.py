"""
Isolated unit tests for SOPHIA ActionEngine

Tests the core functionality without importing the full SOPHIA package.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import directly from the module
from sophia.core.action_engine import ActionEngine, ActionResult, ActionStatus, ResearchResult

class TestActionEngineIsolated:
    """Isolated test suite for ActionEngine"""
    
    @pytest.fixture
    def action_engine(self):
        """Create ActionEngine instance for testing"""
        return ActionEngine()
    
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
    async def test_execute_action_unknown_action(self, action_engine):
        """Test execution of unknown action"""
        result = await action_engine.execute_action(
            "unknown.action",
            {"query": "test"}
        )
        
        assert result.status == ActionStatus.FAILURE
        assert "Unknown action: unknown.action" in result.errors
    
    def test_action_result_creation(self):
        """Test ActionResult creation and defaults"""
        result = ActionResult(
            status=ActionStatus.SUCCESS,
            query="test query",
            results=[]
        )
        
        assert result.status == ActionStatus.SUCCESS
        assert result.query == "test query"
        assert result.results == []
        assert result.timestamp != ""  # Should be auto-generated
        assert result.execution_time_ms == 0
        assert result.errors == []
    
    def test_research_result_creation(self):
        """Test ResearchResult creation"""
        result = ResearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            extracted_text="Full content",
            source="serper",
            fetched_at="2025-08-21T04:00:00Z",
            score=0.85
        )
        
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.extracted_text == "Full content"
        assert result.source == "serper"
        assert result.score == 0.85

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

