#!/usr/bin/env python3
"""
Airbyte API smoke test - quick connectivity check
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('.env.local'):
    load_dotenv('.env.local')


def test_airbyte():
    """Quick Airbyte connectivity test"""
    api_url = os.getenv("AIRBYTE_API_URL", "").rstrip("/")
    api_key = os.getenv("AIRBYTE_API_KEY")
    
    if not api_url:
        print("❌ AIRBYTE_API_URL not configured")
        return False
        
    if not api_key:
        print("❌ AIRBYTE_API_KEY not configured") 
        return False
    
    try:
        # Test health endpoint
        health_response = requests.get(f"{api_url}/health", timeout=10)
        if health_response.status_code != 200:
            print(f"❌ Airbyte health check failed: {health_response.status_code}")
            return False
        
        print("✅ Airbyte health check passed")
        
        # Test authenticated endpoint
        headers = {"Authorization": f"Bearer {api_key}"}
        auth_response = requests.get(f"{api_url}/v1/workspaces", headers=headers, timeout=10)
        
        if auth_response.status_code == 200:
            workspaces = auth_response.json()
            workspace_count = len(workspaces.get('workspaces', workspaces))
            print(f"✅ Airbyte auth successful: {workspace_count} workspaces")
            return True
        else:
            print(f"❌ Airbyte auth failed: {auth_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Airbyte connection failed: {e}")
        return False


if __name__ == "__main__":
    success = test_airbyte()
    sys.exit(0 if success else 1)
