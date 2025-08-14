# Mega Prompt: Swarm-First MCP Architecture Implementation

## CURRENT STATE

The Sophia Intelligence platform currently implements:

1. **A Swarm System** - A production-ready multi-agent system with:
   - Linear deterministic workflow (architect → builder → tester → operator)
   - MCP-first RAG with cloud fallback
   - Comprehensive telemetry
   - No-BS tone filtering
   - Cloud-native architecture (Qdrant, Redis)

2. **Fragmented MCP Implementation** across multiple files:
   - `mcp_servers/unified_mcp_server.py`: Basic MCP server
   - `mcp_servers/enhanced_unified_server.py`: Extended server with AI router
   - `mcp_servers/memory_service.py`: Qdrant vector database integration
   - `mcp_servers/notion_server.py`: Specialized Notion integration
   - `integrations/mcp_tools.py`: Client integrations for semantic search
   - `libs/mcp_client/*`: Client libraries
   - `rag/pipeline.py`: RAG implementation using MCP for semantic search

The current implementation lacks standardization, has inconsistent error handling, and lacks a unified foundation for new SaaS integrations.

## ASPIRATIONAL STATE

Create a **Swarm-Integrated MCP Suite** that:

1. Maintains and enhances the existing Swarm System capabilities:
   - Preserves the linear deterministic workflow
   - Continues MCP-first RAG with enhanced features
   - Maintains comprehensive telemetry
   - Keeps the No-BS tone filtering
   - Strengthens cloud-native architecture

2. Delivers a standardized MCP architecture:
   - Common foundation for all MCP services
   - Consistent error handling, health checks, and resilience
   - Support for multiple SaaS integrations
   - Unified client interfaces
   - Enhanced telemetry and monitoring
   - Horizontal scaling capabilities

## YOUR TASK

Implement a standardized, Swarm-integrated MCP Suite following these phases:

### Phase 1: Foundation and Swarm Integration

1. Create a shared foundation library:
   - Implement `mcp/saas/common/base_server.py` with standardized patterns
   - Add common models, auth, and error handling
   - Create health check and readiness endpoints

2. Implement Swarm-MCP integration layer:
   - Create `mcp/saas/common/swarm_integration.py` to connect MCP with Swarm
   - Ensure compatibility with existing Swarm system
   - Support circuit breakers (hop limit, time limit, error limit)

3. Implement Slack as the reference implementation:
   - Create `mcp/saas/slack/slack_server.py` using the common foundation
   - Implement context storage and search endpoints
   - Add Swarm-specific endpoints for agent communication
   - Write tests in `tests/mcp/saas/test_slack.py`

### Phase 2: Core MCP Services with Swarm Awareness

1. Implement these core service integrations:
   - Salesforce MCP (`mcp/saas/salesforce/`)
   - HubSpot MCP (`mcp/saas/hubspot/`)
   - Intercom MCP (`mcp/saas/intercom/`)
   - Notion MCP (`mcp/saas/notion/`) - migrate from current implementation

2. Each service should:
   - Follow the same patterns as the reference implementation
   - Handle service-specific data formats
   - Support Swarm agent workflows
   - Include comprehensive tests
   - Have proper documentation

### Phase 3: Enhanced Client Libraries and Swarm Tools

1. Update client libraries to support the new MCP architecture:
   - Create `libs/mcp_client/base_client.py` with common functionality
   - Implement service-specific clients (e.g., `libs/mcp_client/slack.py`)
   - Add service discovery and failover mechanisms
   - Ensure Swarm compatibility and telemetry integration

2. Enhance the RAG pipeline:
   - Update `rag/pipeline.py` to use the new standardized MCP services
   - Improve cross-service context retrieval
   - Maintain fallback mechanisms (Qdrant Cloud, mock data)

### Phase 4: Advanced Features and Scaling

1. Implement task management integrations:
   - Asana MCP (`mcp/saas/asana/`)
   - Linear MCP (`mcp/saas/linear/`)
   - FactoryAI MCP (`mcp/saas/factoryai/`)

2. Add advanced monitoring and scaling features:
   - Implement log rotation for `.swarm_handoffs.log`
   - Add resource usage monitoring
   - Support horizontal scaling for production workloads

## TECHNICAL SPECIFICATIONS AND CODE EXAMPLES

### Common Foundation with Swarm Integration

```python
# mcp/saas/common/base_server.py
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from typing import Callable, Dict, Any, Optional, Type, List, Union
from pydantic import BaseModel, Field
import time
import os

class ContextRequest(BaseModel):
    """Base model for context storage requests"""
    session_id: str = Field(..., description="Session identifier")
    content: str = Field(..., description="Content to store")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    context_type: str = Field(default="general", description="Type of context")
    swarm_stage: Optional[str] = Field(None, description="Current swarm stage if applicable")

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
    swarm_stage: Optional[str] = Field(None, description="Current swarm stage if applicable")

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
        self._setup_swarm_integration()
        
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
            # Add to swarm telemetry if applicable
            if hasattr(self, 'swarm_telemetry') and callable(self.swarm_telemetry):
                await self.swarm_telemetry({
                    "endpoint": request.url.path,
                    "method": request.method,
                    "duration": process_time,
                    "timestamp": time.time()
                })
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
            # Record in swarm telemetry
            if hasattr(self, 'swarm_telemetry') and callable(self.swarm_telemetry):
                await self.swarm_telemetry({
                    "error": str(exc),
                    "endpoint": request.url.path,
                    "timestamp": time.time(),
                    "type": "exception"
                })
            return {"error": "Internal server error", "status_code": 500}
    
    def _setup_swarm_integration(self):
        """Setup Swarm integration if enabled"""
        if os.getenv("USE_SWARM", "1") == "1":
            try:
                from mcp.saas.common.swarm_integration import SwarmIntegration
                self.swarm = SwarmIntegration()
                self.swarm_telemetry = self.swarm.record_telemetry
                
                # Add Swarm-specific endpoints
                @self.app.post("/swarm/handoff")
                async def swarm_handoff(data: Dict[str, Any]):
                    return await self.swarm.process_handoff(data)
                
                @self.app.get("/swarm/status/{session_id}")
                async def swarm_status(session_id: str):
                    return await self.swarm.get_status(session_id)
                
                logger.info("Swarm integration enabled")
            except ImportError:
                logger.warning("Swarm integration requested but module not found")
    
    def register_route(self, path: str, method: str, handler: Callable, 
                       response_model=None, dependencies=None):
        route_params = {}
        if response_model:
            route_params["response_model"] = response_model
        if dependencies:
            route_params["dependencies"] = dependencies
            
        self.app.add_api_route(path, handler, methods=[method], **route_params)
```

### Swarm Integration Module

```python
# mcp/saas/common/swarm_integration.py
from typing import Dict, Any, Optional, List
import json
import time
import os
import asyncio
from datetime import datetime
from pathlib import Path
from loguru import logger

class SwarmIntegration:
    """Integration between MCP servers and Swarm system"""
    
    def __init__(self):
        self.handoff_log = os.getenv("SWARM_HANDOFFS_LOG", ".swarm_handoffs.log")
        self.max_hops = int(os.getenv("MAX_SWARM_HOPS", "12"))
        self.max_time_minutes = int(os.getenv("MAX_STAGE_TIME_MINUTES", "10"))
        self.max_errors = int(os.getenv("MAX_ERRORS", "3"))
        self.min_artifact_chars = int(os.getenv("MIN_ARTIFACT_CHARS", "50"))
        
        # Ensure log directory exists
        Path(self.handoff_log).parent.mkdir(exist_ok=True)
        
    async def record_telemetry(self, data: Dict[str, Any]) -> None:
        """Record telemetry to swarm handoffs log"""
        try:
            data["timestamp"] = data.get("timestamp", time.time())
            data["type"] = data.get("type", "mcp_telemetry")
            
            with open(self.handoff_log, "a") as f:
                f.write(json.dumps(data) + "\n")
        except Exception as e:
            logger.error(f"Failed to record telemetry: {e}")
    
    async def process_handoff(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a handoff between swarm agents"""
        session_id = data.get("session_id")
        from_stage = data.get("from_stage")
        to_stage = data.get("to_stage")
        artifact = data.get("artifact", "")
        
        # Record the handoff
        handoff_data = {
            "type": "handoff",
            "session_id": session_id,
            "from_stage": from_stage,
            "to_stage": to_stage,
            "artifact_size": len(artifact),
            "timestamp": time.time()
        }
        
        # Apply circuit breakers
        circuit_breakers = await self._check_circuit_breakers(session_id)
        if circuit_breakers["broken"]:
            handoff_data["circuit_breaker"] = circuit_breakers["reason"]
            await self.record_telemetry(handoff_data)
            return {
                "status": "error",
                "error": f"Circuit breaker triggered: {circuit_breakers['reason']}",
                "session_id": session_id
            }
            
        # Validate artifact
        if len(artifact) < self.min_artifact_chars:
            handoff_data["circuit_breaker"] = "artifact_validation"
            await self.record_telemetry(handoff_data)
            return {
                "status": "error",
                "error": f"Artifact too small: {len(artifact)} chars (min: {self.min_artifact_chars})",
                "session_id": session_id
            }
            
        # Record successful handoff
        await self.record_telemetry(handoff_data)
        
        return {
            "status": "success",
            "session_id": session_id,
            "from_stage": from_stage,
            "to_stage": to_stage
        }
        
    async def get_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a swarm session"""
        # Implementation would read from handoffs log to reconstruct status
        try:
            handoffs = []
            with open(self.handoff_log, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if (data.get("session_id") == session_id and 
                            data.get("type") in ["handoff", "circuit_breaker"]):
                            handoffs.append(data)
                    except:
                        continue
                        
            if not handoffs:
                return {
                    "status": "not_found",
                    "session_id": session_id
                }
                
            # Sort by timestamp
            handoffs.sort(key=lambda x: x.get("timestamp", 0))
            
            # Determine current stage
            current_stage = handoffs[-1].get("to_stage", "unknown")
            if handoffs[-1].get("circuit_breaker"):
                current_stage = "terminated"
                
            return {
                "status": "active" if current_stage != "terminated" else "terminated",
                "session_id": session_id,
                "current_stage": current_stage,
                "hop_count": len(handoffs),
                "start_time": handoffs[0].get("timestamp"),
                "elapsed_seconds": time.time() - handoffs[0].get("timestamp", time.time())
            }
        except Exception as e:
            logger.error(f"Error getting swarm status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
    
    async def _check_circuit_breakers(self, session_id: str) -> Dict[str, Any]:
        """Check if any circuit breakers should trigger"""
        status = await self.get_status(session_id)
        
        # Already terminated
        if status.get("status") == "terminated":
            return {"broken": True, "reason": "already_terminated"}
            
        # Hop limit
        if status.get("hop_count", 0) >= self.max_hops:
            return {"broken": True, "reason": "hop_limit_exceeded"}
            
        # Time limit
        elapsed_minutes = status.get("elapsed_seconds", 0) / 60
        if elapsed_minutes >= self.max_time_minutes:
            return {"broken": True, "reason": "time_limit_exceeded"}
            
        # Count errors
        error_count = 0
        try:
            with open(self.handoff_log, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if (data.get("session_id") == session_id and 
                            data.get("type") == "error"):
                            error_count += 1
                    except:
                        continue
                        
            if error_count >= self.max_errors:
                return {"broken": True, "reason": "error_limit_exceeded"}
        except:
            pass
            
        return {"broken": False, "reason": None}
```

### Slack Reference Implementation (With Swarm Integration)

```python
# mcp/saas/slack/slack_server.py
from mcp.saas.common.base_server import (
    BaseMCPServer, ContextRequest, ContextResponse, 
    SearchRequest, SearchResponse
)
from mcp.saas.common.auth import api_key_auth
from fastapi import Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from loguru import logger
import time
import os
import httpx
import asyncio

class SlackContextRequest(ContextRequest):
    """Slack-specific context request"""
    workspace_id: str = Field(..., description="Slack workspace ID")
    channel_id: Optional[str] = Field(None, description="Slack channel ID")
    thread_ts: Optional[str] = Field(None, description="Slack thread timestamp")

class SwarmSlackMessage(BaseModel):
    """Message from Swarm to be sent to Slack"""
    channel: str
    text: str
    thread_ts: Optional[str] = None
    swarm_stage: str
    session_id: str

class SlackMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            title="Slack MCP Server",
            description="Model Context Protocol server for Slack integration with Swarm support",
        )
        self._setup_slack_client()
        self._setup_slack_routes()
        
    def _setup_slack_client(self):
        self.slack_token = os.getenv("SLACK_API_TOKEN")
        self.slack_client = httpx.AsyncClient(
            base_url="https://slack.com/api/",
            headers={"Authorization": f"Bearer {self.slack_token}"}
        )
        
    def _setup_slack_routes(self):
        # Standard MCP routes
        self.register_route(
            "/slack/context",
            "POST",
            self.store_context,
            response_model=ContextResponse,
            dependencies=[Depends(api_key_auth)]
        )
        
        self.register_route(
            "/slack/search",
            "POST",
            self.search_context,
            response_model=SearchResponse,
            dependencies=[Depends(api_key_auth)]
        )
        
        # Swarm-specific routes
        self.register_route(
            "/slack/swarm/message",
            "POST",
            self.send_swarm_message,
            dependencies=[Depends(api_key_auth)]
        )
        
        # Slack-specific routes
        self.register_route(
            "/slack/channels/{channel_id}/history",
            "GET",
            self.get_channel_history,
            dependencies=[Depends(api_key_auth)]
        )
        
    async def store_context(self, request: SlackContextRequest, background_tasks: BackgroundTasks):
        """Store Slack conversation context"""
        logger.info(f"Storing context for Slack: {request.metadata}")
        
        # Generate context ID
        context_id = f"slack_{request.workspace_id}_{int(time.time())}"
        
        # Store in vector database (would implement with Qdrant here)
        # ...
        
        # If part of Swarm flow, record in telemetry
        if request.swarm_stage:
            background_tasks.add_task(
                self.swarm_telemetry,
                {
                    "type": "context_storage",
                    "session_id": request.session_id,
                    "swarm_stage": request.swarm_stage,
                    "content_size": len(request.content),
                    "context_type": request.context_type
                }
            )
        
        return ContextResponse(
            status="success",
            id=context_id,
            timestamp=time.time()
        )
        
    async def search_context(self, request: SearchRequest):
        """Search Slack conversation context"""
        logger.info(f"Searching Slack context: {request.query}")
        
        # Implementation for searching (vector DB query)
        # This would use something like Qdrant's semantic search
        results = []  # Replace with actual search implementation
        
        # Example response format
        return SearchResponse(
            results=results,
            count=len(results),
            query=request.query
        )
    
    async def send_swarm_message(self, message: SwarmSlackMessage):
        """Send a message from Swarm to Slack"""
        logger.info(f"Sending Swarm message to Slack from stage {message.swarm_stage}")
        
        # Format the message with Swarm stage
        formatted_text = f"*[{message.swarm_stage.upper()}]* {message.text}"
        
        # Send to Slack
        params = {
            "channel": message.channel,
            "text": formatted_text,
        }
        
        if message.thread_ts:
            params["thread_ts"] = message.thread_ts
            
        response = await self.slack_client.post("chat.postMessage", json=params)
        
        if response.status_code != 200 or not response.json().get("ok", False):
            logger.error(f"Failed to send Slack message: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to send message to Slack")
            
        # Record in Swarm telemetry
        await self.swarm_telemetry({
            "type": "swarm_message",
            "session_id": message.session_id,
            "swarm_stage": message.swarm_stage,
            "channel": message.channel,
            "timestamp": time.time()
        })
        
        return {
            "status": "success",
            "ts": response.json().get("ts"),
            "channel": message.channel
        }
        
    async def get_channel_history(self, channel_id: str, limit: int = 100):
        """Fetch channel history from Slack"""
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

### Enhanced RAG Pipeline

```python
# rag/pipeline.py
import os, json
from functools import lru_cache
from integrations.mcp_tools import mcp_semantic_search

def _qdrant_search_fallback(query: str, k: int = 8):
    """Fallback Qdrant search without Haystack dependencies"""
    try:
        import qdrant_client
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        client = qdrant_client.QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        collection = os.getenv("QDRANT_COLLECTION", "repo_docs")
        
        # Simple text search without embeddings - basic implementation
        results = client.scroll(
            collection_name=collection,
            limit=k,
            with_payload=True,
            with_vectors=False
        )
        
        docs = []
        for point in results[0]:
            payload = point.payload or {}
            docs.append({
                "path": payload.get("path", ""),
                "content": payload.get("content", "")[:800],
                "score": 0.5,  # Default score since we can't do semantic search
                "source": "qdrant_fallback"
            })
        
        return docs[:k]
    except Exception as e:
        print(f"Qdrant fallback failed: {e}")
        return []

def repo_search(query: str, k: int = 8, swarm_stage: str = None):
    """Search repo using MCP first, then Qdrant fallback"""
    # Try MCP first - now with swarm stage awareness
    hits = mcp_semantic_search(query, k=k, swarm_stage=swarm_stage)
    if hits:
        for hit in hits:
            hit["source"] = hit.get("source", "mcp")
        return hits
    
    # Try Qdrant fallback
    fallback_hits = _qdrant_search_fallback(query, k=k)
    if fallback_hits:
        return fallback_hits
    
    # Return mock results for development
    return [{
        "path": "mock/development.py",
        "content": f"# Mock search result for query: {query}\n# This is returned when no search backend is available",
        "score": 0.1,
        "source": "mock"
    }]

def rag_tool(query: str, swarm_stage: str = None) -> str:
    """RAG tool with enhanced formatting and error handling"""
    try:
        k = int(os.getenv("RAG_TOPK", "8"))
        results = repo_search(query, k=k, swarm_stage=swarm_stage)
        
        formatted_results = {
            "query": query,
            "swarm_stage": swarm_stage,
            "result_count": len(results),
            "results": results[:k]
        }
        
        output = json.dumps(formatted_results, indent=2)
        max_chars = int(os.getenv("MAX_RAG_CHARS", "8000"))
        
        return output[:max_chars]
        
    except Exception as e:
        return json.dumps({"error": f"RAG tool failed: {str(e)}", "query": query})
```

### Updated MCP Tools Integration

```python
# integrations/mcp_tools.py
from __future__ import annotations
import os
from pathlib import Path

USE_MCP = os.getenv("USE_MCP", "1") == "1"
SESSION_DIR = Path(os.getenv("MCP_SESSION_DIR", ".sophia_sessions"))
SESSION_DIR.mkdir(parents=True, exist_ok=True)

def _noop(*args, **kwargs): return [] if "search" in kwargs or (args and isinstance(args[0], str)) else {}

# defaults (no-op if MCP not available or disabled)
mcp_semantic_search = lambda query, k=8, swarm_stage=None: []
mcp_file_map = lambda paths=None: {}
mcp_smart_hints = lambda tool_name, context="", swarm_stage=None: {}
def mcp_learn(event: dict) -> None: pass

if USE_MCP:
    try:
        # Try to import from the new standardized client library first
        try:
            from libs.mcp_client.base_client import BaseMCPClient
            from libs.mcp_client.session_manager import SessionManager
            
            _mgr = SessionManager(session_dir=str(SESSION_DIR))
            _sess = _mgr.start_or_resume()
            
            # Dynamically determine available MCP clients
            from importlib import import_module
            from pathlib import Path
            import pkgutil
            
            # List of potential MCP service clients to try
            service_names = ["slack", "notion", "salesforce", "hubspot", "intercom"]
            _clients = {}
            
            for service in service_names:
                try:
                    module = import_module(f"libs.mcp_client.{service}")
                    client_class = getattr(module, f"{service.capitalize()}Client")
                    _clients[service] = client_class(session=_sess)
                except (ImportError, AttributeError):
                    pass
                    
            # If no specific clients loaded, use base client
            if not _clients:
                _clients["default"] = BaseMCPClient(
                    code_context_transport=os.getenv("MCP_CODE_CONTEXT", "stdio"),
                    http_url=os.getenv("MCP_HTTP_URL", "")
                )
                
            def mcp_semantic_search(query: str, k: int = 8, swarm_stage: str = None) -> list[dict]:
                """Search across all available MCP clients"""
                all_results = []
                
                # Try each client, collect results
                for service, client in _clients.items():
                    try:
                        service_results = client.semantic_search(
                            query=query, 
                            k=k, 
                            swarm_stage=swarm_stage
                        ) or []
                        
                        # Tag results with source
                        for result in service_results:
                            result["source"] = service
                            
                        all_results.extend(service_results)
                    except Exception:
                        pass
                
                # Sort by score and return top k
                all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
                return all_results[:k]
                
            def mcp_file_map(paths: list[str] | None = None) -> dict:
                """Get file map from any available client"""
                for client in _clients.values():
                    try:
                        result = client.code_map(paths or [])
                        if result:
                            return result
                    except:
                        pass
                return {}
                
            def mcp_smart_hints(tool_name: str, context: str = "", swarm_stage: str = None) -> dict:
                """Get smart hints from any available client"""
                for client in _clients.values():
                    try:
                        result = client.next_actions(
                            tool_name=tool_name, 
                            context=context,
                            swarm_stage=swarm_stage
                        ) or {}
                        if result:
                            return result
                    except:
                        pass
                return {}
                
            def mcp_learn(event: dict) -> None:
                """Send learning events to all available clients"""
                # Add swarm_stage if missing but in environment
                if "swarm_stage" not in event and os.getenv("SWARM_CURRENT_STAGE"):
                    event["swarm_stage"] = os.getenv("SWARM_CURRENT_STAGE")
                    
                for client in _clients.values():
                    try:
                        client.learn(event)
                    except:
                        pass
                        
        except ImportError:
            # Fall back to legacy client library
            from libs.mcp_client.sophia_client import SophiaClient
            from libs.mcp_client.session_manager import SessionManager
            from libs.mcp_client.repo_intelligence import RepoIntelligence
            from libs.mcp_client.context_tools import ContextTools
            from libs.mcp_client.predictive_assistant import PredictiveAssistant
            from libs.mcp_client.performance_monitor import PerfMonitor

            _mgr = SessionManager(session_dir=str(SESSION_DIR))
            _sess = _mgr.start_or_resume()
            _cli  = SophiaClient(
                code_context_transport=os.getenv("MCP_CODE_CONTEXT", "stdio"),
                http_url=os.getenv("MCP_HTTP_URL", "")
            )
            _repo = RepoIntelligence(client=_cli, session=_sess)
            _ctx  = ContextTools(client=_cli, session=_sess)
            _pred = PredictiveAssistant(client=_cli, session=_sess)
            _perf = PerfMonitor(client=_cli, session=_sess)

            def mcp_semantic_search(query: str, k: int = 8, swarm_stage: str = None) -> list[dict]:
                # Legacy client doesn't support swarm_stage, ignore it
                return _repo.semantic_search(query=query, k=k) or []

            def mcp_file_map(paths: list[str] | None = None) -> dict:
                return _repo.code_map(paths or [])

            def mcp_smart_hints(tool_name: str, context: str = "", swarm_stage: str = None) -> dict:
                # Legacy client doesn't support swarm_stage, ignore it
                return _pred.next_actions(tool_name=tool_name, context=context) or {}

            def mcp_learn(event: dict) -> None:
                try:
                    _ctx.learn(event); _perf.record(event)
                except Exception:
                    pass
    except Exception:
        # If all else fails, use no-op functions
        pass
```

## IMPLEMENTATION STEPS

1. Create the directory structure:
```
mkdir -p mcp/saas/{common,slack,salesforce,hubspot,intercom,notion,asana,linear,factoryai}
mkdir -p tests/mcp/saas
touch mcp/saas/__init__.py
touch mcp/saas/common/__init__.py
```

2. Implement the common foundation:
   - Create base_server.py with Swarm integration
   - Implement models.py for standard requests/responses
   - Add auth.py for authentication
   - Create swarm_integration.py for Swarm connectivity

3. Build the Slack reference implementation:
   - Implement slack_server.py with Swarm awareness
   - Add Slack-specific endpoints

4. Write tests for the Slack implementation:
   - Unit tests for core functionality
   - Integration tests with mocked Slack API
   - Swarm workflow tests

5. Systematically implement each additional service:
   - Follow the same pattern as Slack
   - Ensure Swarm compatibility
   - Adapt to service-specific requirements
   - Write comprehensive tests

6. Update client libraries:
   - Create a base client class
   - Implement service-specific clients
   - Ensure backward compatibility
   - Add Swarm stage awareness

7. Update the RAG pipeline:
   - Modify pipeline.py to use the new architecture
   - Add Swarm stage-specific context retrieval
   - Maintain fallback mechanisms

8. Enhance Swarm integration:
   - Add telemetry recording in `.swarm_handoffs.log`
   - Implement circuit breakers
   - Support agent workflow stages

## DELIVERABLES

1. Complete MCP Suite with Swarm integration:
   - Shared foundation library
   - Swarm integration module
   - Reference implementation (Slack)
   - Core service integrations
   - Enhanced client libraries
   - Integration layer updates

2. Comprehensive test suite covering:
   - Unit tests for all components
   - Integration tests for services
   - Swarm workflow tests
   - End-to-end tests

3. Documentation:
   - Architecture overview
   - Integration guides with Swarm-specific instructions
   - Usage examples
   - API documentation

## CODING STANDARDS

1. Follow PEP 8 and project-specific style guidelines
2. Use type hints for all function signatures
3. Add docstrings for all classes and functions
4. Use async/await for I/O operations
5. Implement proper error handling and logging
6. Write comprehensive tests for all functionality
7. Ensure Swarm compatibility throughout

Start by implementing the foundation and reference implementation, focusing on quality, maintainability, consistency, and seamless integration with the existing Swarm system.
