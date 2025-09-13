#!/usr/bin/env python3
"""
DNSimple DNS Setup for Sophia AI
The DNS solution that doesn't suck
"""
import time
import requests
class DNSimpleSetup:
    def __init__(self, api_token, account_id):
        self.api_token = api_token
        self.account_id = account_id
        self.base_url = "https://api.dnsimple.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        self.domain = "sophia-intel.ai"
        self.lambda_ip = "192.222.58.232"
    def sophia_api_connection(self):
        """Test DNSimple API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/whoami", headers=self.headers, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Connected to DNSimple as: {data['data']['email']}")
                return True
            else:
                print(f"❌ API connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API connection error: {e}")
            return False
    def check_domain_zone(self):
        """Check if domain zone exists"""
        try:
            response = requests.get(
                f"{self.base_url}/{self.account_id}/zones/{self.domain}",
                headers=self.headers,
                timeout=10,
            )
            if response.status_code == 200:
                print(f"✅ Domain zone exists: {self.domain}")
                return True
            elif response.status_code == 404:
                print(f"⚠️  Domain zone not found: {self.domain}")
                print("   Add the domain to DNSimple first via the dashboard")
                return False
            else:
                print(f"❌ Error checking domain: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error checking domain: {e}")
            return False
    def create_dns_record(self, name, record_type, content, ttl=300):
        """Create a DNS record"""
        data = {"name": name, "type": record_type, "content": content, "ttl": ttl}
        try:
            response = requests.post(
                f"{self.base_url}/{self.account_id}/zones/{self.domain}/records",
                headers=self.headers,
                json=data,
                timeout=10,
            )
            if response.status_code == 201:
                record_data = response.json()["data"]
                display_name = name if name else "@"
                print(f"✅ Created {record_type} record: {display_name} → {content}")
                return True
            else:
                error_data = response.json()
                display_name = name if name else "@"
                print(f"❌ Failed to create {record_type} record: {display_name}")
                print(f"   Error: {error_data}")
                return False
        except Exception as e:
            display_name = name if name else "@"
            print(f"❌ Error creating {record_type} record {display_name}: {e}")
            return False
    def get_existing_records(self):
        """Get existing DNS records"""
        try:
            response = requests.get(
                f"{self.base_url}/{self.account_id}/zones/{self.domain}/records",
                headers=self.headers,
                timeout=10,
            )
            if response.status_code == 200:
                records = response.json()["data"]
                print(f"📋 Found {len(records)} existing DNS records")
                return records
            else:
                print(f"❌ Error getting records: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error getting records: {e}")
            return []
    def setup_sophia_dns(self):
        """Set up complete DNS for Sophia AI"""
        print("🚀 DNSimple DNS Setup for Sophia AI")
        print("=" * 50)
        print(f"Domain: {self.domain}")
        print(f"Target: Lambda Labs ({self.lambda_ip})")
        print()
        # Test API connection
        if not self.sophia_api_connection():
            return False
        # Check domain zone
        if not self.check_domain_zone():
            return False
        # Get existing records
        existing_records = self.get_existing_records()
        # DNS records for Sophia AI
        records_to_create = [
            ("", "A", self.lambda_ip),  # Root domain
            ("www", "A", self.lambda_ip),  # www
            ("api", "A", self.lambda_ip),  # API endpoint
            ("chat", "A", self.lambda_ip),  # Chat interface
            ("dashboard", "A", self.lambda_ip),  # Dashboard
            ("agents", "A", self.lambda_ip),  # AI agents
            ("docs", "A", self.lambda_ip),  # Documentation
            ("status", "A", self.lambda_ip),  # Status page
            ("api-lb", "A", self.lambda_ip),  # API load balancer
            ("chat-lb", "A", self.lambda_ip),  # Chat load balancer
        ]
        print(f"📝 Creating {len(records_to_create)} DNS records...")
        print()
        success_count = 0
        for name, record_type, content in records_to_create:
            if self.create_dns_record(name, record_type, content):
                success_count += 1
            time.sleep(0.5)  # Rate limiting
        print()
        print("🎉 DNS Setup Complete!")
        print(
            f"✅ {success_count}/{len(records_to_create)} records created successfully"
        )
        if success_count == len(records_to_create):
            print()
            print("🌐 Sophia AI domains configured:")
            print("  • https://sophia-intel.ai")
            print("  • https://www.sophia-intel.ai")
            print("  • http://104.171.202.103:8080/api")
            print("  • https://chat.sophia-intel.ai")
            print("  • https://dashboard.sophia-intel.ai")
            print()
            print("⏳ DNS propagation: 2-5 minutes")
            print("🔒 SSL certificates: Auto-issued by DNSimple")
            print("⚡ Global CDN: Available via DNSimple")
            print()
            print("🧪 Test commands:")
            print("  curl http://104.171.202.103:8080/api/health")
            print("  curl https://chat.sophia-intel.ai/health")
            return True
        else:
            print("⚠️  Some records failed to create. Check the errors above.")
            return False
    def get_nameservers(self):
        """Get DNSimple nameservers for the domain"""
        try:
            response = requests.get(
                f"{self.base_url}/{self.account_id}/zones/{self.domain}",
                headers=self.headers,
                timeout=10,
            )
            if response.status_code == 200:
                zone_data = response.json()["data"]
                nameservers = zone_data.get("name_servers", [])
                print("📡 DNSimple Nameservers:")
                for i, ns in enumerate(nameservers, 1):
                    print(f"  {i}. {ns}")
                print()
                print("🔧 Update these nameservers at NameCheap:")
                print("  1. Login to NameCheap")
                print("  2. Domain List → sophia-intel.ai → Manage")
                print("  3. Domain tab → Nameservers → Custom DNS")
                print("  4. Enter the nameservers above")
                print("  5. Save changes")
                print()
                print("⏳ Nameserver propagation: 15-30 minutes")
                return nameservers
            else:
                print(f"❌ Error getting nameservers: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error getting nameservers: {e}")
            return []
def main():
    """Main execution"""
    print("DNSimple Setup for Sophia AI")
    print("=" * 40)
    print()
    # Get API credentials
    api_token = input("Enter your DNSimple API token: ").strip()
    if not api_token:
        print("❌ API token required. Get it from DNSimple dashboard.")
        return
    account_id = input("Enter your DNSimple account ID: ").strip()
    if not account_id:
        print("❌ Account ID required. Find it in DNSimple dashboard.")
        return
    print()
    # Set up DNS
    dns_setup = DNSimpleSetup(api_token, account_id)
    # Get nameservers first
    print("📡 Getting DNSimple nameservers...")
    nameservers = dns_setup.get_nameservers()
    if nameservers:
        print()
        proceed = (
            input("Have you updated nameservers at NameCheap? (y/n): ").strip().lower()
        )
        if proceed != "y":
            print(
                "⚠️  Update nameservers at NameCheap first, then run this script again."
            )
            return
    # Set up DNS records
    success = dns_setup.setup_sophia_dns()
    if success:
        print("\n🎉 SUCCESS! Sophia AI DNS is configured on DNSimple!")
        print("🚀 Your enhanced AI platform will be live in 2-5 minutes!")
    else:
        print("\n❌ Setup failed. Check the errors above and try again.")
if __name__ == "__main__":
    main()
