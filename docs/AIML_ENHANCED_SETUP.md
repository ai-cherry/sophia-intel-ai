# AIML Enhanced API Setup Guide

## Overview

The AIML Enhanced API provides repository-aware chat completions by integrating AIMLAPI with MCP (Model Context Protocol) servers. This enables AI models to have full context of your codebase when generating responses.

## Architecture

```
┌─────────────────────────────────────────┐
│           Client Application            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      AIML Enhanced Router (8003)        │
│  - Chat completions with context        │
│  - Model profiles & streaming           │
└────────┬───────────────┬────────────────┘
         │               │
         ▼               ▼
┌──────────────┐  ┌──────────────────────┐
│   AIMLAPI    │  │    MCP Servers       │
│   Service    │  ├──────────────────────┤
└──────────────┘  │ Memory (8081)        │
                  │ Filesystem (8082)     │
                  │ Git (8084)            │
                  └──────────────────────┘
```

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.template .env.master && chmod 600 .env.master

# Edit with your API key
nano .env.master

# Set required variables:
# AIMLAPI_API_KEY=your-actual-key-here
# AIMLAPI_BASE=https://api.aimlapi.com/v1
# AIML_ENHANCED_ENABLED=true
# WORKSPACE_PATH=/path/to/sophia-intel-ai

# Secure the file
# already set above
```

### 2. Start MCP Servers

```bash
# Using the orchestrator script
./scripts/dev/squad.sh start

# Or manually:
cd ~/sophia-intel-ai

# Memory server
python3 -m uvicorn mcp.memory.server:app --port 8081 &

# Filesystem server (requires WORKSPACE_PATH)
WORKSPACE_PATH=$(pwd) python3 -m uvicorn mcp.filesystem.server:app --port 8082 &

# Git server
python3 -m uvicorn mcp.git.server:app --port 8084 &
```

### 3. Start Unified API

```bash
# Start the unified server with AIML router
python3 sophia_unified_server.py

# Or use the start script
make dev-docker
```

### 4. Verify Setup

```bash
# Check health
curl http://localhost:8003/api/aiml/health

# List available models
curl http://localhost:8003/api/aiml/models

# Test MCP endpoints
./scripts/dev/squad.sh test
```

## API Endpoints

### Chat Completion

**POST** `/api/aiml/chat`

Send chat messages with optional repository context injection.

```json
{
    "messages": [
        {"role": "user", "content": "Analyze the MCP architecture"}
    ],
    "model": "sophia-architect",
    "temperature": 0.7,
    "max_tokens": 8000,
    "stream": false,
    "include_context": true,
    "context_options": {
        "structure": true,
        "git": true,
        "memory": false
    }
}
```

**Response:**
```json
{
    "id": "chat-123",
    "object": "chat.completion",
    "model": "sophia-architect",
    "choices": [{
        "message": {"content": "Based on the repository structure..."},
        "finish_reason": "stop"
    }],
    "usage": {"total_tokens": 500}
}
```

### Streaming Chat

Enable streaming by setting `stream: true`:

```bash
curl -X POST http://localhost:8003/api/aiml/chat \
    -H "Content-Type: application/json" \
    -d '{
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "sophia-general",
        "stream": true
    }'
```

Returns Server-Sent Events (SSE) stream.

### List Models

**GET** `/api/aiml/models`

```bash
curl http://localhost:8003/api/aiml/models
```

Returns available model profiles with their capabilities.

### Repository Analysis

**POST** `/api/aiml/repository/analyze`

Analyze repository structure without LLM calls:

```bash
curl -X POST http://localhost:8003/api/aiml/repository/analyze \
    -H "Content-Type: application/json"
```

## Model Profiles

| Profile ID | Model | Use Case |
|------------|-------|----------|
| `sophia-general` | gpt-4o | General assistance |
| `sophia-architect` | grok-4 | System design |
| `sophia-coder` | codestral-2501 | Implementation |
| `sophia-reasoner` | deepseek-v3.1 | Complex analysis |
| `sophia-reviewer` | qwen-3-235b | Code review |
| `sophia-prover` | deepseek-prover-v2 | Verification |
| `sophia-creative` | llama-3.3-70b | Creative solutions |
| `sophia-analyst` | gpt-4-turbo | Data analysis |

## Security

### Optional Authentication

Set `AIML_ROUTER_TOKEN` in environment to require bearer token:

```bash
# In <repo>/.env.master
AIML_ROUTER_TOKEN=your-secret-token
```

Then include in requests:

```bash
curl -H "Authorization: Bearer your-secret-token" \
    http://localhost:8003/api/aiml/chat
```

### CORS Configuration

Default CORS allows:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

Modify in unified server configuration as needed.

## Development Scripts

### Squad Orchestrator

The `scripts/dev/squad.sh` script provides convenient commands:

```bash
# Start all MCP servers
./scripts/dev/squad.sh start

# Stop all servers
./scripts/dev/squad.sh stop

# Monitor logs
./scripts/dev/squad.sh monitor

# Test endpoints
./scripts/dev/squad.sh test

# Analyze and improve a file
./scripts/dev/squad.sh improve app/main.py
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/test_aiml_*.py -v

# Run specific test
pytest tests/test_aiml_client.py -v

# Run with coverage
pytest tests/test_aiml_*.py --cov=app.services --cov=app.routers
```

## Troubleshooting

### AIMLAPI not configured

**Error:** "AIMLAPI not configured"

**Solution:** Ensure `AIMLAPI_API_KEY` is set in environment:
```bash
echo $AIMLAPI_API_KEY  # Should show your key (not CHANGEME)
```

### MCP servers not responding

**Error:** "MCP request failed"

**Solution:** Check MCP servers are running:
```bash
curl http://localhost:8081/health  # Memory
curl http://localhost:8082/health  # Filesystem
curl http://localhost:8084/health  # Git
```

### Port conflicts

**Error:** "Address already in use"

**Solution:** Stop conflicting services:
```bash
./scripts/dev/squad.sh stop
lsof -ti:8003 | xargs kill -9  # Force stop on port
```

### Context too large

**Error:** Context exceeds size limit

**Solution:** Reduce context options:
```json
{
    "include_context": true,
    "context_options": {
        "structure": true,
        "git": false,
        "memory": false
    }
}
```

## Advanced Configuration

### Custom Model Profiles

Add profiles in `app/config/models.py`:

```python
MODEL_PROFILES["my-profile"] = ModelProfile(
    id="my-profile",
    name="Custom Model",
    model="model-id",
    temperature=0.5,
    max_tokens=4000,
    context_type="custom",
    mcp_tools=["filesystem"],
    system_prompt="Custom instructions..."
)
```

### MCP Endpoint Customization

Modify endpoints in `app/services/mcp_context.py`:

```python
MCP_SERVERS = {
    "custom": {
        "base_url": "http://localhost:9000",
        "endpoints": {
            "action": "/custom/action"
        }
    }
}
```

## Performance Optimization

1. **Context Caching**: Repository structure is cached for 5 minutes
2. **Connection Pooling**: HTTP clients reuse connections
3. **Streaming**: Use `stream: true` for real-time responses
4. **Selective Context**: Only include needed context components

## Integration Examples

### Python Client

```python
import httpx
import json

async def chat_with_context(message: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8003/api/aiml/chat",
            json={
                "messages": [{"role": "user", "content": message}],
                "model": "sophia-architect",
                "include_context": True
            }
        )
        return response.json()

# Usage
result = await chat_with_context("Explain the MCP architecture")
print(result["choices"][0]["message"]["content"])
```

### JavaScript/TypeScript

```typescript
async function chatWithContext(message: string) {
    const response = await fetch('http://localhost:8003/api/aiml/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            messages: [{role: 'user', content: message}],
            model: 'sophia-architect',
            include_context: true
        })
    });
    return response.json();
}
```

## Monitoring

### Health Checks

```bash
# Check all services
curl http://localhost:8003/api/aiml/health
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:8084/health
```

### Logs

```bash
# View MCP logs
tail -f logs/squad/*.log

# View unified server logs
tail -f logs/unified_server.log
```

### Metrics

Track in application:
- Response times
- Token usage
- Context size
- Error rates

## Contributing

1. Follow existing patterns in codebase
2. Add tests for new features
3. Update documentation
4. Run linters and type checks

## Support

For issues or questions:
- Check logs in `logs/squad/`
- Review this documentation
- Check environment variables
- Verify MCP server status

## License

Part of Sophia Intel AI project.
