#!/usr/bin/env python3
"""Linear API smoke test"""
import os, sys, requests
from dotenv import load_dotenv
if os.path.exists('.env.local'): load_dotenv('.env.local')

def test_linear():
    token = os.getenv("LINEAR_API_KEY")
    if not token:
        print("❌ LINEAR_API_KEY not configured")
        return False
    try:
        query = {"query": "query { viewer { id name displayName } }"}
        response = requests.post("https://api.linear.app/graphql",
                               headers={"Authorization": token, "Content-Type": "application/json"},
                               json=query, timeout=10)
        if response.status_code == 200:
            result = response.json()
            viewer = result["data"]["viewer"]
            name = viewer.get("displayName") or viewer.get("name", "Unknown")
            print(f"✅ Linear auth successful: {name}")
            return True
        else:
            print(f"❌ Linear auth failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Linear connection failed: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if test_linear() else 1)
