# Dashboard Integration Implementation Plan for Sophia-Intel-AI

## Overview
This plan details the selective integration of beneficial dashboard patterns from AG-UI into the sophia-intel-ai repository. The approach emphasizes building visual layers over existing robust infrastructure while preserving the dual orchestrator pattern and domain boundaries.

**Core Principle**: Enhance, don't replace. Build visual interfaces that leverage existing APIs and infrastructure.

## Architecture

### High-Level Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ENHANCED DASHBOARD LAYER                  │
│            (New Visual Components & Interfaces)              │
├─────────────────────────────────────────────────────────────┤
│  Model Registry │ Prompt Library │ Tool Registry │ Event Bus│
│    (Visual)     │   (Visual)     │   (Visual)    │ (Adapter)│
└────────┬────────┴───────┬────────┴──────┬────────┴────┬─────┘
         │                │                │             │
    ┌────▼────┐    ┌──────▼─────┐  ┌──────▼──────┐ ┌───▼────┐
    │ Portkey │    │  Mythology │  │     MCP     │ │WebSocket│
    │  Config │    │   Agents   │  │   Router    │ │ Manager │
    └─────────┘    └────────────┘  └─────────────┘ └─────────┘
         ↓                ↓                ↓             ↓
    EXISTING INFRASTRUCTURE (PRESERVED & ENHANCED)
```

## Implementation Steps

### Phase 1: Foundation Enhancement (Days 1-3)

#### 1.1 Model Registry Visual Interface

**Target Files:**
- `/agent-ui/src/components/sophia/ModelRegistry.tsx` (NEW)
- `/agent-ui/src/hooks/usePortkeyModels.ts` (NEW)
- `/app/core/portkey_config.py` (ENHANCE)

**Implementation:**

```typescript
// /agent-ui/src/components/sophia/ModelRegistry.tsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { usePortkeyModels } from '@/hooks/usePortkeyModels';
import { 
  Cpu, DollarSign, Zap, Shield, 
  TrendingUp, AlertCircle, CheckCircle 
} from 'lucide-react';

interface ModelCardProps {
  provider: string;
  models: string[];
  status: 'active' | 'degraded' | 'offline';
  metrics: {
    avgLatency: number;
    successRate: number;
    costPerToken: number;
    dailyUsage: number;
  };
  capabilities: string[];
}

export const ModelRegistry: React.FC = () => {
  const { models, testConnection, getProviderStatus } = usePortkeyModels();
  const [selectedRole, setSelectedRole] = useState<AgentRole>('strategic');
  const [testResults, setTestResults] = useState<Record<string, boolean>>({});

  const testProvider = async (provider: string) => {
    const result = await testConnection(provider);
    setTestResults(prev => ({ ...prev, [provider]: result }));
  };

  return (
    <div className="space-y-6">
      {/* Role-Based Model Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Model Selection by Agent Role</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(roleModelMappings).map(([role, providers]) => (
              <div 
                key={role}
                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                  selectedRole === role ? 'border-blue-500 bg-blue-50' : ''
                }`}
                onClick={() => setSelectedRole(role)}
              >
                <h4 className="font-medium">{role}</h4>
                <div className="mt-2 space-x-2">
                  {providers.map(p => (
                    <Badge key={p} variant="secondary">{p}</Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Provider Health Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {models.map((model) => (
          <ModelCard 
            key={model.provider}
            {...model}
            onTest={() => testProvider(model.provider)}
            testResult={testResults[model.provider]}
          />
        ))}
      </div>

      {/* Cost Optimization Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Cost Optimization Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded">
              <span>Switch coding tasks to DeepSeek for 70% cost reduction</span>
              <Button size="sm">Apply</Button>
            </div>
            <div className="flex items-center justify-between p-3 bg-yellow-50 rounded">
              <span>Use Groq for real-time responses (3x faster)</span>
              <Button size="sm" variant="outline">Review</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
```

```python
# Enhancement to /app/core/portkey_config.py
class PortkeyManager:
    # ... existing code ...
    
    def get_model_metrics(self, provider: ModelProvider) -> Dict[str, Any]:
        """Get real-time metrics for a model provider"""
        return {
            "provider": provider.value,
            "models": self.providers[provider].models,
            "status": self._check_provider_status(provider),
            "metrics": {
                "avgLatency": self._get_avg_latency(provider),
                "successRate": self._get_success_rate(provider),
                "costPerToken": self._get_cost_per_token(provider),
                "dailyUsage": self._get_daily_usage(provider)
            },
            "capabilities": self._get_provider_capabilities(provider),
            "fallbacks": [p.value for p in self.providers[provider].fallback_providers]
        }
    
    def get_role_recommendations(self, role: AgentRole) -> List[Dict[str, Any]]:
        """Get optimized provider recommendations for a role"""
        providers = self.role_mappings[role]
        recommendations = []
        
        for provider in providers:
            metrics = self.get_model_metrics(provider)
            score = self._calculate_provider_score(provider, role)
            recommendations.append({
                "provider": provider.value,
                "score": score,
                "reason": self._get_recommendation_reason(provider, role),
                "metrics": metrics
            })
        
        return sorted(recommendations, key=lambda x: x["score"], reverse=True)
```

#### 1.2 Prompt Library Integration

**Target Files:**
- `/agent-ui/src/components/sophia/PromptLibrary.tsx` (NEW)
- `/app/sophia/prompt_templates.py` (NEW)
- `/app/artemis/prompt_templates.py` (NEW)

**Implementation:**

```typescript
// /agent-ui/src/components/sophia/PromptLibrary.tsx
export const PromptLibrary: React.FC = () => {
  const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('athena');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const mythologyAgents = [
    { id: 'athena', name: 'Athena', domain: 'Strategic Wisdom' },
    { id: 'hermes', name: 'Hermes', domain: 'Communication' },
    { id: 'apollo', name: 'Apollo', domain: 'Insights' },
    { id: 'hephaestus', name: 'Hephaestus', domain: 'Technical Creation' }
  ];

  return (
    <div className="space-y-6">
      {/* Agent-Specific Prompt Templates */}
      <Card>
        <CardHeader>
          <CardTitle>Mythology Agent Templates</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={selectedAgent} onValueChange={setSelectedAgent}>
            <TabsList>
              {mythologyAgents.map(agent => (
                <TabsTrigger key={agent.id} value={agent.id}>
                  {agent.name}
                </TabsTrigger>
              ))}
            </TabsList>
            
            {mythologyAgents.map(agent => (
              <TabsContent key={agent.id} value={agent.id}>
                <PromptTemplateList 
                  agentId={agent.id}
                  templates={prompts.filter(p => p.agentId === agent.id)}
                  onEdit={handleEditPrompt}
                  onTest={handleTestPrompt}
                />
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* Prompt Performance Analytics */}
      <Card>
        <CardHeader>
          <CardTitle>Template Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <PromptAnalytics 
            templates={prompts}
            metrics={{
              avgCompletionTime: 2.3,
              successRate: 94.5,
              userSatisfaction: 4.7,
              tokenEfficiency: 0.82
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
};
```

```python
# /app/sophia/prompt_templates.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

@dataclass
class PromptTemplate:
    """Enhanced prompt template with metadata and versioning"""
    id: str
    agent_id: str
    name: str
    description: str
    template: str
    variables: List[str]
    category: str
    version: str
    performance_metrics: Dict[str, float]
    tags: List[str]
    
class MythologyPromptLibrary:
    """Centralized prompt management for mythology agents"""
    
    def __init__(self):
        self.templates = {
            "athena": {
                "strategic_analysis": PromptTemplate(
                    id="athena_strat_001",
                    agent_id="athena",
                    name="Strategic Market Analysis",
                    description="Comprehensive market positioning analysis",
                    template="""
                    As Athena, goddess of strategic wisdom, analyze the following:
                    
                    Market Context: {market_context}
                    Competitive Landscape: {competitors}
                    Internal Capabilities: {capabilities}
                    
                    Provide strategic recommendations focusing on:
                    1. Market positioning opportunities
                    2. Competitive advantages to leverage
                    3. Risk mitigation strategies
                    4. Long-term growth pathways
                    
                    Format the response with clear sections and actionable insights.
                    """,
                    variables=["market_context", "competitors", "capabilities"],
                    category="strategy",
                    version="1.2.0",
                    performance_metrics={
                        "avg_completion_time": 3.2,
                        "success_rate": 0.96,
                        "user_rating": 4.8
                    },
                    tags=["strategy", "market_analysis", "competitive"]
                ),
                "risk_assessment": PromptTemplate(
                    id="athena_risk_001",
                    agent_id="athena",
                    name="Strategic Risk Assessment",
                    description="Identify and evaluate strategic risks",
                    template="""
                    Evaluate strategic risks for the following scenario:
                    
                    Context: {context}
                    Proposed Action: {action}
                    Timeline: {timeline}
                    
                    Assess:
                    - Probability of key risks
                    - Potential impact severity
                    - Mitigation strategies
                    - Contingency plans
                    """,
                    variables=["context", "action", "timeline"],
                    category="risk",
                    version="1.1.0",
                    performance_metrics={
                        "avg_completion_time": 2.8,
                        "success_rate": 0.94,
                        "user_rating": 4.7
                    },
                    tags=["risk", "assessment", "mitigation"]
                )
            },
            "hermes": {
                "client_communication": PromptTemplate(
                    id="hermes_comm_001",
                    agent_id="hermes",
                    name="Client Communication Optimizer",
                    description="Optimize client messaging for clarity and impact",
                    template="""
                    As Hermes, messenger of the gods, craft the perfect communication:
                    
                    Recipient: {recipient}
                    Context: {context}
                    Key Message: {message}
                    Desired Outcome: {outcome}
                    
                    Create a communication that:
                    - Is clear and concise
                    - Addresses recipient concerns
                    - Drives desired action
                    - Maintains professional tone
                    """,
                    variables=["recipient", "context", "message", "outcome"],
                    category="communication",
                    version="2.0.1",
                    performance_metrics={
                        "avg_completion_time": 1.5,
                        "success_rate": 0.97,
                        "user_rating": 4.9
                    },
                    tags=["communication", "client", "messaging"]
                )
            }
        }
    
    def get_template(self, agent_id: str, template_name: str) -> Optional[PromptTemplate]:
        """Retrieve a specific prompt template"""
        agent_templates = self.templates.get(agent_id, {})
        return agent_templates.get(template_name)
    
    def get_agent_templates(self, agent_id: str) -> List[PromptTemplate]:
        """Get all templates for a specific agent"""
        return list(self.templates.get(agent_id, {}).values())
    
    def update_metrics(self, template_id: str, metrics: Dict[str, float]):
        """Update performance metrics for a template"""
        # Find and update template metrics
        for agent_templates in self.templates.values():
            for template in agent_templates.values():
                if template.id == template_id:
                    template.performance_metrics.update(metrics)
                    return True
        return False
```

### Phase 2: Tool Registry & MCP Visualization (Days 4-6)

#### 2.1 Visual Tool Registry

**Target Files:**
- `/agent-ui/src/components/sophia/ToolRegistry.tsx` (NEW)
- `/agent-ui/src/components/sophia/MCPRouterVisualization.tsx` (NEW)
- `/app/api/mcp_dashboard.py` (NEW)

**Implementation:**

```typescript
// /agent-ui/src/components/sophia/MCPRouterVisualization.tsx
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import ReactFlow, { Node, Edge, Background, Controls } from 'reactflow';

export const MCPRouterVisualization: React.FC = () => {
  const [routerConfig, setRouterConfig] = useState<MCPRouterConfig>();
  const [domainFilter, setDomainFilter] = useState<'all' | 'artemis' | 'sophia'>('all');
  
  // Convert MCP config to flow diagram
  const generateFlowDiagram = (config: MCPRouterConfig) => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    
    // Domain nodes
    nodes.push(
      { id: 'artemis', position: { x: 100, y: 100 }, data: { label: 'Artemis Domain' }, style: { background: '#3B82F6' } },
      { id: 'sophia', position: { x: 100, y: 300 }, data: { label: 'Sophia Domain' }, style: { background: '#8B5CF6' } },
      { id: 'shared', position: { x: 300, y: 200 }, data: { label: 'Shared Resources' }, style: { background: '#10B981' } }
    );
    
    // Server nodes
    config.servers.forEach((server, idx) => {
      const domain = server.metadata.domain || 'shared';
      const x = domain === 'artemis' ? 400 : domain === 'sophia' ? 400 : 600;
      const y = 100 + (idx * 60);
      
      nodes.push({
        id: server.name,
        position: { x, y },
        data: {
          label: (
            <div className="p-2">
              <div className="font-semibold">{server.name}</div>
              <div className="text-xs text-gray-500">{server.endpoint}</div>
              <div className="mt-1">
                {server.healthStatus === 'healthy' ? (
                  <Badge variant="success">Healthy</Badge>
                ) : (
                  <Badge variant="destructive">Unhealthy</Badge>
                )}
              </div>
            </div>
          )
        },
        style: {
          background: server.healthStatus === 'healthy' ? '#F3F4F6' : '#FEE2E2',
          border: `2px solid ${domain === 'artemis' ? '#3B82F6' : domain === 'sophia' ? '#8B5CF6' : '#10B981'}`
        }
      });
      
      // Connect to domain
      edges.push({
        id: `${domain}-${server.name}`,
        source: domain === 'shared' ? 'shared' : domain,
        target: server.name,
        animated: server.activeConnections > 0
      });
    });
    
    return { nodes, edges };
  };
  
  return (
    <div className="space-y-6">
      {/* MCP Server Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Artemis Servers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {routerConfig?.servers
                .filter(s => s.metadata.domain === 'artemis')
                .map(server => (
                  <ServerStatusCard key={server.name} server={server} />
                ))}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Sophia Servers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {routerConfig?.servers
                .filter(s => s.metadata.domain === 'sophia')
                .map(server => (
                  <ServerStatusCard key={server.name} server={server} />
                ))}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Shared Resources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {routerConfig?.servers
                .filter(s => s.metadata.domain === 'shared')
                .map(server => (
                  <ServerStatusCard key={server.name} server={server} />
                ))}
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Interactive Flow Diagram */}
      <Card>
        <CardHeader>
          <CardTitle>MCP Routing Architecture</CardTitle>
        </CardHeader>
        <CardContent>
          <div style={{ height: '500px' }}>
            <ReactFlow
              nodes={flowDiagram.nodes}
              edges={flowDiagram.edges}
              fitView
            >
              <Background />
              <Controls />
            </ReactFlow>
          </div>
        </CardContent>
      </Card>
      
      {/* Connection Pool Analytics */}
      <Card>
        <CardHeader>
          <CardTitle>Connection Pool Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {routerConfig?.servers.map(server => (
              <div key={server.name} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{server.name}</span>
                  <span className="text-xs text-gray-500">
                    {server.activeConnections}/{server.maxConnections} connections
                  </span>
                </div>
                <Progress 
                  value={(server.activeConnections / server.maxConnections) * 100} 
                  className="h-2"
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
```

```python
# /app/api/mcp_dashboard.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.mcp.router_config import MCPRouterConfiguration, MCPServerType, MemoryDomain

router = APIRouter(prefix="/api/mcp", tags=["mcp_dashboard"])

class MCPDashboardService:
    """Service for MCP dashboard visualization and monitoring"""
    
    def __init__(self):
        self.router_config = MCPRouterConfiguration()
    
    async def get_router_visualization(self) -> Dict[str, Any]:
        """Get router configuration for visualization"""
        servers = []
        
        for name, config in self.router_config.server_configs.items():
            servers.append({
                "name": name,
                "serverType": config.server_type.value,
                "endpoint": config.endpoint,
                "metadata": config.metadata,
                "capabilities": config.capabilities,
                "healthStatus": "healthy" if self.router_config.health_status.get(name) else "unhealthy",
                "connectionPool": {
                    "min": config.connection_pool.min_connections,
                    "max": config.connection_pool.max_connections,
                    "active": self.router_config._get_active_connections(name),
                    "idle": config.connection_pool.idle_timeout
                },
                "activeConnections": self.router_config._get_active_connections(name),
                "maxConnections": config.connection_pool.max_connections
            })
        
        routing_rules = []
        for server_type, rule in self.router_config.routing_rules.items():
            routing_rules.append({
                "serverType": server_type.value,
                "allowedDomains": [d.value for d in rule.allowed_domains],
                "priority": rule.priority,
                "loadBalancing": rule.load_balancing,
                "filters": rule.filters
            })
        
        return {
            "servers": servers,
            "routingRules": routing_rules,
            "summary": self.router_config.get_routing_summary()
        }
    
    async def test_routing(
        self,
        server_type: str,
        domain: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test routing for a specific request"""
        try:
            server_type_enum = MCPServerType(server_type)
            domain_enum = MemoryDomain(domain)
            
            result = await self.router_config.route_request(
                server_type_enum,
                domain_enum,
                request_data
            )
            
            return {
                "success": result is not None,
                "routedTo": result,
                "reason": "Successfully routed" if result else "No available server or access denied"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

mcp_service = MCPDashboardService()

@router.get("/visualization")
async def get_mcp_visualization():
    """Get MCP router visualization data"""
    return await mcp_service.get_router_visualization()

@router.post("/test-routing")
async def test_mcp_routing(request: Dict[str, Any]):
    """Test MCP routing for a specific request"""
    return await mcp_service.test_routing(
        request.get("serverType"),
        request.get("domain"),
        request.get("requestData", {})
    )
```

### Phase 3: Event Bus Integration & Monitoring (Days 7-9)

#### 3.1 Selective Event Bus Adoption

**Target Files:**
- `/app/core/event_adapter.py` (NEW)
- `/agent-ui/src/hooks/useEventBus.ts` (NEW)
- `/agent-ui/src/components/sophia/EventMonitor.tsx` (NEW)

**Implementation:**

```python
# /app/core/event_adapter.py
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio
from app.core.websocket_manager import WebSocketManager
import logging

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Standardized event structure"""
    id: str
    type: str
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]

class EventAdapter:
    """
    Adapter to bridge AG-UI event patterns with existing WebSocket infrastructure
    Selective adoption of beneficial event patterns without disrupting current flow
    """
    
    def __init__(self):
        self.ws_manager = WebSocketManager()
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.event_filters: Dict[str, Callable] = {}
        self.event_history: List[Event] = []
        self.max_history = 1000
        
    async def emit(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "system",
        broadcast: bool = False
    ) -> None:
        """
        Emit an event through both event bus and WebSocket channels
        
        Args:
            event_type: Type of event (e.g., 'model.selected', 'prompt.executed')
            data: Event payload
            source: Source of the event
            broadcast: Whether to broadcast to all connected clients
        """
        event = Event(
            id=self._generate_event_id(),
            type=event_type,
            source=source,
            timestamp=datetime.utcnow(),
            data=data,
            metadata={
                "broadcast": broadcast,
                "version": "1.0"
            }
        )
        
        # Store in history
        self._add_to_history(event)
        
        # Execute registered handlers
        await self._execute_handlers(event)
        
        # Broadcast via WebSocket if needed
        if broadcast:
            await self.ws_manager.broadcast({
                "type": "event",
                "event": event_type,
                "data": data,
                "timestamp": event.timestamp.isoformat()
            })
        
        logger.debug(f"Event emitted: {event_type} from {source}")
    
    def on(self, event_type: str, handler: Callable) -> None:
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def off(self, event_type: str, handler: Callable) -> None:
        """Unregister an event handler"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].remove(handler)
    
    async def _execute_handlers(self, event: Event) -> None:
        """Execute all handlers for an event"""
        handlers = self.event_handlers.get(event.type, [])
        
        # Apply filters if any
        if event.type in self.event_filters:
            if not self.event_filters[event.type](event):
                return
        
        # Execute handlers concurrently
        tasks = [handler(event) for handler in handlers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def add_filter(self, event_type: str, filter_func: Callable[[Event], bool]) -> None:
        """Add a filter for specific event types"""
        self.event_filters[event_type] = filter_func
    
    def _add_to_history(self, event: Event) -> None:
        """Add event to history with size limit"""
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
    
    def get_history(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get filtered event history"""
        history = self.event_history
        
        if event_type:
            history = [e for e in history if e.type == event_type]
        
        if source:
            history = [e for e in history if e.source == source]
        
        return history[-limit:]
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        import uuid
        return str(uuid.uuid4())

# Global event adapter instance
event_adapter = EventAdapter()

# Pre-registered event types for dashboard
DASHBOARD_EVENTS = {
    "MODEL_SELECTED": "dashboard.model.selected",
    "PROMPT_EXECUTED": "dashboard.prompt.executed",
    "TOOL_INVOKED": "dashboard.tool.invoked",
    "AGENT_ACTIVATED": "dashboard.agent.activated",
    "METRIC_UPDATED": "dashboard.metric.updated",
    "ALERT_TRIGGERED": "dashboard.alert.triggered",
    "CONNECTION_STATUS": "dashboard.connection.status"
}
```

```typescript
// /agent-ui/src/hooks/useEventBus.ts
import { useEffect, useCallback, useState } from 'react';
import { useWebSocket } from './useWebSocket';

interface EventBusOptions {
  filter?: (event: any) => boolean;
  transform?: (event: any) => any;
  debounce?: number;
}

export const useEventBus = (eventTypes: string[], options?: EventBusOptions) => {
  const { ws, connected } = useWebSocket();
  const [events, setEvents] = useState<any[]>([]);
  const [lastEvent, setLastEvent] = useState<any>(null);
  
  const emit = useCallback((type: string, data: any) => {
    if (!connected || !ws) return;
    
    ws.send(JSON.stringify({
      type: 'event',
      event: type,
      data,
      timestamp: new Date().toISOString()
    }));
  }, [ws, connected]);
  
  useEffect(() => {
    if (!ws || !connected) return;
    
    const handleMessage = (event: MessageEvent) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'event' && eventTypes.includes(message.event)) {
        // Apply filter if provided
        if (options?.filter && !options.filter(message)) {
          return;
        }
        
        // Apply transformation if provided
        const processedEvent = options?.transform 
          ? options.transform(message) 
          : message;
        
        setLastEvent(processedEvent);
        setEvents(prev => [...prev.slice(-99), processedEvent]);
      }
    };
    
    ws.addEventListener('message', handleMessage);
    
    return () => {
      ws.removeEventListener('message', handleMessage);
    };
  }, [ws, connected, eventTypes, options]);
  
  return {
    events,
    lastEvent,
    emit,
    connected
  };
};
```

### Phase 4: Dashboard Enhancement Integration (Days 10-12)

#### 4.1 Unified Dashboard with New Components

**Target Files:**
- `/agent-ui/src/app/sophia/page.tsx` (ENHANCE)
- `/agent-ui/src/components/sophia/UnifiedDashboard.tsx` (NEW)

**Implementation:**

```typescript
// /agent-ui/src/components/sophia/UnifiedDashboard.tsx
import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ModelRegistry } from './ModelRegistry';
import { PromptLibrary } from './PromptLibrary';
import { MCPRouterVisualization } from './MCPRouterVisualization';
import { EventMonitor } from './EventMonitor';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Brain, Layers, Network, Activity, 
  Zap, Eye, Settings, TrendingUp 
} from 'lucide-react';

export const UnifiedDashboard: React.FC = () => {
  const [activeView, setActiveView] = useState('overview');
  
  return (
    <div className="space-y-6">
      {/* Quick Status Bar */}
      <div className="grid grid-cols-4 gap-4">
        <StatusCard
          title="Active Models"
          value="12"
          change="+3"
          icon={<Brain className="w-4 h-4" />}
          color="blue"
        />
        <StatusCard
          title="MCP Servers"
          value="11/11"
          change="100%"
          icon={<Network className="w-4 h-4" />}
          color="green"
        />
        <StatusCard
          title="Events/min"
          value="247"
          change="+12%"
          icon={<Activity className="w-4 h-4" />}
          color="purple"
        />
        <StatusCard
          title="Cost Saved"
          value="$1,247"
          change="+18%"
          icon={<TrendingUp className="w-4 h-4" />}
          color="emerald"
        />
      </div>
      
      {/* Main Dashboard Tabs */}
      <Card>
        <CardHeader>
          <CardTitle>Intelligence Infrastructure</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeView} onValueChange={setActiveView}>
            <TabsList className="grid grid-cols-5 w-full">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="models">Model Registry</TabsTrigger>
              <TabsTrigger value="prompts">Prompt Library</TabsTrigger>
              <TabsTrigger value="mcp">MCP Router</TabsTrigger>
              <TabsTrigger value="events">Event Monitor</TabsTrigger>
            </TabsList>
            
            <TabsContent value="overview" className="mt-6">
              <DashboardOverview />
            </TabsContent>
            
            <TabsContent value="models" className="mt-6">
              <ModelRegistry />
            </TabsContent>
            
            <TabsContent value="prompts" className="mt-6">
              <PromptLibrary />
            </TabsContent>
            
            <TabsContent value="mcp" className="mt-6">
              <MCPRouterVisualization />
            </TabsContent>
            
            <TabsContent value="events" className="mt-6">
              <EventMonitor />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};
```

## Technical Considerations

### 1. Preservation of Existing Architecture

```yaml
preserved_components:
  dual_orchestrators:
    artemis: "Technical domain orchestrator"
    sophia: "Business domain orchestrator"
    separation: "Maintained with clear boundaries"
  
  memory_architecture:
    tier_1: "Operational Memory (Redis)"
    tier_2: "Working Memory (PostgreSQL)"
    tier_3: "Long-term Memory (S3/Archive)"
    tier_4: "Semantic Memory (Vector DB)"
  
  infrastructure:
    websocket_manager: "Existing real-time communication"
    message_bus: "Redis-backed messaging"
    mcp_router: "Domain-aware routing preserved"
```

### 2. Integration Points

```python
integration_strategy = {
    "visual_layer": {
        "approach": "Build on top, don't replace",
        "components": ["ModelRegistry", "PromptLibrary", "ToolRegistry"],
        "apis": "Leverage existing REST and WebSocket endpoints"
    },
    "event_system": {
        "approach": "Selective adoption via adapter",
        "preserved": "WebSocket Manager primary communication",
        "enhanced": "Event bus for dashboard-specific events"
    },
    "data_flow": {
        "existing": "Maintain current data pipelines",
        "new": "Add visualization endpoints only",
        "caching": "Use existing Redis infrastructure"
    }
}
```

### 3. Performance Optimization

```typescript
const performanceOptimizations = {
  lazyLoading: {
    components: ["ModelRegistry", "PromptLibrary"],
    strategy: "Load on tab activation"
  },
  caching: {
    modelMetrics: "5 minute TTL",
    mcpStatus: "30 second TTL",
    promptTemplates: "1 hour TTL"
  },
  websocketOptimization: {
    subscriptions: "Component-specific channels",
    batching: "100ms debounce for updates",
    compression: "Enable for large payloads"
  }
};
```

## Testing Strategy

### 1. Unit Testing
```bash
# New test files
/tests/unit/test_model_registry_api.py
/tests/unit/test_prompt_library.py
/tests/unit/test_event_adapter.py
/tests/unit/test_mcp_dashboard.py
```

### 2. Integration Testing
```python
# Test integration points
async def test_model_registry_portkey_integration():
    """Test Model Registry uses actual Portkey config"""
    
async def test_prompt_library_agent_integration():
    """Test Prompt Library works with mythology agents"""
    
async def test_mcp_visualization_router_sync():
    """Test MCP visualization reflects actual router state"""
```

### 3. Performance Testing
```yaml
performance_targets:
  dashboard_load: "< 2 seconds"
  model_switch: "< 500ms"
  event_latency: "< 100ms"
  mcp_status_update: "< 1 second"
```

## Deployment Plan

### Phase 1: Backend APIs (Day 1)
- Deploy model metrics endpoints
- Deploy prompt library API
- Deploy MCP dashboard service
- Deploy event adapter

### Phase 2: Frontend Components (Day 2)
- Deploy ModelRegistry component
- Deploy PromptLibrary component
- Deploy MCPRouterVisualization
- Deploy EventMonitor

### Phase 3: Integration (Day 3)
- Wire up components to Sophia dashboard
- Test end-to-end flows
- Performance optimization
- Documentation update

## Success Metrics

```yaml
success_criteria:
  technical:
    - "Zero disruption to existing functionality"
    - "All new components load < 2 seconds"
    - "API response times < 200ms p95"
    - "WebSocket latency < 100ms"
  
  user_experience:
    - "Model selection 3x faster"
    - "Prompt management centralized"
    - "MCP routing visible and debuggable"
    - "Event flow traceable"
  
  business_value:
    - "20% reduction in LLM costs via optimization"
    - "50% faster debugging with visual tools"
    - "30% improvement in prompt quality"
    - "Real-time infrastructure monitoring"
```

## Risk Mitigation

```yaml
risks:
  - risk: "Performance degradation"
    mitigation: "Lazy loading, caching, progressive enhancement"
  
  - risk: "Breaking existing flows"
    mitigation: "Adapter pattern, careful integration testing"
  
  - risk: "Complexity increase"
    mitigation: "Clear separation of concerns, documentation"
  
  - risk: "WebSocket overload"
    mitigation: "Selective subscriptions, batching, throttling"
```

## Conclusion

This implementation plan provides a structured approach to enhancing the sophia-intel-ai dashboard with beneficial patterns from AG-UI while preserving the existing robust architecture. The plan emphasizes:

1. **Visual Enhancement**: Building intuitive interfaces over existing APIs
2. **Selective Adoption**: Taking only the beneficial patterns via adapters
3. **Architecture Preservation**: Maintaining dual orchestrators and domain boundaries
4. **Incremental Value**: Delivering improvements without disruption

The implementation can be completed in 12 days with clear phases, testing strategies, and success metrics.

## Ideas and Observations

1. **Unified Monitoring Dashboard**: Consider adding a unified monitoring view that shows the health of both Sophia and Artemis domains side-by-side, making it easier to spot cross-domain issues or optimization opportunities.

2. **Prompt Version Control**: The prompt library could benefit from Git-like versioning with branching and merging capabilities, allowing teams to experiment with prompt variations without affecting production.

3. **Cost Prediction API**: Building on the model registry, adding a cost prediction endpoint that estimates the cost of a task before execution could help teams make more informed decisions about model selection.