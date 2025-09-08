# Agno ↔ UI Wiring Plan (Refined)

Objectives
- Connect Agno core (agents/teams/orchestrator) to Next.js UI via FastAPI bridge.
- Enable real-time chat, agent management, analytics, and playground embedding.
- Voice/TTS support via UI extensions; monitoring via health endpoints.
- Strict separation of concerns per AGENTS.md (no secrets in repo; no cross-imports between repos).

What We Learned From Code
- Next.js app already uses Zustand (`agent-ui/src/store.ts`).
- Realtime patterns: heavy WebSocket usage, some SSE; no Socket.io.
- API usage: 64 `fetch` calls, no `axios`.
- Dashboards: 11; Chat components: 19. See UNIFICATION_REPORT.md.

Architecture Updates
- Keep single UI app; avoid micro-frontends.
- Centralize realtime in `lib/realtime/RealtimeManager.ts` (future work) built on native WebSocket with SSE fallback.
- Typed API client in `lib/api/client.ts` (future work) wrapping `fetch` with auth and error normalization.
- Bridge: `agno_ui_bridge.py` (FastAPI) with JWT and CORS; default port 8003 to match UI defaults.

Phases
1) Foundation
   - Add `setup_agno_core.py` to scaffold `agno_core` and `orchestrator` with `/health`.
   - Verify structure created; no secrets checked in.
2) Bridge
   - Add `agno_ui_bridge.py` with CORS allowlist (env `UI_ORIGINS`) and JWT (env `BRIDGE_SECRET`).
   - Provide `/health`, `/chat` (skeleton), `/ws/{client_id}` (echo skeleton) with token validation.
3) UI Integration (next steps)
   - Add `lib/realtime/RealtimeManager.ts`, `lib/api/client.ts`, and small slices in Zustand.
   - Wire top realtime/API hotspots (see IMPLEMENTATION_ROADMAP.md) first.
4) Unified Launch
   - `launch_sophia.sh` starts bridge and UI with health wait; keeps logs attached.

Security & Ops
- CORS restricted via `UI_ORIGINS` env; JWT via `BRIDGE_SECRET`.
- No secrets in repo; prefer `~/.config/artemis/env` or process env.
- Health: `/health` on bridge and orchestrator.

Timeline (4–5 days)
- Day 1: Foundation + Bridge
- Days 2–3: UI integration (RealtimeManager/API client) over hotspots
- Day 4: Stabilize, tests, rollout via feature flags
- Day 5: Buffer

Deliverables Done
- `setup_agno_core.py`, `agno_ui_bridge.py`, `launch_sophia.sh` committed.
- Analysis artifacts: `UNIFICATION_REPORT.md`, `IMPLEMENTATION_ROADMAP.md`.

