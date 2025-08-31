# API Reference

## Overview

The Sophia Intel AI API provides comprehensive endpoints for agent orchestration, memory management, and search operations.

## Base URLs

- **Unified API**: `http://localhost:8000`
- **Agno Bridge**: `http://localhost:7777`
- **Health Check**: `http://localhost:8000/healthz`

## Authentication

All API requests require authentication via API key:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/teams
```

## Core Endpoints

### Team Execution

#### Execute Team Task
```http
POST /run/team
```

Execute a task with an agent team.

**Request Body:**
```json
{
  "request": "Analyze the security vulnerabilities in this codebase",
  "team_id": "security_team",
  "stream": true,
  "context": {
    "repository": "https://github.com/user/repo",
    "branch": "main"
  }
}
```

**Response (Streaming):**
```json
{"type": "start", "team": "security_team", "agents": 6}
{"type": "agent", "name": "SecurityAnalyst", "content": "Scanning for vulnerabilities..."}
{"type": "complete", "summary": "Found 3 critical issues"}
```

### Memory Operations

#### Add Memory
```http
POST /memory/add
```

Store information in the memory system.

**Request Body:**
```json
{
  "topic": "Project Architecture",
  "content": "The system uses a microservices architecture...",
  "tags": ["architecture", "design"],
  "memory_type": "procedural",
  "metadata": {
    "source": "design_doc.md",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### Search Memory
```http
POST /memory/search
```

Search for memories using hybrid search.

**Request Body:**
```json
{
  "query": "authentication implementation",
  "limit": 10,
  "memory_types": ["procedural", "semantic"],
  "tags": ["security"],
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  }
}
```

### Search Operations

#### Hybrid Search
```http
POST /search/hybrid
```

Perform hybrid BM25 + vector search.

**Request Body:**
```json
{
  "query": "implement oauth authentication",
  "limit": 20,
  "alpha": 0.5,
  "rerank": true,
  "filters": {
    "file_type": [".py", ".js"],
    "modified_after": "2024-01-01"
  }
}
```

### Agent Information

#### List Teams
```http
GET /api/teams
```

Get available agent teams.

**Response:**
```json
[
  {
    "team_id": "strategic_team",
    "name": "Strategic Planning Team",
    "description": "High-level analysis and planning",
    "agents": [
      {
        "agent_id": "strategist_001",
        "name": "Strategic Analyst",
        "role": "planning",
        "capabilities": ["analysis", "forecasting"]
      }
    ]
  }
]
```

## Agno Compatibility Endpoints

For Agno UI compatibility:

### Get Agents
```http
GET /agents
```

### Agent Activity
```http
GET /agents?action=activity
```

### Execute Playground
```http
POST /v1/playground/run
```

## WebSocket Endpoints

### Real-time Streaming
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/team');

ws.send(JSON.stringify({
  request: 'Analyze this code',
  team_id: 'development_team'
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data.content);
};
```

## Rate Limiting

- **Default**: 100 requests/minute
- **Team Execution**: 10 requests/minute
- **Memory Write**: 50 requests/minute
- **Search**: 200 requests/minute

## Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {
      "limit": 100,
      "reset_at": "2024-01-15T10:35:00Z"
    }
  }
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_REQUEST` | Malformed request | 400 |
| `UNAUTHORIZED` | Missing/invalid API key | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |
| `INTERNAL_ERROR` | Server error | 500 |
| `SERVICE_UNAVAILABLE` | Temporary outage | 503 |

## Pagination

List endpoints support pagination:

```http
GET /api/memories?page=2&limit=50
```

**Response Headers:**
```
X-Total-Count: 245
X-Page: 2
X-Limit: 50
Link: <http://localhost:8000/api/memories?page=3&limit=50>; rel="next"
```

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:
- JSON: `http://localhost:8000/openapi.json`
- Interactive docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## SDK Examples

### Python
```python
from sophia_intel import Client

client = Client(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

response = client.teams.execute(
    request="Analyze this code",
    team_id="development_team",
    stream=True
)

for chunk in response:
    print(chunk.content)
```

### JavaScript/TypeScript
```typescript
import { SophiaClient } from '@sophia-intel/sdk';

const client = new SophiaClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key'
});

const response = await client.teams.execute({
  request: 'Analyze this code',
  teamId: 'development_team',
  stream: true
});

for await (const chunk of response) {
  console.log(chunk.content);
}
```

## Performance Tips

1. **Use streaming** for long-running operations
2. **Batch requests** when possible
3. **Cache responses** for repeated queries
4. **Use pagination** for large result sets
5. **Implement exponential backoff** for retries

## Versioning

API version is included in the response headers:
```
X-API-Version: 2.0.0
```

For version-specific endpoints:
```http
GET /v2/api/teams
```