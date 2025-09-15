#!/usr/bin/env python3
"""
Salesforce API smoke test - quick connectivity check
"""

import os
import sys
import requests
from dotenv import load_dotenv

if os.path.exists('.env.local'):
    load_dotenv('.env.local')

def test_salesforce():
    """Quick Salesforce connectivity test"""
    client_id = os.getenv("SALESFORCE_CLIENT_ID")
    client_secret = os.getenv("SALESFORCE_CLIENT_SECRET") 
    username = os.getenv("SALESFORCE_USERNAME")
    password = os.getenv("SALESFORCE_PASSWORD")
    security_token = os.getenv("SALESFORCE_SECURITY_TOKEN", "")
    instance_url = os.getenv("SALESFORCE_INSTANCE_URL", "https://login.salesforce.com")
    
    if not all([client_id, client_secret, username, password]):
        print("❌ Salesforce credentials not fully configured")
        return False
    
    try:
        oauth_data = {
            'grant_type': 'password',
            'client_id': client_id,
            'client_secret': client_secret,
            'username': username,
            'password': password + security_token
        }
        
        response = requests.post(f"{instance_url}/services/oauth2/token", data=oauth_data, timeout=15)
        
        if response.status_code == 200:
            token_data = response.json()
            sf_instance = token_data["instance_url"]
            print(f"✅ Salesforce auth successful: {sf_instance}")
            return True
        else:
            print(f"❌ Salesforce auth failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Salesforce connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_salesforce()
    sys.exit(0 if success else 1)
