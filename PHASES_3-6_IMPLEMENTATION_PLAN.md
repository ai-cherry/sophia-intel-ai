# Phases 3-6 Implementation Plan: Terminal-First Multi-Agent AI Coding Environment

## Executive Summary

This plan creates a unified terminal-first environment where multiple AI coding agents (Claude Coder, Grok, DeepSeek, Codex) coordinate via MCP servers, share memory/embeddings, access both sophia-intel-ai and artemis-cli repos, and enable natural language interaction through a web UI - all without touching host Python.

## Core Architecture

```
Terminal → Docker Containers → MCP Servers → Shared Memory → GitHub
         ↓                    ↓             ↓              ↓
    Agent Runtime      File/Git/Tools   Redis/Weaviate  SSH Forward
```

## Phase 3: Task-Aware LLM Router (Days 1-5)

### 3.1 Docker-Based Agent Testing Environment

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  # Development container for running agents
  agent-dev:
    image: python:3.11-slim
    container_name: sophia-agent-dev
    volumes:
      - ./:/workspace/sophia
      - ../artemis-cli:/workspace/artemis
      - ~/.ssh:/root/.ssh:ro
      - ${SSH_AUTH_SOCK}:${SSH_AUTH_SOCK}
    environment:
      - SSH_AUTH_SOCK=${SSH_AUTH_SOCK}
      - PYTHONPATH=/workspace/sophia:/workspace/artemis
    env_file: .env
    working_dir: /workspace/sophia
    networks:
      - sophia-network
    stdin_open: true
    tty: true
    command: /bin/bash

  # Redis for short-term memory
  redis:
    image: redis:7-alpine
    container_name: sophia-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - sophia-network

  # Weaviate for vector embeddings
  weaviate:
    image: semitechnologies/weaviate:latest
    container_name: sophia-weaviate
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
    volumes:
      - weaviate-data:/var/lib/weaviate
    networks:
      - sophia-network

networks:
  sophia-network:
    driver: bridge

volumes:
  redis-data:
  weaviate-data:
```

### 3.2 Quick Grok Test Script

```bash
#!/bin/bash
# scripts/test_grok_docker.sh

echo "Testing Grok integration in Docker..."

# Start services if not running
docker compose -f docker-compose.dev.yml up -d redis weaviate

# Run Grok test in container
docker compose -f docker-compose.dev.yml run --rm agent-dev bash -c "
  pip install -q -r requirements.txt && \
  python3 scripts/sophia.py agent grok \
    --mode code \
    --task 'Create a REST API endpoint' \
    --provider xai
"
```

### 3.3 LLM Router Implementation

```python
# packages/sophia_core/models/router.py

from typing import Dict, Optional, List, Any
from enum import Enum
import asyncio
from dataclasses import dataclass
import time

from ..exceptions import ProviderUnavailableError, RateLimitError
from ..utils.cbreaker import CircuitBreaker
from ..utils.retry import RetryManager, RetryConfig

class TaskType(Enum):
    FAST = "fast"           # Quick responses, simple queries
    REASON = "reason"       # Complex reasoning, analysis
    GENERAL = "general"     # General purpose tasks
    CODEGEN = "codegen"     # Code generation
    VISION = "vision"       # Image understanding
    JSON_MODE = "json_mode" # Structured output

@dataclass
class ModelConfig:
    provider: str
    model: str
    max_tokens: int
    temperature: float
    supports_vision: bool = False
    supports_json: bool = False
    cost_per_1k_tokens: float = 0.0

class TaskAwareRouter:
    """Routes tasks to appropriate LLM providers based on task type and availability"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.circuit_breakers = {}
        self.provider_metrics = {}
        
    def _initialize_providers(self) -> Dict[str, Dict[TaskType, ModelConfig]]:
        """Initialize provider configurations for different task types"""
        return {
            "groq": {
                TaskType.FAST: ModelConfig(
                    provider="groq", 
                    model="mixtral-8x7b-32768",
                    max_tokens=32768,
                    temperature=0.3,
                    cost_per_1k_tokens=0.27
                ),
                TaskType.CODEGEN: ModelConfig(
                    provider="groq",
                    model="llama-3.1-70b-versatile",
                    max_tokens=8192,
                    temperature=0.2,
                    cost_per_1k_tokens=0.59
                )
            },
            "anthropic": {
                TaskType.REASON: ModelConfig(
                    provider="anthropic",
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=8192,
                    temperature=0.5,
                    supports_vision=True,
                    cost_per_1k_tokens=3.0
                ),
                TaskType.CODEGEN: ModelConfig(
                    provider="anthropic",
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=8192,
                    temperature=0.2,
                    supports_vision=True,
                    cost_per_1k_tokens=3.0
                )
            },
            "openai": {
                TaskType.GENERAL: ModelConfig(
                    provider="openai",
                    model="gpt-4o",
                    max_tokens=4096,
                    temperature=0.7,
                    supports_vision=True,
                    supports_json=True,
                    cost_per_1k_tokens=5.0
                ),
                TaskType.VISION: ModelConfig(
                    provider="openai",
                    model="gpt-4o",
                    max_tokens=4096,
                    temperature=0.5,
                    supports_vision=True,
                    cost_per_1k_tokens=5.0
                )
            },
            "xai": {
                TaskType.REASON: ModelConfig(
                    provider="xai",
                    model="grok-beta",
                    max_tokens=131072,
                    temperature=0.5,
                    cost_per_1k_tokens=5.0
                ),
                TaskType.CODEGEN: ModelConfig(
                    provider="xai",
                    model="grok-beta",
                    max_tokens=131072,
                    temperature=0.2,
                    cost_per_1k_tokens=5.0
                )
            },
            "deepseek": {
                TaskType.CODEGEN: ModelConfig(
                    provider="deepseek",
                    model="deepseek-coder",
                    max_tokens=16384,
                    temperature=0.1,
                    cost_per_1k_tokens=0.14
                )
            }
        }
    
    async def route_task(
        self, 
        task_type: TaskType,
        prompt: str,
        fallback_providers: Optional[List[str]] = None
    ) -> Any:
        """Route task to appropriate provider with fallback"""
        
        # Get primary provider for task type
        primary_config = self._select_provider(task_type)
        
        try:
            return await self._execute_with_provider(primary_config, prompt)
        except (ProviderUnavailableError, RateLimitError) as e:
            # Try fallback providers
            if fallback_providers:
                for provider_name in fallback_providers:
                    if provider_name in self.providers:
                        fallback_config = self.providers[provider_name].get(task_type)
                        if fallback_config:
                            try:
                                return await self._execute_with_provider(
                                    fallback_config, prompt
                                )
                            except Exception:
                                continue
            raise e
    
    def _select_provider(self, task_type: TaskType) -> ModelConfig:
        """Select best provider for task type based on availability and cost"""
        
        candidates = []
        
        for provider_name, configs in self.providers.items():
            if task_type in configs:
                # Check circuit breaker
                breaker = self.circuit_breakers.get(provider_name)
                if not breaker or not breaker.is_open:
                    candidates.append(configs[task_type])
        
        if not candidates:
            raise ProviderUnavailableError("all", "No providers available")
        
        # Sort by cost and select cheapest available
        candidates.sort(key=lambda x: x.cost_per_1k_tokens)
        return candidates[0]
    
    async def _execute_with_provider(
        self, 
        config: ModelConfig, 
        prompt: str
    ) -> Any:
        """Execute task with specific provider"""
        
        # Get or create circuit breaker for provider
        if config.provider not in self.circuit_breakers:
            self.circuit_breakers[config.provider] = CircuitBreaker(
                name=f"{config.provider}_breaker",
                failure_threshold=3,
                timeout=60
            )
        
        breaker = self.circuit_breakers[config.provider]
        
        # Create provider-specific client
        client = self._create_client(config)
        
        # Execute with circuit breaker protection
        start_time = time.time()
        try:
            result = await breaker.call_async(
                client.complete,
                prompt=prompt,
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
            # Record metrics
            self._record_success(config.provider, time.time() - start_time)
            return result
            
        except Exception as e:
            self._record_failure(config.provider, time.time() - start_time)
            raise
    
    def _create_client(self, config: ModelConfig):
        """Create provider-specific client"""
        # This will be implemented with actual provider SDKs
        # For now, return a mock client
        if config.provider == "xai":
            from .providers.xai import XAIClient
            return XAIClient()
        elif config.provider == "anthropic":
            from .providers.anthropic import AnthropicClient
            return AnthropicClient()
        # ... other providers
    
    def _record_success(self, provider: str, latency: float):
        """Record successful provider call metrics"""
        if provider not in self.provider_metrics:
            self.provider_metrics[provider] = {
                "successes": 0,
                "failures": 0,
                "total_latency": 0
            }
        
        self.provider_metrics[provider]["successes"] += 1
        self.provider_metrics[provider]["total_latency"] += latency
    
    def _record_failure(self, provider: str, latency: float):
        """Record failed provider call metrics"""
        if provider not in self.provider_metrics:
            self.provider_metrics[provider] = {
                "successes": 0,
                "failures": 0,
                "total_latency": 0
            }
        
        self.provider_metrics[provider]["failures"] += 1
```

### 3.4 Provider Adapters

```python
# packages/sophia_core/models/providers/xai.py

import os
import httpx
from typing import Optional, Dict, Any

class XAIClient:
    """X.AI (Grok) provider client"""
    
    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        self.base_url = "https://api.x.ai/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def complete(
        self,
        prompt: str,
        model: str = "grok-beta",
        max_tokens: int = 4096,
        temperature: float = 0.5,
        **kwargs
    ) -> Dict[str, Any]:
        """Complete a prompt using Grok"""
        
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }
        )
        
        response.raise_for_status()
        return response.json()
```

## Phase 4: Shared Memory System with MCP (Days 6-9)

### 4.1 MCP Memory Server

```yaml
# Add to docker-compose.dev.yml
mcp-memory:
  build:
    context: .
    dockerfile: automation/docker/Dockerfile.mcp-memory
  container_name: sophia-mcp-memory
  ports:
    - "8081:8000"
  environment:
    - REDIS_URL=redis://redis:6379
    - WEAVIATE_URL=http://weaviate:8080
  depends_on:
    - redis
    - weaviate
  networks:
    - sophia-network
```

### 4.2 Memory Manager Implementation

```python
# packages/sophia_core/memory/manager.py

from typing import Dict, List, Any, Optional
import redis
import weaviate
from dataclasses import dataclass
import json
import asyncio

@dataclass
class MemoryScope:
    tenant: str = "default"
    project: str = "sophia"
    repo: str = "sophia-intel-ai"
    agent: str = "unknown"
    session: str = "default"
    
    @property
    def redis_key_prefix(self) -> str:
        return f"{self.tenant}:{self.project}:{self.repo}:{self.agent}:{self.session}"
    
    @property
    def weaviate_namespace(self) -> str:
        return f"{self.project}_{self.repo}".replace("-", "_")

class MemoryManager:
    """Unified memory manager for agent coordination"""
    
    def __init__(self, redis_url: str, weaviate_url: str):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.weaviate_client = weaviate.Client(weaviate_url)
        self._setup_weaviate_schema()
    
    def _setup_weaviate_schema(self):
        """Setup Weaviate schema for code and documents"""
        
        schemas = [
            {
                "class": "CodeChunk",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "file_path", "dataType": ["string"]},
                    {"name": "language", "dataType": ["string"]},
                    {"name": "repo", "dataType": ["string"]},
                    {"name": "doc_id", "dataType": ["string"]},
                    {"name": "chunk_index", "dataType": ["int"]},
                    {"name": "metadata", "dataType": ["text"]}
                ]
            },
            {
                "class": "Document",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "title", "dataType": ["string"]},
                    {"name": "source", "dataType": ["string"]},
                    {"name": "doc_type", "dataType": ["string"]},
                    {"name": "metadata", "dataType": ["text"]}
                ]
            }
        ]
        
        for schema in schemas:
            try:
                self.weaviate_client.schema.create_class(schema)
            except Exception:
                pass  # Schema already exists
    
    async def remember(
        self,
        scope: MemoryScope,
        key: str,
        value: Any,
        ttl: Optional[int] = 1800
    ):
        """Store value in short-term memory"""
        
        full_key = f"{scope.redis_key_prefix}:{key}"
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        self.redis_client.set(full_key, value, ex=ttl)
    
    async def recall(
        self,
        scope: MemoryScope,
        key: str
    ) -> Optional[Any]:
        """Retrieve value from short-term memory"""
        
        full_key = f"{scope.redis_key_prefix}:{key}"
        value = self.redis_client.get(full_key)
        
        if value:
            try:
                return json.loads(value)
            except:
                return value
        
        return None
    
    async def upsert_code(
        self,
        scope: MemoryScope,
        file_path: str,
        content: str,
        language: str,
        metadata: Optional[Dict] = None
    ):
        """Store code in vector database"""
        
        # Chunk the code for better retrieval
        chunks = self._chunk_code(content, chunk_size=500)
        
        for i, chunk in enumerate(chunks):
            data_object = {
                "content": chunk,
                "file_path": file_path,
                "language": language,
                "repo": scope.repo,
                "doc_id": f"{scope.repo}:{file_path}",
                "chunk_index": i,
                "metadata": json.dumps(metadata or {})
            }
            
            self.weaviate_client.data_object.create(
                data_object,
                class_name="CodeChunk"
            )
    
    async def hybrid_search(
        self,
        scope: MemoryScope,
        query: str,
        limit: int = 10,
        rerank: bool = False
    ) -> List[Dict]:
        """Perform hybrid search combining keyword and semantic search"""
        
        # Combine BM25 (keyword) and vector search
        result = self.weaviate_client.query.get(
            "CodeChunk",
            ["content", "file_path", "language", "metadata"]
        ).with_hybrid(
            query,
            alpha=0.5  # Balance between keyword and vector search
        ).with_where({
            "path": ["repo"],
            "operator": "Equal",
            "valueString": scope.repo
        }).with_limit(limit).do()
        
        chunks = result.get("data", {}).get("Get", {}).get("CodeChunk", [])
        
        if rerank and chunks:
            # TODO: Implement LLM-based reranking
            pass
        
        return chunks
    
    def _chunk_code(self, content: str, chunk_size: int = 500) -> List[str]:
        """Chunk code into smaller pieces for embedding"""
        
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            
            if current_size + line_size > chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
```

## Phase 5: Tools SDK with MCP Servers (Days 10-14)

### 5.1 MCP Filesystem Server

```yaml
# Add to docker-compose.dev.yml
mcp-filesystem-sophia:
  build:
    context: .
    dockerfile: automation/docker/Dockerfile.mcp-filesystem
  container_name: sophia-mcp-fs-sophia
  environment:
    - WORKSPACE_PATH=/workspace/sophia
    - WORKSPACE_NAME=sophia
    - READ_ONLY=false
  volumes:
    - ./:/workspace/sophia
  networks:
    - sophia-network
  ports:
    - "8082:8000"

mcp-filesystem-artemis:
  build:
    context: .
    dockerfile: automation/docker/Dockerfile.mcp-filesystem
  container_name: sophia-mcp-fs-artemis
  environment:
    - WORKSPACE_PATH=/workspace/artemis
    - WORKSPACE_NAME=artemis
    - READ_ONLY=false
  volumes:
    - ../artemis-cli:/workspace/artemis
  networks:
    - sophia-network
  ports:
    - "8083:8000"
```

### 5.2 MCP Git Server

```yaml
# Add to docker-compose.dev.yml
mcp-git:
  build:
    context: .
    dockerfile: automation/docker/Dockerfile.mcp-git
  container_name: sophia-mcp-git
  environment:
    - SSH_AUTH_SOCK=${SSH_AUTH_SOCK}
    - GIT_USER_NAME=Sophia AI Agent
    - GIT_USER_EMAIL=agent@sophia-intel.ai
  volumes:
    - ./:/workspace/sophia
    - ../artemis-cli:/workspace/artemis
    - ~/.ssh:/root/.ssh:ro
    - ${SSH_AUTH_SOCK}:${SSH_AUTH_SOCK}
  networks:
    - sophia-network
  ports:
    - "8084:8000"
```

### 5.3 Tools SDK Implementation

```python
# packages/sophia_core/tools/sdk.py

from typing import Dict, List, Any, Optional
import httpx
from dataclasses import dataclass
import asyncio

@dataclass
class MCPEndpoints:
    filesystem_sophia: str = "http://mcp-filesystem-sophia:8000"
    filesystem_artemis: str = "http://mcp-filesystem-artemis:8000"
    git: str = "http://mcp-git:8000"
    memory: str = "http://mcp-memory:8000"

class MCPToolsSDK:
    """SDK for interacting with MCP servers"""
    
    def __init__(self, endpoints: Optional[MCPEndpoints] = None):
        self.endpoints = endpoints or MCPEndpoints()
        self.clients = {
            "fs_sophia": httpx.AsyncClient(base_url=self.endpoints.filesystem_sophia),
            "fs_artemis": httpx.AsyncClient(base_url=self.endpoints.filesystem_artemis),
            "git": httpx.AsyncClient(base_url=self.endpoints.git),
            "memory": httpx.AsyncClient(base_url=self.endpoints.memory)
        }
    
    async def read_file(self, repo: str, path: str) -> str:
        """Read file from repository via MCP"""
        
        client = self.clients[f"fs_{repo}"]
        response = await client.post(
            "/read",
            json={"path": path}
        )
        response.raise_for_status()
        return response.json()["content"]
    
    async def write_file(self, repo: str, path: str, content: str):
        """Write file to repository via MCP"""
        
        client = self.clients[f"fs_{repo}"]
        response = await client.post(
            "/write",
            json={"path": path, "content": content}
        )
        response.raise_for_status()
    
    async def list_files(self, repo: str, directory: str = "/") -> List[str]:
        """List files in directory via MCP"""
        
        client = self.clients[f"fs_{repo}"]
        response = await client.post(
            "/list",
            json={"directory": directory}
        )
        response.raise_for_status()
        return response.json()["files"]
    
    async def git_status(self, repo: str) -> Dict[str, Any]:
        """Get git status via MCP"""
        
        response = await self.clients["git"].post(
            "/status",
            json={"repo": repo}
        )
        response.raise_for_status()
        return response.json()
    
    async def git_commit(
        self,
        repo: str,
        message: str,
        files: List[str]
    ) -> str:
        """Commit changes via MCP"""
        
        response = await self.clients["git"].post(
            "/commit",
            json={
                "repo": repo,
                "message": message,
                "files": files
            }
        )
        response.raise_for_status()
        return response.json()["commit_hash"]
    
    async def git_push(self, repo: str, branch: str = "main"):
        """Push changes to remote via MCP"""
        
        response = await self.clients["git"].post(
            "/push",
            json={
                "repo": repo,
                "branch": branch
            }
        )
        response.raise_for_status()
    
    async def store_memory(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: Optional[int] = None
    ):
        """Store value in shared memory via MCP"""
        
        response = await self.clients["memory"].post(
            "/store",
            json={
                "key": key,
                "value": value,
                "namespace": namespace,
                "ttl": ttl
            }
        )
        response.raise_for_status()
    
    async def retrieve_memory(
        self,
        key: str,
        namespace: str = "default"
    ) -> Optional[Any]:
        """Retrieve value from shared memory via MCP"""
        
        response = await self.clients["memory"].post(
            "/retrieve",
            json={
                "key": key,
                "namespace": namespace
            }
        )
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return response.json()["value"]
    
    async def search_memory(
        self,
        query: str,
        namespace: str = "default",
        limit: int = 10
    ) -> List[Dict]:
        """Search memory via MCP"""
        
        response = await self.clients["memory"].post(
            "/search",
            json={
                "query": query,
                "namespace": namespace,
                "limit": limit
            }
        )
        response.raise_for_status()
        return response.json()["results"]
```

## Phase 6: Swarm Coordination & Web UI (Days 15-20)

### 6.1 Swarm Orchestrator

```yaml
# Add to docker-compose.dev.yml
swarm-orchestrator:
  build:
    context: .
    dockerfile: automation/docker/Dockerfile.swarm
  container_name: sophia-swarm
  ports:
    - "8090:8000"
  environment:
    - REDIS_URL=redis://redis:6379
    - MCP_ENDPOINTS={"fs_sophia":"http://mcp-filesystem-sophia:8000"}
  depends_on:
    - redis
    - mcp-memory
    - mcp-filesystem-sophia
    - mcp-filesystem-artemis
    - mcp-git
  networks:
    - sophia-network
```

### 6.2 Web UI Service

```yaml
# Add to docker-compose.dev.yml
webui:
  build:
    context: .
    dockerfile: automation/docker/Dockerfile.webui
  container_name: sophia-webui
  ports:
    - "3001:3000"
  environment:
    - API_URL=http://swarm-orchestrator:8000
    - WEBSOCKET_URL=ws://swarm-orchestrator:8000/ws
  depends_on:
    - swarm-orchestrator
  networks:
    - sophia-network
```

### 6.3 Terminal CLI Implementation

```python
# scripts/sophia_cli.py

import click
import asyncio
from typing import Optional
import httpx
import json
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.progress import Progress

console = Console()

@click.group()
def cli():
    """Sophia AI Multi-Agent CLI"""
    pass

@cli.group()
def swarm():
    """Manage agent swarms"""
    pass

@swarm.command()
@click.argument('task')
@click.option('--agents', default='auto', help='Agents to use (auto/claude/grok/deepseek)')
@click.option('--repo', default='sophia', help='Repository context (sophia/artemis/both)')
def start(task: str, agents: str, repo: str):
    """Start a new swarm task"""
    
    console.print(f"[green]Starting swarm for task:[/green] {task}")
    
    async def run():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8090/swarm/start",
                json={
                    "task": task,
                    "agents": agents,
                    "repo": repo
                }
            )
            
            swarm_id = response.json()["swarm_id"]
            console.print(f"[blue]Swarm ID:[/blue] {swarm_id}")
            
            # Stream progress
            async with httpx.AsyncClient() as ws_client:
                async with ws_client.stream(
                    "GET",
                    f"http://localhost:8090/swarm/{swarm_id}/stream"
                ) as stream:
                    async for line in stream.aiter_lines():
                        if line:
                            event = json.loads(line)
                            _display_event(event)
    
    asyncio.run(run())

@swarm.command()
def status():
    """Show swarm status"""
    
    async def run():
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8090/swarm/status")
            swarms = response.json()["swarms"]
            
            table = Table(title="Active Swarms")
            table.add_column("ID", style="cyan")
            table.add_column("Task", style="green")
            table.add_column("Agents", style="yellow")
            table.add_column("Status", style="blue")
            table.add_column("Progress", style="magenta")
            
            for swarm in swarms:
                table.add_row(
                    swarm["id"][:8],
                    swarm["task"][:50],
                    ", ".join(swarm["agents"]),
                    swarm["status"],
                    f"{swarm['progress']}%"
                )
            
            console.print(table)
    
    asyncio.run(run())

@cli.group()
def agent():
    """Manage individual agents"""
    pass

@agent.command()
@click.argument('agent_type', type=click.Choice(['claude', 'grok', 'deepseek', 'codex']))
@click.option('--task', required=True, help='Task to execute')
@click.option('--mode', default='code', type=click.Choice(['code', 'chat', 'analyze']))
@click.option('--repo', default='sophia', help='Repository context')
def run(agent_type: str, task: str, mode: str, repo: str):
    """Run a single agent task"""
    
    console.print(f"[green]Running {agent_type} agent...[/green]")
    
    async def execute():
        # Import the appropriate agent
        if agent_type == "grok":
            from packages.sophia_core.agents.grok import GrokAgent
            agent = GrokAgent()
        elif agent_type == "claude":
            from packages.sophia_core.agents.claude import ClaudeAgent
            agent = ClaudeAgent()
        # ... other agents
        
        # Setup MCP SDK
        from packages.sophia_core.tools.sdk import MCPToolsSDK
        sdk = MCPToolsSDK()
        
        # Execute task
        result = await agent.execute(
            task=task,
            mode=mode,
            repo=repo,
            tools=sdk
        )
        
        console.print(f"[blue]Result:[/blue]\n{result}")
    
    asyncio.run(execute())

@cli.group()
def memory():
    """Manage shared memory"""
    pass

@memory.command()
@click.argument('query')
@click.option('--namespace', default='default', help='Memory namespace')
@click.option('--limit', default=10, help='Result limit')
def search(query: str, namespace: str, limit: int):
    """Search shared memory"""
    
    async def run():
        from packages.sophia_core.tools.sdk import MCPToolsSDK
        sdk = MCPToolsSDK()
        
        results = await sdk.search_memory(query, namespace, limit)
        
        for i, result in enumerate(results, 1):
            console.print(f"\n[cyan]Result {i}:[/cyan]")
            console.print(f"[yellow]File:[/yellow] {result.get('file_path', 'N/A')}")
            console.print(f"[green]Content:[/green] {result.get('content', '')[:200]}...")
    
    asyncio.run(run())

def _display_event(event: Dict):
    """Display swarm event in terminal"""
    
    event_type = event.get("type")
    
    if event_type == "agent_started":
        console.print(f"[yellow]►[/yellow] Agent {event['agent']} started on: {event['task']}")
    elif event_type == "agent_completed":
        console.print(f"[green]✓[/green] Agent {event['agent']} completed")
    elif event_type == "agent_error":
        console.print(f"[red]✗[/red] Agent {event['agent']} error: {event['error']}")
    elif event_type == "file_modified":
        console.print(f"[blue]📝[/blue] Modified: {event['file']}")
    elif event_type == "git_commit":
        console.print(f"[magenta]🔀[/magenta] Committed: {event['message']}")
    elif event_type == "swarm_completed":
        console.print(f"[green]✅ Swarm completed successfully![/green]")

if __name__ == "__main__":
    cli()
```

### 6.4 Makefile for Quick Commands

```makefile
# Makefile

.PHONY: help env-check dev-up dev-down grok-test claude-test swarm-test rag-index clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

env-check: ## Check environment configuration
	@python3 scripts/agents_env_check.py

dev-up: ## Start development environment
	docker compose -f docker-compose.dev.yml up -d

dev-down: ## Stop development environment
	docker compose -f docker-compose.dev.yml down

grok-test: ## Test Grok integration
	@echo "Testing Grok in Docker..."
	@docker compose -f docker-compose.dev.yml run --rm agent-dev bash -c \
		"pip install -q -r requirements.txt && \
		python3 scripts/sophia_cli.py agent run grok \
			--task 'Create a REST API endpoint' \
			--mode code"

claude-test: ## Test Claude integration
	@echo "Testing Claude in Docker..."
	@docker compose -f docker-compose.dev.yml run --rm agent-dev bash -c \
		"pip install -q -r requirements.txt && \
		python3 scripts/sophia_cli.py agent run claude \
			--task 'Refactor the main module' \
			--mode code"

swarm-test: ## Test swarm coordination
	@echo "Testing swarm coordination..."
	@docker compose -f docker-compose.dev.yml run --rm agent-dev bash -c \
		"pip install -q -r requirements.txt && \
		python3 scripts/sophia_cli.py swarm start \
			'Implement user authentication system' \
			--agents auto"

rag-index: ## Index repositories for RAG
	@echo "Indexing repositories..."
	@docker compose -f docker-compose.dev.yml run --rm agent-dev bash -c \
		"pip install -q -r requirements.txt && \
		python3 scripts/index_repos.py --repos sophia,artemis"

rag-test: ## Test RAG search
	@echo "Testing RAG search..."
	@docker compose -f docker-compose.dev.yml run --rm agent-dev bash -c \
		"pip install -q -r requirements.txt && \
		python3 scripts/sophia_cli.py memory search 'authentication'"

clean: ## Clean up containers and volumes
	docker compose -f docker-compose.dev.yml down -v
	docker system prune -f
```

## Terminal Workflow Examples

### Quick Grok Test (No Compose Network)
```bash
# One-liner test with your XAI key
export XAI_API_KEY='your_real_key'
docker run --rm -it \
  -v "$PWD":/workspace -w /workspace \
  -e XAI_API_KEY="$XAI_API_KEY" \
  python:3.11-slim bash -lc \
  "pip install -r requirements.txt && python3 scripts/sophia.py agent grok --mode code --task 'Create REST API' --provider xai"
```

### Full Environment with Memory
```bash
# Start services
make dev-up

# Run agent with memory/MCP access
make grok-test

# Start a swarm task
make swarm-test

# Check swarm status
docker compose -f docker-compose.dev.yml run --rm agent-dev \
  python3 scripts/sophia_cli.py swarm status

# Search memory
docker compose -f docker-compose.dev.yml run --rm agent-dev \
  python3 scripts/sophia_cli.py memory search "API endpoint"

# Clean up
make dev-down
```

### Git Push Workflow
```bash
# Run agent that modifies code
docker compose -f docker-compose.dev.yml run --rm agent-dev bash -c \
  "python3 scripts/sophia_cli.py agent run claude \
    --task 'Add error handling to authentication module' \
    --mode code --repo sophia"

# Agent automatically:
# 1. Reads files via MCP filesystem
# 2. Makes changes
# 3. Commits via MCP git (using SSH agent forwarding)
# 4. Optionally pushes to GitHub
```

## Key Features Delivered

1. **Terminal-First**: Everything runs from terminal, no VS Code needed
2. **No Host Python**: All execution in Docker containers
3. **Multi-Agent Support**: Claude, Grok, DeepSeek, Codex with task routing
4. **MCP Coordination**: All file/git/memory ops go through MCP servers
5. **Dual Repo Access**: Both sophia-intel-ai and artemis-cli mounted
6. **Shared Memory**: Redis + Weaviate accessible to all agents
7. **SSH Forwarding**: Git push works with your SSH keys
8. **Web UI**: Optional browser interface for natural language interaction
9. **Observability**: Metrics, logging, and tracing built-in
10. **Quick Testing**: One-liner Docker commands for rapid iteration

## Implementation Timeline

- **Days 1-5**: Phase 3 - LLM Router with Docker testing
- **Days 6-9**: Phase 4 - Memory System with MCP
- **Days 10-14**: Phase 5 - Tools SDK and MCP servers
- **Days 15-20**: Phase 6 - Swarm coordination and Web UI

Total: ~20 working days for complete implementation

## Next Steps

1. Create `docker-compose.dev.yml` with all services
2. Implement the LLM router with provider adapters
3. Build MCP servers (filesystem, git, memory)
4. Create the terminal CLI
5. Add Web UI for natural language chat
6. Test end-to-end workflows