"""
Tests for SOPHIAFlyMaster
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import requests
from sophia.core.fly_master import SOPHIAFlyMaster, FlyAppInfo, FlyReleaseInfo, FlyMachineInfo

class TestSOPHIAFlyMaster:
    """Test cases for SOPHIAFlyMaster."""

    def test_fly_master_initialization(self):
        """Test that Fly master initializes correctly with valid token."""
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            assert master.token == "test_token"
            assert "Authorization" in master.headers
            assert master.headers["Authorization"] == "Bearer test_token"

    def test_fly_master_initialization_no_token(self):
        """Test that Fly master raises error when no token is provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError, match="FLY_API_TOKEN or FLY_ACCESS_TOKEN is not set"):
                SOPHIAFlyMaster()

    def test_fly_master_uses_fly_access_token(self):
        """Test that Fly master can use FLY_ACCESS_TOKEN as fallback."""
        with patch.dict(os.environ, {"FLY_ACCESS_TOKEN": "access_token"}, clear=True):
            master = SOPHIAFlyMaster()
            assert master.token == "access_token"

    @patch('requests.post')
    def test_execute_graphql_query_success(self, mock_post):
        """Test successful GraphQL query execution."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {"test": "result"}
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            result = master._execute_graphql_query("query { test }")
            
            assert result == {"test": "result"}
            mock_post.assert_called_once()

    @patch('requests.post')
    def test_execute_graphql_query_with_errors(self, mock_post):
        """Test GraphQL query execution with errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "errors": [{"message": "Test error"}]
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            
            with pytest.raises(RuntimeError, match="GraphQL errors: Test error"):
                master._execute_graphql_query("query { test }")

    @patch.object(SOPHIAFlyMaster, '_execute_graphql_query')
    def test_get_apps_success(self, mock_query):
        """Test successful apps retrieval."""
        mock_query.return_value = {
            "apps": {
                "nodes": [
                    {
                        "name": "test-app",
                        "status": "running",
                        "platformVersion": "v2",
                        "hostname": "test-app.fly.dev",
                        "organization": {"slug": "test-org"},
                        "regions": [{"code": "ord"}]
                    },
                    {
                        "name": "another-app",
                        "status": "stopped",
                        "platformVersion": "v2",
                        "hostname": "another-app.fly.dev",
                        "organization": {"slug": "test-org"},
                        "regions": [{"code": "lax"}]
                    }
                ]
            }
        }
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            apps = master.get_apps()
            
            assert len(apps) == 2
            assert all(isinstance(app, FlyAppInfo) for app in apps)
            assert apps[0].name == "test-app"
            assert apps[0].status == "running"
            assert apps[0].region == "ord"

    @patch.object(SOPHIAFlyMaster, '_execute_graphql_query')
    def test_get_app_status_success(self, mock_query):
        """Test successful app status retrieval."""
        mock_query.return_value = {
            "app": {
                "name": "test-app",
                "status": "running",
                "hostname": "test-app.fly.dev",
                "platformVersion": "v2",
                "currentRelease": {
                    "id": "release123",
                    "version": 5,
                    "status": "succeeded",
                    "description": "Test release",
                    "createdAt": "2024-01-01T00:00:00Z"
                },
                "machines": {
                    "nodes": [
                        {
                            "id": "machine1",
                            "name": "test-machine",
                            "state": "started",
                            "region": "ord",
                            "instanceId": "instance1",
                            "privateIP": "192.168.1.1"
                        }
                    ]
                }
            }
        }
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            status = master.get_app_status("test-app")
            
            assert status["name"] == "test-app"
            assert status["status"] == "running"
            assert isinstance(status["current_release"], FlyReleaseInfo)
            assert status["current_release"].version == 5
            assert len(status["machines"]) == 1
            assert status["healthy_machines"] == 1

    @patch.object(SOPHIAFlyMaster, '_execute_graphql_query')
    def test_get_app_status_not_found(self, mock_query):
        """Test app status retrieval for non-existent app."""
        mock_query.return_value = {"app": None}
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            
            with pytest.raises(ValueError, match="App nonexistent-app not found"):
                master.get_app_status("nonexistent-app")

    @patch.object(SOPHIAFlyMaster, '_execute_graphql_query')
    @patch.object(SOPHIAFlyMaster, '_wait_for_deployment')
    def test_deploy_app_success(self, mock_wait, mock_query):
        """Test successful app deployment."""
        mock_query.return_value = {
            "deployImage": {
                "release": {
                    "id": "release456",
                    "version": 6,
                    "status": "pending",
                    "description": "New deployment",
                    "createdAt": "2024-01-01T01:00:00Z"
                }
            }
        }
        mock_wait.return_value = True
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            release_info = master.deploy_app("test-app", "test-image:latest")
            
            assert isinstance(release_info, FlyReleaseInfo)
            assert release_info.id == "release456"
            assert release_info.version == 6
            assert release_info.status == "pending"
            mock_wait.assert_called_once()

    @patch.object(SOPHIAFlyMaster, '_execute_graphql_query')
    def test_deploy_app_no_release_data(self, mock_query):
        """Test app deployment with no release data returned."""
        mock_query.return_value = {"deployImage": {}}
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            
            with pytest.raises(RuntimeError, match="No release data returned from deployment"):
                master.deploy_app("test-app", "test-image:latest")

    @patch.object(SOPHIAFlyMaster, '_execute_graphql_query')
    def test_scale_app_success(self, mock_query):
        """Test successful app scaling."""
        mock_query.return_value = {
            "scaleApp": {
                "app": {"name": "test-app"},
                "placement": {"count": 3, "region": "ord"}
            }
        }
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            result = master.scale_app("test-app", 3)
            
            assert result is True

    @patch.object(SOPHIAFlyMaster, '_execute_graphql_query')
    def test_scale_app_failure(self, mock_query):
        """Test app scaling failure."""
        mock_query.return_value = {}
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            
            with pytest.raises(RuntimeError, match="Scale operation failed"):
                master.scale_app("test-app", 3)

    @patch.object(SOPHIAFlyMaster, '_execute_graphql_query')
    def test_restart_app_success(self, mock_query):
        """Test successful app restart."""
        mock_query.return_value = {
            "restartApp": {
                "app": {"name": "test-app", "status": "running"}
            }
        }
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            result = master.restart_app("test-app")
            
            assert result is True

    @patch.object(SOPHIAFlyMaster, '_execute_graphql_query')
    def test_set_secrets_success(self, mock_query):
        """Test successful secrets setting."""
        mock_query.return_value = {
            "setSecrets": {
                "app": {"name": "test-app"}
            }
        }
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            secrets = {"API_KEY": "secret123", "DB_PASSWORD": "password456"}
            result = master.set_secrets("test-app", secrets)
            
            assert result is True

    @patch.object(SOPHIAFlyMaster, '_execute_graphql_query')
    def test_get_secrets_success(self, mock_query):
        """Test successful secrets retrieval."""
        mock_query.return_value = {
            "app": {
                "secrets": [
                    {"name": "API_KEY", "digest": "abc123", "createdAt": "2024-01-01T00:00:00Z"},
                    {"name": "DB_PASSWORD", "digest": "def456", "createdAt": "2024-01-01T00:00:00Z"}
                ]
            }
        }
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            secrets = master.get_secrets("test-app")
            
            assert secrets == ["API_KEY", "DB_PASSWORD"]

    @patch.object(SOPHIAFlyMaster, '_execute_graphql_query')
    def test_get_secrets_app_not_found(self, mock_query):
        """Test secrets retrieval for non-existent app."""
        mock_query.return_value = {"app": None}
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            
            with pytest.raises(ValueError, match="App nonexistent-app not found"):
                master.get_secrets("nonexistent-app")

    def test_get_logs_placeholder(self):
        """Test logs retrieval placeholder implementation."""
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            logs = master.get_logs("test-app", 5)
            
            assert len(logs) == 5
            assert all("test-app" in log for log in logs)

    @patch.object(SOPHIAFlyMaster, 'get_app_status')
    @patch('time.sleep')
    def test_wait_for_deployment_success(self, mock_sleep, mock_status):
        """Test successful deployment waiting."""
        # Mock successful deployment progression
        mock_status.side_effect = [
            {"current_release": FlyReleaseInfo("release123", 1, "pending", "", "")},
            {"current_release": FlyReleaseInfo("release123", 1, "succeeded", "", "")}
        ]
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            result = master._wait_for_deployment("test-app", "release123", timeout=60)
            
            assert result is True

    @patch.object(SOPHIAFlyMaster, 'get_app_status')
    @patch('time.sleep')
    def test_wait_for_deployment_failure(self, mock_sleep, mock_status):
        """Test deployment waiting with failure."""
        mock_status.return_value = {
            "current_release": FlyReleaseInfo("release123", 1, "failed", "", "")
        }
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            
            with pytest.raises(RuntimeError, match="Deployment release123 failed"):
                master._wait_for_deployment("test-app", "release123", timeout=60)

    @patch.object(SOPHIAFlyMaster, 'get_apps')
    def test_health_check_success(self, mock_get_apps):
        """Test successful health check."""
        mock_get_apps.return_value = [
            FlyAppInfo("app1", "running", "ord", "v2", "app1.fly.dev"),
            FlyAppInfo("app2", "stopped", "lax", "v2", "app2.fly.dev")
        ]
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            health = master.health_check()
            
            assert health["status"] == "healthy"
            assert health["apps_count"] == 2
            assert health["api_accessible"] is True

    @patch.object(SOPHIAFlyMaster, 'get_apps')
    def test_health_check_failure(self, mock_get_apps):
        """Test health check with API failure."""
        mock_get_apps.side_effect = Exception("API connection failed")
        
        with patch.dict(os.environ, {"FLY_API_TOKEN": "test_token"}):
            master = SOPHIAFlyMaster()
            health = master.health_check()
            
            assert health["status"] == "unhealthy"
            assert health["api_accessible"] is False
            assert "API connection failed" in health["error"]

    def test_fly_app_info_dataclass(self):
        """Test FlyAppInfo dataclass functionality."""
        app_info = FlyAppInfo(
            name="test-app",
            status="running",
            region="ord",
            platform_version="v2",
            hostname="test-app.fly.dev"
        )
        
        assert app_info.name == "test-app"
        assert app_info.status == "running"
        assert app_info.region == "ord"

    def test_fly_release_info_dataclass(self):
        """Test FlyReleaseInfo dataclass functionality."""
        release_info = FlyReleaseInfo(
            id="release123",
            version=5,
            status="succeeded",
            description="Test release",
            created_at="2024-01-01T00:00:00Z"
        )
        
        assert release_info.id == "release123"
        assert release_info.version == 5
        assert release_info.status == "succeeded"

    def test_fly_machine_info_dataclass(self):
        """Test FlyMachineInfo dataclass functionality."""
        machine_info = FlyMachineInfo(
            id="machine123",
            name="test-machine",
            state="started",
            region="ord",
            instance_id="instance123",
            private_ip="192.168.1.1"
        )
        
        assert machine_info.id == "machine123"
        assert machine_info.name == "test-machine"
        assert machine_info.state == "started"

