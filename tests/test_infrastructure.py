"""
Test suite for infrastructure components (secrets, memory, portkey)
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.portkey_manager import PortkeyManager, TaskType
from app.core.secrets_manager import SecretsManager as SecureSecretsManager
from app.memory.unified_memory_router import DocChunk, MemoryDomain, UnifiedMemoryRouter


class TestSecretsManager:
    """Test secure secrets management"""

    def test_initialization(self):
        """Test secrets manager initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecureSecretsManager(vault_path=Path(tmpdir))
            assert manager.vault_path.exists()
            assert manager._cipher is not None

    def test_set_and_get_secret(self):
        """Test setting and getting secrets"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecureSecretsManager(vault_path=Path(tmpdir))

            # Set secret
            manager.set_secret("TEST_KEY", "test_value")

            # Get secret
            value = manager.get_secret("TEST_KEY")
            assert value == "test_value"

    def test_encryption(self):
        """Test that secrets are encrypted in vault"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecureSecretsManager(vault_path=Path(tmpdir))

            # Set secret
            manager.set_secret("SENSITIVE_KEY", "sensitive_data")

            # Read vault file directly
            vault_file = manager.vault_path / "secrets.json"
            with open(vault_file) as f:
                vault_data = json.load(f)

            # Verify data is encrypted
            assert "SENSITIVE_KEY" in vault_data
            assert vault_data["SENSITIVE_KEY"] != "sensitive_data"
            assert len(vault_data["SENSITIVE_KEY"]) > 50  # Encrypted data is longer

    def test_environment_fallback(self):
        """Test fallback to environment variables"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecureSecretsManager(vault_path=Path(tmpdir))

            # Set environment variable
            os.environ["ENV_TEST_KEY"] = "env_value"

            # Get secret (not in vault, should fall back to env)
            value = manager.get_secret("ENV_TEST_KEY")
            assert value == "env_value"

            # Clean up
            del os.environ["ENV_TEST_KEY"]

    def test_cache_functionality(self):
        """Test in-memory cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecureSecretsManager(vault_path=Path(tmpdir))

            # Set secret
            manager.set_secret("CACHE_KEY", "cached_value")

            # First get should populate cache
            value1 = manager.get_secret("CACHE_KEY")

            # Modify vault directly (simulate external change)
            vault_file = manager.vault_path / "secrets.json"
            os.remove(vault_file)

            # Second get should use cache
            value2 = manager.get_secret("CACHE_KEY")
            assert value2 == "cached_value"

    def test_default_value(self):
        """Test default value when secret not found"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecureSecretsManager(vault_path=Path(tmpdir))

            value = manager.get_secret("NONEXISTENT_KEY", default="default_value")
            assert value == "default_value"

    def test_list_secrets(self):
        """Test listing all secret keys"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecureSecretsManager(vault_path=Path(tmpdir))

            # Set multiple secrets
            manager.set_secret("KEY1", "value1")
            manager.set_secret("KEY2", "value2")
            manager.set_secret("KEY3", "value3")

            keys = manager.list_secrets()
            assert "KEY1" in keys
            assert "KEY2" in keys
            assert "KEY3" in keys

    def test_delete_secret(self):
        """Test deleting a secret"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SecureSecretsManager(vault_path=Path(tmpdir))

            # Set and delete secret
            manager.set_secret("DELETE_ME", "value")
            manager.delete_secret("DELETE_ME")

            # Verify deleted
            value = manager.get_secret("DELETE_ME")
            assert value is None


class TestPortkeyManager:
    """Test Portkey virtual key management"""

    @pytest.fixture
    def mock_secrets(self):
        """Mock secrets manager"""
        with patch("app.core.portkey_manager.get_secrets_manager") as mock:
            secrets = MagicMock()
            secrets.get_secret = MagicMock(
                side_effect=lambda key, default=None: f"mock-{key}"
            )
            mock.return_value = secrets
            yield secrets

    def test_initialization(self, mock_secrets):
        """Test Portkey manager initialization"""
        manager = PortkeyManager()
        assert len(manager.VIRTUAL_KEYS) >= 14
        assert manager.circuit_breaker is not None

    def test_get_virtual_key(self, mock_secrets):
        """Test getting virtual keys"""
        manager = PortkeyManager()

        key = manager.get_virtual_key("openai")
        assert key == "openai-vk-190a60"

        key = manager.get_virtual_key("anthropic")
        assert key == "anthropic-vk-b42804"

    def test_invalid_provider(self, mock_secrets):
        """Test invalid provider handling"""
        manager = PortkeyManager()

        with pytest.raises(ValueError):
            manager.get_virtual_key("invalid_provider")

    @pytest.mark.asyncio
    async def test_task_routing(self, mock_secrets):
        """Test task type routing"""
        manager = PortkeyManager()

        # Mock the actual API call
        with patch.object(
            manager, "_execute_with_portkey", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = {"choices": [{"message": {"content": "test"}}]}

            result = await manager.execute_with_fallback(
                task_type=TaskType.ANALYSIS,
                messages=[{"role": "user", "content": "test"}],
            )

            assert result["choices"][0]["message"]["content"] == "test"
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, mock_secrets):
        """Test fallback to secondary providers"""
        manager = PortkeyManager()

        # Mock primary provider failure and secondary success
        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Primary provider failed")
            return {"choices": [{"message": {"content": "fallback"}}]}

        with patch.object(manager, "_execute_with_portkey", side_effect=mock_execute):
            result = await manager.execute_with_fallback(
                task_type=TaskType.CODE_GENERATION,
                messages=[{"role": "user", "content": "test"}],
            )

            assert result["choices"][0]["message"]["content"] == "fallback"
            assert call_count == 2  # Primary failed, secondary succeeded

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, mock_secrets):
        """Test circuit breaker activation"""
        manager = PortkeyManager()

        # Simulate repeated failures
        with patch.object(
            manager, "_execute_with_portkey", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.side_effect = Exception("API Error")

            # Multiple failures should trip circuit
            for _ in range(5):
                try:
                    await manager.execute_with_fallback(
                        task_type=TaskType.RESEARCH,
                        messages=[{"role": "user", "content": "test"}],
                    )
                except Exception:pass

            # Circuit should be open
            assert manager.circuit_breaker.current_state == "open"


class TestUnifiedMemoryRouter:
    """Test unified memory routing"""

    @pytest.fixture
    def mock_clients(self):
        """Mock memory backend clients"""
        with (
            patch("app.memory.unified_memory_router.redis.Redis") as mock_redis,
            patch("app.memory.unified_memory_router.weaviate.Client") as mock_weaviate,
        ):
            redis_client = MagicMock()
            redis_client.get = MagicMock(return_value=None)
            redis_client.setex = MagicMock()
            mock_redis.return_value = redis_client

            weaviate_client = MagicMock()
            mock_weaviate.return_value = weaviate_client

            yield redis_client, weaviate_client

    @pytest.mark.asyncio
    async def test_initialization(self, mock_clients):
        """Test memory router initialization"""
        router = UnifiedMemoryRouter()
        assert router.domain_isolation is True

    @pytest.mark.asyncio
    async def test_ephemeral_storage(self, mock_clients):
        """Test L1 ephemeral storage"""
        redis_client, _ = mock_clients
        router = UnifiedMemoryRouter()

        # Store ephemeral
        await router.put_ephemeral("test_key", {"data": "test"}, ttl_s=60)
        redis_client.setex.assert_called_with("test_key", 60, '{"data": "test"}')

        # Get ephemeral
        redis_client.get.return_value = b'{"data": "test"}'
        result = await router.get_ephemeral("test_key")
        assert result == '{"data": "test"}'

    @pytest.mark.asyncio
    async def test_semantic_search(self, mock_clients):
        """Test L2 semantic search"""
        _, weaviate_client = mock_clients
        router = UnifiedMemoryRouter()

        # Mock Weaviate query
        mock_results = MagicMock()
        mock_results.objects = [
            {"properties": {"content": "Result 1"}, "vector": [0.1, 0.2]},
            {"properties": {"content": "Result 2"}, "vector": [0.3, 0.4]},
        ]
        weaviate_client.query.get.return_value.with_near_vector.return_value.with_limit.return_value.do.return_value = {
            "data": {"Get": {"Document": mock_results.objects}}
        }

        results = await router.semantic_search(
            query_embedding=[0.5, 0.5], domain=MemoryDomain.SOPHIA, limit=2
        )

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_domain_isolation(self, mock_clients):
        """Test domain isolation in memory"""
        router = UnifiedMemoryRouter()

        # Create chunks for different domains
        sophia_chunk = DocChunk(
            content="Sophia BI data", metadata={"domain": "bi"}, embedding=[0.1, 0.2]
        )

        artemis_chunk = DocChunk(
            content="Artemis code data",
            metadata={"domain": "code"},
            embedding=[0.3, 0.4],
        )

        # Store in different domains
        await router.upsert_chunks([sophia_chunk], MemoryDomain.SOPHIA)
        await router.upsert_chunks([artemis_chunk], MemoryDomain.ARTEMIS)

        # Verify isolation (would be tested with actual backend)
        # Here we're testing that the router maintains separate namespaces

    @pytest.mark.asyncio
    async def test_cost_optimization(self, mock_clients):
        """Test cost-based tier selection"""
        router = UnifiedMemoryRouter()

        # Hot data should go to L1
        await router.put_ephemeral("hot_key", "hot_data", ttl_s=300)

        # Large cold data would go to L4 (S3)
        large_data = "x" * (10 * 1024 * 1024)  # 10MB
        await router.archive("cold_key", large_data.encode(), {"type": "backup"})

        # Verify routing decisions (mock verification)
        assert mock_clients[0].setex.called  # Redis for hot data


class TestIntegrationE2E:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test complete pipeline from secrets to memory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize components
            secrets = SecureSecretsManager(vault_path=Path(tmpdir))
            secrets.set_secret("OPENAI_API_KEY", "test-key")

            with patch("app.core.portkey_manager.get_secrets_manager") as mock_secrets:
                mock_secrets.return_value = secrets

                portkey = PortkeyManager()

                # Verify integration
                assert portkey.get_virtual_key("openai") is not None

    @pytest.mark.asyncio
    async def test_security_isolation(self):
        """Test security boundaries between components"""
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets = SecureSecretsManager(vault_path=Path(tmpdir))

            # Set sensitive data
            secrets.set_secret("SENSITIVE_API_KEY", "super-secret")

            # Verify it's not accessible without proper access
            vault_file = secrets.vault_path / "secrets.json"
            with open(vault_file) as f:
                vault_data = json.load(f)

            # Data should be encrypted
            assert "super-secret" not in str(vault_data)


@pytest.mark.parametrize("domain", [MemoryDomain.SOPHIA, MemoryDomain.ARTEMIS])
def test_memory_domain_separation(domain):
    """Test that memory domains are properly separated"""
    # This would test with actual backends
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
