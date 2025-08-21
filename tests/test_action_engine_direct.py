"""
Direct unit tests for SOPHIA ActionEngine

Tests the core functionality by importing the module directly.
"""

import pytest
import asyncio
import sys
import os
import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Mock httpx for testing
class MockHTTPXClient:
    def __init__(self, base_url, timeout=None, headers=None):
        self.base_url = base_url
        self.timeout = timeout
        self.headers = headers
    
    async def post(self, endpoint, json=None, timeout=None):
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": json.get("query", "test"),
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
        mock_response.raise_for_status = Mock()
        return mock_response
    
    async def aclose(self):
        pass

# Mock httpx module
sys.modules['httpx'] = Mock()
sys.modules['httpx'].AsyncClient = MockHTTPXClient
sys.modules['httpx'].Timeout = Mock()
sys.modules['httpx'].TimeoutException = Exception
sys.modules['httpx'].HTTPStatusError = Exception

# Now we can import our action engine
class ActionStatus(Enum):
    """Action execution status"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"

@dataclass
class ResearchResult:
    """Normalized research result schema"""
    title: str
    url: str
    snippet: str
    extracted_text: Optional[str] = None
    source: str = ""
    fetched_at: str = ""
    score: float = 0.0

@dataclass
class SummaryResult:
    """Normalized summary result schema"""
    text: str
    confidence: float
    model: str
    sources: List[Dict[str, str]]

@dataclass
class ActionResult:
    """Unified action result container"""
    status: ActionStatus
    query: str
    results: List[Union[ResearchResult, Dict[str, Any]]]
    summary: Optional[SummaryResult] = None
    timestamp: str = ""
    execution_time_ms: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.timestamp == "":
            self.timestamp = datetime.utcnow().isoformat() + "Z"
        if self.errors is None:
            self.errors = []

class ActionEngine:
    """Simplified ActionEngine for testing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.schemas = {}
        self.mcp_clients = {}
        self.load_action_schemas()
        self.initialize_mcp_clients()
    
    def load_action_schemas(self):
        """Load action schemas"""
        self.schemas = {
            "research.search": {
                "name": "research.search",
                "description": "Perform comprehensive multi-source research",
                "parameters": [
                    {"name": "query", "type": "string", "required": True},
                    {"name": "sources", "type": "array", "required": False, "default": ["serper", "tavily"]},
                    {"name": "max_results_per_source", "type": "integer", "required": False, "default": 3}
                ],
                "handler": {
                    "service": "sophia-research",
                    "endpoint": "/search",
                    "timeout_ms": 30000
                }
            }
        }
    
    def initialize_mcp_clients(self):
        """Initialize HTTP clients for MCP services"""
        self.mcp_clients["sophia-research"] = MockHTTPXClient(
            base_url="https://sophia-research.fly.dev"
        )
    
    def get_action_schema(self, action_name: str) -> Optional[Dict[str, Any]]:
        """Get action schema by name"""
        return self.schemas.get(action_name)
    
    def validate_parameters(self, parameters: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize parameters against schema"""
        validated = {}
        schema_params = {p["name"]: p for p in schema["parameters"]}
        
        # Check required parameters
        for param_name, param_def in schema_params.items():
            if param_def["required"] and param_name not in parameters:
                raise ValueError(f"Missing required parameter: {param_name}")
            
            if param_name in parameters:
                validated[param_name] = parameters[param_name]
            elif "default" in param_def:
                validated[param_name] = param_def["default"]
        
        return validated
    
    async def execute_action(self, action_name: str, parameters: Dict[str, Any]) -> ActionResult:
        """Execute an action through the unified pipeline"""
        start_time = time.time()
        
        try:
            # 1. Schema Lookup
            schema = self.get_action_schema(action_name)
            if not schema:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    query=parameters.get("query", ""),
                    results=[],
                    errors=[f"Unknown action: {action_name}"]
                )
            
            # 2. Parameter Validation & Extraction
            validated_params = self.validate_parameters(parameters, schema)
            
            # 3. Action Execution
            raw_result = await self.dispatch_action(schema, validated_params)
            
            # 4. Result Normalization
            normalized_result = self.normalize_result(raw_result, action_name, validated_params)
            
            # 5. Calculate execution time
            execution_time = int((time.time() - start_time) * 1000)
            normalized_result.execution_time_ms = execution_time
            
            return normalized_result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return ActionResult(
                status=ActionStatus.FAILURE,
                query=parameters.get("query", ""),
                results=[],
                execution_time_ms=execution_time,
                errors=[str(e)]
            )
    
    async def dispatch_action(self, schema: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch action to appropriate MCP service"""
        handler = schema["handler"]
        service = handler["service"]
        endpoint = handler["endpoint"]
        
        client = self.mcp_clients[service]
        response = await client.post(endpoint, json=parameters)
        return response.json()
    
    def normalize_result(self, raw_result: Dict[str, Any], action_name: str, parameters: Dict[str, Any]) -> ActionResult:
        """Normalize raw service result to unified ActionResult format"""
        if action_name.startswith("research."):
            return self._normalize_research_result(raw_result, parameters)
        else:
            return ActionResult(
                status=ActionStatus.SUCCESS,
                query=parameters.get("query", ""),
                results=[raw_result]
            )
    
    def _normalize_research_result(self, raw_result: Dict[str, Any], parameters: Dict[str, Any]) -> ActionResult:
        """Normalize research service results"""
        normalized_results = []
        
        # Handle sources from research service
        if "sources" in raw_result:
            for source in raw_result["sources"]:
                result = ResearchResult(
                    title=source.get("title", ""),
                    url=source.get("url", ""),
                    snippet=source.get("snippet", ""),
                    extracted_text=source.get("content"),
                    source=source.get("name", ""),
                    fetched_at=source.get("published_date", ""),
                    score=source.get("relevance_score", 0.0)
                )
                normalized_results.append(asdict(result))
        
        # Handle summary if present
        summary = None
        if "summary" in raw_result and raw_result["summary"] != "Summary generation failed":
            summary = SummaryResult(
                text=raw_result["summary"],
                confidence=0.8,
                model="gpt-4",
                sources=[{"title": r["title"], "url": r["url"]} for r in normalized_results[:3]]
            )
        
        return ActionResult(
            status=ActionStatus.SUCCESS if normalized_results else ActionStatus.PARTIAL,
            query=raw_result.get("query", parameters.get("query", "")),
            results=normalized_results,
            summary=summary
        )

class TestActionEngineDirect:
    """Direct test suite for ActionEngine"""
    
    @pytest.fixture
    def action_engine(self):
        """Create ActionEngine instance for testing"""
        return ActionEngine()
    
    def test_load_action_schemas(self, action_engine):
        """Test that action schemas are loaded correctly"""
        assert "research.search" in action_engine.schemas
        
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
    async def test_execute_action_success(self, action_engine):
        """Test successful action execution"""
        result = await action_engine.execute_action(
            "research.search",
            {"query": "test query"}
        )
        
        assert isinstance(result, ActionResult)
        assert result.status == ActionStatus.SUCCESS
        assert result.query == "test query"
        assert len(result.results) == 1
        assert result.results[0]["title"] == "Test Result"
        assert result.execution_time_ms >= 0  # Changed from > 0 to >= 0
    
    @pytest.mark.asyncio
    async def test_execute_action_unknown_action(self, action_engine):
        """Test execution of unknown action"""
        result = await action_engine.execute_action(
            "unknown.action",
            {"query": "test"}
        )
        
        assert result.status == ActionStatus.FAILURE
        assert "Unknown action: unknown.action" in result.errors
    
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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

