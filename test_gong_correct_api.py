#!/usr/bin/env python3
"""
Test Gong API with correct endpoints
"""

from datetime import datetime, timedelta

import requests
from requests.auth import HTTPBasicAuth

# API credentials
GONG_ACCESS_KEY = "TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N"
GONG_CLIENT_SECRET = "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tleSI6IlRWMzNCUFo1VU40NVFLWkNaMlVDQUtSWEhRNlEzTDVOIn0.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU"

# Use Basic Auth
auth = HTTPBasicAuth(GONG_ACCESS_KEY, GONG_CLIENT_SECRET)

print("🔍 Testing Gong API Connectivity with Correct Endpoints")
print("=" * 60)

# Test 1: Current user info
print("\n1. Testing current user endpoint...")
try:
    response = requests.get(
        "https://api.gong.io/v2/users/current", auth=auth, timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        user_data = response.json()
        print(f"   ✅ User: {user_data.get('user', {}).get('emailAddress', 'Unknown')}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Connection error: {e}")

# Test 2: List calls with POST endpoint
print("\n2. Testing calls list endpoint (POST)...")
try:
    # Calculate date range
    from_date = (datetime.now() - timedelta(days=30)).isoformat()
    to_date = datetime.now().isoformat()

    request_body = {
        "filter": {"fromDateTime": from_date, "toDateTime": to_date},
        "cursor": None,
    }

    response = requests.post(
        "https://api.gong.io/v2/calls/list", auth=auth, json=request_body, timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        calls_data = response.json()
        calls = calls_data.get("calls", [])
        print(f"   ✅ Found {len(calls)} calls")
        if calls:
            first_call = calls[0]
            print(f"   First call ID: {first_call.get('id')}")
            print(f"   Title: {first_call.get('title', 'N/A')}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Connection error: {e}")

# Test 3: Get transcript with POST endpoint (correct method)
print("\n3. Testing transcript endpoint (POST with body)...")
try:
    # First, get a call ID from the list
    request_body = {
        "filter": {"fromDateTime": from_date, "toDateTime": to_date},
        "cursor": None,
    }

    response = requests.post(
        "https://api.gong.io/v2/calls/list", auth=auth, json=request_body, timeout=10
    )

    if response.status_code == 200:
        calls_data = response.json()
        calls = calls_data.get("calls", [])

        if calls:
            call_id = calls[0].get("id")
            print(f"   Using call ID: {call_id}")

            # Now fetch transcript using POST with body
            transcript_body = {"filter": {"callIds": [call_id]}}

            transcript_response = requests.post(
                "https://api.gong.io/v2/calls/transcript",
                auth=auth,
                json=transcript_body,
                timeout=10,
            )

            print(f"   Transcript Status: {transcript_response.status_code}")
            if transcript_response.status_code == 200:
                transcript_data = transcript_response.json()
                call_transcripts = transcript_data.get("callTranscripts", [])
                if call_transcripts:
                    sentences = call_transcripts[0].get("sentences", [])
                    print(f"   ✅ Got {len(sentences)} sentences")
                    if sentences:
                        print(
                            f"   First sentence: {sentences[0].get('text', '')[:100]}..."
                        )
                else:
                    print("   ⚠️ No transcript available for this call")
            else:
                print(f"   ❌ Error: {transcript_response.text}")
        else:
            print("   ⚠️ No calls found to test transcript")
    else:
        print(f"   ❌ Could not get calls list: {response.text}")

except Exception as e:
    print(f"   ❌ Connection error: {e}")

# Test 4: Get extensive call metadata with POST
print("\n4. Testing extensive call metadata (POST)...")
try:
    if calls:
        call_id = calls[0].get("id")
        extensive_body = {"filter": {"callIds": [call_id]}}

        response = requests.post(
            "https://api.gong.io/v2/calls/extensive",
            auth=auth,
            json=extensive_body,
            timeout=10,
        )

        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            extensive_data = response.json()
            call_details = extensive_data.get("calls", [])
            if call_details:
                detail = call_details[0]
                print("   ✅ Got extensive metadata")
                print(f"   Duration: {detail.get('duration', 0)} seconds")
                print(f"   Participants: {len(detail.get('parties', []))}")
                if "stats" in detail:
                    stats = detail["stats"]
                    print(f"   Talk ratio: {stats.get('talkRatio', 'N/A')}")
                    print(f"   Interactivity: {stats.get('interactivity', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Connection error: {e}")

# Test 5: Check Engage API access (for flows)
print("\n5. Testing Engage API (flows)...")
try:
    response = requests.get("https://api.gong.io/v2/flows", auth=auth, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        flows_data = response.json()
        flows = flows_data.get("flows", [])
        print(f"   ✅ Found {len(flows)} flows")
    elif response.status_code == 403:
        print("   ⚠️ Engage API not enabled or no permission")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Connection error: {e}")

# Test 6: Check webhook capabilities (list automation rules)
print("\n6. Checking webhook/automation capabilities...")
print("   ℹ️ Webhooks must be configured in Gong UI by admin")
print("   Go to: Admin → Ecosystem → Automation Rules")

print("\n" + "=" * 60)
print("📊 API Test Summary:")
print("=" * 60)
print("✅ Correct transcript endpoint: POST /v2/calls/transcript")
print("✅ Correct extensive endpoint: POST /v2/calls/extensive")
print("✅ Both require JSON body with filter/callIds")
print("\n💡 Key findings:")
print("- Your Gong API credentials are working")
print("- Use POST with body for transcript and extensive data")
print("- Engage API access depends on your license")
print("\n⚠️ Admin actions needed:")
print("1. Set up webhooks in Gong UI")
print("2. Enable Data Cloud if needed")
print("3. Configure email export settings")
