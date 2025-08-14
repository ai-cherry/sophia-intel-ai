# Sophia Intel MCP Architecture Transition

## Current State Analysis

The Sophia Intel platform currently implements MCP (Model Context Protocol) services through several specialized servers in the `mcp_servers` directory:

1. **unified_mcp_server.py**: A basic MCP server implementing context storage and retrieval
2. **enhanced_unified_server.py**: An expanded server with AI router integration and more features
3. **memory_service.py**: A service layer for Qdrant vector database integration
4. **notion_server.py**: A specialized MCP server for Notion integration
5. **ai_router.py**: Logic for routing AI requests to appropriate models/services

The integration between clients and these MCP servers is managed through:
- `libs/mcp_client/*`: Client libraries for interacting with MCP servers
- `integrations/mcp_tools.py`: Integration layer providing semantic search and other MCP capabilities

Current RAG implementation (`rag/pipeline.py`) relies on MCP services for semantic search with fallback mechanisms.

## Aspirational State

We aim to build a comprehensive, modular, and standardized MCP Suite architecture that:

1. **Follows standardized patterns** across all MCP services
2. **Provides a common foundation** for error handling, health checks, and resilience
3. **Delivers specialized SaaS integrations** (Slack, Salesforce, HubSpot, etc.)
4. **Offers unified client interfaces** for seamless integration
5. **Implements proper telemetry and monitoring**
6. **Supports horizontal scaling** for production workloads

## Implementation Plan

### Phase 1: Foundation and Reference Implementation

1. Create a shared foundation library at `mcp/saas/common/`:
   - Base HTTP server with standardized error handling
   - Health check and readiness endpoints
   - Common authentication patterns
   - Standardized logging and telemetry
   - Request rate limiting and circuit breakers
   - Consistent response schemas

2. Develop a reference implementation for Slack:
   - Implement `mcp/saas/slack/` directory
   - Create `slack_server.py` using the common foundation
   - Include comprehensive tests in `tests/mcp/saas/test_slack.py`
   - Document API contract and usage patterns

### Phase 2: Core MCP Services

1. Implement core service integrations:
   - Salesforce MCP (`mcp/saas/salesforce/`)
   - HubSpot MCP (`mcp/saas/hubspot/`)
   - Intercom MCP (`mcp/saas/intercom/`)
   - Notion MCP (`mcp/saas/notion/`) (migrating from current implementation)

2. For each service:
   - Create a dedicated server module
   - Implement specialized endpoints for service-specific features
   - Add complete test coverage
   - Provide usage examples and documentation

### Phase 3: Enhanced Client Libraries

1. Update client libraries to support the new MCP architecture:
   - Refactor `libs/mcp_client/sophia_client.py` to use the new MCP endpoints
   - Create service-specific client modules (e.g., `libs/mcp_client/slack.py`)
   - Implement automatic service discovery and failover mechanisms
   - Add client-side caching for improved performance

2. Enhance integration layer:
   - Update `integrations/mcp_tools.py` to leverage the new client libraries
   - Create specialized integration modules for each service type
   - Add performance monitoring and telemetry

### Phase 4: Productivity Tools

1. Implement task management integrations:
   - Asana MCP (`mcp/saas/asana/`)
   - Linear MCP (`mcp/saas/linear/`)
   - FactoryAI MCP (`mcp/saas/factoryai/`)

2. Enhance RAG capabilities:
   - Improve `rag/pipeline.py` to use all available MCP services for context
   - Add document chunking and processing capabilities
   - Implement cross-service search for comprehensive results
   - Create specialized retrieval pipelines for different content types

## Technical Specifications

### HTTP Server Foundation

```python
# mcp/saas/common/base_server.py

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from typing import Callable, Dict, Any

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
        # Custom exception handling
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            logger.error(f"HTTP error: {exc.detail}")
            return {"error": exc.detail, "status_code": exc.status_code}
    
    def register_route(self, path: str, method: str, handler: Callable, 
                       response_model=None, dependencies=None):
        # Helper for adding routes with consistent patterns
        route_params = {}
        if response_model:
            route_params["response_model"] = response_model
        if dependencies:
            route_params["dependencies"] = dependencies
            
        self.app.add_api_route(path, handler, methods=[method], **route_params)
```

### Reference Implementation for Slack

```python
# mcp/saas/slack/slack_server.py

from mcp.saas.common.base_server import BaseMCPServer
from mcp.saas.common.models import ContextRequest, ContextResponse, SearchRequest
from mcp.saas.common.auth import api_key_auth
from typing import List, Dict, Any
from loguru import logger

class SlackMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            title="Slack MCP Server",
            description="Model Context Protocol server for Slack integration",
        )
        self._setup_slack_routes()
        
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
            dependencies=[Depends(api_key_auth)]
        )
        
    async def store_context(self, request: ContextRequest):
        # Implementation for storing Slack-specific context
        logger.info(f"Storing context for Slack: {request.metadata}")
        # Actual implementation logic here
        return {"status": "success", "id": "generated-id-here"}
        
    async def search_context(self, request: SearchRequest):
        # Implementation for searching Slack-specific context
        logger.info(f"Searching Slack context: {request.query}")
        # Actual implementation logic here
        return {"results": [], "count": 0}

app = SlackMCPServer().app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

## Execution Strategy

1. **Begin with the foundation**:
   - Create the common module structure
   - Implement the base server class
   - Develop shared models and authentication

2. **Build the reference implementation (Slack MCP)**:
   - Use it to validate the foundation
   - Document patterns for other services to follow

3. **Migrate existing implementations**:
   - Move Notion MCP to the new structure
   - Refactor the enhanced unified server components

4. **Add new services incrementally**:
   - Implement one service at a time
   - Add tests before moving to the next service

5. **Update client libraries and integration layer**:
   - Ensure backward compatibility
   - Add new features that leverage the modular architecture

6. **Complete documentation and examples**:
   - Create usage guides for each service
   - Document the overall architecture

## Success Criteria

1. All MCP services follow the standardized pattern
2. Comprehensive test coverage for each service
3. Documentation for integration and usage
4. Improved performance and resilience metrics
5. Successful deployment to production environment

## Next Steps

1. Create the directory structure for the new MCP Suite
2. Implement the shared foundation library
3. Begin work on the Slack reference implementation
4. Set up continuous integration tests
5. Begin migrating existing services to the new pattern

This implementation will transform the current MCP architecture into a robust, modular system that can easily integrate with multiple SaaS platforms while maintaining consistent patterns and high reliability.
