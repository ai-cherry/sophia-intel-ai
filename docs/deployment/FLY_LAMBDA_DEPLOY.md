# Cloud Deployment — Fly.io + Lambda Labs

This repo standardizes on Fly.io for app deployment and uses Lambda Labs Cloud Services for GPU capacity when needed.

## Prerequisites
- Install flyctl: `curl -L https://fly.io/install.sh | sh`
- Login: `flyctl auth login` or `export FLY_API_TOKEN=... && flyctl auth token $FLY_API_TOKEN`
- Ensure secrets are not in the repo. Place local values in `<repo>/.env.master` and pass to Fly using `fly secrets set`.

## Unified API (8000)
- Deploy: `fly deploy -c deploy/fly-unified-api.toml`
- Health: `https://<app>.fly.dev/api/health`
- Secrets (examples):
  - `fly secrets set OPENAI_API_KEY=... ANTHROPIC_API_KEY=... OPENROUTER_API_KEY=...`
  - `fly secrets set POSTGRES_URL=... REDIS_URL=...`
  - `fly secrets set LAMBDA_API_TOKEN=... LAMBDA_CLOUD_ENDPOINT=https://cloud.lambdalabs.com/api/v1`

## UI (Next.js on 3000)
- Deploy: `fly deploy -c deploy/fly-ui.toml`
- Point UI to API: `NEXT_PUBLIC_API_BASE=https://sophia-api.fly.dev`
- Set via secrets/env in Fly config as needed.

## Lambda Labs Integration
- Store token in Fly secrets: `fly secrets set LAMBDA_API_TOKEN=...`
- In-app code should read `LAMBDA_API_TOKEN` and `LAMBDA_CLOUD_ENDPOINT` to schedule GPU jobs.

## Notes
- No Render configs are used. Fly.io is the cloud provider of record for app deployment.
- MCP servers may run as part of the unified API or as separate services if needed; for now, they are managed in local dev and via app processes.
