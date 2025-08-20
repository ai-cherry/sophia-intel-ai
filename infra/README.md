# Sophia Intel Infra (Pulumi + Fly.io)

## Prereqs
- `flyctl` installed and authenticated (`fly auth login`)
- Docker + access to the GitHub Container Registry (GHCR)
- `FLY_API_TOKEN` exported in environment or set as Pulumi config `fly:token`

## Config
Pulumi config for production is defined in `Pulumi.production.yaml`. Do **not** store secrets here.
- App list & Docker settings
- Registry settings

## Deploy (local)
```bash
cd infra
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pulumi stack select production --create
pulumi up
```

## Apps Deployed
- `sophia-code` - Code generation and operations MCP server
- `sophia-context` - Context and session management MCP server  
- `sophia-memory` - Memory and knowledge management MCP server
- `sophia-research` - Research and data gathering MCP server
- `sophia-business` - Business intelligence MCP server

## Health Checks
Each app exposes:
- `GET /healthz` - Health check endpoint
- `GET /readyz` - Readiness check endpoint
- `GET /metrics` - Prometheus metrics (optional)

## Rollback
```bash
# Scale to 0 (emergency)
flyctl scale count 0 --app sophia-code

# Destroy stack (non-prod only)
pulumi destroy
```

