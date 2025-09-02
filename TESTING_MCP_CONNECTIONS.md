# Testing MCP Connections: Roo, Cline, and Claude

## Overview
This guide provides step-by-step instructions to verify connections for all external tools to the MCP server. All tests assume:
- MCP server running on `http://localhost:8004`
- API running on `http://localhost:8003`
- Bridge built with `npm run build` in `mcp-bridge/`

---

## 🛠️ 1. Roo/Cursor (IDE Integration)

### Configuration
1. Create `.cursor/mcp.json` in your project root:
```json
{
  "servers": {
    "sophia": {
      "command": "node",
      "args": [
        "/path/to/sophia-intel-ai/mcp-bridge/dist/roo-adapter.js"
      ]
    }
  }
}
```

2. **Replace `/path/to/sophia-intel-ai`** with your actual project path

### Verification Steps
1. Open Cursor IDE
2. Create a new file and type:
   ```
   Call search_code_patterns for main.py through Sophia's MCP.
   ```
3. **Expected Output**:
   ```
   ✅ MCP connection established
   🔍 Found 3 relevant code patterns in main.py
   ```
4. **Troubleshooting**:
   - If connection fails: `lsof -i :8004` to verify MCP server is running
   - Check adapter path in `.cursor/mcp.json` matches your file system

---

## 💻 2. Cline (VS Code)

### Configuration
1. Add to `settings.json` in VS Code:
```json
{
  "cline.mcp.servers": {
    "sophia": {
      "command": "node",
      "args": [
        "/path/to/sophia-intel-ai/mcp-bridge/dist/cline-adapter.js"
      ]
    }
  }
}
```

2. **Replace `/path/to/sophia-intel-ai`** with your actual path

### Verification Steps
1. Open VS Code
2. Type in a new file:
   ```
   Use analyze_project via the Sophia MCP connection to confirm link.
   ```
3. **Expected Output**:
   ```
   ✅ MCP connection established
   📁 Project analysis complete (12 files processed)
   ```
4. **Troubleshooting**:
   - If connection fails: `curl http://localhost:8004/health` to verify server
   - Check for path errors in `settings.json`

---

## 🖥️ 3. Claude Desktop (Terminal)

### Configuration
1. Update `claude.config.json`:
```json
{
  "mcpServers": {
    "sophia-mcp": {
      "command": "node",
      "args": [
        "/path/to/sophia-intel-ai/mcp-bridge/dist/claude-adapter.js"
      ],
      "env": {
        "MCP_SERVER_URL": "http://localhost:8004",
        "REDIS_URL": "redis://localhost:6379"
      }
    }
  }
}
```

2. **Replace `/path/to/sophia-intel-ai`** with your actual path

### Verification Steps
1. Start Claude Desktop
2. In chat, type:
   ```
   Use get_context via the Sophia MCP server.
   ```
3. **Expected Output**:
   ```
   ✅ MCP connection established
   📌 Context retrieved: "Project structure analysis complete"
   ```
4. **Troubleshooting**:
   - If connection fails: `ps aux | grep claude-adapter` to verify process
   - Check `MCP_SERVER_URL` matches your local port

---

## 🔍 Universal Verification Checklist

| Step | Command/Action | Expected Result |
|------|----------------|----------------|
| 1 | `curl http://localhost:8004/health` | `{"status":"healthy","mcp_server":"running"}` |
| 2 | `lsof -i :8004` | Shows `node` process listening on port 8004 |
| 3 | Test any of the sample prompts above | ✅ MCP connection established |
| 4 | Check logs for `mcp-bridge` | No errors in adapter startup |

---

## ⚠️ Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Connection timeout | MCP server not running | `docker-compose -f docker-compose.minimal.yml up -d mcp-server` |
| Path not found | Incorrect adapter path | Verify path in config files matches actual location |
| Authentication error | Missing MCP_API_KEY | Add `MCP_API_KEY` to environment variables |
| Memory operations fail | Redis not running | `docker-compose -f docker-compose.minimal.yml up -d redis` |

---

## 📌 Final Notes

1. **Always build the bridge first**:
   ```bash
   cd mcp-bridge && npm run build && cd ..
   ```

2. **Verify MCP server is ready** before starting adapters:
   ```bash
   curl http://localhost:8004/health
   ```

3. **All tools should now share the same memory**:
   - Any `store_memory` call from one tool is visible to others
   - `search_memory` queries return results from all connected tools

This setup completes the MCP ecosystem, enabling all external tools to share a single memory layer with consistent configuration and reliable connections.