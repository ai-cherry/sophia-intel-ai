# Sophia MCP Bridge

Multi-assistant coordination bridge for Sophia Intel AI, enabling seamless integration between Claude Desktop, Roo/Cursor, and Cline through the Model Context Protocol (MCP).

## Features

- **Unified Memory System**: Shared knowledge base across all assistants
- **Real-time Synchronization**: Redis pub/sub for instant updates
- **Intelligent Caching**: Multi-tier cache for optimal performance
- **Enterprise Security**: JWT authentication, encryption, rate limiting
- **Task Orchestration**: Coordinate complex multi-assistant workflows
- **Code Intelligence**: Share code patterns and insights

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Claude Desktop  │     │   Roo/Cursor    │     │      Cline      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │      stdio            │      stdio            │      stdio
         │                       │                       │
    ┌────▼────────┐         ┌────▼────────┐         ┌────▼────────┐
    │Claude Adapter│         │ Roo Adapter  │         │Cline Adapter│
    └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
             │                       │                       │
             └───────────┬───────────┴───────────┬───────────┘
                         │                       │
                    ┌────▼────────────────────────▼────┐
                    │      MCP Server v2               │
                    │   (FastAPI + Security)           │
                    └────────────┬─────────────────────┘
                                 │
                    ┌────────────┼─────────────┐
                    │            │             │
               ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
               │  Redis  │  │Weaviate │  │Postgres │
               └─────────┘  └─────────┘  └─────────┘
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Redis
- Weaviate
- Docker (for monitoring stack)

### Installation

1. Install dependencies:
```bash
cd mcp-bridge
npm install
```

2. Copy environment configuration:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Build TypeScript:
```bash
npm run build
```

### Starting the Bridge

#### Option 1: Start all adapters
```bash
npm run dev
```

#### Option 2: Start individual adapters
```bash
# Claude Desktop
npm run claude

# Roo/Cursor
npm run roo

# Cline
npm run cline
```

## Configuration

### Claude Desktop

Add to Claude Desktop settings:

```json
{
  "mcpServers": {
    "sophia-mcp": {
      "command": "node",
      "args": ["/path/to/sophia-intel-ai/mcp-bridge/dist/claude-adapter.js"],
      "env": {
        "MCP_SERVER_URL": "http://localhost:8004",
        "REDIS_URL": "redis://localhost:6379"
      }
    }
  }
}
```

### Roo/Cursor

Configure in `.cursor/mcp.json`:

```json
{
  "servers": {
    "sophia": {
      "command": "node",
      "args": ["/path/to/sophia-intel-ai/mcp-bridge/dist/roo-adapter.js"]
    }
  }
}
```

### Cline

Add to VS Code settings:

```json
{
  "cline.mcp.servers": {
    "sophia": {
      "command": "node",
      "args": ["/path/to/sophia-intel-ai/mcp-bridge/dist/cline-adapter.js"]
    }
  }
}
```

## Available Tools

### Claude Desktop Tools
- `store_memory`: Store information in knowledge base
- `search_memory`: Search for memories
- `update_memory`: Update existing memories
- `delete_memory`: Remove memories
- `get_context`: Get contextual information

### Roo/Cursor Tools
- `store_code_memory`: Store code patterns
- `search_code_patterns`: Find code patterns
- `analyze_codebase`: Analyze project structure
- `suggest_refactoring`: Get refactoring suggestions
- `generate_tests`: Generate test suggestions
- `share_insight`: Share coding insights
- `get_team_context`: Get team context

### Cline Tools
- `create_task`: Create development tasks
- `execute_task`: Execute tasks autonomously
- `analyze_project`: Analyze project health
- `plan_implementation`: Plan feature implementation
- `implement_feature`: Implement complete features
- `track_progress`: Track project progress
- `coordinate_with_team`: Coordinate with other assistants

## Monitoring

### Health Check
```bash
curl http://localhost:8004/health
```

### Metrics
```bash
curl http://localhost:8004/metrics
```

### Dashboards
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/sophia-monitor)
- Jaeger: http://localhost:16686

## Development

### Running Tests
```bash
npm test
```

### Building for Production
```bash
npm run build
```

### Debugging
Set `LOG_LEVEL=debug` in your `.env` file for verbose logging.

## Security

- JWT-based authentication with refresh tokens
- End-to-end encryption for sensitive data
- Rate limiting per assistant
- Comprehensive audit logging
- RBAC with granular permissions

## Troubleshooting

### Redis Connection Issues
```bash
# Check Redis is running
redis-cli ping

# Check Redis connectivity
redis-cli -h localhost -p 6379
```

### MCP Server Not Responding
```bash
# Check server status
curl http://localhost:8004/health

# Check logs
tail -f mcp-bridge.log
```

### Adapter Startup Issues
```bash
# Run adapter directly for debugging
tsx src/claude-adapter.ts
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## License

MIT