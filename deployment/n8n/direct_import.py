#!/usr/bin/env python3
"""
Direct n8n workflow import - minimal approach
This script directly imports a clean workflow without problematic fields
"""

from datetime import datetime

import requests

# n8n Configuration
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzN2Y4NTVkMi05ODIwLTQ2ZmMtYjlhMS1kMjdlN2ZhMGQ3MDIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUwMjgyMjU5LCJleHAiOjE3NTgwMDYwMDB9.5uLdSTZdIwlSld3WpVGC0TVm97vvzXs3y44FNeRm3N8"
N8N_INSTANCE_URL = "https://scoobyjava.app.n8n.cloud"


def import_minimal_workflow():
    """Import minimal workflow directly"""

    # Minimal workflow definition
    workflow_data = {
        "name": f"Gong Integration - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "gong-webhook",
                    "responseMode": "onReceived",
                    "responseData": "allEntries",
                },
                "id": "webhook-node",
                "name": "Gong Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [240, 300],
            },
            {
                "parameters": {
                    "functionCode": "// Process Gong webhook\nconst input = $input.first().json;\nconst timestamp = new Date().toISOString();\n\nconst eventType = input.eventType || 'unknown';\nconst callId = input.callId || 'no-id';\n\nconsole.log(`[${timestamp}] Gong ${eventType} for call ${callId}`);\n\nreturn {\n  eventType,\n  callId,\n  timestamp,\n  processed: true,\n  rawData: input\n};"
                },
                "id": "process-node",
                "name": "Process Event",
                "type": "n8n-nodes-base.function",
                "typeVersion": 1,
                "position": [440, 300],
            },
        ],
        "connections": {
            "Gong Webhook": {"main": [[{"node": "Process Event", "type": "main", "index": 0}]]}
        },
        "settings": {},
    }

    # API request
    headers = {"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"}

    print("🚀 Importing minimal Gong webhook workflow...")
    print(f"📡 Target: {N8N_INSTANCE_URL}")

    try:
        response = requests.post(
            f"{N8N_INSTANCE_URL}/api/v1/workflows", headers=headers, json=workflow_data, timeout=30
        )

        if response.status_code in [200, 201]:
            workflow = response.json()
            workflow_id = workflow.get("id")

            print("✅ Workflow imported successfully!")
            print(f"🆔 Workflow ID: {workflow_id}")
            print(f"🔗 Webhook URL: {N8N_INSTANCE_URL}/webhook/gong-webhook")
            print(f"📊 Dashboard: {N8N_INSTANCE_URL}")

            print("\n📋 Next Steps:")
            print("1. Login to n8n Cloud dashboard")
            print("2. Find your workflow: 'Gong Integration - [timestamp]'")
            print("3. Click the toggle to ACTIVATE the workflow")
            print("4. Test the webhook URL")

            return workflow_id

        else:
            print(f"❌ Import failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error importing workflow: {e}")
        return None


def test_webhook(webhook_url):
    """Test the webhook once it's activated"""
    test_payload = {
        "eventType": "test",
        "callId": f"test_{int(datetime.now().timestamp())}",
        "timestamp": datetime.now().isoformat(),
        "source": "direct_import_test",
    }

    print(f"\n🧪 Testing webhook: {webhook_url}")

    try:
        response = requests.post(webhook_url, json=test_payload, timeout=10)

        if response.status_code in [200, 201, 202]:
            print("✅ Webhook test successful!")
            return True
        else:
            print(f"⚠️ Webhook returned: {response.status_code}")
            if response.status_code == 404:
                print("💡 This is expected if workflow is not activated yet")
            return False

    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
        return False


if __name__ == "__main__":
    print("🔧 n8n Direct Workflow Import")
    print("=" * 40)

    workflow_id = import_minimal_workflow()

    if workflow_id:
        webhook_url = f"{N8N_INSTANCE_URL}/webhook/gong-webhook"
        print("\n⏳ Please activate the workflow in n8n UI, then test:")
        print(
            f'curl -X POST \'{webhook_url}\' -H \'Content-Type: application/json\' -d \'{{"eventType":"test","callId":"test_123"}}\''
        )
    else:
        print("\n❌ Import failed - check API key and n8n instance URL")
