#!/usr/bin/env python3
"""
Simple NetSuite TBA test without dependencies
"""
import base64
import hashlib
import hmac
import json
import os
import random
import time
import urllib.parse
import urllib.request

from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
ACCOUNT_ID = os.getenv("NETSUITE_ACCOUNT_ID")
CONSUMER_KEY = os.getenv("NETSUITE_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("NETSUITE_CONSUMER_SECRET")
TOKEN_ID = os.getenv("NETSUITE_TOKEN_ID")
TOKEN_SECRET = os.getenv("NETSUITE_TOKEN_SECRET")


def generate_oauth_header(method, url):
    """Generate OAuth 1.0a header for NetSuite TBA"""
    timestamp = str(int(time.time()))
    nonce = str(random.getrandbits(64))

    # Parse URL to get base URL without query params
    parsed = urllib.parse.urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    # OAuth parameters
    oauth_params = {
        "oauth_consumer_key": CONSUMER_KEY,
        "oauth_token": TOKEN_ID,
        "oauth_signature_method": "HMAC-SHA256",
        "oauth_timestamp": timestamp,
        "oauth_nonce": nonce,
        "oauth_version": "1.0",
    }

    # Create parameter string
    param_string = "&".join([f"{k}={v}" for k, v in sorted(oauth_params.items())])

    # Create signature base string
    signature_base = "&".join(
        [
            method.upper(),
            urllib.parse.quote(base_url, safe=""),
            urllib.parse.quote(param_string, safe=""),
        ]
    )

    # Generate signature
    signing_key = f"{CONSUMER_SECRET}&{TOKEN_SECRET}"
    signature = base64.b64encode(
        hmac.new(
            signing_key.encode("utf-8"), signature_base.encode("utf-8"), hashlib.sha256
        ).digest()
    ).decode("utf-8")

    # Add signature to params
    oauth_params["oauth_signature"] = signature

    # Build authorization header
    auth_header = "OAuth " + ", ".join(
        [
            f'{k}="{urllib.parse.quote(str(v), safe="")}"'
            for k, v in oauth_params.items()
        ]
    )

    return auth_header


def test_netsuite_connection():
    """Test NetSuite connection with simple request"""
    print("=== NetSuite TBA Connection Test ===\n")
    print(f"Account ID: {ACCOUNT_ID}")
    print(f"Consumer Key: {CONSUMER_KEY[:20]}...")
    print(f"Token ID: {TOKEN_ID[:20]}...")

    # Test URL - metadata catalog endpoint
    url = f"https://{ACCOUNT_ID}.suitetalk.api.netsuite.com/services/rest/record/v1/metadata-catalog"

    print(f"\nTesting URL: {url}\n")

    # Generate OAuth header
    auth_header = generate_oauth_header("GET", url)
    print("Authorization header generated\n")

    # Make request
    try:
        req = urllib.request.Request(url)
        req.add_header("Authorization", auth_header)
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("✅ SUCCESS! Connection established")
            print(f"Response: Found {len(data.get('items', []))} record types")

            # Show first few record types
            for item in data.get("items", [])[:5]:
                print(f"  - {item}")

    except urllib.error.HTTPError as e:
        print(f"❌ FAILED: {e.code} {e.reason}")
        error_body = e.read().decode()
        print(f"Error details: {error_body}")

        # Common issues
        if e.code == 401:
            print("\nPossible issues:")
            print("1. Token ID/Secret might be incorrect")
            print("2. Consumer Key/Secret might be incorrect")
            print("3. Account ID format might be wrong")
            print("4. User permissions might be insufficient")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_netsuite_connection()
