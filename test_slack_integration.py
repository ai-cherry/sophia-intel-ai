#!/usr/bin/env python3
"""
Test script for Slack integration functionality
"""

import asyncio
import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.integrations.slack_integration import (
    SlackClient,
    test_slack_connection,
    get_slack_channels,
    send_slack_message,
    SlackIntegrationError
)

async def test_slack_integration():
    """Test all major Slack integration functions"""
    print("🔧 Testing Sophia Slack Integration")
    print("=" * 50)
    
    # Test 1: Connection test
    print("\n1️⃣ Testing Slack Connection...")
    try:
        connection_result = await test_slack_connection()
        print(f"Connection Status: {'✅ Success' if connection_result.get('success') else '❌ Failed'}")
        if connection_result.get('success'):
            print(f"  Team: {connection_result.get('team')}")
            print(f"  User: {connection_result.get('user')}")
            print(f"  Bot ID: {connection_result.get('bot_id')}")
        else:
            print(f"  Error: {connection_result.get('error')}")
            print(f"  Error Code: {connection_result.get('error_code')}")
            if connection_result.get('error_code') == 'account_inactive':
                print("  ⚠️  Account is inactive - this is the expected issue from your test")
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
    
    # Test 2: List channels (might fail due to account issue)
    print("\n2️⃣ Testing Channel Listing...")
    try:
        channels_result = await get_slack_channels()
        print(f"Channel List Status: {'✅ Success' if channels_result.get('success') else '❌ Failed'}")
        if channels_result.get('success'):
            channels = channels_result.get('channels', [])
            print(f"  Found {len(channels)} channels")
            for i, channel in enumerate(channels[:3]):  # Show first 3
                print(f"    {i+1}. #{channel.get('name')} ({'private' if channel.get('is_private') else 'public'})")
        else:
            print(f"  Error: {channels_result.get('error')}")
            print(f"  Error Code: {channels_result.get('error_code')}")
    except Exception as e:
        print(f"❌ Channel listing failed: {str(e)}")
    
    # Test 3: Client initialization
    print("\n3️⃣ Testing Client Initialization...")
    try:
        client = SlackClient()
        print("✅ SlackClient initialized successfully")
        print(f"  Base URL: {client.base_url}")
        print(f"  Bot token configured: {'✅ Yes' if client.bot_token else '❌ No'}")
        print(f"  App token configured: {'✅ Yes' if client.app_token else '❌ No'}")
    except SlackIntegrationError as e:
        print(f"❌ Client initialization failed: {str(e)}")
        print(f"  Error Code: {e.error_code}")
    except Exception as e:
        print(f"❌ Client initialization failed: {str(e)}")
    
    # Test 4: Test user listing
    print("\n4️⃣ Testing User Listing...")
    try:
        client = SlackClient()
        users_result = await client.list_users()
        print(f"User List Status: {'✅ Success' if users_result.get('success') else '❌ Failed'}")
        if users_result.get('success'):
            users = users_result.get('users', [])
            print(f"  Found {len(users)} users")
            for i, user in enumerate(users[:3]):  # Show first 3
                print(f"    {i+1}. {user.get('real_name', user.get('name'))} ({'bot' if user.get('is_bot') else 'user'})")
        else:
            print(f"  Error: {users_result.get('error')}")
            print(f"  Error Code: {users_result.get('error_code')}")
    except Exception as e:
        print(f"❌ User listing failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Slack Integration Test Complete")
    
    return True

async def test_api_endpoints():
    """Test the API endpoints by starting the server and making requests"""
    print("\n🌐 Testing Slack API Endpoints...")
    print("=" * 50)
    
    try:
        import httpx
        
        # Test the status endpoint
        print("\n📡 Testing /api/slack/status endpoint...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:9000/api/slack/status", timeout=10.0)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Status endpoint working: {result.get('success', 'Unknown')}")
                    if not result.get('success'):
                        print(f"  Expected error: {result.get('error')}")
                else:
                    print(f"❌ Status endpoint failed: HTTP {response.status_code}")
            except httpx.ConnectError:
                print("⚠️  Sophia server not running on localhost:9000")
                print("   Start it with: SOPHIA_PORT=9000 python3.12 sophia_server_standalone.py")
            except Exception as e:
                print(f"❌ Status endpoint test failed: {str(e)}")
        
    except ImportError:
        print("❌ httpx not available for API endpoint testing")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Slack Integration Tests")
    
    # Run integration tests
    asyncio.run(test_slack_integration())
    
    # Test API endpoints if server is running
    asyncio.run(test_api_endpoints())
    
    print("\n💡 Next steps:")
    print("1. Start Sophia server: SOPHIA_PORT=9000 python3.12 sophia_server_standalone.py")
    print("2. Test endpoints: curl http://localhost:9000/api/slack/status")
    print("3. Try channel listing: curl http://localhost:9000/api/slack/channels")
    print("4. The account_inactive error is expected based on your test results")