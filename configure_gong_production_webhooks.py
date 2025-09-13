#!/usr/bin/env python3
"""
Gong Production Webhook Configuration Script
Provides instructions and automated configuration for Gong webhooks
"""
import json
from datetime import datetime
import httpx
# Production Configuration
PRODUCTION_WEBHOOK_URL = "https://scoobyjava.app.n8n.cloud/webhook/gong-webhook"
GONG_API_BASE = "https://api.gong.io"
GONG_ACCESS_KEY = "TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N"
GONG_ACCESS_KEY_SECRET = "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tleSI6IlRWMzNCUFo1VU40NVFLWkNaMlVDQUtSWEhRNlEzTDVOIn0.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU"
class GongWebhookConfigurator:
    """Handles Gong webhook configuration for production"""
    def __init__(self):
        self.webhook_config = {
            "webhook_url": PRODUCTION_WEBHOOK_URL,
            "timestamp": datetime.now().isoformat(),
            "configured_events": [],
            "errors": [],
            "status": "pending",
        }
        # Set up authentication
        import base64
        auth_string = f"{GONG_ACCESS_KEY}:{GONG_ACCESS_KEY_SECRET}"
        auth_bytes = auth_string.encode("ascii")
        auth_base64 = base64.b64encode(auth_bytes).decode("ascii")
        self.headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/json",
        }
    def generate_manual_configuration_guide(self):
        """Generate detailed manual configuration guide"""
        guide = f"""
# 🎯 GONG PRODUCTION WEBHOOK CONFIGURATION GUIDE
## Overview
Configure Gong webhooks to send events to your validated n8n endpoint for production traffic processing.
**Production Webhook URL:** `{PRODUCTION_WEBHOOK_URL}`
**Configuration Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
## 📋 Manual Configuration Steps
### Step 1: Login to Gong Admin Panel
1. Navigate to: https://app.gong.io
2. Login with your admin credentials
3. Go to: **Admin → Automation → Webhook Rules**
### Step 2: Create Webhook Rules
#### A) Call Ended Webhook
```
Name: Production - Call Ended
Trigger: Call Ended
Action: Send Webhook
URL: {PRODUCTION_WEBHOOK_URL}
Method: POST
Headers:
  Content-Type: application/json
```
#### B) Transcript Ready Webhook
```
Name: Production - Transcript Ready
Trigger: Transcript Ready
Action: Send Webhook
URL: {PRODUCTION_WEBHOOK_URL}
Method: POST
Headers:
  Content-Type: application/json
```
#### C) Deal at Risk Webhook
```
Name: Production - Deal at Risk
Trigger: Deal Health Changed to At Risk
Action: Send Webhook
URL: {PRODUCTION_WEBHOOK_URL}
Method: POST
Headers:
  Content-Type: application/json
```
#### D) Meeting Insights Webhook
```
Name: Production - Meeting Insights
Trigger: Meeting Insights Generated
Action: Send Webhook
URL: {PRODUCTION_WEBHOOK_URL}
Method: POST
Headers:
  Content-Type: application/json
```
### Step 3: Configure Webhook Security
#### Enable Signature Validation
1. In each webhook rule, enable **"Sign webhook requests"**
2. Copy the provided webhook secret
3. Store the secret securely for signature validation
#### Save Webhook Secret
```bash
# Add to your environment variables
export GONG_WEBHOOK_SECRET="<webhook_secret_from_gong>"
```
### Step 4: Test Webhook Configuration
#### Test Each Webhook Rule
1. In Gong Admin, click **"Test"** on each webhook rule
2. Verify webhook appears in n8n execution log
3. Check n8n dashboard for successful executions
#### Validation Commands
```bash
# Check n8n workflow executions
curl -H "X-N8N-API-KEY: YOUR_API_KEY" \\
     "https://scoobyjava.app.n8n.cloud/api/v1/executions"
# Test webhook directly
curl -X POST '{PRODUCTION_WEBHOOK_URL}' \\
     -H 'Content-Type: application/json' \\
     -d '{{"eventType":"test","source":"manual_test"}}'
```
### Step 5: Monitor Production Traffic
#### Expected Event Types
- `call.ended` - Sales call completion
- `transcript.ready` - Call transcript processed
- `deal.at_risk` - Deal health degradation
- `insight.generated` - Meeting insights available
#### Monitoring URLs
- **n8n Dashboard:** https://scoobyjava.app.n8n.cloud
- **Sophia Health:** http://localhost:8000/health
- **Integration Status:** Check workflow executions
## 🔐 Security Configuration
### Webhook Signature Validation
Gong signs webhook requests with HMAC-SHA256. Validate signatures to ensure authenticity:
```python
import hmac
import hashlib
def validate_gong_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```
### IP Whitelist (Optional)
If needed, whitelist Gong's webhook IP ranges:
- Check Gong documentation for current IP ranges
- Configure firewall rules accordingly
## 📊 Production Readiness Checklist
- [ ] All 4 webhook rules created in Gong Admin
- [ ] Webhook URLs pointing to production endpoint
- [ ] Signature validation enabled
- [ ] Webhook secret stored securely
- [ ] Test webhooks successfully fired
- [ ] n8n workflows executing correctly
- [ ] Sophia system processing events
- [ ] Monitoring alerts configured
## ⚠️ Important Notes
1. **Webhook Secret Management**
   - Store webhook secrets securely
   - Rotate secrets periodically
   - Never commit secrets to version control
2. **Error Handling**
   - Monitor webhook failure rates
   - Set up alerts for failed deliveries
   - Implement retry mechanisms
3. **Rate Limiting**
   - Gong may rate limit webhook deliveries
   - Ensure n8n can handle burst traffic
   - Monitor performance metrics
## 🆘 Troubleshooting
### Common Issues
#### Webhook Not Firing
- Check webhook rule is active in Gong Admin
- Verify trigger conditions are met
- Check Gong webhook delivery logs
#### 404/500 Errors
- Verify webhook URL is correct
- Check n8n workflow is activated
- Validate n8n instance is responding
#### Signature Validation Failures
- Ensure webhook secret is correct
- Check signature validation logic
- Verify payload formatting
### Support Contacts
- **Gong Support:** support@gong.io
- **n8n Support:** Via n8n Cloud dashboard
- **Integration Team:** Internal escalation
---
**Generated by:** Gong Webhook Configurator
**Status:** Ready for Production Configuration
**Next Step:** Execute manual configuration in Gong Admin Panel
"""
        # Save guide to file
        guide_file = f"gong_webhook_configuration_guide_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(guide_file, "w") as f:
            f.write(guide)
        print("📄 Manual configuration guide generated:")
        print(f"   File: {guide_file}")
        return guide_file
    async def check_existing_webhooks(self):
        """Check existing webhook configurations in Gong"""
        print("🔍 Checking existing Gong webhook configurations...")
        # Note: Gong API doesn't provide webhook management endpoints
        # This would need to be done through their web interface
        print("⚠️ Webhook management must be done through Gong Admin interface")
        print("   URL: https://app.gong.io → Admin → Automation → Webhook Rules")
        return []
    async def validate_gong_api_access(self):
        """Validate Gong API access and permissions"""
        print("🔑 Validating Gong API access...")
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                # Test basic API access with user info endpoint
                response = await client.get(
                    f"{GONG_API_BASE}/v2/users", headers=self.headers
                )
                if response.status_code == 200:
                    print("✅ Gong API access validated")
                    users = response.json()
                    user_count = len(users.get("users", []))
                    print(f"   Found {user_count} users in Gong instance")
                    return True
                elif response.status_code == 401:
                    print("❌ Gong API authentication failed")
                    print("   Check access key and secret")
                    return False
                else:
                    print(f"⚠️ Gong API returned status {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    return False
            except Exception as e:
                print(f"❌ Gong API validation error: {e}")
                self.webhook_config["errors"].append(f"API validation error: {e}")
                return False
    async def test_production_webhook_endpoint(self):
        """Test the production webhook endpoint"""
        print("🧪 Testing production webhook endpoint...")
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                test_payload = {
                    "eventType": "production_configuration_test",
                    "callId": "prod_config_test_001",
                    "timestamp": datetime.now().isoformat(),
                    "source": "gong_production_configuration",
                    "testData": {
                        "configured_by": "automated_script",
                        "webhook_url": PRODUCTION_WEBHOOK_URL,
                        "configuration_time": datetime.now().isoformat(),
                    },
                }
                response = await client.post(PRODUCTION_WEBHOOK_URL, json=test_payload)
                if response.status_code in [200, 201, 202]:
                    print(
                        f"✅ Production webhook endpoint is ready (Status: {response.status_code})"
                    )
                    print(f"   Response: {response.text[:100]}")
                    return True
                else:
                    print(f"❌ Webhook endpoint returned status {response.status_code}")
                    self.webhook_config["errors"].append(
                        f"Webhook test failed: {response.status_code}"
                    )
                    return False
            except Exception as e:
                print(f"❌ Webhook endpoint test error: {e}")
                self.webhook_config["errors"].append(f"Webhook test error: {e}")
                return False
    def create_webhook_test_payloads(self):
        """Create test payloads for each webhook type"""
        test_payloads = {
            "call_ended": {
                "eventType": "call.ended",
                "callId": "test_call_001",
                "callUrl": "https://gong.io/call/test_001",
                "participants": ["Test User 1", "Test User 2"],
                "duration": 1800,
                "endedAt": datetime.now().isoformat(),
                "source": "gong_production_test",
            },
            "transcript_ready": {
                "eventType": "transcript.ready",
                "callId": "test_call_002",
                "transcriptUrl": "https://gong.io/transcript/test_002",
                "language": "en",
                "readyAt": datetime.now().isoformat(),
                "source": "gong_production_test",
            },
            "deal_at_risk": {
                "eventType": "deal.at_risk",
                "dealId": "test_deal_001",
                "callId": "test_call_003",
                "riskLevel": "high",
                "riskFactors": ["lack_of_engagement", "pricing_concerns"],
                "detectedAt": datetime.now().isoformat(),
                "source": "gong_production_test",
            },
            "insight_generated": {
                "eventType": "insight.generated",
                "callId": "test_call_004",
                "insightType": "competitor_mentioned",
                "confidence": 0.95,
                "generatedAt": datetime.now().isoformat(),
                "source": "gong_production_test",
            },
        }
        # Save test payloads to file
        payloads_file = f"gong_webhook_test_payloads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(payloads_file, "w") as f:
            json.dump(test_payloads, f, indent=2)
        print(f"📄 Test payloads saved to: {payloads_file}")
        return test_payloads
    async def configure_production_webhooks(self):
        """Main configuration process"""
        print("🎯 CONFIGURING GONG PRODUCTION WEBHOOKS")
        print("=" * 50)
        # Step 1: Validate Gong API access
        api_valid = await self.validate_gong_api_access()
        if not api_valid:
            print("❌ Cannot proceed without valid Gong API access")
            self.webhook_config["status"] = "failed"
            return False
        # Step 2: Test webhook endpoint
        webhook_valid = await self.test_production_webhook_endpoint()
        if not webhook_valid:
            print("⚠️ Webhook endpoint test failed, but continuing...")
        # Step 3: Check existing webhooks (manual only)
        await self.check_existing_webhooks()
        # Step 4: Generate manual configuration guide
        guide_file = self.generate_manual_configuration_guide()
        # Step 5: Create test payloads
        test_payloads = self.create_webhook_test_payloads()
        # Step 6: Set status
        self.webhook_config["status"] = "ready_for_manual_config"
        self.webhook_config["guide_file"] = guide_file
        self.webhook_config["test_payloads_available"] = True
        print("\n✅ Gong webhook configuration preparation complete!")
        print("\n📋 MANUAL STEPS REQUIRED:")
        print("   1. Review the generated configuration guide")
        print("   2. Login to Gong Admin Panel")
        print("   3. Create webhook rules as specified in the guide")
        print("   4. Test webhooks using provided test payloads")
        print("   5. Monitor n8n dashboard for successful executions")
        return True
    def save_configuration_report(self):
        """Save configuration results"""
        report_file = f"gong_webhook_configuration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(self.webhook_config, f, indent=2)
        print(f"📄 Configuration report saved: {report_file}")
        return report_file
async def main():
    """Main execution function"""
    configurator = GongWebhookConfigurator()
    print("🚀 GONG PRODUCTION WEBHOOK CONFIGURATION")
    print("=" * 48)
    print(f"Webhook URL: {PRODUCTION_WEBHOOK_URL}")
    print(f"Gong API Base: {GONG_API_BASE}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 48)
    success = await configurator.configure_production_webhooks()
    report_file = configurator.save_configuration_report()
    if success:
        print("\n🎉 GONG WEBHOOK CONFIGURATION READY!")
        print("\nNext actions:")
        print("  1. Follow the manual configuration guide")
        print("  2. Create webhook rules in Gong Admin")
        print("  3. Test webhook deliveries")
        print("  4. Monitor production traffic")
    else:
        print("\n❌ GONG WEBHOOK CONFIGURATION FAILED")
        print("Review errors and try again")
    return success
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
