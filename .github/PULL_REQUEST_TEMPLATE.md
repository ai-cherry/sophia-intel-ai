## Summary

- [ ] Scope: Sophia BI only (coding UI is external; no UI changes in this repo)
- [ ] Portkey-only LLM usage (no direct provider SDKs/keys)
- [ ] Domain separation respected (no Sophia↔Builder blending)
- [ ] Secrets policy respected (no keys in repo; uses <repo>/.env.master only)

## Changes

- What changed and why?

## Validation

- Commands run locally (build/tests/linters):
- Portkey routing validated (if applicable):

## Checklist

- [ ] No `/health` endpoint duplication (uses /healthz and /api/health)
- [ ] No introduction of UI directories or builder references (no `builder-agno-system`, no `frontend/`)
- [ ] Docs updated if behavior/process changed (AGENTS.md, docs/AGENTS_CONTRACT.md)
