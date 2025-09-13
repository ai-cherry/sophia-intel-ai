"""
MCP Servers Integration Tests
Tests all 8 unified MCP servers for functionality and health
"""
import asyncio
import os
import httpx
import pytest
from dotenv import load_dotenv
# Load environment variables
load_dotenv(".env.production")
class TestMCPServersIntegration:
    @pytest.fixture
    def mcp_base_url(self):
        """Get MCP base URL"""
        return os.getenv("MCP_URL", "http://localhost:8001")
    @pytest.fixture
    def client(self):
        """Create HTTP client for MCP API"""
        return httpx.AsyncClient(timeout=30.0)
    @pytest.mark.asyncio
    async def test_mcp_gateway_health(self, client, mcp_base_url):
        """Test MCP gateway health endpoint"""
        try:
            response = await client.get(f"{mcp_base_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"
            print("✅ MCP Gateway health check successful")
        except Exception as e:
            pytest.fail(f"MCP Gateway health check failed: {e}")
    @pytest.mark.asyncio
    async def test_unified_mcp_servers_list(self, client, mcp_base_url):
        """Test listing all unified MCP servers"""
        try:
            response = await client.get(f"{mcp_base_url}/servers")
            assert response.status_code == 200
            servers = response.json()
            assert isinstance(servers, list)
            assert len(servers) == 8  # Should have 8 unified servers
            expected_servers = [
                "sophia-core",
                "github-integration",
                "gong-crm",
                "hubspot-integration",
                "knowledge-base",
                "monitoring",
                "super-memory",
                "enterprise-tools",
            ]
            server_names = [server["name"] for server in servers]
            for expected in expected_servers:
                assert expected in server_names, f"Missing server: {expected}"
            print(f"✅ MCP Servers list successful - {len(servers)} servers found")
        except Exception as e:
            pytest.fail(f"MCP Servers list failed: {e}")
    @pytest.mark.asyncio
    async def test_sophia_core_server(self, client, mcp_base_url):
        """Test Sophia Core MCP server"""
        try:
            # Test server health
            response = await client.get(f"{mcp_base_url}/servers/sophia-core/health")
            assert response.status_code == 200
            # Test chat functionality
            chat_response = await client.post(
                f"{mcp_base_url}/servers/sophia-core/chat",
                json={"message": "Hello Sophia Core", "context": {"test": True}},
            )
            assert chat_response.status_code == 200
            chat_data = chat_response.json()
            assert "response" in chat_data
            print("✅ Sophia Core MCP server working")
        except Exception as e:
            pytest.fail(f"Sophia Core MCP server failed: {e}")
    @pytest.mark.asyncio
    async def test_github_integration_server(self, client, mcp_base_url):
        """Test GitHub Integration MCP server"""
        try:
            # Test server health
            response = await client.get(
                f"{mcp_base_url}/servers/github-integration/health"
            )
            assert response.status_code == 200
            # Test repository listing (if GitHub token is available)
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                repos_response = await client.get(
                    f"{mcp_base_url}/servers/github-integration/repositories",
                    headers={"Authorization": f"Bearer {github_token}"},
                )
                assert repos_response.status_code == 200
                repos_data = repos_response.json()
                assert isinstance(repos_data, list)
            print("✅ GitHub Integration MCP server working")
        except Exception as e:
            pytest.fail(f"GitHub Integration MCP server failed: {e}")
    @pytest.mark.asyncio
    async def test_gong_crm_server(self, client, mcp_base_url):
        """Test Gong CRM MCP server"""
        try:
            # Test server health
            response = await client.get(f"{mcp_base_url}/servers/gong-crm/health")
            assert response.status_code == 200
            # Test Gong connection (if credentials are available)
            gong_key = os.getenv("GONG_ACCESS_KEY")
            gong_secret = os.getenv("GONG_CLIENT_SECRET")
            if gong_key and gong_secret:
                connection_response = await client.post(
                    f"{mcp_base_url}/servers/gong-crm/test-connection",
                    json={"access_key": gong_key, "client_secret": gong_secret},
                )
                # May return 200 or 401 depending on credentials
                assert connection_response.status_code in [200, 401]
            print("✅ Gong CRM MCP server working")
        except Exception as e:
            pytest.fail(f"Gong CRM MCP server failed: {e}")
    @pytest.mark.asyncio
    async def test_hubspot_integration_server(self, client, mcp_base_url):
        """Test HubSpot Integration MCP server"""
        try:
            # Test server health
            response = await client.get(
                f"{mcp_base_url}/servers/hubspot-integration/health"
            )
            assert response.status_code == 200
            # Test HubSpot connection (if API key is available)
            hubspot_key = os.getenv("HUBSPOT_API_KEY")
            if hubspot_key:
                connection_response = await client.post(
                    f"{mcp_base_url}/servers/hubspot-integration/test-connection",
                    json={"api_key": hubspot_key},
                )
                # May return 200 or 401 depending on credentials
                assert connection_response.status_code in [200, 401]
            print("✅ HubSpot Integration MCP server working")
        except Exception as e:
            pytest.fail(f"HubSpot Integration MCP server failed: {e}")
    @pytest.mark.asyncio
    async def test_knowledge_base_server(self, client, mcp_base_url):
        """Test Knowledge Base MCP server"""
        try:
            # Test server health
            response = await client.get(f"{mcp_base_url}/servers/knowledge-base/health")
            assert response.status_code == 200
            # Test knowledge search
            search_response = await client.post(
                f"{mcp_base_url}/servers/knowledge-base/search",
                json={"query": "test search", "limit": 5},
            )
            assert search_response.status_code == 200
            search_data = search_response.json()
            assert "results" in search_data
            print("✅ Knowledge Base MCP server working")
        except Exception as e:
            pytest.fail(f"Knowledge Base MCP server failed: {e}")
    @pytest.mark.asyncio
    async def test_monitoring_server(self, client, mcp_base_url):
        """Test Monitoring MCP server"""
        try:
            # Test server health
            response = await client.get(f"{mcp_base_url}/servers/monitoring/health")
            assert response.status_code == 200
            # Test metrics endpoint
            metrics_response = await client.get(
                f"{mcp_base_url}/servers/monitoring/metrics"
            )
            assert metrics_response.status_code == 200
            metrics_data = metrics_response.json()
            assert "system" in metrics_data
            assert "mcp_servers" in metrics_data
            print("✅ Monitoring MCP server working")
        except Exception as e:
            pytest.fail(f"Monitoring MCP server failed: {e}")
    @pytest.mark.asyncio
    async def test_super_memory_server(self, client, mcp_base_url):
        """Test Super Memory MCP server"""
        try:
            # Test server health
            response = await client.get(f"{mcp_base_url}/servers/super-memory/health")
            assert response.status_code == 200
            # Test memory storage
            store_response = await client.post(
                f"{mcp_base_url}/servers/super-memory/store",
                json={
                    "key": "test_memory",
                    "value": "integration test data",
                    "ttl": 300,
                },
            )
            assert store_response.status_code == 200
            # Test memory retrieval
            retrieve_response = await client.get(
                f"{mcp_base_url}/servers/super-memory/retrieve/test_memory"
            )
            assert retrieve_response.status_code == 200
            retrieve_data = retrieve_response.json()
            assert retrieve_data["value"] == "integration test data"
            print("✅ Super Memory MCP server working")
        except Exception as e:
            pytest.fail(f"Super Memory MCP server failed: {e}")
    @pytest.mark.asyncio
    async def test_enterprise_tools_server(self, client, mcp_base_url):
        """Test Enterprise Tools MCP server"""
        try:
            # Test server health
            response = await client.get(
                f"{mcp_base_url}/servers/enterprise-tools/health"
            )
            assert response.status_code == 200
            # Test tools listing
            tools_response = await client.get(
                f"{mcp_base_url}/servers/enterprise-tools/tools"
            )
            assert tools_response.status_code == 200
            tools_data = tools_response.json()
            assert isinstance(tools_data, list)
            assert len(tools_data) > 0
            print("✅ Enterprise Tools MCP server working")
        except Exception as e:
            pytest.fail(f"Enterprise Tools MCP server failed: {e}")
    @pytest.mark.asyncio
    async def test_mcp_servers_performance(self, client, mcp_base_url):
        """Test MCP servers performance and response times"""
        try:
            import time
            # Test concurrent health checks
            start_time = time.time()
            servers = [
                "sophia-core",
                "github-integration",
                "gong-crm",
                "hubspot-integration",
                "knowledge-base",
                "monitoring",
                "super-memory",
                "enterprise-tools",
            ]
            tasks = []
            for server in servers:
                task = client.get(f"{mcp_base_url}/servers/{server}/health")
                tasks.append(task)
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            # Check that most servers responded successfully
            successful_responses = [
                r
                for r in responses
                if not isinstance(r, Exception) and r.status_code == 200
            ]
            success_rate = len(successful_responses) / len(servers)
            print("✅ MCP Servers performance test completed:")
            print(f"   Total time: {total_time:.3f}s for {len(servers)} servers")
            print(
                f"   Success rate: {success_rate:.1%} ({len(successful_responses)}/{len(servers)})"
            )
            print(
                f"   Average response time: {total_time/len(servers):.3f}s per server"
            )
            # Assert reasonable performance
            assert total_time < 10.0, f"MCP servers too slow: {total_time}s"
            assert (
                success_rate >= 0.75
            ), f"Too many MCP server failures: {success_rate:.1%}"
        except Exception as e:
            pytest.fail(f"MCP servers performance test failed: {e}")
    @pytest.mark.asyncio
    async def test_mcp_heartbeat_monitoring(self, client, mcp_base_url):
        """Test MCP heartbeat monitoring system"""
        try:
            # Test heartbeat endpoint
            response = await client.get(f"{mcp_base_url}/heartbeat")
            assert response.status_code == 200
            heartbeat_data = response.json()
            assert "timestamp" in heartbeat_data
            assert "servers" in heartbeat_data
            assert "latency" in heartbeat_data
            # Check that latency is reasonable (should be improved by 45%)
            latency = heartbeat_data["latency"]
            assert latency < 2.0, f"MCP heartbeat latency too high: {latency}s"
            print(f"✅ MCP Heartbeat monitoring working - latency: {latency:.3f}s")
        except Exception as e:
            pytest.fail(f"MCP heartbeat monitoring failed: {e}")
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
