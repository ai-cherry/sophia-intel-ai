"""
Asana API Integration Tests

Tests Asana project management API connectivity and basic operations.
Requires ASANA_PERSONAL_ACCESS_TOKEN in .env.local
"""

import os
import pytest
import requests
from typing import Dict, Any, List, Optional


@pytest.mark.integration
@pytest.mark.asana
def test_asana_authentication():
    """Test Asana API authentication."""
    access_token = os.getenv("ASANA_PERSONAL_ACCESS_TOKEN")
    
    if not access_token:
        pytest.skip("ASANA_PERSONAL_ACCESS_TOKEN not configured")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(
            "https://app.asana.com/api/1.0/users/me",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200
        
        user_data = response.json()
        assert "data" in user_data
        
        user = user_data["data"]
        assert "gid" in user
        assert "name" in user
        
        print(f"✅ Asana auth successful: {user['name']} ({user['gid']})")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Asana authentication failed: {e}")


@pytest.mark.integration
@pytest.mark.asana
def test_asana_list_workspaces():
    """Test listing Asana workspaces."""
    access_token = os.getenv("ASANA_PERSONAL_ACCESS_TOKEN")
    
    if not access_token:
        pytest.skip("ASANA_PERSONAL_ACCESS_TOKEN not configured")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(
            "https://app.asana.com/api/1.0/workspaces",
            headers=headers,
            timeout=15
        )
        assert response.status_code == 200
        
        workspaces_data = response.json()
        assert "data" in workspaces_data
        
        workspaces = workspaces_data["data"]
        print(f"✅ Asana workspaces retrieved: {len(workspaces)} workspaces")
        
        # Store first workspace for other tests
        if workspaces:
            os.environ["_ASANA_WORKSPACE_GID"] = workspaces[0]["gid"]
            
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Asana workspaces: {e}")


@pytest.mark.integration
@pytest.mark.asana
def test_asana_list_projects():
    """Test listing Asana projects."""
    access_token = os.getenv("ASANA_PERSONAL_ACCESS_TOKEN")
    workspace_gid = os.getenv("_ASANA_WORKSPACE_GID")
    
    if not access_token:
        pytest.skip("ASANA_PERSONAL_ACCESS_TOKEN not configured")
    
    if not workspace_gid:
        pytest.skip("Asana workspace required (run test_asana_list_workspaces first)")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        params = {"workspace": workspace_gid, "limit": 10}
        
        response = requests.get(
            "https://app.asana.com/api/1.0/projects",
            headers=headers,
            params=params,
            timeout=15
        )
        assert response.status_code == 200
        
        projects_data = response.json()
        assert "data" in projects_data
        
        projects = projects_data["data"]
        print(f"✅ Asana projects retrieved: {len(projects)} projects")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Asana projects: {e}")


@pytest.mark.integration
@pytest.mark.asana
def test_asana_list_tasks():
    """Test listing Asana tasks."""
    access_token = os.getenv("ASANA_PERSONAL_ACCESS_TOKEN")
    
    if not access_token:
        pytest.skip("ASANA_PERSONAL_ACCESS_TOKEN not configured")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        params = {"assignee": "me", "limit": 10, "completed_since": "now"}
        
        response = requests.get(
            "https://app.asana.com/api/1.0/tasks",
            headers=headers,
            params=params,
            timeout=15
        )
        assert response.status_code == 200
        
        tasks_data = response.json()
        assert "data" in tasks_data
        
        tasks = tasks_data["data"]
        print(f"✅ Asana tasks retrieved: {len(tasks)} tasks")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Asana tasks: {e}")


def _has_asana_env() -> bool:
    return bool(os.getenv("ASANA_PERSONAL_ACCESS_TOKEN"))


if __name__ == "__main__":
    if _has_asana_env():
        print("Testing Asana integration...")
        test_asana_authentication()
        test_asana_list_workspaces()
        print("✅ Asana integration tests passed")
    else:
        print("⚪ Skipping Asana tests - credentials not configured")
