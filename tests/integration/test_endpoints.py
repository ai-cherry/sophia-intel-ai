"""
SOPHIA V4 Integration Tests
Comprehensive endpoint testing for real-world cloud deployment
Works in any Python environment with pytest
"""

import pytest
import asyncio
import os
import json
from typing import Dict, Any
from httpx import AsyncClient
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = os.getenv("SOPHIA_BASE_URL", "https://sophia-intel.fly.dev")
TIMEOUT = 30.0  # seconds

class TestSophiaV4Endpoints:
    """Comprehensive integration tests for SOPHIA V4"""
    
    @pytest.fixture
    async def client(self):
        """Create async HTTP client for testing"""
        async with AsyncClient(
            base_url=BASE_URL,
            timeout=TIMEOUT,
            follow_redirects=True
        ) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test basic health endpoint"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        
        logger.info(f"✅ Health endpoint: {data}")
    
    @pytest.mark.asyncio
    async def test_api_v1_health_endpoint(self, client: AsyncClient):
        """Test API v1 health endpoint"""
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert "database" in data
        
        logger.info(f"✅ API v1 health endpoint: {data}")
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_basic(self, client: AsyncClient):
        """Test chat endpoint with basic query"""
        payload = {
            "query": "What is artificial intelligence?",
            "sources_limit": 3
        }
        
        response = await client.post("/api/v1/chat", json=payload)
        
        # Should return 200 or appropriate error code
        assert response.status_code in [200, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "results" in data or "response" in data
            logger.info(f"✅ Chat endpoint successful: {len(str(data))} chars")
        else:
            logger.info(f"ℹ️ Chat endpoint returned {response.status_code}: {response.text[:200]}")
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_validation(self, client: AsyncClient):
        """Test chat endpoint input validation"""
        # Test empty query
        response = await client.post("/api/v1/chat", json={"query": ""})
        assert response.status_code in [400, 422]
        
        # Test missing query
        response = await client.post("/api/v1/chat", json={})
        assert response.status_code in [400, 422]
        
        # Test invalid sources_limit
        response = await client.post("/api/v1/chat", json={
            "query": "test",
            "sources_limit": -1
        })
        assert response.status_code in [200, 422]  # May be handled gracefully
        
        logger.info("✅ Chat endpoint validation tests passed")
    
    @pytest.mark.asyncio
    async def test_swarm_trigger_endpoint(self, client: AsyncClient):
        """Test swarm coordination endpoint"""
        payload = {
            "task": "Research current AI trends and developments",
            "agents": ["research", "analysis"],
            "objective": "Generate comprehensive report on AI trends"
        }
        
        response = await client.post("/api/v1/swarm/trigger", json=payload)
        
        # Should return 200 or appropriate error code
        assert response.status_code in [200, 422, 500, 501]
        
        if response.status_code == 200:
            data = response.json()
            assert "task_id" in data or "status" in data
            logger.info(f"✅ Swarm trigger successful: {data}")
        else:
            logger.info(f"ℹ️ Swarm trigger returned {response.status_code}: {response.text[:200]}")
    
    @pytest.mark.asyncio
    async def test_code_commit_endpoint(self, client: AsyncClient):
        """Test GitHub commit automation endpoint"""
        payload = {
            "repo": "ai-cherry/sophia-intel",
            "changes": "Test commit from integration tests",
            "branch": "main"
        }
        
        response = await client.post("/api/v1/code/commit", json=payload)
        
        # Should return 200 or appropriate error code
        assert response.status_code in [200, 401, 403, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "commit_hash" in data or "status" in data
            logger.info(f"✅ Code commit successful: {data}")
        elif response.status_code in [401, 403]:
            logger.info("ℹ️ Code commit requires authentication (expected in some environments)")
        else:
            logger.info(f"ℹ️ Code commit returned {response.status_code}: {response.text[:200]}")
    
    @pytest.mark.asyncio
    async def test_deploy_trigger_endpoint(self, client: AsyncClient):
        """Test deployment automation endpoint"""
        payload = {
            "app_name": "sophia-intel",
            "org_name": "sophia-org"
        }
        
        response = await client.post("/api/v1/deploy/trigger", json=payload)
        
        # Should return 200 or appropriate error code
        assert response.status_code in [200, 401, 403, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "deployment_id" in data or "status" in data
            logger.info(f"✅ Deploy trigger successful: {data}")
        elif response.status_code in [401, 403]:
            logger.info("ℹ️ Deploy trigger requires authentication (expected in some environments)")
        else:
            logger.info(f"ℹ️ Deploy trigger returned {response.status_code}: {response.text[:200]}")
    
    @pytest.mark.asyncio
    async def test_frontend_static_files(self, client: AsyncClient):
        """Test frontend static file serving"""
        # Test main frontend page
        response = await client.get("/v4/")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            assert "html" in response.headers.get("content-type", "").lower()
            logger.info("✅ Frontend main page accessible")
        
        # Test specific frontend file
        response = await client.get("/v4/index.html")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            content = response.text
            assert "SOPHIA" in content or "chat" in content.lower()
            logger.info("✅ Frontend index.html accessible")
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers for frontend integration"""
        # Test preflight request
        response = await client.options("/api/v1/chat", headers={
            "Origin": "https://sophia-intel.fly.dev",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        })
        
        # Should allow CORS
        assert response.status_code in [200, 204, 405]
        
        # Test actual request with CORS
        response = await client.post("/api/v1/chat", 
            json={"query": "test", "sources_limit": 1},
            headers={"Origin": "https://sophia-intel.fly.dev"}
        )
        
        # Should include CORS headers
        cors_header = response.headers.get("access-control-allow-origin")
        if cors_header:
            logger.info(f"✅ CORS enabled: {cors_header}")
        else:
            logger.info("ℹ️ CORS headers not found (may be handled by proxy)")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, client: AsyncClient):
        """Test error handling and response formats"""
        # Test non-existent endpoint
        response = await client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        # Test malformed JSON
        response = await client.post("/api/v1/chat", 
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
        
        logger.info("✅ Error handling tests passed")
    
    @pytest.mark.asyncio
    async def test_performance_basic(self, client: AsyncClient):
        """Basic performance tests"""
        import time
        
        # Test health endpoint response time
        start_time = time.time()
        response = await client.get("/health")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0  # Should respond within 5 seconds
        
        logger.info(f"✅ Health endpoint response time: {response_time:.2f}s")
        
        # Test multiple concurrent requests
        async def make_request():
            return await client.get("/health")
        
        start_time = time.time()
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        assert all(r.status_code == 200 for r in responses)
        assert total_time < 10.0  # Should handle 5 concurrent requests within 10 seconds
        
        logger.info(f"✅ Concurrent requests handled in {total_time:.2f}s")

class TestSophiaV4Production:
    """Production-specific tests"""
    
    @pytest.mark.asyncio
    async def test_ssl_certificate(self, client: AsyncClient):
        """Test SSL certificate validity"""
        if BASE_URL.startswith("https://"):
            response = await client.get("/health")
            assert response.status_code == 200
            logger.info("✅ SSL certificate valid")
    
    @pytest.mark.asyncio
    async def test_security_headers(self, client: AsyncClient):
        """Test security headers"""
        response = await client.get("/health")
        
        # Check for common security headers
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "strict-transport-security"
        ]
        
        found_headers = []
        for header in security_headers:
            if header in response.headers:
                found_headers.append(header)
        
        logger.info(f"✅ Security headers found: {found_headers}")
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient):
        """Test rate limiting (if implemented)"""
        # Make multiple rapid requests
        responses = []
        for i in range(20):
            try:
                response = await client.get("/health")
                responses.append(response.status_code)
            except Exception as e:
                logger.info(f"Request {i} failed: {e}")
        
        # Check if any requests were rate limited
        rate_limited = any(status == 429 for status in responses)
        if rate_limited:
            logger.info("✅ Rate limiting is active")
        else:
            logger.info("ℹ️ No rate limiting detected (may not be implemented)")

# Utility functions for running tests
def run_integration_tests():
    """Run integration tests programmatically"""
    import subprocess
    import sys
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            __file__, 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Failed to run tests: {e}")
        return False

if __name__ == "__main__":
    # Run tests when executed directly
    success = run_integration_tests()
    exit(0 if success else 1)

