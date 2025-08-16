# Sophia Intel Unified Platform Implementation

## Phase 1: Adopt Enhanced Unified MCP Server as Primary Orchestrator ✅ IN PROGRESS

### 1.1 Remove Legacy Orchestrators
- [ ] Remove services/orchestrator.py (if exists)
- [ ] Migrate functionality from agents/swarm/swarm_orchestrator.py to enhanced_unified_server.py
- [ ] Move GPU management functionality to enhanced MCP server

### 1.2 Enhance Unified MCP Server Endpoints ✅
- [x] Ensure /ai/chat endpoint handles chat and code requests
- [x] Verify /context/store & /context/query endpoints work with Qdrant
- [x] Add /agent/task endpoint for agent task delegation
- [x] Add GPU management endpoints (/gpu/list, /gpu/launch, etc.)
- [x] Ensure single /health endpoint returns comprehensive status

### 1.3 Integration with LambdaClient ✅
- [x] Import and integrate LambdaClient for GPU management
- [x] Add GPU quota endpoint
- [x] Add GPU launch/terminate endpoints
- [x] Add GPU instance management endpoints
- [x] Add GPU instance types endpoint

## Phase 2: Refactor Swarm Orchestrator

### 2.1 Configuration Updates
- [ ] Remove hardcoded localhost:5000 from swarm_orchestrator.py
- [ ] Add ORCHESTRATOR_URL environment variable support
- [ ] Update ai_router_url to use settings.ORCHESTRATOR_URL + "/ai/chat"

### 2.2 Unified Communication
- [ ] Replace direct service calls with unified orchestrator requests
- [ ] Implement standard JSON payloads (AIRequest, ContextRequest)
- [ ] Update mission task handling to use /ai/chat endpoint
- [ ] Deprecate direct calls to services/orchestrator.py

### 2.3 Mission State Management
- [ ] Unify mission state management under new orchestrator
- [ ] Update session management to use unified system

## Phase 3: Standardize Memory and Retrieval ✅ IN PROGRESS

### 3.1 MemoryService Integration ✅
- [x] Make all services depend on MemoryService for context storage
- [x] Remove direct Qdrant calls from agents
- [x] Remove old mcp_servers/code_context dependencies

### 3.2 Create MCP Memory Client ✅
- [x] Create libs/mcp_client/memory_client.py extending BaseMCPClient
- [x] Implement store() and query() methods
- [x] Add caching and resilience features

### 3.3 Update Agents ✅ IN PROGRESS
- [x] Replace httpx calls in agents/coding_agent.py with MCPMemoryClient
- [ ] Update RAG pipeline to use libs/mcp_client first
- [ ] Maintain fallback chain (legacy MCP → Qdrant → mock)

### 3.4 Multi-Service Search
- [ ] Add GET /context/search_multi_service route to unified MCP server
- [ ] Forward queries to RAG pipeline
- [ ] Return fused results for UI clients

## Phase 4: Harmonize AI Routing

### 4.1 Remove Legacy Router
- [ ] Remove services/routing/model_router.py
- [ ] Consolidate model definitions into mcp_servers/ai_router.py

### 4.2 Configuration Management
- [ ] Create config/models.yaml for approved models
- [ ] Load model configuration at AI Router startup
- [ ] Update model registry with cost/quality metadata

### 4.3 Documentation Updates
- [ ] Update docs/development/models.md with new models
- [ ] Document cost changes and model capabilities

## Phase 5: Integrate Agents with MCP Suite

### 5.1 MCP Client Injection
- [ ] Inject MCP client reference into each agent
- [ ] Remove settings.MCP_PORT usage
- [ ] Add MCP_BASE_URL environment variable support

### 5.2 Enhanced Task Processing
- [ ] Store both task and result using MCPMemoryClient
- [ ] Capture metadata (swarm stage, mission ID)
- [ ] Implement streaming capabilities for code generation

### 5.3 Agent Updates
- [ ] Update coding_agent.py for MCP integration
- [ ] Update reviewer_agent.py for MCP integration
- [ ] Update integrator_agent.py for MCP integration

## Phase 6: Robust Configuration and Secrets Management

### 6.1 Centralized Configuration
- [ ] Centralize all environment variables in config/config.py
- [ ] Use pydantic for configuration validation
- [ ] Validate required keys (OPENROUTER_API_KEY, QDRANT_URL, GITHUB_PAT)

### 6.2 Remove Direct .env Reads
- [ ] Replace direct .env reads with settings object
- [ ] Update all services to use centralized config

### 6.3 Production Secrets Management
- [ ] Use Kubernetes Secrets for sensitive values
- [ ] Map secrets to environment variables via Pulumi
- [ ] Integrate with AWS Secrets Manager/HashiCorp Vault if needed

## Phase 7: Consolidate and Upgrade UI/Dashboard

### 7.1 Frontend Consolidation
- [ ] Choose sophia-dashboard-enhanced as base UI
- [ ] Remove/deprecate apps/sophia-dashboard-frontend
- [ ] Remove/deprecate apps/interface (already done)
- [ ] Move enhanced dashboard to apps/dashboard

### 7.2 Integrate Chat Interface
- [ ] Create Chat component inside enhanced dashboard
- [ ] Remove external link to http://104.171.202.107:30081
- [ ] Create FastAPI/Flask wrapper around SwarmChatInterface
- [ ] Replace direct swarm.graph.run calls with unified MCP server calls

### 7.3 Expose Missions and Agent Control
- [ ] Add Missions page/tab to dashboard
- [ ] List active missions and statuses
- [ ] Add buttons for common actions (coding, testing, review)
- [ ] Call appropriate /agent/task endpoints

### 7.4 System Metrics and Memory Browser
- [ ] Expand Overview/Analytics tabs with real MCP server metrics
- [ ] Fetch metrics from /health or /metrics endpoint
- [ ] Create Memory tab for context search
- [ ] Implement /context/search_multi_service integration

### 7.5 Configuration and API Updates
- [ ] Read base URLs from environment variables (REACT_APP_ORCHESTRATOR_URL)
- [ ] Remove hardcoded IPs (http://104.171.202.107:30083)
- [ ] Provide .env.example template

### 7.6 Remove Obsolete Interfaces
- [ ] Deprecate/delete old Swarm chat entry points
- [ ] Remove scripts/run_swarm_chat_api.sh
- [ ] Remove duplicate dashboard documentation

## Phase 8: Update Documentation and Runbooks

### 8.1 Architecture Documentation
- [ ] Revise docs/deployment/README.md for unified architecture
- [ ] Update docs/setup/SECRETS.md
- [ ] Include interaction diagrams (Swarm, agents, orchestrator, memory, AI router)

### 8.2 API Reference
- [ ] Create docs/api_reference.md
- [ ] Document all unified MCP server endpoints
- [ ] Document request/response schemas

### 8.3 Operational Runbooks
- [ ] Create runbook for scaling orchestrator
- [ ] Create runbook for rotating secrets
- [ ] Create runbook for updating model definitions
- [ ] Create runbook for onboarding new developers

### 8.4 User Documentation
- [ ] Update docs/USER_GUIDE.md
- [ ] Update LOGIN_INSTRUCTIONS.md
- [ ] Provide screenshots/GIFs of new UI
- [ ] Document required environment variables

## Phase 9: Testing, Validation and Deployment

### 9.1 Testing
- [ ] Run existing tests
- [ ] Add new tests for each new endpoint
- [ ] Test unified MCP server functionality
- [ ] Test dashboard integration

### 9.2 Incremental Commits
- [ ] "Migrate coding agent to unified MCP client"
- [ ] "Add GPU endpoints to Enhanced MCP server"
- [ ] "Integrate chat UI with unified MCP server"
- [ ] "Remove legacy dashboard"

### 9.3 Deployment
- [ ] Push changes to main branch
- [ ] Verify CI/CD deploys updated infrastructure
- [ ] Test production deployment
- [ ] Monitor system health

## Completion Criteria

- [ ] All legacy orchestrator code removed or migrated
- [ ] Agents and Swarm orchestrator call unified MCP server through new client libraries
- [ ] Configuration centralized and validated at startup
- [ ] Secrets injected via Kubernetes or vault
- [ ] RAG pipeline uses new MCP architecture by default
- [ ] Dashboard shows real-time metrics and memory browser
- [ ] Updated documentation and runbooks present in docs/
- [ ] Single front-end application with integrated chat, missions, analytics, memory browsing
- [ ] Chat component communicates with Enhanced Unified MCP Server
- [ ] Hard-coded IPs and ports removed
- [ ] Old dashboards removed or marked as deprecated

## Current Status: Phase 1 - Starting Implementation

