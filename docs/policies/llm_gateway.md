# LLM Gateway Policy (Portkey/OpenRouter Only)

Purpose
- Enforce a single gateway for all LLM and embedding calls to ensure observability, cost control, and model routing without vendor SDK drift.

Rules
- All app/CLI code must send LLM and embedding requests through the configured gateway base URL (Portkey → OpenRouter virtual key or equivalent).
- No direct imports of provider SDKs (e.g., `openai`, `anthropic`) in application code outside the gateway adapter.
- No vendor keys in code, env files, or compose. Only gateway credentials are allowed at runtime.

Configuration
- Base URL: `http://localhost:8080` (dev) or gateway URL per environment.
- Auth: `PORTKEY_API_KEY` (and virtual keys managed inside gateway).
- Model aliases are defined centrally in gateway config; application refers to logical names (e.g., `planner.smart`, `coder.fast`).

Validation
- CI guard fails on `import openai|anthropic` usage outside gateway adapters.
- Portkey logs must show 100% of LLM calls.

