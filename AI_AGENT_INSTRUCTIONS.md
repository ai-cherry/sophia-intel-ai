# 🚨 CRITICAL INSTRUCTIONS FOR AI AGENTS WORKING ON SOPHIA INTEL APP

## THE ONE RULE
**There is ONE Sophia Intel App. Do NOT create new apps, dashboards, or duplicates.**

## Directory Map - USE THESE EXACT PATHS

### Main Application (DO NOT CREATE NEW APPS)
- `sophia-intel-app/` – The ONLY dashboard (Next.js). All dashboards live here.
- `app/` – Unified FastAPI backend (business intelligence API)
- `sophia_cli.py` – Canonical CLI entry (delegates to `builder_cli/`)

### Business Logic (DO NOT RECREATE)
- `app/sophia/sophia_orchestrator.py` - Main orchestrator
- `app/sophia/unified_factory.py` - Agent factory
- `app/integrations/*.py` - 21 existing integrations

### MCP Servers (ALREADY EXIST)
- `mcp/memory_server.py` - Port 8081
- `mcp/git_server.py` - Port 8084
- `mcp_servers/sophia_intel_mcp.py` - Main MCP

### DO NOT TOUCH (Legacy/Backups)
- `sophia-intel-app/` - Old duplicate, ignore
- `dashboard_backup_*/` - Old backups, ignore

## When Asked to Add Features

1. **CHECK FIRST**: Does it already exist in `app/integrations/`?
2. **USE EXISTING**: Add dashboards/pages in `sophia-intel-app/` only
3. **NEVER CREATE**: Separate dashboard apps or frameworks

## Port Allocations (FIXED)
- 3000: Agent UI (Sophia Dashboard)
- 8003: Sophia API (FastAPI)
- 8004: Builder Bridge API (dev codegen)
- 8081: Memory MCP
- 8082: Filesystem MCP
- 8084: Git MCP

## Integration Pattern
```python
# ALWAYS use existing integrations like this:
from app.integrations.salesforce_optimized_client import SalesforceClient
from app.integrations.slack_optimized_client import SlackClient
# DO NOT create new integration files
```

## Startup Commands
```bash
# Preferred (Docker):
make all   # UI 3000, API 8003, DBs, MCPs

# Native (ARM64 convenience):
scripts/arm64/deploy.sh
```

## Environment Variables
All secrets go in `<repo>/.env.master` (single source). Start services via `./sophia` to export env to all children.

## If You're Confused
1. Read `docs/SOPHIA_ARCHITECTURE.md`
2. Check existing code in `app/sophia/`
3. Do NOT create anything new without checking if it exists

## FORBIDDEN ACTIONS
❌ Creating new Next.js apps
❌ Creating new React apps
❌ Creating new dashboards
❌ Using create-react-app
❌ Making new UI frameworks
❌ Duplicating existing services
❌ Creating mock integrations
❌ Making demo data

## REQUIRED ACTIONS
✅ Add dashboards in `sophia-intel-app/`
✅ Use existing integrations in `app/integrations/`
✅ Use existing MCP servers
✅ Follow port allocations above
✅ Check if feature exists before creating

Remember: SOPHIA INTEL APP IS ALREADY BUILT. Your job is to enhance and fix, not recreate.
