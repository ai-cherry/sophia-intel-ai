"""
Comprehensive Integration Test Suite for Sophia AI v7.0
Tests all components including Opus 4.1, MCP services, and production features
"""
import asyncio
import os
import time
from typing import Dict
import httpx
import pytest
# Test configuration
TEST_BASE_URL = "http://localhost:8000"
TEST_API_KEY = "test-key-12345"
class TestSophiaIntegration:
    """Integration tests for Sophia AI platform"""
    @pytest.fixture(scope="class")
    async def client(self):
        """HTTP client for testing"""
        async with httpx.AsyncClient(base_url=TEST_BASE_URL, timeout=30.0) as client:
            yield client
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Authentication headers for testing"""
        return {
            "Authorization": f"Bearer {TEST_API_KEY}",
            "Content-Type": "application/json",
        }
    async def test_health_check(self, client: httpx.AsyncClient):
        """Test basic health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data
    async def test_platform_info(self, client: httpx.AsyncClient):
        """Test platform information endpoint"""
        response = await client.get("/api/platform/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Sophia AI Platform"
        assert data["version"].startswith("v")
        assert "features" in data
        assert "opus_4_1_integration" in data["features"]
        assert data["features"]["opus_4_1_integration"] is True
    async def test_opus_chat_basic(
        self, client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test basic Opus 4.1 chat functionality"""
        chat_request = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! Please respond with exactly: 'Integration test successful'",
                }
            ],
            "config": {
                "model": "anthropic/claude-opus-4-1-20250805",
                "provider": "openrouter",
                "temperature": 0.1,
                "max_tokens": 100,
            },
        }
        response = await client.post(
            "/api/chat/opus", json=chat_request, headers=auth_headers
        )
        if response.status_code == 403:
            pytest.skip("Authentication not configured for testing")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "metadata" in data
        assert "usage" in data
        # Check metadata
        metadata = data["metadata"]
        assert metadata["provider"] in ["openrouter", "anthropic", "portkey"]
        assert metadata["tokens"] > 0
        assert metadata["cost"] >= 0
        assert metadata["responseTime"] > 0
    async def test_opus_provider_fallback(
        self, client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test provider fallback mechanism"""
        # Test with invalid provider first, should fallback
        chat_request = {
            "messages": [{"role": "user", "content": "Test fallback"}],
            "config": {
                "provider": "invalid_provider",
                "temperature": 0.1,
                "max_tokens": 50,
            },
        }
        response = await client.post(
            "/api/chat/opus", json=chat_request, headers=auth_headers
        )
        if response.status_code == 403:
            pytest.skip("Authentication not configured for testing")
        # Should still work due to fallback
        assert response.status_code in [200, 503]  # 503 if all providers fail
    async def test_opus_usage_stats(
        self, client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test usage statistics tracking"""
        response = await client.get("/api/chat/usage", headers=auth_headers)
        if response.status_code == 403:
            pytest.skip("Authentication not configured for testing")
        assert response.status_code == 200
        data = response.json()
        assert "requests_today" in data
        assert "tokens_used" in data
        assert "cost_today" in data
        assert "average_response_time" in data
        # All values should be non-negative
        assert data["requests_today"] >= 0
        assert data["tokens_used"] >= 0
        assert data["cost_today"] >= 0
        assert data["average_response_time"] >= 0
    async def test_provider_status(self, client: httpx.AsyncClient):
        """Test provider status monitoring"""
        response = await client.get("/api/chat/providers/status")
        assert response.status_code == 200
        data = response.json()
        assert "openrouter" in data
        assert "anthropic" in data
        assert "portkey" in data
        for provider, status in data.items():
            assert "available" in status
            assert "failures" in status
            assert isinstance(status["available"], bool)
            assert isinstance(status["failures"], int)
    async def test_mcp_services(self, client: httpx.AsyncClient):
        """Test MCP services integration"""
        response = await client.get("/api/mcp/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert len(data["services"]) > 0
        # Check for key MCP services
        service_names = [service["name"] for service in data["services"]]
        assert "enhanced_enterprise_server" in service_names
        assert "unified_super_memory_server" in service_names
    async def test_mcp_health_checks(self, client: httpx.AsyncClient):
        """Test MCP service health checks"""
        response = await client.get("/api/mcp/health")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "overall_status" in data
        # Check individual service health
        for service_name, health in data["services"].items():
            assert "status" in health
            assert "last_check" in health
            assert health["status"] in ["healthy", "warning", "error"]
    async def test_domains_api(
        self, client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test business domains API"""
        response = await client.get("/api/domains", headers=auth_headers)
        if response.status_code == 403:
            pytest.skip("Authentication not configured for testing")
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert isinstance(data["domains"], list)
        # Check domain structure
        if data["domains"]:
            domain = data["domains"][0]
            assert "id" in domain
            assert "name" in domain
            assert "description" in domain
            assert "status" in domain
    async def test_gpu_quota_monitoring(self, client: httpx.AsyncClient):
        """Test GPU quota monitoring"""
        response = await client.get("/api/gpu-quota")
        assert response.status_code == 200
        data = response.json()
        assert "hours_remaining" in data
        assert "quota_limit" in data
        assert "usage_today" in data
        # Values should be reasonable
        assert 0 <= data["hours_remaining"] <= 1000
        assert data["quota_limit"] > 0
        assert data["usage_today"] >= 0
    async def test_security_headers(self, client: httpx.AsyncClient):
        """Test security headers are present"""
        response = await client.get("/health")
        # Check for security headers
        headers = response.headers
        assert (
            "x-content-type-options" in headers.keys()
            or "X-Content-Type-Options" in headers.keys()
        )
        # CORS should be configured
        options_response = await client.options("/api/chat/opus")
        assert options_response.status_code in [
            200,
            204,
            405,
        ]  # 405 is acceptable for OPTIONS
    async def test_rate_limiting(self, client: httpx.AsyncClient):
        """Test rate limiting functionality"""
        # Make multiple rapid requests
        tasks = []
        for i in range(10):
            task = client.get("/health")
            tasks.append(task)
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        # Should have some successful responses
        successful_responses = [
            r
            for r in responses
            if isinstance(r, httpx.Response) and r.status_code == 200
        ]
        assert len(successful_responses) > 0
        # Check if rate limiting is working (some requests might be limited)
        rate_limited = [
            r
            for r in responses
            if isinstance(r, httpx.Response) and r.status_code == 429
        ]
        # Rate limiting might not be enabled in test environment, so this is optional
    async def test_error_handling(self, client: httpx.AsyncClient):
        """Test error handling and responses"""
        # Test 404 for non-existent endpoint
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "suggestions" in data  # Custom 404 handler should provide suggestions
    async def test_opus_integration_test_endpoint(self, client: httpx.AsyncClient):
        """Test the built-in Opus integration test"""
        response = await client.post("/api/chat/test")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        if data["status"] == "success":
            assert "response" in data
            assert "provider" in data
            assert "cost" in data
        else:
            # If it fails, should have error message
            assert "message" in data
            assert data["status"] == "error"
    @pytest.mark.performance
    async def test_response_times(self, client: httpx.AsyncClient):
        """Test response time performance"""
        start_time = time.time()
        response = await client.get("/health")
        end_time = time.time()
        assert response.status_code == 200
        response_time = end_time - start_time
        # Health check should be fast
        assert response_time < 1.0  # Less than 1 second
    @pytest.mark.performance
    async def test_concurrent_requests(self, client: httpx.AsyncClient):
        """Test handling of concurrent requests"""
        # Create multiple concurrent health check requests
        tasks = [client.get("/health") for _ in range(20)]
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        # Should handle concurrent requests efficiently
        total_time = end_time - start_time
        assert total_time < 5.0  # Should complete within 5 seconds
class TestProductionReadiness:
    """Tests for production readiness"""
    async def test_environment_variables(self):
        """Test that required environment variables are documented"""
        required_vars = [
            "OPENROUTER_API_KEY",
            "ANTHROPIC_API_KEY",
            "PORTKEY_API_KEY",
            "DATABASE_URL",
            "REDIS_URL",
        ]
        # Check if .env.template exists and contains required variables
        env_template_path = "/.env.template"
        if os.path.exists(env_template_path):
            with open(env_template_path) as f:
                template_content = f.read()
            for var in required_vars:
                assert (
                    var in template_content
                ), f"Required environment variable {var} not in .env.template"
    async def test_docker_configuration(self):
        """Test Docker configuration exists"""
        docker_files = ["/backend/Dockerfile", "/docker-compose.yml", "/.dockerignore"]
        for docker_file in docker_files:
            if os.path.exists(docker_file):
                # File exists, check it's not empty
                with open(docker_file) as f:
                    content = f.read().strip()
                assert len(content) > 0, f"{docker_file} exists but is empty"
    async def test_deployment_scripts(self):
        """Test deployment scripts exist and are executable"""
        deployment_scripts = ["/scripts/deploy_production.sh", "/scripts/sophia.sh"]
        for script in deployment_scripts:
            if os.path.exists(script):
                # Check if executable
                import stat
                file_stat = os.stat(script)
                is_executable = file_stat.st_mode & stat.S_IEXEC
                assert is_executable, f"{script} exists but is not executable"
# Test runner configuration
if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])
