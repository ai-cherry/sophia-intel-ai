#!/usr/bin/env python3
"""
Detailed Qdrant debug script to capture exact error information.
Provides comprehensive diagnostics for 403 authentication issues.
"""
import os, sys, httpx, json

URL = os.environ.get("QDRANT_URL")
KEY = os.environ.get("QDRANT_API_KEY")

if not URL or not KEY:
    print("MISSING: QDRANT_URL or QDRANT_API_KEY", file=sys.stderr)
    sys.exit(2)

base_url = URL.rstrip('/')

def debug_auth_issue():
    print("QDRANT DEBUG REPORT")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Key format: {'pipe-delimited' if '|' in KEY else 'standard'}")
    print(f"Key length: {len(KEY)} characters")
    print(f"Key prefix: {KEY[:8]}...")
    print(f"Key contains pipe: {'Yes' if '|' in KEY else 'No'}")
    
    if "|" in KEY:
        parts = KEY.split("|")
        print(f"Pipe-delimited parts: {len(parts)} (cluster_id|api_key format)")
        print(f"Part 1 length: {len(parts[0])}")
        print(f"Part 2 length: {len(parts[1]) if len(parts) > 1 else 0}")
    
    print("\nTesting authentication methods:")
    print("-" * 40)
    
    auth_methods = [
        ("api-key", {"api-key": KEY}),
        ("x-api-key", {"x-api-key": KEY}),
        ("Authorization Bearer", {"Authorization": f"Bearer {KEY}"}),
    ]
    
    # If pipe-delimited, try just the second part
    if "|" in KEY:
        parts = KEY.split("|")
        if len(parts) >= 2:
            api_key_only = parts[1]
            auth_methods.extend([
                ("api-key (key part only)", {"api-key": api_key_only}),
                ("x-api-key (key part only)", {"x-api-key": api_key_only}),
                ("Authorization Bearer (key part only)", {"Authorization": f"Bearer {api_key_only}"}),
            ])
    
    try:
        with httpx.Client(timeout=10) as client:
            for method_name, headers in auth_methods:
                print(f"\n{method_name}:")
                try:
                    response = client.get(f"{base_url}/collections", headers=headers)
                    print(f"  Status: {response.status_code}")
                    print(f"  Headers: {dict(response.headers)}")
                    
                    if response.status_code == 403:
                        print(f"  Body: {response.text[:500]}")
                    elif response.status_code == 200:
                        print(f"  ✅ SUCCESS! Collections endpoint accessible")
                        data = response.json()
                        collections = data.get("result", {}).get("collections", [])
                        print(f"  Collections found: {len(collections)}")
                        return True
                    else:
                        print(f"  Unexpected status: {response.text[:200]}")
                        
                except Exception as e:
                    print(f"  Error: {repr(e)}")
    
    except Exception as e:
        print(f"\nClient error: {repr(e)}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS:")
    print("All authentication methods failed with 403 Forbidden.")
    print("This indicates:")
    print("1. API key may not have sufficient permissions")
    print("2. API key may be expired or invalid")
    print("3. Qdrant cluster may require different auth method")
    print("4. Network/firewall restrictions")
    print("\nRECOMMENDATIONS:")
    print("1. Verify API key permissions in Qdrant Cloud console")
    print("2. Check if key has 'collections' read/write permissions")
    print("3. Confirm cluster is accessible from current IP")
    print("4. Try regenerating API key if permissions look correct")
    
    return False

if __name__ == "__main__":
    success = debug_auth_issue()
    sys.exit(0 if success else 3)

