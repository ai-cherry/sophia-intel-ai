#!/usr/bin/env python3
import os
import sys
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv('.env.local')

print("=== Testing different Microsoft Graph configurations ===\n")

# Test 1: Current configuration (what we know fails)
print("TEST 1: Current configuration")
tenant_id = os.getenv("MS_TENANT_ID") or os.getenv("MICROSOFT_TENANT_ID")
client_id = os.getenv("MS_CLIENT_ID") or os.getenv("MICROSOFT_CLIENT_ID")
client_secret = os.getenv("MS_CLIENT_SECRET") or os.getenv("MICROSOFT_SECRET_KEY")

print(f"tenant_id: {tenant_id}")
print(f"client_id: {client_id}")
print(f"client_secret: {client_secret[:20]}...")

try:
    import msal
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id, authority=authority, client_credential=client_secret
    )
    scopes = ["https://graph.microsoft.com/.default"]
    token = app.acquire_token_for_client(scopes=scopes)
    if token and token.get("access_token"):
        print("✅ SUCCESS: Token acquired with current config!")
        print(f"Token type: {token.get('token_type')}")
        print(f"Expires in: {token.get('expires_in')} seconds")
    else:
        print("❌ FAILED with current config")
        print(f"Error: {token}")
except Exception as e:
    print(f"❌ EXCEPTION with current config: {e}")

print("\n" + "="*60 + "\n")

# Test 2: Try with certificate (if available)
cert_thumbprint = os.getenv("MICROSOFT_CERTIFICATE_ID")
cert_pem = os.getenv("MICROSOFT_SIGNING_CERTIFICATE")

if cert_thumbprint and cert_pem:
    print("TEST 2: Certificate-based authentication")
    print(f"Certificate ID: {cert_thumbprint}")
    print(f"Certificate (first 100 chars): {cert_pem[:100]}...")
    
    try:
        # Create certificate credential
        cert_credential = {
            "private_key": cert_pem,
            "thumbprint": cert_thumbprint.replace("-", "").upper()  # Remove dashes, uppercase
        }
        
        app_cert = msal.ConfidentialClientApplication(
            client_id, authority=authority, client_credential=cert_credential
        )
        token_cert = app_cert.acquire_token_for_client(scopes=scopes)
        
        if token_cert and token_cert.get("access_token"):
            print("✅ SUCCESS: Token acquired with certificate!")
            print(f"Token type: {token_cert.get('token_type')}")
            print(f"Expires in: {token_cert.get('expires_in')} seconds")
        else:
            print("❌ FAILED with certificate")
            print(f"Error: {token_cert}")
    except Exception as e:
        print(f"❌ EXCEPTION with certificate: {e}")
else:
    print("TEST 2: Skipped (no certificate found)")

print("\n" + "="*60 + "\n")

# Test 3: Try the secret value as-is but with different formatting
print("TEST 3: Alternative secret formatting")
alt_secrets = [
    client_secret,  # Original
    client_secret.lower(),  # Lowercase
    client_secret.upper(),  # Uppercase
    client_secret.replace("-", ""),  # Remove any dashes
]

for i, alt_secret in enumerate(alt_secrets):
    if alt_secret != client_secret or i == 0:  # Skip duplicates except first
        print(f"Trying variant {i+1}: {alt_secret[:20]}...")
        try:
            app_alt = msal.ConfidentialClientApplication(
                client_id, authority=authority, client_credential=alt_secret
            )
            token_alt = app_alt.acquire_token_for_client(scopes=scopes)
            if token_alt and token_alt.get("access_token"):
                print(f"✅ SUCCESS with variant {i+1}!")
                break
            else:
                print(f"❌ Failed with variant {i+1}: {token_alt.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Exception with variant {i+1}: {e}")

