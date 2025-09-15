# MCP Server Connection & Verification Guide
## Complete Instructions for Cline, Roo, and AI Agents

---

## 🚀 Quick Start Verification

### Step 1: Verify All MCP Servers Are Running

```bash
# Run the comprehensive validation script
python3 scripts/validate_mcp_servers.py --verbose

# Expected output: All servers showing "✓ HEALTHY"
```

### Step 2: Quick Health Check

```bash
# Memory Server (Port 8081)
curl -X GET http://localhost:8081/health \
  -H "Authorization: Bearer dev-token"
# Expected: {"status":"healthy","redis":"connected"}

# Filesystem Server (Port 8082)  
curl -X GET http://localhost:8082/health \
  -H "Authorization: Bearer dev-token"
# Expected: {"status":"ok"}

# Git Server (Port 8084)
curl -X GET http://localhost:8084/health \
  -H "Authorization: Bearer dev-token"
# Expected: {"status":"ok","ssh_agent":"running"}
```

---

## 📋 MCP Server Capabilities

### Memory Server (Port 8081)
- **Purpose**: Store and retrieve context between operations
- **Key Features**: Session management, Redis persistence, semantic search
- **Use Cases**: 
  - Store conversation context
  - Remember previous decisions
  - Share state between agents

### Filesystem Server (Port 8082)
- **Purpose**: File operations and code intelligence
- **Key Features**: Read/write files, symbol indexing, repository search
- **Use Cases**:
  - Read project files
  - Write new code
  - Search for patterns
  - Index symbols

### Git Server (Port 8084)
- **Purpose**: Version control operations
- **Key Features**: Status, commits, branches, history
- **Use Cases**:
  - Check repository status
  - View commit history
  - Manage branches

---

## 🔌 Connection Configuration

### For Cline (VS Code Extension)

**Configuration Location**: `../workbench-ui/.cline/mcp_settings.json`

```json
{
  "mcpServers": {
    "memory": {
      "type": "http",
      "url": "http://localhost:8081",
      "headers": {
        "Authorization": "Bearer dev-token"
      },
      "capabilities": ["memory", "context"]
    },
    "filesystem": {
      "type": "http", 
      "url": "http://localhost:8082",
      "headers": {
        "Authorization": "Bearer dev-token"
      },
      "capabilities": ["fs", "code_intelligence"]
    },
    "git": {
      "type": "http",
      "url": "http://localhost:8084",
      "headers": {
        "Authorization": "Bearer dev-token"
      },
      "capabilities": ["git", "version_control"]
    }
  }
}
```

### For Claude Desktop

**Configuration Location**: `mcp_configs/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sophia-memory": {
      "type": "http",
      "url": "http://localhost:8081",
      "headers": {
        "Authorization": "Bearer dev-token"
      }
    },
    "sophia-filesystem": {
      "type": "http",
      "url": "http://localhost:8082",
      "headers": {
        "Authorization": "Bearer dev-token"
      }
    },
    "sophia-git": {
      "type": "http",
      "url": "http://localhost:8084",
      "headers": {
        "Authorization": "Bearer dev-token"
      }
    }
  }
}
```

---

## 🧪 Test Each Server Connection

### Test Memory Server

```bash
# 1. Create a session
curl -X POST http://localhost:8081/sessions/test-session/memory \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"content":"Test memory storage"}'

# 2. Retrieve the memory
curl -X GET http://localhost:8081/sessions/test-session/memory \
  -H "Authorization: Bearer dev-token"

# 3. Search memories
curl -X GET "http://localhost:8081/search?query=test" \
  -H "Authorization: Bearer dev-token"
```

### Test Filesystem Server

```bash
# 1. List files in current directory
curl -X POST http://localhost:8082/fs/list \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"path":"."}'

# 2. Read a file
curl -X POST http://localhost:8082/fs/read \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"path":"README.md"}'

# 3. Search repository
curl -X POST http://localhost:8082/repo/search \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"query":"MCP","max_results":5}'
```

### Test Git Server

```bash
# 1. Get repository status
curl -X GET http://localhost:8084/status \
  -H "Authorization: Bearer dev-token"

# 2. Get recent commits
curl -X GET "http://localhost:8084/log?limit=5" \
  -H "Authorization: Bearer dev-token"

# 3. List branches
curl -X GET http://localhost:8084/branches \
  -H "Authorization: Bearer dev-token"
```

---

## 🎯 Using MCP in Your Code

### Python Example

```python
import requests

class MCPClient:
    def __init__(self):
        self.headers = {"Authorization": "Bearer dev-token"}
        self.memory_url = "http://localhost:8081"
        self.fs_url = "http://localhost:8082"
        self.git_url = "http://localhost:8084"
    
    def store_memory(self, session_id, content):
        response = requests.post(
            f"{self.memory_url}/sessions/{session_id}/memory",
            json={"content": content},
            headers=self.headers
        )
        return response.json()
    
    def read_file(self, path):
        response = requests.post(
            f"{self.fs_url}/fs/read",
            json={"path": path},
            headers=self.headers
        )
        return response.json()
    
    def get_git_status(self):
        response = requests.get(
            f"{self.git_url}/status",
            headers=self.headers
        )
        return response.json()

# Usage
client = MCPClient()
client.store_memory("agent-1", "Task completed successfully")
content = client.read_file("README.md")
status = client.get_git_status()
```

### TypeScript Example

```typescript
class MCPClient {
  private headers = { 'Authorization': 'Bearer dev-token' };
  private memoryUrl = 'http://localhost:8081';
  private fsUrl = 'http://localhost:8082';
  private gitUrl = 'http://localhost:8084';

  async storeMemory(sessionId: string, content: string) {
    const response = await fetch(
      `${this.memoryUrl}/sessions/${sessionId}/memory`,
      {
        method: 'POST',
        headers: { ...this.headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      }
    );
    return response.json();
  }

  async readFile(path: string) {
    const response = await fetch(
      `${this.fsUrl}/fs/read`,
      {
        method: 'POST',
        headers: { ...this.headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
      }
    );
    return response.json();
  }

  async getGitStatus() {
    const response = await fetch(
      `${this.gitUrl}/status`,
      { headers: this.headers }
    );
    return response.json();
  }
}

// Usage
const client = new MCPClient();
await client.storeMemory('agent-1', 'Task completed');
const content = await client.readFile('README.md');
const status = await client.getGitStatus();
```

---

## 🔍 Troubleshooting

### Server Not Responding

```bash
# Check if server is running
ps aux | grep -E "(memory|filesystem|git)_server"

# Check port availability
lsof -i :8081  # Memory
lsof -i :8082  # Filesystem
lsof -i :8084  # Git

# Restart servers if needed
./startup.sh
```

### Authentication Errors

```bash
# Verify token in request
curl -v -X GET http://localhost:8081/health \
  -H "Authorization: Bearer dev-token"

# Check server logs
tail -f logs/mcp_memory.log
tail -f logs/mcp_filesystem.log
tail -f logs/mcp_git.log
```

### Connection Refused

```bash
# Verify servers are listening
netstat -an | grep -E "(8081|8082|8084)"

# Test localhost connectivity
ping localhost
telnet localhost 8081
```

---

## 📊 Monitoring Server Health

### Automated Health Monitoring

```bash
# Run continuous health monitoring
watch -n 5 'python3 scripts/validate_mcp_servers.py --quick'
```

### Manual Health Checks

```bash
# Create a health check script
cat > check_mcp_health.sh << 'EOF'
#!/bin/bash
echo "🔍 Checking MCP Server Health..."
echo ""

echo "Memory Server (8081):"
curl -s -X GET http://localhost:8081/health \
  -H "Authorization: Bearer dev-token" | jq '.'

echo ""
echo "Filesystem Server (8082):"
curl -s -X GET http://localhost:8082/health \
  -H "Authorization: Bearer dev-token" | jq '.'

echo ""
echo "Git Server (8084):"
curl -s -X GET http://localhost:8084/health \
  -H "Authorization: Bearer dev-token" | jq '.'
EOF

chmod +x check_mcp_health.sh
./check_mcp_health.sh
```

---

## ✅ Verification Checklist

Before using MCP servers, ensure:

- [ ] All servers show "healthy" or "ok" status
- [ ] Authentication with "Bearer dev-token" works
- [ ] Memory server can store and retrieve data
- [ ] Filesystem server can list and read files
- [ ] Git server shows repository status
- [ ] Configuration files are properly updated
- [ ] Network connectivity to localhost ports works
- [ ] Redis is running (for Memory server)
- [ ] SSH agent is running (for Git server)

---

## 🚨 Emergency Commands

```bash
# Stop all MCP servers
pkill -f "mcp.*server"

# Restart all servers
./startup.sh

# Check all logs
tail -f logs/mcp_*.log

# Full system validation
python3 scripts/validate_mcp_servers.py --verbose

# Reset Redis (Memory server)
redis-cli FLUSHALL

# Clear server caches
rm -rf .cache/mcp_*
```

---

## 📚 Additional Resources

- **Full API Documentation**: [`docs/MCP_INTEGRATION_GUIDE.md`](MCP_INTEGRATION_GUIDE.md)
- **Server Implementation**: `mcp/` directory
- **Validation Script**: [`scripts/validate_mcp_servers.py`](../scripts/validate_mcp_servers.py)
- **Startup Script**: [`startup.sh`](../startup.sh)
- **Configuration Examples**: `mcp_configs/` directory

---

## 🎉 Success Confirmation

When everything is working correctly, you should see:

1. **Validation Script Output**:
```
✅ All MCP servers are healthy and operational!
```

2. **Health Check Responses**:
- Memory: `{"status":"healthy","redis":"connected"}`
- Filesystem: `{"status":"ok"}`
- Git: `{"status":"ok","ssh_agent":"running"}`

3. **Successful Operations**:
- Can store and retrieve memories
- Can read and write files
- Can query git status

---

*Last Updated: [Current Date]*
*Version: 1.0 - MCP HTTP Integration*