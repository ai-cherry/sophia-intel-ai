#!/usr/bin/env python3
"""
CloudFlare DNS Setup for sophia-intel.ai
Better than NameCheap's bullshit manual process
"""

import requests
import json
import time

class CloudFlareDNSSetup:
    def __init__(self, api_token, zone_name="sophia-intel.ai"):
        self.api_token = api_token
        self.zone_name = zone_name
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        self.zone_id = None

    def get_zone_id(self):
        """Get zone ID for the domain"""
        response = requests.get(
            f"{self.base_url}/zones?name={self.zone_name}",
            headers=self.headers
        )

        if response.status_code == 200:
            zones = response.json()['result']
            if zones:
                self.zone_id = zones[0]['id']
                return self.zone_id

        print(f"❌ Zone {self.zone_name} not found. Add it to CloudFlare first.")
        return None

    def create_dns_record(self, record_type, name, content, proxied=True):
        """Create a DNS record"""
        if not self.zone_id:
            self.get_zone_id()

        data = {
            'type': record_type,
            'name': name,
            'content': content,
            'ttl': 300,
            'proxied': proxied
        }

        response = requests.post(
            f"{self.base_url}/zones/{self.zone_id}/dns_records",
            headers=self.headers,
            json=data
        )

        if response.status_code == 200:
            print(f"✅ Created {record_type} record: {name} → {content}")
            return True
        else:
            print(f"❌ Failed to create {record_type} record: {name}")
            print(f"   Error: {response.json()}")
            return False

    def setup_sophia_dns(self):
        """Set up complete DNS for sophia-intel.ai"""
        print("🚀 Setting up CloudFlare DNS for sophia-intel.ai")
        print("=" * 50)

        if not self.get_zone_id():
            return False

        # DNS records for Sophia AI
        records = [
            # Main domain
            ('A', 'sophia-intel.ai', '192.222.58.232', True),
            ('A', 'www', '192.222.58.232', True),

            # API endpoints
            ('A', 'api', '192.222.58.232', True),
            ('A', 'chat', '192.222.58.232', True),
            ('A', 'dashboard', '192.222.58.232', True),
            ('A', 'agents', '192.222.58.232', True),
            ('A', 'docs', '192.222.58.232', True),
            ('A', 'status', '192.222.58.232', True),

            # Load balancers (not proxied for direct access)
            ('A', 'api-lb', '192.222.58.232', False),
            ('A', 'chat-lb', '192.222.58.232', False),
            ('A', 'dash-lb', '192.222.58.232', False),

            # Security
            ('TXT', 'sophia-intel.ai', 'v=spf1 include:_spf.google.com ~all', False),
        ]

        success_count = 0
        for record_type, name, content, proxied in records:
            if self.create_dns_record(record_type, name, content, proxied):
                success_count += 1
            time.sleep(1)  # Rate limiting

        print(f"\n🎉 DNS Setup Complete!")
        print(f"✅ {success_count}/{len(records)} records created successfully")
        print(f"🌐 sophia-intel.ai will be live in 2-5 minutes")
        print(f"🔒 SSL certificates will be issued automatically")
        print(f"⚡ CDN acceleration enabled globally")

        return success_count == len(records)

def main():
    print("CloudFlare DNS Setup for Sophia AI")
    print("=" * 40)

    api_token = input("Enter your CloudFlare API token: ").strip()

    if not api_token:
        print("❌ API token required. Get it from CloudFlare dashboard.")
        return

    cf = CloudFlareDNSSetup(api_token)
    success = cf.setup_sophia_dns()

    if success:
        print("\n🎉 SUCCESS! Sophia AI is now live on CloudFlare!")
        print("\nNext steps:")
        print("1. Test: curl http://104.171.202.103:8080/api/health")
        print("2. Verify SSL: https://www.ssllabs.com/ssltest/")
        print("3. Check CDN: https://www.whatsmydns.net/")
    else:
        print("\n❌ Setup failed. Check your API token and try again.")

if __name__ == "__main__":
    main()
