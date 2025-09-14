# Pulumi ESC Guide

We store real secrets in Pulumi ESC and map them to canonical env keys per environment (dev/staging/prod).

Structure
- ESC org: `sophia`
- Environments: `dev`, `staging`, `prod`
- Secret groups: `ai_providers`, `datastores`, `infra_tokens`, `mcp`

Mapping
- See `esc/esc_mapping.yaml` for key → secret path mapping.

Local Development
- Use `.env.master` placeholders. Do not copy real keys locally.
- Optional helper may materialize dev secrets to env at runtime via `pulumi esc env` (not committed).

CI/CD Injection
- Deploy pipelines fetch secrets from ESC and expose as container env vars.
- Example (pseudo):
  - `pulumi esc env get sophia/${ENV} --json | jq ...` → export as step env
  - Application receives process env; loaders do not read files in prod.

Rotation
- Rotate keys in ESC; no Git changes needed.
- Re-run deployments to pick up rotated values.

Audit
- ESC maintains history; use `pulumi esc` commands for audit reports.

