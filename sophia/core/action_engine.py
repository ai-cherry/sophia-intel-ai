"""
SOPHIA Action Engine - Unified Action Orchestration Framework

This module implements the core ActionEngine that orchestrates all SOPHIA actions
following the pattern: Intent → Schema → Param Extract → Execute → Normalize Result

Eliminates fragmentation by providing a single source of truth for action execution.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

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
    """
    Unified Action Engine for SOPHIA
    
    Orchestrates all actions through a standardized pipeline:
    1. Intent Recognition
    2. Schema Lookup
    3. Parameter Extraction
    4. Action Execution
    5. Result Normalization
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.schemas = {}
        self.mcp_clients = {}
        self.load_action_schemas()
        self.initialize_mcp_clients()
    
    def load_action_schemas(self):
        """Load action schemas from ACTION_SCHEMAS.md"""
        # For now, define schemas programmatically
        # TODO: Load from ACTION_SCHEMAS.md file
        self.schemas = {
            "research.search": {
                "name": "research.search",
                "description": "Perform comprehensive multi-source research",
                "parameters": [
                    {"name": "query", "type": "string", "required": True},
                    {"name": "sources", "type": "array", "required": False, "default": ["serper", "tavily"]},
                    {"name": "max_results_per_source", "type": "integer", "required": False, "default": 3},
                    {"name": "include_content", "type": "boolean", "required": False, "default": True},
                    {"name": "summarize", "type": "boolean", "required": False, "default": True}
                ],
                "handler": {
                    "service": "sophia-research",
                    "endpoint": "/search",
                    "timeout_ms": 30000
                }
            },
            "research.fetch": {
                "name": "research.fetch",
                "description": "Fetch and extract content from specific URLs",
                "parameters": [
                    {"name": "urls", "type": "array", "required": True},
                    {"name": "extract_text", "type": "boolean", "required": False, "default": True}
                ],
                "handler": {
                    "service": "sophia-research",
                    "endpoint": "/fetch",
                    "timeout_ms": 15000
                }
            },
            "research.summarize": {
                "name": "research.summarize",
                "description": "Generate summary from research results",
                "parameters": [
                    {"name": "results", "type": "array", "required": True},
                    {"name": "query", "type": "string", "required": True},
                    {"name": "model", "type": "string", "required": False, "default": "gpt-4"}
                ],
                "handler": {
                    "service": "sophia-research",
                    "endpoint": "/summarize",
                    "timeout_ms": 15000
                }
            },
            "business.create_task": {
                "name": "business.create_task",
                "description": "Create task in business management system",
                "parameters": [
                    {"name": "title", "type": "string", "required": True},
                    {"name": "description", "type": "string", "required": False},
                    {"name": "assignee", "type": "string", "required": False},
                    {"name": "project", "type": "string", "required": False}
                ],
                "handler": {
                    "service": "sophia-business",
                    "endpoint": "/create_task",
                    "timeout_ms": 10000
                }
            },
            "code.pr_open": {
                "name": "code.pr_open",
                "description": "Open pull request in GitHub repository",
                "parameters": [
                    {"name": "title", "type": "string", "required": True},
                    {"name": "body", "type": "string", "required": False},
                    {"name": "branch", "type": "string", "required": True},
                    {"name": "base", "type": "string", "required": False, "default": "main"}
                ],
                "handler": {
                    "service": "sophia-code",
                    "endpoint": "/pr_open",
                    "timeout_ms": 10000
                }
            }
        }
    
    def initialize_mcp_clients(self):
        """Initialize HTTP clients for MCP services"""
        base_urls = {
            "sophia-research": "https://sophia-research.fly.dev",
            "sophia-business": "https://sophia-business.fly.dev",
            "sophia-code": "https://sophia-code.fly.dev",
            "sophia-context": "https://sophia-context.fly.dev",
            "sophia-memory": "https://sophia-memory.fly.dev"
        }
        
        for service, base_url in base_urls.items():
            self.mcp_clients[service] = httpx.AsyncClient(
                base_url=base_url,
                timeout=httpx.Timeout(30.0),
                headers={"Content-Type": "application/json"}
            )
    
    async def execute_action(self, action_name: str, parameters: Dict[str, Any]) -> ActionResult:
        """
        Execute an action through the unified pipeline
        
        Args:
            action_name: Name of the action to execute (e.g., "research.search")
            parameters: Parameters for the action
            
        Returns:
            ActionResult with normalized results
        """
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
            logger.error(f"Action execution failed: {e}")
            execution_time = int((time.time() - start_time) * 1000)
            return ActionResult(
                status=ActionStatus.FAILURE,
                query=parameters.get("query", ""),
                results=[],
                execution_time_ms=execution_time,
                errors=[str(e)]
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
    
    async def dispatch_action(self, schema: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch action to appropriate MCP service"""
        handler = schema["handler"]
        service = handler["service"]
        endpoint = handler["endpoint"]
        timeout_ms = handler.get("timeout_ms", 30000)
        
        if service not in self.mcp_clients:
            raise ValueError(f"Unknown service: {service}")
        
        client = self.mcp_clients[service]
        
        try:
            response = await client.post(
                endpoint,
                json=parameters,
                timeout=timeout_ms / 1000.0
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            raise Exception(f"Service {service} timed out after {timeout_ms}ms")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Service {service} returned {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Service {service} error: {str(e)}")
    
    def normalize_result(self, raw_result: Dict[str, Any], action_name: str, parameters: Dict[str, Any]) -> ActionResult:
        """Normalize raw service result to unified ActionResult format"""
        
        if action_name.startswith("research."):
            return self._normalize_research_result(raw_result, parameters)
        elif action_name.startswith("business."):
            return self._normalize_business_result(raw_result, parameters)
        elif action_name.startswith("code."):
            return self._normalize_code_result(raw_result, parameters)
        else:
            # Generic normalization
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
                confidence=0.8,  # Default confidence
                model="gpt-4",   # Default model
                sources=[{"title": r["title"], "url": r["url"]} for r in normalized_results[:3]]
            )
        
        return ActionResult(
            status=ActionStatus.SUCCESS if normalized_results else ActionStatus.PARTIAL,
            query=raw_result.get("query", parameters.get("query", "")),
            results=normalized_results,
            summary=summary
        )
    
    def _normalize_business_result(self, raw_result: Dict[str, Any], parameters: Dict[str, Any]) -> ActionResult:
        """Normalize business service results"""
        return ActionResult(
            status=ActionStatus.SUCCESS,
            query=parameters.get("title", ""),
            results=[raw_result]
        )
    
    def _normalize_code_result(self, raw_result: Dict[str, Any], parameters: Dict[str, Any]) -> ActionResult:
        """Normalize code service results"""
        return ActionResult(
            status=ActionStatus.SUCCESS,
            query=parameters.get("title", ""),
            results=[raw_result]
        )
    
    async def close(self):
        """Close all HTTP clients"""
        for client in self.mcp_clients.values():
            await client.aclose()

# Global action engine instance
_action_engine = None

async def get_action_engine() -> ActionEngine:
    """Get or create global action engine instance"""
    global _action_engine
    if _action_engine is None:
        _action_engine = ActionEngine()
    return _action_engine

async def execute_action(action_name: str, parameters: Dict[str, Any]) -> ActionResult:
    """Convenience function to execute an action"""
    engine = await get_action_engine()
    return await engine.execute_action(action_name, parameters)

