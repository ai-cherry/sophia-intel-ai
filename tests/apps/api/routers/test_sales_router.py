"""
Tests for the Sales Router using Gong MCP.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime

from apps.api.routers.sales_router import router, get_gong_client
from libs.mcp_client.gong import GongMCPClient
from schemas.gong import CallTranscript, CallInsight, CallSummary, MCPError


@pytest.fixture
def mock_gong_client():
    """Create a mock Gong MCP client for testing."""
    mock_client = AsyncMock(spec=GongMCPClient)

    # Mock the get_call_transcript method
    transcript = CallTranscript(
        call_id="call123",
        title="Test Call",
        date=datetime.now(),
        duration=1800.0,
        participants=[],
        segments=[]
    )
    mock_client.get_call_transcript.return_value = transcript

    # Mock the get_call_insights method
    insight = CallInsight(
        id="insight1",
        call_id="call123",
        category="objection",
        text="Customer expressed concerns about pricing",
        confidence=0.85,
        segment_ids=["seg1"],
        timestamp=120.5
    )
    mock_client.get_call_insights.return_value = [insight]

    # Mock the get_call_summary method
    summary = CallSummary(
        call_id="call123",
        title="Test Call",
        date=datetime.now(),
        duration=1800.0,
        summary_text="This is a summary of the call",
        topics=[],
        action_items=[]
    )
    mock_client.get_call_summary.return_value = summary

    # Mock the search_calls method
    mock_client.search_calls.return_value = {
        "data": [
            {
                "id": "call123",
                "title": "Test Call"
            }
        ],
        "meta": {
            "has_more": False,
            "next_cursor": None
        }
    }

    return mock_client


@pytest.fixture
def app(mock_gong_client):
    """Create a FastAPI app with the sales router and a mocked Gong client."""
    app = FastAPI()

    # Override the get_gong_client dependency
    async def override_get_gong_client():
        yield mock_gong_client

    app.dependency_overrides[get_gong_client] = override_get_gong_client
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_get_call_transcript(client):
    """Test the get_call_transcript endpoint."""
    response = client.get("/sales/calls/call123/transcript")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "data" in response.json()
    assert response.json()["data"]["call_id"] == "call123"


def test_get_call_insights(client):
    """Test the get_call_insights endpoint."""
    response = client.get("/sales/calls/call123/insights")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "data" in response.json()
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["id"] == "insight1"


def test_get_call_summary(client):
    """Test the get_call_summary endpoint."""
    response = client.get("/sales/calls/call123/summary")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "data" in response.json()
    assert response.json()["data"]["call_id"] == "call123"


def test_search_calls(client):
    """Test the search_calls endpoint."""
    response = client.get("/sales/calls/search?query=test")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "data" in response.json()
    assert "meta" in response.json()


def test_analyze_call(client):
    """Test the analyze_call endpoint."""
    response = client.get("/sales/calls/call123/analyze")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "data" in response.json()
    assert "transcript" in response.json()["data"]
    assert "insights" in response.json()["data"]
    assert "summary" in response.json()["data"]


def test_error_handling(client, mock_gong_client):
    """Test error handling in the sales router."""
    # Mock the get_call_transcript method to raise an error
    mock_gong_client.get_call_transcript.side_effect = MCPError(
        error_type="not_found",
        message="Call not found",
        status_code=404
    )

    response = client.get("/sales/calls/invalid_id/transcript")
    assert response.status_code == 404
    assert not response.json()["success"]
    assert "error" in response.json()
    assert response.json()["error"]["type"] == "not_found"
    assert response.json()["error"]["status"] == 404
