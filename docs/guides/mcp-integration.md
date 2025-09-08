# MCP Integration Guide

Overview
- MCP (Model Context Protocol) bridges IDEs/agents to Sophia’s filesystem, git, and memory operations during development.
- Local endpoints (default):
  - Memory:     http://localhost:8081
  - Filesystem: http://localhost:8082
  - Git:        http://localhost:8084

What each server does
- Memory MCP: Provides semantic memory operations (via Weaviate). Health endpoint ensures readiness of the bridge.
- Filesystem MCP: Exposes safe filesystem interactions in the container workspace.
- Git MCP: Exposes repository status/commit/diff operations using your SSH agent.

How Cursor/Claude connect
- VS Code settings are provided in `.vscode/settings.json`. Reload window to apply.
- Claude Desktop needs to be restarted after configuration updates.

Verification
1) Health checks
```
curl -sf http://localhost:8081/health  # Memory
curl -sf http://localhost:8082/health  # Filesystem
curl -sf http://localhost:8084/health  # Git
```

2) Typical issues
- Memory MCP unhealthy: ensure Weaviate is up (`curl -sf http://localhost:8080/v1/.well-known/ready`).
- Git MCP unhealthy: ensure SSH agent is running (`ssh-add -l`) and `SSH_AUTH_SOCK` is set in the compose env.
- Filesystem MCP unhealthy: ensure container is running and port 8082 is free.

Notes
- In dev, use `make full-start` to bring services up in the right order.
- Ensure `.env` and `.env.local` are present and direnv or `source scripts/env.sh` is used for consistent env.

