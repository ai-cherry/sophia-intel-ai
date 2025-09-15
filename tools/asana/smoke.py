#!/usr/bin/env python3
"""Asana API smoke test"""
import os, sys, requests
from dotenv import load_dotenv
if os.path.exists('.env.local'): load_dotenv('.env.local')

def test_asana():
    token = os.getenv("ASANA_PERSONAL_ACCESS_TOKEN")
    if not token:
        print("❌ ASANA_PERSONAL_ACCESS_TOKEN not configured")
        return False
    try:
        response = requests.get("https://app.asana.com/api/1.0/users/me", 
                              headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if response.status_code == 200:
            user = response.json()["data"]
            name = user.get("name", "Unknown")
            print(f"✅ Asana auth successful: {name}")
            return True
        else:
            print(f"❌ Asana auth failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Asana connection failed: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if test_asana() else 1)
