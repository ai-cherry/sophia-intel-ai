"""
Test Fixtures and Mocks for AI Orchestra Testing
Provides reusable test fixtures and mock objects
"""

import pytest
import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
import json

from app.api.contracts import (
    ChatRequestV2, ChatResponseV2,
    WebSocketMessage, WebSocketMessageType
)

# ==================== Mock Data Factories ====================

class MockDataFactory:
    """Factory for creating mock test data"""
    
    @staticmethod
    def create_chat_request(**kwargs) -> ChatRequestV2:
        """Create mock chat request"""
        defaults = {
            "message": "Test message",
            "session_id": "test-session",
            "optimization_mode": "balanced",
            "swarm_type": None,
            "use_memory": False,
            "user_context": {}
        }
        defaults.update(kwargs)
        return ChatRequestV2(**defaults)
    
    @staticmethod
    def create_chat_response(**kwargs) -> ChatResponseV2:
        """Create mock chat response"""
        defaults = {
            "response": "Test response",
            "session_id": "test-session",
            "success": True,
            "metadata": {
                "processing_time": 0.1,
                "tokens_used": 10,
                "model": "test-model"
            },
            "execution_mode": "balanced",
            "quality_score": 0.85,
            "execution_time": 0.1,
            "error": None
        }
        defaults.update(kwargs)
        return ChatResponseV2(**defaults)
    
    @staticmethod
    def create_websocket_message(**kwargs) -> Dict[str, Any]:
        """Create mock WebSocket message"""
        defaults = {
            "type": "chat",
            "data": {
                "message": "Test WebSocket message",
                "context": {}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_manager_result(**kwargs) -> Dict[str, Any]:
        """Create mock manager result"""
        defaults = {
            "intent": "general",
            "parameters": {},
            "confidence": 0.9,
            "response": "Manager response"
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_command_result(**kwargs) -> Mock:
        """Create mock command dispatcher result"""
        mock = Mock()
        mock.success = kwargs.get("success", True)
        mock.response = kwargs.get("response", "Command executed")
        mock.execution_mode = Mock(value=kwargs.get("execution_mode", "balanced"))
        mock.quality_score = kwargs.get("quality_score", 0.85)
        mock.execution_time = kwargs.get("execution_time", 0.1)
        mock.error = kwargs.get("error", None)
        mock.metadata = kwargs.get("metadata", {})
        return mock

# ==================== Component Mocks ====================

class MockOrchestrator:
    """Mock ChatOrchestrator for testing"""
    
    def __init__(self):
        self.initialized = True
        self.handle_chat = AsyncMock(return_value=MockDataFactory.create_chat_response())
        self.websocket_endpoint = AsyncMock()
        self.get_metrics = AsyncMock(return_value={
            "active_connections": 0,
            "total_requests": 0,
            "average_response_time": 0.0
        })
        self.circuit_breakers = {}
        self.active_connections = {}
        self.session_history = {}
        self.shutdown = AsyncMock()
        self.initialize = AsyncMock()

class MockCommandDispatcher:
    """Mock CommandDispatcher for testing"""
    
    def __init__(self):
        self.process_command = AsyncMock(
            return_value=MockDataFactory.create_command_result()
        )
        self.get_available_commands = Mock(return_value=[
            "analyze", "generate", "optimize"
        ])

class MockOrchestraManager:
    """Mock Orchestra Manager for testing"""
    
    def __init__(self):
        self.process_message = Mock(
            return_value=MockDataFactory.create_manager_result()
        )
        self.process_result = Mock(return_value="Processed")
        self.get_status = Mock(return_value={"status": "healthy"})

class MockWebSocket:
    """Mock WebSocket connection for testing"""
    
    def __init__(self):
        self.send_json = AsyncMock()
        self.send_text = AsyncMock()
        self.receive_json = AsyncMock(
            return_value=MockDataFactory.create_websocket_message()
        )
        self.close = AsyncMock()
        self.accept = AsyncMock()
        self.client_state = {"connected": True}

class MockCircuitBreaker:
    """Mock Circuit Breaker for testing"""
    
    def __init__(self, name: str):
        self.name = name
        self.state = "CLOSED"
        self.call = AsyncMock(side_effect=self._call)
        self.failure_count = 0
        self.success_count = 0
    
    async def _call(self, func):
        if self.state == "OPEN":
            raise Exception("Circuit breaker is open")
        try:
            result = await func()
            self.success_count += 1
            return result
        except Exception as e:
            self.failure_count += 1
            raise

# ==================== Test Fixtures ====================

@pytest.fixture
def mock_orchestrator():
    """Provide mock orchestrator"""
    return MockOrchestrator()

@pytest.fixture
def mock_command_dispatcher():
    """Provide mock command dispatcher"""
    return MockCommandDispatcher()

@pytest.fixture
def mock_orchestra_manager():
    """Provide mock orchestra manager"""
    return MockOrchestraManager()

@pytest.fixture
def mock_websocket():
    """Provide mock WebSocket connection"""
    return MockWebSocket()

@pytest.fixture
def mock_circuit_breaker():
    """Provide mock circuit breaker"""
    return MockCircuitBreaker("test")

@pytest.fixture
def chat_request():
    """Provide sample chat request"""
    return MockDataFactory.create_chat_request()

@pytest.fixture
def chat_response():
    """Provide sample chat response"""
    return MockDataFactory.create_chat_response()

@pytest.fixture
def websocket_message():
    """Provide sample WebSocket message"""
    return MockDataFactory.create_websocket_message()

# ==================== Async Test Helpers ====================

class AsyncTestHelper:
    """Helper utilities for async testing"""
    
    @staticmethod
    async def run_with_timeout(coro, timeout: float = 1.0):
        """Run coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            pytest.fail(f"Async operation timed out after {timeout} seconds")
    
    @staticmethod
    async def wait_for_condition(
        condition_func,
        timeout: float = 1.0,
        interval: float = 0.1
    ):
        """Wait for condition to become true"""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if await condition_func():
                return True
            await asyncio.sleep(interval)
        return False
    
    @staticmethod
    def create_async_mock_with_delay(
        return_value: Any,
        delay: float = 0.1
    ) -> AsyncMock:
        """Create async mock that simulates processing delay"""
        async def delayed_return(*args, **kwargs):
            await asyncio.sleep(delay)
            return return_value
        
        return AsyncMock(side_effect=delayed_return)

# ==================== Database Mocks ====================

class MockDatabase:
    """Mock database for testing"""
    
    def __init__(self):
        self.data = {}
        self.connect = AsyncMock()
        self.disconnect = AsyncMock()
        self.execute = AsyncMock(side_effect=self._execute)
        self.fetch_one = AsyncMock(side_effect=self._fetch_one)
        self.fetch_all = AsyncMock(side_effect=self._fetch_all)
    
    async def _execute(self, query: str, params: Dict = None):
        """Mock query execution"""
        return {"affected_rows": 1}
    
    async def _fetch_one(self, query: str, params: Dict = None):
        """Mock fetching single row"""
        return {"id": 1, "data": "test"}
    
    async def _fetch_all(self, query: str, params: Dict = None):
        """Mock fetching multiple rows"""
        return [
            {"id": 1, "data": "test1"},
            {"id": 2, "data": "test2"}
        ]

# ==================== External Service Mocks ====================

class MockExternalService:
    """Mock external service for testing"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.available = True
        self.response_delay = 0.1
        self.failure_rate = 0.0
        self.call_count = 0
    
    async def call(self, endpoint: str, data: Dict = None):
        """Mock service call"""
        self.call_count += 1
        
        # Simulate failure rate
        import random
        if random.random() < self.failure_rate:
            raise Exception(f"{self.service_name} service failed")
        
        # Simulate processing delay
        await asyncio.sleep(self.response_delay)
        
        if not self.available:
            raise Exception(f"{self.service_name} service unavailable")
        
        return {
            "status": "success",
            "data": f"Response from {self.service_name}",
            "timestamp": datetime.utcnow().isoformat()
        }

# ==================== Event Mocks ====================

class MockEventBus:
    """Mock event bus for testing"""
    
    def __init__(self):
        self.events = []
        self.subscribers = {}
    
    async def publish(self, event_type: str, data: Any):
        """Publish event"""
        self.events.append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow()
        })
        
        # Notify subscribers
        if event_type in self.subscribers:
            for subscriber in self.subscribers[event_type]:
                await subscriber(data)
    
    def subscribe(self, event_type: str, handler):
        """Subscribe to event"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    def get_events(self, event_type: str = None) -> List[Dict]:
        """Get published events"""
        if event_type:
            return [e for e in self.events if e["type"] == event_type]
        return self.events

# ==================== Performance Test Helpers ====================

class PerformanceTestHelper:
    """Helper for performance testing"""
    
    @staticmethod
    def measure_time(func):
        """Decorator to measure function execution time"""
        import time
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            duration = time.perf_counter() - start
            return result, duration
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start
            return result, duration
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    @staticmethod
    async def simulate_load(
        func,
        concurrent_requests: int = 10,
        duration_seconds: float = 1.0
    ):
        """Simulate load on a function"""
        import time
        
        results = []
        errors = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            tasks = []
            for _ in range(concurrent_requests):
                tasks.append(func())
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    errors.append(result)
                else:
                    results.append(result)
        
        return {
            "total_requests": len(results) + len(errors),
            "successful": len(results),
            "failed": len(errors),
            "success_rate": len(results) / (len(results) + len(errors)) if results or errors else 0,
            "duration": time.time() - start_time
        }

# ==================== Test Data Generators ====================

class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def generate_chat_messages(count: int = 10) -> List[str]:
        """Generate sample chat messages"""
        templates = [
            "What is {}?",
            "How do I {}?",
            "Can you explain {}?",
            "Show me an example of {}",
            "Help me with {}"
        ]
        topics = [
            "Python", "JavaScript", "machine learning",
            "web development", "databases", "APIs",
            "testing", "deployment", "debugging"
        ]
        
        import random
        messages = []
        for _ in range(count):
            template = random.choice(templates)
            topic = random.choice(topics)
            messages.append(template.format(topic))
        
        return messages
    
    @staticmethod
    def generate_session_ids(count: int = 5) -> List[str]:
        """Generate unique session IDs"""
        import uuid
        return [f"session-{uuid.uuid4().hex[:8]}" for _ in range(count)]
    
    @staticmethod
    def generate_user_contexts(count: int = 5) -> List[Dict]:
        """Generate user context objects"""
        contexts = []
        for i in range(count):
            contexts.append({
                "user_id": f"user-{i}",
                "preferences": {
                    "language": "python" if i % 2 == 0 else "javascript",
                    "expertise": "beginner" if i % 3 == 0 else "advanced"
                },
                "history_length": i * 10
            })
        return contexts

# ==================== Export All Fixtures ====================

__all__ = [
    "MockDataFactory",
    "MockOrchestrator",
    "MockCommandDispatcher",
    "MockOrchestraManager",
    "MockWebSocket",
    "MockCircuitBreaker",
    "MockDatabase",
    "MockExternalService",
    "MockEventBus",
    "AsyncTestHelper",
    "PerformanceTestHelper",
    "TestDataGenerator",
    "mock_orchestrator",
    "mock_command_dispatcher",
    "mock_orchestra_manager",
    "mock_websocket",
    "mock_circuit_breaker",
    "chat_request",
    "chat_response",
    "websocket_message"
]