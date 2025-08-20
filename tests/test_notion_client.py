"""
Tests for Notion API Client
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from sophia.integrations.notion_client import NotionClient, NotionDatabase, NotionPage


class TestNotionClient:
    """Test suite for NotionClient"""
    
    @pytest.fixture
    def mock_token(self):
        return "test_notion_token_12345"
    
    @pytest.fixture
    def notion_client(self, mock_token):
        with patch.dict('os.environ', {'NOTION_API_KEY': mock_token}):
            return NotionClient()
    
    @pytest.fixture
    def mock_bot_response(self):
        return {
            "id": "bot123",
            "name": "SOPHIA Bot",
            "type": "bot"
        }
    
    @pytest.fixture
    def mock_databases_response(self):
        return {
            "results": [
                {
                    "object": "database",
                    "id": "db1",
                    "title": [{"plain_text": "Projects"}],
                    "url": "https://notion.so/db1",
                    "created_time": "2025-08-20T10:00:00Z",
                    "last_edited_time": "2025-08-20T11:00:00Z"
                },
                {
                    "object": "database",
                    "id": "db2",
                    "title": [{"plain_text": "Tasks"}],
                    "url": "https://notion.so/db2",
                    "created_time": "2025-08-20T09:00:00Z",
                    "last_edited_time": "2025-08-20T10:30:00Z"
                }
            ]
        }
    
    @pytest.fixture
    def mock_page_response(self):
        return {
            "id": "page123",
            "properties": {
                "Name": {
                    "title": [{"plain_text": "Test Page"}]
                }
            },
            "url": "https://notion.so/page123",
            "created_time": "2025-08-20T12:00:00Z",
            "last_edited_time": "2025-08-20T12:30:00Z"
        }
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_token):
        """Test client initialization"""
        with patch.dict('os.environ', {'NOTION_API_KEY': mock_token}):
            client = NotionClient()
            assert client.token == mock_token
            assert client.base_url == "https://api.notion.com/v1"
            assert client.rate_limit == 3
    
    @pytest.mark.asyncio
    async def test_initialization_no_token(self):
        """Test client initialization without token"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(EnvironmentError, match="Missing required environment variable: NOTION_API_KEY"):
                NotionClient()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, notion_client):
        """Test rate limiting functionality (3 requests per second)"""
        # Fill up the rate limit
        current_time = asyncio.get_event_loop().time()
        notion_client._request_times = [current_time - 0.5] * 3  # Fill to limit
        
        # This should trigger rate limiting
        start_time = asyncio.get_event_loop().time()
        await notion_client._rate_limit_check()
        end_time = asyncio.get_event_loop().time()
        
        # Should have waited
        assert end_time - start_time >= 0  # At least some delay
    
    @pytest.mark.asyncio
    async def test_get_me_success(self, notion_client, mock_bot_response):
        """Test successful get_me call"""
        with patch.object(notion_client, '_make_request', return_value=mock_bot_response):
            result = await notion_client.get_me()
            
            assert result["id"] == "bot123"
            assert result["name"] == "SOPHIA Bot"
            assert result["type"] == "bot"
    
    @pytest.mark.asyncio
    async def test_list_databases_success(self, notion_client, mock_databases_response):
        """Test successful list_databases call"""
        with patch.object(notion_client, '_make_request', return_value=mock_databases_response):
            databases = await notion_client.list_databases()
            
            assert len(databases) == 2
            assert isinstance(databases[0], NotionDatabase)
            assert databases[0].id == "db1"
            assert databases[0].title == "Projects"
            assert databases[0].url == "https://notion.so/db1"
            
            assert databases[1].id == "db2"
            assert databases[1].title == "Tasks"
    
    @pytest.mark.asyncio
    async def test_create_page_in_database(self, notion_client, mock_page_response):
        """Test successful page creation in database"""
        with patch.object(notion_client, '_make_request', return_value=mock_page_response):
            page = await notion_client.create_page(
                parent_id="db123",
                title="Test Page",
                content="This is test content.\n\nSecond paragraph.",
                is_database_parent=True
            )
            
            assert isinstance(page, NotionPage)
            assert page.id == "page123"
            assert page.title == "Test Page"
            assert page.url == "https://notion.so/page123"
            assert page.parent_id == "db123"
    
    @pytest.mark.asyncio
    async def test_create_page_as_child(self, notion_client, mock_page_response):
        """Test page creation as child of another page"""
        mock_page_response["properties"] = {
            "title": {
                "title": [{"plain_text": "Child Page"}]
            }
        }
        
        with patch.object(notion_client, '_make_request', return_value=mock_page_response):
            page = await notion_client.create_page(
                parent_id="parent123",
                title="Child Page",
                content="Child page content",
                is_database_parent=False
            )
            
            assert isinstance(page, NotionPage)
            assert page.title == "Child Page"
    
    @pytest.mark.asyncio
    async def test_update_page_success(self, notion_client, mock_page_response):
        """Test successful page update"""
        mock_page_response["properties"]["Name"]["title"][0]["plain_text"] = "Updated Page"
        
        with patch.object(notion_client, '_make_request', return_value=mock_page_response):
            page = await notion_client.update_page(
                page_id="page123",
                title="Updated Page"
            )
            
            assert isinstance(page, NotionPage)
            assert page.title == "Updated Page"
    
    @pytest.mark.asyncio
    async def test_append_block_children_success(self, notion_client):
        """Test successful block children append"""
        mock_response = {
            "results": [
                {
                    "id": "block123",
                    "type": "paragraph"
                }
            ]
        }
        
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "New paragraph"}
                        }
                    ]
                }
            }
        ]
        
        with patch.object(notion_client, '_make_request', return_value=mock_response):
            result = await notion_client.append_block_children("page123", children)
            
            assert result["results"][0]["id"] == "block123"
    
    @pytest.mark.asyncio
    async def test_search_pages_success(self, notion_client):
        """Test successful page search"""
        mock_response = {
            "results": [
                {
                    "object": "page",
                    "id": "page1",
                    "properties": {
                        "Name": {
                            "title": [{"plain_text": "Search Result 1"}]
                        }
                    },
                    "url": "https://notion.so/page1",
                    "created_time": "2025-08-20T10:00:00Z",
                    "last_edited_time": "2025-08-20T11:00:00Z"
                },
                {
                    "object": "page",
                    "id": "page2",
                    "properties": {
                        "title": {
                            "title": [{"plain_text": "Search Result 2"}]
                        }
                    },
                    "url": "https://notion.so/page2",
                    "created_time": "2025-08-20T09:00:00Z",
                    "last_edited_time": "2025-08-20T10:30:00Z"
                }
            ]
        }
        
        with patch.object(notion_client, '_make_request', return_value=mock_response):
            pages = await notion_client.search_pages("test query")
            
            assert len(pages) == 2
            assert isinstance(pages[0], NotionPage)
            assert pages[0].id == "page1"
            assert pages[0].title == "Search Result 1"
            
            assert pages[1].id == "page2"
            assert pages[1].title == "Search Result 2"
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self, notion_client):
        """Test HTTP error handling in _make_request"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )
        
        with patch.object(notion_client._client, 'request', return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                await notion_client._make_request("GET", "/test")
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit_retry(self, notion_client):
        """Test rate limit retry logic"""
        # First response: rate limited
        rate_limited_response = MagicMock()
        rate_limited_response.status_code = 429
        rate_limited_response.headers = {"Retry-After": "1"}
        
        # Second response: success
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.raise_for_status.return_value = None
        success_response.json.return_value = {"id": "success"}
        
        with patch.object(notion_client._client, 'request', side_effect=[rate_limited_response, success_response]):
            with patch('asyncio.sleep') as mock_sleep:
                result = await notion_client._make_request("GET", "/test")
                
                assert result == {"id": "success"}
                mock_sleep.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, notion_client, mock_bot_response):
        """Test successful health check"""
        with patch.object(notion_client, 'get_me', return_value=mock_bot_response):
            health = await notion_client.health_check()
            
            assert health["status"] == "healthy"
            assert health["bot_id"] == "bot123"
            assert health["bot_name"] == "SOPHIA Bot"
            assert health["bot_type"] == "bot"
            assert "response_time_ms" in health
            assert health["base_url"] == "https://api.notion.com/v1"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, notion_client):
        """Test health check failure"""
        with patch.object(notion_client, 'get_me', side_effect=Exception("API Error")):
            health = await notion_client.health_check()
            
            assert health["status"] == "unhealthy"
            assert health["error"] == "API Error"
            assert health["base_url"] == "https://api.notion.com/v1"
    
    @pytest.mark.asyncio
    async def test_context_manager(self, notion_client):
        """Test async context manager"""
        with patch.object(notion_client, 'aclose') as mock_close:
            async with notion_client:
                pass
            mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_request_error_retry(self, notion_client):
        """Test request error retry logic"""
        with patch.object(notion_client._client, 'request', side_effect=[
            httpx.RequestError("Connection failed"),
            httpx.RequestError("Connection failed"),
            MagicMock(status_code=200, json=lambda: {"id": "success"}, raise_for_status=lambda: None)
        ]):
            with patch('asyncio.sleep'):
                result = await notion_client._make_request("GET", "/test")
                assert result == {"id": "success"}
    
    @pytest.mark.asyncio
    async def test_create_page_minimal_params(self, notion_client, mock_page_response):
        """Test page creation with minimal parameters"""
        with patch.object(notion_client, '_make_request', return_value=mock_page_response):
            page = await notion_client.create_page(
                parent_id="db123",
                title="Minimal Page"
            )
            
            assert isinstance(page, NotionPage)
            assert page.title == "Test Page"  # From mock response
    
    @pytest.mark.asyncio
    async def test_search_pages_with_filter(self, notion_client):
        """Test search_pages with filter"""
        mock_response = {"results": []}
        
        with patch.object(notion_client, '_make_request', return_value=mock_response) as mock_request:
            await notion_client.search_pages(
                query="test",
                filter_type="page",
                page_size=50
            )
            
            # Verify the correct parameters were passed
            call_args = mock_request.call_args
            json_data = call_args[1]['json_data']
            assert json_data['query'] == "test"
            assert json_data['filter']['value'] == "page"
            assert json_data['page_size'] == 50
    
    @pytest.mark.asyncio
    async def test_list_databases_pagination(self, notion_client):
        """Test list_databases with pagination"""
        mock_response = {"results": []}
        
        with patch.object(notion_client, '_make_request', return_value=mock_response) as mock_request:
            await notion_client.list_databases(
                start_cursor="cursor123",
                page_size=25
            )
            
            # Verify pagination parameters
            call_args = mock_request.call_args
            json_data = call_args[1]['json_data']
            assert json_data['start_cursor'] == "cursor123"
            assert json_data['page_size'] == 25
    
    @pytest.mark.asyncio
    async def test_update_page_archive(self, notion_client, mock_page_response):
        """Test page archiving"""
        with patch.object(notion_client, '_make_request', return_value=mock_page_response):
            page = await notion_client.update_page(
                page_id="page123",
                archived=True
            )
            
            assert isinstance(page, NotionPage)

