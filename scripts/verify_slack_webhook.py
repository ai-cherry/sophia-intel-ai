#!/usr/bin/env python3
"""
Slack Webhook Verification Script

Tests webhook endpoint configuration and validates
that Sophia AI can receive Slack events properly.
"""

from datetime import datetime

import requests


def test_webhook_endpoint(base_url: str | None = None):
    if not base_url:
        import os
        base_url = f"http://localhost:{os.getenv('AGENT_API_PORT','8003')}"
    """Test the webhook endpoint is accessible"""
    print("🔍 TESTING SLACK WEBHOOK CONFIGURATION")
    print("=" * 50)

    webhook_url = f"{base_url}/api/slack/webhook"

    # Test 1: URL Verification Challenge
    print("\n1️⃣ Testing URL Verification Challenge...")
    challenge_payload = {
        "type": "url_verification",
        "challenge": "test_challenge_12345",
    }

    try:
        response = requests.post(
            webhook_url,
            json=challenge_payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("challenge") == "test_challenge_12345":
                print("✅ URL verification challenge passed")
            else:
                print(f"❌ Challenge response incorrect: {result}")
        else:
            print(f"❌ URL verification failed: {response.status_code}")

    except Exception as e:
        print(f"❌ URL verification error: {str(e)}")

    # Test 2: Slash Command Format
    print("\n2️⃣ Testing Slash Command Format...")
    slash_command_data = {
        "command": "/sophia",
        "text": "help",
        "user_id": "U1234567890",
        "channel_id": "C1234567890",
        "team_id": "T1234567890",
    }

    try:
        response = requests.post(
            webhook_url,
            data=slash_command_data,  # Form-encoded for slash commands
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )

        if response.status_code == 200:
            print("✅ Slash command format accepted")
            result = response.json()
            if "text" in result:
                print(f"📝 Response preview: {result['text'][:100]}...")
        else:
            print(f"❌ Slash command test failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Slash command test error: {str(e)}")

    # Test 3: App Mention Event
    print("\n3️⃣ Testing App Mention Event...")
    mention_event = {
        "type": "event_callback",
        "event": {
            "type": "app_mention",
            "text": "<@U12345> reports",
            "user": "U1234567890",
            "channel": "C1234567890",
            "ts": str(datetime.now().timestamp()),
        },
    }

    try:
        response = requests.post(
            webhook_url,
            json=mention_event,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 200:
            print("✅ App mention event processed")
        else:
            print(f"❌ App mention test failed: {response.status_code}")

    except Exception as e:
        print(f"❌ App mention test error: {str(e)}")

    print(f"\n🎯 Webhook endpoint ready at: {webhook_url}")
    print("📋 Configure this URL in your Slack app settings")


def generate_ngrok_instructions():
    """Generate ngrok setup instructions for development"""
    print("\n" + "=" * 50)
    print("🌐 DEVELOPMENT SETUP WITH NGROK")
    print("=" * 50)

    instructions = """
# 1. Install ngrok (if not already installed):
brew install ngrok
# OR download from: https://ngrok.com/download

# 2. Start your Sophia server:
cd /Users/lynnmusil/sophia-intel-ai
python3 -m app.api.unified_server

# 3. In another terminal, start ngrok tunnel:
ngrok http 8000

# 4. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)

# 5. Update Slack app webhook URL to:
https://your-ngrok-url.ngrok.io/api/slack/webhook

# 6. Test webhook:
python3 scripts/verify_slack_webhook.py
"""

    print(instructions)


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else None

    test_webhook_endpoint(base_url)

    if "localhost" in base_url:
        generate_ngrok_instructions()
