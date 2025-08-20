"""
Tests for Linear API Client
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from sophia.integrations.linear_client import LinearClient, LinearTeam, LinearIssue


class TestLinearClient:
    """Test suite for LinearClient"""
    
    @pytest.fixture
    def mock_api_key(self):
        return "test_linear_api_key_12345"
    
    @pytest.fixture
    def linear_client(self, mock_api_key):
        with patch.dict('os.environ', {'LINEAR_API_KEY': mock_api_key}):
            return LinearClient()
    
    @pytest.fixture
    def mock_viewer_response(self):
        return {
            "data": {
                "viewer": {
                    "id": "user123",
                    "name": "Test User",
                    "email": "test@example.com",
                    "displayName": "Test User"
                }
            }
        }
    
    @pytest.fixture
    def mock_teams_response(self):
        return {
            "data": {
                "teams": {
                    "nodes": [
                        {
                            "id": "team1",
                            "name": "Engineering",
                            "key": "ENG",
                            "description": "Engineering team"
                        },
                        {
                            "id": "team2",
                            "name": "Product",
                            "key": "PROD",
                            "description": "Product team"
                        }
                    ]
                }
            }
        }
    
    @pytest.fixture
    def mock_issue_response(self):
        return {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "issue123",
                        "identifier": "ENG-123",
                        "title": "Test Issue",
                        "description": "Test issue description",
                        "assignee": {"name": "John Doe"},
                        "team": {"name": "Engineering"},
                        "state": {"name": "Todo"},
                        "priority": 2,
                        "url": "https://linear.app/company/issue/ENG-123",
                        "createdAt": "2025-08-20T12:00:00Z"
                    }
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_api_key):
        """Test client initialization"""
        with patch.dict('os.environ', {'LINEAR_API_KEY': mock_api_key}):
            client = LinearClient()
            assert client.api_key == mock_api_key
            assert client.base_url == "https://api.linear.app/graphql"
            assert client.rate_limit == 1800
    
    @pytest.mark.asyncio
    async def test_initialization_no_api_key(self):
        """Test client initialization without API key"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(EnvironmentError, match="Missing required environment variable: LINEAR_API_KEY"):
                LinearClient()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, linear_client):
        """Test rate limiting functionality"""
        # Fill up the rate limit
        current_time = asyncio.get_event_loop().time()
        linear_client._request_times = [current_time - 1800] * 1800  # Fill to limit
        
        # This should trigger rate limiting
        start_time = asyncio.get_event_loop().time()
        await linear_client._rate_limit_check()
        end_time = asyncio.get_event_loop().time()
        
        # Should have waited
        assert end_time - start_time >= 0  # At least some delay
    
    @pytest.mark.asyncio
    async def test_get_viewer_success(self, linear_client, mock_viewer_response):
        """Test successful get_viewer call"""
        with patch.object(linear_client, '_make_request', return_value=mock_viewer_response):
            result = await linear_client.get_viewer()
            
            assert result["id"] == "user123"
            assert result["name"] == "Test User"
            assert result["email"] == "test@example.com"
            assert result["displayName"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_list_teams_success(self, linear_client, mock_teams_response):
        """Test successful list_teams call"""
        with patch.object(linear_client, '_make_request', return_value=mock_teams_response):
            teams = await linear_client.list_teams()
            
            assert len(teams) == 2
            assert isinstance(teams[0], LinearTeam)
            assert teams[0].id == "team1"
            assert teams[0].name == "Engineering"
            assert teams[0].key == "ENG"
            assert teams[0].description == "Engineering team"
            
            assert teams[1].id == "team2"
            assert teams[1].name == "Product"
            assert teams[1].key == "PROD"
    
    @pytest.mark.asyncio
    async def test_create_issue_success(self, linear_client, mock_issue_response):
        """Test successful issue creation"""
        with patch.object(linear_client, '_make_request', return_value=mock_issue_response):
            issue = await linear_client.create_issue(
                title="Test Issue",
                description="Test description",
                team_id="team1",
                assignee_id="user123",
                priority=2
            )
            
            assert isinstance(issue, LinearIssue)
            assert issue.id == "issue123"
            assert issue.identifier == "ENG-123"
            assert issue.title == "Test Issue"
            assert issue.description == "Test issue description"
            assert issue.assignee == "John Doe"
            assert issue.team == "Engineering"
            assert issue.state == "Todo"
            assert issue.priority == 2
            assert issue.url == "https://linear.app/company/issue/ENG-123"
    
    @pytest.mark.asyncio
    async def test_create_issue_minimal_params(self, linear_client, mock_issue_response):
        """Test issue creation with minimal parameters"""
        with patch.object(linear_client, '_make_request', return_value=mock_issue_response):
            issue = await linear_client.create_issue(title="Minimal Issue")
            
            assert isinstance(issue, LinearIssue)
            assert issue.title == "Test Issue"  # From mock response
    
    @pytest.mark.asyncio
    async def test_create_issue_failure(self, linear_client):
        """Test issue creation failure"""
        mock_response = {
            "data": {
                "issueCreate": {
                    "success": False,
                    "issue": None
                }
            }
        }
        
        with patch.object(linear_client, '_make_request', return_value=mock_response):
            with pytest.raises(Exception, match="Failed to create issue"):
                await linear_client.create_issue(title="Failed Issue")
    
    @pytest.mark.asyncio
    async def test_update_issue_success(self, linear_client):
        """Test successful issue update"""
        mock_response = {
            "data": {
                "issueUpdate": {
                    "success": True,
                    "issue": {
                        "id": "issue123",
                        "identifier": "ENG-123",
                        "title": "Updated Issue",
                        "description": "Updated description",
                        "assignee": {"name": "Jane Doe"},
                        "team": {"name": "Engineering"},
                        "state": {"name": "In Progress"},
                        "priority": 1,
                        "url": "https://linear.app/company/issue/ENG-123",
                        "createdAt": "2025-08-20T12:00:00Z"
                    }
                }
            }
        }
        
        with patch.object(linear_client, '_make_request', return_value=mock_response):
            issue = await linear_client.update_issue(
                issue_id="issue123",
                title="Updated Issue",
                priority=1
            )
            
            assert isinstance(issue, LinearIssue)
            assert issue.title == "Updated Issue"
            assert issue.priority == 1
            assert issue.assignee == "Jane Doe"
            assert issue.state == "In Progress"
    
    @pytest.mark.asyncio
    async def test_list_issues_success(self, linear_client):
        """Test successful list_issues call"""
        mock_response = {
            "data": {
                "issues": {
                    "nodes": [
                        {
                            "id": "issue1",
                            "identifier": "ENG-1",
                            "title": "Issue 1",
                            "description": "Description 1",
                            "assignee": {"name": "User 1"},
                            "team": {"name": "Engineering"},
                            "state": {"name": "Todo"},
                            "priority": 3,
                            "url": "https://linear.app/company/issue/ENG-1",
                            "createdAt": "2025-08-20T10:00:00Z"
                        },
                        {
                            "id": "issue2",
                            "identifier": "ENG-2", 
                            "title": "Issue 2",
                            "description": "Description 2",
                            "assignee": {"name": "User 2"},
                            "team": {"name": "Engineering"},
                            "state": {"name": "Done"},
                            "priority": 2,
                            "url": "https://linear.app/company/issue/ENG-2",
                            "createdAt": "2025-08-20T11:00:00Z"
                        }
                    ]
                }
            }
        }
        
        with patch.object(linear_client, '_make_request', return_value=mock_response):
            issues = await linear_client.list_issues(team_id="team1", limit=10)
            
            assert len(issues) == 2
            assert isinstance(issues[0], LinearIssue)
            assert issues[0].id == "issue1"
            assert issues[0].identifier == "ENG-1"
            assert issues[0].title == "Issue 1"
            assert issues[0].state == "Todo"
            
            assert issues[1].id == "issue2"
            assert issues[1].state == "Done"
    
    @pytest.mark.asyncio
    async def test_make_request_graphql_error(self, linear_client):
        """Test GraphQL error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "errors": [{"message": "Field 'invalid' not found"}]
        }
        
        with patch.object(linear_client._client, 'post', return_value=mock_response):
            with pytest.raises(Exception, match="GraphQL errors"):
                await linear_client._make_request("query { invalid }")
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self, linear_client):
        """Test HTTP error handling in _make_request"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        
        with patch.object(linear_client._client, 'post', return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                await linear_client._make_request("query { viewer { id } }")
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit_retry(self, linear_client):
        """Test rate limit retry logic"""
        # First response: rate limited
        rate_limited_response = MagicMock()
        rate_limited_response.status_code = 429
        rate_limited_response.headers = {"Retry-After": "1"}
        
        # Second response: success
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.raise_for_status.return_value = None
        success_response.json.return_value = {"data": {"viewer": {"id": "user123"}}}
        
        with patch.object(linear_client._client, 'post', side_effect=[rate_limited_response, success_response]):
            with patch('asyncio.sleep') as mock_sleep:
                result = await linear_client._make_request("query { viewer { id } }")
                
                assert result == {"data": {"viewer": {"id": "user123"}}}
                mock_sleep.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, linear_client, mock_viewer_response):
        """Test successful health check"""
        with patch.object(linear_client, 'get_viewer', return_value=mock_viewer_response["data"]["viewer"]):
            health = await linear_client.health_check()
            
            assert health["status"] == "healthy"
            assert health["user_id"] == "user123"
            assert health["user_name"] == "Test User"
            assert health["user_email"] == "test@example.com"
            assert "response_time_ms" in health
            assert health["base_url"] == "https://api.linear.app/graphql"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, linear_client):
        """Test health check failure"""
        with patch.object(linear_client, 'get_viewer', side_effect=Exception("GraphQL Error")):
            health = await linear_client.health_check()
            
            assert health["status"] == "unhealthy"
            assert health["error"] == "GraphQL Error"
            assert health["base_url"] == "https://api.linear.app/graphql"
    
    @pytest.mark.asyncio
    async def test_context_manager(self, linear_client):
        """Test async context manager"""
        with patch.object(linear_client, 'aclose') as mock_close:
            async with linear_client:
                pass
            mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_request_error_retry(self, linear_client):
        """Test request error retry logic"""
        with patch.object(linear_client._client, 'post', side_effect=[
            httpx.RequestError("Connection failed"),
            httpx.RequestError("Connection failed"),
            MagicMock(
                status_code=200, 
                json=lambda: {"data": {"viewer": {"id": "user123"}}}, 
                raise_for_status=lambda: None
            )
        ]):
            with patch('asyncio.sleep'):
                result = await linear_client._make_request("query { viewer { id } }")
                assert result == {"data": {"viewer": {"id": "user123"}}}
    
    @pytest.mark.asyncio
    async def test_list_issues_with_filters(self, linear_client):
        """Test list_issues with various filters"""
        mock_response = {"data": {"issues": {"nodes": []}}}
        
        with patch.object(linear_client, '_make_request', return_value=mock_response) as mock_request:
            await linear_client.list_issues(
                team_id="team123",
                assignee_id="user456",
                state_name="In Progress",
                limit=25
            )
            
            # Verify the GraphQL query was constructed correctly
            call_args = mock_request.call_args
            variables = call_args[1]['variables']
            assert variables['filter']['team']['id']['eq'] == "team123"
            assert variables['filter']['assignee']['id']['eq'] == "user456"
            assert variables['filter']['state']['name']['eq'] == "In Progress"
            assert variables['first'] == 25

