Secrets Policy and Rotation

Summary
- Never commit secrets to the repository. Use `<repo>/.env.master` (chmod 600) as the single source of truth.
- `.env` is git-ignored and must not contain real credentials in commits. Use `.env.template` for placeholders only.
- Rotate any keys that were ever committed.

Immediate Actions
- Rotate exposed tokens in historical commits (Slack, Asana, Sentry, etc.).
- Replace repository `.env` with a blank stub (done) and sanitize `.env.template` (done).
- All processes inherit environment from `./sophia start`. No interactive prompts; missing file prints one-line fix.

How to Store Secrets Locally
- Create `<repo>/.env.master` with `KEY=VALUE` lines (chmod 600 enforced).
- Example keys: `OPENROUTER_API_KEY`, `AUTH_TOKEN`, `POSTGRES_URL`, `REDIS_URL`.

Runtime Verification
- `make status` to check API (8000), Bridge/Legacy (8003), MCP (8081/8082/8084).
- `python3 scripts/smoke_test.py` to run a minimal E2E smoke.

Bridge Auth
- Set `AUTH_TOKEN` and/or `ENFORCE_AUTH=true` in your environment to require a specific token.
- The Builder UI uses a dev token (`Bearer dev-token`). Update the token or set `AUTH_TOKEN=dev-token` locally.
