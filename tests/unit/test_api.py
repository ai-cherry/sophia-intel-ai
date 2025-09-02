"""
Unit Tests for API Endpoints
"""

from unittest.mock import Mock, patch

import pytest
from httpx import AsyncClient

# ============================================
# Health Check Tests
# ============================================

class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_healthz(self, api_client: AsyncClient):
        """Test health check endpoint."""
        response = await api_client.get("/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_readyz(self, api_client: AsyncClient):
        """Test readiness check endpoint."""
        response = await api_client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "services" in data

    @pytest.mark.asyncio
    async def test_metrics(self, api_client: AsyncClient):
        """Test metrics endpoint."""
        response = await api_client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

# ============================================
# Team Execution Tests
# ============================================

class TestTeamEndpoints:
    """Test team execution endpoints."""

    @pytest.mark.asyncio
    async def test_get_teams(self, authenticated_client: AsyncClient):
        """Test getting available teams."""
        response = await authenticated_client.get("/api/teams")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if data:  # If teams exist
            team = data[0]
            assert "team_id" in team
            assert "name" in team
            assert "agents" in team

    @pytest.mark.asyncio
    async def test_execute_team(self, authenticated_client: AsyncClient, sample_team_request):
        """Test team execution."""
        with patch('app.swarms.SwarmOrchestrator.execute_task') as mock_execute:
            mock_execute.return_value = {
                "status": "success",
                "result": "Test result"
            }

            response = await authenticated_client.post(
                "/run/team",
                json=sample_team_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_team_streaming(self, authenticated_client: AsyncClient):
        """Test team execution with streaming."""
        request = {
            "request": "Test streaming",
            "team_id": "test_team",
            "stream": True
        }

        with patch('app.swarms.SwarmOrchestrator.execute_stream') as mock_stream:
            async def stream_generator():
                yield {"type": "start", "team": "test_team"}
                yield {"type": "agent", "content": "Processing..."}
                yield {"type": "complete", "result": "Done"}

            mock_stream.return_value = stream_generator()

            response = await authenticated_client.post(
                "/run/team",
                json=request
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_execute_team_invalid_request(self, authenticated_client: AsyncClient):
        """Test team execution with invalid request."""
        response = await authenticated_client.post(
            "/run/team",
            json={"invalid": "request"}
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_execute_team_not_found(self, authenticated_client: AsyncClient):
        """Test team execution with non-existent team."""
        request = {
            "request": "Test",
            "team_id": "non_existent_team"
        }

        with patch('app.swarms.SwarmOrchestrator.execute_task') as mock_execute:
            mock_execute.side_effect = ValueError("Team not found")

            response = await authenticated_client.post(
                "/run/team",
                json=request
            )

            assert response.status_code == 404
            data = response.json()
            assert "error" in data

# ============================================
# Memory Endpoints Tests
# ============================================

class TestMemoryEndpoints:
    """Test memory management endpoints."""

    @pytest.mark.asyncio
    async def test_add_memory(self, authenticated_client: AsyncClient, sample_memory_entry):
        """Test adding memory."""
        with patch('app.memory.supermemory_mcp.SupermemoryStore.add_memory') as mock_add:
            mock_add.return_value = Mock(
                hash_id="test_hash",
                topic=sample_memory_entry["topic"],
                content=sample_memory_entry["content"]
            )

            response = await authenticated_client.post(
                "/memory/add",
                json=sample_memory_entry
            )

            assert response.status_code == 200
            data = response.json()
            assert data["hash_id"] == "test_hash"

    @pytest.mark.asyncio
    async def test_search_memory(self, authenticated_client: AsyncClient, sample_search_request):
        """Test searching memories."""
        with patch('app.memory.supermemory_mcp.SupermemoryStore.search') as mock_search:
            mock_search.return_value = [
                Mock(
                    hash_id="hash1",
                    topic="Result 1",
                    content="Content 1",
                    score=0.95
                )
            ]

            response = await authenticated_client.post(
                "/memory/search",
                json=sample_search_request
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["results"], list)
            assert len(data["results"]) > 0

    @pytest.mark.asyncio
    async def test_get_memory(self, authenticated_client: AsyncClient):
        """Test retrieving specific memory."""
        with patch('app.memory.supermemory_mcp.SupermemoryStore.get_memory') as mock_get:
            mock_get.return_value = Mock(
                hash_id="test_hash",
                topic="Test Topic",
                content="Test Content"
            )

            response = await authenticated_client.get("/memory/test_hash")

            assert response.status_code == 200
            data = response.json()
            assert data["hash_id"] == "test_hash"

    @pytest.mark.asyncio
    async def test_update_memory(self, authenticated_client: AsyncClient):
        """Test updating memory."""
        update_data = {
            "content": "Updated content",
            "tags": ["updated", "test"]
        }

        with patch('app.memory.supermemory_mcp.SupermemoryStore.update_memory') as mock_update:
            mock_update.return_value = Mock(
                hash_id="test_hash",
                content="Updated content"
            )

            response = await authenticated_client.put(
                "/memory/test_hash",
                json=update_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "Updated content"

    @pytest.mark.asyncio
    async def test_delete_memory(self, authenticated_client: AsyncClient):
        """Test deleting memory."""
        with patch('app.memory.supermemory_mcp.SupermemoryStore.delete_memory') as mock_delete:
            mock_delete.return_value = True

            response = await authenticated_client.delete("/memory/test_hash")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

# ============================================
# Search Endpoints Tests
# ============================================

class TestSearchEndpoints:
    """Test search endpoints."""

    @pytest.mark.asyncio
    async def test_hybrid_search(self, authenticated_client: AsyncClient):
        """Test hybrid search endpoint."""
        request = {
            "query": "test query",
            "limit": 10,
            "alpha": 0.5
        }

        with patch('app.search.hybrid_search.HybridSearch.search') as mock_search:
            mock_search.return_value = [
                {
                    "content": "Result 1",
                    "score": 0.9,
                    "source": "bm25"
                }
            ]

            response = await authenticated_client.post(
                "/search/hybrid",
                json=request
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_vector_search(self, authenticated_client: AsyncClient):
        """Test vector search endpoint."""
        request = {
            "query": "test query",
            "limit": 10,
            "threshold": 0.7
        }

        with patch('app.search.vector_search.VectorSearch.search') as mock_search:
            mock_search.return_value = [
                {
                    "content": "Vector result",
                    "similarity": 0.85
                }
            ]

            response = await authenticated_client.post(
                "/search/vector",
                json=request
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["results"], list)

# ============================================
# Authentication Tests
# ============================================

class TestAuthentication:
    """Test API authentication."""

    @pytest.mark.asyncio
    async def test_missing_api_key(self, api_client: AsyncClient):
        """Test request without API key."""
        response = await api_client.post(
            "/run/team",
            json={"request": "test", "team_id": "test"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, api_client: AsyncClient):
        """Test request with invalid API key."""
        api_client.headers["X-API-Key"] = "invalid-key"

        response = await api_client.post(
            "/run/team",
            json={"request": "test", "team_id": "test"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data

# ============================================
# Rate Limiting Tests
# ============================================

class TestRateLimiting:
    """Test rate limiting."""

    @pytest.mark.asyncio
    async def test_rate_limit(self, authenticated_client: AsyncClient, monkeypatch):
        """Test rate limiting enforcement."""
        # Enable rate limiting for test
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")

        # Make multiple rapid requests
        for i in range(101):  # Exceed default limit of 100/min
            response = await authenticated_client.get("/api/teams")

            if response.status_code == 429:
                data = response.json()
                assert "error" in data
                assert "rate limit" in data["error"]["message"].lower()
                break
        else:
            pytest.fail("Rate limit not enforced")

# ============================================
# Error Handling Tests
# ============================================

class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_internal_error(self, authenticated_client: AsyncClient):
        """Test internal server error handling."""
        with patch('app.swarms.SwarmOrchestrator.execute_task') as mock_execute:
            mock_execute.side_effect = Exception("Internal error")

            response = await authenticated_client.post(
                "/run/team",
                json={"request": "test", "team_id": "test"}
            )

            assert response.status_code == 500
            data = response.json()
            assert "error" in data

    @pytest.mark.asyncio
    async def test_validation_error(self, authenticated_client: AsyncClient):
        """Test request validation error."""
        response = await authenticated_client.post(
            "/memory/add",
            json={"invalid_field": "value"}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_not_found_error(self, authenticated_client: AsyncClient):
        """Test not found error."""
        response = await authenticated_client.get("/api/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

# ============================================
# WebSocket Tests
# ============================================

class TestWebSocket:
    """Test WebSocket endpoints."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, api_client: AsyncClient):
        """Test WebSocket connection."""
        # Note: httpx doesn't support WebSocket, this is a placeholder
        # In real tests, use websocket-client or similar
        pass

    @pytest.mark.asyncio
    async def test_websocket_team_execution(self):
        """Test team execution over WebSocket."""
        # Placeholder for WebSocket test
        pass
