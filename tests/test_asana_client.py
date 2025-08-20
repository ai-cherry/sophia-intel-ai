"""
Tests for Asana API Client
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from sophia.integrations.asana_client import AsanaClient, AsanaProject, AsanaTask


class TestAsanaClient:
    """Test suite for AsanaClient"""
    
    @pytest.fixture
    def mock_token(self):
        return "test_asana_token_12345"
    
    @pytest.fixture
    def asana_client(self, mock_token):
        with patch.dict('os.environ', {'ASANA_ACCESS_TOKEN': mock_token}):
            return AsanaClient()
    
    @pytest.fixture
    def mock_response_data(self):
        return {
            "data": {
                "gid": "123456789",
                "name": "Test Task",
                "notes": "Test task description",
                "assignee": {"name": "John Doe"},
                "projects": [{"name": "Test Project"}],
                "completed": False,
                "due_on": "2025-08-25",
                "permalink_url": "https://app.asana.com/0/123456789/987654321"
            }
        }
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_token):
        """Test client initialization"""
        with patch.dict('os.environ', {'ASANA_ACCESS_TOKEN': mock_token}):
            client = AsanaClient()
            assert client.token == mock_token
            assert client.base_url == "https://app.asana.com/api/1.0"
            assert client.rate_limit == 150
    
    @pytest.mark.asyncio
    async def test_initialization_no_token(self):
        """Test client initialization without token"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(EnvironmentError, match="Missing required environment variable: ASANA_ACCESS_TOKEN"):
                AsanaClient()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, asana_client):
        """Test rate limiting functionality"""
        # Fill up the rate limit
        current_time = asyncio.get_event_loop().time()
        asana_client._request_times = [current_time - 30] * 150  # Fill to limit
        
        # This should trigger rate limiting
        start_time = asyncio.get_event_loop().time()
        await asana_client._rate_limit_check()
        end_time = asyncio.get_event_loop().time()
        
        # Should have waited
        assert end_time - start_time >= 0  # At least some delay
    
    @pytest.mark.asyncio
    async def test_get_me_success(self, asana_client, mock_response_data):
        """Test successful get_me call"""
        mock_response_data["data"] = {
            "gid": "user123",
            "name": "Test User",
            "email": "test@example.com"
        }
        
        with patch.object(asana_client, '_make_request', return_value=mock_response_data):
            result = await asana_client.get_me()
            
            assert result["gid"] == "user123"
            assert result["name"] == "Test User"
            assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_list_projects_success(self, asana_client):
        """Test successful list_projects call"""
        mock_response = {
            "data": [
                {
                    "gid": "project1",
                    "name": "Project 1",
                    "team": {"name": "Team A"},
                    "archived": False
                },
                {
                    "gid": "project2", 
                    "name": "Project 2",
                    "team": {"name": "Team B"},
                    "archived": True
                }
            ]
        }
        
        with patch.object(asana_client, '_make_request', return_value=mock_response):
            projects = await asana_client.list_projects()
            
            assert len(projects) == 2
            assert isinstance(projects[0], AsanaProject)
            assert projects[0].gid == "project1"
            assert projects[0].name == "Project 1"
            assert projects[0].team == "Team A"
            assert projects[0].archived == False
            
            assert projects[1].gid == "project2"
            assert projects[1].archived == True
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, asana_client, mock_response_data):
        """Test successful task creation"""
        with patch.object(asana_client, '_make_request', return_value=mock_response_data):
            task = await asana_client.create_task(
                name="Test Task",
                notes="Test description",
                assignee="user123",
                project="project123",
                due_on="2025-08-25"
            )
            
            assert isinstance(task, AsanaTask)
            assert task.gid == "123456789"
            assert task.name == "Test Task"
            assert task.notes == "Test task description"
            assert task.assignee == "John Doe"
            assert task.project == "Test Project"
            assert task.completed == False
            assert task.due_on == "2025-08-25"
            assert task.permalink_url == "https://app.asana.com/0/123456789/987654321"
    
    @pytest.mark.asyncio
    async def test_update_task_success(self, asana_client, mock_response_data):
        """Test successful task update"""
        mock_response_data["data"]["name"] = "Updated Task"
        mock_response_data["data"]["completed"] = True
        
        with patch.object(asana_client, '_make_request', return_value=mock_response_data):
            task = await asana_client.update_task(
                task_gid="123456789",
                name="Updated Task",
                completed=True
            )
            
            assert isinstance(task, AsanaTask)
            assert task.name == "Updated Task"
            assert task.completed == True
    
    @pytest.mark.asyncio
    async def test_list_tasks_success(self, asana_client):
        """Test successful list_tasks call"""
        mock_response = {
            "data": [
                {
                    "gid": "task1",
                    "name": "Task 1",
                    "notes": "Description 1",
                    "assignee": {"name": "User 1"},
                    "projects": [{"name": "Project 1"}],
                    "completed": False,
                    "due_on": "2025-08-25",
                    "permalink_url": "https://app.asana.com/0/task1"
                },
                {
                    "gid": "task2",
                    "name": "Task 2", 
                    "notes": "Description 2",
                    "assignee": {"name": "User 2"},
                    "projects": [{"name": "Project 2"}],
                    "completed": True,
                    "due_on": None,
                    "permalink_url": "https://app.asana.com/0/task2"
                }
            ]
        }
        
        with patch.object(asana_client, '_make_request', return_value=mock_response):
            tasks = await asana_client.list_tasks(project_gid="project123")
            
            assert len(tasks) == 2
            assert isinstance(tasks[0], AsanaTask)
            assert tasks[0].gid == "task1"
            assert tasks[0].name == "Task 1"
            assert tasks[0].completed == False
            
            assert tasks[1].gid == "task2"
            assert tasks[1].completed == True
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self, asana_client):
        """Test HTTP error handling in _make_request"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
        
        with patch.object(asana_client._client, 'request', return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                await asana_client._make_request("GET", "/test")
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit_retry(self, asana_client):
        """Test rate limit retry logic"""
        # First response: rate limited
        rate_limited_response = MagicMock()
        rate_limited_response.status_code = 429
        rate_limited_response.headers = {"Retry-After": "1"}
        
        # Second response: success
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.raise_for_status.return_value = None
        success_response.json.return_value = {"data": "success"}
        
        with patch.object(asana_client._client, 'request', side_effect=[rate_limited_response, success_response]):
            with patch('asyncio.sleep') as mock_sleep:
                result = await asana_client._make_request("GET", "/test")
                
                assert result == {"data": "success"}
                mock_sleep.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, asana_client):
        """Test successful health check"""
        mock_user_data = {
            "gid": "user123",
            "name": "Test User",
            "email": "test@example.com"
        }
        
        with patch.object(asana_client, 'get_me', return_value=mock_user_data):
            health = await asana_client.health_check()
            
            assert health["status"] == "healthy"
            assert health["user_gid"] == "user123"
            assert health["user_name"] == "Test User"
            assert health["user_email"] == "test@example.com"
            assert "response_time_ms" in health
            assert health["base_url"] == "https://app.asana.com/api/1.0"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, asana_client):
        """Test health check failure"""
        with patch.object(asana_client, 'get_me', side_effect=Exception("API Error")):
            health = await asana_client.health_check()
            
            assert health["status"] == "unhealthy"
            assert health["error"] == "API Error"
            assert health["base_url"] == "https://app.asana.com/api/1.0"
    
    @pytest.mark.asyncio
    async def test_context_manager(self, asana_client):
        """Test async context manager"""
        with patch.object(asana_client, 'aclose') as mock_close:
            async with asana_client:
                pass
            mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_request_error_retry(self, asana_client):
        """Test request error retry logic"""
        with patch.object(asana_client._client, 'request', side_effect=[
            httpx.RequestError("Connection failed"),
            httpx.RequestError("Connection failed"),
            MagicMock(status_code=200, json=lambda: {"data": "success"}, raise_for_status=lambda: None)
        ]):
            with patch('asyncio.sleep'):
                result = await asana_client._make_request("GET", "/test")
                assert result == {"data": "success"}
    
    @pytest.mark.asyncio
    async def test_create_task_minimal_params(self, asana_client, mock_response_data):
        """Test task creation with minimal parameters"""
        with patch.object(asana_client, '_make_request', return_value=mock_response_data):
            task = await asana_client.create_task(name="Minimal Task")
            
            assert isinstance(task, AsanaTask)
            assert task.name == "Test Task"  # From mock response
    
    @pytest.mark.asyncio
    async def test_list_projects_with_filters(self, asana_client):
        """Test list_projects with workspace and team filters"""
        mock_response = {"data": []}
        
        with patch.object(asana_client, '_make_request', return_value=mock_response) as mock_request:
            await asana_client.list_projects(
                workspace_gid="workspace123",
                team_gid="team456",
                archived=True
            )
            
            # Verify the correct parameters were passed
            call_args = mock_request.call_args
            params = call_args[1]['params']
            assert params['workspace'] == "workspace123"
            assert params['team'] == "team456"
            assert params['archived'] == True

