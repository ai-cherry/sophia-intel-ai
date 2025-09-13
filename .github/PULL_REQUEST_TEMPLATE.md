## Summary

- [ ] Scope: Sophia / Builder (choose one)
- [ ] Portkey-only LLM usage (no direct provider SDKs/keys)
- [ ] Domain separation respected (no Sophia↔Builder blending)
- [ ] Secrets policy respected (no keys in repo; uses ~/.config/sophia/env)

## Changes

- What changed and why?

## Validation

- Commands run locally (build/tests/linters):
- Portkey routing validated (if applicable):

## Checklist

- [ ] No `/health` endpoint duplication (uses /healthz and /api/health)
- [ ] No new cross-imports across `sophia-intel-app` and `builder-agno-system`
- [ ] Docs updated if behavior/process changed (AGENTS.md, docs/AGENTS_CONTRACT.md)

