#!/usr/bin/env python3
"""Test Slack token connectivity and permissions"""

import os
import sys
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def test_slack_tokens():
    """Test the Slack tokens to ensure they're valid and working"""
    
    bot_token = os.environ.get('SLACK_BOT_TOKEN')
    app_token = os.environ.get('SLACK_APP_TOKEN')
    signing_secret = os.environ.get('SLACK_SIGNING_SECRET')
    
    print("=" * 60)
    print("SLACK TOKEN VALIDATION TEST")
    print("=" * 60)
    
    # Check if tokens are present
    print("\n1. Token Presence Check:")
    print(f"   Bot Token: {'✓ Present' if bot_token else '✗ Missing'}")
    print(f"   App Token: {'✓ Present' if app_token else '✗ Missing'}")
    print(f"   Signing Secret: {'✓ Present' if signing_secret else '✗ Missing'}")
    
    if not bot_token:
        print("\n✗ Bot token is missing. Cannot proceed with API tests.")
        return False
    
    # Test Bot Token by calling auth.test
    print("\n2. Bot Token Authentication Test:")
    try:
        client = WebClient(token=bot_token)
        response = client.auth_test()
        
        if response["ok"]:
            print(f"   ✓ Bot authenticated successfully")
            print(f"   Team: {response.get('team', 'N/A')}")
            print(f"   Team ID: {response.get('team_id', 'N/A')}")
            print(f"   User: {response.get('user', 'N/A')}")
            print(f"   User ID: {response.get('user_id', 'N/A')}")
            print(f"   Bot ID: {response.get('bot_id', 'N/A')}")
        else:
            print(f"   ✗ Authentication failed: {response.get('error', 'Unknown error')}")
            return False
            
    except SlackApiError as e:
        print(f"   ✗ Slack API Error: {e.response['error']}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {str(e)}")
        return False
    
    # Test permissions by listing channels
    print("\n3. Permissions Test (List Channels):")
    try:
        response = client.conversations_list(limit=5)
        
        if response["ok"]:
            channels = response.get('channels', [])
            print(f"   ✓ Successfully retrieved {len(channels)} channels")
            if channels:
                print("   Sample channels:")
                for channel in channels[:3]:
                    print(f"     - #{channel.get('name', 'N/A')}")
        else:
            print(f"   ✗ Failed to list channels: {response.get('error', 'Unknown error')}")
            
    except SlackApiError as e:
        print(f"   ✗ Slack API Error: {e.response['error']}")
        if 'missing_scope' in str(e):
            print("     Note: Bot may need 'channels:read' scope")
    except Exception as e:
        print(f"   ✗ Unexpected error: {str(e)}")
    
    # Test user info retrieval
    print("\n4. User Info Test:")
    try:
        response = client.users_list(limit=5)
        
        if response["ok"]:
            users = response.get('members', [])
            print(f"   ✓ Successfully retrieved {len(users)} users")
        else:
            print(f"   ✗ Failed to list users: {response.get('error', 'Unknown error')}")
            
    except SlackApiError as e:
        print(f"   ✗ Slack API Error: {e.response['error']}")
        if 'missing_scope' in str(e):
            print("     Note: Bot may need 'users:read' scope")
    except Exception as e:
        print(f"   ✗ Unexpected error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_slack_tokens()
    sys.exit(0 if success else 1)