"""
Tests for MCP Context Service
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from app.services.mcp_context import (
    MCPContextManager,
    get_mcp_context_manager,
    MCP_SERVERS,
    MAX_CONTEXT_SIZE
)


@pytest.fixture
async def mcp_context_manager():
    """Create MCP context manager with mocked clients"""
    manager = MCPContextManager(timeout=5)
    
    # Mock HTTP clients
    manager._clients = {
        "filesystem": AsyncMock(spec=httpx.AsyncClient),
        "memory": AsyncMock(spec=httpx.AsyncClient),
        "git": AsyncMock(spec=httpx.AsyncClient)
    }
    
    yield manager


class TestMCPContextManager:
    """Test MCP context manager functionality"""
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """Test context manager initialization"""
        async with MCPContextManager() as manager:
            assert manager.timeout == 10  # Default timeout
            assert len(manager._clients) == 3
            assert "filesystem" in manager._clients
            assert "memory" in manager._clients
            assert "git" in manager._clients
    
    @pytest.mark.asyncio
    async def test_request_success(self, mcp_context_manager):
        """Test successful MCP request"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success", "data": "test"}
        mock_response.raise_for_status = MagicMock()
        
        mcp_context_manager._clients["filesystem"].post = AsyncMock(
            return_value=mock_response
        )
        
        # Make request
        result = await mcp_context_manager._request(
            "filesystem",
            "list",
            method="POST",
            root=".",
            globs=["*.py"]
        )
        
        assert result["status"] == "success"
        assert result["data"] == "test"
        
        # Verify API call
        mcp_context_manager._clients["filesystem"].post.assert_called_once_with(
            "/repo/list",
            json={"root": ".", "globs": ["*.py"]}
        )
    
    @pytest.mark.asyncio
    async def test_request_failure(self, mcp_context_manager):
        """Test MCP request failure handling"""
        # Mock HTTP error
        mock_error = httpx.HTTPError("Connection failed")
        mcp_context_manager._clients["filesystem"].post = AsyncMock(
            side_effect=mock_error
        )
        
        # Request should return None on error
        result = await mcp_context_manager._request(
            "filesystem",
            "list",
            root="."
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_repository_structure(self, mcp_context_manager):
        """Test getting repository structure"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "files": [
                "dir1/",
                "dir2/",
                "file1.py",
                "file2.py",
                "file3.txt"
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        mcp_context_manager._clients["filesystem"].post = AsyncMock(
            return_value=mock_response
        )
        
        # Mock os.path functions
        with patch("os.path.isdir") as mock_isdir:
            with patch("os.path.isfile") as mock_isfile:
                with patch("os.path.getsize") as mock_getsize:
                    mock_isdir.side_effect = lambda x: x.endswith("/")
                    mock_isfile.side_effect = lambda x: not x.endswith("/")
                    mock_getsize.return_value = 1024
                    
                    # Get structure
                    structure = await mcp_context_manager.get_repository_structure()
                    
                    assert "directories" in structure
                    assert "files" in structure
                    assert "total_files" in structure
                    assert structure["total_files"] == 5
    
    @pytest.mark.asyncio
    async def test_get_git_status(self, mcp_context_manager):
        """Test getting git status"""
        # Mock status response
        status_response = MagicMock()
        status_response.json.return_value = {
            "branch": "main",
            "modified": ["file1.py", "file2.py"],
            "staged": ["file3.py"],
            "untracked": ["new_file.txt"]
        }
        status_response.raise_for_status = MagicMock()
        
        # Mock log response
        log_response = MagicMock()
        log_response.json.return_value = {
            "commits": [
                {
                    "sha": "abc123def456",
                    "message": "Fix bug in authentication",
                    "author": "John Doe"
                },
                {
                    "sha": "def456ghi789",
                    "message": "Add new feature",
                    "author": "Jane Smith"
                }
            ]
        }
        log_response.raise_for_status = MagicMock()
        
        # Set up mock responses
        mcp_context_manager._clients["git"].post = AsyncMock(
            side_effect=[status_response, log_response]
        )
        
        # Get git status
        status = await mcp_context_manager.get_git_status()
        
        assert status["branch"] == "main"
        assert status["modified"] == 2
        assert status["staged"] == 1
        assert status["untracked"] == 1
        assert len(status["recent_commits"]) == 2
        assert status["recent_commits"][0]["sha"] == "abc123d"
    
    @pytest.mark.asyncio
    async def test_search_memory(self, mcp_context_manager):
        """Test memory search"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "content": "This is a long piece of content that should be truncated",
                    "metadata": {"type": "context"},
                    "score": 0.95
                },
                {
                    "content": "Another result",
                    "metadata": {"type": "decision"},
                    "score": 0.85
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        mcp_context_manager._clients["memory"].post = AsyncMock(
            return_value=mock_response
        )
        
        # Search memory
        results = await mcp_context_manager.search_memory(
            query="test query",
            limit=2
        )
        
        assert len(results) == 2
        assert results[0]["score"] == 0.95
        assert len(results[0]["content"]) <= 200  # Content truncated
        assert results[1]["score"] == 0.85
    
    @pytest.mark.asyncio
    async def test_build_compact_context(self, mcp_context_manager):
        """Test building compact context"""
        # Mock structure response
        structure_response = MagicMock()
        structure_response.json.return_value = {
            "files": ["dir1/", "file1.py", "file2.py"]
        }
        structure_response.raise_for_status = MagicMock()
        
        # Mock git status response
        git_response = MagicMock()
        git_response.json.return_value = {
            "branch": "main",
            "modified": ["file1.py"],
            "staged": [],
            "untracked": []
        }
        git_response.raise_for_status = MagicMock()
        
        # Mock git log response
        log_response = MagicMock()
        log_response.json.return_value = {
            "commits": [{
                "sha": "abc123",
                "message": "Latest commit message",
                "author": "Dev"
            }]
        }
        log_response.raise_for_status = MagicMock()
        
        # Mock memory response
        memory_response = MagicMock()
        memory_response.json.return_value = {
            "results": [{
                "content": "Important context information",
                "metadata": {},
                "score": 0.9
            }]
        }
        memory_response.raise_for_status = MagicMock()
        
        # Set up mock responses
        responses = [
            structure_response,  # get_repository_structure
            git_response,        # get_git_status
            log_response,        # git log
            memory_response      # search_memory
        ]
        
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            response = responses[call_count] if call_count < len(responses) else MagicMock()
            call_count += 1
            return response
        
        for client in mcp_context_manager._clients.values():
            client.post = AsyncMock(side_effect=mock_post)
        
        # Mock os.path functions
        with patch("os.path.isdir") as mock_isdir:
            with patch("os.path.isfile") as mock_isfile:
                with patch("os.path.getsize") as mock_getsize:
                    mock_isdir.side_effect = lambda x: x.endswith("/")
                    mock_isfile.side_effect = lambda x: not x.endswith("/")
                    mock_getsize.return_value = 1024
                    
                    # Build context
                    context = await mcp_context_manager.build_compact_context()
                    
                    assert "workspace" in context
                    assert "structure" in context
                    assert "git" in context
                    assert "memory" in context
                    
                    # Verify context is compact
                    context_str = json.dumps(context)
                    assert len(context_str) <= MAX_CONTEXT_SIZE
    
    @pytest.mark.asyncio
    async def test_read_file(self, mcp_context_manager):
        """Test reading file content"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "File content here"
        }
        mock_response.raise_for_status = MagicMock()
        
        mcp_context_manager._clients["filesystem"].post = AsyncMock(
            return_value=mock_response
        )
        
        # Read file
        content = await mcp_context_manager.read_file(
            path="test.py",
            start_line=1,
            end_line=10
        )
        
        assert content == "File content here"
        
        # Verify API call
        mcp_context_manager._clients["filesystem"].post.assert_called_once_with(
            "/repo/read",
            json={"path": "test.py", "start_line": 1, "end_line": 10}
        )
    
    @pytest.mark.asyncio
    async def test_write_file(self, mcp_context_manager):
        """Test writing file content"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()
        
        mcp_context_manager._clients["filesystem"].post = AsyncMock(
            return_value=mock_response
        )
        
        # Write file
        success = await mcp_context_manager.write_file(
            path="test.py",
            content="New content"
        )
        
        assert success is True
        
        # Verify API call
        mcp_context_manager._clients["filesystem"].post.assert_called_once_with(
            "/fs/write",
            json={"path": "test.py", "content": "New content"}
        )
    
    @pytest.mark.asyncio
    async def test_singleton_manager(self):
        """Test singleton pattern for context manager"""
        from app.services.mcp_context import close_mcp_context_manager
        
        # Get first instance
        manager1 = await get_mcp_context_manager()
        
        # Get second instance (should be same)
        manager2 = await get_mcp_context_manager()
        
        assert manager1 is manager2
        
        # Clean up
        await close_mcp_context_manager()