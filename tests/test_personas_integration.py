#!/usr/bin/env python3
"""
Test script for persona agents integration
Tests that personas can be initialized and interacted with via API
"""

import asyncio
import httpx
import json
from datetime import datetime

# Server configuration
API_BASE = "http://localhost:8003"
PERSONAS_API = f"{API_BASE}/api/personas"

async def test_persona_integration():
    """Test persona agents end-to-end"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n🤖 TESTING PERSONA AGENTS INTEGRATION\n")
        print("="*50)
        
        # Test 1: Get AI team members
        print("\n1️⃣ Testing: Get AI Team Members")
        try:
            response = await client.get(f"{PERSONAS_API}/team")
            if response.status_code == 200:
                team_data = response.json()
                print(f"✅ Team endpoint working!")
                print(f"   Found {team_data.get('total', 0)} team members:")
                for member in team_data.get('team_members', []):
                    print(f"   - {member['name']} ({member['title']})")
            else:
                print(f"❌ Failed to get team: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting team: {e}")
        
        # Test 2: Initialize Marcus
        print("\n2️⃣ Testing: Initialize Marcus (Sales Coach)")
        try:
            response = await client.post(f"{PERSONAS_API}/persona/marcus/initialize")
            if response.status_code == 200:
                print("✅ Marcus initialized successfully!")
            else:
                print(f"❌ Failed to initialize Marcus: {response.status_code}")
        except Exception as e:
            print(f"❌ Error initializing Marcus: {e}")
        
        # Test 3: Initialize Sarah
        print("\n3️⃣ Testing: Initialize Sarah (Client Health)")
        try:
            response = await client.post(f"{PERSONAS_API}/persona/sarah/initialize")
            if response.status_code == 200:
                print("✅ Sarah initialized successfully!")
            else:
                print(f"❌ Failed to initialize Sarah: {response.status_code}")
        except Exception as e:
            print(f"❌ Error initializing Sarah: {e}")
        
        # Test 4: Chat with Marcus
        print("\n4️⃣ Testing: Chat with Marcus")
        try:
            chat_request = {
                "message": "Hi Marcus! I'm struggling with a deal worth $500K. The client seems hesitant. What should I do?",
                "context": {"user": "test_user", "deal_stage": "negotiation"}
            }
            response = await client.post(f"{PERSONAS_API}/chat/marcus", json=chat_request)
            if response.status_code == 200:
                chat_data = response.json()
                print("✅ Chat with Marcus successful!")
                print(f"   Response: {chat_data.get('response', '')[:200]}...")
            else:
                print(f"❌ Failed to chat with Marcus: {response.status_code}")
        except Exception as e:
            print(f"❌ Error chatting with Marcus: {e}")
        
        # Test 5: Get deal coaching from Marcus
        print("\n5️⃣ Testing: Deal Coaching from Marcus")
        try:
            deal_request = {
                "deal_id": "TEST-001",
                "deal_name": "Enterprise Software Deal",
                "stage": "negotiation",
                "value": 500000,
                "probability": 0.65,
                "stakeholders": ["CTO", "CFO"],
                "competitors": ["Competitor A"],
                "pain_points": ["Current system is slow", "High maintenance costs"],
                "next_steps": ["Demo scheduled", "Contract review"],
                "risks": ["Budget constraints"],
                "rep_name": "Test Rep"
            }
            response = await client.post(f"{PERSONAS_API}/marcus/coach-deal", json=deal_request)
            if response.status_code == 200:
                coaching_data = response.json()
                print("✅ Deal coaching received!")
                print(f"   Message: {coaching_data.get('message', '')[:200]}...")
            else:
                print(f"❌ Failed to get deal coaching: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting deal coaching: {e}")
        
        # Test 6: Health assessment from Sarah
        print("\n6️⃣ Testing: Client Health Assessment from Sarah")
        try:
            health_request = {
                "client_id": "CLIENT-001",
                "client_name": "Acme Corp",
                "usage_metrics": {
                    "daily_active_users": 150,
                    "api_calls": 10000,
                    "feature_adoption": 0.75
                },
                "engagement_score": 85,
                "support_tickets": 3,
                "last_contact_days": 5,
                "contract_value": 120000,
                "renewal_date": "2024-06-01",
                "stakeholders": ["Product Manager", "Engineering Lead"]
            }
            response = await client.post(f"{PERSONAS_API}/sarah/assess-health", json=health_request)
            if response.status_code == 200:
                health_data = response.json()
                print("✅ Health assessment received!")
                print(f"   Assessment: {health_data.get('message', '')[:200]}...")
            else:
                print(f"❌ Failed to get health assessment: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting health assessment: {e}")
        
        # Test 7: System health check
        print("\n7️⃣ Testing: Persona System Health")
        try:
            response = await client.get(f"{PERSONAS_API}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ System health: {health_data.get('status', 'unknown')}")
                for persona_id, status in health_data.get('personas', {}).items():
                    print(f"   - {persona_id}: {status}")
            else:
                print(f"❌ Failed to get system health: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting system health: {e}")
        
        # Test 8: Get system stats
        print("\n8️⃣ Testing: System Statistics")
        try:
            response = await client.get(f"{PERSONAS_API}/stats")
            if response.status_code == 200:
                stats_data = response.json()
                stats = stats_data.get('statistics', {})
                print("✅ System statistics:")
                print(f"   - Total personas: {stats.get('total_personas', 0)}")
                print(f"   - Active personas: {stats.get('active_personas', 0)}")
                print(f"   - Total interactions: {stats.get('total_interactions', 0)}")
                print(f"   - WebSocket connections: {stats.get('websocket_connections', 0)}")
            else:
                print(f"❌ Failed to get stats: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
        
        print("\n" + "="*50)
        print("✅ PERSONA TESTING COMPLETE!")
        print("="*50 + "\n")

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_persona_integration())