# 🎯 Correct Naming Convention - OFFICIAL

## We Agreed On These Names:

### 1. **Sophia Intel App** (NOT sophia-intel-app)
- **Location**: `/sophia-intel-app/`
- **Purpose**: B2B Business Intelligence Platform
- **Port**: 3000
- **Description**: Executive dashboard for business metrics, team performance, integrations

### 2. **Agno Builder App**
- **Location**: `/agno-builder-app/`
- **Purpose**: AI Agent Development Platform
- **Port**: 3001
- **Description**: Developer tool for building AI agents and swarms

### 3. **LiteLLM Builder App**
- **Location**: `/litellm-builder-app/`
- **Purpose**: Intelligent AI Routing System
- **Port**: 8090
- **Description**: Cost-optimized model routing for coding tasks

## Current Issues to Fix:

1. **WRONG**: The UI is currently in `/sophia-intel-app/` directory
   **CORRECT**: Should be `/sophia-intel-app/`

2. **WRONG**: References to "sophia-intel-app" throughout the codebase
   **CORRECT**: Should reference "sophia-intel-app"

3. **WRONG**: Generic "agent" terminology
   **CORRECT**: Specific app names with clear purposes

## Directory Structure (CORRECT):

```
sophia-intel-ai/
├── apps/
│   ├── sophia-intel-app/      ✅ (Business Intelligence)
│   ├── agno-builder-app/       ✅ (AI Agent Builder)
│   └── litellm-builder-app/    ✅ (AI Routing Engine)
│
├── services/
│   ├── unified-api/            ✅ (Port 8000)
│   ├── mcp-servers/            ✅ (Ports 8081-8084)
│   └── litellm-router/         ✅ (Port 8090)
│
└── libs/
    ├── shared-components/      ✅
    ├── ai-agents/              ✅
    └── research-tools/         ✅
```

## Quick Fix Commands:

```bash
# 1. Rename the directory
mv sophia-intel-app sophia-intel-app

# 2. Update package.json
sed -i 's/"name": "sophia-intel-app"/"name": "sophia-intel-app"/g' sophia-intel-app/package.json

# 3. Update all imports
find . -type f -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | \
  xargs sed -i 's/sophia-intel-app/sophia-intel-app/g'

# 4. Update documentation
find . -type f -name "*.md" | \
  xargs sed -i 's/sophia-intel-app/sophia-intel-app/g'

# 5. Update environment variables
sed -i 's/AGENT_UI/SOPHIA_INTEL_APP/g' .env.example
```

## Naming Philosophy:

1. **Sophia Intel App**: Named after the main product - Sophia Intel AI for business intelligence
2. **Agno Builder App**: "Agno" (from Latin "agnosco" - to recognize/understand) for building intelligent agents
3. **LiteLLM Builder App**: Named after the LiteLLM routing technology it's built on

## Why This Matters:

- **Clarity**: Each app has a distinct identity and purpose
- **Professionalism**: "Sophia Intel" sounds like a real product, not a generic tool
- **Searchability**: Unique names make it easier to find specific components
- **Branding**: Consistent naming builds product identity

## Action Items:

1. ✅ Rename `/sophia-intel-app/` to `/sophia-intel-app/`
2. ✅ Update all references in code
3. ✅ Update documentation
4. ✅ Update Docker/deployment configs
5. ✅ Update README files
6. ✅ Ensure consistent naming everywhere

---

**Remember**: 
- **Sophia Intel App** = Business Intelligence Dashboard
- **Agno Builder App** = AI Agent Development
- **LiteLLM Builder App** = Intelligent Routing

**NO MORE "sophia-intel-app"!**