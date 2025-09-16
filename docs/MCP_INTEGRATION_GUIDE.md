# MCP Server Integration Guide for AI Agents
## Complete Instructions for Cline, Roo, and Other AI Extensions

---

## 🚀 Current MCP Server Status

All MCP servers are **OPERATIONAL** and ready for integration:

| Server | Port | Status | Health Endpoint | Base URL |
|--------|------|--------|-----------------|----------|
| **Memory** | 8081 | ✅ Healthy | `/health` | `http://localhost:8081` |
| **Filesystem** | 8082 | ✅ Healthy | `/health` | `http://localhost:8082` |
| **Git** | 8084 | ✅ Healthy | `/health` | `http://localhost:8084` |

---

## 📡 Connection Configuration

### For Cline

Update your Cline MCP settings (`~/.cline/mcp_settings.json` or project `.cline/mcp_settings.json`):

```json
{
  "mcpServers": {
    "sophia-memory": {
      "type": "http",
      "url": "http://localhost:8081",
      "headers": {
        "Authorization": "Bearer dev-token"
      },
      "description": "Session memory and context management"
    },
    "sophia-filesystem": {
      "type": "http", 
      "url": "http://localhost:8082",
      "headers": {
        "Authorization": "Bearer dev-token"
      },
      "description": "File operations and code intelligence"
    },
    "sophia-git": {
      "type": "http",
      "url": "http://localhost:8084",
      "headers": {
        "Authorization": "Bearer dev-token"
      },
      "description": "Git operations and version control"
    }
  }
}
```

### For Claude Desktop

Update your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

### For Cursor

Update your Cursor MCP config (`.cursor/mcp.json`):

```json
{
  "servers": {
    "sophia-memory": {
      "endpoint": "http://localhost:8081",
      "auth": {
        "type": "bearer",
        "token": "dev-token"
      }
    },
    "sophia-filesystem": {
      "endpoint": "http://localhost:8082",
      "auth": {
        "type": "bearer",
        "token": "dev-token"
      }
    },
    "sophia-git": {
      "endpoint": "http://localhost:8084",
      "auth": {
        "type": "bearer",
        "token": "dev-token"
      }
    }
  }
}
```

---

## 🔧 API Endpoints Reference

### Memory Server (Port 8081)

#### Core Operations
```bash
# Store memory in session
POST http://localhost:8081/sessions/{session_id}/memory
Content-Type: application/json
Authorization: Bearer dev-token

{
  "content": "Your memory content",
  "role": "user",
  "metadata": {}
}

# Retrieve session memory
GET http://localhost:8081/sessions/{session_id}/memory
Authorization: Bearer dev-token

# Search memories
POST http://localhost:8081/search
Content-Type: application/json
Authorization: Bearer dev-token

{
  "query": "search term",
  "session_id": "optional_session_id",
  "limit": 20
}

# List all sessions
GET http://localhost:8081/sessions
Authorization: Bearer dev-token

# Clear session
DELETE http://localhost:8081/sessions/{session_id}/memory
Authorization: Bearer dev-token
```

### Filesystem Server (Port 8082)

#### File Operations
```bash
# List files
POST http://localhost:8082/fs/list
Content-Type: application/json
Authorization: Bearer dev-token

{
  "path": "."
}

# Read file
POST http://localhost:8082/fs/read
Content-Type: application/json
Authorization: Bearer dev-token

{
  "path": "path/to/file.ext"
}

# Write file
POST http://localhost:8082/fs/write
Content-Type: application/json
Authorization: Bearer dev-token

{
  "path": "path/to/file.ext",
  "content": "file content",
  "create_dirs": true
}

# Delete file
POST http://localhost:8082/fs/delete
Content-Type: application/json
Authorization: Bearer dev-token

{
  "path": "path/to/file.ext",
  "recursive": false
}
```

#### Code Intelligence
```bash
# Search in repository
POST http://localhost:8082/repo/search
Content-Type: application/json
Authorization: Bearer dev-token

{
  "query": "search pattern",
  "regex": false,
  "case_sensitive": false,
  "limit": 200
}

# Index symbols
POST http://localhost:8082/symbols/index
Content-Type: application/json
Authorization: Bearer dev-token

{
  "paths": ["src/"],
  "languages": ["python", "typescript"]
}

# Search symbols
POST http://localhost:8082/symbols/search
Content-Type: application/json
Authorization: Bearer dev-token

{
  "name": "function_name",
  "kind": "function",
  "lang": "python"
}
```

### Git Server (Port 8084)

#### Git Operations
```bash
# Get repository status
GET http://localhost:8084/status
Authorization: Bearer dev-token

# Get commit history
GET http://localhost:8084/log?limit=10
Authorization: Bearer dev-token

# List branches
GET http://localhost:8084/branches
Authorization: Bearer dev-token

# Get file diff
GET http://localhost:8084/diff?file=path/to/file.ext
Authorization: Bearer dev-token
```

---

## 🧪 Testing MCP Connections

### Quick Health Check
```bash
# Run the validation script
python3 scripts/validate_mcp_servers.py --quick

# Full validation with all endpoints
python3 scripts/validate_mcp_servers.py --verbose
```

### Manual Testing
```bash
# Test Memory Server
curl -X GET http://localhost:8081/health \
  -H "Authorization: Bearer dev-token"

# Test Filesystem Server
curl -X GET http://localhost:8082/health \
  -H "Authorization: Bearer dev-token"

# Test Git Server
curl -X GET http://localhost:8084/health \
  -H "Authorization: Bearer dev-token"
```

---

## 🔄 Starting MCP Servers

If servers are not running:

```bash
# Start all servers at once
./startup.sh

# Or start individually
python3 mcp/memory_server.py &
python3 mcp/filesystem/server.py &
python3 mcp/git/server.py &
```

---

## 🎯 Usage Examples for AI Agents

### Example 1: Storing Context
```python
# Store planning context
POST http://localhost:8081/sessions/planning-session/memory
{
  "content": "User wants to implement a new authentication system",
  "role": "assistant",
  "metadata": {
    "task": "auth-implementation",
    "priority": "high"
  }
}
```

### Example 2: Code Search
```python
# Find all authentication functions
POST http://localhost:8082/repo/search
{
  "query": "def.*auth|function.*auth",
  "regex": true,
  "limit": 50
}
```

### Example 3: Symbol Navigation
```python
# Index project symbols
POST http://localhost:8082/symbols/index
{
  "paths": ["src/", "lib/"],
  "languages": ["python", "typescript", "javascript"]
}

# Find specific class
POST http://localhost:8082/symbols/search
{
  "name": "AuthManager",
  "kind": "class"
}
```

### Example 4: Git History
```python
# Check recent changes
GET http://localhost:8084/log?limit=20

# Get current branch status
GET http://localhost:8084/status
```

---

## 🚨 Troubleshooting

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Connection refused | Run `./startup.sh` to start servers |
| 401 Unauthorized | Add `Authorization: Bearer dev-token` header |
| 404 Not Found | Check endpoint path is correct |
| Empty responses | Verify workspace path configuration |
| Redis connection error | Start Redis: `redis-server` |

### Debug Commands
```bash
# Check if servers are running
ps aux | grep -E "memory_server|filesystem|git/server"

# Check port availability
lsof -i :8081,8082,8084

# View server logs
tail -f logs/mcp_*.log

# Test Redis connection
redis-cli ping
```

---

## 📊 Monitoring

### Server Status Dashboard
```bash
# Run monitoring script
python3 scripts/monitor_mcp.py

# Or use the validation script
python3 scripts/validate_mcp_servers.py --verbose
```

### Health Check Endpoints
- Memory: `http://localhost:8081/health`
- Filesystem: `http://localhost:8082/health`
- Git: `http://localhost:8084/health`
- Metrics: `http://localhost:{port}/metrics` (Prometheus format)

---

## 🔐 Security Notes

### Development Environment
- Currently using `dev-token` for authentication
- MCP_DEV_BYPASS=1 allows development without strict auth
- Rate limiting: 100 requests per minute per IP

### Production Environment
- Set `MCP_TOKEN` environment variable
- Disable `MCP_DEV_BYPASS`
- Configure proper authentication tokens
- Use HTTPS in production

---

## 📚 Additional Resources

- [MCP Server Source Code](../mcp/)
- [Validation Script](../scripts/validate_mcp_servers.py)
- [Startup Script](../startup.sh)
- [Environment Configuration](../ENVIRONMENT.md)
- [API Documentation](./MCP_API_REFERENCE.md)

---

## ✅ Verification Checklist

Before using MCP servers, verify:

- [ ] All servers show "healthy" status
- [ ] Redis is running (`redis-cli ping`)
- [ ] Correct ports are available (8081, 8082, 8084)
- [ ] Authorization headers are configured
- [ ] Workspace path is set correctly
- [ ] AI extension configs are updated

---

## 🎉 Success Indicators

You know MCP integration is working when:

1. **Health checks pass**: All servers return healthy status
2. **Memory persists**: Sessions maintain context across interactions
3. **File operations work**: Can read/write files through MCP
4. **Code intelligence functions**: Symbol search and indexing work
5. **Git operations succeed**: Can query repository status and history

---

*Last Updated: {{ current_timestamp }}*
*Version: 1.0*