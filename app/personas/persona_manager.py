"""
Unified Persona Manager
Integrates Sophia's business intelligence personas with specific agent personas like Marcus and Sarah
Handles proper JSON serialization to prevent escaping issues
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import aiohttp
import os
from pathlib import Path

# Import existing persona system
try:
    from app.orchestrators.persona_system import SophiaPersonaSystem, PersonaContext, PersonaResponse
except ImportError:
    # Fallback if import fails
    logging.warning("Could not import SophiaPersonaSystem")
    SophiaPersonaSystem = None

logger = logging.getLogger(__name__)

@dataclass
class AgentPersona:
    """Represents a specific agent persona like Marcus or Sarah"""
    id: str
    name: str
    title: str
    tagline: str
    avatar: str
    status: str
    personality_type: str
    voice_id: Optional[str] = None
    stats: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "tagline": self.tagline,
            "avatar": self.avatar,
            "status": self.status,
            "personality_type": self.personality_type,
            "voice_id": self.voice_id,
            "stats": self.stats or {}
        }

@dataclass 
class ChatResponse:
    """Standardized chat response format"""
    success: bool
    response: str
    persona_id: str
    persona_name: str
    timestamp: str
    metadata: Dict[str, Any] = None
    audio_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper JSON serialization"""
        return {
            "success": self.success,
            "response": self.response,
            "persona_id": self.persona_id,
            "persona_name": self.persona_name,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {},
            "audio_url": self.audio_url
        }

class PersonaManager:
    """Unified manager for all persona types"""
    
    def __init__(self, elevenlabs_api_key: Optional[str] = None):
        self.elevenlabs_api_key = elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
        self.sophia_system = SophiaPersonaSystem() if SophiaPersonaSystem else None
        
        # Initialize agent personas
        self.agent_personas = self._initialize_agent_personas()
        
        # Voice mappings
        self.voice_mappings = {
            "marcus": "pNInz6obpgDQGcFmaJgB",  # Example ElevenLabs voice ID
            "sarah": "Xb7hH8MSUJpSbSDYk0k2"   # Example ElevenLabs voice ID
        }
        
        logger.info(f"PersonaManager initialized with {len(self.agent_personas)} agent personas")
    
    def _initialize_agent_personas(self) -> Dict[str, AgentPersona]:
        """Initialize specific agent personas"""
        return {
            "marcus": AgentPersona(
                id="marcus",
                name="Marcus 'The Catalyst' Rodriguez",
                title="Sales Coach & Performance Catalyst",
                tagline="Every 'no' is one step closer to your breakthrough 'yes'!",
                avatar="💪",
                status="online",
                personality_type="sales_coach",
                voice_id="pNInz6obpgDQGcFmaJgB",
                stats={
                    "conversations": 156,
                    "deals_coached": 47,
                    "win_rate_improvement": "23%",
                    "client_satisfaction": 4.8
                }
            ),
            "sarah": AgentPersona(
                id="sarah", 
                name="Dr. Sarah 'The Guardian' Chen",
                title="Client Success Strategist & Health Guardian",
                tagline="Your success is my mission - let's build something amazing together!",
                avatar="🛡️",
                status="online",
                personality_type="client_health",
                voice_id="Xb7hH8MSUJpSbSDYk0k2",
                stats={
                    "conversations": 203,
                    "health_assessments": 89,
                    "churn_prevented": 12,
                    "client_satisfaction": 4.9
                }
            )
        }
    
    async def get_team_members(self) -> Dict[str, Any]:
        """Get all team members with proper JSON structure"""
        try:
            team_members = []
            
            # Add agent personas
            for persona in self.agent_personas.values():
                team_members.append(persona.to_dict())
            
            # Add Sophia business intelligence personas if available
            if self.sophia_system:
                sophia_personas = await self.sophia_system.list_available_personas()
                for persona_info in sophia_personas:
                    team_members.append({
                        "id": persona_info["name"].lower().replace(" ", "_"),
                        "name": persona_info["config"]["name"],
                        "title": f"AI {persona_info['config']['style'].replace('_', ' ').title()}",
                        "tagline": f"Specialized in {persona_info['config']['style']}",
                        "avatar": persona_info["config"]["emoji"],
                        "status": "online", 
                        "personality_type": persona_info["name"],
                        "stats": {
                            "conversations": 0,
                            "specialization": persona_info["config"]["domains"]
                        }
                    })
            
            return {
                "success": True,
                "team_members": team_members,
                "total": len(team_members)
            }
        except Exception as e:
            logger.error(f"Error getting team members: {e}")
            return {
                "success": False,
                "error": str(e),
                "team_members": [],
                "total": 0
            }
    
    async def chat_with_persona(self, persona_id: str, message: str, context: Optional[Dict] = None) -> ChatResponse:
        """Chat with a specific persona"""
        try:
            # Check if it's an agent persona
            if persona_id in self.agent_personas:
                return await self._chat_with_agent_persona(persona_id, message, context)
            
            # Check if it's a Sophia business intelligence persona
            elif self.sophia_system:
                return await self._chat_with_sophia_persona(persona_id, message, context)
            
            else:
                return ChatResponse(
                    success=False,
                    response="Persona not found",
                    persona_id=persona_id,
                    persona_name="Unknown",
                    timestamp=datetime.now().isoformat()
                )
        
        except Exception as e:
            logger.error(f"Error in persona chat: {e}")
            return ChatResponse(
                success=False,
                response=f"Error processing request: {str(e)}",
                persona_id=persona_id,
                persona_name="Error",
                timestamp=datetime.now().isoformat()
            )
    
    async def _chat_with_agent_persona(self, persona_id: str, message: str, context: Optional[Dict] = None) -> ChatResponse:
        """Handle chat with agent personas (Marcus, Sarah)"""
        persona = self.agent_personas[persona_id]
        
        # Generate personality-specific response
        if persona_id == "marcus":
            response_text = await self._generate_marcus_response(message, context)
        elif persona_id == "sarah":
            response_text = await self._generate_sarah_response(message, context)
        else:
            response_text = f"Hello! I'm {persona.name}. How can I help you today?"
        
        # Generate voice if available
        audio_url = None
        if self.elevenlabs_api_key and persona.voice_id:
            audio_url = await self._generate_voice(response_text, persona.voice_id)
        
        return ChatResponse(
            success=True,
            response=response_text,
            persona_id=persona_id,
            persona_name=persona.name,
            timestamp=datetime.now().isoformat(),
            audio_url=audio_url,
            metadata={
                "personality_type": persona.personality_type,
                "voice_enabled": audio_url is not None
            }
        )
    
    async def _chat_with_sophia_persona(self, persona_id: str, message: str, context: Optional[Dict] = None) -> ChatResponse:
        """Handle chat with Sophia business intelligence personas"""
        if not self.sophia_system:
            raise ValueError("Sophia persona system not available")
        
        # Create context for Sophia system
        persona_context = PersonaContext(
            query_type=context.get("query_type", "general") if context else "general",
            domain=context.get("domain", "business") if context else "business",
            urgency=context.get("urgency", "normal") if context else "normal",
            user_role=context.get("user_role", "user") if context else "user",
            conversation_history=context.get("history", []) if context else []
        )
        
        # Generate response
        persona_response = await self.sophia_system.generate_response(message, persona_context)
        
        return ChatResponse(
            success=True,
            response=persona_response.content,
            persona_id=persona_id,
            persona_name=persona_response.persona_used,
            timestamp=datetime.now().isoformat(),
            metadata={
                "confidence": persona_response.confidence,
                "suggested_actions": persona_response.suggested_actions,
                "persona_metadata": persona_response.metadata
            }
        )
    
    async def _generate_marcus_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate Marcus-style response"""
        base_responses = [
            f"Hey there, champion! I hear you about '{message[:50]}...' Let me tell you, every challenge is just a breakthrough waiting to happen!",
            f"Absolutely love the energy in your message about '{message[:50]}...' - this is exactly the kind of opportunity that separates winners from everyone else!",
            f"I'm fired up about what you're sharing regarding '{message[:50]}...' - let's turn this into your next big win!"
        ]
        
        import random
        base = random.choice(base_responses)
        
        coaching_advice = [
            "Here's what I'm thinking - we need to dig deeper into the value proposition and really understand what's driving their hesitation.",
            "The key is to position this as the solution they've been searching for, not just another option on their list.",
            "Let's focus on the transformation they'll experience and paint that picture crystal clear for them.",
            "Remember, every objection is just a request for more information - they're still engaged and that's what matters!"
        ]
        
        closer = [
            "Let's turn this around and make it happen! 💪",
            "Together, we're going to crush this! 🚀",
            "I believe in you - now let's show them what you're made of! ⭐"
        ]
        
        return f"{base} {random.choice(coaching_advice)} {random.choice(closer)}"
    
    async def _generate_sarah_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate Sarah-style response"""
        base_responses = [
            f"Thank you for reaching out about '{message[:50]}...' I'm here to help ensure the best possible outcome for your client relationship.",
            f"I appreciate you sharing this about '{message[:50]}...' - proactive communication like this is exactly what builds strong partnerships.",
            f"What you've mentioned regarding '{message[:50]}...' is exactly the kind of situation where strategic intervention can make all the difference."
        ]
        
        import random
        base = random.choice(base_responses)
        
        strategic_advice = [
            "Let me analyze what you've shared - it sounds like we need to take a proactive approach to address their concerns and strengthen the partnership.",
            "Based on my assessment, I recommend we schedule a health check call to understand their current needs and identify opportunities.",
            "This is a perfect opportunity to demonstrate our commitment to their success and deepen the relationship.",
            "I see several pathways here to not only resolve this but to actually strengthen the overall engagement."
        ]
        
        closer = [
            "Together, we can turn this into a success story! 🛡️",
            "Let's build something amazing together! ✨", 
            "I'm confident we can navigate this successfully! 🌟"
        ]
        
        return f"{base} {random.choice(strategic_advice)} {random.choice(closer)}"
    
    async def _generate_voice(self, text: str, voice_id: str) -> Optional[str]:
        """Generate voice audio using ElevenLabs"""
        if not self.elevenlabs_api_key:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.elevenlabs_api_key
                }
                data = {
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.5
                    }
                }
                
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        # Save audio file and return URL
                        audio_data = await response.read()
                        filename = f"voice_{voice_id}_{datetime.now().timestamp()}.mp3"
                        filepath = Path(f"/tmp/{filename}")
                        
                        with open(filepath, "wb") as f:
                            f.write(audio_data)
                        
                        return f"/api/voice/{filename}"
                    else:
                        logger.warning(f"ElevenLabs API error: {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"Error generating voice: {e}")
            return None
    
    async def get_persona_health(self) -> Dict[str, Any]:
        """Get health status of all personas"""
        try:
            health_status = {
                "success": True,
                "status": "healthy",
                "personas": {}
            }
            
            # Check agent personas
            for persona_id, persona in self.agent_personas.items():
                health_status["personas"][persona_id] = {
                    "active": persona.status == "online",
                    "name": persona.name,
                    "interactions": persona.stats.get("conversations", 0) if persona.stats else 0,
                    "voice_available": bool(self.elevenlabs_api_key and persona.voice_id)
                }
            
            # Check Sophia personas if available
            if self.sophia_system:
                sophia_personas = await self.sophia_system.list_available_personas()
                for persona_info in sophia_personas:
                    persona_key = persona_info["name"].lower().replace(" ", "_")
                    health_status["personas"][persona_key] = {
                        "active": True,
                        "name": persona_info["config"]["name"],
                        "interactions": 0,
                        "domains": persona_info["config"]["domains"]
                    }
            
            return health_status
        
        except Exception as e:
            logger.error(f"Error getting persona health: {e}")
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "personas": {}
            }

    def serialize_response(self, data: Any) -> str:
        """Properly serialize response data to prevent JSON escaping issues"""
        try:
            # Convert dataclasses and custom objects to dictionaries
            if hasattr(data, 'to_dict'):
                data = data.to_dict()
            elif hasattr(data, '__dict__'):
                data = asdict(data) if hasattr(data, '__dataclass_fields__') else data.__dict__
            
            # Use json.dumps with ensure_ascii=False to prevent escaping
            return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        
        except Exception as e:
            logger.error(f"JSON serialization error: {e}")
            return json.dumps({"success": False, "error": "Serialization error"})

# Global persona manager instance
_persona_manager = None

def get_persona_manager() -> PersonaManager:
    """Get or create global persona manager instance"""
    global _persona_manager
    if _persona_manager is None:
        _persona_manager = PersonaManager()
    return _persona_manager