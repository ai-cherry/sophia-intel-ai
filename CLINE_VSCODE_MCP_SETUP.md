# 🔧 Cline/VS Code MCP Integration Setup

## Sophia Intel AI - Model Context Protocol for Cline/VS Code

**Setup Status:** ✅ Ready for Connection  
**MCP Server:** <http://localhost:8000>  
**Protocol:** MCP 1.0  
**Cline Extension:** Enhanced with MCP Support

---

## 🚀 Quick Setup Instructions

### 1. Ensure MCP Server is Running

```bash
# Start the MCP verification server
cd sophia-intel-ai
python3 mcp_verification_server.py

# Verify server is running (should show healthy status)
curl http://localhost:8000/healthz
```

### 2. VS Code Cline Extension Configuration

Your VS Code is already configured with MCP support in `.vscode/settings.json`:

```json
{
  "cline.mcpServers": {
    "sophia": {
      "command": "node",
      "args": ["./mcp-bridge/dist/cline-adapter.js"],
      "env": {
        "MCP_SERVER_URL": "http://localhost:8000",
        "LOG_LEVEL": "info",
        "REDIS_URL": "redis://localhost:6379",
        "WORKSPACE_ID": "sophia-intel-ai"
      }
    }
  },
  "cline.enableMcp": true,
  "cline.mcpTimeout": 30000
}
```

### 3. Install/Update Cline Extension

1. **Open VS Code** in the `sophia-intel-ai` directory
2. **Install Cline Extension** (if not already installed):
   - Press `Ctrl+Shift+X` (Extensions)
   - Search for "Cline"
   - Install the latest version with MCP support
3. **Reload VS Code** to activate MCP integration

### 4. Verify Prerequisites

```bash
# Check Redis is running
redis-cli ping
# Should respond: PONG

# Check Node.js and MCP bridge
cd mcp-bridge
npm install  # If needed
ls -la dist/  # Should show cline-adapter.js
```

---

## 🧠 Cline MCP Commands

### Memory Management

```
/mcp store "Working on AI swarm orchestration system"
/mcp search "swarm"
/mcp recall "previous swarm work"
```

### Task Management

```
/mcp task create "Implement multi-agent debate system"
/mcp task list
/mcp task status <task-id>
/mcp task complete <task-id>
```

### Code Context

```
/mcp context save "Current file: improved_swarm.py"
/mcp context load "swarm implementation"
/mcp context share "debugging agent communication"
```

### Cross-Tool Sync

```
/mcp sync workspace
/mcp broadcast "Starting Phase 5 implementation"
/mcp status
```

---

## 🎯 Enhanced Cline Features with MCP

### 1. Persistent Task Memory

```
# Create a task that persists across sessions
/mcp task create "Refactor swarm communication system" --priority high --type refactor

# Add context to the task
/mcp task context <task-id> "Located in app/swarms/communication/message_bus.py"

# Assign dependencies
/mcp task depend <task-id> "Complete MCP integration testing"
```

### 2. Smart Code Generation

```
# Generate code with shared context
/mcp generate "Create a new agent type for code review" --context swarm-system

# Use cross-tool memory for better context
/mcp code improve "Use previous discussions from Cursor about swarm architecture"
```

### 3. Advanced Project Management

```
# Track project progress
/mcp project status sophia-intel-ai

# Set project milestones
/mcp milestone create "Phase 5: AI Swarm Intelligence" --date "2024-10-01"

# Link tasks to milestones
/mcp task assign <task-id> --milestone "Phase 5"
```

---

## 🔧 Advanced Configuration

### Enhanced .vscode/settings.json

```json
{
  "cline.mcpServers": {
    "sophia": {
      "command": "node",
      "args": ["./mcp-bridge/dist/cline-adapter.js"],
      "env": {
        "MCP_SERVER_URL": "http://localhost:8000",
        "LOG_LEVEL": "debug",
        "REDIS_URL": "redis://localhost:6379",
        "WORKSPACE_ID": "sophia-intel-ai",
        "ENABLE_TASK_MANAGEMENT": "true",
        "ENABLE_CODE_CONTEXT": "true",
        "ENABLE_CROSS_TOOL_SYNC": "true",
        "MAX_MEMORY_ENTRIES": "1000",
        "MEMORY_RETENTION_DAYS": "30"
      }
    }
  },
  "cline.enableMcp": true,
  "cline.mcpTimeout": 30000,
  "cline.mcpRetryAttempts": 3,
  "cline.autoSaveContext": true,
  "cline.contextSaveInterval": 300000,
  "cline.enableWebSocket": true
}
```

### Custom Environment File (.env.cline)

```bash
# Cline MCP Configuration
MCP_SERVER_URL=http://localhost:8000
MCP_API_KEY=sophia-mcp-key
REDIS_URL=redis://localhost:6379

# Cline-specific settings
CLINE_WORKSPACE_ID=sophia-intel-ai
CLINE_USER_PROFILE=developer
CLINE_AUTO_SAVE_CONTEXT=true
CLINE_CONTEXT_DEPTH=deep

# Task management
ENABLE_TASK_TRACKING=true
TASK_AUTO_ASSIGNMENT=true
TASK_PRIORITY_SYSTEM=true

# Code generation
ENABLE_SMART_GENERATION=true
USE_PROJECT_PATTERNS=true
RESPECT_CODE_STYLE=true
```

---

## 🚦 Testing MCP Integration

### Test 1: Basic MCP Connection

1. Open VS Code in `sophia-intel-ai`
2. Open Cline panel (usually in sidebar)
3. Type: `/mcp status`
4. Should show: "✅ Connected to Sophia MCP Server"

### Test 2: Memory Operations

```
# Store memory
/mcp store "Testing Cline MCP integration - all systems working"

# Search memory
/mcp search "MCP integration"

# Should return the stored memory
```

### Test 3: Task Management

```
# Create a task
/mcp task create "Test MCP task creation" --type test

# List tasks
/mcp task list

# Should show the created task
```

### Test 4: Cross-Tool Communication

```
# Send a message to other connected tools
/mcp broadcast "Cline MCP connection verified and working"

# Check workspace context
/mcp workspace

# Should show current project status
```

---

## 🔍 Troubleshooting Guide

### Issue: Cline Not Recognizing MCP Commands

**Solution 1: Restart VS Code**

```bash
# Close VS Code completely
# Reopen in project directory
code sophia-intel-ai
```

**Solution 2: Check Extension Version**

- Ensure Cline extension supports MCP
- Update to latest version if needed

**Solution 3: Verify Configuration**

```bash
# Check settings file
cat .vscode/settings.json | grep -A 20 "mcpServers"
```

### Issue: MCP Server Connection Failed

**Check Server Status:**

```bash
curl http://localhost:8000/healthz
```

**Restart Server if Needed:**

```bash
pkill -f mcp_verification_server
python3 mcp_verification_server.py
```

### Issue: Redis Connection Problems

**Start Redis:**

```bash
redis-server &
redis-cli ping  # Should return PONG
```

**Check Redis Configuration:**

```bash
redis-cli config get bind
redis-cli config get port
```

### Issue: Node.js/Adapter Problems

**Reinstall MCP Bridge:**

```bash
cd mcp-bridge
npm install
npm run build
ls -la dist/cline-adapter.js  # Should exist
```

---

## 🎯 Advanced Usage Patterns

### 1. Autonomous Development Workflow

```
# Start a complex development task
/mcp task create "Implement AI swarm consensus algorithm" --type feature --priority high

# Add detailed context
/mcp context save "Requirements: Multi-agent voting system with Byzantine fault tolerance"

# Generate initial implementation
/mcp generate "Create consensus algorithm class with voting methods"

# Track progress automatically
/mcp task progress <task-id> 25%
```

### 2. Cross-Tool Development Session

```
# Start session with shared context
/mcp session start "Phase 5 Implementation"

# Share current work with other tools
/mcp share "Working on swarm orchestration in improved_swarm.py"

# Get updates from other tools
/mcp sync updates

# End session with summary
/mcp session end "Completed consensus algorithm base structure"
```

### 3. Code Review Workflow

```
# Create review task
/mcp task create "Review swarm communication refactor" --type review

# Add code context
/mcp context file app/swarms/communication/message_bus.py

# Generate review checklist
/mcp generate checklist "Code review for message bus implementation"

# Track review progress
/mcp task checklist <task-id> --item "Check error handling" --status completed
```

---

## 📊 MCP Integration Features

### ✅ Fully Functional

- **Memory Persistence**: Store and retrieve development context
- **Task Management**: Create, track, and complete development tasks
- **Code Context**: Automatic context awareness for better AI assistance
- **Cross-Tool Sync**: Real-time synchronization with Cursor and Claude
- **Project Tracking**: Monitor development progress and milestones
- **Smart Generation**: Context-aware code generation

### 🔧 Available Commands

| Command          | Description             | Example               |
| ---------------- | ----------------------- | --------------------- |
| `/mcp status`    | Check connection status | Shows server health   |
| `/mcp store`     | Store memory/context    | Store current work    |
| `/mcp search`    | Search memories         | Find previous work    |
| `/mcp task`      | Task management         | Create/track tasks    |
| `/mcp context`   | Context operations      | Save/load context     |
| `/mcp sync`      | Cross-tool sync         | Sync with other tools |
| `/mcp workspace` | Workspace status        | Project overview      |
| `/mcp broadcast` | Send messages           | Notify other tools    |

---

## 🚀 Success Indicators

When Cline MCP integration is working correctly:

1. **✅ Command Recognition**: `/mcp` commands are recognized and autocomplete
2. **✅ Server Connection**: `/mcp status` shows connected state
3. **✅ Memory Operations**: Can store and retrieve context successfully
4. **✅ Task Management**: Tasks are created and tracked properly
5. **✅ Cross-Tool Sync**: Context is shared with Cursor/Roo automatically
6. **✅ Enhanced AI**: Cline provides better assistance with shared context
7. **✅ Real-time Updates**: Changes appear in other connected tools

**Ready for advanced AI-assisted development with Cline! 🎉**
