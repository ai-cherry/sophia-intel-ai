"""
Looker API Integration Tests

Tests Looker API connectivity and basic query operations.
Requires LOOKER_BASE_URL, LOOKER_CLIENT_ID, LOOKER_CLIENT_SECRET in .env.local
"""

import os
import pytest
import requests
from typing import Dict, Any, Optional


@pytest.mark.integration
@pytest.mark.looker
def test_looker_authentication():
    """Test Looker API authentication."""
    base_url = os.getenv("LOOKER_BASE_URL", "").rstrip("/")
    client_id = os.getenv("LOOKER_CLIENT_ID")
    client_secret = os.getenv("LOOKER_CLIENT_SECRET")
    
    if not all([base_url, client_id, client_secret]):
        pytest.skip("LOOKER_BASE_URL, LOOKER_CLIENT_ID, LOOKER_CLIENT_SECRET required")
    
    auth_data = {
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/4.0/login",
            data=auth_data,
            timeout=15
        )
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        
        access_token = token_data["access_token"]
        os.environ["_LOOKER_ACCESS_TOKEN"] = access_token
        os.environ["_LOOKER_BASE_URL"] = base_url
        
        print(f"✅ Looker auth successful: {base_url}")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Looker authentication failed: {e}")


@pytest.mark.integration
@pytest.mark.looker
def test_looker_list_looks():
    """Test listing Looker saved looks."""
    access_token = os.getenv("_LOOKER_ACCESS_TOKEN")
    base_url = os.getenv("_LOOKER_BASE_URL")
    
    if not access_token or not base_url:
        pytest.skip("Looker authentication required")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(
            f"{base_url}/api/4.0/looks",
            headers=headers,
            params={"limit": 10},
            timeout=15
        )
        assert response.status_code == 200
        
        looks = response.json()
        print(f"✅ Looker looks retrieved: {len(looks)} looks")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Looker looks: {e}")


def _has_looker_env() -> bool:
    return bool(os.getenv("LOOKER_BASE_URL") and os.getenv("LOOKER_CLIENT_ID"))


if __name__ == "__main__":
    if _has_looker_env():
        print("Testing Looker integration...")
        test_looker_authentication()
        test_looker_list_looks()
        print("✅ Looker integration tests passed")
    else:
        print("⚪ Skipping Looker tests - credentials not configured")
