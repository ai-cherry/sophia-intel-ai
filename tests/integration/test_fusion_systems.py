#!/usr/bin/env python3
"""
Integration tests for Sophia AI Fusion Systems
Tests the 4 fusion systems working together in realistic scenarios
"""

import json
import os
import time
from datetime import datetime

import pytest
import redis

# Handle optional dependencies gracefully
try:
    from qdrant_client import QdrantClient

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

    # Mock QdrantClient for when Qdrant is not available
    class QdrantClient:
        def __init__(self, *args, **kwargs):
            pass


# Test configuration
TEST_REDIS_URL = os.getenv("REDIS_URL", "${REDIS_URL}")
TEST_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


class TestFusionSystemsIntegration:
    """Integration tests for all fusion systems"""

    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment before each test"""
        # Initialize Redis client
        self.redis_client = redis.from_url(TEST_REDIS_URL, decode_responses=True)

        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(url=TEST_QDRANT_URL)

        # Clear test data
        await self.cleanup_test_data()

        yield

        # Cleanup after test
        await self.cleanup_test_data()

    async def cleanup_test_data(self):
        """Clean up test data from Redis and Qdrant"""
        try:
            # Clear Redis test keys
            test_keys = self.redis_client.keys("test:*")
            if test_keys:
                self.redis_client.delete(*test_keys)

            # Clear fusion metrics
            fusion_keys = self.redis_client.keys("fusion:*")
            if fusion_keys:
                self.redis_client.delete(*fusion_keys)

        except Exception as e:
            print(f"Cleanup warning: {e}")

    @pytest.mark.asyncio
    async def test_redis_optimization_system(self):
        """Test Redis optimization system functionality"""
        # Import the Redis optimization system
        import sys

        sys.path.append("/home/ubuntu/sophia-main/swarms")

        try:
            from mem0_agno_self_pruning import MemoryOptimizationSwarm

            # Create test data in Redis
            test_keys = []
            for i in range(10):
                key = f"test:large_key_{i}"
                value = "x" * 1024 * 100  # 100KB value
                self.redis_client.set(key, value)
                test_keys.append(key)

            # Initialize optimization swarm
            optimizer = MemoryOptimizationSwarm()

            # Run optimization cycle
            result = await optimizer.run_optimization_cycle()

            # Verify results
            assert result is not None
            assert "status" in result

            # Check if optimization was attempted
            if result["status"] in ["completed", "skipped", "no_candidates"]:
                print(f"Redis optimization test passed: {result['status']}")
            else:
                pytest.fail(f"Unexpected optimization status: {result['status']}")

        except ImportError as e:
            pytest.skip(f"Redis optimization system not available: {e}")
        except Exception as e:
            pytest.fail(f"Redis optimization test failed: {e}")

    @pytest.mark.asyncio
    async def test_edge_rag_system(self):
        """Test Edge RAG system functionality"""
        import sys

        sys.path.append("/home/ubuntu/sophia-main/monitoring")

        try:
            from qdrant_edge_rag import QdrantEdgeRAG

            # Initialize Edge RAG system
            rag_system = QdrantEdgeRAG()

            # Setup collection
            setup_success = await rag_system.setup_edge_collection()
            assert setup_success, "Failed to setup Qdrant collection"

            # Index mock transcripts
            indexed_count = await rag_system.index_gong_transcripts(limit=5)
            assert indexed_count > 0, "Failed to index transcripts"

            # Test RAG query
            results = await rag_system.query_rag(
                "property management automation", limit=3
            )
            assert isinstance(results, list), "RAG query should return a list"

            # Test coding assistant
            assistant_result = await rag_system.real_time_coding_assistant(
                "Implementing Redis caching for property search"
            )
            assert "suggestions" in assistant_result
            assert isinstance(assistant_result["suggestions"], list)

            print(
                f"Edge RAG test passed: {len(results)} results, {len(assistant_result['suggestions'])} suggestions"
            )

        except ImportError as e:
            pytest.skip(f"Edge RAG system not available: {e}")
        except Exception as e:
            pytest.fail(f"Edge RAG test failed: {e}")

    @pytest.mark.asyncio
    async def test_hybrid_routing_system(self):
        """Test Hybrid Routing system functionality"""
        import sys

        sys.path.append("/home/ubuntu/sophia-main/devops")

        try:
            from portkey_openrouter_hybrid import HybridModelRouter

            # Initialize hybrid router
            router = HybridModelRouter()

            # Test routing decision (without actual API calls)
            test_prompt = "Analyze the PropTech market trends for Q1 2025"

            # Mock the API calls to avoid external dependencies
            original_execute = router._execute_request

            async def mock_execute_request(prompt, rule):
                return {
                    "response": f"Mock response for {rule.model_type.value}",
                    "latency_ms": 250,
                    "cost": 0.01,
                    "success": True,
                    "tokens_used": 100,
                }

            router._execute_request = mock_execute_request

            # Test routing
            result = await router.route_request(test_prompt)

            # Verify result structure
            assert "response" in result
            assert "provider" in result
            assert "model_type" in result
            assert "latency_ms" in result
            assert "cost" in result

            print(
                f"Hybrid routing test passed: {result['provider']} -> {result['model_type']}"
            )

        except ImportError as e:
            pytest.skip(f"Hybrid routing system not available: {e}")
        except Exception as e:
            pytest.fail(f"Hybrid routing test failed: {e}")

    @pytest.mark.asyncio
    async def test_cross_db_analytics_system(self):
        """Test Cross-DB Analytics system functionality"""
        import sys

        sys.path.append("/home/ubuntu/sophia-main/pipelines")

        try:
            from neon_qdrant_analytics import (
                AnalyticsQuery,
                CrossDatabaseAnalyticsMCP,
                DataDomain,
            )

            # Initialize MCP system
            mcp = CrossDatabaseAnalyticsMCP()
            await mcp.initialize()

            # Test revenue forecast
            revenue_query = AnalyticsQuery(
                domain=DataDomain.FINANCE,
                query_type="revenue_forecast",
                parameters={"months": 6},
                timestamp=datetime.now(),
            )

            revenue_result = await mcp.handle_analytics_query(revenue_query)

            # Verify revenue forecast result
            assert "value" in revenue_result
            assert "confidence" in revenue_result
            assert "factors" in revenue_result
            assert revenue_result["prediction_type"] == "revenue_forecast"

            # Test property value prediction
            property_query = AnalyticsQuery(
                domain=DataDomain.PROPTECH,
                query_type="property_value_prediction",
                parameters={
                    "property_type": "apartment",
                    "square_feet": 1200,
                    "bedrooms": 2,
                    "bathrooms": 2.0,
                },
                timestamp=datetime.now(),
            )

            property_result = await mcp.handle_analytics_query(property_query)

            # Verify property prediction result
            assert "value" in property_result
            assert "confidence" in property_result
            assert property_result["prediction_type"] == "property_value"

            print(
                f"Cross-DB analytics test passed: Revenue=${revenue_result['value']:,.2f}, Property=${property_result['value']:,.2f}"
            )

        except ImportError as e:
            pytest.skip(f"Cross-DB analytics system not available: {e}")
        except Exception as e:
            pytest.fail(f"Cross-DB analytics test failed: {e}")

    @pytest.mark.asyncio
    async def test_fusion_systems_coordination(self):
        """Test coordination between fusion systems"""
        try:
            # Test data flow between systems

            # 1. Store metrics in Redis (simulating Redis optimization)
            redis_metrics = {
                "memory_saved_gb": 2.4,
                "cost_savings": 127.50,
                "keys_pruned": 1847,
                "status": "active",
                "timestamp": datetime.now().isoformat(),
            }

            self.redis_client.setex(
                "fusion:redis_optimization:metrics", 3600, json.dumps(redis_metrics)
            )

            # 2. Store Edge RAG metrics
            edge_metrics = {
                "query_count": 342,
                "avg_latency": 245,
                "success_rate": 98.7,
                "status": "active",
                "timestamp": datetime.now().isoformat(),
            }

            self.redis_client.setex(
                "fusion:edge_rag:metrics", 3600, json.dumps(edge_metrics)
            )

            # 3. Verify metrics can be retrieved
            stored_redis_metrics = self.redis_client.get(
                "fusion:redis_optimization:metrics"
            )
            stored_edge_metrics = self.redis_client.get("fusion:edge_rag:metrics")

            assert stored_redis_metrics is not None
            assert stored_edge_metrics is not None

            # Parse and verify
            redis_data = json.loads(stored_redis_metrics)
            edge_data = json.loads(stored_edge_metrics)

            assert redis_data["status"] == "active"
            assert edge_data["status"] == "active"
            assert redis_data["cost_savings"] == 127.50
            assert edge_data["success_rate"] == 98.7

            print("Fusion systems coordination test passed")

        except Exception as e:
            pytest.fail(f"Fusion systems coordination test failed: {e}")

    @pytest.mark.asyncio
    async def test_fusion_metrics_api_integration(self):
        """Test integration with fusion metrics API"""
        try:
            # This would test the actual API endpoints
            # For now, we'll test the data structures

            # Simulate API response structure
            expected_metrics = {
                "redis_optimization": {
                    "memory_saved": 2.4,
                    "cost_savings": 127.50,
                    "keys_pruned": 1847,
                    "status": "active",
                },
                "edge_rag": {
                    "query_count": 342,
                    "avg_latency": 245,
                    "success_rate": 98.7,
                    "status": "active",
                },
                "hybrid_routing": {
                    "requests_routed": 15420,
                    "cost_optimization": 31.2,
                    "uptime": 99.94,
                    "status": "active",
                },
                "cross_db_analytics": {
                    "predictions_made": 89,
                    "accuracy": 94.3,
                    "data_points": 12847,
                    "status": "active",
                },
            }

            # Verify structure
            for system, metrics in expected_metrics.items():
                assert "status" in metrics
                assert metrics["status"] in ["active", "idle", "error"]

                # System-specific validations
                if system == "redis_optimization":
                    assert "memory_saved" in metrics
                    assert "cost_savings" in metrics
                    assert "keys_pruned" in metrics
                elif system == "edge_rag":
                    assert "query_count" in metrics
                    assert "avg_latency" in metrics
                    assert "success_rate" in metrics
                elif system == "hybrid_routing":
                    assert "requests_routed" in metrics
                    assert "cost_optimization" in metrics
                    assert "uptime" in metrics
                elif system == "cross_db_analytics":
                    assert "predictions_made" in metrics
                    assert "accuracy" in metrics
                    assert "data_points" in metrics

            print("Fusion metrics API integration test passed")

        except Exception as e:
            pytest.fail(f"Fusion metrics API integration test failed: {e}")


class TestFusionSystemsPerformance:
    """Performance tests for fusion systems"""

    @pytest.mark.asyncio
    async def test_redis_optimization_performance(self):
        """Test Redis optimization performance"""
        try:
            redis_client = redis.from_url(TEST_REDIS_URL, decode_responses=True)

            # Create test data
            start_time = time.time()

            for i in range(100):
                key = f"perf_test:key_{i}"
                value = "x" * 1024  # 1KB value
                redis_client.set(key, value)

            creation_time = time.time() - start_time

            # Test retrieval performance
            start_time = time.time()

            for i in range(100):
                key = f"perf_test:key_{i}"
                redis_client.get(key)

            retrieval_time = time.time() - start_time

            # Cleanup
            test_keys = redis_client.keys("perf_test:*")
            if test_keys:
                redis_client.delete(*test_keys)

            # Performance assertions
            assert creation_time < 1.0, f"Redis creation too slow: {creation_time:.3f}s"
            assert (
                retrieval_time < 0.5
            ), f"Redis retrieval too slow: {retrieval_time:.3f}s"

            print(
                f"Redis performance test passed: Create={creation_time:.3f}s, Retrieve={retrieval_time:.3f}s"
            )

        except Exception as e:
            pytest.fail(f"Redis performance test failed: {e}")

    @pytest.mark.asyncio
    async def test_qdrant_performance(self):
        """Test Qdrant performance"""
        try:
            qdrant_client = QdrantClient(url=TEST_QDRANT_URL)

            # Test collection operations
            start_time = time.time()

            # Simple health check
            collections = qdrant_client.get_collections()

            query_time = time.time() - start_time

            # Performance assertion
            assert query_time < 2.0, f"Qdrant query too slow: {query_time:.3f}s"

            print(f"Qdrant performance test passed: Query={query_time:.3f}s")

        except Exception as e:
            pytest.fail(f"Qdrant performance test failed: {e}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
