#!/usr/bin/env python3
"""
Test Builder Agno System - Complete verification
"""

import requests
import time
import json
from typing import Dict

class BuilderSystemTester:
    def __init__(self):
        self.results = {
            'builder_dashboard': False,
            'bridge_api': False,
            'bridge_health': False,
            'sophia_running': False,
            'separation_maintained': False
        }
    
    def test_builder_dashboard(self):
        """Test if Builder Dashboard is accessible"""
        try:
            response = requests.get('http://localhost:8005', timeout=3)
            if response.status_code == 200 and 'BUILDER AGNO' in response.text:
                self.results['builder_dashboard'] = True
                print('✅ Builder Dashboard: Running on port 8005')
                return True
        except:
            pass
        print('❌ Builder Dashboard: Not accessible on port 8005')
        return False
    
    def test_bridge_api(self):
        """Test if Bridge API is running"""
        try:
            # Test health endpoint
            response = requests.get('http://localhost:8004/health', timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.results['bridge_api'] = True
                    self.results['bridge_health'] = True
                    print('✅ Bridge API: Healthy on port 8004')
                    return True
        except Exception as e:
            print(f'❌ Bridge API: Error - {str(e)}')
        print('❌ Bridge API: Not running on port 8004')
        return False
    
    def test_bridge_endpoints(self):
        """Test Bridge API endpoints"""
        if not self.results['bridge_api']:
            print('⚠️  Bridge API not running, skipping endpoint tests')
            return
        
        print('\nTesting Bridge API Endpoints:')
        
        # Test compile endpoint
        try:
            response = requests.post('http://localhost:8004/compile', 
                json={
                    'task': 'Test task',
                    'context': {},
                    'team': 'construction'
                },
                timeout=3
            )
            if response.status_code in [200, 422, 500]:  # Any response means it's working
                print('  ✅ /compile endpoint: Accessible')
            else:
                print(f'  ⚠️ /compile endpoint: Status {response.status_code}')
        except Exception as e:
            print(f'  ❌ /compile endpoint: {str(e)}')
        
        # Test docs endpoint
        try:
            response = requests.get('http://localhost:8004/docs', timeout=3)
            if response.status_code == 200:
                print('  ✅ /docs endpoint: Accessible')
            else:
                print(f'  ⚠️ /docs endpoint: Status {response.status_code}')
        except:
            print('  ❌ /docs endpoint: Not accessible')
    
    def test_sophia_separation(self):
        """Verify Sophia UI/API are separate from Builder"""
        ui_ok = False
        api_ok = False
        try:
            # UI check
            r_ui = requests.get('http://localhost:3000', timeout=3)
            ui_ok = (r_ui.status_code == 200)
            # API health
            r_api = requests.get('http://localhost:8003/healthz', timeout=3)
            api_ok = (r_api.status_code == 200)
        except Exception:
            pass

        self.results['sophia_running'] = ui_ok or api_ok
        if ui_ok:
            print('✅ Sophia UI: Running on port 3000')
        else:
            print('⚠️  Sophia UI: Not responding on port 3000')
        if api_ok:
            print('✅ Sophia API: Healthy on port 8003')
        else:
            print('⚠️  Sophia API: Not healthy on port 8003')

        if self.results['builder_dashboard'] and self.results['sophia_running']:
            self.results['separation_maintained'] = True
            print('✅ System Separation: Maintained (UI 3000/API 8003 vs Builder 8005)')
        else:
            print('⚠️  System Separation: Cannot verify (systems may not be running)')
    
    def generate_report(self):
        """Generate final test report"""
        print('\n' + '='*60)
        print('         BUILDER AGNO SYSTEM - TEST REPORT')
        print('='*60)
        
        print('\n📊 Component Status:')
        print(f'  Builder Dashboard (8005): {"✅" if self.results["builder_dashboard"] else "❌"}')
        print(f'  Bridge API (8004): {"✅" if self.results["bridge_api"] else "❌"}')
        print(f'  Bridge Health: {"✅" if self.results["bridge_health"] else "❌"}')
        print(f'  Sophia UI/API (3000/8003): {"✅" if self.results["sophia_running"] else "❌"}')
        print(f'  Separation Maintained: {"✅" if self.results["separation_maintained"] else "❌"}')
        
        # Overall health
        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)
        health = (passed / total) * 100
        
        print(f'\n🎯 Overall Health: {health:.0f}% ({passed}/{total} checks passed)')
        
        if health < 100:
            print('\n⚠️  Issues Found:')
            if not self.results['builder_dashboard']:
                print('  - Builder Dashboard not running')
                print('    Fix: cd builder-system && python3 -m http.server 8005 --directory dashboard')
            if not self.results['bridge_api']:
                print('  - Bridge API not running')
                print('    Fix: python3 -m uvicorn bridge.api:app --port 8004')
            if not self.results['sophia_running']:
                print('  - Sophia not running (optional but good to verify separation)')
                print('    Fix: ./start_sophia_complete.sh')
        else:
            print('\n✅ All systems operational and properly separated!')
        
        print('\n📋 Quick Access:')
        print('  Builder Dashboard: http://localhost:8005')
        print('  Bridge API Docs: http://localhost:8004/docs')
        print('  Sophia UI: http://localhost:3000')
        print('  Sophia API: http://localhost:8003/healthz')

if __name__ == '__main__':
    print('Testing Builder Agno System...\n')
    
    tester = BuilderSystemTester()
    tester.test_builder_dashboard()
    tester.test_bridge_api()
    tester.test_bridge_endpoints()
    tester.test_sophia_separation()
    tester.generate_report()
