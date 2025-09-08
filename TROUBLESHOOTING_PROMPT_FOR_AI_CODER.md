# AI Agent Swarm UI Local Deployment Troubleshooting Guide

## Context

You are helping fix a React/Next.js UI (agent-ui) that connects to a Python FastAPI backend (unified_server.py) for an AI agent swarm system. The UI runs on port 3000, the API runs on port 8003, but there are persistent connection and data mapping issues.

## Current Issues to Fix

### 1. Port/URL Drift Issues

**Problem**: UI keeps trying to connect to port 8000 (old cached value) instead of 8003
**Root Cause**: localStorage persists old endpoint under 'endpoint-storage' key from Zustand store

**Solutions to Implement**:

```typescript
// agent-ui/src/store.ts - Add migration to fix cached endpoints
persist: {
  name: 'endpoint-storage',
  version: 2, // Bump version
  migrate: (persistedState: any, version: number) => {
    const state = persistedState as any;
    // Force migration from old ports to new
    if (state.selectedEndpoint) {
      if (state.selectedEndpoint.includes(':8000') ||
          state.selectedEndpoint.includes(':7777')) {
        state.selectedEndpoint = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';
      }
    }
    return state;
  },
  onRehydrateStorage: () => (state) => {
    // Clean up legacy keys
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('swarm-endpoint');
      } catch {}
    }
  }
}
```

### 2. Next.js Rewrites for Development

**Problem**: Hardcoded URLs cause CORS issues and port confusion
**Solution**: Add Next.js rewrites to proxy API calls

```typescript
// agent-ui/next.config.ts
const nextConfig = {
  async rewrites() {
    const apiBase = process.env.API_BASE_URL || "http://localhost:8003";
    return [
      {
        source: "/api/:path*",
        destination: `${apiBase}/:path*`,
      },
    ];
  },
};
```

### 3. Select Component Empty Value Crash

**Problem**: Radix Select.Item crashes when value prop is empty string
**Location**: agent-ui/src/components/playground/Sidebar/EntitySelector.tsx

**Fix in API transforms**:

```typescript
// agent-ui/src/api/playground.ts
export const getPlaygroundAgentsAPI = async (
  selectedEndpoint: string,
): Promise<ComboboxAgent[]> => {
  const response = await fetchJSON(
    `${buildEndpointUrl(selectedEndpoint, "/agents")}`,
  );
  const data = await response.json();

  // Normalize and filter out invalid entries
  const agents: ComboboxAgent[] = data
    .map((item: any) => ({
      value: item.agent_id || item.id || item.name || "",
      label: item.name || item.id || item.agent_id || "Unnamed Agent",
      model: {
        provider: item.model?.provider || item.model_pool || "unknown",
      },
      storage: !!item.storage,
    }))
    .filter((agent: ComboboxAgent) => agent.value !== "");

  if (data.length !== agents.length) {
    console.warn(
      `Filtered out ${data.length - agents.length} agents with empty values`,
    );
  }

  return agents;
};

// Similar fix for getPlaygroundTeamsAPI
```

**Fix in EntitySelector**:

```typescript
// agent-ui/src/components/playground/Sidebar/EntitySelector.tsx
const safeValue = useMemo(() => {
  if (!value) return '';
  const exists = currentEntities.some(e => e.value === value);
  return exists ? value : '';
}, [value, currentEntities]);

// In Select component
<Select value={safeValue} onValueChange={onValueChange}>
```

### 4. API Response "No solution generated" Error

**Problem**: Backend returns nested response but UI expects flat content
**Location**: app/api/unified_server.py

**Add helper function**:

```python
# app/api/unified_server.py
def _extract_solution(result: dict) -> str:
    """Extract actual solution content from nested response structures"""
    if not result:
        return "Error: No result received"

    # Try common paths for content
    paths_to_try = [
        lambda r: r.get('content'),
        lambda r: r.get('result', {}).get('content'),
        lambda r: r.get('solution'),
        lambda r: r.get('response'),
        lambda r: r.get('final_output'),
        lambda r: r.get('choices', [{}])[0].get('message', {}).get('content') if r.get('choices') else None,
        lambda r: r.get('final_answer'),
        lambda r: r.get('assistant_message'),
    ]

    for path in paths_to_try:
        try:
            content = path(result)
            if content and isinstance(content, str) and content.strip():
                return content
        except (KeyError, IndexError, TypeError):
            continue

    # Last resort - return raw result as string
    if isinstance(result, str):
        return result

    # Log the structure for debugging
    import json
    logger.warning(f"Could not extract solution from structure: {json.dumps(result, indent=2)[:500]}")
    return f"Error: Unable to extract solution from response structure"

# In run_team endpoint
@swarms_router.post("/teams/run")
async def run_team(request: TeamRunRequest):
    # ... existing code ...

    # In non-streaming response section
    content = _extract_solution(result)
    success = not content.startswith("Error:")

    return JSONResponse(content={
        "success": success,
        "content": content,
        "raw": result if not success else None  # Include raw for debugging failures
    })
```

### 5. Route Path Alignment

**Problem**: UI uses /v1/playground/\* but API exposes /teams, /workflows directly

**Fix all route references**:

```typescript
// agent-ui/src/api/routes.ts
export const API_ROUTES = {
  AGENTS: "/agents", // NOT /v1/playground/agents
  TEAMS: "/teams",
  WORKFLOWS: "/workflows",
  TEAM_RUN: "/teams/run",
  WORKFLOW_RUN: "/workflows/run",
  HEALTH: "/healthz",
};
```

### 6. Node.js OOM Errors

**Problem**: Next.js dev server runs out of memory
**Solution**: Set NODE_OPTIONS when starting dev server

```bash
# In package.json scripts or start command
NODE_OPTIONS="--max-old-space-size=4096" npm run dev
```

### 7. Duplicate/Legacy Files Cleanup

**Files to handle**:

- Remove `agent-ui/src/lib/endpointutils.ts` (lowercase) - keep only `endpointUtils.ts`
- Remove or rename old `/ui` directory to `/ui-legacy` if it exists
- Clean Next.js cache: `rm -rf agent-ui/.next`

### 8. Default Endpoint Configuration

**Update all default references**:

```typescript
// agent-ui/src/lib/endpointUtils.ts
export const DEFAULT_ENDPOINT =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8003";
export const DEFAULT_ENDPOINT_CONFIG = {
  url: DEFAULT_ENDPOINT,
  timeout: 10000,
  retries: 3,
  healthPath: "/healthz",
};

// agent-ui/src/components/swarm/EndpointPicker.tsx
// Update placeholder
placeholder = "http://localhost:8003";
```

## Health-Gated Start Script

Create `start-local.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Starting AI Agent Swarm Local Development"

# Kill any existing processes
pkill -f "unified_server" || true
pkill -f "next dev" || true

# Start API server
echo "Starting API server on port 8003..."
cd /path/to/sophia-intel-ai
python app/api/unified_server.py &
API_PID=$!

# Wait for API health
echo "Waiting for API to be healthy..."
MAX_WAIT=30
WAITED=0
until curl -sf http://localhost:8003/healthz > /dev/null; do
  sleep 1
  WAITED=$((WAITED + 1))
  if [ $WAITED -ge $MAX_WAIT ]; then
    echo "❌ API failed to start after ${MAX_WAIT} seconds"
    kill $API_PID 2>/dev/null || true
    exit 1
  fi
  echo -n "."
done
echo " ✅ API is healthy!"

# Start UI with increased memory
echo "Starting UI on port 3000..."
cd agent-ui
rm -rf .next  # Clean cache
NODE_OPTIONS="--max-old-space-size=4096" npm run dev &
UI_PID=$!

# Wait for UI
sleep 5
echo "
✅ Local development environment ready!
   - UI: http://localhost:3000
   - API: http://localhost:8003
   - API Health: http://localhost:8003/healthz
   - Test Page: http://localhost:3000/test-api.html

Press Ctrl+C to stop all services
"

# Wait for interrupt
trap "kill $API_PID $UI_PID 2>/dev/null; exit" INT
wait
```

## Testing Checklist

1. **Clear browser cache/localStorage**:

   - Open Chrome DevTools > Application > Storage > Clear site data
   - Or use incognito mode

2. **Verify endpoints**:

   ```bash
   # API health check
   curl -s http://localhost:8003/healthz

   # Teams endpoint
   curl -s http://localhost:8003/teams

   # Test team run
   curl -X POST http://localhost:8003/teams/run \
     -H "Content-Type: application/json" \
     -d '{"message": "test", "team_id": "coding_team"}'
   ```

3. **Check for port references**:

   ```bash
   # Should return nothing
   rg -n "localhost:8000|:8000|:7777|/v1/playground" agent-ui/src
   ```

4. **Create test page** `agent-ui/public/test-api.html`:

   ```html
   <!doctype html>
   <html>
     <head>
       <title>API Connection Test</title>
       <style>
         body {
           font-family: monospace;
           padding: 20px;
         }
         .test {
           margin: 10px 0;
           padding: 10px;
           border: 1px solid #ccc;
         }
         .success {
           background: #d4edda;
         }
         .error {
           background: #f8d7da;
         }
       </style>
     </head>
     <body>
       <h1>API Connection Test</h1>

       <div id="localStorage-info"></div>

       <button onclick="testEndpoint('http://localhost:8000')">
         Test Port 8000
       </button>
       <button onclick="testEndpoint('http://localhost:8003')">
         Test Port 8003
       </button>
       <button onclick="clearStorage()">Clear LocalStorage</button>

       <div id="results"></div>

       <script>
         // Show localStorage
         document.getElementById("localStorage-info").innerHTML =
           "<h3>LocalStorage:</h3><pre>" +
           JSON.stringify(
             Object.fromEntries(
               Object.entries(localStorage).filter(([k]) =>
                 k.includes("endpoint"),
               ),
             ),
             null,
             2,
           ) +
           "</pre>";

         async function testEndpoint(url) {
           const div = document.createElement("div");
           div.className = "test";

           try {
             const response = await fetch(url + "/healthz");
             if (response.ok) {
               div.className += " success";
               div.innerHTML = `✅ ${url} - Success`;
             } else {
               div.className += " error";
               div.innerHTML = `❌ ${url} - Failed: ${response.status}`;
             }
           } catch (e) {
             div.className += " error";
             div.innerHTML = `❌ ${url} - Error: ${e.message}`;
           }

           document.getElementById("results").appendChild(div);
         }

         function clearStorage() {
           localStorage.clear();
           location.reload();
         }
       </script>
     </body>
   </html>
   ```

## Expected Outcomes After Fixes

1. ✅ UI always connects to port 8003, never 8000
2. ✅ No Select component errors
3. ✅ API returns actual content, not "No solution generated"
4. ✅ All network requests go to correct endpoints
5. ✅ No OOM errors during development
6. ✅ Clean file structure without duplicates
7. ✅ Health-gated startup ensures both services are ready

## Quick Validation Commands

```bash
# After implementing all fixes, run these:

# 1. Start services
./start-local.sh

# 2. In another terminal, validate:
curl -s http://localhost:8003/healthz | jq .
curl -s http://localhost:8003/teams | jq .
curl -X POST http://localhost:8003/teams/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "team_id": "coding_team"}' | jq .

# 3. Open browser
open http://localhost:3000/test-api.html
# Click "Test Port 8003" - should succeed
# Click "Test Port 8000" - should fail

# 4. Open main UI
open http://localhost:3000
# Should connect to 8003 automatically
# Entity selectors should work without errors
```

## Common Pitfalls to Avoid

1. Don't forget to bump Zustand persist version when adding migration
2. Clear .next cache after config changes
3. Use incognito or clear localStorage when testing
4. Ensure NODE_OPTIONS is set before npm run dev
5. Check for case-sensitive duplicate files (endpointUtils vs endpointutils)
6. Verify all imports use the correct file name casing

## Final Notes

This system uses:

- **Frontend**: Next.js 14+ with TypeScript, Zustand for state, Radix UI components
- **Backend**: FastAPI with Python, OpenRouter/Portkey for LLM routing
- **Ports**: UI on 3000, API on 8003
- **Key Issue**: Persistent localStorage overriding code changes - migration fixes this

The core problem is that the UI's Zustand store persists the endpoint selection in localStorage, and old values (8000/7777) override the new defaults (8003). The migration function in the persist configuration is crucial to fixing this permanently.
