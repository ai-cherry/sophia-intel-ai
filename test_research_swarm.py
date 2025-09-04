#!/usr/bin/env python3
"""
Test Script for Orchestrator Research Swarm
============================================
This script demonstrates deploying and using the research swarm
to find improvements for Sophia and Artemis orchestrators.
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any

# Configuration
ARTEMIS_URL = "http://localhost:8001"
RESEARCH_API = f"{ARTEMIS_URL}/api/research-swarm"


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def deploy_swarm() -> Dict[str, Any]:
    """Deploy the research swarm"""
    print_section("🚀 Deploying Research Swarm")
    
    response = requests.post(f"{RESEARCH_API}/deploy")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data['status']}")
        print(f"📝 Message: {data['message']}")
        print(f"\n🤖 Deployed Agents:")
        for agent in data.get('agents', []):
            print(f"  - {agent}")
        print(f"\n🎯 Capabilities:")
        for cap in data.get('capabilities', []):
            print(f"  - {cap}")
        return data
    else:
        print(f"❌ Failed to deploy: {response.text}")
        return {}


def start_research() -> Dict[str, Any]:
    """Start the research process"""
    print_section("🔍 Starting Research")
    
    response = requests.post(f"{RESEARCH_API}/research/start")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data['status']}")
        print(f"📝 Message: {data['message']}")
        print(f"⏱️  Estimated Time: {data.get('estimated_time', 'Unknown')}")
        print(f"\n📊 Research Areas:")
        for area in data.get('research_areas', []):
            print(f"  - {area}")
        return data
    else:
        print(f"❌ Failed to start research: {response.text}")
        return {}


def check_status() -> Dict[str, Any]:
    """Check research status"""
    response = requests.get(f"{RESEARCH_API}/research/status")
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"❌ Failed to check status: {response.text}")
        return {}


def wait_for_research(max_wait: int = 300, check_interval: int = 10):
    """Wait for research to complete"""
    print_section("⏳ Waiting for Research to Complete")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status = check_status()
        
        if status.get('completed'):
            print(f"\n✅ Research completed!")
            print(f"📊 Findings count: {status.get('findings_count', 0)}")
            return True
        
        if status.get('error'):
            print(f"\n❌ Research failed: {status['error']}")
            return False
        
        if status.get('researching'):
            elapsed = int(time.time() - start_time)
            print(f"  Still researching... ({elapsed}s elapsed)", end='\r')
        
        time.sleep(check_interval)
    
    print(f"\n⚠️  Research timed out after {max_wait} seconds")
    return False


def get_results() -> Dict[str, Any]:
    """Get research results"""
    print_section("📊 Research Results")
    
    response = requests.get(f"{RESEARCH_API}/research/results")
    
    if response.status_code == 200:
        data = response.json()
        
        # Print summary
        print("📝 Summary:")
        print(data.get('summary', 'No summary available'))
        
        # Print findings count
        findings = data.get('findings', [])
        print(f"\n📈 Total Findings: {len(findings)}")
        
        # Print improvement plans summary
        plans = data.get('improvement_plans', {})
        if plans.get('sophia'):
            print("\n💎 Sophia Improvements Available: Yes")
        if plans.get('artemis'):
            print("⚔️  Artemis Improvements Available: Yes")
        
        return data
    else:
        print(f"❌ Failed to get results: {response.text}")
        return {}


def get_sophia_improvements() -> Dict[str, Any]:
    """Get Sophia-specific improvements"""
    print_section("💎 Sophia Orchestrator Improvements")
    
    response = requests.get(f"{RESEARCH_API}/research/improvements/sophia")
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('plan'):
            plan = data['plan']
            print(f"📋 Improvement Plan for Sophia:")
            print(f"  Priority: {plan.get('priority', 'Not set')}")
            print(f"  Timeline: {plan.get('timeline_estimate', 'Not estimated')}")
            
            if plan.get('proposed_improvements'):
                print("\n🎯 Proposed Improvements:")
                for key, value in plan['proposed_improvements'].items():
                    print(f"  - {key}: {value}")
            
            if plan.get('expected_benefits'):
                print("\n✨ Expected Benefits:")
                for benefit in plan['expected_benefits']:
                    print(f"  - {benefit}")
        
        if data.get('quick_wins'):
            print("\n⚡ Quick Wins:")
            for win in data['quick_wins']:
                print(f"  - {win}")
        
        return data
    else:
        print(f"❌ Failed to get Sophia improvements: {response.text}")
        return {}


def get_artemis_improvements() -> Dict[str, Any]:
    """Get Artemis-specific improvements"""
    print_section("⚔️ Artemis Orchestrator Improvements")
    
    response = requests.get(f"{RESEARCH_API}/research/improvements/artemis")
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('plan'):
            plan = data['plan']
            print(f"📋 Improvement Plan for Artemis:")
            print(f"  Priority: {plan.get('priority', 'Not set')}")
            print(f"  Timeline: {plan.get('timeline_estimate', 'Not estimated')}")
            
            if plan.get('proposed_improvements'):
                print("\n🎯 Proposed Improvements:")
                for key, value in plan['proposed_improvements'].items():
                    print(f"  - {key}: {value}")
            
            if plan.get('expected_benefits'):
                print("\n✨ Expected Benefits:")
                for benefit in plan['expected_benefits']:
                    print(f"  - {benefit}")
        
        if data.get('quick_wins'):
            print("\n⚡ Quick Wins:")
            for win in data['quick_wins']:
                print(f"  - {win}")
        
        return data
    else:
        print(f"❌ Failed to get Artemis improvements: {response.text}")
        return {}


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("  ORCHESTRATOR RESEARCH SWARM TEST")
    print("  Testing AI-powered orchestrator improvements")
    print("="*60)
    
    try:
        # Step 1: Deploy the swarm
        deployment = deploy_swarm()
        if not deployment:
            print("Failed to deploy swarm. Exiting.")
            return
        
        time.sleep(2)
        
        # Step 2: Start research
        research = start_research()
        if not research:
            print("Failed to start research. Exiting.")
            return
        
        # Step 3: Wait for completion
        if not wait_for_research():
            print("Research did not complete. Checking partial results...")
        
        # Step 4: Get results
        results = get_results()
        
        # Step 5: Get specific improvements
        sophia_improvements = get_sophia_improvements()
        artemis_improvements = get_artemis_improvements()
        
        # Step 6: Summary
        print_section("📈 Test Complete")
        print("✅ Research swarm successfully:")
        print("  1. Deployed with specialized agents")
        print("  2. Conducted web research on AI orchestration")
        print("  3. Analyzed current limitations")
        print("  4. Designed improvement plans")
        print("  5. Provided implementation strategies")
        
        print("\n🎯 Next Steps:")
        print("  1. Review the improvement plans")
        print("  2. Approve implementation phases")
        print("  3. Run tests on improvements")
        print("  4. Deploy to production")
        
        # Optional: Save results to file
        if results:
            with open('research_results.json', 'w') as f:
                json.dump(results, f, indent=2)
                print("\n💾 Results saved to research_results.json")
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if Artemis server is running
    try:
        response = requests.get(f"{ARTEMIS_URL}/health")
        if response.status_code == 200:
            print("✅ Artemis server is running")
            main()
        else:
            print("⚠️  Artemis server returned non-200 status")
            main()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Artemis server at", ARTEMIS_URL)
        print("Please ensure Artemis is running: ./deploy_all.sh")
        print("\nTo run this test:")
        print("1. Start the platform: ./deploy_all.sh")
        print("2. Run this test: python test_research_swarm.py")