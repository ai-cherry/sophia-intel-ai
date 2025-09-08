# SOPHIA Unified Design Plan

## Architecture Overview
- State management: Zustand (already in use via `agent-ui/src/store.ts`).
- Real-time: Primary WebSocket with SSE fallback; centralize in a `RealtimeManager`.
- API layer: typed fetch wrappers; consolidate endpoints in `agent-ui/src/api`.
- Module structure: Dashboards, Chat, Streams, MCP, Model Registry, Analytics, Playground.
- Shared widget library: charts, cards, status, stream display.

## Key Modules To Create/Consolidate
- `lib/realtime/RealtimeManager.ts`: single connection manager with auto-retry and SSE fallback.
- `lib/api/client.ts`: fetch/axios wrapper with interceptors and error normalization.
- `lib/state/unifiedStore.ts`: thin layer reusing Zustand slices for dashboards/chat.
- `components/widgets/*`: extract shared cards, tables, charts from dashboards.
- `components/chat/*`: unify ChatArea and hooks around `useAIStreamHandler`.

## Roadmap (11 Weeks)
- Weeks 1–2: Core infrastructure (RealtimeManager, API client, store slices).
- Weeks 3–4: Extract shared widgets from dashboards; standardize props.
- Weeks 5–6: CommandCenter: compose dashboards into unified routes/layout.
- Week 7: Chat consolidation across Playground and Stream displays.
- Week 8: Agent orchestration UI harmonization (swarm, MCP status, prompts).
- Week 9: Intelligence hub integrations (analytics, cost/model registry).
- Week 10: Testing and performance; storybook for widgets.
- Week 11: Deployment playbook; feature flags and rollout.

## Cross-References
- Dashboards to widgets: see UNIFICATION_REPORT for extraction targets.
- Chat to streams: consolidate around `hooks/useAIStreamHandler.tsx`.
- Realtime hotspots: top files under `top_files.realtime`.
- API hotspots: top files under `top_files.api_calls`.
