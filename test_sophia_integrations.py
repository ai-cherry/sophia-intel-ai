#!/usr/bin/env python3
"""
Test all Sophia Intel App integrations and services
"""

import os
import sys
import importlib
import requests
from typing import Dict, List, Tuple

class SophiaIntegrationTester:
    def __init__(self):
        self.results = {
            'services': {},
            'integrations': {},
            'mcp_servers': {},
            'env_vars': {}
        }
    
    def test_services(self) -> Dict:
        """Test running services"""
        services = [
            ('Sophia BI Dashboard', 'http://localhost:8000/api/health'),
            ('Bridge API', 'http://localhost:8004/health'),
            ('Memory MCP', 'http://localhost:8081/health'),
            ('Git MCP', 'http://localhost:8084/health'),
        ]
        
        print("\n🔍 Testing Services...\n")
        for name, url in services:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    self.results['services'][name] = '✅ Running'
                    print(f"  ✅ {name}: Running")
                else:
                    self.results['services'][name] = f'⚠️ Status {response.status_code}'
                    print(f"  ⚠️ {name}: Status {response.status_code}")
            except:
                self.results['services'][name] = '❌ Not running'
                print(f"  ❌ {name}: Not running")
        
        return self.results['services']
    
    def test_integrations(self) -> Dict:
        """Test integration imports"""
        integrations = [
            ('Salesforce', 'app.integrations.salesforce_optimized_client', 'SalesforceClient'),
            ('Slack', 'app.integrations.slack_optimized_client', 'SlackClient'),
            ('HubSpot', 'app.integrations.hubspot_optimized_client', 'HubSpotClient'),
            ('Gong', 'app.integrations.gong_optimized_client', 'GongClient'),
            ('Linear', 'app.integrations.linear_client', 'LinearClient'),
            ('Airtable', 'app.integrations.airtable_optimized_client', 'AirtableClient'),
            ('Looker', 'app.integrations.looker_optimized_client', 'LookerClient'),
        ]
        
        print("\n🔌 Testing Integrations...\n")
        for name, module_path, class_name in integrations:
            try:
                module = importlib.import_module(module_path)
                if hasattr(module, class_name):
                    self.results['integrations'][name] = '✅ Available'
                    print(f"  ✅ {name}: Module loaded")
                else:
                    self.results['integrations'][name] = '⚠️ Class not found'
                    print(f"  ⚠️ {name}: Class {class_name} not found")
            except ImportError as e:
                self.results['integrations'][name] = f'❌ Import error'
                print(f"  ❌ {name}: Import error - {str(e)[:50]}")
        
        return self.results['integrations']
    
    def test_env_vars(self) -> Dict:
        """Check environment variables"""
        required_vars = [
            'SALESFORCE_CLIENT_ID',
            'SLACK_BOT_TOKEN',
            'HUBSPOT_API_KEY',
            'GONG_API_KEY',
            'LINEAR_API_KEY',
            'AIRTABLE_API_KEY',
            'OPENAI_API_KEY',
        ]
        
        print("\n🔐 Checking Environment Variables...\n")
        for var in required_vars:
            value = os.getenv(var)
            if value and len(value) > 5:
                self.results['env_vars'][var] = '✅ Set'
                print(f"  ✅ {var}: Configured")
            else:
                self.results['env_vars'][var] = '❌ Missing'
                print(f"  ❌ {var}: Not configured")
        
        return self.results['env_vars']
    
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*60)
        print("         SOPHIA INTEL APP - INTEGRATION REPORT")
        print("="*60)
        
        # Services summary
        running = sum(1 for v in self.results['services'].values() if '✅' in v)
        total = len(self.results['services'])
        print(f"\n📊 Services: {running}/{total} running")
        
        # Integrations summary
        available = sum(1 for v in self.results['integrations'].values() if '✅' in v)
        total = len(self.results['integrations'])
        print(f"🔌 Integrations: {available}/{total} available")
        
        # Environment summary
        configured = sum(1 for v in self.results['env_vars'].values() if '✅' in v)
        total = len(self.results['env_vars'])
        print(f"🔐 Environment: {configured}/{total} configured")
        
        # Overall health
        overall_health = (running + available + configured) / (len(self.results['services']) + len(self.results['integrations']) + len(self.results['env_vars'])) * 100
        
        print(f"\n🎯 Overall Health: {overall_health:.1f}%")
        
        if overall_health < 50:
            print("\n⚠️  ACTION REQUIRED:")
            print("1. Start services: ./start_sophia_complete.sh")
            print("2. Configure .env with API credentials")
            print("3. Install dependencies: pip install -r requirements.txt")

if __name__ == "__main__":
    tester = SophiaIntegrationTester()
    tester.test_services()
    tester.test_integrations()
    tester.test_env_vars()
    tester.generate_report()
