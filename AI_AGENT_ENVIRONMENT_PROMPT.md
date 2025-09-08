# AI Agent Environment Setup Prompt

## 🤖 FOR ALL AI CODING AGENTS WORKING IN SOPHIA-INTEL-AI

Copy and paste this prompt to any AI agent (Claude, GPT-4, etc.) working on this codebase:

---

## ENVIRONMENT CONTEXT - CRITICAL SETUP

You are working in the **sophia-intel-ai** multi-agent coding environment. **All API keys and credentials are pre-configured in a secure location.**

### 🔐 SECURE CONFIGURATION (NEVER REQUEST KEYS)

**API Keys Location**: `~/.config/artemis/env` (88+ keys configured)
**Validation Command**: `make env.check`

### ✅ IMMEDIATE SETUP VERIFICATION

Before starting ANY work, run:
```bash
make env.check
# Must show: "✅ Found artemis env: /Users/lynnmusil/.config/artemis/env"
```

### 🚨 MANDATORY AGENT REQUIREMENTS

1. **NEVER ask users for API keys** - they're already configured
2. **NEVER create .env files with secrets** - use secure location
3. **ALWAYS validate environment first** with `make env.check`
4. **USE containerized development** with `make dev-up`
5. **FOLLOW secure patterns** documented in ENVIRONMENT_GUIDE.md

### 🚀 DEVELOPMENT WORKFLOW

```bash
# 1. Validate environment (REQUIRED)
make env.check

# 2. Start multi-agent stack
make dev-up

# 3. Check all services
make status

# 4. Test provider access
make grok-test

# 5. Enter development shell
make dev-shell

# 6. Run swarm tasks
make swarm-start TASK="your task description"
```

### 🔧 AVAILABLE SERVICES

**LLM Providers** (all configured):
- OpenAI (GPT-4, GPT-3.5-turbo)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- XAI/Grok (Grok-2)
- OpenRouter (300+ models)
- Groq, DeepSeek, Gemini, Mistral, Perplexity

**Infrastructure**:
- Redis: localhost:6379
- Weaviate: localhost:8080
- MCP Memory: localhost:8081
- MCP Filesystem: localhost:8082
- MCP Git: localhost:8084

**Docker Services**: All APIs accessible in containers automatically

### 📚 KEY DOCUMENTATION

1. **ENVIRONMENT_GUIDE.md** - Complete setup guide
2. **ARTEMIS_SETUP_COMPLETE.md** - Implementation details
3. **docker-compose.multi-agent.yml** - Service configuration
4. **MULTI_AGENT_PLAN_ADDENDUM.md** - Architecture overview

### ⚠️ COMMON MISTAKES TO AVOID

❌ **DON'T**: Ask "Do you have an OpenAI API key?"
✅ **DO**: Run `make env.check` and proceed

❌ **DON'T**: Create `.env` files with secrets
✅ **DO**: Use `~/.config/artemis/env`

❌ **DON'T**: Install dependencies outside container
✅ **DO**: Use `make dev-shell` for containerized development

### 🎯 SUCCESS CRITERIA

Before starting work, verify:
- ✅ `make env.check` passes
- ✅ Docker services running (`make status`)
- ✅ SSH agent configured (for Git operations)
- ✅ No API key requests from user

### 🔄 ENVIRONMENT UPDATES

If you find outdated environment instructions:
1. **Flag for cleanup** - note conflicting documentation
2. **Follow current guide** - use ENVIRONMENT_GUIDE.md as authority
3. **Update or deprecate** - old env patterns in documentation

---

**This environment is production-ready with 88+ API keys configured securely. Focus on coding, not configuration.**