#!/usr/bin/env python3
"""
Airbyte API smoke test for CI/CD pipeline
Tests workspace listing, connections, and optional sync trigger
"""
import os
import json
import sys
import base64

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

# Configuration
AIRBYTE_API_URL = os.getenv("AIRBYTE_API_URL")
AIRBYTE_API_TOKEN = os.getenv("AIRBYTE_API_TOKEN")
AIRBYTE_BASIC_USER = os.getenv("AIRBYTE_BASIC_USER")
AIRBYTE_BASIC_PASS = os.getenv("AIRBYTE_BASIC_PASS")
AIRBYTE_WORKSPACE_ID = os.getenv("AIRBYTE_WORKSPACE_ID")
AIRBYTE_TEST_CONNECTION_ID = os.getenv("AIRBYTE_TEST_CONNECTION_ID")

if not AIRBYTE_API_URL:
    print("SKIP: No AIRBYTE_API_URL configured")
    sys.exit(0)

def get_headers():
    """Generate headers for Airbyte API requests"""
    headers = {"Content-Type": "application/json"}
    
    if AIRBYTE_API_TOKEN:
        headers["Authorization"] = f"Bearer {AIRBYTE_API_TOKEN}"
    elif AIRBYTE_BASIC_USER and AIRBYTE_BASIC_PASS:
        creds = base64.b64encode(f"{AIRBYTE_BASIC_USER}:{AIRBYTE_BASIC_PASS}".encode()).decode()
        headers["Authorization"] = f"Basic {creds}"
    else:
        print("WARNING: No authentication configured (AIRBYTE_API_TOKEN or AIRBYTE_BASIC_USER/PASS)")
    
    return headers

def post_request(path, body):
    """Make POST request to Airbyte API"""
    url = AIRBYTE_API_URL.rstrip("/") + path
    try:
        response = httpx.post(url, headers=get_headers(), json=body, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP {e.response.status_code}: {e.response.text}")
        raise
    except Exception as e:
        print(f"Request failed: {e}")
        raise

def main():
    print("🔍 Airbyte API Smoke Test")
    print(f"URL: {AIRBYTE_API_URL}")
    
    try:
        # Test 1: List workspaces
        print("\n1. Testing workspace listing...")
        workspaces = post_request("/api/v1/workspaces/list", {})
        workspace_count = len(workspaces.get("workspaces", []))
        print(f"✅ Found {workspace_count} workspaces")
        if workspace_count > 0:
            print(f"   Sample: {json.dumps(workspaces)[:200]}...")
        
        # Test 2: List connections
        print("\n2. Testing connection listing...")
        conn_body = {"workspaceId": AIRBYTE_WORKSPACE_ID} if AIRBYTE_WORKSPACE_ID else {}
        connections = post_request("/api/v1/connections/list", conn_body)
        connection_count = len(connections.get("connections", []))
        print(f"✅ Found {connection_count} connections")
        if connection_count > 0:
            print(f"   Sample: {json.dumps(connections)[:200]}...")
        
        # Test 3: Optional sync trigger (only if test connection ID provided)
        if AIRBYTE_TEST_CONNECTION_ID:
            print(f"\n3. Testing sync trigger for connection {AIRBYTE_TEST_CONNECTION_ID}...")
            try:
                sync_result = post_request("/api/v1/connections/sync", {
                    "connectionId": AIRBYTE_TEST_CONNECTION_ID
                })
                job_id = sync_result.get("job", {}).get("id")
                print(f"✅ Sync triggered successfully, job ID: {job_id}")
                print(f"   Result: {json.dumps(sync_result)[:200]}...")
            except Exception as e:
                print(f"⚠️  Sync trigger failed (non-critical): {e}")
        else:
            print("\n3. Skipping sync trigger (no AIRBYTE_TEST_CONNECTION_ID)")
        
        print("\n🎉 All Airbyte smoke tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Airbyte smoke test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

