> Deprecated: Start guide moved. Use START_HERE.md at repo root. For all-in-one local bringup and env validation, use `scripts/start_all_and_validate.sh`.

## Goal
Fastest path to a productive, contextual AI coding + BI environment

Environment policy (enforced): `.env.master` only; manage with `./bin/keys edit`; start with `./sophia start`.

## 2. Service Management

### Master Control Script (Recommended)
```bash
# Primary management tool
./sophia start    # Start all services (MCP servers; Portkey gateway via env)
./sophia status   # Check system status
./sophia test     # Run comprehensive tests
./sophia stop     # Stop all services
./sophia logs     # Tail all logs
```

### Alternative: Dev CLI Wrapper
```bash
# Unified wrapper for tools + services
./dev start       # Start all services
./dev status      # Show health + process details
./dev check       # Preflight check with API tests
./dev stop        # Stop services
```

## 3. Service Endpoints

| Service | Port | URL | Auth |
|---------|------|-----|------|
| Portkey | n/a  | https://api.portkey.ai/v1/health | x-portkey-api-key: $PORTKEY_API_KEY |
| MCP Memory | 8081 | http://localhost:8081 | None (dev bypass) |
| MCP Filesystem | 8082 | http://localhost:8082 | None (dev bypass) |
| MCP Git | 8084 | http://localhost:8084 | None (dev bypass) |
| Redis | 6379 | redis://localhost:6379 | None |

## 4. Terminal AI Agents

### Unified AI Router
```bash
# Quick AI tasks via terminal
./dev ai claude -p "Summarize pipeline trends"
./dev ai codex "Write SQL to aggregate MRR by month"
./dev ai lite --usecase analysis.large_context -p "Analyze anomalies in bookings"
./dev ai lite --model analytical -p "Explain trend drivers"
```

### OpenCode Integration
```bash
# Works even if PATH is broken
./dev opencode --version
./bin/opencode  # Direct binary wrapper
```

## 5. Cursor IDE MCP Integration

### Configuration
* **Config file**: `.cursor/mcp.json` (ready to use)
* **Prerequisites**: Start services first (`./sophia start`)
* **Features**: Memory persistence, filesystem access, git operations

### MCP Server URLs in Cursor
```json
{
  "servers": [
    { "name": "memory", "url": "http://127.0.0.1:8081" },
    { "name": "filesystem", "url": "http://127.0.0.1:8082" },
    { "name": "git", "url": "http://127.0.0.1:8084" }
  ]
}
```

## 6. Security Configuration

### Development Mode (Current)
* `MCP_DEV_BYPASS=true` - No authentication required
* Suitable for local development only

### Production Mode
```bash
# In .env.master:
# MCP_DEV_BYPASS=false
MCP_TOKEN=your-secure-token-here

# Then use in requests:
curl -H "Authorization: Bearer your-secure-token-here" http://localhost:8081/sessions
```

## 7. Quick Start Workflow

```bash
# 1. Initial setup (one time)
cd ~/sophia-intel-ai
cp .env.template .env.master  # If missing
nano .env.master              # Add your API keys
chmod 600 .env.master         # Secure permissions

# 2. Start services
./sophia start                # Or: ./dev start

# 3. Verify everything works
./sophia test                 # All 5 tests should pass
./dev check                   # Detailed preflight check

# 4. Use the system
./dev ai claude -p "Help me build a REST API"
./dev opencode                # Launch OpenCode
cursor .                      # Open in Cursor with MCP
```

## 8. Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Port already in use" | `./sophia clean` then `./sophia start` |
| "API key not found" | Check `.env.master` has the key |
| "Permission denied" | Run `chmod 600 .env.master` |
| "Service won't start" | Check logs: `./sophia logs <service>` |
| "Auth error on MCP" | Ensure `MCP_DEV_BYPASS=true` and no `MCP_TOKEN` |

### Health Check Commands
```bash
./sophia status               # Quick status
./dev status                  # Detailed with processes
./dev check                   # Full preflight test
./sophia test                 # Run test suite
```

## 9. Advanced Features

### BI Pipeline
```bash
./dev bi --query "Show MRR trends" --run
```

### Model Management
```bash
./dev models show             # Show model configuration
./dev models set alias fast gpt-4o-mini
./dev models set usecase coding fast
```

### System Diagnostics
```bash
./dev doctor                  # Deep environment diagnostics
./dev info                    # Configuration summary
```

## 10. Available LLM Models (25 configured)

**Claude**: claude-3-5-haiku, claude-3-5-sonnet, claude-3-opus
**GPT**: gpt-4o, gpt-4o-mini, gpt-o1-preview, gpt-o1-mini
**Gemini**: gemini-2.0-flash, gemini-1.5-pro
**Grok**: grok-2-latest, grok-2-vision
**DeepSeek**: deepseek-chat, deepseek-coder
**Together**: mixtral-8x22b, qwen-72b
**And more...**

## Next Steps

1. **Explore agents**: See `docs/AGENTS.md` for AI agent capabilities
2. **BI workflows**: Check `docs/BI_WORKFLOWS.md` 
3. **API integration**: Review `docs/API_REFERENCE.md`
4. **Operations**: See `OPERATIONS_RUNBOOK.md` for production setup

## Support

* **Logs**: `logs/` directory
* **Config**: `.env.master` (environment). Portkey Gateway + VKs only.
* **Scripts**: `sophia` (master control), `dev` (unified wrapper)

---

**System Status**: ✅ All services operational
**Last tested**: 2025-09-13 04:15 AM
