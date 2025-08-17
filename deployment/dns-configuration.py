#!/usr/bin/env python3
"""
DNS Configuration for SOPHIA Intel Production Deployment
Configures sophia-intel.ai domain with proper DNS records
"""

import os
import requests
import json
import sys
from typing import Dict, List, Optional

class DNSimpleManager:
    def __init__(self, api_key: str, account_id: Optional[str] = None):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = "https://api.dnsimple.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_account_id(self) -> str:
        """Get the account ID if not provided"""
        if self.account_id:
            return self.account_id
            
        response = requests.get(f"{self.base_url}/whoami", headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            if 'account' in data['data']:
                self.account_id = str(data['data']['account']['id'])
                return self.account_id
            elif 'user' in data['data']:
                # For user accounts, we need to list accounts
                accounts_response = requests.get(f"{self.base_url}/accounts", headers=self.headers)
                if accounts_response.status_code == 200:
                    accounts = accounts_response.json()['data']
                    if accounts:
                        self.account_id = str(accounts[0]['id'])
                        return self.account_id
        
        raise Exception(f"Failed to get account ID: {response.text}")
    
    def get_domain_info(self, domain: str) -> Dict:
        """Get domain information"""
        account_id = self.get_account_id()
        response = requests.get(
            f"{self.base_url}/{account_id}/domains/{domain}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()['data']
        else:
            raise Exception(f"Failed to get domain info: {response.text}")
    
    def list_dns_records(self, domain: str) -> List[Dict]:
        """List all DNS records for a domain"""
        account_id = self.get_account_id()
        response = requests.get(
            f"{self.base_url}/{account_id}/zones/{domain}/records",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()['data']
        else:
            raise Exception(f"Failed to list DNS records: {response.text}")
    
    def create_dns_record(self, domain: str, record_type: str, name: str, content: str, ttl: int = 3600) -> Dict:
        """Create a DNS record"""
        account_id = self.get_account_id()
        
        record_data = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": ttl
        }
        
        response = requests.post(
            f"{self.base_url}/{account_id}/zones/{domain}/records",
            headers=self.headers,
            json=record_data
        )
        
        if response.status_code == 201:
            return response.json()['data']
        else:
            raise Exception(f"Failed to create DNS record: {response.text}")
    
    def update_dns_record(self, domain: str, record_id: str, record_type: str, name: str, content: str, ttl: int = 3600) -> Dict:
        """Update a DNS record"""
        account_id = self.get_account_id()
        
        record_data = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": ttl
        }
        
        response = requests.patch(
            f"{self.base_url}/{account_id}/zones/{domain}/records/{record_id}",
            headers=self.headers,
            json=record_data
        )
        
        if response.status_code == 200:
            return response.json()['data']
        else:
            raise Exception(f"Failed to update DNS record: {response.text}")
    
    def delete_dns_record(self, domain: str, record_id: str) -> bool:
        """Delete a DNS record"""
        account_id = self.get_account_id()
        
        response = requests.delete(
            f"{self.base_url}/{account_id}/zones/{domain}/records/{record_id}",
            headers=self.headers
        )
        
        return response.status_code == 204

def configure_sophia_intel_dns():
    """Configure DNS for SOPHIA Intel production deployment"""
    
    # Get API key from environment
    api_key = os.getenv('DNSIMPLE_API_KEY')
    if not api_key:
        print("❌ DNSIMPLE_API_KEY environment variable not set")
        sys.exit(1)
    
    # Initialize DNS manager
    dns = DNSimpleManager(api_key)
    domain = "sophia-intel.ai"
    
    print(f"🌐 Configuring DNS for {domain}")
    
    try:
        # Get account info
        account_id = dns.get_account_id()
        print(f"✅ Connected to DNSimple account: {account_id}")
        
        # Get domain info
        domain_info = dns.get_domain_info(domain)
        print(f"✅ Domain found: {domain_info['name']} (ID: {domain_info['id']})")
        
        # List existing records
        existing_records = dns.list_dns_records(domain)
        print(f"📋 Found {len(existing_records)} existing DNS records")
        
        # Define required DNS records for SOPHIA Intel
        required_records = [
            {
                "type": "CNAME",
                "name": "www",
                "content": "sophia-frontend-production.up.railway.app",  # Frontend Railway URL
                "ttl": 300,
                "description": "Frontend Dashboard"
            },
            {
                "type": "CNAME", 
                "name": "api",
                "content": "sophia-backend-production-1fc3.up.railway.app",  # Backend Railway URL
                "ttl": 300,
                "description": "Backend API"
            },
            {
                "type": "CNAME",
                "name": "@",  # Root domain
                "content": "sophia-frontend-production.up.railway.app",  # Frontend Railway URL
                "ttl": 300,
                "description": "Root Domain → Frontend"
            }
        ]
        
        # Create or update DNS records
        for record in required_records:
            existing_record = None
            
            # Check if record already exists
            for existing in existing_records:
                if existing['name'] == record['name'] and existing['type'] == record['type']:
                    existing_record = existing
                    break
            
            if existing_record:
                # Update existing record
                if existing_record['content'] != record['content']:
                    print(f"🔄 Updating {record['type']} record: {record['name']} → {record['content']}")
                    dns.update_dns_record(
                        domain,
                        existing_record['id'],
                        record['type'],
                        record['name'],
                        record['content'],
                        record['ttl']
                    )
                    print(f"✅ Updated {record['description']}")
                else:
                    print(f"✅ {record['description']} already configured correctly")
            else:
                # Create new record
                print(f"➕ Creating {record['type']} record: {record['name']} → {record['content']}")
                dns.create_dns_record(
                    domain,
                    record['type'],
                    record['name'],
                    record['content'],
                    record['ttl']
                )
                print(f"✅ Created {record['description']}")
        
        print("\n🎉 DNS Configuration Complete!")
        print("\n📋 SOPHIA Intel Domain Configuration:")
        print(f"   🌐 Main Site: https://www.sophia-intel.ai")
        print(f"   🌐 Root Domain: https://sophia-intel.ai")
        print(f"   🔗 API Endpoint: https://api.sophia-intel.ai")
        print(f"\n⏱️  DNS propagation may take up to 24 hours")
        print(f"   💡 Use 'dig' or online DNS checkers to verify propagation")
        
        return True
        
    except Exception as e:
        print(f"❌ DNS Configuration failed: {str(e)}")
        return False

if __name__ == "__main__":
    configure_sophia_intel_dns()

