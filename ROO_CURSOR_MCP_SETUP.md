# 🎯 Roo/Cursor MCP Integration Setup
## Sophia Intel AI - Model Context Protocol for Roo/Cursor

**Setup Status:** ✅ Ready for Connection  
**MCP Server:** http://localhost:8000  
**Protocol:** MCP 1.0

---

## 🚀 Quick Setup Instructions

### 1. Ensure MCP Server is Running
```bash
# Start the MCP verification server
cd sophia-intel-ai
python3 mcp_verification_server.py

# Verify server is running
curl http://localhost:8000/healthz
```

### 2. Roo/Cursor MCP Configuration

The MCP configuration is already set up in your project at `.cursor/mcp.json`:

```json
{
    "mcpServers": {
        "sophia-mcp": {
            "command": "node",
            "args": ["./mcp-bridge/dist/roo-adapter.js"],
            "env": {
                "MCP_SERVER_URL": "http://localhost:8000",
                "LOG_LEVEL": "info",
                "REDIS_URL": "redis://localhost:6379"
            }
        }
    }
}
```

### 3. Verify Redis is Running
```bash
# Test Redis connection
redis-cli ping
# Should respond with: PONG
```

### 4. Test MCP Connection in Cursor/Roo

1. **Open Cursor/Roo** in the `sophia-intel-ai` directory
2. **Enable MCP** in Cursor settings (if not auto-enabled)
3. **Check MCP Status** - Look for Sophia MCP server in the status bar
4. **Test Shared Memory** - Try this:

```
@sophia-mcp store this context: "Working on MCP integration with Cursor"
```

---

## 🧠 Available MCP Commands

### Memory Management
- `@sophia-mcp store [context]` - Store development context
- `@sophia-mcp search [query]` - Search shared memories
- `@sophia-mcp workspace` - Get current workspace context

### Code Context Sharing
- `@sophia-mcp sync` - Sync current file context
- `@sophia-mcp share [description]` - Share current code context
- `@sophia-mcp recall [project]` - Recall project context

### Cross-Tool Collaboration
- `@sophia-mcp broadcast [message]` - Send message to other tools
- `@sophia-mcp status` - Check MCP connection status
- `@sophia-mcp history` - View shared context history

---

## 🔧 Advanced Configuration

### Custom Environment Variables
Create a `.env.cursor` file in your project root:

```bash
# MCP Configuration for Cursor
MCP_SERVER_URL=http://localhost:8000
MCP_API_KEY=sophia-mcp-key
LOG_LEVEL=debug
ENABLE_WEBSOCKET=true
ENABLE_REAL_TIME_SYNC=true

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_KEY_PREFIX=cursor:

# Cursor-specific settings
CURSOR_WORKSPACE_ID=sophia-intel-ai
CURSOR_USER_ID=your-username
CURSOR_SESSION_ID=auto-generated
```

### Performance Tuning
```json
{
    "mcpServers": {
        "sophia-mcp": {
            "command": "node",
            "args": ["./mcp-bridge/dist/roo-adapter.js"],
            "env": {
                "MCP_SERVER_URL": "http://localhost:8000",
                "LOG_LEVEL": "info",
                "MEMORY_CACHE_SIZE": "100",
                "WEBSOCKET_TIMEOUT": "30000",
                "RETRY_ATTEMPTS": "3"
            }
        }
    }
}
```

---

## 🚦 Connection Testing

### Test 1: Basic Connectivity
```bash
# In Cursor/Roo terminal
curl http://localhost:8000/healthz
```

### Test 2: Memory Store
```
@sophia-mcp store "Test memory from Cursor - MCP working!"
```

### Test 3: Memory Search
```
@sophia-mcp search "MCP working"
```

### Test 4: Workspace Sync
```
@sophia-mcp workspace
```

---

## 🔍 Troubleshooting

### Issue: MCP Server Not Found
```bash
# Check if server is running
ps aux | grep mcp_verification_server
# If not running, start it:
python3 mcp_verification_server.py
```

### Issue: Redis Connection Failed
```bash
# Start Redis if not running
redis-server
# Test connection
redis-cli ping
```

### Issue: Node.js Dependencies
```bash
# Install MCP bridge dependencies
cd mcp-bridge
npm install
npm run build
```

### Issue: Port 8000 Already in Use
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process and restart MCP server
kill -9 <PID>
python3 mcp_verification_server.py
```

---

## 📊 Expected Behavior

### ✅ Working Correctly
- **Status Bar**: Shows "Sophia MCP: Connected"
- **Autocomplete**: `@sophia-mcp` appears in suggestions
- **Memory Commands**: Store/search commands work
- **Context Sharing**: Can share code context between tools
- **Real-time Sync**: Changes appear in other connected tools

### ❌ Common Issues
- **Status**: "MCP: Disconnected" or no MCP status
- **Commands**: `@sophia-mcp` not recognized
- **Errors**: Connection timeout or server unreachable
- **No Sync**: Context not shared between tools

---

## 🎯 Usage Examples

### Store Code Context
```
@sophia-mcp store "Currently working on the swarm orchestration system in app/swarms/improved_swarm.py. The main challenge is implementing multi-agent debate systems with consensus building."
```

### Search for Related Work
```
@sophia-mcp search "swarm orchestration"
```

### Share Current File Context
```
@sophia-mcp sync "Reviewing the message bus implementation for cross-agent communication"
```

### Get Workspace Status
```
@sophia-mcp workspace
```

---

## 🔗 Integration with Other Tools

### With Cline/VS Code
The MCP server enables seamless context sharing:
- **Shared Memory**: Both tools access the same memory store
- **Real-time Updates**: Changes in one tool appear in the other
- **Cross-references**: Code references work across tools

### With Claude Desktop
Full integration for:
- **Project Context**: Shared understanding of codebase
- **Code History**: Access to previous conversations
- **Development State**: Current progress and challenges

---

## 📝 Configuration Files

Your project already includes these configured files:
- ✅ `.cursor/mcp.json` - Cursor MCP configuration
- ✅ `mcp-bridge/dist/roo-adapter.js` - Roo/Cursor adapter
- ✅ `mcp_verification_server.py` - MCP server
- ✅ `MCP_INTEGRATION_VERIFICATION_REPORT.md` - Verification results

---

## 🎉 Success Indicators

When everything is working correctly, you should see:

1. **Cursor Status**: MCP server connected indicator
2. **Command Availability**: `@sophia-mcp` commands work
3. **Memory Persistence**: Stored contexts are retrievable
4. **Cross-tool Sync**: Context shared with VS Code/Cline
5. **Real-time Updates**: Live synchronization active

**Ready to code with enhanced AI collaboration! 🚀**