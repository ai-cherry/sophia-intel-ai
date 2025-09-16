"""
Intercom API Integration Tests

Tests Intercom customer messaging API connectivity and basic operations.
Requires INTERCOM_ACCESS_TOKEN in .env.local
"""

import os
import pytest
import requests
from typing import Dict, Any, List, Optional


@pytest.mark.integration
@pytest.mark.intercom
def test_intercom_authentication():
    """Test Intercom API authentication."""
    access_token = os.getenv("INTERCOM_ACCESS_TOKEN")
    
    if not access_token:
        pytest.skip("INTERCOM_ACCESS_TOKEN not configured")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        # Test with me endpoint (current authenticated app info)
        response = requests.get(
            "https://api.intercom.io/me",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200
        
        app_info = response.json()
        assert "type" in app_info
        assert "app" in app_info or "workspace" in app_info
        
        app_name = app_info.get("name", "Unknown")
        app_type = app_info.get("type", "Unknown")
        
        print(f"✅ Intercom auth successful: {app_name} ({app_type})")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Intercom authentication failed: {e}")


@pytest.mark.integration
@pytest.mark.intercom
def test_intercom_list_conversations():
    """Test listing Intercom conversations."""
    access_token = os.getenv("INTERCOM_ACCESS_TOKEN")
    
    if not access_token:
        pytest.skip("INTERCOM_ACCESS_TOKEN not configured")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        params = {
            "per_page": 10,
            "order": "desc"
        }
        
        response = requests.get(
            "https://api.intercom.io/conversations",
            headers=headers,
            params=params,
            timeout=15
        )
        assert response.status_code == 200
        
        conversations_data = response.json()
        assert "conversations" in conversations_data
        assert "total_count" in conversations_data
        
        conversations = conversations_data["conversations"]
        total_count = conversations_data["total_count"]
        
        print(f"✅ Intercom conversations retrieved: {len(conversations)} conversations (total: {total_count})")
        
        # Validate conversation structure
        if conversations:
            first_conv = conversations[0]
            required_fields = ["id", "created_at", "state"]
            for field in required_fields:
                assert field in first_conv, f"Missing field {field}"
                
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Intercom conversations: {e}")


@pytest.mark.integration
@pytest.mark.intercom
def test_intercom_list_contacts():
    """Test listing Intercom contacts (users)."""
    access_token = os.getenv("INTERCOM_ACCESS_TOKEN")
    
    if not access_token:
        pytest.skip("INTERCOM_ACCESS_TOKEN not configured")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        params = {
            "per_page": 10,
            "order": "desc"
        }
        
        response = requests.get(
            "https://api.intercom.io/contacts",
            headers=headers,
            params=params,
            timeout=15
        )
        assert response.status_code == 200
        
        contacts_data = response.json()
        assert "data" in contacts_data
        
        contacts = contacts_data["data"]
        total_count = contacts_data.get("total_count", len(contacts))
        
        print(f"✅ Intercom contacts retrieved: {len(contacts)} contacts (total: {total_count})")
        
        # Validate contact structure
        if contacts:
            first_contact = contacts[0]
            required_fields = ["id", "type"]
            for field in required_fields:
                assert field in first_contact, f"Missing field {field}"
                
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Intercom contacts: {e}")


@pytest.mark.integration
@pytest.mark.intercom
def test_intercom_list_admins():
    """Test listing Intercom team admins."""
    access_token = os.getenv("INTERCOM_ACCESS_TOKEN")
    
    if not access_token:
        pytest.skip("INTERCOM_ACCESS_TOKEN not configured")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(
            "https://api.intercom.io/admins",
            headers=headers,
            timeout=15
        )
        assert response.status_code == 200
        
        admins_data = response.json()
        assert "admins" in admins_data
        
        admins = admins_data["admins"]
        print(f"✅ Intercom admins retrieved: {len(admins)} admins")
        
        # Validate admin structure
        if admins:
            first_admin = admins[0]
            required_fields = ["id", "name", "email"]
            for field in required_fields:
                assert field in first_admin, f"Missing field {field}"
                
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list Intercom admins: {e}")


@pytest.mark.integration
@pytest.mark.intercom
def test_intercom_search_conversations():
    """Test searching Intercom conversations."""
    access_token = os.getenv("INTERCOM_ACCESS_TOKEN")
    
    if not access_token:
        pytest.skip("INTERCOM_ACCESS_TOKEN not configured")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Search for conversations from the last 30 days
    search_payload = {
        "query": {
            "operator": "AND",
            "value": [
                {
                    "field": "created_at",
                    "operator": ">",
                    "value": 1693526400  # 30 days ago (approximate)
                }
            ]
        },
        "pagination": {
            "per_page": 5
        }
    }
    
    try:
        response = requests.post(
            "https://api.intercom.io/conversations/search",
            headers=headers,
            json=search_payload,
            timeout=15
        )
        assert response.status_code == 200
        
        search_results = response.json()
        assert "conversations" in search_results
        
        conversations = search_results["conversations"]
        total_count = search_results.get("total_count", len(conversations))
        
        print(f"✅ Intercom conversation search: {len(conversations)} results (total: {total_count})")
        
    except requests.exceptions.RequestException as e:
        # Search might not be available on all plans
        if "403" in str(e) or "402" in str(e):
            pytest.skip(f"Intercom conversation search not available on current plan: {e}")
        else:
            pytest.fail(f"Failed to search Intercom conversations: {e}")


@pytest.mark.integration
@pytest.mark.intercom
def test_intercom_create_note_optional():
    """Test creating a note on a contact (optional - requires INTERCOM_ALLOW_WRITE=true)."""
    if not os.getenv("INTERCOM_ALLOW_WRITE"):
        pytest.skip("INTERCOM_ALLOW_WRITE not enabled - skipping write operations")
    
    access_token = os.getenv("INTERCOM_ACCESS_TOKEN")
    test_contact_id = os.getenv("INTERCOM_TEST_CONTACT_ID")
    
    if not access_token:
        pytest.skip("INTERCOM_ACCESS_TOKEN not configured")
        
    if not test_contact_id:
        pytest.skip("INTERCOM_TEST_CONTACT_ID required for write operations")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    import time
    timestamp = int(time.time())
    note_data = {
        "body": f"Integration test note created at {timestamp}",
        "contact_id": test_contact_id
    }
    
    try:
        response = requests.post(
            "https://api.intercom.io/notes",
            headers=headers,
            json=note_data,
            timeout=15
        )
        assert response.status_code == 200
        
        created_note = response.json()
        assert "id" in created_note
        note_id = created_note["id"]
        
        print(f"✅ Intercom note created: {note_id}")
        
        # Note: Notes typically can't be deleted via API, so no cleanup
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to create Intercom note: {e}")


def _has_intercom_env() -> bool:
    """Check if Intercom environment variables are configured."""
    return bool(os.getenv("INTERCOM_ACCESS_TOKEN"))


if __name__ == "__main__":
    # Quick smoke test when run directly
    if _has_intercom_env():
        print("Testing Intercom integration...")
        test_intercom_authentication()
        test_intercom_list_conversations()
        print("✅ Intercom integration tests passed")
    else:
        print("⚪ Skipping Intercom tests - credentials not configured")
