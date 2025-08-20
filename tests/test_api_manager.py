"""
Tests for SOPHIAAPIManager
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from sophia.core.api_manager import SOPHIAAPIManager, ServiceClient

class TestSOPHIAAPIManager:
    """Test cases for SOPHIAAPIManager."""

    def test_api_manager_initialization(self):
        """Test that API manager initializes without errors."""
        # Mock environment variables to avoid actual connections
        with patch.dict(os.environ, {
            "QDRANT_URL": "http://localhost:6333",
            "QDRANT_API_KEY": "dummy",
            "REDIS_URL": "redis://localhost:6379",
            "NEON_POSTGRES_DSN": "postgresql://user:pass@localhost/db"
        }):
            manager = SOPHIAAPIManager()
            assert manager is not None
            assert isinstance(manager.service_clients, dict)

    def test_service_client_dataclass(self):
        """Test ServiceClient dataclass functionality."""
        client = ServiceClient(
            name="test_service",
            client=None,
            api_key_env_var="TEST_API_KEY",
            endpoint="https://api.test.com"
        )
        
        assert client.name == "test_service"
        assert client.client is None
        assert client.api_key_env_var == "TEST_API_KEY"
        assert client.endpoint == "https://api.test.com"
        assert client.status == "unknown"  # default value

    def test_get_service_status(self):
        """Test getting service status."""
        with patch.dict(os.environ, {
            "QDRANT_URL": "http://localhost:6333",
            "REDIS_URL": "redis://localhost:6379"
        }):
            manager = SOPHIAAPIManager()
            status = manager.get_service_status()
            
            assert isinstance(status, dict)
            assert "databases" in status
            assert "infrastructure" in status
            assert "services" in status

    def test_get_configured_services(self):
        """Test getting list of configured services."""
        with patch.dict(os.environ, {
            "SERPER_API_KEY": "test_key",
            "GITHUB_TOKEN": "test_token"
        }):
            manager = SOPHIAAPIManager()
            services = manager.get_configured_services()
            
            assert isinstance(services, list)
            assert "serper" in services
            assert "github" in services

    def test_redis_operations_not_configured(self):
        """Test Redis operations when Redis is not configured."""
        manager = SOPHIAAPIManager()
        manager.redis_client = None
        
        with pytest.raises(RuntimeError, match="Redis not configured"):
            manager.get_redis("test_key")
        
        with pytest.raises(RuntimeError, match="Redis not configured"):
            manager.set_redis("test_key", "test_value")

    def test_qdrant_operations_not_configured(self):
        """Test Qdrant operations when Qdrant is not configured."""
        manager = SOPHIAAPIManager()
        manager.qdrant_client = None
        
        with pytest.raises(RuntimeError, match="Qdrant not configured"):
            manager.upsert_qdrant("test_collection", [], [])

    @pytest.mark.asyncio
    async def test_postgres_operations_not_configured(self):
        """Test PostgreSQL operations when PostgreSQL is not configured."""
        manager = SOPHIAAPIManager()
        manager.postgres_pool = None
        
        with pytest.raises(RuntimeError, match="PostgreSQL not configured"):
            await manager.query_postgres("SELECT 1")

    @patch('redis.from_url')
    def test_redis_initialization_success(self, mock_redis):
        """Test successful Redis initialization."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}):
            manager = SOPHIAAPIManager()
            assert manager.redis_client == mock_client

    @patch('qdrant_client.QdrantClient')
    def test_qdrant_initialization_success(self, mock_qdrant):
        """Test successful Qdrant initialization."""
        mock_client = MagicMock()
        mock_qdrant.return_value = mock_client
        
        with patch.dict(os.environ, {
            "QDRANT_URL": "http://localhost:6333",
            "QDRANT_API_KEY": "test_key"
        }):
            manager = SOPHIAAPIManager()
            assert manager.qdrant_client == mock_client

    def test_lambda_ips_parsing(self):
        """Test Lambda Labs IP parsing."""
        with patch.dict(os.environ, {"LAMBDA_IPS": "192.168.1.1,192.168.1.2,192.168.1.3"}):
            manager = SOPHIAAPIManager()
            assert len(manager.lambda_ips) == 3
            assert "192.168.1.1" in manager.lambda_ips
            assert "192.168.1.2" in manager.lambda_ips
            assert "192.168.1.3" in manager.lambda_ips

    def test_fly_app_ids_parsing(self):
        """Test Fly.io app IDs parsing."""
        with patch.dict(os.environ, {"FLY_APP_IDS": "app1,app2,app3"}):
            manager = SOPHIAAPIManager()
            assert len(manager.fly_app_ids) == 3
            assert "app1" in manager.fly_app_ids
            assert "app2" in manager.fly_app_ids
            assert "app3" in manager.fly_app_ids

    def test_service_configuration_with_api_keys(self):
        """Test that services are configured when API keys are present."""
        env_vars = {
            "SERPER_API_KEY": "test_serper",
            "BRIGHT_DATA_API_KEY": "test_bright",
            "GONG_ACCESS_KEY": "test_gong",
            "HUBSPOT_API_KEY": "test_hubspot",
            "OPENROUTER_API_KEY": "test_openrouter"
        }
        
        with patch.dict(os.environ, env_vars):
            manager = SOPHIAAPIManager()
            
            # Check that services are configured
            assert "serper" in manager.service_clients
            assert "bright_data" in manager.service_clients
            assert "gong" in manager.service_clients
            assert "hubspot" in manager.service_clients
            assert "openrouter" in manager.service_clients
            
            # Check service client properties
            serper_client = manager.service_clients["serper"]
            assert serper_client.name == "serper"
            assert serper_client.api_key_env_var == "SERPER_API_KEY"
            assert serper_client.status == "configured"

    def test_service_not_configured_without_api_keys(self):
        """Test that services are not configured when API keys are missing."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            manager = SOPHIAAPIManager()
            
            # Check that services are not configured
            assert "serper" not in manager.service_clients
            assert "gong" not in manager.service_clients
            assert "hubspot" not in manager.service_clients

    @pytest.mark.asyncio
    async def test_health_check_redis_success(self):
        """Test health check with successful Redis ping."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        
        manager = SOPHIAAPIManager()
        manager.redis_client = mock_redis
        
        health = await manager.health_check()
        assert "redis" in health
        assert health["redis"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_redis_failure(self):
        """Test health check with Redis ping failure."""
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = Exception("Connection failed")
        
        manager = SOPHIAAPIManager()
        manager.redis_client = mock_redis
        
        health = await manager.health_check()
        assert "redis" in health
        assert "unhealthy" in health["redis"]

    @pytest.mark.asyncio
    async def test_health_check_qdrant_success(self):
        """Test health check with successful Qdrant connection."""
        mock_qdrant = MagicMock()
        mock_qdrant.get_collections.return_value = []
        
        manager = SOPHIAAPIManager()
        manager.qdrant_client = mock_qdrant
        
        health = await manager.health_check()
        assert "qdrant" in health
        assert health["qdrant"] == "healthy"

