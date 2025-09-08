# UI Library Primitives (Migration Guide)

This folder collects new primitives to unify streaming, API calls, and state management without breaking existing views.

- `api/client.ts` — Typed API client wrapping `fetch` with JSON parsing and error normalization. Use for new endpoints and to gradually replace ad-hoc `fetch`.
- `realtime/RealtimeManager.ts` — Centralized WS/SSE manager (reconnect + pub/sub). Wire into hotspots incrementally.
- `state/unifiedStore.ts` — Unified Zustand store with small slices (`chat`, `swarm`, `metrics`). Coexists with `src/store.ts` during migration.

Recommended adoption path
- Start with non-invasive wrappers (e.g., `useUnifiedStream`) that proxy existing hooks while updating unified store state.
- Convert top API hotspots to `ApiClient` where it adds error handling value.
- Introduce `RealtimeManager` for live widgets; keep it behind feature flags initially.

Environment
- `NEXT_PUBLIC_API_URL` defaults to `http://localhost:8003`
- `NEXT_PUBLIC_ENABLE_AGNO_BRIDGE` toggles the bridge status indicator

Telemetry and feature flags
- ApiClient timings: pass a `category` in request options; timings feed `useUnifiedStore().updateLatency(category, ms)`.
- Unified stream timing: `useUnifiedStream` measures end-to-end chat stream and records `chat.stream` latency.
- Debug panel: set `NEXT_PUBLIC_SHOW_METRICS_DEBUG=1|true` to render a latency/budget panel.
- RealtimeManager trial: set `NEXT_PUBLIC_USE_REALTIME_MANAGER=1|true` to enable flagged widgets.
- Unified chat reader (planned): `NEXT_PUBLIC_USE_UNIFIED_CHAT=1|true` to read chat from `unifiedStore`.

Example (ApiClient with timings)
```ts
import { ApiClient } from '@/lib/api/client'
import { useUnifiedStore } from '@/lib/state/unifiedStore'

const client = new ApiClient('', (cat, ms) => useUnifiedStore.getState().updateLatency(cat, ms))
const data = await client.get('/api/model-registry/providers', { category: 'api.modelRegistry.providers' })
```

No secrets in repo. Configure runtime via env or your local config manager.
