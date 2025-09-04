#!/usr/bin/env python3
"""
Minimal test of persona agents - direct class imports only
"""

import asyncio
import sys
import os
from typing import Dict, Any
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

async def test_personas_minimal():
    """Test persona agents with minimal dependencies"""
    
    print("\n🤖 TESTING PERSONAS - MINIMAL APPROACH\n")
    print("="*50)
    
    try:
        print("\n1️⃣ Testing: Import base persona classes")
        
        # Import personas directly 
        sys.path.insert(0, '/Users/lynnmusil/sophia-intel-ai')
        
        # Import base persona class first
        from app.agents.personas.base_persona import BasePersonaAgent, PersonaProfile, PersonalityTrait
        print("✅ Base persona classes imported")
        
        # Import specific persona classes
        from app.agents.personas.sales_coach import SalesCoachAgent
        from app.agents.personas.client_health import ClientHealthAgent
        print("✅ Specific persona classes imported")
        
        print("\n2️⃣ Testing: Create persona instances")
        
        # Create Marcus (Sales Coach)
        marcus = SalesCoachAgent()
        print(f"✅ Marcus created: {marcus.__class__.__name__}")
        
        # Create Sarah (Client Health)
        sarah = ClientHealthAgent()
        print(f"✅ Sarah created: {sarah.__class__.__name__}")
        
        print("\n3️⃣ Testing: Access personality data")
        
        # Check Marcus personality
        print(f"✅ Marcus personality loaded:")
        print(f"   Name: {marcus.personality.get('name', 'Unknown')}")
        print(f"   Title: {marcus.personality.get('title', 'Unknown')}")
        print(f"   Tagline: {marcus.personality.get('tagline', 'Unknown')}")
        
        # Check Sarah personality  
        print(f"✅ Sarah personality loaded:")
        print(f"   Name: {sarah.personality.get('name', 'Unknown')}")
        print(f"   Title: {sarah.personality.get('title', 'Unknown')}")  
        print(f"   Tagline: {sarah.personality.get('tagline', 'Unknown')}")
        
        print("\n4️⃣ Testing: Memory systems")
        
        # Test memory initialization
        print(f"✅ Marcus memory systems:")
        print(f"   Episodic: {len(marcus.episodic_memory)} items")
        print(f"   Semantic: {len(marcus.semantic_memory)} items")
        print(f"   Working: {len(marcus.working_memory)} items")
        
        print(f"✅ Sarah memory systems:")
        print(f"   Episodic: {len(sarah.episodic_memory)} items")
        print(f"   Semantic: {len(sarah.semantic_memory)} items")
        print(f"   Working: {len(sarah.working_memory)} items")
        
        print("\n5️⃣ Testing: Basic functionality")
        
        # Test stats
        marcus_stats = marcus.get_stats()
        print(f"✅ Marcus stats: {list(marcus_stats.keys())}")
        
        sarah_stats = sarah.get_stats()
        print(f"✅ Sarah stats: {list(sarah_stats.keys())}")
        
        # Test greeting
        marcus_greeting = marcus.get_persona_greeting("Test User")
        print(f"✅ Marcus greeting: {marcus_greeting[:100]}...")
        
        sarah_greeting = sarah.get_persona_greeting("Test User")
        print(f"✅ Sarah greeting: {sarah_greeting[:100]}...")
        
        print("\n6️⃣ Testing: Learning systems")
        
        # Test learning pattern addition
        marcus.learn_from_feedback({
            "rating": 5,
            "feedback": "Great advice!",
            "context": "deal_coaching"
        })
        print(f"✅ Marcus learning: {len(marcus.learning_patterns)} patterns")
        
        sarah.learn_from_feedback({
            "rating": 4,
            "feedback": "Helpful health insights",
            "context": "health_assessment"
        })
        print(f"✅ Sarah learning: {len(sarah.learning_patterns)} patterns")
        
        print("\n" + "="*50)
        print("✅ PERSONA MINIMAL TESTING COMPLETE!")
        print("✅ Basic persona functionality working!")
        print("="*50 + "\n")
        
        # Summary
        print("📊 SUMMARY:")
        print(f"   - Marcus: {marcus.personality['name']} ({marcus.personality['title']})")
        print(f"   - Sarah: {sarah.personality['name']} ({sarah.personality['title']})")
        print(f"   - Both personas have functional memory and learning systems")
        print(f"   - Personas can generate greetings and stats")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR during minimal persona testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(test_personas_minimal())
    
    if success:
        print("\n🎉 PERSONAS ARE READY FOR INTEGRATION!")
    else:
        print("\n❌ PERSONA TESTING FAILED")
        sys.exit(1)