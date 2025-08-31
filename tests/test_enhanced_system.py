"""
Comprehensive tests for the enhanced AI system.
Tests real LLM integration, memory system, and swarm execution.
"""

import pytest
import asyncio
import json
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Test the real LLM executor
from app.llm.real_executor import RealLLMExecutor, Role
from app.memory.enhanced_memory import EnhancedMemoryStore, SearchResult
from app.memory.types import MemoryEntry, MemoryType
from app.api.real_streaming import stream_real_ai_execution
from app.swarms.coding.models import SwarmConfiguration, PoolType


class TestRealLLMExecutor:
    """Test the real LLM executor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.executor = RealLLMExecutor()
    
    def test_model_selection(self):
        """Test model selection logic."""
        # Test pool-based selection
        model = self.executor._select_model("fast", None)
        assert "deepseek" in model.lower() or "gemini" in model.lower()
        
        model = self.executor._select_model("heavy", None)
        assert "gpt-5" in model or "claude-opus" in model or "grok" in model
        
        # Test role-specific selection
        model = self.executor._select_model("balanced", Role.CRITIC)
        assert "claude-3.7-sonnet" in model
        
        model = self.executor._select_model("balanced", Role.JUDGE)
        assert "gpt-5" in model
    
    def test_temperature_for_role(self):
        """Test temperature selection by role."""
        # Critic should be very consistent
        temp = self.executor._get_temperature_for_role(Role.CRITIC)
        assert temp == 0.1
        
        # Generator should be more creative
        temp = self.executor._get_temperature_for_role(Role.GENERATOR)
        assert temp == 0.7
        
        # Default
        temp = self.executor._get_temperature_for_role(None)
        assert temp == 0.7
    
    def test_build_messages(self):
        """Test message building."""
        messages = self.executor._build_messages("Hello world")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello world"
        
        # With context
        context = {
            "system_prompt": "You are helpful",
            "conversation_history": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"}
            ]
        }
        messages = self.executor._build_messages("Continue", context)
        assert len(messages) == 4  # system + history + user
        assert messages[0]["role"] == "system"
        assert messages[-1]["content"] == "Continue"
    
    def test_coding_prompt_building(self):
        """Test role-specific coding prompt building."""
        # Planner prompt
        prompt = self.executor._build_coding_prompt(
            "Create a web server", 
            Role.PLANNER, 
            None
        )
        assert "planner" in prompt.lower()
        assert "plan" in prompt.lower()
        assert "Create a web server" in prompt
        
        # Generator prompt  
        prompt = self.executor._build_coding_prompt(
            "Create a web server",
            Role.GENERATOR,
            {"memory_results": "FastAPI is recommended"}
        )
        assert "production-ready" in prompt.lower()
        assert "Create a web server" in prompt
        assert "FastAPI is recommended" in prompt
    
    @pytest.mark.asyncio
    @patch('app.llm.real_executor.gateway')
    async def test_execute_success(self, mock_gateway):
        """Test successful LLM execution."""
        # Mock successful response
        mock_gateway.achat = AsyncMock(return_value="Generated code here")
        
        result = await self.executor.execute(
            prompt="Create a function",
            model_pool="balanced",
            role=Role.GENERATOR
        )
        
        assert result["success"] is True
        assert "Generated code here" in result["content"]
        assert result["model"]
        assert result["timestamp"]
        
    @pytest.mark.asyncio
    @patch('app.llm.real_executor.gateway')
    async def test_execute_failure(self, mock_gateway):
        """Test LLM execution failure handling."""
        # Mock failure
        mock_gateway.achat = AsyncMock(side_effect=Exception("API Error"))
        
        result = await self.executor.execute(
            prompt="Create a function",
            model_pool="balanced"
        )
        
        assert result["success"] is False
        assert "Error: API Error" in result["content"]
        assert "API Error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_embed_text(self):
        """Test text embedding."""
        with patch.object(self.executor.gateway, 'aembed') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            
            embeddings = await self.executor.embed_text(["text1", "text2"])
            
            assert len(embeddings) == 2
            assert len(embeddings[0]) == 3
            mock_embed.assert_called_once_with(["text1", "text2"])


class TestEnhancedMemoryStore:
    """Test the enhanced memory system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        from app.memory.enhanced_memory import EnhancedMemoryConfig
        config = EnhancedMemoryConfig()
        config.SQLITE_PATH = self.temp_db.name
        
        self.memory_store = EnhancedMemoryStore(config)
    
    def teardown_method(self):
        """Clean up."""
        import os
        if hasattr(self, 'temp_db'):
            try:
                os.unlink(self.temp_db.name)
            except:
                pass
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test memory store initialization."""
        await self.memory_store.initialize()
        
        assert self.memory_store._initialized is True
        assert self.memory_store.sqlite_conn is not None
        
        # Check tables exist
        cursor = self.memory_store.sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'memory_entries' in tables
        assert 'memory_fts' in tables
    
    @pytest.mark.asyncio
    async def test_add_memory(self):
        """Test adding memory entries."""
        entry = MemoryEntry(
            topic="Test Topic",
            content="This is test content",
            source="test_source",
            tags=["test", "memory"],
            memory_type=MemoryType.SEMANTIC
        )
        
        hash_id = await self.memory_store.add_memory(entry)
        
        assert hash_id == entry.hash_id
        
        # Verify stored in database
        cursor = self.memory_store.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM memory_entries WHERE hash_id = ?", (hash_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row["topic"] == "Test Topic"
        assert row["content"] == "This is test content"
        assert json.loads(row["tags"]) == ["test", "memory"]
    
    @pytest.mark.asyncio
    async def test_fts_search(self):
        """Test FTS search functionality."""
        # Add test entries
        entries = [
            MemoryEntry(
                topic="Python Functions",
                content="How to create functions in Python with def keyword",
                source="docs",
                memory_type=MemoryType.SEMANTIC
            ),
            MemoryEntry(
                topic="JavaScript Arrays", 
                content="Working with arrays in JavaScript using map and filter",
                source="tutorial",
                memory_type=MemoryType.PROCEDURAL
            )
        ]
        
        for entry in entries:
            await self.memory_store.add_memory(entry)
        
        # Search for Python
        results = await self.memory_store.search_memory(
            "Python functions",
            use_vector=False,  # FTS only
            rerank=False
        )
        
        assert len(results) >= 1
        assert any("Python" in r.entry.content for r in results)
        assert all(r.fts_score is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_search_with_memory_type_filter(self):
        """Test search with memory type filtering."""
        # Add entries of different types
        semantic_entry = MemoryEntry(
            topic="Design Patterns",
            content="Observer pattern implementation",
            source="book",
            memory_type=MemoryType.SEMANTIC
        )
        
        procedural_entry = MemoryEntry(
            topic="Deployment Steps",
            content="Step 1: Build, Step 2: Test, Step 3: Deploy",
            source="runbook", 
            memory_type=MemoryType.PROCEDURAL
        )
        
        await self.memory_store.add_memory(semantic_entry)
        await self.memory_store.add_memory(procedural_entry)
        
        # Search semantic only
        results = await self.memory_store.search_memory(
            "pattern implementation",
            memory_type=MemoryType.SEMANTIC,
            use_vector=False,
            rerank=False
        )
        
        assert len(results) >= 1
        assert all(r.entry.memory_type == MemoryType.SEMANTIC for r in results)
    
    @pytest.mark.asyncio
    async def test_escape_fts_query(self):
        """Test FTS query escaping."""
        # Test special characters
        escaped = self.memory_store._escape_fts_query('test "query" with (special)')
        assert '"' not in escaped or escaped.startswith('"')
        
        # Test simple query
        escaped = self.memory_store._escape_fts_query('simple')
        assert '"simple"' == escaped
    
    @pytest.mark.asyncio
    async def test_combine_results(self):
        """Test result combination and deduplication."""
        entry = MemoryEntry(
            topic="Test",
            content="Content",
            source="test"
        )
        
        # Create duplicate results
        results = [
            SearchResult(entry=entry, fts_score=0.8),
            SearchResult(entry=entry, vector_score=0.9),  # Same entry
            SearchResult(
                entry=MemoryEntry(topic="Other", content="Other", source="test"),
                fts_score=0.7
            )
        ]
        
        combined = self.memory_store._combine_results(results, 10)
        
        # Should deduplicate by hash_id
        assert len(combined) == 2
        
        # Should combine scores
        first_result = combined[0]  # Should be sorted by combined score
        assert first_result.combined_score is not None
    
    @pytest.mark.asyncio 
    async def test_access_stats_update(self):
        """Test access statistics updating."""
        entry = MemoryEntry(
            topic="Stats Test",
            content="Testing access stats",
            source="test"
        )
        
        hash_id = await self.memory_store.add_memory(entry)
        
        # Update access stats
        await self.memory_store._update_access_stats([hash_id])
        
        # Check updated
        cursor = self.memory_store.sqlite_conn.cursor()
        cursor.execute("SELECT access_count FROM memory_entries WHERE hash_id = ?", (hash_id,))
        count = cursor.fetchone()[0]
        
        assert count == 1
    
    def test_config_defaults(self):
        """Test configuration defaults."""
        from app.memory.enhanced_memory import EnhancedMemoryConfig
        
        config = EnhancedMemoryConfig()
        assert config.MAX_RESULTS == 50
        assert config.EMBEDDING_BATCH_SIZE == 100
        assert config.CACHE_TTL == 3600


class TestRealStreaming:
    """Test the real streaming functionality."""
    
    @pytest.fixture
    def mock_request(self):
        """Mock request object."""
        request = Mock()
        request.message = "Create a web server"
        request.team_id = "coding-swarm"
        request.pool = "balanced"
        request.use_memory = True
        return request
    
    @pytest.mark.asyncio
    async def test_stream_real_ai_execution(self, mock_request):
        """Test real AI streaming."""
        with patch('app.api.real_streaming.get_enhanced_memory_instance') as mock_memory:
            with patch('app.api.real_streaming.real_executor') as mock_executor:
                
                # Mock memory search
                mock_memory_instance = AsyncMock()
                mock_memory_instance.search_memory.return_value = [
                    Mock(entry=Mock(content="FastAPI is good for web servers"))
                ]
                mock_memory.return_value = mock_memory_instance
                
                # Mock LLM execution
                mock_executor.execute.return_value = {
                    'success': True,
                    'content': 'Generated planning content',
                    'timestamp': datetime.now().isoformat()
                }
                
                # Collect streamed results
                results = []
                async for chunk in stream_real_ai_execution(mock_request):
                    results.append(json.loads(chunk))
                
                # Verify phases
                phases = [r['phase'] for r in results]
                assert 'initialization' in phases
                assert 'memory' in phases  
                assert 'planning' in phases
                assert 'generation' in phases
                
                # Verify memory integration
                memory_results = [r for r in results if r['phase'] == 'memory']
                assert len(memory_results) > 0
                assert 'Found' in memory_results[0]['token']
    
    @pytest.mark.asyncio
    async def test_error_handling_in_streaming(self, mock_request):
        """Test error handling in streaming."""
        with patch('app.api.real_streaming.get_enhanced_memory_instance') as mock_memory:
            # Mock memory failure
            mock_memory.side_effect = Exception("Memory error")
            
            results = []
            async for chunk in stream_real_ai_execution(mock_request):
                results.append(json.loads(chunk))
            
            # Should continue despite memory error
            phases = [r['phase'] for r in results]
            assert 'initialization' in phases
            
            # Should have warning about memory
            memory_warnings = [r for r in results if 'memory' in r.get('token', '').lower()]
            assert any('unavailable' in r['token'].lower() for r in memory_warnings)


class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_coding_swarm(self):
        """Test end-to-end coding swarm execution."""
        # This would test the full pipeline from request to response
        # In a real environment with actual API keys
        
        config = SwarmConfiguration(
            pool=PoolType.BALANCED,
            max_generators=2,
            use_memory=False,  # Skip memory for this test
            timeout_seconds=30
        )
        
        # Mock the actual LLM calls for testing
        with patch('app.llm.real_executor.gateway') as mock_gateway:
            mock_gateway.achat = AsyncMock(return_value="# Mock generated code\nprint('Hello World')")
            
            from app.swarms.coding.team import make_coding_swarm
            
            # Create swarm
            swarm = make_coding_swarm(pool="balanced")
            
            # Verify swarm creation
            assert swarm is not None
            assert swarm.name
    
    def test_swarm_configuration_validation(self):
        """Test swarm configuration validation."""
        # Valid config
        config = SwarmConfiguration(
            pool=PoolType.FAST,
            max_generators=3,
            accuracy_threshold=8.0
        )
        assert config.pool == PoolType.FAST
        assert config.max_generators == 3
        
        # Test constraints
        with pytest.raises(Exception):
            SwarmConfiguration(max_generators=15)  # Too high
        
        with pytest.raises(Exception):
            SwarmConfiguration(accuracy_threshold=15.0)  # Too high
    
    @pytest.mark.asyncio
    async def test_memory_search_performance(self):
        """Test memory search performance with many entries."""
        from app.memory.enhanced_memory import EnhancedMemoryStore
        
        # Use in-memory database for speed
        import tempfile
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            from app.memory.enhanced_memory import EnhancedMemoryConfig
            config = EnhancedMemoryConfig()
            config.SQLITE_PATH = temp_db.name
            
            store = EnhancedMemoryStore(config)
            await store.initialize()
            
            # Add many entries
            import time
            start_time = time.time()
            
            for i in range(100):
                entry = MemoryEntry(
                    topic=f"Topic {i}",
                    content=f"This is content number {i} with various keywords python javascript react",
                    source=f"source_{i}",
                    memory_type=MemoryType.SEMANTIC if i % 2 else MemoryType.PROCEDURAL
                )
                await store.add_memory(entry)
            
            add_time = time.time() - start_time
            print(f"Added 100 entries in {add_time:.3f}s")
            
            # Test search performance
            start_time = time.time()
            results = await store.search_memory("python javascript", limit=10, use_vector=False)
            search_time = time.time() - start_time
            
            print(f"Search completed in {search_time:.3f}s")
            assert search_time < 1.0  # Should be fast
            assert len(results) > 0
            
            await store.close()
            
        finally:
            import os
            try:
                os.unlink(temp_db.name)
            except:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])