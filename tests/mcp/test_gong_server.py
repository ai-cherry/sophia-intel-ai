"""
Tests for the Gong MCP server.
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Import the Gong server module
from mcp.gong.server import app, router
from schemas.gong import CallTranscript, CallInsight, CallSummary


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_gong_api():
    """Create a mock for the Gong API."""
    with patch("mcp.gong.server.GongAPI") as mock:
        yield mock


def test_get_call_transcript(test_client, mock_gong_api):
    """Test the transcript endpoint."""
    # Mock data
    call_id = "call123"
    mock_transcript = {
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

    # Configure the mock
    mock_instance = mock_gong_api.return_value
    mock_instance.get_call_transcript.return_value = mock_transcript

    # Make the request
    response = test_client.get(f"/calls/{call_id}/transcript")

    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["call_id"] == call_id
    assert data["data"]["title"] == "Sales Call with Acme Inc"

    # Verify the mock was called
    mock_instance.get_call_transcript.assert_called_once_with(call_id)


def test_get_call_insights(test_client, mock_gong_api):
    """Test the insights endpoint."""
    # Mock data
    call_id = "call123"
    mock_insights = [
        {
            "id": "insight1",
            "call_id": call_id,
            "category": "objection",
            "text": "Customer expressed concern about pricing",
            "confidence": 0.85,
            "segment_ids": ["seg1", "seg2"],
            "timestamp": 125.5
        }
    ]

    # Configure the mock
    mock_instance = mock_gong_api.return_value
    mock_instance.get_call_insights.return_value = mock_insights

    # Make the request
    response = test_client.get(f"/calls/{call_id}/insights")

    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "insight1"
    assert data["data"][0]["category"] == "objection"

    # Verify the mock was called
    mock_instance.get_call_insights.assert_called_once_with(call_id)


def test_get_call_summary(test_client, mock_gong_api):
    """Test the summary endpoint."""
    # Mock data
    call_id = "call123"
    mock_summary = {
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
            }
        ],
        "action_items": ["Send pricing document"],
        "sentiment_score": 0.4
    }

    # Configure the mock
    mock_instance = mock_gong_api.return_value
    mock_instance.get_call_summary.return_value = mock_summary

    # Make the request
    response = test_client.get(f"/calls/{call_id}/summary")

    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["call_id"] == call_id
    assert data["data"]["summary_text"] == "This was a productive call where we discussed pricing and timeline."

    # Verify the mock was called
    mock_instance.get_call_summary.assert_called_once_with(call_id)


def test_search_calls(test_client, mock_gong_api):
    """Test the search endpoint."""
    # Mock data
    query = "pricing"
    limit = 5
    mock_results = {
        "data": [
            {"call_id": "call123", "title": "Pricing Discussion"}
        ],
        "meta": {
            "has_more": False,
            "next_cursor": None
        }
    }

    # Configure the mock
    mock_instance = mock_gong_api.return_value
    mock_instance.search_calls.return_value = mock_results

    # Make the request
    response = test_client.get(f"/calls/search?query={query}&limit={limit}")

    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["title"] == "Pricing Discussion"
    assert data["meta"]["has_more"] is False

    # Verify the mock was called
    mock_instance.search_calls.assert_called_once_with(
        query=query, limit=limit)


def test_health_check(test_client, mock_gong_api):
    """Test the health check endpoint."""
    # Configure the mock
    mock_instance = mock_gong_api.return_value
    mock_instance.health_check.return_value = {"status": "healthy"}

    # Make the request
    response = test_client.get("/health")

    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

    # Verify the mock was called
    mock_instance.health_check.assert_called_once()


def test_error_handling(test_client, mock_gong_api):
    """Test error handling in the server."""
    # Mock an error
    call_id = "call123"
    mock_instance = mock_gong_api.return_value
    mock_instance.get_call_transcript.side_effect = Exception("API Error")

    # Make the request
    response = test_client.get(f"/calls/{call_id}/transcript")

    # Verify the error response
    assert response.status_code == 500
    data = response.json()
    assert data["error_type"] == "upstream_error"
    assert "API Error" in data["error"]
