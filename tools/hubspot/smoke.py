#!/usr/bin/env python3
"""
HubSpot API smoke test - quick connectivity check
"""

import os
import sys
import requests
from dotenv import load_dotenv

if os.path.exists('.env.local'):
    load_dotenv('.env.local')

def test_hubspot():
    """Quick HubSpot connectivity test"""
    api_key = os.getenv("HUBSPOT_API_KEY")
    
    if not api_key:
        print("❌ HUBSPOT_API_KEY not configured")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get("https://api.hubapi.com/account-info/v3/details", headers=headers, timeout=10)
        
        if response.status_code == 200:
            account_info = response.json()
            portal_id = account_info.get('portalId', 'Unknown')
            account_type = account_info.get('accountType', 'Unknown')
            print(f"✅ HubSpot auth successful: Portal {portal_id} ({account_type})")
            return True
        else:
            print(f"❌ HubSpot auth failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ HubSpot connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_hubspot()
    sys.exit(0 if success else 1)
