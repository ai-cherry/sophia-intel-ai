# 🚀 Sophia Intel AI - Quick Start Guide

## System Overview
A unified multi-model AI orchestration system that intelligently routes requests to the most cost-effective model while maintaining high quality.

## ✅ Current Status
- ✅ Redis Cache: Running (port 6379)
- ✅ MCP Memory Server: Running (port 8081)
- ✅ MCP Filesystem Server: Running (port 8082)
- ✅ MCP Git Server: Running (port 8084)
- ✅ Unified API: Running (port 8000)
- 🔧 LiteLLM Router: Ready to start (port 8090)

## 🎯 Quick Start Commands

### 1. Start Everything (Recommended)
```bash
# Using Docker Compose (recommended for dev)
docker compose -f infra/docker-compose.yml up -d unified-api sophia-intel-app mcp-filesystem mcp-git mcp-memory valkey

# Or native start
./start_sophia_unified.sh
```

### 2. Manual Service Start
```bash
# Already running:
# - Redis (6379)
# - MCP servers (8081, 8082, 8084)

# Start Unified API (if needed)
python3 sophia_unified_server.py
```

## 📋 Basic Usage Examples

### 1. Simple Query (Auto-routes to cheapest model)
```bash
# Uses Gemini Flash ($0.0001/1k tokens)
curl -X POST http://localhost:8081/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "test",
    "content": "Hello World",
    "metadata": {"type": "greeting"}
  }'
```

### 2. Repository Context Query
```bash
# List Python files in project
curl -X POST http://localhost:8082/repo/list \
  -H "Content-Type: application/json" \
  -d '{
    "root": ".",
    "globs": ["*.py"],
    "limit": 10
  }'
```

### 3. Git Status Check
```bash
# Get current git status
curl -X POST http://localhost:8084/git/status \
  -H "Content-Type: application/json" \
  -d '{"repo": "sophia"}'
```

### 4. Store and Search Memory
```bash
# Store information
curl -X POST http://localhost:8081/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "project",
    "content": "The authentication system uses JWT tokens with refresh capability",
    "metadata": {"category": "architecture", "importance": "high"}
  }'

# Search memory
curl -X POST http://localhost:8081/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "project",
    "query": "authentication",
    "limit": 5
  }'
```

### 5. Read Project Files
```bash
# Read a specific file
curl -X POST http://localhost:8082/repo/read \
  -H "Content-Type: application/json" \
  -d '{
    "path": "README.md",
    "start_line": 1,
    "end_line": 50
  }'
```

## 🎨 Advanced Features

### Multi-Model Routing (When LiteLLM is running)
```python
# The system automatically selects the best model:
# - Simple task → Gemini Flash ($0.0001/1k)
# - Code generation → DeepSeek Coder ($2/1k)
# - Architecture → Claude Opus ($15/1k)
# - Review → Claude Sonnet ($3/1k)
```

### Cost Tracking
```bash
# Check daily costs (requires LiteLLM router)
curl http://localhost:8090/v1/costs
```

### Squad Orchestration
```bash
# Complex multi-agent task (requires full system)
curl -X POST http://localhost:8095/process \
  -d '{"request": "Build user authentication system"}'
```

## 💡 Common Use Cases

### 1. Code Analysis
```bash
# Analyze repository structure
curl -X POST http://localhost:8082/repo/list \
  -d '{"root": "app", "globs": ["**/*.py"], "limit": 100}'
```

### 2. Project Memory
```bash
# Store architectural decisions
curl -X POST http://localhost:8081/memory/store \
  -d '{
    "namespace": "decisions",
    "content": "Using FastAPI for REST API due to async support",
    "metadata": {"date": "2024-01-10", "type": "architecture"}
  }'
```

### 3. Git Operations
```bash
# Check modified files
curl -X POST http://localhost:8084/git/status \
  -d '{"repo": "sophia"}' | jq '.modified'
```

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Kill process on port (macOS)
kill -9 $(lsof -ti:8000)  # Replace 8000 with your port
```

### Redis Not Running
```bash
redis-server --daemonize yes
```

### MCP Server Failed
```bash
# Check logs
tail -f logs/mcp-*.log
```

### Memory Issues
```bash
# Clear Redis cache
redis-cli FLUSHALL
```

## 📊 Service Status Check
```bash
# Quick health check for all services
for port in 6379 8081 8082 8084; do
  echo -n "Port $port: "
  curl -sf http://localhost:$port/health > /dev/null 2>&1 && echo "✓" || echo "✗"
done
```

## 🔍 Monitoring

### View Logs
```bash
# All logs
tail -f logs/*.log

# Specific service
tail -f logs/mcp-memory.log
```

### Redis Monitor
```bash
redis-cli MONITOR
```

## 🎯 Next Steps

1. **Test MCP Integration**: The MCP servers are running and ready for repository-aware operations
2. **Configure LiteLLM**: Add your API keys for multi-model support
3. **Try Squad Orchestration**: Use multiple agents for complex tasks
4. **Monitor Costs**: Track API usage and optimize model selection

## 📚 Key Endpoints

| Service | Port | Purpose |
|---------|------|---------|
| Redis | 6379 | Caching & state |
| MCP Memory | 8081 | Knowledge storage |
| MCP Filesystem | 8082 | Code access |
| MCP Git | 8084 | Version control |
| Unified API | 8003 | Main API |
| LiteLLM | 8090 | Model routing |
| Squad | 8095 | Multi-agent |

## 🚦 System Architecture
```
User Request
    ↓
Squad Orchestrator (determines task complexity)
    ↓
LiteLLM Router (selects optimal model)
    ↓
MCP Servers (provide context)
    ↓
AI Model (generates response)
    ↓
Redis Cache (stores result)
```

## ⚡ Performance Tips

1. **Use Memory Caching**: Store frequently accessed data in MCP Memory
2. **Batch Operations**: Group related queries together
3. **Context Limiting**: Only include necessary MCP servers for each task
4. **Model Selection**: Let the router choose models automatically

## 🔐 Security Notes

- API keys are in `<repo>/.env.master`
- Never commit real keys to git
- Use environment variables for production
- Enable auth tokens for public deployment

---

**Ready to build something amazing? The system is running and waiting for your commands!** 🚀
