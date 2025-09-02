# MCP Integration Plan: Unified Memory & Assistant Ecosystem

## Executive Summary
This plan completes the MCP ecosystem by implementing the missing memory layer, assistant coordination, and Python client. It enables:
- Custom agents/swarms to interact with memory via MCP server
- External tools (Claude Desktop, Roo/Cursor, Cline.bot) to share memory
- Consistent configuration across all clients
- Full observability and testing

## Current State Analysis

| Component | Status | Gap |
|-----------|--------|-----|
| UnifiedMemoryStore | Missing | Required by EnhancedMCPServer and orchestrator |
| MCPAssistantCoordinator | Missing | Required by UnifiedOrchestratorFacade |
| Python Agent Client | Missing | Custom agents talk directly to memory |
| Configuration | Inconsistent | MCP_SERVER_URL, REDIS_URL, MCP_API_KEY not unified |
| External Clients | Partial | Adapters exist but need config updates |

## Implementation Plan (5 Days)

### Phase 1: Core Memory Layer (Day 1-2)

#### Task 1: Unified Memory Implementation
```python
# app/memory/unified_memory.py
from app.memory.supermemory_mcp import SupermemoryStore

class UnifiedMemoryStore:
    """Unified interface for memory operations"""
    
    def __init__(self, config: dict):
        self.supermemory = SupermemoryStore(config)
    
    async def initialize(self):
        await self.supermemory.initialize()
    
    async def store_memory(self, content: str, metadata: dict):
        return await self.supermemory.add_memory(content, metadata)
    
    async def search_memory(self, query: str, filters: dict = None):
        return await self.supermemory.search_memory(query, filters or {})
    
    async def update_memory(self, memory_id: str, content: str, metadata: dict):
        # Implementation using SupermemoryStore
        pass
    
    async def delete_memory(self, memory_id: str):
        # Implementation using SupermemoryStore
        pass
```

#### Task 2: Update References
```diff
# app/orchestration/unified_facade.py
- from app.memory import UnifiedMemoryStore
+ from app.memory import UnifiedMemoryStore

# app/mcp/server_v2.py
- from app.memory import UnifiedMemoryStore
+ from app.memory import UnifiedMemoryStore
```

### Phase 2: Assistant Coordination (Day 2-3)

#### Task 3: MCP Assistant Coordinator
```python
# app/mcp/assistant_coordinator.py
import httpx
from typing import Dict, Any

class MCPAssistantCoordinator:
    """Manages authentication and API calls for external assistants"""
    
    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url
        self.api_key = api_key
        self.token = None
    
    async def initialize(self):
        """Authenticate and get JWT token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/mcp/initialize",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            self.token = response.json()["token"]
    
    async def memory_store(self, content: str, metadata: dict):
        """Store memory via MCP server"""
        return await self._call_mcp("memory/store", {
            "content": content,
            "metadata": metadata
        })
    
    async def memory_search(self, query: str, filters: dict = None):
        """Search memory via MCP server"""
        return await self._call_mcp("memory/search", {
            "query": query,
            "filters": filters or {}
        })
    
    async def _call_mcp(self, endpoint: str, data: dict):
        """Generic MCP API call"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/mcp/{endpoint}",
                json=data,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            return response.json()
```

### Phase 3: Python Client & Configuration (Day 3-4)

#### Task 4: Python Agent Client
```python
# app/mcp/python_adapter.py
from app.mcp.assistant_coordinator import MCPAssistantCoordinator

class PythonAgentClient:
    """Python client for custom agents and swarms"""
    
    def __init__(self, server_url: str, api_key: str):
        self.coordinator = MCPAssistantCoordinator(server_url, api_key)
    
    async def initialize(self):
        await self.coordinator.initialize()
    
    async def store_memory(self, content: str, metadata: dict):
        return await self.coordinator.memory_store(content, metadata)
    
    async def search_memory(self, query: str, filters: dict = None):
        return await self.coordinator.memory_search(query, filters)
```

#### Task 5: Configuration Standardization
```python
# app/config/env_loader.py
import os
from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8003")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MCP_API_KEY = os.getenv("MCP_API_KEY", "default_key")
```

### Phase 4: Integration & Testing (Day 4-5)

#### Task 6: Integration Tests
```python
# tests/mcp/test_mcp_integration.py
import pytest
from app.mcp.python_adapter import PythonAgentClient

@pytest.mark.asyncio
async def test_memory_operations():
    client = PythonAgentClient(
        MCP_SERVER_URL,
        MCP_API_KEY
    )
    await client.initialize()
    
    # Store memory
    memory_id = await client.store_memory(
        "Test memory content",
        {"source": "test_agent"}
    )
    
    # Search memory
    results = await client.search_memory("Test")
    assert len(results) > 0
    assert results[0]["content"] == "Test memory content"
```

#### Task 7: External Client Configuration
| Client | Configuration File | Required Entry |
|--------|-------------------|---------------|
| Claude Desktop | `claude.config.json` | `"mcpServers": ["http://localhost:8003"]` |
| Roo/Cursor | `.cursor/mcp.json` | `{"servers": [{"url": "http://localhost:8003"}]}` |
| Cline.bot | `settings.json` | `"cline.mcp.servers": ["http://localhost:8003"]` |

## Success Metrics

| Metric | Target | Validation Method |
|--------|--------|------------------|
| Memory operations | 100% success rate | Integration tests |
| Configuration consistency | 100% across clients | Manual config review |
| API latency | < 200ms | Benchmark tests |
| Token authentication | 100% success | Test with invalid keys |
| Cross-client memory sharing | Works | Test from multiple clients |

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|------------|-------|
| Memory store failure | Fallback to direct SupermemoryStore | Lead Engineer |
| Token expiration | Automatic re-authentication | Coordinator |
| Config misconfiguration | Pre-start validation script | DevOps |
| API version mismatch | Versioned endpoints | API Team |

## Implementation Timeline

| Day | Tasks | Deliverables |
|-----|-------|-------------|
| 1 | UnifiedMemoryStore implementation | `unified_memory.py` |
| 2 | Update references, implement coordinator | `assistant_coordinator.py` |
| 3 | Python client, config standardization | `python_adapter.py`, `env_loader.py` |
| 4 | Integration tests, client configs | Test suite, config docs |
| 5 | Final validation, documentation | All tests passing, docs updated |

## Why This Plan Works

1. **Leverages Existing Code**: Uses SupermemoryStore as foundation instead of rebuilding
2. **Minimal Changes**: Only updates references to UnifiedMemoryStore
3. **Consistent Configuration**: Centralizes environment variables
4. **Test-Driven**: Includes concrete integration tests
5. **Client-Agnostic**: Works for all external clients and internal agents
6. **Observability Ready**: Integrates with existing logging/monitoring

## Next Steps

1. Implement `unified_memory.py` (Day 1)
2. Update all references to UnifiedMemoryStore (Day 1)
3. Implement `assistant_coordinator.py` (Day 2)
4. Create Python client (Day 3)
5. Write integration tests (Day 4)
6. Update client configurations (Day 5)

This plan directly addresses all gaps identified in the repository review and provides a clear path to a unified MCP ecosystem where all agents and external tools share a single memory layer.