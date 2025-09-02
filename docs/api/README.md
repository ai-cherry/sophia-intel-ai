# AI Orchestra API Documentation

## Overview
The AI Orchestra provides a unified API for intelligent agent orchestration, supporting both REST and WebSocket protocols. The system features automatic version detection, backward compatibility, and comprehensive error handling.

## Base URL
```
Production: https://api.ai-orchestra.com
Staging: https://staging-api.ai-orchestra.com
Development: http://localhost:8000
```

## Authentication
All API requests require authentication using Bearer tokens:
```http
Authorization: Bearer <your-api-token>
```

## API Versions
- **v1**: Legacy API (deprecated, maintained for compatibility)
- **v2**: Current stable API with enhanced features

## Rate Limiting
- 1000 requests per minute per API key
- WebSocket: 100 messages per minute per connection
- Burst allowance: 50 requests

## Response Format
All responses follow a consistent format:
```json
{
  "success": true,
  "data": {},
  "metadata": {
    "request_id": "uuid",
    "timestamp": "ISO-8601",
    "version": "v2"
  },
  "error": null
}
```

## Error Handling
Errors use standard HTTP status codes with detailed messages:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "message",
      "reason": "Required field missing"
    }
  }
}
```

## Endpoints

### Chat API

#### POST /chat/v2/chat
Process a chat message through the AI Orchestra system.

**Request Body:**
```json
{
  "message": "string",
  "session_id": "string",
  "optimization_mode": "lite|balanced|quality",
  "swarm_type": "coding-team|research-team|creative-team|coding-debate",
  "use_memory": false,
  "user_context": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "response": "string",
    "session_id": "string",
    "execution_mode": "string",
    "quality_score": 0.85,
    "execution_time": 0.5,
    "metadata": {
      "tokens_used": 150,
      "model": "gpt-4",
      "processing_steps": []
    }
  }
}
```

**Example:**
```bash
curl -X POST https://api.ai-orchestra.com/chat/v2/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing",
    "session_id": "user-123-session-456",
    "optimization_mode": "balanced"
  }'
```

### WebSocket API

#### WS /chat/ws/{client_id}/{session_id}
Establish a WebSocket connection for real-time chat.

**Connection:**
```javascript
const ws = new WebSocket('wss://api.ai-orchestra.com/chat/ws/client-123/session-456');
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'chat',
    data: {
      message: 'Hello AI',
      context: {}
    }
  }));
};
```

**Message Types:**
- `chat`: Regular chat message
- `command`: System command
- `control`: Connection control (ping/pong/status)
- `stream`: Token streaming

**Message Format:**
```json
{
  "type": "chat|command|control|stream",
  "data": {},
  "timestamp": "ISO-8601"
}
```

### Health Check API

#### GET /health
Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600,
  "components": {
    "orchestra_manager": "healthy",
    "command_dispatcher": "healthy",
    "memory_system": "degraded",
    "swarm_intelligence": "healthy"
  }
}
```

#### GET /readiness
Check if system is ready to accept requests.

**Response:**
```json
{
  "ready": true,
  "checks": {
    "database": true,
    "cache": true,
    "external_services": true
  }
}
```

#### GET /metrics
Get system metrics in Prometheus format.

**Response:**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/chat/v2/chat"} 1234

# HELP websocket_connections Active WebSocket connections
# TYPE websocket_connections gauge
websocket_connections 42
```

## SDK Examples

### Python SDK
```python
from ai_orchestra import Client

client = Client(api_key="YOUR_TOKEN")

# Synchronous chat
response = client.chat(
    message="Explain machine learning",
    optimization_mode="balanced"
)

# Async streaming
async for token in client.stream_chat(
    message="Write a Python function",
    session_id="session-123"
):
    print(token, end="")
```

### JavaScript SDK
```javascript
import { AIOrchestra } from '@ai-orchestra/sdk';

const client = new AIOrchestra({ apiKey: 'YOUR_TOKEN' });

// Promise-based
const response = await client.chat({
  message: 'Explain React hooks',
  optimizationMode: 'quality'
});

// WebSocket streaming
const stream = client.streamChat({
  message: 'Generate a React component',
  onToken: (token) => console.log(token)
});
```

## Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Invalid request parameters | 400 |
| `AUTHENTICATION_ERROR` | Invalid or missing API key | 401 |
| `RATE_LIMIT_ERROR` | Rate limit exceeded | 429 |
| `INTERNAL_ERROR` | Internal server error | 500 |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | 503 |
| `TIMEOUT_ERROR` | Request timeout | 504 |

## Webhooks

Configure webhooks to receive async notifications:

```json
{
  "url": "https://your-server.com/webhook",
  "events": ["chat.completed", "session.ended"],
  "secret": "webhook-secret"
}
```

## Best Practices

1. **Session Management**: Reuse session IDs for conversation context
2. **Error Handling**: Implement exponential backoff for retries
3. **Rate Limiting**: Cache responses when possible
4. **WebSocket**: Implement reconnection logic with backoff
5. **Monitoring**: Track request IDs for debugging

## Migration Guide

### From v1 to v2
```diff
// v1 Request
{
  "text": "Hello",
  "sessionId": "123"
}

// v2 Request  
{
- "text": "Hello",
+ "message": "Hello",
- "sessionId": "123"
+ "session_id": "123",
+ "optimization_mode": "balanced"
}
```

## Support

- Documentation: https://docs.ai-orchestra.com
- Status Page: https://status.ai-orchestra.com
- Support Email: support@ai-orchestra.com
- Discord: https://discord.gg/ai-orchestra