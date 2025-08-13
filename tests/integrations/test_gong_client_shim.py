"""
Tests for the Gong client shim.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from integrations.gong_client_shim import GongClient
from schemas.gong import CallTranscript, CallInsight, CallSummary, MCPError


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client for testing the shim."""
    mock_client = AsyncMock()

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


@patch('integrations.gong_client_shim.GongMCPClient')
def test_gong_client_shim_initialization(MockGongMCPClient, mock_mcp_client):
    """Test that the GongClient initializes correctly."""
    MockGongMCPClient.return_value = mock_mcp_client

    # Create a client with dummy credentials (should be ignored)
    client = GongClient(api_key="dummy", client_secret="dummy")

    # Verify that GongMCPClient was initialized
    MockGongMCPClient.assert_called_once()


@patch('integrations.gong_client_shim.GongMCPClient')
def test_get_call_transcript(MockGongMCPClient, mock_mcp_client):
    """Test that get_call_transcript correctly delegates to the MCP client."""
    MockGongMCPClient.return_value = mock_mcp_client

    client = GongClient()
    result = client.get_call_transcript("call123")

    # Verify that the MCP client was called with the correct parameters
    mock_mcp_client.get_call_transcript.assert_called_once_with("call123")

    # The result should be the dict representation of the transcript
    assert isinstance(result, dict)
    assert "call_id" in result
    assert result["call_id"] == "call123"


@patch('integrations.gong_client_shim.GongMCPClient')
def test_get_call_insights(MockGongMCPClient, mock_mcp_client):
    """Test that get_call_insights correctly delegates to the MCP client."""
    MockGongMCPClient.return_value = mock_mcp_client

    client = GongClient()
    result = client.get_call_insights("call123")

    # Verify that the MCP client was called with the correct parameters
    mock_mcp_client.get_call_insights.assert_called_once_with("call123")

    # The result should be a list of dict representations of insights
    assert isinstance(result, list)
    assert len(result) == 1
    assert "id" in result[0]
    assert result[0]["id"] == "insight1"


@patch('integrations.gong_client_shim.GongMCPClient')
def test_get_call_summary(MockGongMCPClient, mock_mcp_client):
    """Test that get_call_summary correctly delegates to the MCP client."""
    MockGongMCPClient.return_value = mock_mcp_client

    client = GongClient()
    result = client.get_call_summary("call123")

    # Verify that the MCP client was called with the correct parameters
    mock_mcp_client.get_call_summary.assert_called_once_with("call123")

    # The result should be the dict representation of the summary
    assert isinstance(result, dict)
    assert "call_id" in result
    assert result["call_id"] == "call123"
    assert "summary_text" in result


@patch('integrations.gong_client_shim.GongMCPClient')
def test_search_calls(MockGongMCPClient, mock_mcp_client):
    """Test that search_calls correctly delegates to the MCP client."""
    MockGongMCPClient.return_value = mock_mcp_client

    client = GongClient()
    result = client.search_calls("test query", 10)

    # Verify that the MCP client was called with the correct parameters
    mock_mcp_client.search_calls.assert_called_once_with("test query", 10)

    # The result should be the dict from the MCP client
    assert isinstance(result, dict)
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "call123"


@patch('integrations.gong_client_shim.GongMCPClient')
def test_close(MockGongMCPClient, mock_mcp_client):
    """Test that close correctly delegates to the MCP client."""
    MockGongMCPClient.return_value = mock_mcp_client

    client = GongClient()
    client.close()

    # Verify that the MCP client's close method was called
    mock_mcp_client.close.assert_called_once()


@patch('integrations.gong_client_shim.GongMCPClient')
def test_error_handling(MockGongMCPClient):
    """Test that errors from the MCP client are correctly propagated."""
    mock_client = AsyncMock()
    mock_client.get_call_transcript.side_effect = MCPError(
        error_type="not_found",
        message="Call not found",
        status_code=404
    )
    MockGongMCPClient.return_value = mock_client

    client = GongClient()

    with pytest.raises(MCPError) as exc_info:
        client.get_call_transcript("invalid_id")

    assert exc_info.value.error_type == "not_found"
    assert exc_info.value.status_code == 404
