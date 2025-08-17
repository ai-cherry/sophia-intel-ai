#!/usr/bin/env python3
"""
DNS Configuration Script for SOPHIA Intel using DNSimple API
Configures domain routing for all services
"""

import requests
import json
import os
import sys
from typing import Dict, List, Optional

class DNSimpleClient:
    def __init__(self, api_key: str, account_id: Optional[str] = None):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = "https://api.dnsimple.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_accounts(self):
        """Get all accounts"""
        response = requests.get(f"{self.base_url}/accounts", headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            return data["data"]
        else:
            print(f"Error getting accounts: {response.status_code} - {response.text}")
            return None
    
    def list_domains(self):
        """List all domains in the account"""
        if not self.account_id:
            account_info = self.get_account_info()
            if account_info and "account" in account_info:
                self.account_id = account_info["account"]["id"]
        
        response = requests.get(f"{self.base_url}/{self.account_id}/domains", headers=self.headers)
        if response.status_code == 200:
            return response.json()["data"]
        else:
            print(f"Error listing domains: {response.status_code} - {response.text}")
            return []
    
    def get_domain_records(self, domain: str):
        """Get all DNS records for a domain"""
        response = requests.get(f"{self.base_url}/{self.account_id}/zones/{domain}/records", headers=self.headers)
        if response.status_code == 200:
            return response.json()["data"]
        else:
            print(f"Error getting records for {domain}: {response.status_code} - {response.text}")
            return []
    
    def create_record(self, domain: str, record_type: str, name: str, content: str, ttl: int = 3600):
        """Create a DNS record"""
        data = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": ttl
        }
        
        response = requests.post(
            f"{self.base_url}/{self.account_id}/zones/{domain}/records",
            headers=self.headers,
            json=data
        )
        
        if response.status_code == 201:
            print(f"✅ Created {record_type} record: {name}.{domain} → {content}")
            return response.json()["data"]
        else:
            print(f"❌ Error creating record {name}.{domain}: {response.status_code} - {response.text}")
            return None
    
    def update_record(self, domain: str, record_id: int, content: str, ttl: int = 3600):
        """Update an existing DNS record"""
        data = {
            "content": content,
            "ttl": ttl
        }
        
        response = requests.patch(
            f"{self.base_url}/{self.account_id}/zones/{domain}/records/{record_id}",
            headers=self.headers,
            json=data
        )
        
        if response.status_code == 200:
            record = response.json()["data"]
            print(f"✅ Updated record: {record['name']}.{domain} → {content}")
            return record
        else:
            print(f"❌ Error updating record {record_id}: {response.status_code} - {response.text}")
            return None
    
    def delete_record(self, domain: str, record_id: int):
        """Delete a DNS record"""
        response = requests.delete(
            f"{self.base_url}/{self.account_id}/zones/{domain}/records/{record_id}",
            headers=self.headers
        )
        
        if response.status_code == 204:
            print(f"✅ Deleted record ID: {record_id}")
            return True
        else:
            print(f"❌ Error deleting record {record_id}: {response.status_code} - {response.text}")
            return False

def configure_sophia_intel_dns():
    """Configure DNS for SOPHIA Intel services"""
    
    # Get DNSimple API key
    api_key = os.getenv("DNSIMPLE_API_KEY")
    if not api_key:
        print("❌ DNSIMPLE_API_KEY environment variable not set")
        sys.exit(1)
    
    client = DNSimpleClient(api_key)
    
    # Get accounts
    print("🔍 Getting account information...")
    accounts = client.get_accounts()
    if not accounts:
        print("❌ Failed to get accounts")
        sys.exit(1)
    
    # Use first account
    account = accounts[0]
    client.account_id = account["id"]
    print(f"✅ Using Account ID: {client.account_id} ({account['email']})")
    
    # List domains
    print("\n🔍 Listing domains...")
    domains = client.list_domains()
    
    # Find sophia-intel.ai domain
    sophia_domain = None
    for domain in domains:
        if domain["name"] == "sophia-intel.ai":
            sophia_domain = domain
            break
    
    if not sophia_domain:
        print("❌ sophia-intel.ai domain not found in account")
        print("Available domains:")
        for domain in domains:
            print(f"  - {domain['name']}")
        sys.exit(1)
    
    print(f"✅ Found domain: {sophia_domain['name']}")
    
    # Get existing records
    print("\n🔍 Getting existing DNS records...")
    existing_records = client.get_domain_records("sophia-intel.ai")
    
    # Define desired DNS configuration
    # Note: These are placeholder IPs - replace with actual Railway service IPs
    dns_config = {
        "www": {
            "type": "CNAME",
            "content": "sophia-intel-production.up.railway.app"
        },
        "api": {
            "type": "CNAME", 
            "content": "api-gateway-production.up.railway.app"
        },
        "dashboard": {
            "type": "CNAME",
            "content": "dashboard-production.up.railway.app"
        },
        "mcp": {
            "type": "CNAME",
            "content": "mcp-server-production.up.railway.app"
        },
        "@": {
            "type": "CNAME",
            "content": "sophia-intel-production.up.railway.app"
        }
    }
    
    # Create or update records
    print("\n🔧 Configuring DNS records...")
    
    for name, config in dns_config.items():
        record_type = config["type"]
        content = config["content"]
        
        # Check if record already exists
        existing_record = None
        for record in existing_records:
            if record["name"] == name and record["type"] == record_type:
                existing_record = record
                break
        
        if existing_record:
            # Update existing record
            if existing_record["content"] != content:
                client.update_record("sophia-intel.ai", existing_record["id"], content)
            else:
                print(f"✅ Record {name}.sophia-intel.ai already correct: {content}")
        else:
            # Create new record
            client.create_record("sophia-intel.ai", record_type, name, content)
    
    print("\n🎉 DNS configuration complete!")
    print("\n📋 Current DNS Configuration:")
    print("  www.sophia-intel.ai → sophia-intel-production.up.railway.app")
    print("  api.sophia-intel.ai → api-gateway-production.up.railway.app")
    print("  dashboard.sophia-intel.ai → dashboard-production.up.railway.app")
    print("  mcp.sophia-intel.ai → mcp-server-production.up.railway.app")
    print("  sophia-intel.ai → sophia-intel-production.up.railway.app")
    
    print("\n⏰ DNS propagation may take up to 24 hours")
    print("🔒 Remember to configure SSL certificates in Railway")

if __name__ == "__main__":
    configure_sophia_intel_dns()

