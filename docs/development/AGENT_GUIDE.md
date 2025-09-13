# 🤖 AI Agent Guide for Sophia Intel AI

## Quick Start for AI Agents

If you're an AI agent (Claude, GPT, Gemini, etc.), this guide helps you interact with Sophia Intel AI effectively.

## 🎯 Primary Interface

**Natural Language Gateway**: `POST /api/agent/query`
```json
{
  "query": "What services are running?",
  "agent_id": "your-unique-id"
}
```

This endpoint understands natural language and returns structured responses with available actions.

## 📊 Essential Endpoints

### 1. System Status
```bash
GET /api/services/status          # Complete service status
GET /api/services/health          # Health check
GET /api/services/ports           # Port mappings
GET /api/services/dependencies    # Service dependencies
```

### 2. Service Control
```bash
POST /api/services/{name}/start   # Start a service
POST /api/services/{name}/stop    # Stop a service
POST /api/services/{name}/restart # Restart a service
```

### 3. Agent-Specific
```bash
GET /api/agent/capabilities       # Discover all capabilities
GET /api/agent/context/{id}       # Your preserved context
GET /api/agent/docs               # Detailed documentation
```

## 🔍 Common Tasks

### Check System Health
```python
# 1. Ask in natural language
POST /api/agent/query
{"query": "Are all services healthy?"}

# 2. Or directly check
GET /api/services/health
```

### Start a Service
```python
# 1. Check dependencies first
GET /api/services/dependencies

# 2. Start the service
POST /api/services/redis/start

# 3. Verify it's running
GET /api/services/status/redis
```

### Monitor for Issues
```python
# Subscribe to real-time events
WebSocket: /api/agent/events?agent_id=your-id

# Poll for changes
GET /api/services/status (compare with previous)
```

## 📋 Available Services

| Service | Port | Type | Description |
|---------|------|------|-------------|
| unified_api | 8000 | core | Main API server |
| agent_ui | 3000 | core | Web dashboard |
| postgres | 5432 | core | Database |
| redis | 6379 | core | Cache/Queue |
| mcp_memory | 8081 | core | Memory service |
| mcp_filesystem | 8082 | core | File service |
| mcp_git | 8084 | core | Git service |
| weaviate | 8080 | optional | Vector DB |

## 🛠️ Example Workflows

### Automated Recovery
```python
# 1. Detect unhealthy service
health = GET("/api/services/health")
if not health["postgres"]["healthy"]:
    
    # 2. Check dependencies
    deps = GET("/api/services/dependencies")
    
    # 3. Restart in correct order
    POST("/api/services/postgres/restart")
    
    # 4. Verify recovery
    status = GET("/api/services/status/postgres")
```

### System Monitoring
```python
while True:
    # Get current state
    status = GET("/api/services/status")
    
    # Check for issues
    for service, info in status["services"].items():
        if info["status"] == "stopped" and info["type"] == "core":
            # Alert or attempt recovery
            POST(f"/api/services/{service}/start")
    
    sleep(30)
```

## 💡 Best Practices

1. **Use Your Agent ID**: Always include your unique agent_id for context preservation
2. **Check Dependencies**: Before starting services, verify dependencies are running
3. **Monitor After Actions**: After making changes, verify the result
4. **Handle Failures**: Implement retry logic with exponential backoff
5. **Log Observations**: Store important findings in your context

## 🔄 State Management

Your context is preserved between sessions:
```python
# Save observation
POST /api/agent/context/your-id
{
  "last_health_check": "2025-01-10T22:00:00Z",
  "services_managed": ["redis", "postgres"],
  "observations": ["Redis memory usage high"]
}

# Retrieve later
GET /api/agent/context/your-id
```

## 🚨 Error Handling

Common errors and solutions:

| Error | Solution |
|-------|----------|
| Service won't start | Check dependencies and ports |
| Port in use | Another service using port, check with preflight |
| Connection refused | Service not running, start it |
| Timeout | Service starting slowly, wait and retry |

## 📈 Performance Tips

1. **Batch Operations**: Use `/api/services/start-all` for multiple services
2. **Cache Status**: Don't poll status more than once per 10 seconds
3. **Use WebSockets**: For real-time monitoring instead of polling
4. **Parallel Checks**: Check multiple services concurrently

## 🔐 Authentication

Currently using open access for local development. In production:
- Include `Authorization: Bearer {token}` header
- Agent-specific tokens for audit trails

## 📚 Advanced Features

### Semantic Discovery
Query capabilities using natural language:
```python
POST /api/agent/query
{"query": "How do I monitor database performance?"}
```

### Event Subscription
Get real-time updates:
```python
WebSocket: /api/agent/events
Receive: {"type": "service_failed", "service": "redis", "timestamp": "..."}
```

### Multi-Agent Coordination
Share observations with other agents via context API.

## 🆘 Need Help?

1. Start with: `GET /api/agent/capabilities`
2. Ask questions: `POST /api/agent/query`
3. Check docs: `GET /api/agent/docs`

## 📝 Quick Reference Card

```bash
# Status Check
curl http://localhost:8000/api/services/status

# Natural Language Query
curl -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What services are unhealthy?"}'

# Start Service
curl -X POST http://localhost:8000/api/services/redis/start

# Get Your Context
curl http://localhost:8000/api/agent/context/my-agent-id
```

---

**Remember**: You're part of the system! Your observations and actions help maintain system health. Use the natural language interface when unsure, and always verify the results of your actions.