# Proof Artifacts

This folder stores **real evidence** for every deploy.

## Structure
- `healthz/` — `curl -i` of each service's `/healthz` (headers + body)
- `endpoints/` — JSON results from functional endpoint calls (e.g., research.search, context.search)
- `manifest-*.json` — machine-readable status snapshots (optional)
- `manifest-snapshot.json` — latest workflow snapshot (run_id, commit, timestamp)

## Policy
- No mocks or simulations. If a dependency is missing, the service must return **normalized error JSON**.
- Every PR must attach proofs for the services it touches.

## How to verify locally
```bash
curl -i https://sophia-code.fly.dev/healthz
curl -i https://sophia-research.fly.dev/healthz
curl -i https://sophia-context-v42.fly.dev/healthz

# Endpoints (examples)
curl -sS -X POST https://sophia-research.fly.dev/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"AI orchestration platforms","max_sources":5}' | jq .

curl -sS -X POST https://sophia-context-v42.fly.dev/context/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"AgentManager create_swarm","k":5}' | jq .
```
