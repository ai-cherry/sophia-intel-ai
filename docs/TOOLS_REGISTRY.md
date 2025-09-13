# 🛠️ TOOLS REGISTRY
*Centralized inventory of all available tools, APIs, and services*

## 🔧 MCP SERVICES (Always Available)

### Memory MCP (Port 8081)
- **Purpose**: Session memory, temporary data storage
- **Health**: `http://localhost:8081/health`
- **Endpoints**: 
  - `POST /memory/store` - Store session data
  - `GET /memory/search` - Query stored data
  - `DELETE /memory/clear` - Clear session data
- **Usage**: Both Sophia and Builder agents can store temporary data

### Filesystem MCP (Port 8082)  
- **Purpose**: Code indexing, symbol search, file operations
- **Health**: `http://localhost:8082/health`
- **Endpoints**:
  - `POST /symbols/index` - Index codebase symbols
  - `GET /symbols/search` - Search for symbols
  - `GET /files/read` - Read file contents
  - `POST /deps/graph` - Generate dependency graph
- **Usage**: Primarily Builder agents, but Sophia can read documentation

### Git MCP (Port 8084)
- **Purpose**: Repository operations, change tracking  
- **Health**: `http://localhost:8084/health`
- **Endpoints**:
  - `GET /repo/status` - Git status
  - `POST /repo/commit` - Create commits
  - `GET /repo/history` - Commit history
  - `POST /repo/branch` - Branch operations
- **Usage**: Primarily Builder agents, Sophia for change notifications

## 🌐 UNIFIED API (Port 8010)

### Core Services
- **Health**: `http://localhost:8010/api/health`
- **Documentation**: `http://localhost:8010/docs`
- **Authentication**: Bearer token from centralized secrets

### Voice System
- **WebRTC**: `/api/voice/webrtc`
- **TTS**: `/api/voice/tts` (ElevenLabs integration)
- **STT**: `/api/voice/stt` (VideoSDK integration)

### Model Routing
- **LLM Proxy**: `/api/llm/chat` (Enforces approved models only)
- **Embeddings**: `/api/embeddings/generate`
- **Model Health**: `/api/llm/health`

## 🏢 BUSINESS INTELLIGENCE TOOLS (Sophia Intel Only)

### Gong Integration
- **API**: Gong REST API v2
- **Purpose**: Sales call analysis, deal intelligence  
- **Secret**: `GONG_API_KEY` in centralized env
- **Endpoints**: `/api/sophia/gong/*`

### Slack Integration  
- **API**: Slack Web API
- **Purpose**: Team communication analysis
- **Secret**: `SLACK_TOKEN` in centralized env
- **Endpoints**: `/api/sophia/slack/*`

### PayReady Systems
- **API**: Custom PayReady APIs
- **Purpose**: Payment processing analytics
- **Secret**: `PAYREADY_API_KEY` in centralized env
- **Endpoints**: `/api/sophia/payready/*`

## 💻 DEVELOPMENT TOOLS (Builder Agno Only)

### GitHub Integration
- **API**: GitHub REST/GraphQL API
- **Purpose**: Repository management, code analysis
- **Secret**: `GITHUB_TOKEN` in centralized env  
- **Endpoints**: `/api/builder/github/*`

### Docker Registry
- **API**: Docker Registry HTTP API V2
- **Purpose**: Container management, deployment
- **Secret**: `DOCKER_REGISTRY_TOKEN` in centralized env
- **Endpoints**: `/api/builder/docker/*`

### AWS Services
- **API**: AWS SDK/REST APIs
- **Purpose**: Infrastructure management
- **Secrets**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- **Endpoints**: `/api/builder/aws/*`

## 🔗 SHARED UTILITIES

### Portkey LLM Gateway
- **Purpose**: Model routing, monitoring, caching
- **Secret**: `PORTKEY_API_KEY` in centralized env
- **Usage**: Both apps for LLM requests

### Redis Cache
- **Purpose**: Application caching, session storage
- **Connection**: Configured in Unified API
- **Usage**: Backend caching for both apps

### Monitoring & Logging
- **Grafana**: Metrics visualization (if configured)
- **Log Aggregation**: Centralized to `logs/` directory
- **Health Checks**: All services expose `/health`

## 📊 AGENT FACTORY TOOLS

### Sophia Intel Agent Tools
- **Data Visualization**: Chart.js, D3.js for business dashboards
- **Report Generation**: PDF generation for business reports
- **Data Analysis**: Pandas-equivalent tools for data processing
- **Notification Systems**: Email, Slack notifications for alerts

### Builder Agno Agent Tools
- **Code Generation**: AST manipulation, template engines  
- **Testing Frameworks**: Automated test generation and execution
- **Deployment Automation**: CI/CD pipeline integration
- **Infrastructure as Code**: Terraform, CloudFormation templates

## 🔍 DISCOVERY & REGISTRATION

### Tool Discovery Pattern
1. **Auto-registration**: Services register themselves on startup
2. **Health monitoring**: Regular health checks update availability
3. **Service mesh**: Tools can discover each other via registry
4. **Documentation**: OpenAPI specs auto-generated and served

### Adding New Tools
1. **Register in this document** with endpoints and purpose
2. **Add health check** endpoint
3. **Update centralized secrets** if authentication needed
4. **Assign to appropriate app** (Sophia vs. Builder)

---
*Tools are auto-discovered by agents at startup from this registry*