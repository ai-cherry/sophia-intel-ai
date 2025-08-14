# Mega Prompt: MCP Architecture Transition Implementation

## CONTEXT: CURRENT STATE
The Sophia Intel platform currently has a fragmented MCP (Model Context Protocol) implementation spread across various files:

1. `mcp_servers/unified_mcp_server.py`: Basic MCP server with context storage and retrieval
2. `mcp_servers/enhanced_unified_server.py`: Extended server with AI router integration
3. `mcp_servers/memory_service.py`: Qdrant vector database integration
4. `mcp_servers/notion_server.py`: Specialized Notion integration
5. `integrations/mcp_tools.py`: Client integration for semantic search and other MCP capabilities
6. `libs/mcp_client/*`: Client libraries for MCP servers
7. `rag/pipeline.py`: RAG implementation using MCP for semantic search

The current implementation lacks standardization, has inconsistent error handling, and doesn't provide a unified foundation for adding new SaaS integrations. Client libraries are tightly coupled to specific server implementations.

## GOAL: ASPIRATIONAL STATE
Create a comprehensive, modular, and standardized MCP Suite that:
1. Follows consistent patterns across all MCP services
2. Provides a common foundation for error handling, health checks, and resilience
3. Supports multiple SaaS integrations (Slack, Salesforce, HubSpot, etc.)
4. Has unified client interfaces
5. Implements proper telemetry and monitoring
6. Supports horizontal scaling

## YOUR TASK

Implement a standardized MCP Suite architecture following these four phases:

### Phase 1: Foundation and Reference Implementation
1. Create a shared foundation library:
   - Implement `mcp/saas/common/base_server.py` with standardized patterns
   - Add common models, auth, and error handling
   - Create health check and readiness endpoints

2. Implement Slack as the reference implementation:
   - Create `mcp/saas/slack/slack_server.py` using the common foundation
   - Implement context storage and search endpoints
   - Write tests in `tests/mcp/saas/test_slack.py`

### Phase 2: Core MCP Services
1. Implement these core service integrations:
   - Salesforce MCP (`mcp/saas/salesforce/`)
   - HubSpot MCP (`mcp/saas/hubspot/`)
   - Intercom MCP (`mcp/saas/intercom/`)
   - Notion MCP (`mcp/saas/notion/`) - migrate from current implementation

2. Each service should:
   - Follow the same patterns as the reference implementation
   - Handle service-specific data formats
   - Include comprehensive tests
   - Have proper documentation

### Phase 3: Enhanced Client Libraries
1. Update client libraries to support the new MCP architecture:
   - Create `libs/mcp_client/base_client.py` with common functionality
   - Implement service-specific clients (e.g., `libs/mcp_client/slack.py`)
   - Add service discovery and failover mechanisms

2. Enhance the integration layer:
   - Update `integrations/mcp_tools.py` for the new architecture
   - Create specialized integration modules per service

### Phase 4: Productivity Tools and Advanced Features
1. Implement task management integrations:
   - Asana MCP (`mcp/saas/asana/`)
   - Linear MCP (`mcp/saas/linear/`)
   - FactoryAI MCP (`mcp/saas/factoryai/`)

2. Enhance RAG capabilities:
   - Improve `rag/pipeline.py` to leverage all available MCP services
   - Add document processing capabilities
   - Implement cross-service search

## TECHNICAL SPECIFICATIONS AND CODE EXAMPLES

### Common Foundation (base_server.py)
```python
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from typing import Callable, Dict, Any, Optional, Type, List, Union
from pydantic import BaseModel, Field

class ContextRequest(BaseModel):
    """Base model for context storage requests"""
    session_id: str = Field(..., description="Session identifier")
    content: str = Field(..., description="Content to store")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    context_type: str = Field(default="general", description="Type of context")

class ContextResponse(BaseModel):
    """Standard response for context operations"""
    status: str
    id: str
    timestamp: Optional[float] = None

class SearchRequest(BaseModel):
    """Base model for context search requests"""
    query: str = Field(..., description="Search query")
    session_id: Optional[str] = Field(None, description="Session to search within")
    limit: int = Field(default=10, description="Maximum number of results")
    filters: Dict[str, Any] = Field(default={}, description="Additional search filters")

class SearchResponse(BaseModel):
    """Standard response for search operations"""
    results: List[Dict[str, Any]]
    count: int
    query: str

class BaseMCPServer:
    def __init__(self, title: str, description: str, version: str = "0.1.0"):
        self.app = FastAPI(
            title=title,
            description=description,
            version=version,
        )
        
        self._setup_middleware()
        self._setup_routes()
        self._setup_exception_handlers()
        
    def _setup_middleware(self):
        # CORS, logging, metrics, etc.
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @self.app.middleware("http")
        async def logging_middleware(request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(f"{request.method} {request.url.path} completed in {process_time:.4f}s")
            return response
            
    def _setup_routes(self):
        # Health checks
        @self.app.get("/health")
        async def health_check():
            return {"status": "ok", "service": self.app.title}
            
        @self.app.get("/ready")
        async def readiness_check():
            # Check dependencies (DB, etc.)
            return {"status": "ready", "service": self.app.title}
    
    def _setup_exception_handlers(self):
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            logger.error(f"HTTP error: {exc.detail}")
            return {"error": exc.detail, "status_code": exc.status_code}
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            logger.error(f"Unhandled exception: {str(exc)}")
            return {"error": "Internal server error", "status_code": 500}
    
    def register_route(self, path: str, method: str, handler: Callable, 
                       response_model=None, dependencies=None):
        route_params = {}
        if response_model:
            route_params["response_model"] = response_model
        if dependencies:
            route_params["dependencies"] = dependencies
            
        self.app.add_api_route(path, handler, methods=[method], **route_params)
```

### Reference Implementation (slack_server.py)
```python
from mcp.saas.common.base_server import (
    BaseMCPServer, ContextRequest, ContextResponse, 
    SearchRequest, SearchResponse
)
from mcp.saas.common.auth import api_key_auth
from typing import List, Dict, Any
from loguru import logger
import time
import os
import httpx

class SlackContextRequest(ContextRequest):
    """Slack-specific context request"""
    workspace_id: str = Field(..., description="Slack workspace ID")
    channel_id: Optional[str] = Field(None, description="Slack channel ID")
    thread_ts: Optional[str] = Field(None, description="Slack thread timestamp")

class SlackMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            title="Slack MCP Server",
            description="Model Context Protocol server for Slack integration",
        )
        self._setup_slack_routes()
        self._setup_slack_client()
        
    def _setup_slack_client(self):
        self.slack_token = os.getenv("SLACK_API_TOKEN")
        self.slack_client = httpx.AsyncClient(
            base_url="https://slack.com/api/",
            headers={"Authorization": f"Bearer {self.slack_token}"}
        )
        
    def _setup_slack_routes(self):
        # Store context
        self.register_route(
            "/slack/context",
            "POST",
            self.store_context,
            response_model=ContextResponse,
            dependencies=[Depends(api_key_auth)]
        )
        
        # Search context
        self.register_route(
            "/slack/search",
            "POST",
            self.search_context,
            response_model=SearchResponse,
            dependencies=[Depends(api_key_auth)]
        )
        
        # Slack-specific: Retrieve channel history
        self.register_route(
            "/slack/channels/{channel_id}/history",
            "GET",
            self.get_channel_history,
            dependencies=[Depends(api_key_auth)]
        )
        
    async def store_context(self, request: SlackContextRequest):
        """Store Slack conversation context"""
        logger.info(f"Storing context for Slack: {request.metadata}")
        
        # Implementation details for storing in vector DB
        context_id = f"slack_{request.workspace_id}_{int(time.time())}"
        
        # Additional processing for Slack-specific content
        
        return ContextResponse(
            status="success",
            id=context_id,
            timestamp=time.time()
        )
        
    async def search_context(self, request: SearchRequest):
        """Search Slack conversation context"""
        logger.info(f"Searching Slack context: {request.query}")
        
        # Implementation for searching (vector DB query)
        results = []  # Replace with actual search implementation
        
        return SearchResponse(
            results=results,
            count=len(results),
            query=request.query
        )
        
    async def get_channel_history(self, channel_id: str, limit: int = 100):
        """Slack-specific endpoint to fetch channel history"""
        logger.info(f"Fetching history for channel: {channel_id}")
        
        response = await self.slack_client.get(
            "conversations.history",
            params={"channel": channel_id, "limit": limit}
        )
        
        if response.status_code != 200:
            logger.error(f"Slack API error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Slack API error")
            
        data = response.json()
        if not data.get("ok", False):
            logger.error(f"Slack API error: {data.get('error')}")
            raise HTTPException(status_code=400, detail=data.get("error"))
            
        return {
            "messages": data.get("messages", []),
            "has_more": data.get("has_more", False)
        }

app = SlackMCPServer().app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

## SPECIFIC IMPLEMENTATION STEPS

1. Create the directory structure:
```
mkdir -p mcp/saas/{common,slack,salesforce,hubspot,intercom,notion,asana,linear,factoryai}
mkdir -p tests/mcp/saas
touch mcp/saas/__init__.py
touch mcp/saas/common/__init__.py
```

2. Implement the common foundation:
   - Create base_server.py
   - Implement models.py
   - Add auth.py with authentication middleware
   - Create utils.py for shared functionality

3. Build the Slack reference implementation:
   - Implement slack_server.py
   - Create models specific to Slack
   - Add integration with the Slack API

4. Write tests for the Slack implementation:
   - Unit tests for core functionality
   - Integration tests with mocked Slack API

5. Systematically implement each additional service:
   - Follow the same pattern as Slack
   - Adapt to service-specific requirements
   - Write comprehensive tests

6. Update client libraries:
   - Create a base client class
   - Implement service-specific clients
   - Ensure backward compatibility

7. Update the integration layer:
   - Modify mcp_tools.py to use the new architecture
   - Add support for all implemented services

8. Enhance RAG capabilities:
   - Update pipeline.py to leverage the new architecture
   - Add cross-service search functionality

9. Document the architecture and usage patterns:
   - Create README.md files in each directory
   - Add examples for common use cases

## DELIVERABLES

1. Complete MCP Suite with:
   - Shared foundation library
   - Reference implementation (Slack)
   - Core service integrations
   - Enhanced client libraries
   - Integration layer updates
   - RAG improvements

2. Comprehensive test suite covering:
   - Unit tests for all components
   - Integration tests for services
   - End-to-end tests for key workflows

3. Documentation:
   - Architecture overview
   - Integration guides
   - Usage examples
   - API documentation

## CODING STANDARDS

1. Follow PEP 8 and project-specific style guidelines
2. Use type hints for all function signatures
3. Add docstrings for all classes and functions
4. Use async/await for I/O operations
5. Implement proper error handling and logging
6. Write comprehensive tests for all functionality
7. Use dependency injection for flexible components

Please implement this plan systematically, starting with the foundation and reference implementation, and then expanding to cover all required services. Focus on quality, maintainability, and consistency across the entire MCP Suite.
