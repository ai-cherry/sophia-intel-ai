# Claude Configuration for Sophia Intel AI

## Deployment Requirements

### Critical Node Version
- **MUST USE Node 20 LTS** - Node 24 breaks Next.js 14's SWC binary
- Path: `/opt/homebrew/opt/node@20/bin/node`

### Network Binding
- **ALWAYS bind to 127.0.0.1** - Never use localhost or [::1]
- All dev servers must use `-H 127.0.0.1` flag

### Next.js Structure
- Both `app/` and `pages/` directories required
- `pages/index.tsx` must import from `app/page`

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| Sophia Dashboard | 3000 | http://127.0.0.1:3000 |
| Workbench UI | 3001 | http://127.0.0.1:3001 |
| MCP Memory | 8081 | http://127.0.0.1:8081 |
| AI Orchestrator | 8000 | http://127.0.0.1:8000 |

## Quick Commands

```bash
# Start Sophia Dashboard
/opt/homebrew/opt/node@20/bin/node node_modules/next/dist/bin/next dev -H 127.0.0.1 -p 3000

# Check status
ai_status

# Deploy all services
~/deploy-all-services.sh
```

## Business Integrations

### Production (7)
- Looker, Gong, Slack, HubSpot, Asana, Linear, Airtable

### Scaffolding (3)
- Microsoft 365, UserGems, Intercom

## Testing
```bash
npm run validate:architecture
python tests/integration/business_integration_test_suite.py
```