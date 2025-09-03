# SuperOrchestrator API Documentation

## Endpoints

### Process Request
**POST** `/orchestrator/process`

Process any type of orchestration request.

**Request Body:**
```json
{
  "type": "chat|command|query|agent",
  "message": "string (for chat)",
  "command": "string (for command)",
  "params": {}
}
```

**Response:**
```json
{
  "type": "response_type",
  "result": {},
  "timestamp": "ISO 8601"
}
```

### WebSocket Connection
**WS** `/orchestrator/ws`

Real-time connection for monitoring and updates.

## Request Types

### Chat
```json
{
  "type": "chat",
  "message": "Your message here"
}
```

### Command
```json
{
  "type": "command",
  "command": "deploy|scale|optimize|analyze|heal",
  "params": {}
}
```

### Query
```json
{
  "type": "query",
  "query_type": "metrics|state|tasks|insights"
}
```

### Agent
```json
{
  "type": "agent",
  "action": "create|destroy|status",
  "config": {}
}
```
