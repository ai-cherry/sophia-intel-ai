from unittest.mock import MagicMock, patch

from app.mcp.memory_adapter import MemoryAdapter


class TestMemoryAdapter:
    @patch('app.mcp.memory_adapter.redis.Redis')
    def test_store_memory(self, mock_redis):
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.set.return_value = True

        adapter = MemoryAdapter()
        result = adapter.store_memory("test content", {"key": "value"})
        assert result is True
        mock_redis_instance.set.assert_called_once_with("memory:test content", "test content", ex=86400)

    @patch('app.mcp.memory_adapter.redis.Redis')
    def test_search_memory(self, mock_redis):
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.get.return_value = b"test content"

        adapter = MemoryAdapter()
        result = adapter.search_memory("test query", {"key": "value"})
        assert result == ["test content"]
        mock_redis_instance.get.assert_called_once_with("memory:test query")

    @patch('app.mcp.memory_adapter.redis.Redis')
    def test_update_memory(self, mock_redis):
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.set.return_value = True

        adapter = MemoryAdapter()
        result = adapter.update_memory("memory_id", "new content", {"key": "value"})
        assert result is True
        mock_redis_instance.set.assert_called_once_with("memory:memory_id", "new content", ex=86400)

    @patch('app.mcp.memory_adapter.redis.Redis')
    def test_delete_memory(self, mock_redis):
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.delete.return_value = 1

        adapter = MemoryAdapter()
        result = adapter.delete_memory("memory_id")
        assert result is True
        mock_redis_instance.delete.assert_called_once_with("memory:memory_id")
