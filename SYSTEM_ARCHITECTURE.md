# System Architecture Overview

## Core Components

### 1. SuperOrchestrator (`app/core/super_orchestrator.py`)
The central control system for all orchestration needs.

**Features:**
- Embedded memory, state, and task managers
- AI-powered monitoring and optimization
- WebSocket support for real-time UI
- Self-healing capabilities

**Usage:**
```python
from app.core.super_orchestrator import get_orchestrator

orchestrator = get_orchestrator()
await orchestrator.initialize()

response = await orchestrator.process_request({
    "type": "chat",
    "message": "Hello!"
})
```

### 2. AI Logger (`app/core/ai_logger.py`)
Intelligent logging system replacing all print statements.

**Features:**
- Pattern analysis and anomaly detection
- Root cause analysis
- Structured logging with trace IDs
- Real-time alerting

**Usage:**
```python
from app.core.ai_logger import logger

logger.info("Task completed", {"task_id": "123"})
logger.error("Connection failed", exc_info=True)
```

### 3. Agno Embedding Service (`app/embeddings/agno_embedding_service.py`)
Unified embedding service with Portkey integration.

**Features:**
- 6 embedding models via Together AI
- Intelligent model selection
- In-memory caching
- Cost optimization

**Usage:**
```python
from app.embeddings.agno_embedding_service import AgnoEmbeddingService

service = AgnoEmbeddingService()
embeddings = await service.embed(["text to embed"])
```

## Removed Components

The following have been consolidated into SuperOrchestrator:
- ❌ simple_orchestrator.py
- ❌ orchestra_manager.py
- ❌ unified_enhanced_orchestrator.py
- ❌ All standalone manager files
- ❌ 14 Docker files (now 1 unified Dockerfile)

## Architecture Principles

1. **Single Responsibility:** One component for each major function
2. **Embedded Management:** Managers are embedded, not separate
3. **AI Enhancement:** AI monitoring and optimization throughout
4. **Clean Hierarchy:** Clear, simple component relationships
