"""
Pytest configuration and shared fixtures for SOPHIA Intel
"""

import asyncio
import pytest
import pytest_asyncio
from typing import Dict, Any, AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import os
from pathlib import Path

# Test configuration
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Mock configuration for testing"""
    return {
        "environment": "test",
        "debug": True,
        "database": {
            "url": "sqlite:///:memory:",
            "echo": False
        },
        "redis": {
            "url": "redis://localhost:6379/1",
            "decode_responses": True
        },
        "openrouter": {
            "api_key": "test_openrouter_key",
            "base_url": "https://openrouter.ai/api/v1"
        },
        "lambda_labs": {
            "api_key": "test_lambda_key",
            "servers": [
                {
                    "name": "test-primary",
                    "url": "http://localhost:8000",
                    "health_endpoint": "/health"
                }
            ]
        },
        "sentry": {
            "dsn": "https://test@sentry.io/test",
            "traces_sample_rate": 0.0,
            "profiles_sample_rate": 0.0
        },
        "monitoring": {
            "enabled": False
        },
        "alerting": {
            "enabled": False
        }
    }

@pytest.fixture
def mock_lambda_labs_client():
    """Mock Lambda Labs client"""
    client = AsyncMock()
    client.list_instances.return_value = {
        "data": [
            {
                "id": "test-instance-1",
                "name": "test-primary",
                "status": "active",
                "ip": "192.168.1.100"
            }
        ]
    }
    client.get_instance.return_value = {
        "id": "test-instance-1",
        "name": "test-primary",
        "status": "active",
        "ip": "192.168.1.100"
    }
    client.start_instance.return_value = {"success": True}
    client.stop_instance.return_value = {"success": True}
    client.restart_instance.return_value = {"success": True}
    return client

@pytest.fixture
def mock_openrouter_client():
    """Mock OpenRouter client"""
    client = AsyncMock()
    client.chat_completion.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Test response from OpenRouter"
                }
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }
    return client

@pytest.fixture
def mock_memory_client():
    """Mock memory client"""
    client = AsyncMock()
    client.store_message.return_value = {"success": True, "id": "test-message-id"}
    client.get_conversation_history.return_value = [
        {
            "role": "user",
            "content": "Test user message",
            "timestamp": 1234567890
        },
        {
            "role": "assistant", 
            "content": "Test assistant response",
            "timestamp": 1234567891
        }
    ]
    client.get_session_summary.return_value = {
        "summary": "Test conversation summary",
        "message_count": 2,
        "duration": 300
    }
    return client

@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    client = AsyncMock()
    client.search.return_value = [
        {
            "id": "test-vector-1",
            "score": 0.95,
            "payload": {"text": "Test vector result"}
        }
    ]
    client.upsert.return_value = {"operation_id": "test-op-1", "status": "completed"}
    return client

@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = AsyncMock()
    client.get.return_value = '{"test": "data"}'
    client.set.return_value = True
    client.delete.return_value = 1
    client.exists.return_value = True
    return client

@pytest.fixture
async def mock_database_session():
    """Mock database session"""
    session = AsyncMock()
    session.execute.return_value = Mock()
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    return session

@pytest.fixture
def mock_tracing_system():
    """Mock distributed tracing system"""
    tracing = Mock()
    tracing.start_span.return_value = "test-span-id"
    tracing.finish_span.return_value = None
    tracing.add_span_tag.return_value = None
    tracing.add_span_log.return_value = None
    return tracing

@pytest.fixture
def mock_alerting_system():
    """Mock alerting system"""
    alerting = AsyncMock()
    alerting.evaluate_alert_rules.return_value = []
    alerting.get_active_alerts.return_value = []
    alerting.acknowledge_alert.return_value = True
    alerting.resolve_alert.return_value = True
    return alerting

@pytest.fixture
def mock_circuit_breaker():
    """Mock circuit breaker"""
    breaker = AsyncMock()
    breaker.call.side_effect = lambda func: func()
    breaker.is_open = False
    breaker.failure_count = 0
    return breaker

@pytest.fixture
def temp_directory():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing"""
    return {
        "message": "Hello, SOPHIA!",
        "session_id": "test-session-123",
        "user_id": "test-user-456",
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 1000,
        "web_access": True,
        "deep_research": False,
        "use_swarm": False,
        "voice_enabled": False,
        "persona": "professional"
    }

@pytest.fixture
def sample_metrics():
    """Sample metrics for testing"""
    return {
        "avg_response_time": 0.5,
        "error_rate": 0.02,
        "lambda_server_health": True,
        "database_health": True,
        "memory_usage": 0.65,
        "disk_usage": 0.45,
        "ai_inference_success_rate": 0.98,
        "model_load_failures": 0,
        "auth_failure_rate": 0.01,
        "suspicious_requests": 5
    }

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for external API calls"""
    client = AsyncMock()
    client.get.return_value = Mock(status=200, json=AsyncMock(return_value={"status": "ok"}))
    client.post.return_value = Mock(status=200, json=AsyncMock(return_value={"success": True}))
    client.put.return_value = Mock(status=200, json=AsyncMock(return_value={"updated": True}))
    client.delete.return_value = Mock(status=204)
    return client

@pytest.fixture
def mock_file_system(temp_directory):
    """Mock file system operations"""
    # Create some test files
    test_file = temp_directory / "test_file.txt"
    test_file.write_text("Test file content")
    
    config_file = temp_directory / "config.json"
    config_file.write_text('{"test": "config"}')
    
    return {
        "temp_dir": temp_directory,
        "test_file": test_file,
        "config_file": config_file
    }

# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.performance = pytest.mark.performance
pytest.mark.security = pytest.mark.security

# Async test helpers
@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client for testing"""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        yield session

# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables"""
    test_env = {
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/1",
        "OPENROUTER_API_KEY": "test_openrouter_key",
        "LAMBDA_API_KEY": "test_lambda_key",
        "SENTRY_DSN": "https://test@sentry.io/test",
        "MCP_AUTH_TOKEN": "test_mcp_token"
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

# Database fixtures
@pytest_asyncio.fixture
async def test_database():
    """Test database setup"""
    # This would set up a test database
    # For now, we'll use SQLite in-memory
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables (would import actual models)
    # await create_tables(engine)
    
    yield async_session
    
    await engine.dispose()

# Performance testing fixtures
@pytest.fixture
def performance_thresholds():
    """Performance test thresholds"""
    return {
        "response_time_max": 2.0,  # seconds
        "memory_usage_max": 100,   # MB
        "cpu_usage_max": 80,       # percentage
        "concurrent_requests": 50,
        "requests_per_second": 100
    }

# Security testing fixtures
@pytest.fixture
def security_test_payloads():
    """Security test payloads"""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ],
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`"
        ]
    }

# Load testing fixtures
@pytest.fixture
def load_test_scenarios():
    """Load testing scenarios"""
    return {
        "light_load": {
            "concurrent_users": 10,
            "duration": 60,
            "ramp_up": 10
        },
        "normal_load": {
            "concurrent_users": 50,
            "duration": 300,
            "ramp_up": 30
        },
        "heavy_load": {
            "concurrent_users": 100,
            "duration": 600,
            "ramp_up": 60
        },
        "stress_test": {
            "concurrent_users": 200,
            "duration": 300,
            "ramp_up": 30
        }
    }

# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Cleanup code here
    # Clear caches, reset mocks, etc.
    pass

