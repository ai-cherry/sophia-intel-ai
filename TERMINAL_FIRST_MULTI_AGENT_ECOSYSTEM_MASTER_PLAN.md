# Terminal-First Multi-Agent Coding Ecosystem - Master Implementation Plan

## 🎯 **Executive Objectives**

**Vision**: Terminal-only multi-agent coding ecosystem with Docker isolation, MCP coordination, shared memory/indexing, cross-repository access, and 6-pane Web UI for simultaneous agent chats.

**Core Principles**:
- **Terminal-First**: No IDE dependencies, all operations via CLI
- **Docker-Isolated**: Zero host Python drift, everything containerized
- **MCP-Coordinated**: Unified tool access through MCP servers
- **Multi-Repository**: Seamless access to sophia-intel-ai + artemis-cli
- **Agent-Agnostic**: Uniform interface across Grok/Claude/Codex/DeepSeek

## 📊 **Current Foundation Assessment**

### ✅ **Delivered Components**
```
✅ scripts/agents_env_check.py - Preflight validator (arch/wheel/Rosetta checks)
✅ app/api/memory/memory_endpoints.py - Production memory API (/ready, /live, /version)
✅ scripts/test_rag_integration.py - RAG test suite
✅ requirements/ - Structured dependency management
✅ scripts/sophia.py - CLI foundation with provider routing
✅ scripts/unified_ai_agents.py - Multi-provider support
✅ mcp_servers/grok/server.py - Grok MCP stub
✅ .python-version - Python 3.11.10 policy
```

### ❌ **Critical Gaps To Close**
```
❌ Docker Compose for full multi-agent development environment
❌ 6-pane Web UI with WebSocket streaming
❌ MCP servers for filesystem/git operations across both repositories  
❌ Provider router hardening (retries, backoffs, circuit breakers)
❌ Unified tool registry with standardized capability shapes
❌ Cross-repository indexing and memory coordination
```

## 🏗️ **Target Architecture**

### **Docker Services Stack**
```yaml
# docker-compose.multi-agent.yml - Complete development environment

services:
  # Core Development Environment
  agent-dev:
    image: python:3.11-slim
    working_dir: /workspace
    volumes:
      - ./sophia-intel-ai:/workspace/sophia:rw
      - ../artemis-cli:/workspace/artemis:rw  
      - ~/.ssh:/root/.ssh:ro
      - $SSH_AUTH_SOCK:/ssh-agent
    environment:
      - SSH_AUTH_SOCK=/ssh-agent
      - PYTHONPATH=/workspace/sophia:/workspace/artemis
    networks: [multi-agent-net]

  # Infrastructure Services
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes: [redis_data:/data]
    networks: [multi-agent-net]

  weaviate:
    image: semitechnologies/weaviate:1.25.0
    ports: ["8080:8080"]
    environment:
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      DEFAULT_VECTORIZER_MODULE: text2vec-openai
    volumes: [weaviate_data:/var/lib/weaviate]
    networks: [multi-agent-net]

  # MCP Server Hub
  mcp-filesystem-sophia:
    build: ./mcp/filesystem
    environment:
      - REPO_PATH=/workspace/sophia
      - REPO_NAME=sophia-intel-ai
    volumes: [./sophia-intel-ai:/workspace/sophia:rw]
    networks: [multi-agent-net]

  mcp-filesystem-artemis:
    build: ./mcp/filesystem  
    environment:
      - REPO_PATH=/workspace/artemis
      - REPO_NAME=artemis-cli
    volumes: [../artemis-cli:/workspace/artemis:rw]
    networks: [multi-agent-net]

  mcp-git:
    build: ./mcp/git
    volumes:
      - ./sophia-intel-ai:/workspace/sophia:rw
      - ../artemis-cli:/workspace/artemis:rw
      - ~/.ssh:/root/.ssh:ro
      - $SSH_AUTH_SOCK:/ssh-agent
    environment:
      - SSH_AUTH_SOCK=/ssh-agent
    networks: [multi-agent-net]

  mcp-memory:
    build: ./mcp/memory
    environment:
      - REDIS_URL=redis://redis:6379
      - WEAVIATE_URL=http://weaviate:8080
    depends_on: [redis, weaviate]
    networks: [multi-agent-net]

  # 6-Pane Web UI
  webui:
    build: ./webui
    ports: ["3001:3001"]
    environment:
      - MCP_FILESYSTEM_SOPHIA_URL=http://mcp-filesystem-sophia:8000
      - MCP_FILESYSTEM_ARTEMIS_URL=http://mcp-filesystem-artemis:8000
      - MCP_GIT_URL=http://mcp-git:8000
      - MCP_MEMORY_URL=http://mcp-memory:8000
    depends_on: [mcp-filesystem-sophia, mcp-filesystem-artemis, mcp-git, mcp-memory]
    networks: [multi-agent-net]

  # Code Indexer
  indexer:
    build: ./indexer
    environment:
      - WEAVIATE_URL=http://weaviate:8080
      - SOPHIA_PATH=/workspace/sophia
      - ARTEMIS_PATH=/workspace/artemis
    volumes:
      - ./sophia-intel-ai:/workspace/sophia:ro
      - ../artemis-cli:/workspace/artemis:ro
    depends_on: [weaviate]
    networks: [multi-agent-net]

  # Observability (Optional)
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes: [./observability/prometheus.yml:/etc/prometheus/prometheus.yml]
    networks: [multi-agent-net]

  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    environment: [GF_SECURITY_ADMIN_PASSWORD=admin]
    volumes: [grafana_data:/var/lib/grafana]
    networks: [multi-agent-net]

volumes:
  redis_data:
  weaviate_data:
  grafana_data:

networks:
  multi-agent-net:
    driver: bridge
```

## 🔧 **MCP Server Specifications**

### **Filesystem MCP Servers**
```python
# mcp/filesystem/server.py
class FilesystemMCPServer:
    """
    Provides standardized file operations for a specific repository
    Capabilities: list, read, write, search, create, delete with policies
    """
    
    tools = [
        "fs.list",        # List directory contents
        "fs.read",        # Read file content  
        "fs.write",       # Write/update file
        "fs.search",      # Search files by content/name
        "fs.create",      # Create new file/directory
        "fs.delete",      # Delete file/directory (with policies)
        "fs.watch",       # Watch for file changes
    ]
    
    def __init__(self, repo_path: str, repo_name: str):
        self.repo_path = Path(repo_path)
        self.repo_name = repo_name
        self.write_policies = self._load_write_policies()
        
    async def fs_write(self, file_path: str, content: str, backup: bool = True):
        """Write file with policy checks and optional backup"""
        if not self._check_write_policy(file_path):
            raise PolicyViolation(f"Write denied for {file_path}")
        # Implementation with backup/versioning
```

### **Git MCP Server**
```python
# mcp/git/server.py  
class GitMCPServer:
    """
    Git operations across both repositories with SSH agent forwarding
    Capabilities: status, diff, commit, push, branch, merge
    """
    
    tools = [
        "git.status",     # Get repo status
        "git.diff",       # Show diffs
        "git.commit",     # Commit changes
        "git.push",       # Push to remote via SSH
        "git.branch",     # Branch operations  
        "git.merge",      # Merge operations
        "git.log",        # Commit history
    ]
    
    def __init__(self):
        self.repos = {
            'sophia': '/workspace/sophia',
            'artemis': '/workspace/artemis'
        }
        
    async def git_push(self, repo: str, branch: str = 'main', force: bool = False):
        """Push changes via SSH agent forwarding"""
        if force and not self._allow_force_push():
            raise PolicyViolation("Force push disabled by policy")
        # SSH agent forwarding implementation
```

### **Memory MCP Server**
```python
# mcp/memory/server.py
class MemoryMCPServer:
    """
    Unified memory operations with Redis + Weaviate integration
    Namespaces: local:sophia, local:artemis, session:{session_id}
    """
    
    tools = [
        "memory.store",    # Store conversation/context
        "memory.search",   # Hybrid search (Redis + Weaviate)
        "memory.recall",   # Retrieve by ID/namespace
        "memory.embed",    # Generate embeddings
        "memory.index",    # Index content for search
        "memory.clear",    # Clear namespace/session
    ]
    
    def __init__(self):
        self.redis = redis.AsyncRedis.from_url("redis://redis:6379")
        self.weaviate = weaviate.Client("http://weaviate:8080")
        
    async def memory_store(self, content: str, namespace: str, metadata: dict):
        """Store with automatic embedding generation"""
        # Dual storage: Redis for fast access, Weaviate for semantic search
```

## 🎮 **Unified CLI Interface**

### **Terminal Commands**
```bash
# Core agent commands
python3 scripts/sophia.py agent grok --mode code --task "Create REST API" --provider xai
python3 scripts/sophia.py agent claude --mode code --task "Refactor main.py" --repo sophia  
python3 scripts/sophia.py agent codex --mode code --task "Write tests" --repo artemis
python3 scripts/sophia.py agent deepseek --mode code --task "Optimize function" --both-repos

# Memory operations
python3 scripts/sophia.py memory search "authentication patterns" --repo sophia
python3 scripts/sophia.py memory store --session dev_session --content "API design notes"
python3 scripts/sophia.py memory recall --namespace local:artemis --limit 10

# Repository operations  
python3 scripts/sophia.py repo status --both
python3 scripts/sophia.py repo diff --repo sophia --staged
python3 scripts/sophia.py repo commit --message "Add auth endpoint" --repo sophia
python3 scripts/sophia.py repo push --repo sophia --branch feature/auth

# Swarm operations
python3 scripts/sophia.py swarm start --task "Build user management system" --agents "grok,claude" --repos both
python3 scripts/sophia.py swarm status --session swarm_123
```

### **Provider Router Enhancement**
```python
# packages/sophia_core/models/router.py
class EnhancedProviderRouter:
    """
    Hardened router with circuit breakers, retries, budgets, and metrics
    """
    
    providers = {
        'grok': XAIProvider(circuit_breaker=True, max_retries=3),
        'claude': AnthropicProvider(circuit_breaker=True, max_retries=3),
        'codex': OpenAIProvider(circuit_breaker=True, max_retries=3),
        'deepseek': DeepSeekProvider(circuit_breaker=True, max_retries=3),
        'openrouter': OpenRouterProvider(circuit_breaker=True, max_retries=3),
    }
    
    def __init__(self):
        self.circuit_breakers = {}
        self.retry_strategies = {}
        self.budget_managers = {}
        self.metrics_collector = MetricsCollector()
        
    async def route_task(self, task: CodingTask, preferred_provider: str = None):
        """Route with intelligent provider selection and fallbacks"""
        provider = preferred_provider or self._select_best_provider(task)
        
        async with self.circuit_breakers[provider]:
            try:
                return await self._execute_with_retries(provider, task)
            except ProviderUnavailable:
                # Intelligent fallback
                fallback_provider = self._get_fallback_provider(provider, task)
                return await self._execute_with_retries(fallback_provider, task)
```

## 🌐 **6-Pane Web UI Architecture**

### **Backend (FastAPI + WebSocket)**
```python
# webui/backend/main.py
class WebUIServer:
    """
    6-session concurrent chat server with real-time streaming
    """
    
    MAX_SESSIONS = 6
    
    def __init__(self):
        self.active_sessions: Dict[str, ChatSession] = {}
        self.mcp_clients = {
            'fs_sophia': MCPClient('http://mcp-filesystem-sophia:8000'),
            'fs_artemis': MCPClient('http://mcp-filesystem-artemis:8000'),
            'git': MCPClient('http://mcp-git:8000'),
            'memory': MCPClient('http://mcp-memory:8000'),
        }
        
    @app.post("/sessions")
    async def create_session(self, request: CreateSessionRequest):
        """Create new chat session (max 6)"""
        if len(self.active_sessions) >= self.MAX_SESSIONS:
            raise HTTPException(429, "Maximum sessions reached")
            
        session = ChatSession(
            agent=request.agent,
            repo_scope=request.repo_scope,
            mcp_clients=self.mcp_clients
        )
        self.active_sessions[session.id] = session
        return {"session_id": session.id}
        
    @app.websocket("/ws")
    async def websocket_endpoint(self, websocket: WebSocket, session_id: str):
        """WebSocket for real-time streaming"""
        session = self.active_sessions.get(session_id)
        if not session:
            await websocket.close(code=4004, reason="Session not found")
            return
            
        await websocket.accept()
        async for message in session.stream_responses():
            await websocket.send_json(message)
            
    @app.post("/sessions/{session_id}/proposals/{proposal_id}/approve")
    async def approve_proposal(self, session_id: str, proposal_id: str):
        """Apply code changes via MCP filesystem"""
        session = self.active_sessions[session_id]
        proposal = session.get_proposal(proposal_id)
        
        # Apply changes via MCP
        for change in proposal.changes:
            await self.mcp_clients['fs_sophia'].call_tool('fs.write', {
                'file_path': change.file_path,
                'content': change.new_content
            })
            
        # Optional auto-commit
        if proposal.auto_commit:
            await self.mcp_clients['git'].call_tool('git.commit', {
                'message': proposal.commit_message,
                'repo': session.repo_scope
            })
```

### **Frontend (React + 6-Pane Grid)**
```typescript
// webui/frontend/src/components/MultiAgentDashboard.tsx
export const MultiAgentDashboard: React.FC = () => {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const maxSessions = 6;
    
    const createSession = async (agent: string, repoScope: string) => {
        if (sessions.length >= maxSessions) {
            toast.error('Maximum 6 sessions allowed');
            return;
        }
        
        const response = await fetch('/api/sessions', {
            method: 'POST',
            body: JSON.stringify({ agent, repo_scope: repoScope })
        });
        
        const session = await response.json();
        setSessions([...sessions, session]);
    };
    
    return (
        <div className="multi-agent-dashboard">
            <Header />
            <div className="sessions-grid grid-cols-3 grid-rows-2 gap-4">
                {Array.from({ length: maxSessions }, (_, index) => (
                    <ChatPane
                        key={index}
                        session={sessions[index]}
                        onCreateSession={createSession}
                        onCloseSession={() => closeSession(index)}
                    />
                ))}
            </div>
            <GlobalControls sessions={sessions} />
        </div>
    );
};

const ChatPane: React.FC<ChatPaneProps> = ({ session, onCreateSession }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [streamingContent, setStreamingContent] = useState('');
    const [proposals, setProposals] = useState<Proposal[]>([]);
    
    return (
        <div className="chat-pane border rounded-lg flex flex-col h-96">
            <div className="pane-header p-2 border-b">
                {session ? (
                    <div className="flex justify-between items-center">
                        <span className="font-medium">{session.agent} - {session.repo_scope}</span>
                        <AgentControls session={session} />
                    </div>
                ) : (
                    <SessionCreator onCreate={onCreateSession} />
                )}
            </div>
            
            <div className="messages flex-1 overflow-y-auto p-2">
                {messages.map(msg => <MessageBubble key={msg.id} message={msg} />)}
                {streamingContent && (
                    <div className="streaming-message">
                        <TypewriterText content={streamingContent} />
                    </div>
                )}
            </div>
            
            <div className="tools-tray p-2 border-t">
                <ToolButtons session={session} />
            </div>
            
            {proposals.length > 0 && (
                <ProposalModal 
                    proposals={proposals} 
                    onApprove={approveProposal}
                    onReject={rejectProposal}
                />
            )}
        </div>
    );
};
```

## 🔄 **Cross-Repository Operations**

### **Unified Indexing System**
```python
# indexer/main.py
class CrossRepoIndexer:
    """
    Monitors both repositories and maintains unified search index
    """
    
    def __init__(self):
        self.repos = {
            'sophia': '/workspace/sophia',
            'artemis': '/workspace/artemis'
        }
        self.weaviate = weaviate.Client("http://weaviate:8080")
        self.embedding_service = TogetherEmbeddingService()
        
    async def start_watching(self):
        """Start file watchers for both repositories"""
        tasks = []
        for repo_name, repo_path in self.repos.items():
            task = asyncio.create_task(self._watch_repo(repo_name, repo_path))
            tasks.append(task)
        await asyncio.gather(*tasks)
        
    async def _watch_repo(self, repo_name: str, repo_path: str):
        """Watch repository for changes and update index"""
        async for event in aiofiles_watch(repo_path):
            if event.event_type in ['created', 'modified']:
                await self._index_file(repo_name, event.src_path)
                
    async def _index_file(self, repo_name: str, file_path: str):
        """Index file content with metadata"""
        if not self._should_index(file_path):
            return
            
        content = await aiofiles.read(file_path)
        embedding = await self.embedding_service.embed(content)
        
        await self.weaviate.data_object.create({
            'content': content,
            'file_path': file_path,
            'repo_name': repo_name,
            'indexed_at': datetime.now().isoformat(),
            'file_type': Path(file_path).suffix,
            'size': len(content)
        }, vector=embedding, class_name='CodeFile')
```

## 🚀 **Immediate Implementation Scripts**

### **Quick Grok Test**
```bash
#!/bin/bash
# scripts/quick-grok-test.sh
set -euo pipefail

# Quick one-off Grok test (no compose/network needed)
export XAI_API_KEY="${XAI_API_KEY:-$(cat .env | grep XAI_API_KEY | cut -d'=' -f2)}"

if [ -z "$XAI_API_KEY" ]; then
    echo "❌ XAI_API_KEY not found in environment or .env file"
    exit 1
fi

echo "🧪 Testing Grok integration..."

docker run --rm -it \
    -v "$PWD":/workspace -w /workspace \
    -e XAI_API_KEY="$XAI_API_KEY" \
    python:3.11-slim bash -lc \
    "pip install -r requirements/base.txt && python3 scripts/sophia.py agent grok --mode code --task 'Create simple REST API endpoint' --provider xai"

echo "✅ Grok test completed"
```

### **Multi-Agent Environment Manager**
```bash
#!/bin/bash
# scripts/multi-agent-docker-env.sh
set -euo pipefail

COMPOSE_FILE="docker-compose.multi-agent.yml"
NETWORK_NAME="$(basename "$PWD")_multi-agent-net"

case "${1:-up}" in
    "up")
        echo "🚀 Starting multi-agent environment..."
        
        # Ensure SSH agent is available
        if [ -z "${SSH_AUTH_SOCK:-}" ]; then
            echo "⚠️  SSH_AUTH_SOCK not set. GitHub push may not work."
        fi
        
        # Start infrastructure first
        docker compose -f "$COMPOSE_FILE" up -d redis weaviate
        sleep 5
        
        # Start MCP servers
        docker compose -f "$COMPOSE_FILE" up -d mcp-filesystem-sophia mcp-filesystem-artemis mcp-git mcp-memory
        sleep 3
        
        # Start indexer and web UI
        docker compose -f "$COMPOSE_FILE" up -d indexer webui
        
        echo "✅ Environment ready!"
        echo "🌐 Web UI: http://localhost:3001"
        echo "📊 Grafana: http://localhost:3000 (admin/admin)"
        ;;
        
    "down")
        echo "🛑 Stopping multi-agent environment..."
        docker compose -f "$COMPOSE_FILE" down
        ;;
        
    "logs")
        docker compose -f "$COMPOSE_FILE" logs -f "${2:-}"
        ;;
        
    "shell")
        echo "🐚 Entering development shell..."
        docker compose -f "$COMPOSE_FILE" run --rm agent-dev bash
        ;;
        
    "status")
        echo "📊 Environment status:"
        docker compose -f "$COMPOSE_FILE" ps
        ;;
        
    *)
        echo "Usage: $0 {up|down|logs|shell|status}"
        exit 1
        ;;
esac
```

### **Enhanced Makefile**
```makefile
# Makefile - Terminal-friendly multi-agent commands
.PHONY: help dev-up dev-down dev-shell grok-test swarm-start memory-search env-check

# Colors for output
CYAN=\033[0;36m
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)Multi-Agent Development Environment$(NC)"
	@echo "$(YELLOW)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev-up: ## Start full multi-agent environment
	@echo "$(CYAN)🚀 Starting multi-agent environment...$(NC)"
	@./scripts/multi-agent-docker-env.sh up

dev-down: ## Stop multi-agent environment  
	@echo "$(RED)🛑 Stopping multi-agent environment...$(NC)"
	@./scripts/multi-agent-docker-env.sh down

dev-shell: ## Enter development shell
	@echo "$(CYAN)🐚 Entering development shell...$(NC)"
	@./scripts/multi-agent-docker-env.sh shell

grok-test: ## Quick Grok integration test
	@echo "$(YELLOW)🧪 Testing Grok integration...$(NC)"
	@./scripts/quick-grok-test.sh

env-check: ## Run environment preflight check
	@echo "$(YELLOW)🔍 Running environment check...$(NC)"
	@python3 scripts/agents_env_check.py

swarm-start: ## Start multi-agent swarm (use: make swarm-start TASK="your task")
	@echo "$(GREEN)🤖 Starting agent swarm...$(NC)"
	@docker compose -f docker-compose.multi-agent.yml run --rm agent-dev \
		python3 scripts/sophia.py swarm start --task "$(TASK)" --agents "grok,claude,deepseek"

memory-search: ## Search shared memory (use: make memory-search QUERY="search term")
	@echo "$(CYAN)🧠 Searching memory...$(NC)"
	@docker compose -f docker-compose.multi-agent.yml run --rm agent-dev \
		python3 scripts/sophia.py memory search "$(QUERY)"

logs: ## View logs from all services
	@./scripts/multi-agent-docker-env.sh logs

status: ## Show environment status
	@./scripts/multi-agent-docker-env.sh status

clean: ## Clean up Docker resources
	@echo "$(RED)🧹 Cleaning Docker resources...$(NC)"
	@docker system prune -f
	@docker volume prune -f
```

## 📅 **Implementation Timeline & Phases**

### **Phase 0: Immediate Setup (2-3 Hours)**
```bash
# Immediate actions for next session
1. Create docker-compose.multi-agent.yml
2. Implement scripts/quick-grok-test.sh  
3. Implement scripts/multi-agent-docker-env.sh
4. Update Makefile with terminal commands
5. Test basic Grok integration
```

### **Phase 1: Core MCP Infrastructure (Week 1)**
- **Day 1-2**: MCP filesystem servers for both repositories
- **Day 3-4**: MCP git server with SSH agent forwarding  
- **Day 5-7**: MCP memory server with Redis/Weaviate integration

### **Phase 2: Enhanced CLI & Providers (Week 2)**
- **Day 1-3**: Hardened provider router with circuit breakers
- **Day 4-5**: Enhanced CLI commands for all operations
- **Day 6-7**: Cross-repository indexing system

### **Phase 3: Web UI Implementation (Week 3)**
- **Day 1-3**: Backend with WebSocket streaming
- **Day 4-5**: 6-pane React frontend
- **Day 6-7**: Proposal system with approve/reject workflow

### **Phase 4: Production Readiness (Week 4)**
- **Day 1-2**: Security policies and access control
- **Day 3-4**: Observability (Prometheus/Grafana)  
- **Day 5-7**: Performance optimization and documentation

## 🎯 **Success Criteria & Acceptance Tests**

### **Technical Acceptance**
- [ ] `make dev-up` starts all services without errors
- [ ] Six concurrent chat sessions can stream with different agents  
- [ ] File operations work across both repositories via MCP
- [ ] Git commits/pushes work via SSH agent forwarding
- [ ] Memory search returns relevant results from both repos
- [ ] Code proposals can be approved and auto-committed
- [ ] Preflight check passes or provides clear remediation
- [ ] All secrets are redacted in logs and metrics are visible

### **User Experience Tests**
```bash
# Test 1: Quick Grok verification
make grok-test

# Test 2: Full environment startup  
make dev-up && make status

# Test 3: Multi-agent swarm coordination
make swarm-start TASK="Create authentication system across both repos"

# Test 4: Memory operations
make memory-search QUERY="API patterns"

# Test 5: Web UI access
curl http://localhost:3001/health
```

### **Performance Targets**
- Environment startup: < 2 minutes
- Agent response time: < 30 seconds for simple tasks  
- Memory search: < 3 seconds
- File operations: < 1 second
- WebSocket message latency: < 100ms

## 🔒 **Security & Policies**

### **Access Control Policies**
```yaml
# mcp/policies/filesystem.yml
filesystem_policies:
  sophia-intel-ai:
    write_allowed_paths: ["/app", "/scripts", "/mcp_servers"]
    write_denied_paths: ["/secrets", "/.env*", "/docker-compose*"]
    backup_on_write: true
    
  artemis-cli:  
    write_allowed_paths: ["/agents", "/tools", "/cli"]
    write_denied_paths: ["/config", "/.env*"]
    backup_on_write: true

git_policies:
  force_push_allowed: false
  auto_push_branches: ["feature/*", "bugfix/*"]
  protected_branches: ["main", "production"]
  commit_message_required: true
```

### **Secret Management**
```bash
# .env.example (template for environment setup)
# AI Provider Keys
XAI_API_KEY=your_grok_key_here
OPENROUTER_API_KEY=your_openrouter_key
ANTHROPIC_API_KEY=your_claude_key  
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_KEY=your_openai_key

# Infrastructure
REDIS_URL=redis://redis:6379
WEAVIATE_URL=http://weaviate:8080
GITHUB_TOKEN=your_github_token

# Security
SECRET_KEY=generate_random_secret_key
JWT_SECRET=generate_jwt_secret

# Observability  
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=secure_password
```

## 📊 **Observability & Monitoring**

### **Metrics Collection**
```python
# observability/metrics.py
class MultiAgentMetrics:
    """
    Comprehensive metrics for multi-agent ecosystem
    """
    
    metrics = {
        'provider_requests_total': Counter('provider_requests_total', ['provider', 'model']),
        'provider_latency_seconds': Histogram('provider_latency_seconds', ['provider']),
        'mcp_operations_total': Counter('mcp_operations_total', ['server', 'operation']),
        'websocket_connections': Gauge('websocket_connections_active'),
        'memory_operations_total': Counter('memory_operations_total', ['operation', 'namespace']),
        'git_operations_total': Counter('git_operations_total', ['repo', 'operation']),
        'file_operations_total': Counter('file_operations_total', ['repo', 'operation']),
    }
```

### **Logging Configuration**
```yaml
# observability/logging.yml
version: 1
formatters:
  json:
    format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "%(name)s", "message": "%(message)s", "correlation_id": "%(correlation_id)s"}'
    
handlers:
  console:
    class: logging.StreamHandler
    formatter: json
    stream: ext://sys.stdout
    
  file:
    class: logging.handlers.RotatingFileHandler
    formatter: json
    filename: /var/log/multi-agent.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

root:
  level: INFO
  handlers: [console, file]
```

## 🚀 **Developer Workflow Examples**

### **Daily Development Workflow**
```bash
# Morning startup
make env-check        # Verify environment health
make dev-up          # Start all services
make status          # Confirm everything running

# Development work
make dev-shell       # Enter container for terminal work
# Inside container:
python3 scripts/sophia.py agent claude --task "Review PR changes" --repo sophia
python3 scripts/sophia.py memory store --content "Today's architecture decisions"

# Web UI work
# Open http://localhost:3001
# Create multiple sessions for different agents
# Use natural language: "Refactor the authentication system using best practices"

# End of day
make logs           # Review any errors
make dev-down       # Clean shutdown
```

### **Cross-Repository Feature Development**
```bash
# Feature: Shared authentication between repos
make swarm-start TASK="Design and implement shared JWT authentication system across sophia and artemis repos"

# This would:
# 1. Analyze both codebases via MCP filesystem
# 2. Generate implementation plan 
# 3. Create code in both repositories
# 4. Show diffs for approval
# 5. Auto-commit and push changes
```

## 🔄 **Migration from Previous Plans**

### **Consolidated Components** (Replaces Previous Plans)
- ❌ `COMPREHENSIVE_MULTI_AGENT_CODING_ECOSYSTEM_PLAN.md` - **SUPERSEDED**
- ❌ `ARCHITECTURE_RUNTIME_IMPLEMENTATION_PLAN.md` - **PARTIALLY SUPERSEDED**  
- ✅ `ARCHITECTURE_RUNTIME_PHASES_A1-A3_COMPLETE.md` - **PRESERVED** (Foundation work)
- ✅ This master plan becomes the **SINGLE SOURCE OF TRUTH**

### **Key Improvements Over Previous Plans**
1. **Terminal-First Focus**: Eliminated IDE dependencies completely
2. **Docker Isolation**: Solved host Python compatibility issues  
3. **MCP Standardization**: Unified all operations through MCP servers
4. **6-Pane Web UI**: Specific requirement for concurrent agent sessions
5. **SSH Agent Forwarding**: Practical solution for GitHub push access
6. **Immediate Scripts**: Ready-to-use implementation scripts

### **Preserved Foundation Work**
- Enhanced preflight validator (Phase A1)
- Production memory API (Phase A2) 
- RAG integration (Phase A3)
- Structured requirements (Phase B)
- Python version policy

## 📋 **Final Implementation Checklist**

### **Immediate Next Steps (This Session)**
- [ ] Create `docker-compose.multi-agent.yml`
- [ ] Implement `scripts/quick-grok-test.sh`
- [ ] Implement `scripts/multi-agent-docker-env.sh`
- [ ] Update `Makefile` with terminal commands
- [ ] Test basic Grok integration in Docker
- [ ] **Delete conflicting/superseded plan files**

### **Week 1 Deliverables**
- [ ] Complete MCP server implementations
- [ ] Enhanced provider router with circuit breakers  
- [ ] Cross-repository indexing system
- [ ] Basic Web UI backend with WebSocket

### **Production Ready (4 Weeks)**
- [ ] Full 6-pane Web UI operational
- [ ] Security policies implemented
- [ ] Observability dashboards configured  
- [ ] Performance optimization complete
- [ ] Documentation and onboarding guides

---

**This master plan consolidates all previous work and provides the definitive roadmap for the terminal-first, multi-agent coding ecosystem. All conflicting plans should be archived or deleted in favor of this unified approach.**
