# SOPHIA Intel API Documentation

> **API-First Architecture** | **Intelligent Model Routing** | **Agent Swarm Integration**

The SOPHIA Intel API provides a comprehensive interface for AI-powered development tasks through intelligent model routing and specialized agent swarms.

## 🌐 Base URL

- **Production**: `https://api.sophia-intel.ai`
- **Development**: `http://localhost:5000`

## 🔐 Authentication

All API requests require authentication via API key:

```bash
curl -H "Authorization: Bearer your-api-key" \
     https://api.sophia-intel.ai/api/health
```

## 📋 Core Endpoints

### Health & Status

#### `GET /api/health`
System health check with detailed component status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "components": {
    "api_server": "healthy",
    "ai_router": "healthy",
    "agent_swarm": "healthy",
    "mcp_servers": "healthy",
    "database": "healthy"
  },
  "metrics": {
    "uptime_seconds": 86400,
    "requests_per_minute": 45,
    "average_response_time_ms": 150
  }
}
```

#### `GET /api/status`
Detailed system status and performance metrics.

**Response:**
```json
{
  "version": "1.0.0",
  "environment": "production",
  "infrastructure": {
    "cluster_type": "cpu_optimized",
    "instance_count": 3,
    "instance_type": "cpu.c2-2",
    "region": "us-west-1"
  },
  "ai_models": {
    "available_models": 8,
    "primary_provider": "lambda_inference",
    "fallback_provider": "openrouter",
    "routing_decisions_per_hour": 1200
  }
}
```

---

## 🧠 AI Router API

The AI Router intelligently selects optimal models based on task requirements, cost preferences, and performance needs.

### Model Selection

#### `POST /api/ai/route`
Request intelligent model routing for a specific task.

**Request:**
```json
{
  "task_type": "code_generation",
  "prompt": "Create a Python function to calculate fibonacci numbers",
  "context": "Working on a mathematical utilities library",
  "preferences": {
    "cost_preference": "balanced",
    "quality_requirement": "high",
    "max_latency_ms": 5000
  },
  "metadata": {
    "requires_function_calling": false,
    "requires_structured_output": true,
    "max_tokens": 2000
  }
}
```

**Response:**
```json
{
  "routing_decision": {
    "selected_provider": "lambda_inference",
    "selected_model": "lambda-lfm-40b",
    "confidence_score": 0.92,
    "reasoning": "Selected for optimal balance of cost and performance for code generation tasks",
    "estimated_cost": 0.002,
    "estimated_latency_ms": 1200,
    "fallback_options": [
      ["openrouter", "openrouter-gpt-4o"],
      ["openai", "gpt-4o-mini"]
    ]
  },
  "execution_result": {
    "content": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "status": "success",
    "execution_time_ms": 1150,
    "actual_cost": 0.0018,
    "usage": {
      "prompt_tokens": 45,
      "completion_tokens": 120,
      "total_tokens": 165
    }
  }
}
```

### Available Models

#### `GET /api/ai/models`
List all available AI models with their capabilities.

**Response:**
```json
{
  "models": {
    "lambda_inference": [
      {
        "model_id": "lambda-lfm-40b",
        "name": "LFM 40B",
        "cost_per_1k_tokens": 0.001,
        "max_tokens": 8192,
        "context_window": 32768,
        "specialties": ["code_generation", "general_chat"],
        "supports_function_calling": false,
        "supports_structured_output": true,
        "avg_response_time_ms": 1200,
        "quality_score": 0.85
      }
    ],
    "openrouter": [
      {
        "model_id": "openrouter-gpt-4o",
        "name": "GPT-4o via OpenRouter",
        "cost_per_1k_tokens": 0.005,
        "max_tokens": 4096,
        "context_window": 128000,
        "specialties": ["code_generation", "function_calling", "structured_output"],
        "supports_function_calling": true,
        "supports_structured_output": true,
        "avg_response_time_ms": 2200,
        "quality_score": 0.95
      }
    ]
  }
}
```

---

## 🤖 Agent Swarm API

The Agent Swarm consists of six specialized agents that collaborate on complex development tasks.

### Mission Execution

#### `POST /api/agents/mission`
Execute a complex development mission using the agent swarm.

**Request:**
```json
{
  "mission": "Create a REST API for user authentication with JWT tokens",
  "requirements": {
    "language": "Python",
    "framework": "FastAPI",
    "database": "PostgreSQL",
    "testing": "pytest",
    "documentation": "OpenAPI"
  },
  "preferences": {
    "code_style": "PEP8",
    "security_level": "high",
    "performance_priority": "balanced"
  }
}
```

**Response:**
```json
{
  "mission_id": "mission_12345",
  "status": "in_progress",
  "estimated_completion_minutes": 15,
  "assigned_agents": [
    "planner",
    "coder", 
    "reviewer",
    "integrator",
    "tester",
    "documenter"
  ],
  "progress": {
    "current_phase": "planning",
    "completion_percentage": 10,
    "next_phase": "coding"
  }
}
```

#### `GET /api/agents/mission/{mission_id}`
Get status and results of a specific mission.

**Response:**
```json
{
  "mission_id": "mission_12345",
  "status": "completed",
  "completion_time": "2025-01-15T10:45:00Z",
  "duration_minutes": 12,
  "results": {
    "files_created": 8,
    "tests_written": 15,
    "documentation_pages": 3,
    "github_pr_url": "https://github.com/user/repo/pull/123"
  },
  "agent_contributions": {
    "planner": "Task decomposition and architecture design",
    "coder": "Implementation of 5 core modules",
    "reviewer": "Code review and optimization suggestions",
    "integrator": "CI/CD pipeline setup and deployment",
    "tester": "15 unit tests and integration tests",
    "documenter": "API documentation and README updates"
  },
  "deliverables": {
    "source_code": "/api/agents/mission/12345/code",
    "documentation": "/api/agents/mission/12345/docs",
    "tests": "/api/agents/mission/12345/tests"
  }
}
```

### Individual Agent Access

#### `POST /api/agents/{agent_type}/task`
Execute a task with a specific agent type.

**Agent Types:**
- `planner` - Task decomposition and strategy
- `coder` - Code generation and implementation
- `reviewer` - Code review and quality assurance
- `integrator` - System integration and deployment
- `tester` - Automated testing and validation
- `documenter` - Documentation generation

**Request Example (Coder Agent):**
```json
{
  "task": "Implement a caching decorator for expensive functions",
  "context": "Python utility library for data processing",
  "requirements": {
    "cache_type": "LRU",
    "max_size": 128,
    "ttl_seconds": 3600,
    "thread_safe": true
  }
}
```

---

## 🔌 MCP Server API

Model Context Protocol (MCP) servers provide standardized interfaces for various development tools.

### Code Context

#### `GET /api/mcp/code/context`
Get comprehensive code context for a repository.

**Parameters:**
- `repo` (required): Repository identifier
- `path` (optional): Specific path within repository
- `context_type` (optional): `full`, `summary`, `structure`

**Response:**
```json
{
  "repository": "ai-cherry/sophia-intel",
  "context_type": "full",
  "structure": {
    "total_files": 156,
    "languages": {
      "Python": 89,
      "TypeScript": 34,
      "YAML": 18,
      "Markdown": 15
    },
    "key_modules": [
      "mcp_servers/ai_router.py",
      "agents/coding_swarm.py",
      "infra/__main__.py"
    ]
  },
  "summary": "AI-first development platform with intelligent model routing...",
  "recent_changes": [
    {
      "file": "mcp_servers/ai_router.py",
      "change": "Added Lambda Inference API integration",
      "timestamp": "2025-01-15T09:30:00Z"
    }
  ]
}
```

### GitHub Integration

#### `POST /api/mcp/github/pr`
Create a pull request with generated code.

**Request:**
```json
{
  "repository": "ai-cherry/sophia-intel",
  "branch": "feature/new-api-endpoint",
  "title": "Add user authentication API endpoint",
  "description": "Implements JWT-based authentication with refresh tokens",
  "files": [
    {
      "path": "api/auth.py",
      "content": "# Authentication module implementation...",
      "action": "create"
    },
    {
      "path": "tests/test_auth.py", 
      "content": "# Authentication tests...",
      "action": "create"
    }
  ]
}
```

**Response:**
```json
{
  "pr_number": 123,
  "pr_url": "https://github.com/ai-cherry/sophia-intel/pull/123",
  "status": "created",
  "checks": {
    "ci_pipeline": "pending",
    "code_review": "pending",
    "security_scan": "pending"
  }
}
```

---

## 📊 Analytics & Monitoring

### Usage Analytics

#### `GET /api/analytics/usage`
Get detailed usage analytics and performance metrics.

**Response:**
```json
{
  "time_period": "last_24_hours",
  "api_requests": {
    "total": 2847,
    "successful": 2801,
    "failed": 46,
    "success_rate": 98.4
  },
  "ai_routing": {
    "total_decisions": 1205,
    "lambda_inference_usage": 68.2,
    "openrouter_usage": 28.1,
    "openai_fallback_usage": 3.7,
    "average_decision_time_ms": 45
  },
  "agent_missions": {
    "completed": 89,
    "in_progress": 12,
    "average_completion_time_minutes": 8.5,
    "success_rate": 94.3
  },
  "cost_analysis": {
    "total_cost_usd": 12.45,
    "cost_per_request": 0.0044,
    "cost_savings_vs_gpu": 78.2
  }
}
```

### Performance Metrics

#### `GET /api/analytics/performance`
Get detailed performance metrics for optimization.

**Response:**
```json
{
  "response_times": {
    "p50_ms": 120,
    "p95_ms": 450,
    "p99_ms": 890,
    "average_ms": 185
  },
  "throughput": {
    "requests_per_second": 45.2,
    "peak_rps": 127.8,
    "concurrent_connections": 23
  },
  "resource_utilization": {
    "cpu_usage_percent": 34.5,
    "memory_usage_percent": 42.1,
    "disk_usage_percent": 18.7
  },
  "model_performance": {
    "lambda_lfm_40b": {
      "avg_response_time_ms": 1150,
      "success_rate": 99.2,
      "cost_per_1k_tokens": 0.001
    },
    "openrouter_gpt_4o": {
      "avg_response_time_ms": 2200,
      "success_rate": 98.8,
      "cost_per_1k_tokens": 0.005
    }
  }
}
```

---

## 🔧 Configuration API

### System Configuration

#### `GET /api/config`
Get current system configuration.

#### `PUT /api/config`
Update system configuration (admin only).

**Request:**
```json
{
  "ai_router": {
    "default_cost_preference": "balanced",
    "fallback_enabled": true,
    "circuit_breaker_threshold": 5
  },
  "agent_swarm": {
    "max_concurrent_missions": 10,
    "default_timeout_minutes": 30
  },
  "infrastructure": {
    "auto_scaling_enabled": true,
    "min_replicas": 2,
    "max_replicas": 10
  }
}
```

---

## 🚨 Error Handling

All API endpoints return consistent error responses:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request parameters are invalid",
    "details": {
      "field": "task_type",
      "issue": "must be one of: code_generation, analysis, reasoning, documentation"
    },
    "correlation_id": "req_12345",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

### Common Error Codes

- `INVALID_REQUEST` (400) - Request validation failed
- `UNAUTHORIZED` (401) - Invalid or missing API key
- `FORBIDDEN` (403) - Insufficient permissions
- `NOT_FOUND` (404) - Resource not found
- `RATE_LIMITED` (429) - Rate limit exceeded
- `INTERNAL_ERROR` (500) - Internal server error
- `SERVICE_UNAVAILABLE` (503) - Service temporarily unavailable

---

## 📚 SDK & Libraries

### Python SDK

```python
from sophia_intel import SophiaClient

client = SophiaClient(api_key="your-api-key")

# AI Router usage
result = client.ai.route(
    task_type="code_generation",
    prompt="Create a REST API endpoint",
    preferences={"cost_preference": "balanced"}
)

# Agent Swarm usage
mission = client.agents.start_mission(
    mission="Build a user authentication system",
    requirements={"language": "Python", "framework": "FastAPI"}
)
```

### JavaScript SDK

```javascript
import { SophiaClient } from '@sophia-intel/sdk';

const client = new SophiaClient({ apiKey: 'your-api-key' });

// AI Router usage
const result = await client.ai.route({
  taskType: 'code_generation',
  prompt: 'Create a REST API endpoint',
  preferences: { costPreference: 'balanced' }
});

// Agent Swarm usage
const mission = await client.agents.startMission({
  mission: 'Build a user authentication system',
  requirements: { language: 'Python', framework: 'FastAPI' }
});
```

---

## 🔗 Webhooks

Configure webhooks to receive real-time notifications about mission completions, system events, and performance alerts.

### Webhook Events

- `mission.completed` - Agent mission completed
- `mission.failed` - Agent mission failed
- `system.alert` - System performance alert
- `cost.threshold` - Cost threshold exceeded
- `model.fallback` - Model fallback triggered

### Webhook Payload Example

```json
{
  "event": "mission.completed",
  "timestamp": "2025-01-15T10:45:00Z",
  "data": {
    "mission_id": "mission_12345",
    "duration_minutes": 12,
    "files_created": 8,
    "github_pr_url": "https://github.com/user/repo/pull/123"
  }
}
```

---

**SOPHIA Intel API** - Powering AI-first development with intelligent automation and cost-optimized infrastructure.

