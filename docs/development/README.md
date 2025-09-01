# Development Guide

## Overview

Comprehensive guide for developers contributing to Sophia Intel AI, covering setup, architecture, testing, and best practices.

## Development Setup

### Prerequisites

- Python 3.10+ (3.11 recommended)
- Node.js 18+ and npm 9+
- Docker Desktop
- Git
- VS Code or PyCharm (recommended)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/ai-cherry/sophia-intel-ai.git
cd sophia-intel-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Install UI dependencies
cd agent-ui && npm install
cd ..
```

## Project Structure

```
sophia-intel-ai/
├── app/                      # Main application code
│   ├── api/                 # API endpoints and routers
│   │   ├── routers/        # Modular endpoint groups
│   │   └── unified_server.py
│   ├── core/               # Core functionality
│   │   ├── config.py      # Configuration management
│   │   ├── middleware.py  # API middleware
│   │   └── observability.py
│   ├── memory/            # Memory system
│   │   ├── supermemory_mcp.py
│   │   └── dual_tier_embeddings.py
│   ├── swarms/            # Agent swarms
│   │   ├── orchestrator.py
│   │   └── agents/
│   ├── models/            # Data models
│   │   └── schemas.py
│   ├── repositories/      # Data access layer
│   │   └── base.py
│   └── tasks/             # Background tasks
│       └── indexing.py
├── agent-ui/             # Next.js Agent playground UI
├── tests/                # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── docker/               # Docker configurations
└── .github/             # GitHub workflows
```

## Development Workflow

### 1. Create Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

```bash
# Run development servers
./scripts/dev.sh

# Or manually:
python -m app.api.unified_server &
python -m app.agno_bridge &
cd agent-ui && npm run dev &
```

### 3. Write Tests

```python
# tests/unit/test_memory.py
import pytest
from app.memory.supermemory_mcp import SupermemoryStore

@pytest.fixture
def memory_store():
    return SupermemoryStore(":memory:")

def test_add_memory(memory_store):
    memory = memory_store.add_memory(
        topic="Test",
        content="Test content"
    )
    assert memory.hash_id is not None
    assert memory.topic == "Test"
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/unit/test_memory.py::test_add_memory

# Run integration tests
pytest -m integration
```

### 5. Code Quality Checks

```bash
# Format code
black app tests

# Lint code
ruff check app tests

# Type checking
mypy app

# Security scan
bandit -r app

# Or run all checks
pre-commit run --all-files
```

### 6. Commit Changes

```bash
# Stage changes
git add .

# Commit with conventional message
git commit -m "feat: add memory deduplication"

# Push to remote
git push origin feature/your-feature-name
```

### 7. Create Pull Request

```bash
# Using GitHub CLI
gh pr create --title "feat: add memory deduplication" \
  --body "Implements semantic deduplication for memory entries"

# Or via GitHub web interface
```

## Plugin Development

### Creating a Plugin

```python
# app/plugins/custom_plugin.py
from app.plugins.base import Plugin, PluginMetadata

class CustomPlugin(Plugin):
    """Custom plugin implementation."""
    
    def __init__(self):
        self.metadata = PluginMetadata(
            name="custom-plugin",
            version="1.0.0",
            description="Custom functionality",
            author="Your Name"
        )
    
    async def initialize(self, config: dict):
        """Initialize plugin with configuration."""
        self.config = config
        # Setup resources
    
    async def execute(self, context: dict) -> dict:
        """Execute plugin functionality."""
        # Plugin logic here
        return {"status": "success"}
    
    async def cleanup(self):
        """Cleanup plugin resources."""
        # Cleanup logic
```

### Registering Plugin

```python
# app/plugins/__init__.py
from app.plugins.registry import PluginRegistry
from app.plugins.custom_plugin import CustomPlugin

# Register plugin
registry = PluginRegistry()
registry.register(CustomPlugin())
```

### Plugin Configuration

```yaml
# config/plugins.yaml
plugins:
  custom-plugin:
    enabled: true
    config:
      option1: value1
      option2: value2
```

## Agent Development

### Creating Custom Agent

```python
# app/swarms/agents/custom_agent.py
from app.swarms.base import Agent, AgentRole

class CustomAgent(Agent):
    """Custom agent implementation."""
    
    def __init__(self):
        super().__init__(
            agent_id="custom_agent_001",
            name="Custom Agent",
            role=AgentRole.SPECIALIST,
            capabilities=["analysis", "planning"],
            model="claude-3-opus",
            temperature=0.7
        )
    
    async def process_task(self, task: str, context: dict) -> str:
        """Process assigned task."""
        # Build prompt
        prompt = self.build_prompt(task, context)
        
        # Get LLM response
        response = await self.llm.complete(prompt)
        
        # Process and return
        return self.format_response(response)
    
    def build_prompt(self, task: str, context: dict) -> str:
        """Build agent-specific prompt."""
        return f"""
        You are a {self.name} with expertise in {', '.join(self.capabilities)}.
        
        Task: {task}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Provide a detailed response:
        """
```

### Agent Configuration

```json
{
  "agent": {
    "id": "custom_agent_001",
    "name": "Custom Agent",
    "model": {
      "provider": "anthropic",
      "name": "claude-3-opus",
      "parameters": {
        "temperature": 0.7,
        "max_tokens": 4000,
        "top_p": 0.9
      }
    },
    "prompts": {
      "system": "You are an expert analyst...",
      "examples": [
        {"input": "...", "output": "..."}
      ]
    }
  }
}
```

## API Development

### Adding New Endpoint

```python
# app/api/routers/custom.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import CustomRequest, CustomResponse

router = APIRouter(prefix="/custom", tags=["custom"])

@router.post("/process", response_model=CustomResponse)
async def process_custom(request: CustomRequest):
    """Process custom request."""
    try:
        # Process request
        result = await process_logic(request)
        
        return CustomResponse(
            status="success",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Register in main app
# app/api/unified_server.py
from app.api.routers import custom
app.include_router(custom.router)
```

### Adding Middleware

```python
# app/core/custom_middleware.py
from fastapi import Request
import time

class TimingMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

# Register middleware
app.add_middleware(TimingMiddleware)
```

## Testing Guidelines

### Unit Tests

```python
# tests/unit/test_orchestrator.py
import pytest
from unittest.mock import Mock, AsyncMock
from app.swarms import SwarmOrchestrator

@pytest.fixture
def orchestrator():
    return SwarmOrchestrator()

@pytest.fixture
def mock_agent():
    agent = Mock()
    agent.process_task = AsyncMock(return_value="Result")
    return agent

@pytest.mark.asyncio
async def test_execute_task(orchestrator, mock_agent):
    orchestrator.register_agent(mock_agent)
    
    result = await orchestrator.execute_task(
        task="Test task",
        agent_id=mock_agent.agent_id
    )
    
    assert result == "Result"
    mock_agent.process_task.assert_called_once()
```

### Integration Tests

```python
# tests/integration/test_api.py
import pytest
from httpx import AsyncClient
from app.api.unified_server import app

@pytest.mark.integration
@pytest.mark.asyncio
async def test_team_execution():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/run/team",
            json={
                "request": "Test request",
                "team_id": "test_team"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
```

### E2E Tests

```python
# tests/e2e/test_workflow.py
import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Navigate to UI
        await page.goto("http://localhost:3001")
        
        # Interact with UI
        await page.fill("#prompt", "Analyze this code")
        await page.click("#submit")
        
        # Wait for response
        await page.wait_for_selector(".response")
        
        # Verify result
        content = await page.text_content(".response")
        assert "Analysis complete" in content
        
        await browser.close()
```

## Debugging

### VS Code Configuration

**.vscode/launch.json:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug API Server",
      "type": "python",
      "request": "launch",
      "module": "app.api.unified_server",
      "env": {
        "LOCAL_DEV_MODE": "true",
        "LOG_LEVEL": "DEBUG"
      }
    },
    {
      "name": "Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-vv", "${file}"]
    }
  ]
}
```

### Logging

```python
import logging
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Use structured logging
logger.info(
    "Processing request",
    extra={
        "request_id": "123",
        "user_id": "456",
        "action": "team_execution"
    }
)

# Debug logging
logger.debug("Detailed information", extra={"data": data})

# Error logging with traceback
try:
    risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        exc_info=True,
        extra={"error": str(e)}
    )
```

### Performance Profiling

```python
# Profile with cProfile
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Code to profile
    expensive_operation()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)

# Profile with memory_profiler
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Code that uses memory
    large_list = [i for i in range(1000000)]
    return large_list
```

## Code Style Guide

### Python Style

```python
# Good example
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Configuration for an agent.
    
    Attributes:
        agent_id: Unique identifier
        name: Human-readable name
        model: LLM model to use
    """
    agent_id: str
    name: str
    model: str
    temperature: float = 0.7
    
    def validate(self) -> bool:
        """Validate configuration.
        
        Returns:
            True if valid, False otherwise
        """
        return (
            self.agent_id 
            and self.name 
            and 0.0 <= self.temperature <= 1.0
        )

async def process_request(
    request: Dict[str, Any],
    config: Optional[AgentConfig] = None
) -> Dict[str, Any]:
    """Process incoming request.
    
    Args:
        request: The request data
        config: Optional configuration
    
    Returns:
        Processed response
    
    Raises:
        ValueError: If request is invalid
    """
    if not request:
        raise ValueError("Request cannot be empty")
    
    config = config or AgentConfig(
        agent_id="default",
        name="Default Agent",
        model="gpt-4"
    )
    
    # Process request
    result = await execute_with_config(request, config)
    
    return {
        "status": "success",
        "data": result
    }
```

### TypeScript Style

```typescript
// Good example
interface AgentConfig {
  agentId: string;
  name: string;
  model: string;
  temperature?: number;
}

class AgentOrchestrator {
  private agents: Map<string, Agent>;
  
  constructor(private config: AgentConfig) {
    this.agents = new Map();
  }
  
  async executeTask(
    task: string,
    context?: Record<string, unknown>
  ): Promise<AgentResponse> {
    try {
      const agent = this.selectAgent(task);
      const response = await agent.process(task, context);
      
      return {
        status: 'success',
        data: response,
      };
    } catch (error) {
      console.error('Task execution failed:', error);
      throw new Error(`Failed to execute task: ${error.message}`);
    }
  }
  
  private selectAgent(task: string): Agent {
    // Agent selection logic
    return this.agents.get('default') ?? new DefaultAgent();
  }
}
```

## Documentation

### Docstring Format

```python
def complex_function(
    param1: str,
    param2: Optional[int] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Brief description of function.
    
    Longer description explaining what the function does,
    any important details, and usage examples.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: None)
        **kwargs: Additional keyword arguments:
            - option1: Description
            - option2: Description
    
    Returns:
        Dictionary containing:
            - key1: Description
            - key2: Description
    
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer
    
    Examples:
        >>> result = complex_function("test", param2=42)
        >>> print(result["status"])
        'success'
    
    Note:
        This function is thread-safe.
    """
    pass
```

## Contributing

### Pull Request Process

1. **Fork and Clone**
2. **Create Feature Branch**
3. **Make Changes**
4. **Write/Update Tests**
5. **Update Documentation**
6. **Run Quality Checks**
7. **Submit PR**
8. **Address Review Comments**
9. **Merge**

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No new warnings
```

## Resources

### Internal Documentation
- [Architecture Guide](../architecture/README.md)
- [API Reference](../api/README.md)
- [Deployment Guide](../deployment/README.md)

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Pydantic Documentation](https://docs.pydantic.dev)
- [Celery Documentation](https://docs.celeryq.dev)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)

### Community
- GitHub Discussions: [github.com/ai-cherry/sophia-intel-ai/discussions](https://github.com/ai-cherry/sophia-intel-ai/discussions)
- Discord: [discord.gg/sophia-intel](https://discord.gg/sophia-intel)
- Email: dev@sophia-intel.ai