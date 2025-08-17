"""
Unit tests for Enhanced Memory Client
Tests context management, summarization, and cross-backend memory sharing
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from libs.mcp_client.enhanced_memory_client import (
    EnhancedMemoryClient, 
    ContextWindow, 
    SessionManager
)


class TestContextWindow:
    """Test cases for ContextWindow"""
    
    @pytest.fixture
    def context_window(self):
        """Create ContextWindow instance"""
        return ContextWindow(max_tokens=1000, summary_threshold=800)
    
    def test_token_estimation(self, context_window):
        """Test token estimation from text"""
        text = "This is a test message with some content"
        tokens = context_window.estimate_tokens(text)
        
        assert tokens > 0
        assert tokens == len(text) // context_window.token_estimate_ratio
    
    def test_needs_summarization(self, context_window):
        """Test summarization threshold detection"""
        # Small context - no summarization needed
        small_context = [
            {"content": "Short message", "metadata": {}}
        ]
        assert not context_window.needs_summarization(small_context)
        
        # Large context - summarization needed
        large_context = [
            {"content": "Very long message " * 100, "metadata": {}}
            for _ in range(10)
        ]
        assert context_window.needs_summarization(large_context)
    
    def test_truncate_context(self, context_window):
        """Test context truncation"""
        # Create context that exceeds max tokens
        large_context = []
        for i in range(20):
            large_context.append({
                "content": f"Message {i} with some content " * 20,
                "metadata": {
                    "timestamp": 1000000 + i,
                    "role": "user" if i % 2 == 0 else "assistant"
                }
            })
        
        truncated = context_window.truncate_context(large_context)
        
        # Should be smaller than original
        assert len(truncated) < len(large_context)
        
        # Should fit within token limit
        total_tokens = sum(
            context_window.estimate_tokens(item.get("content", ""))
            for item in truncated
        )
        assert total_tokens <= context_window.max_tokens
    
    def test_importance_calculation(self, context_window):
        """Test importance scoring for context items"""
        items = [
            {
                "content": "User question",
                "metadata": {"role": "user", "timestamp": 2000000}
            },
            {
                "content": "Assistant response",
                "metadata": {"role": "assistant", "timestamp": 1900000}
            },
            {
                "content": "System message",
                "metadata": {"role": "system", "timestamp": 1800000}
            },
            {
                "content": "Research context",
                "metadata": {"role": "system", "type": "research_context", "timestamp": 1700000}
            }
        ]
        
        # Calculate importance scores
        for item in items:
            score = context_window._calculate_importance(item)
            assert score >= 0.0
        
        # User messages should have high importance
        user_score = context_window._calculate_importance(items[0])
        assistant_score = context_window._calculate_importance(items[1])
        assert user_score > assistant_score


class TestSessionManager:
    """Test cases for SessionManager"""
    
    @pytest.fixture
    def session_manager(self):
        """Create SessionManager with mocked memory client"""
        mock_memory_client = AsyncMock()
        return SessionManager(mock_memory_client)
    
    @pytest.mark.asyncio
    async def test_get_session_context(self, session_manager):
        """Test session context retrieval"""
        session_id = "test_session_123"
        
        # Mock memory client responses
        session_manager.memory_client.query.return_value = [
            {
                "content": "Test message 1",
                "metadata": {"role": "user", "timestamp": 1000000}
            },
            {
                "content": "Test response 1",
                "metadata": {"role": "assistant", "timestamp": 1000001}
            }
        ]
        
        session_manager.memory_client.get_session_stats.return_value = {
            "message_count": 2,
            "last_activity": "2024-01-01T12:00:00Z"
        }
        
        context = await session_manager.get_session_context(session_id)
        
        assert context["session_id"] == session_id
        assert len(context["recent_messages"]) == 2
        assert context["context_ready"] == True
        assert context["total_messages"] == 2
    
    @pytest.mark.asyncio
    async def test_create_session_summary(self, session_manager):
        """Test session summary creation"""
        session_id = "test_session_123"
        
        # Mock messages for summarization
        mock_messages = [
            {
                "content": "How do I create a web application?",
                "metadata": {"role": "user", "backend_used": "orchestrator"}
            },
            {
                "content": "I'll help you create a web application using React and Node.js...",
                "metadata": {"role": "assistant", "backend_used": "orchestrator"}
            },
            {
                "content": "Can you also add authentication?",
                "metadata": {"role": "user", "backend_used": "orchestrator"}
            },
            {
                "content": "Certainly! I'll add JWT authentication...",
                "metadata": {"role": "assistant", "backend_used": "orchestrator"}
            }
        ]
        
        session_manager.memory_client.query.return_value = mock_messages
        
        summary_result = await session_manager.create_session_summary(session_id)
        
        assert summary_result["session_id"] == session_id
        assert len(summary_result["summary"]) > 0
        assert "analysis" in summary_result
        assert summary_result["analysis"]["total_messages"] == 4
        assert "orchestrator" in summary_result["analysis"]["backend_usage"]
    
    def test_analyze_conversation_patterns(self, session_manager):
        """Test conversation pattern analysis"""
        messages = [
            {
                "content": "web development question",
                "metadata": {"role": "user", "backend_used": "orchestrator"}
            },
            {
                "content": "web development response with react",
                "metadata": {"role": "assistant", "backend_used": "orchestrator"}
            },
            {
                "content": "error occurred during processing",
                "metadata": {"role": "system", "error": True}
            }
        ]
        
        analysis = session_manager._analyze_conversation_patterns(messages)
        
        assert analysis["total_messages"] == 3
        assert analysis["user_messages"] == 1
        assert analysis["assistant_messages"] == 1
        assert analysis["error_count"] == 1
        assert "orchestrator" in analysis["backend_usage"]
        assert "web" in analysis["key_topics"]


class TestEnhancedMemoryClient:
    """Test cases for EnhancedMemoryClient"""
    
    @pytest.fixture
    def memory_client(self):
        """Create EnhancedMemoryClient with mocked dependencies"""
        with patch('libs.mcp_client.enhanced_memory_client.MCPMemoryClient.__init__'):
            client = EnhancedMemoryClient()
            client.store = AsyncMock()
            client.query = AsyncMock()
            client.get_session_stats = AsyncMock()
            return client
    
    @pytest.mark.asyncio
    async def test_store_with_context(self, memory_client):
        """Test enhanced context storage"""
        session_id = "test_session"
        content = "Test message content"
        backend_used = "orchestrator"
        
        memory_client.store.return_value = {"id": "msg_123", "status": "stored"}
        
        result = await memory_client.store_with_context(
            session_id=session_id,
            content=content,
            backend_used=backend_used,
            auto_summarize=False  # Disable for test
        )
        
        # Verify store was called with enhanced metadata
        memory_client.store.assert_called_once()
        call_args = memory_client.store.call_args
        
        assert call_args[1]["session_id"] == session_id
        assert call_args[1]["content"] == content
        assert call_args[1]["backend_used"] == backend_used
        assert "timestamp" in call_args[1]["metadata"]
        assert call_args[1]["metadata"]["backend_used"] == backend_used
    
    @pytest.mark.asyncio
    async def test_get_optimized_context(self, memory_client):
        """Test optimized context retrieval"""
        session_id = "test_session"
        
        # Mock session context
        memory_client.session_manager = AsyncMock()
        memory_client.session_manager.get_session_context.return_value = {
            "recent_messages": [
                {
                    "content": "Short message",
                    "metadata": {"role": "user"}
                }
            ],
            "session_summary": None
        }
        
        memory_client.query.return_value = []
        
        result = await memory_client.get_optimized_context(session_id)
        
        assert result["session_id"] == session_id
        assert "context" in result
        assert "estimated_tokens" in result
        assert result["context_ready"] == True
    
    @pytest.mark.asyncio
    async def test_cross_backend_search(self, memory_client):
        """Test cross-backend search functionality"""
        session_id = "test_session"
        query = "web development"
        
        # Mock messages from different backends
        mock_messages = [
            {
                "content": "web development with React",
                "metadata": {"backend_used": "orchestrator"}
            },
            {
                "content": "comprehensive web development architecture",
                "metadata": {"backend_used": "swarm"}
            },
            {
                "content": "web development research results",
                "metadata": {"backend_used": "web_research"}
            }
        ]
        
        memory_client.query.return_value = mock_messages
        
        result = await memory_client.cross_backend_search(session_id, query)
        
        assert result["session_id"] == session_id
        assert result["query"] == query
        assert result["total_results"] > 0
        assert "backend_results" in result
        
        # Should have results from different backends
        backend_results = result["backend_results"]
        assert len(backend_results) > 0
    
    @pytest.mark.asyncio
    async def test_auto_summarization_check(self, memory_client):
        """Test automatic summarization trigger"""
        session_id = "test_session"
        
        # Mock high message count to trigger summarization
        memory_client.get_session_stats.return_value = {
            "message_count": 150  # Above threshold
        }
        
        memory_client.session_manager = AsyncMock()
        memory_client.session_manager.session_summaries = {}
        memory_client.session_manager.create_session_summary = AsyncMock()
        
        await memory_client._check_auto_summarize(session_id)
        
        # Should trigger summarization
        memory_client.session_manager.create_session_summary.assert_called_once_with(session_id)
    
    @pytest.mark.asyncio
    async def test_cleanup_old_sessions(self, memory_client):
        """Test old session cleanup"""
        # Mock session summaries with old data
        old_date = (datetime.now() - timedelta(days=35)).isoformat()
        recent_date = datetime.now().isoformat()
        
        memory_client.session_manager = Mock()
        memory_client.session_manager.session_summaries = {
            "old_session": {"created_at": old_date},
            "recent_session": {"created_at": recent_date}
        }
        
        result = await memory_client.cleanup_old_sessions(days=30)
        
        assert result["cleaned_sessions"] == 1
        assert "old_session" not in memory_client.session_manager.session_summaries
        assert "recent_session" in memory_client.session_manager.session_summaries
    
    @pytest.mark.asyncio
    async def test_health_check_enhanced(self, memory_client):
        """Test enhanced health check"""
        # Mock base health check
        with patch.object(memory_client, 'health_check') as mock_health:
            mock_health.return_value = {"status": "healthy"}
            
            memory_client.context_cache = {"test": "data"}
            memory_client.session_manager = Mock()
            memory_client.session_manager.session_summaries = {"session1": {}}
            memory_client.session_manager.active_sessions = {"session1": {}}
            
            result = await memory_client.health_check_enhanced()
            
            assert result["status"] == "healthy"
            assert result["context_cache_size"] == 1
            assert result["session_summaries"] == 1
            assert result["active_sessions"] == 1
            assert "features" in result
            assert result["features"]["cross_backend_search"] == True


@pytest.mark.asyncio
class TestEnhancedMemoryClientIntegration:
    """Integration tests for EnhancedMemoryClient"""
    
    @pytest.fixture
    def memory_client(self):
        """Create memory client with minimal mocking"""
        client = EnhancedMemoryClient()
        # Only mock the actual MCP server calls
        client._make_request = AsyncMock()
        return client
    
    async def test_full_context_optimization_flow(self, memory_client):
        """Test complete context optimization workflow"""
        session_id = "integration_test_session"
        
        # Mock MCP server responses
        memory_client._make_request.side_effect = [
            # get_session_stats response
            {"message_count": 75, "last_activity": "2024-01-01T12:00:00Z"},
            # query response for recent messages
            {
                "results": [
                    {
                        "content": f"Message {i} content",
                        "metadata": {
                            "role": "user" if i % 2 == 0 else "assistant",
                            "timestamp": 1000000 + i,
                            "backend_used": "orchestrator"
                        }
                    }
                    for i in range(50)
                ]
            }
        ]
        
        result = await memory_client.get_optimized_context(session_id)
        
        assert result["session_id"] == session_id
        assert len(result["context"]) > 0
        assert result["estimated_tokens"] > 0
        assert result["context_ready"] == True
    
    async def test_cross_backend_memory_sharing(self, memory_client):
        """Test memory sharing across different backends"""
        session_id = "cross_backend_test"
        
        # Store messages from different backends
        backends = ["orchestrator", "swarm", "web_research"]
        
        for i, backend in enumerate(backends):
            memory_client._make_request.return_value = {"id": f"msg_{i}", "status": "stored"}
            
            await memory_client.store_with_context(
                session_id=session_id,
                content=f"Message from {backend}",
                backend_used=backend
            )
        
        # Mock cross-backend search
        memory_client._make_request.return_value = {
            "results": [
                {
                    "content": f"Message from {backend}",
                    "metadata": {"backend_used": backend}
                }
                for backend in backends
            ]
        }
        
        search_result = await memory_client.cross_backend_search(
            session_id, "test query"
        )
        
        assert len(search_result["backend_results"]) == len(backends)
        for backend in backends:
            assert backend in search_result["backend_results"]

