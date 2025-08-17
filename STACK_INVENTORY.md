# SOPHIA Intel Stack Inventory for Northflank Migration

## Current Architecture Overview

### Core Services
1. **Enhanced Unified MCP Server** (`mcp_servers/enhanced_unified_server.py`)
   - Primary orchestrator with Lambda AI integration
   - Handles chat, reasoning, code generation, and analysis
   - Port: 5002 (current deployment)

2. **SOPHIA Backend** (`backend/simple_main.py`)
   - FastAPI application with Lambda Inference API
   - Chat endpoints, health checks, model management
   - Port: 5002

3. **React Dashboard** (`apps/dashboard/`)
   - Modern React UI with Vite build system
   - Chat interface, web research, knowledge management
   - Port: 3003 (current deployment)

### MCP Servers (13 Python files)
- `enhanced_unified_server.py` - Main orchestrator
- `ai_router.py` - AI model routing logic
- `code_analysis_mcp_server.py` - Code analysis capabilities
- `code_mcp_server.py` - Code generation and management
- `memory_service.py` - Memory and context management
- `notion_server.py` - Notion integration

### Legacy Services (to be consolidated)
- `apps/api-gateway/` - Legacy API gateway
- `apps/mcp-services/embedding-mcp-server/` - Embedding service
- `apps/mcp-services/notion-sync-mcp-server/` - Notion sync

## Environment Variables & Secrets

### Lambda AI Integration
- `LAMBDA_API_KEY`: secret_sophiacloudapi_17cf7f3cedca48f18b4b8ea46cbb258f.EsLXt0lkGlhZ1Nd369Ld5DMSuhJg9O9y

### DNS Management
- `DNSIMPLE_API_KEY`: dnsimple_u_XBHeyhH3O8uKJF6HnqU76h7ANWdNvUzN

### Database & Storage
- `QDRANT_URL`: (Vector database for embeddings)
- `NOTION_API_KEY`: (Notion integration)
- `POSTGRES_URL`: (If using PostgreSQL)
- `REDIS_URL`: (If using Redis for caching)

### API Endpoints
- `ORCHESTRATOR_URL`: http://localhost:5002
- `API_BASE_URL`: https://api.sophia-intel.ai

## Current Deployment Status

### Working Components
✅ **Enhanced Unified MCP Server**: Running on port 5002 with Lambda AI
✅ **React Dashboard**: Built and serving on port 3003
✅ **Lambda Integration**: 19 AI models available and responding
✅ **Knowledge Base**: 16 documentation chunks embedded

### Issues to Address
⚠️ **Chat Interface**: Frontend-backend API integration needs fixing
⚠️ **CORS Configuration**: Cross-origin requests need proper handling
⚠️ **Environment Variables**: Need centralized secret management

## Northflank Migration Plan

### Services to Deploy
1. **sophia-api** - Enhanced Unified MCP Server (FastAPI)
2. **sophia-dashboard** - React frontend (Static site)
3. **sophia-mcp-memory** - Memory service
4. **sophia-mcp-notion** - Notion integration
5. **sophia-mcp-code** - Code analysis and generation

### Addons Needed
- **PostgreSQL** - Primary database
- **Redis** - Caching and session management
- **Qdrant** - Vector database for embeddings (external or self-hosted)

### Domains
- **Primary**: www.sophia-intel.ai
- **API**: api.sophia-intel.ai
- **Dashboard**: app.sophia-intel.ai

## Next Steps
1. Create Northflank project and secret groups
2. Build Docker images for each service
3. Create Infrastructure-as-Code templates
4. Set up GitOps workflows
5. Migrate DNS to point to Northflank
6. Verify all functionality
7. Decommission Lambda infrastructure

