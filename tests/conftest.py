"""
Pytest Configuration and Shared Fixtures for Sophia Intel AI
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from typing import Generator, AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fakeredis import FakeRedis

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api.unified_server import app
from app.core.config import settings
from app.memory.supermemory_mcp import SupermemoryStore
from app.memory.embedding_pipeline import StandardizedEmbeddingPipeline
from app.swarms.unified_enhanced_orchestrator import UnifiedSwarmOrchestrator

# ============================================
# Test Configuration
# ============================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_config():
    """Test configuration overrides."""
    return {
        "testing": True,
        "database_url": "sqlite:///:memory:",
        "redis_url": "redis://localhost:6379/15",
        "weaviate_url": "http://localhost:8080",
        "log_level": "DEBUG",
        "rate_limit_enabled": False,
        "metrics_enabled": False,
    }

@pytest.fixture(autouse=True)
def setup_test_env(test_config, monkeypatch):
    """Setup test environment variables."""
    for key, value in test_config.items():
        monkeypatch.setenv(key.upper(), str(value))

# ============================================
# Database Fixtures
# ============================================

@pytest.fixture
def db_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    # Create tables
    from app.models.database import Base
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Create database session."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def memory_store():
    """Create test memory store."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        store = SupermemoryStore(db_path=tmp.name)
        yield store

@pytest.fixture
def redis_client():
    """Create fake Redis client."""
    return FakeRedis(decode_responses=True)

# ============================================
# API Client Fixtures
# ============================================

@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async API client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def authenticated_client(api_client: AsyncClient) -> AsyncClient:
    """Create authenticated API client."""
    api_client.headers["X-API-Key"] = "test-api-key"
    return api_client

# ============================================
# Mock Fixtures
# ============================================

@pytest.fixture
def mock_llm():
    """Mock LLM client."""
    mock = AsyncMock()
    mock.complete = AsyncMock(return_value="Test response")
    mock.stream = AsyncMock()
    
    async def stream_generator():
        for chunk in ["Test", " response", " streaming"]:
            yield chunk
    
    mock.stream.return_value = stream_generator()
    return mock

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    mock = MagicMock()
    
    # Mock embeddings
    mock.embeddings.create = AsyncMock()
    mock.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536) for _ in range(10)]
    )
    
    # Mock completions
    mock.chat.completions.create = AsyncMock()
    mock.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test completion"))]
    )
    
    return mock

@pytest.fixture
def mock_weaviate_client():
    """Mock Weaviate client."""
    mock = MagicMock()
    
    # Mock schema
    mock.schema.get.return_value = {"classes": []}
    mock.schema.create_class.return_value = None
    
    # Mock data operations
    mock.data_object.create.return_value = "uuid-123"
    mock.query.get.return_value.with_near_vector.return_value.with_limit.return_value.do.return_value = {
        "data": {"Get": {"Memory": []}}
    }
    
    return mock

# ============================================
# Agent and Swarm Fixtures
# ============================================

@pytest.fixture
def mock_agent():
    """Create mock agent."""
    agent = Mock()
    agent.agent_id = "test_agent_001"
    agent.name = "Test Agent"
    agent.role = "test"
    agent.capabilities = ["testing", "mocking"]
    agent.process_task = AsyncMock(return_value="Agent result")
    return agent

@pytest.fixture
def mock_swarm():
    """Create mock swarm."""
    swarm = Mock()
    swarm.swarm_id = "test_swarm"
    swarm.name = "Test Swarm"
    swarm.agents = []
    swarm.execute = AsyncMock(return_value={"status": "success"})
    return swarm

@pytest.fixture
def orchestrator(mock_agent, mock_swarm):
    """Create orchestrator with mocked components."""
    orch = UnifiedSwarmOrchestrator()
    # Note: UnifiedSwarmOrchestrator may have different interface than SwarmOrchestrator
    # orch.register_agent(mock_agent)
    # orch.register_swarm(mock_swarm)
    return orch

# ============================================
# Embedding Fixtures
# ============================================

@pytest.fixture
def embedding_pipeline(mock_openai_client, monkeypatch):
    """Create embedding pipeline with mocked OpenAI."""
    monkeypatch.setattr(
        "app.memory.embedding_pipeline.AsyncOpenAI",
        lambda **kwargs: mock_openai_client
    )
    return StandardizedEmbeddingPipeline()

@pytest.fixture
def sample_embeddings():
    """Sample embedding vectors."""
    return {
        "small": [0.1] * 512,
        "medium": [0.2] * 1536,
        "large": [0.3] * 3072,
    }

# ============================================
# Sample Data Fixtures
# ============================================

@pytest.fixture
def sample_memory_entry():
    """Sample memory entry."""
    return {
        "topic": "Test Topic",
        "content": "This is test content for memory storage.",
        "memory_type": "semantic",
        "tags": ["test", "sample"],
        "metadata": {
            "source": "test",
            "timestamp": "2024-01-15T10:00:00Z"
        }
    }

@pytest.fixture
def sample_team_request():
    """Sample team execution request."""
    return {
        "request": "Analyze this test code",
        "team_id": "test_team",
        "stream": False,
        "context": {
            "file": "test.py",
            "language": "python"
        }
    }

@pytest.fixture
def sample_search_request():
    """Sample search request."""
    return {
        "query": "test query",
        "limit": 10,
        "filters": {
            "tags": ["test"],
            "memory_type": "semantic"
        }
    }

@pytest.fixture
def sample_code_files():
    """Sample code files for testing."""
    return [
        {
            "path": "test.py",
            "content": "def hello():\n    return 'world'",
            "language": "python"
        },
        {
            "path": "test.js",
            "content": "function hello() { return 'world'; }",
            "language": "javascript"
        },
        {
            "path": "test.md",
            "content": "# Test\n\nThis is a test document.",
            "language": "markdown"
        }
    ]

# ============================================
# File System Fixtures
# ============================================

@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def test_files(temp_dir, sample_code_files):
    """Create test files in temporary directory."""
    files = []
    for file_data in sample_code_files:
        file_path = temp_dir / file_data["path"]
        file_path.write_text(file_data["content"])
        files.append(file_path)
    return files

# ============================================
# Performance Testing Fixtures
# ============================================

@pytest.fixture
def benchmark_data():
    """Generate large dataset for benchmarking."""
    return {
        "texts": [f"Sample text {i}" * 100 for i in range(1000)],
        "embeddings": [[0.1] * 1536 for _ in range(1000)],
        "memories": [
            {
                "topic": f"Topic {i}",
                "content": f"Content {i}" * 50,
                "tags": [f"tag{j}" for j in range(5)]
            }
            for i in range(1000)
        ]
    }

# ============================================
# Cleanup Fixtures
# ============================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Clear any caches
    import gc
    gc.collect()

# ============================================
# Markers
# ============================================

# Register custom markers
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: mark test as requiring API keys"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark test as performance benchmark"
    )