#!/usr/bin/env python3
"""
Unit tests for Fusion Metrics API
Tests the backend API endpoints for fusion system monitoring
"""

import json
import os
from unittest.mock import Mock, patch

import pytest
import redis

# Create test client
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the router under test
from routers.fusion_metrics import get_redis_client, router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestFusionMetricsAPI:
    """Unit tests for Fusion Metrics API endpoints"""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing"""
        mock_client = Mock(spec=redis.Redis)
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock_client.keys.return_value = []
        return mock_client

    def test_get_fusion_metrics_with_redis(self, mock_redis_client):
        """Test getting fusion metrics with Redis available"""
        with patch(
            "routers.fusion_metrics.get_redis_client", return_value=mock_redis_client
        ):
            # Mock Redis responses for each system
            def mock_get(key):
                if "redis_optimization" in key:
                    return json.dumps(
                        {
                            "memory_saved_gb": 2.4,
                            "cost_savings": 127.50,
                            "keys_pruned": 1847,
                            "status": "active",
                        }
                    )
                elif "edge_rag" in key:
                    return json.dumps(
                        {
                            "query_count": 342,
                            "avg_latency": 245,
                            "success_rate": 98.7,
                            "status": "active",
                        }
                    )
                elif "hybrid_routing" in key:
                    return json.dumps(
                        {
                            "requests_routed": 15420,
                            "cost_optimization": 31.2,
                            "uptime": 99.94,
                            "status": "active",
                        }
                    )
                elif "cross_db_analytics" in key:
                    return json.dumps(
                        {
                            "predictions_made": 89,
                            "accuracy": 94.3,
                            "data_points": 12847,
                            "status": "active",
                        }
                    )
                return None

            mock_redis_client.get.side_effect = mock_get

            # Test the endpoint
            response = client.get("/api/fusion/metrics")

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Check structure
            assert "redis_optimization" in data
            assert "edge_rag" in data
            assert "hybrid_routing" in data
            assert "cross_db_analytics" in data
            assert "timestamp" in data

            # Check Redis optimization data
            redis_data = data["redis_optimization"]
            assert redis_data["memory_saved"] == 2.4
            assert redis_data["cost_savings"] == 127.50
            assert redis_data["keys_pruned"] == 1847
            assert redis_data["status"] == "active"

            # Check Edge RAG data
            edge_data = data["edge_rag"]
            assert edge_data["query_count"] == 342
            assert edge_data["avg_latency"] == 245
            assert edge_data["success_rate"] == 98.7
            assert edge_data["status"] == "active"

    def test_get_fusion_metrics_without_redis(self):
        """Test getting fusion metrics without Redis (fallback to mock data)"""
        with patch("routers.fusion_metrics.get_redis_client", return_value=None):
            # Test the endpoint
            response = client.get("/api/fusion/metrics")

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Check structure (should use mock data)
            assert "redis_optimization" in data
            assert "edge_rag" in data
            assert "hybrid_routing" in data
            assert "cross_db_analytics" in data
            assert "timestamp" in data

            # Verify mock data is returned
            redis_data = data["redis_optimization"]
            assert redis_data["status"] == "active"
            assert "memory_saved" in redis_data
            assert "cost_savings" in redis_data

    def test_get_system_health_with_redis(self, mock_redis_client):
        """Test getting system health with Redis available"""
        with patch(
            "routers.fusion_metrics.get_redis_client", return_value=mock_redis_client
        ):
            # Mock Redis responses
            def mock_get(key):
                if "redis_optimization" in key:
                    return json.dumps({"cost_savings": 127.50, "status": "active"})
                elif "edge_rag" in key:
                    return json.dumps({"avg_latency": 245, "status": "active"})
                elif "hybrid_routing" in key:
                    return json.dumps({"uptime": 99.94, "status": "active"})
                elif "cross_db_analytics" in key:
                    return json.dumps({"status": "active"})
                return None

            mock_redis_client.get.side_effect = mock_get

            # Test the endpoint
            response = client.get("/api/fusion/health")

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Check structure
            assert "overall_uptime" in data
            assert "avg_response_time" in data
            assert "total_cost_savings" in data
            assert "active_systems" in data
            assert "timestamp" in data

            # Verify calculated values
            assert data["active_systems"] == 4  # All systems active
            assert data["total_cost_savings"] >= 127.50  # At least Redis savings

    def test_get_system_health_without_redis(self):
        """Test getting system health without Redis (fallback to mock data)"""
        with patch("routers.fusion_metrics.get_redis_client", return_value=None):
            # Test the endpoint
            response = client.get("/api/fusion/health")

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Check structure and mock values
            assert data["overall_uptime"] == 99.94
            assert data["avg_response_time"] == 245
            assert data["total_cost_savings"] == 158.72
            assert data["active_systems"] == 4

    def test_get_performance_metrics_with_redis(self, mock_redis_client):
        """Test getting performance metrics with Redis available"""
        with patch(
            "routers.fusion_metrics.get_redis_client", return_value=mock_redis_client
        ):
            # Mock Redis responses
            def mock_get(key):
                if "edge_rag" in key:
                    return json.dumps({"success_rate": 98.7, "status": "active"})
                elif "hybrid_routing" in key:
                    return json.dumps({"uptime": 99.94, "status": "active"})
                elif "cross_db_analytics" in key:
                    return json.dumps({"accuracy": 94.3, "status": "active"})
                return None

            mock_redis_client.get.side_effect = mock_get

            # Test the endpoint
            response = client.get("/api/fusion/performance")

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Check structure
            assert "redis_memory_reduction" in data
            assert "redis_cost_optimization" in data
            assert "edge_rag_success_rate" in data
            assert "edge_rag_latency_improvement" in data
            assert "hybrid_routing_uptime" in data
            assert "cross_db_accuracy" in data
            assert "timestamp" in data

            # Verify values
            assert data["edge_rag_success_rate"] == 98.7
            assert data["hybrid_routing_uptime"] == 99.94
            assert data["cross_db_accuracy"] == 94.3

    def test_get_performance_metrics_without_redis(self):
        """Test getting performance metrics without Redis (fallback to mock data)"""
        with patch("routers.fusion_metrics.get_redis_client", return_value=None):
            # Test the endpoint
            response = client.get("/api/fusion/performance")

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Check mock values
            assert data["redis_memory_reduction"] == 67.0
            assert data["redis_cost_optimization"] == 43.0
            assert data["edge_rag_success_rate"] == 98.7
            assert data["edge_rag_latency_improvement"] == 15.0
            assert data["hybrid_routing_uptime"] == 99.94
            assert data["cross_db_accuracy"] == 94.3

    def test_trigger_fusion_system_redis(self):
        """Test triggering Redis optimization system"""
        response = client.post("/api/fusion/trigger/redis_optimization")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "redis_optimization" in data["message"]
        assert "timestamp" in data

    def test_trigger_fusion_system_edge_rag(self):
        """Test triggering Edge RAG system"""
        response = client.post("/api/fusion/trigger/edge_rag")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "edge_rag" in data["message"]
        assert "timestamp" in data

    def test_trigger_fusion_system_hybrid_routing(self):
        """Test triggering Hybrid Routing system"""
        response = client.post("/api/fusion/trigger/hybrid_routing")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "hybrid_routing" in data["message"]
        assert "timestamp" in data

    def test_trigger_fusion_system_cross_db(self):
        """Test triggering Cross-DB Analytics system"""
        response = client.post("/api/fusion/trigger/cross_db_analytics")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "cross_db_analytics" in data["message"]
        assert "timestamp" in data

    def test_trigger_fusion_system_invalid(self):
        """Test triggering invalid system"""
        response = client.post("/api/fusion/trigger/invalid_system")

        # Verify error response
        assert response.status_code == 400
        data = response.json()

        assert "detail" in data
        assert "Unknown system" in data["detail"]

    def test_get_fusion_status_with_redis(self, mock_redis_client):
        """Test getting fusion status with Redis available"""
        with patch(
            "routers.fusion_metrics.get_redis_client", return_value=mock_redis_client
        ):
            # Mock Redis responses
            def mock_get(key):
                return json.dumps({"status": "active"})

            mock_redis_client.get.side_effect = mock_get

            # Test the endpoint
            response = client.get("/api/fusion/status")

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Check structure
            assert "overall_status" in data
            assert "systems" in data
            assert "timestamp" in data

            # Verify all systems are active
            assert data["overall_status"] == "healthy"
            systems = data["systems"]
            assert systems["redis_optimization"] == "active"
            assert systems["edge_rag"] == "active"
            assert systems["hybrid_routing"] == "active"
            assert systems["cross_db_analytics"] == "active"

    def test_get_fusion_status_without_redis(self):
        """Test getting fusion status without Redis"""
        with patch("routers.fusion_metrics.get_redis_client", return_value=None):
            # Test the endpoint
            response = client.get("/api/fusion/status")

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Check structure
            assert "overall_status" in data
            assert "systems" in data
            assert "timestamp" in data

            # Verify degraded status due to no Redis
            assert data["overall_status"] == "degraded"
            systems = data["systems"]
            assert all(status == "unknown" for status in systems.values())


class TestRedisClientManagement:
    """Test Redis client management functions"""

    def test_get_redis_client_success(self):
        """Test successful Redis client creation"""
        with patch.dict(os.environ, {"REDIS_URL": "${REDIS_URL}"}):
            with patch("redis.from_url") as mock_redis:
                mock_client = Mock()
                mock_client.ping.return_value = True
                mock_redis.return_value = mock_client

                # Test client creation
                client = get_redis_client()

                # Verify client
                assert client == mock_client
                mock_redis.assert_called_once_with(
                    "${REDIS_URL}", decode_responses=True
                )
                mock_client.ping.assert_called_once()

    def test_get_redis_client_connection_error(self):
        """Test Redis client creation with connection error"""
        with patch.dict(os.environ, {"REDIS_URL": "${REDIS_URL}"}):
            with patch("redis.from_url") as mock_redis:
                mock_client = Mock()
                mock_client.ping.side_effect = redis.ConnectionError(
                    "Connection failed"
                )
                mock_redis.return_value = mock_client

                # Test client creation
                client = get_redis_client()

                # Should return None on connection error
                assert client is None

    def test_get_redis_client_default_url(self):
        """Test Redis client creation with default URL"""
        with patch.dict(os.environ, {}, clear=True):  # Clear REDIS_URL
            with patch("redis.from_url") as mock_redis:
                mock_client = Mock()
                mock_client.ping.return_value = True
                mock_redis.return_value = mock_client

                # Test client creation
                client = get_redis_client()

                # Verify default URL is used
                mock_redis.assert_called_once_with(
                    "${REDIS_URL}", decode_responses=True
                )


class TestErrorHandling:
    """Test error handling in the API"""

    def test_metrics_endpoint_error(self):
        """Test metrics endpoint with internal error"""
        with patch("routers.fusion_metrics.get_redis_client") as mock_get_redis:
            # Mock Redis client that raises an exception
            mock_client = Mock()
            mock_client.get.side_effect = Exception("Redis error")
            mock_get_redis.return_value = mock_client

            # Test the endpoint
            response = client.get("/api/fusion/metrics")

            # Should return 500 error
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_health_endpoint_error(self):
        """Test health endpoint with internal error"""
        with patch("routers.fusion_metrics.get_redis_client") as mock_get_redis:
            # Mock Redis client that raises an exception
            mock_client = Mock()
            mock_client.get.side_effect = Exception("Redis error")
            mock_get_redis.return_value = mock_client

            # Test the endpoint
            response = client.get("/api/fusion/health")

            # Should return 500 error
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_status_endpoint_with_error(self):
        """Test status endpoint handling errors gracefully"""
        with patch("routers.fusion_metrics.get_redis_client") as mock_get_redis:
            # Mock Redis client that raises an exception
            mock_get_redis.side_effect = Exception("Redis connection failed")

            # Test the endpoint
            response = client.get("/api/fusion/status")

            # Should return 200 with error status
            assert response.status_code == 200
            data = response.json()

            assert data["overall_status"] == "error"
            assert "error" in data


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
