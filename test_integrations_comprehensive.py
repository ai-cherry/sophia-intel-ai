#!/usr/bin/env python3
"""
Comprehensive integration testing for Phase A implementation
Tests all available integrations to establish baseline before enhancement
"""
import os
import sys
import asyncio
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.append('.')

async def test_airtable_integration():
    """Test Airtable integration"""
    print("=== TESTING AIRTABLE INTEGRATION ===")

    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')

    if not (api_key and base_id):
        print("❌ Airtable credentials not configured")
        return False

    try:
        from app.connectors.airtable import AirtableConnector
        connector = AirtableConnector()

        if not connector.configured():
            print("❌ Airtable connector not configured")
            return False

        print(f"✅ Airtable configured: API key ({len(api_key)} chars), Base ID: {base_id}")

        # Test basic connection
        auth_result = await connector.authenticate()
        print(f"✅ Authentication: {auth_result}")

        # Test data fetch
        recent_data = await connector.fetch_recent()
        print(f"✅ Recent data fetch: {len(recent_data)} records")

        return True

    except Exception as e:
        print(f"❌ Airtable test failed: {e}")
        return False

async def test_slack_integration():
    """Test Slack integration"""
    print("\n=== TESTING SLACK INTEGRATION ===")

    bot_token = os.getenv('SLACK_BOT_TOKEN')
    if not bot_token:
        print("❌ Slack bot token not configured")
        return False

    try:
        # Use the working Slack tools from the integration report
        result = subprocess.run([
            'python', 'tools/slack/smoke.py'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("✅ Slack integration working")
            print(result.stdout.split('\n')[0])  # First line of output
            return True
        else:
            print(f"❌ Slack test failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Slack test failed: {e}")
        return False

async def test_microsoft_graph():
    """Test Microsoft Graph with available credentials"""
    print("\n=== TESTING MICROSOFT GRAPH ===")

    client_id = os.getenv('MS_CLIENT_ID') or os.getenv('MICROSOFT_CLIENT_ID')
    client_secret = os.getenv('MS_CLIENT_SECRET') or os.getenv('MICROSOFT_SECRET_KEY')
    tenant_id = os.getenv('MS_TENANT_ID') or os.getenv('MICROSOFT_TENANT_ID')

    print(f"Client ID: {'✅' if client_id else '❌'}")
    print(f"Client Secret: {'✅' if client_secret else '❌'}")
    print(f"Tenant ID: {'❌ MISSING' if not tenant_id else '✅'}")

    if not (client_id and client_secret):
        print("❌ Microsoft Graph credentials incomplete")
        return False

    # Try common tenant discovery methods
    if not tenant_id:
        print("🔍 Attempting tenant ID discovery...")

        # Method 1: Try well-known endpoints
        import httpx
        try:
            # Try to get tenant from OpenID configuration
            async with httpx.AsyncClient() as client:
                # This usually works with any valid Azure domain
                response = await client.get(
                    f"https://login.microsoftonline.com/{client_id}/v2.0/.well-known/openid_configuration",
                    timeout=10
                )
                if response.status_code == 404:
                    print("⚠️ Client ID may not be registered or is incorrect")
        except Exception as e:
            print(f"⚠️ Discovery attempt failed: {e}")

    # If we still don't have tenant, we can't proceed with auth
    if not tenant_id:
        print("❌ Cannot test Microsoft Graph without tenant ID")
        print("💡 Please provide MS_TENANT_ID environment variable")
        return False

    try:
        from app.integrations.microsoft_graph_client import MicrosoftGraphClient
        client = MicrosoftGraphClient()

        # Test token acquisition
        token = client._ensure_token()
        print("✅ Microsoft Graph authentication successful")

        # Test basic API call
        users = await client.list_users(top=1)
        print(f"✅ Users API test: {len(users.get('value', []))} users")

        return True

    except Exception as e:
        print(f"❌ Microsoft Graph test failed: {e}")
        return False

async def test_gong_integration():
    """Test Gong integration"""
    print("\n=== TESTING GONG INTEGRATION ===")

    access_key = os.getenv('GONG_ACCESS_KEY')
    client_secret = os.getenv('GONG_CLIENT_SECRET')

    if not (access_key and client_secret):
        print("❌ Gong credentials not configured")
        return False

    try:
        from app.connectors.gong import GongConnector
        connector = GongConnector()

        if not connector.configured():
            print("❌ Gong connector not configured")
            return False

        auth_result = await connector.authenticate()
        print(f"✅ Gong authentication: {auth_result}")

        # Test data fetch
        recent_data = await connector.fetch_recent()
        print(f"✅ Recent calls fetch: {len(recent_data)} records")

        return True

    except Exception as e:
        print(f"❌ Gong test failed: {e}")
        return False

async def test_unified_chat_backend():
    """Test the unified chat backend service"""
    print("\n=== TESTING UNIFIED CHAT BACKEND ===")

    try:
        # Check if chat service exists and is importable
        from app.api.services.unified_chat import UnifiedChatService
        chat_service = UnifiedChatService()

        # Test basic functionality
        test_query = {
            "query": "What's the status of our business integrations?",
            "context": {"current_tab": "Dashboard"},
            "stream": False
        }

        # This should show current fallback mode
        response = await chat_service.process_query(test_query)
        print("✅ Chat service responding")
        print(f"Response type: {type(response)}")

        if "fallback" in str(response).lower() or "local mode" in str(response).lower():
            print("⚠️ Currently in fallback mode - needs data integration")
        else:
            print("✅ Chat service appears to have live data")

        return True

    except ImportError:
        print("❌ Unified chat service not found")
        return False
    except Exception as e:
        print(f"❌ Chat service test failed: {e}")
        return False

async def main():
    """Run comprehensive integration tests"""
    print("🚀 SOPHIA INTEL AI - INTEGRATION READINESS TEST")
    print("=" * 60)

    results = {}

    # Test each integration
    results['airtable'] = await test_airtable_integration()
    results['slack'] = await test_slack_integration()
    results['microsoft'] = await test_microsoft_graph()
    results['gong'] = await test_gong_integration()
    results['chat_backend'] = await test_unified_chat_backend()

    # Summary
    print("\n" + "=" * 60)
    print("🏁 INTEGRATION READINESS SUMMARY")
    print("=" * 60)

    total = len(results)
    working = sum(1 for v in results.values() if v)

    for service, status in results.items():
        emoji = "✅" if status else "❌"
        print(f"{emoji} {service.upper()}: {'READY' if status else 'NEEDS SETUP'}")

    print(f"\n📊 Overall Readiness: {working}/{total} ({(working/total)*100:.0f}%)")

    if working >= 2:  # At least 2 integrations working
        print("🚀 READY to proceed with Phase A implementation")
        print("💡 Focus on working integrations first, then expand")
    else:
        print("⚠️  Need more integrations configured before proceeding")
        print("💡 Priority: Get tenant ID for Microsoft Graph")

    return results

if __name__ == "__main__":
    import subprocess
    asyncio.run(main())