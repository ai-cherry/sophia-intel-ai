"""
Tests for the SalesCoachAgent with Gong MCP client.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from agents.sales_coach_agent import SalesCoachAgent
from libs.mcp_client.gong import GongMCPClient
from schemas.gong import CallTranscript, CallInsight, CallSummary, MCPError


@pytest.fixture
def mock_gong_mcp_client():
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


@pytest.mark.asyncio
@patch('agents.sales_coach_agent.GongMCPClient')
async def test_get_transcript_success(MockGongMCPClient, mock_gong_mcp_client):
    """Test the get_transcript method with a successful response."""
    # Setup
    MockGongMCPClient.return_value = mock_gong_mcp_client
    agent = SalesCoachAgent()

    # Execute
    result = await agent.get_transcript(call_id="call123")

    # Verify
    mock_gong_mcp_client.get_call_transcript.assert_called_once_with("call123")
    assert result.call_id == "call123"
    assert result.title == "Test Call"


@pytest.mark.asyncio
@patch('agents.sales_coach_agent.GongMCPClient')
async def test_get_transcript_error(MockGongMCPClient):
    """Test the get_transcript method with an error response."""
    # Setup
    mock_client = AsyncMock(spec=GongMCPClient)
    mock_client.get_call_transcript.side_effect = MCPError(
        error_type="not_found",
        message="Call not found",
        status_code=404
    )
    MockGongMCPClient.return_value = mock_client
    agent = SalesCoachAgent()

    # Execute and verify
    with pytest.raises(MCPError) as exc_info:
        await agent.get_transcript(call_id="invalid_id")

    # Verify
    assert exc_info.value.error_type == "not_found"
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
@patch('agents.sales_coach_agent.GongMCPClient')
async def test_get_call_insights(MockGongMCPClient, mock_gong_mcp_client):
    """Test the get_call_insights method."""
    # Setup
    MockGongMCPClient.return_value = mock_gong_mcp_client
    agent = SalesCoachAgent()

    # Execute
    result = await agent.get_call_insights(call_id="call123")

    # Verify
    mock_gong_mcp_client.get_call_insights.assert_called_once_with("call123")
    assert len(result) == 1
    assert result[0].id == "insight1"
    assert result[0].category == "objection"


@pytest.mark.asyncio
@patch('agents.sales_coach_agent.GongMCPClient')
async def test_get_call_summary(MockGongMCPClient, mock_gong_mcp_client):
    """Test the get_call_summary method."""
    # Setup
    MockGongMCPClient.return_value = mock_gong_mcp_client
    agent = SalesCoachAgent()

    # Execute
    result = await agent.get_call_summary(call_id="call123")

    # Verify
    mock_gong_mcp_client.get_call_summary.assert_called_once_with("call123")
    assert result.call_id == "call123"
    assert result.summary_text == "This is a summary of the call"


@pytest.mark.asyncio
@patch('agents.sales_coach_agent.GongMCPClient')
async def test_search_calls(MockGongMCPClient, mock_gong_mcp_client):
    """Test the search_calls method."""
    # Setup
    MockGongMCPClient.return_value = mock_gong_mcp_client
    agent = SalesCoachAgent()

    # Execute
    result = await agent.search_calls(query="test", limit=10)

    # Verify
    mock_gong_mcp_client.search_calls.assert_called_once_with("test", 10)
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "call123"
