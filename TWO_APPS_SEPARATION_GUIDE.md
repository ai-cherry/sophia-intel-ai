# TWO APPS SEPARATION GUIDE - CRITICAL ARCHITECTURE

## 🚨 STOP AND READ - DO NOT CONSOLIDATE THESE APPS 🚨

This repository contains **TWO COMPLETELY SEPARATE APPLICATIONS** that must NEVER be consolidated:

1. **BUILDER AGNO SYSTEM** - Code generation and multi-agent swarms
2. **SOPHIA INTEL APP** - Business intelligence for PayReady

## NAMING CONVENTIONS - USE THESE EXACT NAMES

### Builder Agno System
- Directory: `builder-agno-system/`
- Component prefix: `BuilderAgno*`
- API prefix: `/api/builder/`
- Port: 8005 (UI and API combined)
- Database: `builder_agno_db`
- Environment prefix: `BUILDER_AGNO_`

### Sophia Intel App
- Directory: `sophia-intel-app/`
- Component prefix: `SophiaIntel*`
- API prefix: `/api/sophia/`
- UI Port: 3000
- API Port: 8003
- Database: `sophia_intel_db`
- Environment prefix: `SOPHIA_INTEL_`

## PORT ASSIGNMENTS - NEVER CHANGE THESE

```
Builder Agno System:    8005  (Combined UI/API)
Sophia Intel UI:        3000  (React/Next.js)
Sophia Intel API:       8003  (FastAPI)
Bridge API:            8004  (Shared services)
MCP Memory Server:      8081  (Memory operations)
MCP Git Server:        8082  (Git operations)
```

## DIRECTORY STRUCTURE - MAINTAIN THIS SEPARATION

```
sophia-intel-ai/
├── builder-agno-system/        # SEPARATE APP - Code Generation
│   ├── src/
│   │   ├── components/         # Builder-specific components
│   │   ├── agents/            # Multi-agent swarms
│   │   ├── api/               # Builder API routes
│   │   └── ui/                # Builder UI
│   ├── package.json           # Separate dependencies
│   ├── tsconfig.json
│   └── README.md              # Builder-specific docs
│
├── sophia-intel-app/           # SEPARATE APP - Business Intelligence
│   ├── src/
│   │   ├── components/         # Sophia-specific components
│   │   ├── integrations/      # Business service integrations
│   │   ├── api/               # Sophia API routes
│   │   └── dashboard/         # Business dashboards
│   ├── package.json           # Separate dependencies
│   ├── tsconfig.json
│   └── README.md              # Sophia-specific docs
│
├── app/                        # Shared backend services
│   ├── api/
│   │   ├── builder/           # Builder backend routes
│   │   └── sophia/            # Sophia backend routes
│   └── shared/                # Shared utilities ONLY
│
└── bridge/                     # Bridge API for shared services

```

## ARCHITECTURE RULES - ENFORCE THESE

### 1. NO CROSS-IMPORTS
```typescript
// ❌ NEVER DO THIS
import { BuilderComponent } from '@builder-agno/components';  // In Sophia app
import { SophiaService } from '@sophia-intel/services';        // In Builder app

// ✅ ALWAYS DO THIS
import { SharedUtil } from '@shared/utils';  // OK to import shared utilities
```

### 2. SEPARATE PACKAGE.JSON FILES
Each app MUST have its own package.json with NO cross-dependencies:

```json
// builder-agno-system/package.json
{
  "name": "@builder-agno/system",
  "version": "2.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 8005",
    "build": "next build",
    "start": "next start -p 8005"
  }
}

// sophia-intel-app/package.json
{
  "name": "@sophia-intel/app",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000"
  }
}
```

### 3. SEPARATE DATABASES
```sql
-- Builder Agno Database
CREATE DATABASE builder_agno_db;

-- Sophia Intel Database
CREATE DATABASE sophia_intel_db;

-- NEVER share tables between databases
```

### 4. SEPARATE ENVIRONMENT VARIABLES
```bash
# Builder Agno System
BUILDER_AGNO_PORT=8005
BUILDER_AGNO_DB_URL=postgresql://...builder_agno_db
BUILDER_AGNO_API_KEY=...

# Sophia Intel App
SOPHIA_INTEL_UI_PORT=3000
SOPHIA_INTEL_API_PORT=8003
SOPHIA_INTEL_DB_URL=postgresql://...sophia_intel_db
SOPHIA_INTEL_API_KEY=...
```

## STARTUP SCRIPTS - USE THESE

### start_builder_agno.sh
```bash
#!/bin/bash
echo "🔨 Starting Builder Agno System on port 8005..."
cd builder-agno-system
npm run dev
```

### start_sophia_intel.sh
```bash
#!/bin/bash
echo "📊 Starting Sophia Intel App..."
echo "  UI on port 3000"
echo "  API on port 8003"

# Start API
cd app
python -m uvicorn api.sophia.main:app --port 8003 &

# Start UI
cd ../sophia-intel-app
npm run dev
```

## COMPONENT NAMING - STRICT CONVENTIONS

### Builder Agno Components
```typescript
// All Builder components start with BuilderAgno
export const BuilderAgnoCodeEditor = () => { ... }
export const BuilderAgnoSwarmManager = () => { ... }
export const BuilderAgnoAgentPanel = () => { ... }
```

### Sophia Intel Components
```typescript
// All Sophia components start with SophiaIntel
export const SophiaIntelDashboard = () => { ... }
export const SophiaIntelMetricsPanel = () => { ... }
export const SophiaIntelRevenueChart = () => { ... }
```

## API ENDPOINTS - CLEAR SEPARATION

### Builder Agno API
```
POST   /api/builder/generate-code
GET    /api/builder/swarms
POST   /api/builder/agents/execute
GET    /api/builder/repositories
```

### Sophia Intel API
```
GET    /api/sophia/metrics
GET    /api/sophia/revenue
POST   /api/sophia/integrations/sync
GET    /api/sophia/dashboards
```

## WHAT EACH APP DOES - NEVER MIX THESE

### Builder Agno System (Port 8005)
- Code generation using AI agents
- Multi-agent swarm orchestration
- Repository management
- Code planning and implementation
- Development workflow automation
- Agno 2.0 stateless architecture

### Sophia Intel App (Ports 3000/8003)
- PayReady business intelligence
- Revenue and metrics tracking
- Customer analytics
- Integration with business services:
  - Gong (sales calls)
  - Slack (communications)
  - Airtable (data)
  - Linear (project management)
  - Asana (tasks)
  - NetSuite (ERP)
  - Looker (analytics)

## RED FLAGS - SIGNS OF CONSOLIDATION

Watch for these signs that someone is consolidating:

1. ❌ Builder components appearing in sophia-intel-app/
2. ❌ Sophia services being imported in builder-agno-system/
3. ❌ Single package.json for both apps
4. ❌ Shared state management between apps
5. ❌ Combined routing in one app
6. ❌ Port 8005 serving Sophia content
7. ❌ Port 3000 serving Builder content
8. ❌ Database tables with mixed purposes
9. ❌ Environment variables without clear prefixes
10. ❌ Startup scripts that launch both apps together

## HOW TO CHECK SEPARATION

Run these commands to verify separation:

```bash
# Check for cross-imports (should return nothing)
grep -r "from '@builder-agno" sophia-intel-app/
grep -r "from '@sophia-intel" builder-agno-system/

# Check ports are correct
lsof -i :8005  # Should show only Builder
lsof -i :3000  # Should show only Sophia UI
lsof -i :8003  # Should show only Sophia API

# Check separate package.json files exist
ls -la builder-agno-system/package.json
ls -la sophia-intel-app/package.json
```

## AI AGENT INSTRUCTIONS

When ANY AI agent (Claude, Codex, Cursor, etc.) works on this codebase:

1. **NEVER** consolidate Builder Agno and Sophia Intel
2. **NEVER** create shared components between them
3. **NEVER** mix their routing or state management
4. **ALWAYS** maintain separate package.json files
5. **ALWAYS** use the exact naming conventions above
6. **ALWAYS** keep ports strictly separated
7. **ALWAYS** prefix environment variables correctly
8. **NEVER** create a "unified" UI that combines both

## ENFORCEMENT

This separation is MANDATORY. Any consolidation breaks the entire architecture and must be immediately reverted. The CEO (Lynn) has explicitly demanded this separation after multiple failed consolidations.

---

**Last Updated**: 2025-01-11
**Status**: ENFORCED
**Owner**: Lynn Musil (CEO)
**Violation Penalty**: Immediate reversion of all changes