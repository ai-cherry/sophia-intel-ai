# Natural Language Interface Implementation
## Phase 2, Week 3-4: Natural Language Processing with n8n Workflows

### Overview
This implementation provides a Natural Language Interface for the Sophia Intel AI system, allowing users to interact with the system using simple natural language commands. The interface uses pattern matching and Ollama for intent extraction, sequential agent orchestration, and n8n workflow integration.

### Key Features
- **Natural Language Processing**: Simple pattern-based NLP with Ollama fallback
- **Intent Recognition**: 9 predefined intents for common system operations
- **Agent Orchestration**: Sequential execution of agents (researcher → coder → reviewer)
- **n8n Integration**: Workflow automation for complex operations
- **Chat Interface**: Streamlit-based UI for easy interaction
- **API Endpoints**: RESTful API for programmatic access
- **State Management**: Redis-based session and state persistence

### Architecture Components

#### 1. Natural Language Processor (`app/nl_interface/quicknlp.py`)
- Pattern-based intent matching
- Ollama integration for complex queries
- Entity extraction from commands
- Confidence scoring

#### 2. Intent Definitions (`app/nl_interface/intents.py`)
- Predefined intent patterns
- Response templates
- Workflow mappings
- Help text generation

#### 3. Simple Agent Orchestrator (`app/agents/simple_orchestrator.py`)
- Sequential agent execution
- Redis-based state management
- Agent roles: Researcher, Coder, Reviewer, Executor, Monitor
- Async workflow execution

#### 4. API Endpoints (`app/api/nl_endpoints.py`)
- `/api/nl/process` - Process natural language commands
- `/api/nl/intents` - List available intents
- `/api/workflows/trigger` - Trigger n8n workflows
- `/api/workflows/status` - Get workflow execution status
- `/api/agents/execute` - Execute specific agents
- `/api/system/status` - Get system status

#### 5. Chat UI (`app/ui/streamlit_chat.py`)
- Interactive chat interface
- System status monitoring
- Quick command buttons
- Session management
- Debug information

#### 6. n8n Workflows (`n8n/workflows/basic-templates.json`)
- System status workflow
- Agent execution workflow
- Service scaling workflow
- Data query workflow
- Metrics collection workflow

### Supported Commands

| Intent | Example Commands | Description |
|--------|-----------------|-------------|
| `system_status` | "show system status", "how is the system doing" | Check system and service status |
| `run_agent` | "run agent researcher", "start coding agent" | Execute a specific agent |
| `scale_service` | "scale redis to 3", "increase ollama instances" | Scale service replicas |
| `execute_workflow` | "run workflow backup", "execute data-pipeline" | Trigger n8n workflows |
| `query_data` | "search for user documents", "find recent logs" | Query vector store |
| `stop_service` | "stop redis", "shutdown ollama" | Stop a running service |
| `list_agents` | "list all agents", "show available agents" | List available agents |
| `get_metrics` | "show metrics", "get metrics for ollama" | Get performance metrics |
| `help` | "help", "what can you do" | Show available commands |

### Installation and Setup

#### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- 8GB+ RAM recommended
- Ports available: 8003, 8501, 5678, 8080, 11434, 6379, 5432

#### Quick Start

1. **Start all services**:
```bash
chmod +x start-nl-interface.sh
./start-nl-interface.sh
```

2. **Access the interfaces**:
- Chat UI: http://localhost:8501
- API Documentation: http://localhost:8003/docs
- n8n Workflows: http://localhost:5678

3. **Test the system**:
```bash
# Quick component test
python app/nl_interface/test_nl.py --quick

# Full integration test
python app/nl_interface/test_nl.py
```

### Docker Services

| Service | Port | Description |
|---------|------|-------------|
| Ollama | 11434 | Local LLM for NLP and agent processing |
| Weaviate | 8080 | Vector database for semantic search |
| Redis | 6379 | Cache and state management |
| PostgreSQL | 5432 | Metadata storage |
| n8n | 5678 | Workflow automation engine |
| API Server | 8003 | FastAPI NL processing endpoints |
| Streamlit UI | 8501 | Chat interface |

### Testing

#### Unit Tests
```bash
# Test NLP processing
python app/nl_interface/test_nl.py --quick
```

#### Integration Tests
```bash
# Full system test
python app/nl_interface/test_nl.py

# API endpoint tests
curl http://localhost:8003/api/nl/health
curl -X POST http://localhost:8003/api/nl/process \
  -H "Content-Type: application/json" \
  -d '{"text": "show system status"}'
```

#### Manual Testing
1. Open http://localhost:8501
2. Try commands like:
   - "show system status"
   - "list all agents"
   - "help"
   - "run agent researcher"

### API Usage Examples

#### Process Natural Language Command
```python
import requests

response = requests.post(
    "http://localhost:8003/api/nl/process",
    json={
        "text": "show system status",
        "context": {}
    }
)
result = response.json()
print(f"Intent: {result['intent']}")
print(f"Response: {result['response_text']}")
```

#### Execute Agent
```python
response = requests.post(
    "http://localhost:8003/api/nl/agents/execute",
    params={
        "agent_name": "researcher",
        "task": "Research best practices for API design"
    }
)
```

### Key Simplifications from Original Plan

1. **No LangGraph**: Using simple sequential orchestration instead
2. **Pattern Matching**: Primary NLP method with Ollama as fallback
3. **Basic State Management**: Redis for simple key-value storage
4. **No GPU Required**: CPU-only implementation for MVP
5. **Minimal Dependencies**: Focused on core functionality

### Troubleshooting

#### Services not starting
```bash
# Check Docker status
docker ps -a

# View logs
docker-compose -f docker-compose.minimal.yml logs [service_name]

# Restart services
docker-compose -f docker-compose.minimal.yml restart
```

#### Port conflicts
```bash
# Check port usage
lsof -i :8003  # API
lsof -i :8501  # Streamlit
lsof -i :5678  # n8n
```

#### Ollama model issues
```bash
# Pull model manually
docker exec sophia-ollama ollama pull llama3.2:3b

# List available models
docker exec sophia-ollama ollama list
```

### Next Steps (Week 5-6)

- [ ] GPU integration for faster processing
- [ ] Advanced caching strategies
- [ ] Production deployment with Kubernetes
- [ ] Enhanced error handling and retry logic
- [ ] Multi-user session management
- [ ] Advanced semantic parsing
- [ ] Custom n8n workflow creation UI

### File Structure
```
sophia-intel-ai/
├── app/
│   ├── nl_interface/
│   │   ├── quicknlp.py          # NLP processor
│   │   ├── intents.py           # Intent definitions
│   │   └── test_nl.py           # Test suite
│   ├── agents/
│   │   └── simple_orchestrator.py # Agent orchestration
│   ├── api/
│   │   └── nl_endpoints.py      # API endpoints
│   ├── ui/
│   │   └── streamlit_chat.py    # Chat interface
│   └── main_nl.py                # FastAPI app
├── n8n/
│   └── workflows/
│       └── basic-templates.json  # n8n workflows
├── docker-compose.minimal.yml    # Docker services
├── Dockerfile.minimal            # Container definition
├── start-nl-interface.sh         # Startup script
└── NL_INTERFACE_README.md       # This file
```

### Contributors
Phase 2 Week 3-4 Implementation Team

### License
MIT License - See LICENSE file for details