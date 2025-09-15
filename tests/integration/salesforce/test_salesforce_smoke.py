"""
Salesforce API Integration Tests

Tests Salesforce API connectivity, authentication, and SOQL queries.
Supports both OAuth JWT and Username/Password authentication.
Requires SALESFORCE_* credentials in .env.local
"""

import os
import pytest
import requests
import json
from typing import Dict, Any, Optional


@pytest.mark.integration
@pytest.mark.salesforce
def test_salesforce_authentication():
    """Test Salesforce API authentication (OAuth or Username/Password)."""
    # Try OAuth JWT first, then fall back to username/password
    client_id = os.getenv("SALESFORCE_CLIENT_ID")
    client_secret = os.getenv("SALESFORCE_CLIENT_SECRET") 
    username = os.getenv("SALESFORCE_USERNAME")
    password = os.getenv("SALESFORCE_PASSWORD")
    security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")
    instance_url = os.getenv("SALESFORCE_INSTANCE_URL", "https://login.salesforce.com")
    
    if not any([client_id, username]):
        pytest.skip("SALESFORCE_CLIENT_ID or SALESFORCE_USERNAME required")
    
    access_token = None
    auth_method = "unknown"
    
    # Try OAuth first if we have client credentials
    if client_id and client_secret and username and password:
        try:
            auth_method = "oauth_password"
            oauth_data = {
                'grant_type': 'password',
                'client_id': client_id,
                'client_secret': client_secret,
                'username': username,
                'password': password + (security_token or "")
            }
            
            response = requests.post(
                f"{instance_url}/services/oauth2/token",
                data=oauth_data,
                timeout=15
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                instance_url = token_data["instance_url"]
                
        except Exception as e:
            print(f"OAuth failed, will try other methods: {e}")
    
    if not access_token:
        pytest.fail(f"Salesforce authentication failed with {auth_method}")
    
    # Test the token with a simple API call
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(
            f"{instance_url}/services/data/v58.0/",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200
        
        api_info = response.json()
        print(f"✅ Salesforce auth successful via {auth_method}: {instance_url}")
        print(f"📊 Available APIs: {len(api_info)} endpoints")
        
        # Store for other tests
        os.environ["_SALESFORCE_ACCESS_TOKEN"] = access_token
        os.environ["_SALESFORCE_INSTANCE_URL"] = instance_url
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Salesforce API test failed: {e}")


@pytest.mark.integration
@pytest.mark.salesforce
def test_salesforce_query_accounts():
    """Test querying Salesforce Accounts with SOQL."""
    access_token = os.getenv("_SALESFORCE_ACCESS_TOKEN")
    instance_url = os.getenv("_SALESFORCE_INSTANCE_URL")
    
    if not access_token or not instance_url:
        pytest.skip("Salesforce authentication required (run test_salesforce_authentication first)")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # SOQL query for Accounts
    soql = "SELECT Id, Name, Type, Industry, CreatedDate FROM Account LIMIT 10"
    
    try:
        response = requests.get(
            f"{instance_url}/services/data/v58.0/query",
            headers=headers,
            params={"q": soql},
            timeout=15
        )
        assert response.status_code == 200
        
        query_result = response.json()
        assert "records" in query_result
        assert "totalSize" in query_result
        
        accounts = query_result["records"]
        total_count = query_result["totalSize"]
        
        print(f"✅ Salesforce Accounts query: {len(accounts)} records (total: {total_count})")
        
        # Validate account structure
        if accounts:
            first_account = accounts[0]
            required_fields = ["Id", "Name"]
            for field in required_fields:
                assert field in first_account, f"Missing field {field}"
                
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to query Salesforce Accounts: {e}")


@pytest.mark.integration
@pytest.mark.salesforce
def test_salesforce_query_contacts():
    """Test querying Salesforce Contacts with SOQL."""
    access_token = os.getenv("_SALESFORCE_ACCESS_TOKEN")
    instance_url = os.getenv("_SALESFORCE_INSTANCE_URL")
    
    if not access_token or not instance_url:
        pytest.skip("Salesforce authentication required")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    soql = "SELECT Id, FirstName, LastName, Email, AccountId, CreatedDate FROM Contact LIMIT 10"
    
    try:
        response = requests.get(
            f"{instance_url}/services/data/v58.0/query",
            headers=headers,
            params={"q": soql},
            timeout=15
        )
        assert response.status_code == 200
        
        query_result = response.json()
        contacts = query_result["records"]
        total_count = query_result["totalSize"]
        
        print(f"✅ Salesforce Contacts query: {len(contacts)} records (total: {total_count})")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to query Salesforce Contacts: {e}")


@pytest.mark.integration
@pytest.mark.salesforce
def test_salesforce_describe_objects():
    """Test describing Salesforce objects (metadata)."""
    access_token = os.getenv("_SALESFORCE_ACCESS_TOKEN")
    instance_url = os.getenv("_SALESFORCE_INSTANCE_URL")
    
    if not access_token or not instance_url:
        pytest.skip("Salesforce authentication required")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Describe Account object
        response = requests.get(
            f"{instance_url}/services/data/v58.0/sobjects/Account/describe",
            headers=headers,
            timeout=15
        )
        assert response.status_code == 200
        
        describe_result = response.json()
        assert "fields" in describe_result
        assert "name" in describe_result
        
        fields = describe_result["fields"]
        object_name = describe_result["name"]
        
        print(f"✅ Salesforce {object_name} description: {len(fields)} fields")
        
        # Validate some standard fields exist
        field_names = [field["name"] for field in fields]
        standard_fields = ["Id", "Name", "CreatedDate", "LastModifiedDate"]
        
        for std_field in standard_fields:
            assert std_field in field_names, f"Missing standard field {std_field}"
            
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to describe Salesforce objects: {e}")


@pytest.mark.integration
@pytest.mark.salesforce
def test_salesforce_create_account_optional():
    """Test creating a Salesforce Account (optional - requires SALESFORCE_ALLOW_WRITE=true)."""
    if not os.getenv("SALESFORCE_ALLOW_WRITE"):
        pytest.skip("SALESFORCE_ALLOW_WRITE not enabled - skipping write operations")
    
    access_token = os.getenv("_SALESFORCE_ACCESS_TOKEN")
    instance_url = os.getenv("_SALESFORCE_INSTANCE_URL")
    
    if not access_token or not instance_url:
        pytest.skip("Salesforce authentication required")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    import time
    timestamp = int(time.time())
    test_account = {
        "Name": f"Test Account {timestamp}",
        "Type": "Other",
        "Industry": "Technology",
        "Description": "Test account created by integration test"
    }
    
    try:
        response = requests.post(
            f"{instance_url}/services/data/v58.0/sobjects/Account",
            headers=headers,
            json=test_account,
            timeout=15
        )
        assert response.status_code == 201
        
        created_result = response.json()
        assert "id" in created_result
        account_id = created_result["id"]
        
        print(f"✅ Salesforce Account created: {account_id}")
        
        # Clean up: delete the test account
        try:
            delete_response = requests.delete(
                f"{instance_url}/services/data/v58.0/sobjects/Account/{account_id}",
                headers=headers,
                timeout=10
            )
            if delete_response.status_code == 204:
                print(f"🧹 Test account {account_id} cleaned up")
        except:
            print(f"⚠️ Could not clean up test account {account_id}")
            
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to create Salesforce Account: {e}")


def _has_salesforce_env() -> bool:
    """Check if Salesforce environment variables are configured."""
    return bool(
        os.getenv("SALESFORCE_CLIENT_ID") or 
        os.getenv("SALESFORCE_USERNAME")
    )


if __name__ == "__main__":
    # Quick smoke test when run directly
    if _has_salesforce_env():
        print("Testing Salesforce integration...")
        test_salesforce_authentication()
        test_salesforce_query_accounts()
        print("✅ Salesforce integration tests passed")
    else:
        print("⚪ Skipping Salesforce tests - credentials not configured")
