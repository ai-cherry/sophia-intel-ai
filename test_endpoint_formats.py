#!/usr/bin/env python3
"""Test different NetSuite endpoint formats"""
import os
import urllib.error
import urllib.request
from dotenv import load_dotenv
load_dotenv()
ACCOUNT_ID = os.getenv("NETSUITE_ACCOUNT_ID")
# Different URL formats to try
urls = [
    f"https://{ACCOUNT_ID}.suitetalk.api.netsuite.com/services/rest/record/v1/metadata-catalog",
    f"https://{ACCOUNT_ID}.restlets.api.netsuite.com/app/site/hosting/restlet.nl",
    f"https://system.netsuite.com/app/login/oauth2/authorize.nl?account={ACCOUNT_ID}",
    f"https://{ACCOUNT_ID}.app.netsuite.com/app/login/oauth2/authorize.nl",
]
print("Testing NetSuite URL accessibility (without auth):\n")
for url in urls:
    print(f"Testing: {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"   ✅ Accessible: {response.status}")
    except urllib.error.HTTPError as e:
        print(f"   📞 HTTP {e.code}: {e.reason} (endpoint exists)")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    print()
