#!/usr/bin/env python3
"""
Automated n8n Cloud Setup for Gong Integration
This script configures your n8n cloud instance programmatically
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests

# n8n Configuration
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzN2Y4NTVkMi05ODIwLTQ2ZmMtYjlhMS1kMjdlN2ZhMGQ3MDIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUwMjgyMjU5LCJleHAiOjE3NTgwMDYwMDB9.5uLdSTZdIwlSld3WpVGC0TVm97vvzXs3y44FNeRm3N8"
N8N_INSTANCE_URL = "https://scoobyjava.app.n8n.cloud"

# Gong Credentials
GONG_ACCESS_KEY = "TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N"
GONG_CLIENT_SECRET = "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tleSI6IlRWMzNCUFo1VU40NVFLWkNaMlVDQUtSWEhRNlEzTDVOIn0.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU"


class N8NCloudSetup:
    """Automate n8n Cloud configuration for Gong integration"""

    def __init__(self):
        self.api_key = N8N_API_KEY
        self.base_url = f"{N8N_INSTANCE_URL}/api/v1"
        self.headers = {"X-N8N-API-KEY": self.api_key, "Content-Type": "application/json"}
        self.workflow_id = None

    def test_connection(self) -> bool:
        """Test connection to n8n cloud instance"""
        try:
            response = requests.get(f"{self.base_url}/workflows", headers=self.headers, timeout=10)
            if response.status_code == 200:
                print("✅ Connected to n8n Cloud successfully")
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    def create_credentials(self) -> Dict[str, str]:
        """Create required credentials in n8n"""
        credentials_created = {}

        # Note: n8n API doesn't support credential creation directly
        # This would need to be done through the UI
        # However, we can prepare the credential configurations

        credentials_config = {
            "gong_api": {
                "type": "basicAuth",
                "name": "Gong API",
                "data": {"username": GONG_ACCESS_KEY, "password": GONG_CLIENT_SECRET},
            },
            "postgres": {
                "type": "postgres",
                "name": "Neon PostgreSQL",
                "data": {
                    "host": os.getenv("NEON_HOST", "your-neon-host.neon.tech"),
                    "database": "sophia",
                    "user": os.getenv("NEON_USER", "your-user"),
                    "password": os.getenv("NEON_PASSWORD", "your-password"),
                    "port": 5432,
                    "ssl": True,
                },
            },
            "redis": {
                "type": "redis",
                "name": "Redis Cache",
                "data": {
                    "host": os.getenv("REDIS_HOST", "localhost"),
                    "port": 6379,
                    "password": os.getenv("REDIS_PASSWORD", ""),
                },
            },
        }

        print("\n📝 Credential configurations prepared:")
        print("Please create these credentials in the n8n UI:")
        for cred_name, config in credentials_config.items():
            print(f"\n{cred_name}:")
            print(json.dumps(config, indent=2))

        return credentials_config

    def import_workflow(self) -> Optional[str]:
        """Import the Gong webhook workflow"""
        # Load the workflow JSON
        workflow_path = "/Users/lynnmusil/sophia-intel-ai/deployment/n8n/gong-webhook-workflow.json"

        try:
            with open(workflow_path) as f:
                workflow_data = json.load(f)

            # Update workflow for import
            workflow_data["active"] = False  # Start inactive
            workflow_data["name"] = f"Gong Integration - {datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Create workflow via API
            response = requests.post(
                f"{self.base_url}/workflows", headers=self.headers, json=workflow_data, timeout=30
            )

            if response.status_code in [200, 201]:
                workflow = response.json()
                self.workflow_id = workflow.get("id")
                print(f"✅ Workflow created with ID: {self.workflow_id}")
                return self.workflow_id
            else:
                print(f"❌ Failed to create workflow: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except FileNotFoundError:
            print(f"❌ Workflow file not found: {workflow_path}")
            return None
        except Exception as e:
            print(f"❌ Error importing workflow: {e}")
            return None

    def activate_workflow(self, workflow_id: str) -> bool:
        """Activate the imported workflow"""
        try:
            response = requests.patch(
                f"{self.base_url}/workflows/{workflow_id}",
                headers=self.headers,
                json={"active": True},
                timeout=10,
            )

            if response.status_code == 200:
                print(f"✅ Workflow {workflow_id} activated")
                return True
            else:
                print(f"❌ Failed to activate workflow: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error activating workflow: {e}")
            return False

    def get_webhook_url(self, workflow_id: str) -> Optional[str]:
        """Get the webhook URL for the workflow"""
        try:
            response = requests.get(
                f"{self.base_url}/workflows/{workflow_id}", headers=self.headers, timeout=10
            )

            if response.status_code == 200:
                # The webhook URL follows a standard pattern
                webhook_url = f"{N8N_INSTANCE_URL}/webhook/gong-webhook"
                print(f"✅ Webhook URL: {webhook_url}")
                return webhook_url
            else:
                print(f"❌ Failed to get workflow details: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error getting webhook URL: {e}")
            return None

    def test_webhook(self, webhook_url: str) -> bool:
        """Test the webhook endpoint"""
        test_payload = {
            "eventType": "test",
            "callId": "test_" + str(int(time.time())),
            "timestamp": datetime.now().isoformat(),
            "source": "n8n_setup_script",
        }

        try:
            response = requests.post(webhook_url, json=test_payload, timeout=10)

            if response.status_code in [200, 201, 202]:
                print("✅ Webhook test successful")
                return True
            else:
                print(f"⚠️ Webhook returned status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Webhook test failed: {e}")
            return False

    def list_executions(self, workflow_id: str, limit: int = 10) -> list:
        """List recent workflow executions"""
        try:
            response = requests.get(
                f"{self.base_url}/executions",
                headers=self.headers,
                params={"workflowId": workflow_id, "limit": limit},
                timeout=10,
            )

            if response.status_code == 200:
                executions = response.json().get("data", [])
                print(f"\n📊 Recent executions ({len(executions)} found):")
                for exec in executions[:5]:
                    status = exec.get("status", "unknown")
                    started = exec.get("startedAt", "")
                    print(f"  - {status}: {started}")
                return executions
            else:
                print(f"❌ Failed to get executions: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error getting executions: {e}")
            return []

    def generate_gong_config(self, webhook_url: str):
        """Generate Gong configuration instructions"""
        config = f"""
═══════════════════════════════════════════════════════════════
🎯 GONG CONFIGURATION INSTRUCTIONS
═══════════════════════════════════════════════════════════════

Your n8n webhook is ready! Now configure Gong:

1. LOGIN TO GONG:
   URL: https://app.gong.io
   Navigate to: Admin → Automation Rules

2. CREATE WEBHOOK RULES:

   A) Call Ended Webhook:
   ─────────────────────
   Name: n8n - Call Ended
   Event: Call Ended
   URL: {webhook_url}
   Method: POST

   B) Transcript Ready Webhook:
   ────────────────────────────
   Name: n8n - Transcript Ready
   Event: Transcript Ready
   URL: {webhook_url}
   Method: POST

   C) Deal at Risk Webhook:
   ────────────────────────
   Name: n8n - Deal at Risk
   Event: Deal Health Changed to At Risk
   URL: {webhook_url}
   Method: POST

3. COPY WEBHOOK SECRET:
   After creating the first webhook, Gong will provide a secret.
   Copy it and add to n8n Variables:

   n8n → Settings → Variables → Add Variable
   Name: GONG_WEBHOOK_SECRET
   Value: [Paste the secret from Gong]

4. TEST THE INTEGRATION:
   In Gong → Automation Rules → Click "Test" on any rule
   Check n8n → Workflows → Executions

═══════════════════════════════════════════════════════════════
"""
        print(config)

        # Save to file
        with open("gong_webhook_config.txt", "w") as f:
            f.write(config)
        print("📄 Configuration saved to: gong_webhook_config.txt")

    def run_full_setup(self):
        """Run the complete setup process"""
        print("\n" + "=" * 60)
        print("🚀 N8N CLOUD SETUP FOR GONG INTEGRATION")
        print("=" * 60)

        # Step 1: Test connection
        print("\n[1/7] Testing n8n Cloud connection...")
        if not self.test_connection():
            print("❌ Setup failed: Cannot connect to n8n Cloud")
            return False

        # Step 2: Prepare credentials
        print("\n[2/7] Preparing credential configurations...")
        self.create_credentials()

        # Step 3: Import workflow
        print("\n[3/7] Importing Gong webhook workflow...")
        workflow_id = self.import_workflow()
        if not workflow_id:
            print("❌ Setup failed: Cannot import workflow")
            return False

        # Step 4: Get webhook URL
        print("\n[4/7] Getting webhook URL...")
        webhook_url = self.get_webhook_url(workflow_id)
        if not webhook_url:
            print("❌ Setup failed: Cannot get webhook URL")
            return False

        # Step 5: Activate workflow
        print("\n[5/7] Activating workflow...")
        if not self.activate_workflow(workflow_id):
            print("⚠️ Warning: Workflow not activated. Activate manually in n8n UI")

        # Step 6: Test webhook
        print("\n[6/7] Testing webhook endpoint...")
        self.test_webhook(webhook_url)

        # Step 7: Generate Gong configuration
        print("\n[7/7] Generating Gong configuration...")
        self.generate_gong_config(webhook_url)

        print("\n" + "=" * 60)
        print("✅ N8N SETUP COMPLETE!")
        print("=" * 60)
        print("\n📌 Important URLs:")
        print(f"   n8n Dashboard: {N8N_INSTANCE_URL}")
        print(f"   Webhook URL: {webhook_url}")
        print(f"   Workflow ID: {workflow_id}")
        print("\n📋 Next Steps:")
        print("   1. Create credentials in n8n UI (see instructions above)")
        print("   2. Configure webhooks in Gong Admin")
        print("   3. Test the integration")

        return True


def main():
    """Main execution"""
    setup = N8NCloudSetup()

    # Check for environment variables
    if not os.getenv("NEON_HOST"):
        print("\n⚠️ Warning: Database credentials not found in environment")
        print("Set these environment variables:")
        print("  export NEON_HOST=your-neon-host.neon.tech")
        print("  export NEON_USER=your-username")
        print("  export NEON_PASSWORD=your-password")
        print("  export REDIS_HOST=your-redis-host")
        print("  export REDIS_PASSWORD=your-redis-password")
        print("\nContinuing with setup...\n")

    # Run setup
    success = setup.run_full_setup()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
