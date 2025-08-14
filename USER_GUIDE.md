# Sophia Intelligence Swarm System - Complete User Guide

## 🎯 System Overview

The Sophia Intelligence Swarm System is a production-ready multi-agent AI system featuring:
- **Linear Deterministic Workflow**: architect → builder → tester → operator
- **MCP-First RAG**: Intelligent context retrieval with cloud fallback
- **Comprehensive Telemetry**: Real-time monitoring and performance tracking
- **No-BS Tone Filtering**: Structured, professional output format
- **Cloud-Native Architecture**: Qdrant Cloud, Redis integration

---

## 📋 Prerequisites & System Requirements

### Required Software
- **Python 3.8+** (recommended: 3.9+)
- **Git** (for version control)
- **Make** (for automation commands)

### Cloud Services (Optional but Recommended)
- **Qdrant Cloud** account for vector search
- **Redis Cloud** account for caching
- **OpenAI API key** or compatible LLM service

### Environment
- **Linux/macOS**: Fully supported
- **Windows**: Supported via WSL2
- **VS Code**: Enhanced integration with MCP support

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
# Clone or navigate to your repository
cd /path/to/sophia-intel

# Install dependencies
make deps

# Alternative: Manual installation
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (see Configuration Guide below)
nano .env
```

### 3. First Run

```bash
# Test the system
python -m swarm.cli --task "create a hello world function"

# Monitor telemetry (in another terminal)
python scripts/tail_handoffs.py
```

---

## ⚙️ Configuration Guide

### Environment Variables (.env file)

#### **Core System Settings**
```bash
# Tone filtering (recommended: no_bs)
ROO_TONE=no_bs

# MCP Integration
USE_MCP=1
MCP_SESSION_DIR=.sophia_sessions
MCP_CODE_CONTEXT=stdio
MCP_HTTP_URL=http://127.0.0.1:8765
```

#### **RAG & Search Configuration**
```bash
# Qdrant Cloud (for production)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key-here
QDRANT_COLLECTION=repo_docs
RAG_TOPK=8
```

#### **LLM Configuration**
```bash
# Option 1: OpenAI/Compatible API
OPENAI_API_KEY=your-openai-api-key
LLM_MODEL=gpt-4

# Option 2: Local vLLM/Ollama
OPENAI_BASE_URL=http://localhost:8000/v1
LLM_MODEL=llama-3.1-8b

# Option 3: Local Ollama
OLLAMA_MODEL=llama3.2
```

#### **Resource Limits**
```bash
LLM_TIMEOUT=30
MAX_ARTIFACT_CHARS=20000
MAX_SWARM_HOPS=12
MAX_STAGE_TIME_MINUTES=10
```

### Configuration Validation
```bash
# Verify configuration
python -c "from config.config import settings; print('Config loaded:', settings.qdrant_collection)"
```

---

## 📖 Usage Instructions

### Basic Usage

#### Command Line Interface
```bash
# Run a swarm task
python -m swarm.cli --task "your task description here"

# Examples
python -m swarm.cli --task "refactor this Python class for better performance"
python -m swarm.cli --task "add comprehensive logging to a web API"
python -m swarm.cli --task "create unit tests for a data processing pipeline"
```

#### Programmatic Usage
```python
from swarm.graph import run

# Execute swarm task
result = run("create a REST API endpoint for user management")

# Access individual agent outputs
architect_output = result.get('architect', '')
builder_output = result.get('builder', '')
tester_output = result.get('tester', '')
operator_output = result.get('operator', '')
```

### Advanced Usage

#### Repository Indexing (Production Setup)
```bash
# Index your repository for better context
python scripts/index_repo.py

# Verify indexing
python -c "from rag.pipeline import repo_search; print(len(repo_search('function')))"
```

#### Real-Time Monitoring
```bash
# Monitor swarm activity
python scripts/tail_handoffs.py

# View metrics only
python scripts/tail_handoffs.py --metrics
```

#### VS Code Integration (Roo Modes)
1. Open VS Code in your project directory
2. Access Roo modes: `Ctrl+Shift+P` → "Roo: Switch Mode"
3. Select from available modes:
   - **Architect**: System design and planning
   - **Builder**: Implementation and coding
   - **Tester**: Quality assurance and testing
   - **Operator**: Deployment and operations

---

## 🏗️ System Architecture

### Agent Flow
```
User Input → Supervisor → Architect → Builder → Tester → Operator → Results
                ↑                                                        ↓
                └──────────── Circuit Breakers ←───────────────────────┘
```

### Circuit Breakers
- **Hop Limit**: Maximum 12 transitions between agents
- **Time Limit**: Maximum 10 minutes per task
- **Error Limit**: Maximum 3 errors before termination
- **Artifact Validation**: Minimum 50 characters per agent output

### Context Sources (Priority Order)
1. **MCP Integration** (primary)
2. **Qdrant Cloud** (fallback)
3. **Mock Data** (development)

---

## 🔧 Troubleshooting Guide

### Common Issues

#### Issue: "No module named 'langgraph'"
**Solution:**
```bash
pip install langgraph>=0.2.40
# or
make deps
```

#### Issue: "Qdrant collection doesn't exist"
**Solutions:**
1. **Index your repository:**
   ```bash
   python scripts/index_repo.py
   ```
2. **Check Qdrant credentials:**
   ```bash
   python -c "import os; print('URL:', os.getenv('QDRANT_URL')); print('Key:', bool(os.getenv('QDRANT_API_KEY')))"
   ```
3. **Verify collection name:**
   ```bash
   # Ensure QDRANT_COLLECTION matches your setup
   echo $QDRANT_COLLECTION
   ```

#### Issue: "LLM timeout" or "No response"
**Solutions:**
1. **Increase timeout:**
   ```bash
   export LLM_TIMEOUT=60
   ```
2. **Check LLM service:**
   ```bash
   # For OpenAI
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   
   # For local Ollama
   curl http://localhost:11434/api/tags
   ```

#### Issue: "Agent outputs are too verbose"
**Solution:**
```bash
# Enable No-BS filtering
export ROO_TONE=no_bs

# Reduce output limits
export MAX_ARTIFACT_CHARS=10000
```

### Performance Issues

#### Slow Execution
1. **Reduce RAG context:**
   ```bash
   export RAG_TOPK=3
   export MAX_RAG_CHARS=4000
   ```

2. **Use faster LLM model:**
   ```bash
   export LLM_MODEL=gpt-3.5-turbo  # Instead of gpt-4
   ```

3. **Enable caching:**
   ```bash
   export RAG_CACHE_TTL=600  # 10 minutes
   ```

#### High Memory Usage
1. **Limit concurrent operations:**
   ```bash
   export INDEX_BATCH_SIZE=50  # Reduce from 100
   ```

2. **Clear old logs:**
   ```bash
   rm .swarm_handoffs.log.*
   truncate -s 0 .swarm_handoffs.log
   ```

### Debugging

#### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from swarm.graph import run
result = run("debug task")
```

#### Inspect Telemetry
```bash
# View recent activity
tail -20 .swarm_handoffs.log

# Parse JSON logs
cat .swarm_handoffs.log | jq '.'

# Check metrics
python scripts/tail_handoffs.py --metrics | jq '.'
```

---

## ⚠️ Important Warnings & Limitations

### Security Considerations
- **API Keys**: Never commit API keys to version control
- **Local LLMs**: Ensure proper network isolation for sensitive data
- **File Access**: The indexer reads all repository files - exclude sensitive directories

### Resource Limits
- **LLM Costs**: Monitor API usage, especially with GPT-4
- **Qdrant Storage**: Each indexed document uses vector storage
- **Memory Usage**: Large repositories may require substantial RAM

### Current Limitations
1. **Language Support**: Optimized for Python, JavaScript, TypeScript
2. **File Size**: Individual files >1MB are skipped during indexing
3. **Concurrent Tasks**: Single task execution at a time
4. **Network Dependencies**: Requires internet for cloud services

### Best Practices
- **Repository Size**: <10,000 files for optimal performance
- **Task Complexity**: Break large tasks into smaller components
- **Monitoring**: Always monitor `.swarm_handoffs.log` for issues
- **Backups**: Regular backups of Qdrant collections recommended

---

## 🛠️ Advanced Configuration

### Custom LLM Integration
```python
# swarm/graph.py customization
def _llm():
    if os.getenv("CUSTOM_LLM_ENDPOINT"):
        return CustomChatLLM(
            endpoint=os.getenv("CUSTOM_LLM_ENDPOINT"),
            model=os.getenv("CUSTOM_LLM_MODEL"),
            timeout=float(os.getenv("LLM_TIMEOUT", "30"))
        )
    # ... existing code
```

### Custom Agent Prompts
Edit the agent prompts in `swarm/graph.py`:
```python
graph.add_node("architect", _agent_with_monitoring(
    "architect", 
    "You are a senior software architect. Focus on system design and technical specifications..."
))
```

### Custom Indexing Rules
Modify `scripts/index_repo.py`:
```python
# Add custom file patterns
CUSTOM_EXTENSIONS = {
    '.proto': 'protobuf',
    '.graphql': 'graphql',
    '.tf': 'terraform'
}
FILE_EXTENSIONS.update(CUSTOM_EXTENSIONS)
```

---

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# System health check
python -c "
from swarm.graph import run
from rag.pipeline import rag_tool
print('Swarm:', bool(run('health check')))
print('RAG:', bool(rag_tool('test')))
print('System: Healthy')
"
```

### Log Management
```bash
# Rotate large logs
if [ -f .swarm_handoffs.log ] && [ $(stat -f%z .swarm_handoffs.log 2>/dev/null || stat -c%s .swarm_handoffs.log) -gt 52428800 ]; then
    mv .swarm_handoffs.log .swarm_handoffs.log.$(date +%s)
fi
```

### Performance Monitoring
```python
# Custom monitoring script
import time
from swarm.graph import run

start = time.time()
result = run("performance test task")
duration = time.time() - start

print(f"Task completed in {duration:.2f}s")
print(f"Agents executed: {len(result)}")
```

---

## 🆘 Support & Troubleshooting

### Getting Help
1. **Check logs**: `.swarm_handoffs.log` for execution details
2. **Verify configuration**: All required environment variables set
3. **Test components**: Individual system components work in isolation
4. **Monitor resources**: Sufficient memory, disk space, network connectivity

### Diagnostic Commands
```bash
# Quick system check
make deps && python -c "from swarm.graph import run; print('System ready')"

# Component diagnostics
python scripts/tail_handoffs.py --metrics
python -c "from rag.pipeline import repo_search; print('RAG ready')"
python -c "from integrations.mcp_tools import mcp_semantic_search; print('MCP ready')"
```

### Emergency Reset
```bash
# Reset to clean state
rm -rf .sophia_sessions/
rm -f .swarm_handoffs.log*
rm -f .swarm_metrics.json
rm -f .indexing_report_*.json

# Restart system
make deps
python -m swarm.cli --task "system test"
```

---

## 📝 Changelog & Version Notes

### Current Version: 1.0.0
- ✅ Linear deterministic agent workflow
- ✅ MCP-first RAG integration
- ✅ Comprehensive telemetry system
- ✅ No-BS tone filtering
- ✅ Production-ready error handling
- ✅ Cloud-native architecture support

### Known Issues
- Memory system requires external mem0 service
- Qdrant indexing requires adequate vector storage
- Large repositories may need chunking strategies

---

*For additional support, check the system logs and ensure all prerequisites are properly configured.*