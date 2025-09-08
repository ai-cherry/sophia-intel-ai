# Hyper-Detailed MCP Integration Verification Prompt for Claude Coder

## 🚀 Project Context

You are verifying the MCP integration for the Sophia Intel AI platform. The system must enable shared memory across:

- Roo/Cursor (IDE)
- Cline (VS Code)
- Claude Desktop (Terminal)

All components are implemented. Your task is to verify connections using the exact steps below.

## 🔧 Prerequisites (Verify These First)

1. **MCP Server Running**:

   ```bash
   curl http://localhost:8004/health
   ```

   **Expected Output**:

   ```json
   { "status": "healthy", "mcp_server": "running" }
   ```

   **If Not Healthy**:

   ```bash
   docker-compose -f docker-compose.minimal.yml up -d mcp-server
   ```

2. **Bridge Built**:

   ```bash
   cd /Users/lynnmusil/sophia-intel-ai/mcp-bridge && npm run build && cd -
   ```

3. **Port 8004 Free**:

   ```bash
   lsof -i :8004
   ```

   **Expected Output**:

   ```
   COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
   node    12345  lynnmusil   12u  IPv6 123456      0t0  TCP *:8004 (LISTEN)
   ```

## ✅ Verification Steps (Execute in This Order)

### 1. Roo/Cursor Verification

**Step 1**: Open Cursor IDE  
**Step 2**: Create new file `test_roo.md`  
**Step 3**: Type EXACTLY:

```
Call search_code_patterns for main.py through Sophia's MCP.
```

**Expected Output**:

```
✅ MCP connection established
🔍 Found 3 relevant code patterns in main.py
```

**Troubleshooting**:

- If connection fails: `lsof -i :8004` → Verify `node` process exists
- If path error: Check `.cursor/mcp.json` path:

  ```json
  {
    "servers": {
      "sophia": {
        "command": "node",
        "args": [
          "/Users/lynnmusil/sophia-intel-ai/mcp-bridge/dist/roo-adapter.js"
        ]
      }
    }
  }
  ```

### 2. Cline/VS Code Verification

**Step 1**: Open VS Code  
**Step 2**: Create new file `test_cline.md`  
**Step 3**: Type EXACTLY:

```
Use analyze_project via the Sophia MCP connection to confirm link.
```

**Expected Output**:

```
✅ MCP connection established
📁 Project analysis complete (12 files processed)
```

**Troubleshooting**:

- If connection fails: `curl http://localhost:8004/health` → Verify healthy
- If path error: Check `.vscode/settings.json`:

  ```json
  {
    "cline.mcp.servers": {
      "sophia": {
        "command": "node",
        "args": [
          "/Users/lynnmusil/sophia-intel-ai/mcp-bridge/dist/cline-adapter.js"
        ]
      }
    }
  }
  ```

### 3. Shared Memory Verification

**Step 1**: In Roo IDE, run:

```
store_memory "Test from Roo" {"source": "roo"}
```

**Step 2**: In Cline VS Code, run:

```
search_memory "Test from Roo"
```

**Expected Output**:

```
✅ Memory found: "Test from Roo" (source: roo)
```

**Verification**:

- All tools must see the same memory entry
- Check MCP server logs for:

  ```
  [INFO] Memory stored: Test from Roo (source: roo)
  [INFO] Memory retrieved: Test from Roo (source: roo)
  ```

## 🛠️ Critical Path Verification

| Step | Command                             | Expected Output                               | Success |
| ---- | ----------------------------------- | --------------------------------------------- | ------- |
| 1    | `curl http://localhost:8004/health` | `{"status":"healthy","mcp_server":"running"}` | ✅      |
| 2    | `lsof -i :8004`                     | Shows `node` process                          | ✅      |
| 3    | Roo test prompt                     | `✅ MCP connection established`               | ✅      |
| 4    | Cline test prompt                   | `✅ MCP connection established`               | ✅      |
| 5    | Memory store/retrieve               | `✅ Memory found`                             | ✅      |

## ⚠️ Critical Failure Scenarios & Fixes

| Failure                  | Cause                  | Fix                                                             |
| ------------------------ | ---------------------- | --------------------------------------------------------------- |
| `Connection timeout`     | MCP server not running | `docker-compose -f docker-compose.minimal.yml up -d mcp-server` |
| `Path not found`         | Incorrect adapter path | Verify paths in `.cursor/mcp.json` and `.vscode/settings.json`  |
| `Authentication error`   | Missing `MCP_API_KEY`  | Add to `.env.local`: `MCP_API_KEY=your_key`                     |
| `Memory operations fail` | Redis not running      | `docker-compose -f docker-compose.minimal.yml up -d redis`      |

## 📌 Final Verification Checklist

- [ ] MCP server health check returns `healthy`
- [ ] All 3 tools show `✅ MCP connection established`
- [ ] Memory stored in one tool is visible in others
- [ ] No errors in MCP server logs
- [ ] All paths match the exact paths in the config files

## 🎯 Success Criteria

All verification steps must pass with EXACT expected outputs. If any step fails, provide:

1. Exact error message
2. Output of `curl http://localhost:8004/health`
3. Output of `lsof -i :8004`
4. Full config file contents for the failing tool

## 💡 Pro Tip

Run all verification steps in this order:

```bash
# Verify MCP server
curl http://localhost:8004/health

# Verify ports
lsof -i :8004

# Test Roo
# Test Cline
# Test shared memory
```

This prompt contains EVERYTHING needed to verify the MCP integration. No additional information required.
