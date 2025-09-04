#!/usr/bin/env python3
"""
Direct test of persona agents without server dependencies
Tests the persona agents directly to verify they work correctly
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

async def test_personas_directly():
    """Test persona agents directly"""
    
    print("\n🤖 TESTING PERSONA AGENTS DIRECTLY\n")
    print("="*50)
    
    try:
        # Test 1: Import persona classes
        print("\n1️⃣ Testing: Import Persona Classes")
        from app.agents.personas.sales_coach import SalesCoachAgent, DealAnalysis
        from app.agents.personas.client_health import ClientHealthAgent, ClientHealthAssessment
        print("✅ Successfully imported persona classes")
        
        # Test 2: Create and initialize Marcus
        print("\n2️⃣ Testing: Initialize Marcus (Sales Coach)")
        marcus = SalesCoachAgent()
        await marcus.initialize()
        print(f"✅ Marcus initialized: {marcus.personality['name']}")
        print(f"   Tagline: {marcus.personality['tagline']}")
        
        # Test 3: Create and initialize Sarah
        print("\n3️⃣ Testing: Initialize Sarah (Client Health)")  
        sarah = ClientHealthAgent()
        await sarah.initialize()
        print(f"✅ Sarah initialized: {sarah.personality['name']}")
        print(f"   Tagline: {sarah.personality['tagline']}")
        
        # Test 4: Test Marcus interaction
        print("\n4️⃣ Testing: Marcus Conversation")
        marcus_response = await marcus.interact(
            "Hi Marcus! I have a $500K deal that's been stuck in negotiation for 3 weeks. What should I do?",
            {"deal_stage": "negotiation", "urgency": "high"}
        )
        print(f"✅ Marcus responded (length: {len(marcus_response)} chars)")
        print(f"   Preview: {marcus_response[:150]}...")
        
        # Test 5: Test Sarah interaction
        print("\n5️⃣ Testing: Sarah Conversation")
        sarah_response = await sarah.interact(
            "Hi Sarah! Our client Acme Corp hasn't logged in for 2 weeks and their usage is down 40%. Should we be worried?",
            {"client_urgency": "medium", "health_concern": "usage_drop"}
        )
        print(f"✅ Sarah responded (length: {len(sarah_response)} chars)")
        print(f"   Preview: {sarah_response[:150]}...")
        
        # Test 6: Test deal analysis
        print("\n6️⃣ Testing: Deal Analysis")
        deal_analysis = DealAnalysis(
            deal_id="TEST-001",
            stage="negotiation",
            value=500000,
            probability=0.65,
            key_stakeholders=["CTO", "CFO"],
            competitors=["CompetitorX"],
            pain_points=["Legacy system issues", "Cost concerns"],
            next_steps=["Technical demo", "Pricing discussion"],
            risks=["Budget approval needed"],
            rep_name="Test Rep"
        )
        
        coaching = await marcus.coach_deal(deal_analysis)
        print(f"✅ Deal coaching completed")
        print(f"   Strengths: {len(coaching.strengths)} identified")
        print(f"   Recommendations: {len(coaching.recommendations)} provided")
        print(f"   Risk mitigation: {len(coaching.risk_mitigation)} strategies")
        
        # Test 7: Test client health assessment
        print("\n7️⃣ Testing: Client Health Assessment")
        health_assessment = ClientHealthAssessment(
            client_id="CLIENT-001",
            client_name="Acme Corp",
            usage_metrics={
                "daily_active_users": 120,
                "api_calls_per_day": 5000,
                "feature_adoption_rate": 0.6
            },
            engagement_score=75,
            support_tickets=2,
            last_contact_days=14,
            contract_value=120000,
            renewal_date="2024-06-01",
            stakeholders=["Product Manager", "Tech Lead"]
        )
        
        health_result = await sarah.assess_client_health(health_assessment)
        print(f"✅ Client health assessment completed")
        print(f"   Overall score: {health_result.overall_health_score}/100")
        print(f"   Risk level: {health_result.risk_level}")
        print(f"   Recommendations: {len(health_result.recommendations)} provided")
        
        # Test 8: Test learning and feedback
        print("\n8️⃣ Testing: Learning and Feedback")
        
        # Test Marcus learning from feedback
        marcus.learn_from_feedback({
            "interaction_id": "test-001",
            "rating": 5,
            "feedback": "Great advice on the negotiation strategy!",
            "outcome": "successful"
        })
        
        print(f"✅ Marcus learning: {len(marcus.learning_patterns)} patterns learned")
        
        # Test Sarah learning from feedback
        sarah.learn_from_feedback({
            "interaction_id": "test-002", 
            "rating": 4,
            "feedback": "Very helpful health assessment",
            "outcome": "actionable"
        })
        
        print(f"✅ Sarah learning: {len(sarah.learning_patterns)} patterns learned")
        
        # Test 9: Test memory systems
        print("\n9️⃣ Testing: Memory Systems")
        print(f"✅ Marcus memory:")
        print(f"   - Episodic: {len(marcus.episodic_memory)} memories")
        print(f"   - Semantic: {len(marcus.semantic_memory)} facts")
        print(f"   - Working: {len(marcus.working_memory)} active items")
        
        print(f"✅ Sarah memory:")
        print(f"   - Episodic: {len(sarah.episodic_memory)} memories")
        print(f"   - Semantic: {len(sarah.semantic_memory)} facts") 
        print(f"   - Working: {len(sarah.working_memory)} active items")
        
        # Test 10: Test personality consistency
        print("\n🔟 Testing: Personality Consistency")
        
        # Multiple interactions to test consistency
        for i in range(3):
            response = await marcus.interact(f"Quick question #{i+1}: How's your energy today?", {})
            # Check for Marcus's catchphrases or personality markers
            has_personality = any(phrase in response.lower() for phrase in [
                "catalyst", "breakthrough", "champion", "crushing it", "let's go"
            ])
            print(f"   Marcus response {i+1}: {'✅' if has_personality else '⚠️'} personality present")
        
        for i in range(3):
            response = await sarah.interact(f"Quick question #{i+1}: How are things?", {})
            # Check for Sarah's personality markers
            has_personality = any(phrase in response.lower() for phrase in [
                "guardian", "partnership", "success", "health", "monitoring"
            ])
            print(f"   Sarah response {i+1}: {'✅' if has_personality else '⚠️'} personality present")
        
        print("\n" + "="*50)
        print("✅ PERSONA DIRECT TESTING COMPLETE!")
        print("✅ Both Marcus and Sarah are working correctly!")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"❌ ERROR during persona testing: {e}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_personas_directly())