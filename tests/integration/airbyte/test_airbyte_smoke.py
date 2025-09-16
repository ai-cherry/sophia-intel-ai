"""
Airbyte API Integration Tests

Tests Airbyte server connectivity, connection management, and sync operations.
Requires AIRBYTE_API_URL and AIRBYTE_API_KEY in .env.local
"""

import os
import pytest
import requests
from typing import Dict, Any, Optional


@pytest.mark.integration
@pytest.mark.airbyte
def test_airbyte_server_health():
    """Test Airbyte server health endpoint."""
    api_url = os.getenv("AIRBYTE_API_URL", "").rstrip("/")
    if not api_url:
        pytest.skip("AIRBYTE_API_URL not configured")
    
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        assert response.status_code == 200
        health_data = response.json()
        assert "available" in health_data or "status" in health_data
        print(f"✅ Airbyte server health: {health_data}")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Airbyte health check failed: {e}")


@pytest.mark.integration
@pytest.mark.airbyte
def test_airbyte_authentication():
    """Test Airbyte API authentication."""
    api_url = os.getenv("AIRBYTE_API_URL", "").rstrip("/")
    api_key = os.getenv("AIRBYTE_API_KEY")
    
    if not api_url or not api_key:
        pytest.skip("AIRBYTE_API_URL and AIRBYTE_API_KEY required")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # Test with workspaces endpoint (common authenticated endpoint)
        response = requests.get(f"{api_url}/v1/workspaces", headers=headers, timeout=10)
        assert response.status_code in [200, 401, 403]  # 401/403 = auth issue, not connectivity
        
        if response.status_code == 200:
            workspaces = response.json()
            assert "workspaces" in workspaces or isinstance(workspaces, list)
            print(f"✅ Airbyte auth successful: {len(workspaces.get('workspaces', workspaces))} workspaces")
        else:
            pytest.fail(f"Airbyte authentication failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Airbyte API request failed: {e}")


@pytest.mark.integration
@pytest.mark.airbyte
def test_airbyte_list_connections():
    """Test listing Airbyte connections."""
    api_url = os.getenv("AIRBYTE_API_URL", "").rstrip("/")
    api_key = os.getenv("AIRBYTE_API_KEY")
    
    if not api_url or not api_key:
        pytest.skip("AIRBYTE_API_URL and AIRBYTE_API_KEY required")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(f"{api_url}/v1/connections", headers=headers, timeout=15)
        assert response.status_code == 200
        
        connections = response.json()
        assert "connections" in connections or isinstance(connections, list)
        
        connection_list = connections.get("connections", connections)
        print(f"✅ Airbyte connections retrieved: {len(connection_list)} connections")
        
        # Validate connection structure
        if connection_list:
            first_conn = connection_list[0]
            required_fields = ["connectionId", "name", "status"]
            for field in required_fields:
                assert field in first_conn, f"Missing field {field} in connection"
                
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Airbyte connections: {e}")


@pytest.mark.integration
@pytest.mark.airbyte
def test_airbyte_list_sources():
    """Test listing Airbyte sources."""
    api_url = os.getenv("AIRBYTE_API_URL", "").rstrip("/")
    api_key = os.getenv("AIRBYTE_API_KEY")
    
    if not api_url or not api_key:
        pytest.skip("AIRBYTE_API_URL and AIRBYTE_API_KEY required")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(f"{api_url}/v1/sources", headers=headers, timeout=15)
        assert response.status_code == 200
        
        sources = response.json()
        assert "sources" in sources or isinstance(sources, list)
        
        source_list = sources.get("sources", sources)
        print(f"✅ Airbyte sources retrieved: {len(source_list)} sources")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Airbyte sources: {e}")


@pytest.mark.integration
@pytest.mark.airbyte  
def test_airbyte_trigger_sync_optional():
    """Test triggering a sync (optional - requires AIRBYTE_ALLOW_WRITE=true)."""
    if not os.getenv("AIRBYTE_ALLOW_WRITE"):
        pytest.skip("AIRBYTE_ALLOW_WRITE not enabled - skipping write operations")
    
    api_url = os.getenv("AIRBYTE_API_URL", "").rstrip("/")
    api_key = os.getenv("AIRBYTE_API_KEY")
    test_connection_id = os.getenv("AIRBYTE_TEST_CONNECTION_ID")
    
    if not all([api_url, api_key, test_connection_id]):
        pytest.skip("AIRBYTE_API_URL, AIRBYTE_API_KEY, and AIRBYTE_TEST_CONNECTION_ID required")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "connectionId": test_connection_id
    }
    
    try:
        response = requests.post(f"{api_url}/v1/jobs", headers=headers, json=payload, timeout=15)
        assert response.status_code in [200, 201]
        
        job = response.json()
        assert "jobId" in job or "id" in job
        job_id = job.get("jobId") or job.get("id")
        print(f"✅ Airbyte sync triggered: job {job_id}")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to trigger Airbyte sync: {e}")


def _has_airbyte_env() -> bool:
    """Check if Airbyte environment variables are configured."""
    return bool(os.getenv("AIRBYTE_API_URL") and os.getenv("AIRBYTE_API_KEY"))


if __name__ == "__main__":
    # Quick smoke test when run directly
    if _has_airbyte_env():
        print("Testing Airbyte integration...")
        test_airbyte_server_health()
        test_airbyte_authentication()
        print("✅ Airbyte integration tests passed")
    else:
        print("⚪ Skipping Airbyte tests - credentials not configured")
