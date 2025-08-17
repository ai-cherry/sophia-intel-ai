"""
Unit tests for SOPHIA Intel MCP Server
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import json
import os

# Set test environment variables
os.environ["LAMBDA_API_KEY"] = "test_api_key"
os.environ["MCP_AUTH_TOKEN"] = "test_mcp_token"

from mcp_server import app
from lambda_client import LambdaLabsClient, SERVERS

client = TestClient(app)

class TestMCPServer:
    """Test suite for MCP Server endpoints"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.auth_headers = {"X-MCP-Token": "test_mcp_token"}
        self.mock_lambda_response = {
            "data": [
                {
                    "id": "07c099ae5ceb48ffaccd5c91b0560c0e",
                    "status": "active",
                    "instance_type": {"name": "gpu_1x_gh200"},
                    "region": {"name": "us-east-3"},
                    "ip": "192.222.51.223",
                    "hostname": "test-hostname"
                },
                {
                    "id": "9095c29b3292440fb81136810b0785a3",
                    "status": "active", 
                    "instance_type": {"name": "gpu_1x_gh200"},
                    "region": {"name": "us-east-3"},
                    "ip": "192.222.50.242",
                    "hostname": "test-hostname-2"
                }
            ]
        }
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "SOPHIA Intel MCP Server"
        assert "lambda_servers" in data
        assert "environment" in data
        assert "lambda_client_ready" in data
        assert "auth_enabled" in data
    
    def test_health_endpoint_no_auth_required(self):
        """Test that health endpoint doesn't require authentication"""
        response = client.get("/health")
        assert response.status_code == 200
    
    @patch('mcp_server.lambda_client')
    def test_list_servers_success(self, mock_client):
        """Test successful server listing"""
        mock_client.get_instances.return_value = self.mock_lambda_response
        
        response = client.get("/servers", headers=self.auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "servers" in data
        assert "total" in data
        assert len(data["servers"]) == 2
        
        # Check server data structure
        server = data["servers"][0]
        assert "key" in server
        assert "id" in server
        assert "name" in server
        assert "ip" in server
        assert "role" in server
        assert "inference_url" in server
        assert "status" in server
    
    def test_list_servers_no_auth(self):
        """Test server listing without authentication"""
        response = client.get("/servers")
        assert response.status_code == 401
        assert "Invalid or missing X-MCP-Token header" in response.json()["detail"]
    
    @patch('mcp_server.lambda_client')
    def test_list_servers_lambda_error(self, mock_client):
        """Test server listing when Lambda API fails"""
        mock_client.get_instances.side_effect = Exception("Lambda API error")
        
        response = client.get("/servers", headers=self.auth_headers)
        assert response.status_code == 500
        assert "Failed to list servers" in response.json()["detail"]
    
    @patch('mcp_server.lambda_client')
    def test_start_server_success(self, mock_client):
        """Test successful server start"""
        mock_client.start_instance.return_value = {"status": "starting"}
        
        response = client.post("/servers/primary/start", headers=self.auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["server"] == "primary"
        assert data["action"] == "start"
        assert data["status"] == "success"
        assert "instance_id" in data
    
    def test_start_server_invalid_key(self):
        """Test starting non-existent server"""
        response = client.post("/servers/invalid/start", headers=self.auth_headers)
        assert response.status_code == 404
        assert "Server 'invalid' not found" in response.json()["detail"]
    
    @patch('mcp_server.lambda_client')
    def test_start_server_lambda_error(self, mock_client):
        """Test server start when Lambda API fails"""
        mock_client.start_instance.side_effect = Exception("Start failed")
        
        response = client.post("/servers/primary/start", headers=self.auth_headers)
        assert response.status_code == 500
        assert "Failed to start server" in response.json()["detail"]
    
    @patch('mcp_server.lambda_client')
    def test_stop_server_success(self, mock_client):
        """Test successful server stop"""
        mock_client.stop_instance.return_value = {"status": "stopping"}
        
        response = client.post("/servers/primary/stop", headers=self.auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["server"] == "primary"
        assert data["action"] == "stop"
        assert data["status"] == "success"
    
    @patch('mcp_server.lambda_client')
    def test_restart_server_success(self, mock_client):
        """Test successful server restart"""
        mock_client.restart_instance.return_value = {"status": "restarting"}
        
        response = client.post("/servers/secondary/restart", headers=self.auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["server"] == "secondary"
        assert data["action"] == "restart"
        assert data["status"] == "success"
    
    @patch('mcp_server.lambda_client')
    def test_get_server_stats(self, mock_client):
        """Test getting server statistics"""
        mock_stats = {
            "instance_id": "07c099ae5ceb48ffaccd5c91b0560c0e",
            "status": "active",
            "gpu_utilization": "N/A",
            "memory_usage": "N/A"
        }
        mock_client.get_instance_stats.return_value = mock_stats
        
        response = client.get("/servers/primary/stats", headers=self.auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["server"] == "primary"
        assert "stats" in data
        assert "config" in data
    
    @patch('mcp_server.lambda_client')
    def test_get_server_details(self, mock_client):
        """Test getting detailed server information"""
        mock_instance = {"data": {"id": "07c099ae5ceb48ffaccd5c91b0560c0e", "status": "active"}}
        mock_stats = {"gpu_utilization": "N/A"}
        
        mock_client.get_instance.return_value = mock_instance
        mock_client.get_instance_stats.return_value = mock_stats
        
        response = client.get("/servers/primary", headers=self.auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["server"] == "primary"
        assert "config" in data
        assert "instance" in data
        assert "stats" in data
    
    @patch('mcp_server.lambda_client')
    def test_rename_servers_success(self, mock_client):
        """Test successful server renaming"""
        mock_client.rename_instance.return_value = {"status": "success"}
        
        response = client.post("/servers/rename", headers=self.auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "rename_results" in data
        assert "total" in data
        assert len(data["rename_results"]) == len(SERVERS)
    
    @patch('mcp_server.lambda_client')
    def test_rename_servers_partial_failure(self, mock_client):
        """Test server renaming with some failures"""
        def mock_rename(instance_id, name):
            if "primary" in name:
                return {"status": "success"}
            else:
                raise Exception("Rename failed")
        
        mock_client.rename_instance.side_effect = mock_rename
        
        response = client.post("/servers/rename", headers=self.auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        results = data["rename_results"]
        
        # Should have both success and error results
        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = sum(1 for r in results if r["status"] == "error")
        
        assert success_count > 0
        assert error_count > 0

class TestLambdaClient:
    """Test suite for Lambda Labs client"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.mock_response_data = {
            "data": [
                {
                    "id": "test-instance-id",
                    "status": "active",
                    "instance_type": {"name": "gpu_1x_gh200"},
                    "region": {"name": "us-east-3"}
                }
            ]
        }
    
    def test_client_initialization_no_api_key(self):
        """Test client initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="LAMBDA_API_KEY environment variable is required"):
                LambdaLabsClient()
    
    @patch('lambda_client.requests.get')
    def test_get_instances_success(self, mock_get):
        """Test successful instance retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = self.mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = LambdaLabsClient()
        result = client.get_instances()
        
        assert result == self.mock_response_data
        mock_get.assert_called_once()
    
    @patch('lambda_client.requests.get')
    def test_get_instances_api_error(self, mock_get):
        """Test instance retrieval with API error"""
        mock_get.side_effect = Exception("API Error")
        
        client = LambdaLabsClient()
        with pytest.raises(Exception):
            client.get_instances()
    
    @patch('lambda_client.requests.post')
    def test_start_instance_success(self, mock_post):
        """Test successful instance start"""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "starting"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        client = LambdaLabsClient()
        result = client.start_instance("test-instance-id")
        
        assert result["status"] == "starting"
        mock_post.assert_called_once()
    
    @patch('lambda_client.requests.post')
    def test_stop_instance_success(self, mock_post):
        """Test successful instance stop"""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "stopping"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        client = LambdaLabsClient()
        result = client.stop_instance("test-instance-id")
        
        assert result["status"] == "stopping"
        mock_post.assert_called_once()

class TestServerConfiguration:
    """Test suite for server configuration loading"""
    
    def test_get_server_config_from_env(self):
        """Test loading server config from environment variable"""
        test_config = {
            "test_server": {
                "id": "test-id",
                "ip": "192.168.1.1",
                "name": "test-server",
                "role": "testing"
            }
        }
        
        with patch.dict(os.environ, {"LAMBDA_SERVERS_JSON": json.dumps(test_config)}):
            from lambda_client import get_server_config
            config = get_server_config()
            assert config == test_config
    
    def test_get_server_config_invalid_json(self):
        """Test handling of invalid JSON in environment variable"""
        with patch.dict(os.environ, {"LAMBDA_SERVERS_JSON": "invalid json"}):
            from lambda_client import get_server_config
            config = get_server_config()
            
            # Should fall back to default config
            assert "primary" in config
            assert "secondary" in config
    
    def test_get_server_config_default(self):
        """Test default server configuration"""
        with patch.dict(os.environ, {}, clear=True):
            from lambda_client import get_server_config
            config = get_server_config()
            
            assert "primary" in config
            assert "secondary" in config
            assert config["primary"]["id"] == "07c099ae5ceb48ffaccd5c91b0560c0e"
            assert config["secondary"]["id"] == "9095c29b3292440fb81136810b0785a3"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

