# Local Stack Runbook (MCP + Unified API + UI)

This is the fastest, repeatable way to bring up everything locally using the centralized env.

## 0) Centralized Env

Create `<repo>/.env.master` and put your keys there (chmod 600):

```
VIDEOSDK_API_KEY=...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=wrxvN1LZJIfL3HHvffqe
PORTKEY_API_KEY=...
MCP_TOKEN=dev-token
```

The app and CLIs load this file automatically.

## 1) One‑shot Bootstrap

```
bash scripts/dev/bootstrap_all.sh
```

What it does:
- Starts MCP (8081/8082/8084), Unified API (8000), UI (3000)
- Prints environment exports for any CLI/agent
- Verifies health for each service

## 2) Health

```
curl -s http://localhost:8000/api/health
curl -s http://localhost:8082/health   # FS MCP
curl -s http://localhost:8081/health   # Memory MCP
curl -s http://localhost:8084/health   # Git MCP
```

## 3) MCP Quick Tests

```
export MCP_FS_URL=http://localhost:8082
export MCP_TOKEN=${MCP_TOKEN:-dev-token}

curl -s \
  -H "Authorization: Bearer $MCP_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"paths":["."],"languages":["python","ts","tsx","js","jsx"]}' \
  "$MCP_FS_URL/symbols/index"

curl -s \
  -H 'Content-Type: application/json' \
  -d '{"query":"WebRTC","globs":["**/*.py"]}' \
  "$MCP_FS_URL/repo/search"
```

## 4) Voice Quick Test

```
curl -s http://localhost:8000/api/voice/health
```

For terminal playback (optional):

```
export VOICE_DISABLE_PLAYBACK=false
curl -s -X POST http://localhost:8000/api/builder/voice/speak \
  -H 'Content-Type: application/json' \
  -d '{"text":"Let\u2019s code this now","context":"coding"}'
```

## 5) Logs

```
tail -f logs/mcp.log logs/api.log logs/ui.log
```

## 6) Docker Alternative

```
docker compose -f infra/docker-compose.yml --profile dev up -d \
  unified-api sophia-intel-app mcp-filesystem mcp-git mcp-memory valkey
```

## 7) Common Gotchas

- Missing MCP token → 401 from FS MCP. Use `MCP_DEV_BYPASS=true` (default in dev) or send `Authorization: Bearer $MCP_TOKEN`.
- Wrong workspace → set `WORKSPACE_PATH` to repo root. Bootstrap script does it for you.
- No browser audio → ensure `pip install av aiortc` and use the WebRTC view in the app; terminal sounds only when `VOICE_DISABLE_PLAYBACK=false`.
