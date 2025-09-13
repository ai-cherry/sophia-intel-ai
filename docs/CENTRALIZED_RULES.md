# 🚨 CENTRALIZED RULES & POLICIES
*Global rules that ALL agents, CLIs, and orchestrators MUST follow*

## 🏗️ ARCHITECTURE RULES (NEVER VIOLATE)

### Two-App Separation (ABSOLUTE)
1. **Sophia Intel App** = Business intelligence ONLY
2. **Builder Agno System** = Code/infrastructure ONLY  
3. **NO cross-contamination** between apps
4. **NO additional dashboard apps** - everything goes in one of the two

### Dashboard Rules
- **All dashboards MUST be tabs/pages** within existing apps
- **NO standalone dashboard URLs**
- **NO one-off dashboard services**
- Business dashboards → Sophia Intel App
- Technical dashboards → Builder Agno System

## 🔐 SECRETS & CONFIGURATION

### Centralized Secrets (MANDATORY)
- **ALL secrets** go in `<repo>/.env.master`
- **NO scattered .env files**
- **NO hardcoded secrets**
- Load secrets using `app/core/env.load_env_once()` or `builder_cli/lib/env.load_central_env()`

### Model Governance (ENFORCED)
- **Approved models only**: gpt-5, claude-4.1-sonnet, claude-4.1-opus, grok-code-fast-1
- **Blocked models**: gpt-4o, claude-3.5-sonnet, claude-3-haiku, legacy families
- **Runtime enforcement** - no exceptions

## 🤖 AGENT FACTORY RULES

### Sophia Intel Agent Factory
- **Business agents only**: BI, analytics, reporting, sales, customer success
- **Data sources**: Gong, Slack, Asana, PayReady systems
- **NO code generation agents**

### Builder Agno Agent Factory  
- **Technical agents only**: Code generation, infrastructure, DevOps, testing
- **Data sources**: GitHub, AWS, Docker, CI/CD systems
- **NO business intelligence agents**

### Shared Infrastructure (ALLOWED)
- Both factories can use same MCP services
- Both can connect to Unified API
- Both read from centralized secrets
- **BUT agents stay in domain boundaries**

## 📊 LOGGING & MONITORING

### Centralized Logging (REQUIRED)
- All logs go to `logs/` directory
- Standard log files: `sophia.log`, `builder.log`, `mcp.log`, `api.log`
- Use structured logging with timestamps

### Health Monitoring (REQUIRED)
- All services MUST expose `/health` endpoint
- Health checks run every 30 seconds
- Failed services trigger alerts

## 🔄 INTEGRATION PATTERNS

### MCP Service Usage (STANDARD)
- **Memory MCP** (8081): Session memory, temporary data
- **Filesystem MCP** (8082): Code indexing, symbol search, file operations
- **Git MCP** (8084): Repository operations, change tracking

### API Integration (STANDARD)
- **Unified API** (8010): Backend services for both apps
- **RESTful patterns**: Use standard HTTP methods
- **Authentication**: Bearer tokens from centralized secrets

## 🚫 FORBIDDEN PRACTICES

### What NOT to Do
1. **NO multiple dashboard apps**
2. **NO scattered secrets** (.env files everywhere)  
3. **NO cross-app agent contamination**
4. **NO bypassing centralized configuration**
5. **NO hardcoded endpoints or tokens**
6. **NO deprecated model usage**

### Enforcement
- Pre-commit hooks check for violations
- CI/CD pipelines enforce rules
- Runtime validation blocks non-approved patterns

## 📚 KNOWLEDGE SHARING (CONTROLLED)

### Allowed Cross-App Learning
- **Patterns and architectures** (how to structure agents)
- **Integration techniques** (how to connect to MCP)
- **Performance optimizations** (how to make agents faster)

### Forbidden Cross-App Sharing
- **Agent code** (no copying agents between apps)
- **Domain-specific logic** (business vs. technical stays separate)
- **App-specific configurations** (each app owns its config)

---
*These rules are ENFORCED by automation and must be followed by all agents, CLIs, and humans*
