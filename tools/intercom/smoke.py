#!/usr/bin/env python3
"""Intercom API smoke test"""
import os, sys, requests
from dotenv import load_dotenv
if os.path.exists('.env.local'): load_dotenv('.env.local')

def test_intercom():
    token = os.getenv("INTERCOM_ACCESS_TOKEN")
    if not token:
        print("❌ INTERCOM_ACCESS_TOKEN not configured")
        return False
    try:
        response = requests.get("https://api.intercom.io/me", 
                              headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if response.status_code == 200:
            app = response.json()
            name = app.get("name", "Unknown")
            print(f"✅ Intercom auth successful: {name}")
            return True
        else:
            print(f"❌ Intercom auth failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Intercom connection failed: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if test_intercom() else 1)
