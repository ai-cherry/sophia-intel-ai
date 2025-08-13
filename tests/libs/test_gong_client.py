"""
Tests for the Gong MCP client.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from datetime import datetime

from libs.mcp_client.gong import GongMCPClient
from schemas.gong import CallTranscript, CallInsight, CallSummary, MCPError


@pytest.fixture
def mock_response():
    """Create a mock response for testing."""
    def _create_mock_response(data, status_code=200):
        mock_resp = AsyncMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = data
        mock_resp.raise_for_status = AsyncMock()
        if status_code >= 400:
            mock_resp.raise_for_status.side_effect = Exception(
                f"HTTP {status_code}")
        return mock_resp
    return _create_mock_response


@pytest.fixture
def gong_client():
    """Create a Gong MCP client for testing."""
    return GongMCPClient()


@pytest.mark.asyncio
async def test_get_call_transcript(gong_client, mock_response):
    """Test retrieving a call transcript."""
    # Mock data
    call_id = "call123"
    mock_data = {
        "data": {
            "call_id": call_id,
            "title": "Sales Call with Acme Inc",
            "date": "2025-08-01T14:30:00Z",
            "duration": 1800.5,
            "participants": [
                {
                    "id": "user1",
                    "name": "John Sales",
                    "email": "john@company.com",
                    "role": "speaker",
                    "company": "Our Company"
                },
                {
                    "id": "user2",
                    "name": "Jane Customer",
                    "email": "jane@acme.com",
                    "role": "speaker",
                    "company": "Acme Inc"
                }
            ],
            "segments": [
                {
                    "start_time": 0.0,
                    "end_time": 10.5,
                    "speaker_id": "user1",
                    "text": "Hello, thanks for joining the call today."
                }
            ]
        }
    }

    # Mock the request
    with patch("httpx.AsyncClient.request", return_value=mock_response(mock_data)) as mock_request:
        transcript = await gong_client.get_call_transcript(call_id)

        # Verify the request was made correctly
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert f"/calls/{call_id}/transcript" in args[1]

        # Verify the response parsing
        assert isinstance(transcript, CallTranscript)
        assert transcript.call_id == call_id
        assert transcript.title == "Sales Call with Acme Inc"
        assert transcript.participants[0].name == "John Sales"
        assert transcript.segments[0].text == "Hello, thanks for joining the call today."


@pytest.mark.asyncio
async def test_get_call_insights(gong_client, mock_response):
    """Test retrieving call insights."""
    # Mock data
    call_id = "call123"
    mock_data = {
        "data": [
            {
                "id": "insight1",
                "call_id": call_id,
                "category": "objection",
                "text": "Customer expressed concern about pricing",
                "confidence": 0.85,
                "segment_ids": ["seg1", "seg2"],
                "timestamp": 125.5
            },
            {
                "id": "insight2",
                "call_id": call_id,
                "category": "question",
                "text": "Customer asked about implementation timeline",
                "confidence": 0.92,
                "segment_ids": ["seg3"],
                "timestamp": 345.2
            }
        ]
    }

    # Mock the request
    with patch("httpx.AsyncClient.request", return_value=mock_response(mock_data)) as mock_request:
        insights = await gong_client.get_call_insights(call_id)

        # Verify the request was made correctly
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert f"/calls/{call_id}/insights" in args[1]

        # Verify the response parsing
        assert len(insights) == 2
        assert all(isinstance(insight, CallInsight) for insight in insights)
        assert insights[0].id == "insight1"
        assert insights[0].category == "objection"
        assert insights[1].text == "Customer asked about implementation timeline"


@pytest.mark.asyncio
async def test_get_call_summary(gong_client, mock_response):
    """Test retrieving a call summary."""
    # Mock data
    call_id = "call123"
    mock_data = {
        "data": {
            "call_id": call_id,
            "title": "Sales Call with Acme Inc",
            "date": "2025-08-01T14:30:00Z",
            "duration": 1800.5,
            "summary_text": "This was a productive call where we discussed pricing and timeline.",
            "topics": [
                {
                    "name": "Pricing",
                    "importance": 0.8,
                    "segments": [1, 2, 3]
                },
                {
                    "name": "Implementation",
                    "importance": 0.6,
                    "segments": [4, 5]
                }
            ],
            "action_items": ["Send pricing document", "Schedule follow-up call"],
            "sentiment_score": 0.4
        }
    }

    # Mock the request
    with patch("httpx.AsyncClient.request", return_value=mock_response(mock_data)) as mock_request:
        summary = await gong_client.get_call_summary(call_id)

        # Verify the request was made correctly
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert f"/calls/{call_id}/summary" in args[1]

        # Verify the response parsing
        assert isinstance(summary, CallSummary)
        assert summary.call_id == call_id
        assert summary.summary_text == "This was a productive call where we discussed pricing and timeline."
        assert len(summary.topics) == 2
        assert summary.topics[0].name == "Pricing"
        assert len(summary.action_items) == 2
        assert summary.sentiment_score == 0.4


@pytest.mark.asyncio
async def test_search_calls(gong_client, mock_response):
    """Test searching for calls."""
    # Mock data
    query = "pricing discussion"
    limit = 5
    mock_data = {
        "data": [
            {"call_id": "call123", "title": "Acme Inc - Pricing Discussion"},
            {"call_id": "call456", "title": "XYZ Corp - Quarterly Review"}
        ],
        "meta": {
            "has_more": True,
            "next_cursor": "next-page-token"
        }
    }

    # Mock the request
    with patch("httpx.AsyncClient.request", return_value=mock_response(mock_data)) as mock_request:
        results = await gong_client.search_calls(query, limit)

        # Verify the request was made correctly
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert "/calls/search" in args[1]
        assert kwargs["params"] == {"query": query, "limit": limit}

        # Verify the response parsing
        assert len(results["data"]) == 2
        assert results["meta"]["has_more"] is True
        assert results["meta"]["next_cursor"] == "next-page-token"


@pytest.mark.asyncio
async def test_error_handling(gong_client, mock_response):
    """Test error handling in the MCP client."""
    # Mock error response
    call_id = "call123"
    error_resp = {
        "error_type": "upstream_error",
        "error": "Failed to connect to Gong API"
    }

    # Mock the request to raise an error
    with patch("httpx.AsyncClient.request", return_value=mock_response(error_resp, 500)) as mock_request:
        with pytest.raises(MCPError) as exc_info:
            await gong_client.get_call_transcript(call_id)

        # Verify error handling
        assert exc_info.value.error_type == "upstream_error"
        assert "Failed to connect to Gong API" in str(exc_info.value)
        assert exc_info.value.status_code == 500
