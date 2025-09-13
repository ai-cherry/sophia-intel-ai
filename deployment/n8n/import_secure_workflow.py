#!/usr/bin/env python3
"""
Import secure Gong webhook workflow with signature validation
"""
import json
from datetime import datetime
import requests
# n8n Configuration
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzN2Y4NTVkMi05ODIwLTQ2ZmMtYjlhMS1kMjdlN2ZhMGQ3MDIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUwMjgyMjU5LCJleHAiOjE3NTgwMDYwMDB9.5uLdSTZdIwlSld3WpVGC0TVm97vvzXs3y44FNeRm3N8"
N8N_INSTANCE_URL = "https://scoobyjava.app.n8n.cloud"
def import_secure_workflow():
    """Import secure workflow with signature validation"""
    # Load the secure workflow
    with open("gong-webhook-secure.json") as f:
        workflow_data = json.load(f)
    # Update name with timestamp
    workflow_data["name"] = (
        f"Gong Integration - Secure - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    # API request
    headers = {"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"}
    print("🔐 Importing SECURE Gong webhook workflow...")
    print("🛡️ Features: Signature validation with RSA public key")
    print(f"📡 Target: {N8N_INSTANCE_URL}")
    try:
        response = requests.post(
            f"{N8N_INSTANCE_URL}/api/v1/workflows",
            headers=headers,
            json=workflow_data,
            timeout=30,
        )
        if response.status_code in [200, 201]:
            workflow = response.json()
            workflow_id = workflow.get("id")
            print("✅ Secure workflow imported successfully!")
            print(f"🆔 Workflow ID: {workflow_id}")
            print(f"🔗 Webhook URL: {N8N_INSTANCE_URL}/webhook/gong-webhook")
            print(f"📊 Dashboard: {N8N_INSTANCE_URL}")
            print("\\n🔐 Security Features:")
            print("  • RSA-SHA256 signature validation")
            print("  • Gong public key verification")
            print("  • Request authentication")
            print("  • Enhanced logging with security context")
            print("\\n📋 Next Steps:")
            print("1. Login to n8n and ACTIVATE the new secure workflow")
            print("2. DEACTIVATE the old workflows to avoid conflicts")
            print("3. Configure Gong webhooks with 'Show public key' method")
            print("4. Test the secure integration")
            return workflow_id
        else:
            print(f"❌ Import failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error importing secure workflow: {e}")
        return None
if __name__ == "__main__":
    print("🛡️ Secure Gong Webhook Integration")
    print("=" * 45)
    workflow_id = import_secure_workflow()
    if workflow_id:
        print("\\n🎯 Gong Configuration:")
        print("Authentication Method: Show public key (already configured)")
        print("Webhook URL: https://scoobyjava.app.n8n.cloud/webhook/gong-webhook")
        print("Security: Maximum - RSA signature validation")
    else:
        print("\\n❌ Failed to import secure workflow")
