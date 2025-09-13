# AI Agent Observability & Integration Framework

## Executive Summary
This framework makes the entire Sophia Intel AI infrastructure observable and actionable by AI agents through semantic APIs, self-documenting endpoints, and intelligent context management.

## 🎯 Core Design Principles

1. **Self-Describing Systems**: Every endpoint documents itself with examples
2. **Semantic Discovery**: Agents can discover capabilities through natural language
3. **Context Preservation**: Agent decisions and observations are tracked
4. **Tool-First Design**: APIs designed for LLM tool use, not just humans
5. **Observable by Default**: All state changes emit events agents can monitor

## 📊 Architecture Components

### 1. Agent Gateway API
```python
# app/api/routers/agent_gateway.py
from typing import Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter(prefix="/api/agent", tags=["agent"])

class AgentQuery(BaseModel):
    """Natural language query from an AI agent"""
    query: str
    agent_id: str
    context: Dict[str, Any] = {}
    capabilities_needed: List[str] = []

class AgentResponse(BaseModel):
    """Structured response for AI agents"""
    answer: str
    actions_available: List[Dict[str, Any]]
    relevant_endpoints: List[str]
    context_updates: Dict[str, Any]
    examples: List[str]

@router.post("/query")
async def agent_query(query: AgentQuery) -> AgentResponse:
    """
    Natural language interface for agents to discover capabilities
    
    Examples:
    - "How do I check if all services are healthy?"
    - "What's the current system status?"
    - "Start the MCP memory service"
    - "Show me failed services"
    """
    # Semantic routing to appropriate endpoints
    pass

@router.get("/capabilities")
async def get_capabilities():
    """
    Returns all available capabilities in agent-friendly format
    """
    return {
        "capabilities": {
            "service_management": {
                "description": "Start, stop, restart, and monitor services",
                "endpoints": [
                    {
                        "path": "/api/services/status",
                        "method": "GET",
                        "description": "Get status of all services",
                        "returns": "ServiceStatus[]",
                        "example_response": {...}
                    }
                ],
                "natural_language_triggers": [
                    "check service status",
                    "are services running",
                    "show system health"
                ]
            },
            "configuration": {
                "description": "Read and update system configuration",
                "endpoints": [...],
                "natural_language_triggers": [...]
            }
        }
    }

@router.get("/context/{agent_id}")
async def get_agent_context(agent_id: str):
    """
    Retrieve preserved context for a specific agent
    """
    return {
        "agent_id": agent_id,
        "last_seen": "2025-01-10T21:30:00Z",
        "recent_actions": [...],
        "system_state_snapshot": {...},
        "relevant_logs": [...]
    }
```

### 2. Semantic Service Discovery
```python
# app/core/semantic_discovery.py
import asyncio
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticServiceDiscovery:
    """Enable agents to discover services through natural language"""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.service_embeddings = {}
        self.capability_descriptions = {}
        
    async def initialize(self):
        """Build semantic index of all services and capabilities"""
        from app.core.service_registry import ServiceRegistry
        
        for service_name, service_def in ServiceRegistry.SERVICES.items():
            # Create semantic descriptions
            descriptions = [
                f"{service_name} service",
                service_def.description,
                f"Port {service_def.port}",
                *service_def.tags
            ]
            
            # Generate embeddings
            embeddings = self.model.encode(descriptions)
            self.service_embeddings[service_name] = embeddings
            self.capability_descriptions[service_name] = descriptions
    
    async def find_relevant_services(self, query: str, top_k: int = 5) -> List[Dict]:
        """Find services relevant to a natural language query"""
        query_embedding = self.model.encode([query])
        
        scores = {}
        for service_name, embeddings in self.service_embeddings.items():
            # Compute similarity
            similarities = np.dot(embeddings, query_embedding.T)
            scores[service_name] = np.max(similarities)
        
        # Return top services
        top_services = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        return [
            {
                "service": name,
                "relevance": float(score),
                "description": self.capability_descriptions[name][1],
                "actions": self._get_service_actions(name)
            }
            for name, score in top_services
        ]
    
    def _get_service_actions(self, service_name: str) -> List[Dict]:
        """Get available actions for a service"""
        return [
            {"action": "start", "endpoint": f"/api/services/{service_name}/start"},
            {"action": "stop", "endpoint": f"/api/services/{service_name}/stop"},
            {"action": "status", "endpoint": f"/api/services/status/{service_name}"},
            {"action": "logs", "endpoint": f"/api/services/{service_name}/logs"}
        ]
```

### 3. Agent Context Management
```python
# app/core/agent_context.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import asyncio
from collections import deque

class AgentContextManager:
    """Manages context and history for AI agents"""
    
    def __init__(self):
        self.contexts: Dict[str, AgentContext] = {}
        self.global_events = deque(maxlen=1000)
        self.agent_observations = {}
        
    def get_or_create_context(self, agent_id: str) -> 'AgentContext':
        if agent_id not in self.contexts:
            self.contexts[agent_id] = AgentContext(agent_id)
        return self.contexts[agent_id]
    
    async def record_observation(self, agent_id: str, observation: Dict[str, Any]):
        """Record what an agent observed"""
        context = self.get_or_create_context(agent_id)
        context.add_observation(observation)
        
        # Broadcast to other agents if important
        if observation.get('severity') == 'critical':
            await self.broadcast_to_agents(observation, exclude=agent_id)
    
    async def get_relevant_context(self, agent_id: str, query: str) -> Dict[str, Any]:
        """Get context relevant to agent's current query"""
        context = self.get_or_create_context(agent_id)
        
        return {
            "personal_history": context.get_recent_history(),
            "system_events": self.get_recent_system_events(),
            "other_agent_observations": self.get_relevant_observations(query),
            "current_system_state": await self.get_system_snapshot()
        }
    
    async def broadcast_to_agents(self, event: Dict[str, Any], exclude: Optional[str] = None):
        """Broadcast important events to all active agents"""
        for agent_id, context in self.contexts.items():
            if agent_id != exclude and context.is_active():
                context.add_notification(event)

class AgentContext:
    """Individual agent's context and history"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.observations = deque(maxlen=100)
        self.actions = deque(maxlen=50)
        self.notifications = deque(maxlen=20)
        self.preferences = {}
        
    def add_observation(self, observation: Dict[str, Any]):
        self.observations.append({
            "timestamp": datetime.now().isoformat(),
            "data": observation
        })
        self.last_active = datetime.now()
    
    def add_action(self, action: str, result: Any):
        self.actions.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "result": result
        })
        self.last_active = datetime.now()
    
    def is_active(self) -> bool:
        return (datetime.now() - self.last_active) < timedelta(minutes=30)
```

### 4. Observable Event System
```python
# app/core/observable_events.py
from typing import List, Callable, Any
import asyncio
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_FAILED = "service_failed"
    CONFIG_CHANGED = "config_changed"
    HEALTH_CHECK_FAILED = "health_check_failed"
    PERFORMANCE_DEGRADED = "performance_degraded"
    AGENT_ACTION = "agent_action"

@dataclass
class SystemEvent:
    type: EventType
    service: str
    data: Dict[str, Any]
    timestamp: datetime
    severity: str  # info, warning, error, critical
    agent_relevant: bool = True

class ObservableEventBus:
    """Event bus that agents can subscribe to"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history = deque(maxlen=5000)
        self.agent_filters: Dict[str, List[EventType]] = {}
        
    async def emit(self, event: SystemEvent):
        """Emit an event to all subscribers"""
        self.event_history.append(event)
        
        # Notify subscribers
        for agent_id, callback in self.subscribers.items():
            if self.should_notify_agent(agent_id, event):
                await callback(event)
    
    def subscribe(self, agent_id: str, callback: Callable, event_types: List[EventType] = None):
        """Subscribe an agent to events"""
        self.subscribers[agent_id] = callback
        if event_types:
            self.agent_filters[agent_id] = event_types
    
    def should_notify_agent(self, agent_id: str, event: SystemEvent) -> bool:
        """Check if agent should be notified of event"""
        if not event.agent_relevant:
            return False
        
        if agent_id in self.agent_filters:
            return event.type in self.agent_filters[agent_id]
        
        return True
    
    def get_recent_events(self, 
                         event_types: List[EventType] = None,
                         severity: str = None,
                         limit: int = 100) -> List[SystemEvent]:
        """Query recent events"""
        events = list(self.event_history)
        
        if event_types:
            events = [e for e in events if e.type in event_types]
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        return events[-limit:]
```

### 5. Agent-Friendly Documentation
```python
# app/api/routers/agent_docs.py
from fastapi import APIRouter
from typing import Dict, Any, List

router = APIRouter(prefix="/api/agent/docs", tags=["agent-docs"])

@router.get("/")
async def get_agent_documentation():
    """
    Returns documentation specifically formatted for AI agents
    """
    return {
        "system_overview": {
            "name": "Sophia Intel AI",
            "purpose": "Unified Business Intelligence Platform",
            "key_capabilities": [
                "Service orchestration",
                "Health monitoring",
                "Configuration management",
                "MCP integration",
                "Real-time observability"
            ]
        },
        "how_to_use": {
            "discovery": "Use /api/agent/query with natural language",
            "actions": "Call specific endpoints returned in discovery",
            "monitoring": "Subscribe to /api/agent/events for real-time updates",
            "context": "Your context is preserved at /api/agent/context/{your_id}"
        },
        "common_tasks": [
            {
                "task": "Check system health",
                "steps": [
                    "GET /api/services/health",
                    "Parse response for unhealthy services",
                    "GET /api/services/status/{service} for details"
                ],
                "example_code": "curl http://localhost:8000/api/services/health"
            },
            {
                "task": "Start a service",
                "steps": [
                    "Check dependencies: GET /api/services/dependencies",
                    "Start service: POST /api/services/{name}/start",
                    "Verify: GET /api/services/status/{name}"
                ]
            }
        ],
        "best_practices": [
            "Always check service dependencies before starting",
            "Subscribe to events for services you're managing",
            "Store important observations for other agents",
            "Use semantic discovery for finding capabilities"
        ]
    }

@router.get("/examples/{task}")
async def get_task_examples(task: str):
    """
    Get examples for specific tasks
    """
    examples = {
        "health_monitoring": {
            "description": "Monitor system health",
            "curl_examples": [...],
            "python_examples": [...],
            "expected_responses": [...]
        },
        "service_management": {...},
        "configuration": {...}
    }
    return examples.get(task, {"error": "Unknown task"})
```

### 6. MCP Server for Agent Tools
```python
# mcp/agent_tools_server.py
"""
MCP server that exposes all Sophia capabilities as tools for agents
"""
from mcp import MCPServer, Tool, Resource
import httpx

class SophiaAgentMCPServer(MCPServer):
    def __init__(self):
        super().__init__("sophia-agent-tools")
        self.base_url = "http://localhost:8000"
        
    async def list_tools(self) -> List[Tool]:
        return [
            Tool(
                name="check_service_health",
                description="Check health of all services",
                parameters={
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "Optional specific service"}
                    }
                }
            ),
            Tool(
                name="manage_service",
                description="Start, stop, or restart a service",
                parameters={
                    "type": "object",
                    "properties": {
                        "service": {"type": "string"},
                        "action": {"type": "string", "enum": ["start", "stop", "restart"]}
                    },
                    "required": ["service", "action"]
                }
            ),
            Tool(
                name="query_system",
                description="Natural language query about system state",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_logs",
                description="Get recent logs for a service",
                parameters={
                    "type": "object",
                    "properties": {
                        "service": {"type": "string"},
                        "lines": {"type": "integer", "default": 100}
                    },
                    "required": ["service"]
                }
            )
        ]
    
    async def execute_tool(self, name: str, arguments: dict) -> dict:
        async with httpx.AsyncClient() as client:
            if name == "check_service_health":
                response = await client.get(f"{self.base_url}/api/services/health")
                return response.json()
            
            elif name == "manage_service":
                service = arguments["service"]
                action = arguments["action"]
                response = await client.post(
                    f"{self.base_url}/api/services/{service}/{action}"
                )
                return response.json()
            
            elif name == "query_system":
                response = await client.post(
                    f"{self.base_url}/api/agent/query",
                    json={"query": arguments["query"], "agent_id": "mcp"}
                )
                return response.json()
```

## 🚀 Implementation Plan

### Phase 1: Core Observability (Day 1-2)
1. Implement Observable Event Bus
2. Add event emissions to all service state changes
3. Create agent gateway API
4. Set up agent context management

### Phase 2: Semantic Discovery (Day 3-4)
1. Build semantic service discovery
2. Create natural language query endpoint
3. Generate service embeddings
4. Implement similarity search

### Phase 3: Agent Integration (Day 5-6)
1. Create MCP server for agent tools
2. Build agent documentation system
3. Implement context preservation
4. Add example generators

### Phase 4: Advanced Features (Day 7-8)
1. Multi-agent coordination
2. Agent learning from observations
3. Predictive suggestions
4. Anomaly detection for agents

## 📊 Usage Examples

### For Claude/GPT/Other LLMs
```python
# Agent discovers capabilities
response = await client.post("/api/agent/query", json={
    "query": "How do I monitor system health?",
    "agent_id": "claude-001"
})

# Agent subscribes to events
await client.websocket("/api/agent/events", params={
    "agent_id": "claude-001",
    "event_types": ["SERVICE_FAILED", "HEALTH_CHECK_FAILED"]
})

# Agent takes action based on observation
if event.type == "SERVICE_FAILED":
    await client.post(f"/api/services/{event.service}/restart")
```

### For MCP-Enabled Agents
```python
# Tools automatically available
mcp_client.use_tool("check_service_health")
mcp_client.use_tool("manage_service", {"service": "redis", "action": "restart"})
```

### For Monitoring Agents
```python
# Continuous monitoring
async for event in event_stream:
    if event.severity == "critical":
        await notify_human(event)
        await attempt_auto_recovery(event)
```

## 🎯 Key Benefits

1. **Zero Learning Curve**: Agents can discover everything through natural language
2. **Context Preservation**: Agents don't lose track between sessions
3. **Multi-Agent Coordination**: Agents can share observations
4. **Self-Documenting**: Every endpoint explains itself with examples
5. **Event-Driven**: Agents can react to system changes in real-time
6. **Tool-Ready**: Direct integration with LLM tool-use capabilities

## 📈 Metrics & Monitoring

Track agent effectiveness:
- Query success rate
- Action completion rate
- Context retrieval accuracy
- Event response time
- Cross-agent collaboration frequency

## 🔒 Security Considerations

1. **Agent Authentication**: Each agent has unique ID and permissions
2. **Action Validation**: Verify agent actions before execution
3. **Rate Limiting**: Prevent agent abuse
4. **Audit Trail**: Log all agent actions
5. **Sandboxing**: Limit agent capabilities based on trust level

---

**Document Version**: 1.0.0
**Created**: 2025-01-10
**Status**: READY FOR IMPLEMENTATION