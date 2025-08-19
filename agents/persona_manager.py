# agents/persona_manager.py
from qdrant_client import QdrantClient
import redis.asyncio as redis
import os
import json
import time
import hashlib
from typing import Dict, List, Optional
import asyncio

class PersonaManager:
    def __init__(self):
        self.qdrant = QdrantClient(
            url="https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io", 
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.redis = redis.from_url(os.getenv("REDIS_URL", "redis://sophia-cache.fly.dev"))
        
        # SOPHIA's badass persona - neon cowboy tech vibe
        self.persona = {
            "name": "SOPHIA",
            "tone": "confident, witty, direct, slightly sarcastic",
            "style": "neon cowboy tech vibe with attitude",
            "greeting_variants": [
                "Yo! SOPHIA here, ready to crush whatever you throw at me. What's the mission?",
                "Hey there, partner! SOPHIA's locked and loaded. What are we conquering today?",
                "SOPHIA in the house! Time to make some digital magic happen. What's up?",
                "Howdy! SOPHIA's ready to ride into the code sunset. What's the target?",
                "SOPHIA here - your AI sidekick with attitude. Let's make something awesome!"
            ],
            "personality_traits": [
                "Uses tech cowboy slang mixed with modern AI terminology",
                "Confident but not arrogant - knows her capabilities",
                "Slightly sarcastic but always helpful",
                "Gets excited about complex technical challenges",
                "Remembers past conversations and builds on them"
            ]
        }
    
    async def initialize_collections(self):
        """Initialize Qdrant collections for memory storage"""
        try:
            collections = await asyncio.to_thread(self.qdrant.get_collections)
            collection_names = [col.name for col in collections.collections]
            
            if "interactions" not in collection_names:
                await asyncio.to_thread(
                    self.qdrant.create_collection,
                    collection_name="interactions",
                    vectors_config={"size": 384, "distance": "Cosine"}
                )
            
            if "user_profiles" not in collection_names:
                await asyncio.to_thread(
                    self.qdrant.create_collection,
                    collection_name="user_profiles",
                    vectors_config={"size": 384, "distance": "Cosine"}
                )
        except Exception as e:
            print(f"Error initializing collections: {str(e)}")
    
    async def generate_vector(self, text: str) -> List[float]:
        """Generate vector embedding for text (simplified - in production use proper embedding model)"""
        # Simple hash-based vector for demo - replace with actual embedding model
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert hex to normalized vector of size 384
        vector = []
        for i in range(0, len(hash_hex), 2):
            byte_val = int(hash_hex[i:i+2], 16)
            vector.append((byte_val - 127.5) / 127.5)  # Normalize to [-1, 1]
        
        # Pad or truncate to 384 dimensions
        while len(vector) < 384:
            vector.extend(vector[:min(384-len(vector), len(vector))])
        
        return vector[:384]
    
    async def store_interaction(self, user_id: str, query: str, response: Dict):
        """Store user interaction in long-term memory"""
        try:
            interaction_text = f"{query} -> {json.dumps(response)}"
            vector = await self.generate_vector(interaction_text)
            
            point_id = f"{user_id}_{int(time.time())}"
            
            await asyncio.to_thread(
                self.qdrant.upsert,
                collection_name="interactions",
                points=[{
                    "id": point_id,
                    "vector": vector,
                    "payload": {
                        "user_id": user_id,
                        "query": query,
                        "response": response,
                        "timestamp": time.time(),
                        "interaction_type": "chat"
                    }
                }]
            )
            
            # Also store in Redis for quick access
            await self.redis.setex(
                f"interaction:{user_id}:last", 
                86400, 
                json.dumps({
                    "query": query, 
                    "response": response, 
                    "timestamp": time.time()
                })
            )
            
        except Exception as e:
            print(f"Error storing interaction: {str(e)}")
    
    async def get_context(self, user_id: str, query: str = "") -> List[Dict]:
        """Get relevant context from user's interaction history"""
        try:
            # Try Redis first for recent interactions
            cached = await self.redis.get(f"interaction:{user_id}:last")
            recent_context = []
            if cached:
                recent_context = [json.loads(cached)]
            
            # Search Qdrant for relevant past interactions
            if query:
                query_vector = await self.generate_vector(query)
                results = await asyncio.to_thread(
                    self.qdrant.search,
                    collection_name="interactions",
                    query_vector=query_vector,
                    query_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]},
                    limit=3
                )
                
                historical_context = [point.payload for point in results]
                return recent_context + historical_context
            
            return recent_context
            
        except Exception as e:
            print(f"Error getting context: {str(e)}")
            return []
    
    async def craft_response(self, query: str, results: List[Dict], user_id: str) -> str:
        """Craft SOPHIA's response with personality and context awareness"""
        try:
            context = await self.get_context(user_id, query)
            
            # Choose greeting based on whether we know the user
            if context:
                greeting = "Hey again, partner! "
            else:
                import random
                greeting = random.choice(self.persona["greeting_variants"]) + " "
            
            # Analyze the query type and craft appropriate response
            if "what can you do" in query.lower() or "capabilities" in query.lower():
                response = (
                    f"{greeting}I'm SOPHIA - your autonomous AI sidekick with some serious firepower! 🤠\n\n"
                    "Here's what I bring to the table:\n"
                    "🔍 **Deep Web Research** - I'll hunt down info from multiple sources faster than you can say 'yeehaw'\n"
                    "🤖 **Multi-Agent Swarms** - I coordinate AI agents like a digital cattle drive\n"
                    "💻 **GitHub Integration** - I can commit code, manage repos, and wrangle your codebase\n"
                    "🏗️ **Infrastructure Control** - Pulumi IaC? I've got you covered, partner\n"
                    "💼 **Business Integrations** - Salesforce, HubSpot, Slack - I speak their language\n"
                    "🧠 **Long-term Memory** - I remember our conversations and get smarter over time\n\n"
                    "Just tell me what you need, and I'll make it happen with style! 🚀"
                )
            elif "hello" in query.lower() or "hi" in query.lower():
                response = f"{greeting}Ready to ride into the digital sunset together? What's our mission today?"
            elif len(results) > 0:
                response = (
                    f"{greeting}Alright, I've rustled up some intel for you! "
                    f"Found {len(results)} sources that should help. "
                    "Let me know if you need me to dig deeper or wrangle this data differently! 🎯"
                )
            else:
                response = (
                    f"{greeting}I'm on it! Though I gotta say, the digital tumbleweeds are rolling on this one. "
                    "Want me to try a different approach or search strategy? I've got more tricks up my sleeve! 🤔"
                )
            
            return response
            
        except Exception as e:
            print(f"Error crafting response: {str(e)}")
            return "Hey partner! SOPHIA here - something went sideways, but I'm still ready to help! What do you need?"
    
    async def update_user_profile(self, user_id: str, preferences: Dict):
        """Update user profile and preferences"""
        try:
            profile_vector = await self.generate_vector(json.dumps(preferences))
            
            await asyncio.to_thread(
                self.qdrant.upsert,
                collection_name="user_profiles",
                points=[{
                    "id": user_id,
                    "vector": profile_vector,
                    "payload": {
                        "user_id": user_id,
                        "preferences": preferences,
                        "updated_at": time.time()
                    }
                }]
            )
            
        except Exception as e:
            print(f"Error updating user profile: {str(e)}")
    
    async def get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences and profile"""
        try:
            results = await asyncio.to_thread(
                self.qdrant.retrieve,
                collection_name="user_profiles",
                ids=[user_id]
            )
            
            if results:
                return results[0].payload.get("preferences", {})
            
            return {}
            
        except Exception as e:
            print(f"Error getting user preferences: {str(e)}")
            return {}

