This folder contains small, reusable primitives to unify the UI:

- realtime/RealtimeManager.ts
  Centralizes WebSocket/SSE connections, reconnection, and event pub/sub.

- api/client.ts
  Typed fetch wrapper with JSON parsing and normalized ApiError.

- state/unifiedStore.ts
  Zustand slices for chat, swarm, and metrics. Non-breaking: migrate gradually.

Usage guidance
- Start new realtime features via RealtimeManager; adapt legacy WS/SSE callers incrementally.
- Prefer ApiClient for new HTTP calls; migrate hotspots from analysis report first.
- Read/write to unifiedStore for new chat/swarm features; keep existing store.ts until all views migrate.

