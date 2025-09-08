#!/usr/bin/env python3
"""
Production n8n Workflow Activation Script
Automatically activates and validates n8n workflows for Gong integration
"""

import json
import time
from datetime import datetime

import httpx

# n8n Cloud Configuration
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzN2Y4NTVkMi05ODIwLTQ2ZmMtYjlhMS1kMjdlN2ZhMGQ3MDIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUwMjgyMjU5LCJleHAiOjE3NTgwMDYwMDB9.5uLdSTZdIwlSld3WpVGC0TVm97vvzXs3y44FNeRm3N8"
N8N_INSTANCE_URL = "https://scoobyjava.app.n8n.cloud"
WEBHOOK_URL = "https://scoobyjava.app.n8n.cloud/webhook/gong-webhook"


class N8NProductionActivator:
    """Handles production activation of n8n workflows"""

    def __init__(self):
        self.headers = {
            "X-N8N-API-KEY": N8N_API_KEY,
            "Content-Type": "application/json",
        }
        self.activation_results = {
            "timestamp": datetime.now().isoformat(),
            "activated_workflows": [],
            "errors": [],
            "webhook_url": WEBHOOK_URL,
            "status": "pending",
        }

    async def get_workflows(self):
        """Get all workflows from n8n instance"""
        print("🔍 Fetching existing workflows...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{N8N_INSTANCE_URL}/api/v1/workflows", headers=self.headers
                )

                if response.status_code == 200:
                    workflows = response.json()
                    print(f"✅ Found {len(workflows.get('data', []))} workflows")
                    return workflows.get("data", [])
                else:
                    print(f"❌ Failed to fetch workflows: {response.status_code}")
                    print(f"Response: {response.text}")
                    return []

            except Exception as e:
                print(f"❌ Error fetching workflows: {e}")
                self.activation_results["errors"].append(f"Fetch workflows error: {e}")
                return []

    async def activate_workflow(self, workflow_id: str, workflow_name: str):
        """Activate a specific workflow"""
        print(f"⚡ Activating workflow: {workflow_name} ({workflow_id})")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{N8N_INSTANCE_URL}/api/v1/workflows/{workflow_id}/activate",
                    headers=self.headers,
                )

                if response.status_code in [200, 201]:
                    print(f"✅ Successfully activated: {workflow_name}")
                    self.activation_results["activated_workflows"].append(
                        {
                            "id": workflow_id,
                            "name": workflow_name,
                            "status": "activated",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    return True
                else:
                    error_msg = (
                        f"Failed to activate {workflow_name}: {response.status_code}"
                    )
                    print(f"❌ {error_msg}")
                    self.activation_results["errors"].append(error_msg)
                    return False

            except Exception as e:
                error_msg = f"Error activating {workflow_name}: {e}"
                print(f"❌ {error_msg}")
                self.activation_results["errors"].append(error_msg)
                return False

    async def validate_webhook_endpoint(self):
        """Validate the webhook endpoint is responding correctly"""
        print(f"🧪 Validating webhook endpoint: {WEBHOOK_URL}")

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                test_payload = {
                    "eventType": "production_validation",
                    "callId": "prod_validation_001",
                    "timestamp": datetime.now().isoformat(),
                    "source": "n8n_production_activation",
                }

                response = await client.post(WEBHOOK_URL, json=test_payload)

                if response.status_code in [200, 201, 202]:
                    print(
                        f"✅ Webhook endpoint is live and responding (Status: {response.status_code})"
                    )
                    return True
                else:
                    print(f"⚠️ Webhook responded with status {response.status_code}")
                    return False

            except Exception as e:
                print(f"❌ Webhook validation error: {e}")
                self.activation_results["errors"].append(
                    f"Webhook validation error: {e}"
                )
                return False

    async def activate_gong_workflows(self):
        """Find and activate Gong-related workflows"""
        print("🎯 ACTIVATING N8N GONG INTEGRATION WORKFLOWS")
        print("=" * 55)

        workflows = await self.get_workflows()
        if not workflows:
            print("❌ No workflows found to activate")
            self.activation_results["status"] = "failed"
            return False

        # Look for Gong-related workflows
        gong_workflows = []
        for workflow in workflows:
            name = workflow.get("name", "").lower()
            if any(keyword in name for keyword in ["gong", "webhook", "integration"]):
                gong_workflows.append(workflow)

        if not gong_workflows:
            print("⚠️ No Gong-related workflows found")
            # Show all workflows for manual selection
            print("\nAvailable workflows:")
            for wf in workflows[:5]:  # Show first 5
                print(f"  - {wf.get('name', 'Unnamed')} (ID: {wf.get('id', 'No ID')})")

        activated_count = 0
        for workflow in gong_workflows:
            workflow_id = workflow.get("id")
            workflow_name = workflow.get("name", "Unnamed Workflow")

            if workflow_id:
                success = await self.activate_workflow(workflow_id, workflow_name)
                if success:
                    activated_count += 1

                # Small delay between activations
                time.sleep(1)

        # Validate webhook endpoint
        webhook_valid = await self.validate_webhook_endpoint()

        # Set overall status
        if activated_count > 0 and webhook_valid:
            self.activation_results["status"] = "success"
            print(
                f"\n✅ Production activation complete: {activated_count} workflows activated"
            )
        elif activated_count > 0:
            self.activation_results["status"] = "partial"
            print(
                f"\n⚠️ Partial activation: {activated_count} workflows activated but webhook validation failed"
            )
        else:
            self.activation_results["status"] = "failed"
            print("\n❌ Activation failed: No workflows activated")

        return activated_count > 0

    def save_activation_report(self):
        """Save activation results to file"""
        report_file = (
            f"n8n_production_activation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(report_file, "w") as f:
            json.dump(self.activation_results, f, indent=2)

        print(f"📄 Activation report saved: {report_file}")
        return report_file


async def main():
    """Main execution function"""
    activator = N8NProductionActivator()

    print("🚀 N8N PRODUCTION WORKFLOW ACTIVATION")
    print("=" * 45)
    print(f"Instance: {N8N_INSTANCE_URL}")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 45)

    success = await activator.activate_gong_workflows()
    report_file = activator.save_activation_report()

    if success:
        print("\n🎉 N8N PRODUCTION ACTIVATION SUCCESSFUL!")
        print("Next steps:")
        print("  1. Configure Gong webhooks to use the validated endpoint")
        print("  2. Monitor webhook activity in n8n dashboard")
        print("  3. Set up production monitoring alerts")
    else:
        print("\n❌ N8N PRODUCTION ACTIVATION FAILED")
        print("Manual intervention required:")
        print("  1. Check n8n dashboard manually")
        print("  2. Verify workflow configurations")
        print("  3. Review activation errors in report")

    return success


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
