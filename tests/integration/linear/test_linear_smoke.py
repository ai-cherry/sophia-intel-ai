"""
Linear API Integration Tests

Tests Linear issue tracking API connectivity and basic operations.
Requires LINEAR_API_KEY in .env.local
"""

import os
import pytest
import requests
from typing import Dict, Any, List, Optional


@pytest.mark.integration
@pytest.mark.linear
def test_linear_authentication():
    """Test Linear API authentication via GraphQL."""
    api_key = os.getenv("LINEAR_API_KEY")
    
    if not api_key:
        pytest.skip("LINEAR_API_KEY not configured")
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to get viewer info
    query = {
        "query": """
        query {
            viewer {
                id
                name
                email
                displayName
            }
        }
        """
    }
    
    try:
        response = requests.post(
            "https://api.linear.app/graphql",
            headers=headers,
            json=query,
            timeout=10
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "data" in result
        assert "viewer" in result["data"]
        
        viewer = result["data"]["viewer"]
        assert "id" in viewer
        assert "name" in viewer
        
        name = viewer.get("displayName") or viewer.get("name", "Unknown")
        print(f"✅ Linear auth successful: {name} ({viewer['id']})")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Linear authentication failed: {e}")


@pytest.mark.integration
@pytest.mark.linear
def test_linear_list_teams():
    """Test listing Linear teams."""
    api_key = os.getenv("LINEAR_API_KEY")
    
    if not api_key:
        pytest.skip("LINEAR_API_KEY not configured")
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    query = {
        "query": """
        query {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                }
            }
        }
        """
    }
    
    try:
        response = requests.post(
            "https://api.linear.app/graphql",
            headers=headers,
            json=query,
            timeout=15
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "data" in result
        assert "teams" in result["data"]
        
        teams = result["data"]["teams"]["nodes"]
        print(f"✅ Linear teams retrieved: {len(teams)} teams")
        
        # Store first team for other tests
        if teams:
            os.environ["_LINEAR_TEAM_ID"] = teams[0]["id"]
            
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Linear teams: {e}")


@pytest.mark.integration
@pytest.mark.linear
def test_linear_list_issues():
    """Test listing Linear issues."""
    api_key = os.getenv("LINEAR_API_KEY")
    
    if not api_key:
        pytest.skip("LINEAR_API_KEY not configured")
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    query = {
        "query": """
        query {
            issues(first: 10) {
                nodes {
                    id
                    title
                    state {
                        name
                    }
                    priority
                    createdAt
                }
            }
        }
        """
    }
    
    try:
        response = requests.post(
            "https://api.linear.app/graphql",
            headers=headers,
            json=query,
            timeout=15
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "data" in result
        assert "issues" in result["data"]
        
        issues = result["data"]["issues"]["nodes"]
        print(f"✅ Linear issues retrieved: {len(issues)} issues")
        
        # Validate issue structure
        if issues:
            first_issue = issues[0]
            required_fields = ["id", "title"]
            for field in required_fields:
                assert field in first_issue, f"Missing field {field}"
                
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Linear issues: {e}")


@pytest.mark.integration
@pytest.mark.linear
def test_linear_list_projects():
    """Test listing Linear projects."""
    api_key = os.getenv("LINEAR_API_KEY")
    
    if not api_key:
        pytest.skip("LINEAR_API_KEY not configured")
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    query = {
        "query": """
        query {
            projects(first: 10) {
                nodes {
                    id
                    name
                    description
                    state
                    progress
                }
            }
        }
        """
    }
    
    try:
        response = requests.post(
            "https://api.linear.app/graphql",
            headers=headers,
            json=query,
            timeout=15
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "data" in result
        assert "projects" in result["data"]
        
        projects = result["data"]["projects"]["nodes"]
        print(f"✅ Linear projects retrieved: {len(projects)} projects")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Linear projects: {e}")


@pytest.mark.integration
@pytest.mark.linear
def test_linear_create_issue_optional():
    """Test creating a Linear issue (optional - requires LINEAR_ALLOW_WRITE=true)."""
    if not os.getenv("LINEAR_ALLOW_WRITE"):
        pytest.skip("LINEAR_ALLOW_WRITE not enabled - skipping write operations")
    
    api_key = os.getenv("LINEAR_API_KEY")
    team_id = os.getenv("_LINEAR_TEAM_ID")
    
    if not api_key:
        pytest.skip("LINEAR_API_KEY not configured")
        
    if not team_id:
        pytest.skip("Linear team ID required (run test_linear_list_teams first)")
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    import time
    timestamp = int(time.time())
    
    query = {
        "query": """
        mutation IssueCreate($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    title
                }
            }
        }
        """,
        "variables": {
            "input": {
                "title": f"Integration Test Issue {timestamp}",
                "description": "Test issue created by integration test",
                "teamId": team_id
            }
        }
    }
    
    try:
        response = requests.post(
            "https://api.linear.app/graphql",
            headers=headers,
            json=query,
            timeout=15
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "data" in result
        assert "issueCreate" in result["data"]
        
        create_result = result["data"]["issueCreate"]
        assert create_result["success"] == True
        
        issue = create_result["issue"]
        issue_id = issue["id"]
        
        print(f"✅ Linear issue created: {issue_id} - {issue['title']}")
        
        # Note: Linear doesn't typically allow deleting issues via API
        # so we don't clean up
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to create Linear issue: {e}")


def _has_linear_env() -> bool:
    return bool(os.getenv("LINEAR_API_KEY"))


if __name__ == "__main__":
    if _has_linear_env():
        print("Testing Linear integration...")
        test_linear_authentication()
        test_linear_list_teams()
        print("✅ Linear integration tests passed")
    else:
        print("⚪ Skipping Linear tests - credentials not configured")
