"""
HubSpot CRM API Integration Tests

Tests HubSpot API connectivity, contact management, and CRM operations.
Requires HUBSPOT_API_KEY in .env.local
"""

import os
import pytest
import requests
from typing import Dict, Any, List, Optional


@pytest.mark.integration
@pytest.mark.hubspot
def test_hubspot_authentication():
    """Test HubSpot API authentication."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    
    if not api_key:
        pytest.skip("HUBSPOT_API_KEY not configured")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # Test with account-info endpoint
        response = requests.get(
            "https://api.hubapi.com/account-info/v3/details",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200
        
        account_info = response.json()
        assert "portalId" in account_info
        assert "accountType" in account_info
        
        print(f"✅ HubSpot auth successful: Portal {account_info['portalId']} ({account_info.get('accountType', 'Unknown')})")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"HubSpot authentication failed: {e}")


@pytest.mark.integration
@pytest.mark.hubspot
def test_hubspot_list_contacts():
    """Test listing HubSpot contacts."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    
    if not api_key:
        pytest.skip("HUBSPOT_API_KEY not configured")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # List contacts with basic properties
        params = {
            "properties": "email,firstname,lastname,createdate",
            "limit": 10
        }
        
        response = requests.get(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers=headers,
            params=params,
            timeout=15
        )
        assert response.status_code == 200
        
        contacts_data = response.json()
        assert "results" in contacts_data
        
        contacts = contacts_data["results"]
        print(f"✅ HubSpot contacts retrieved: {len(contacts)} contacts")
        
        # Validate contact structure
        if contacts:
            first_contact = contacts[0]
            assert "id" in first_contact
            assert "properties" in first_contact
            
            properties = first_contact["properties"]
            expected_props = ["email", "firstname", "lastname", "createdate"]
            for prop in expected_props:
                assert prop in properties, f"Missing property {prop}"
                
        # Test pagination info
        if "paging" in contacts_data:
            paging = contacts_data["paging"]
            if "next" in paging:
                print(f"📄 More contacts available via pagination")
                
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list HubSpot contacts: {e}")


@pytest.mark.integration
@pytest.mark.hubspot
def test_hubspot_search_contacts():
    """Test searching HubSpot contacts by email."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    test_email = os.getenv("HUBSPOT_TEST_EMAIL", "@")  # Default to find any email with @
    
    if not api_key:
        pytest.skip("HUBSPOT_API_KEY not configured")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    search_payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "email",
                        "operator": "CONTAINS_TOKEN",
                        "value": test_email
                    }
                ]
            }
        ],
        "properties": ["email", "firstname", "lastname"],
        "limit": 5
    }
    
    try:
        response = requests.post(
            "https://api.hubapi.com/crm/v3/objects/contacts/search",
            headers=headers,
            json=search_payload,
            timeout=15
        )
        assert response.status_code == 200
        
        search_results = response.json()
        assert "results" in search_results
        
        contacts = search_results["results"]
        print(f"✅ HubSpot contact search: {len(contacts)} contacts found with '{test_email}'")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to search HubSpot contacts: {e}")


@pytest.mark.integration
@pytest.mark.hubspot
def test_hubspot_list_companies():
    """Test listing HubSpot companies."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    
    if not api_key:
        pytest.skip("HUBSPOT_API_KEY not configured")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        params = {
            "properties": "name,domain,industry,createdate",
            "limit": 10
        }
        
        response = requests.get(
            "https://api.hubapi.com/crm/v3/objects/companies",
            headers=headers,
            params=params,
            timeout=15
        )
        assert response.status_code == 200
        
        companies_data = response.json()
        assert "results" in companies_data
        
        companies = companies_data["results"]
        print(f"✅ HubSpot companies retrieved: {len(companies)} companies")
        
        # Validate company structure
        if companies:
            first_company = companies[0]
            assert "id" in first_company
            assert "properties" in first_company
            
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list HubSpot companies: {e}")


@pytest.mark.integration
@pytest.mark.hubspot
def test_hubspot_list_deals():
    """Test listing HubSpot deals."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    
    if not api_key:
        pytest.skip("HUBSPOT_API_KEY not configured")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        params = {
            "properties": "dealname,amount,dealstage,createdate",
            "limit": 10
        }
        
        response = requests.get(
            "https://api.hubapi.com/crm/v3/objects/deals",
            headers=headers,
            params=params,
            timeout=15
        )
        assert response.status_code == 200
        
        deals_data = response.json()
        assert "results" in deals_data
        
        deals = deals_data["results"]
        print(f"✅ HubSpot deals retrieved: {len(deals)} deals")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to list HubSpot deals: {e}")


@pytest.mark.integration
@pytest.mark.hubspot
def test_hubspot_create_contact_optional():
    """Test creating a HubSpot contact (optional - requires HUBSPOT_ALLOW_WRITE=true)."""
    if not os.getenv("HUBSPOT_ALLOW_WRITE"):
        pytest.skip("HUBSPOT_ALLOW_WRITE not enabled - skipping write operations")
    
    api_key = os.getenv("HUBSPOT_API_KEY")
    
    if not api_key:
        pytest.skip("HUBSPOT_API_KEY not configured")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    import time
    timestamp = int(time.time())
    test_contact = {
        "properties": {
            "email": f"test-{timestamp}@example.com",
            "firstname": "Test",
            "lastname": f"Contact-{timestamp}",
            "company": "Test Company"
        }
    }
    
    try:
        response = requests.post(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers=headers,
            json=test_contact,
            timeout=15
        )
        assert response.status_code == 201
        
        created_contact = response.json()
        assert "id" in created_contact
        contact_id = created_contact["id"]
        
        print(f"✅ HubSpot contact created: {contact_id}")
        
        # Clean up: delete the test contact
        try:
            delete_response = requests.delete(
                f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
                headers=headers,
                timeout=10
            )
            if delete_response.status_code == 204:
                print(f"🧹 Test contact {contact_id} cleaned up")
        except:
            print(f"⚠️ Could not clean up test contact {contact_id}")
            
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to create HubSpot contact: {e}")


def _has_hubspot_env() -> bool:
    """Check if HubSpot environment variables are configured."""
    return bool(os.getenv("HUBSPOT_API_KEY"))


if __name__ == "__main__":
    # Quick smoke test when run directly
    if _has_hubspot_env():
        print("Testing HubSpot integration...")
        test_hubspot_authentication()
        test_hubspot_list_contacts()
        print("✅ HubSpot integration tests passed")
    else:
        print("⚪ Skipping HubSpot tests - credentials not configured")
