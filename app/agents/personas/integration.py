"""
Persona Agent Integration Module

Integrates persistent persona agents with the existing Sophia Intel AI agent system,
providing seamless interaction capabilities, data flow, and API endpoints.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from dataclasses import asdict

from fastapi import HTTPException
from pydantic import BaseModel

from . import (
    create_persona_agent,
    get_available_personas,
    PERSONA_REGISTRY,
    BasePersonaAgent
)
from ..models import AgentStatus
from ..agent_factory import AgentFactory


class PersonaInteractionRequest(BaseModel):
    """Request model for persona interactions"""
    persona_type: str
    message: str
    context: Dict[str, Any] = {}
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class PersonaInteractionResponse(BaseModel):
    """Response model for persona interactions"""
    persona_name: str
    response: str
    interaction_type: str
    metadata: Dict[str, Any] = {}
    session_id: Optional[str] = None
    timestamp: datetime


class PersonaHealthCheck(BaseModel):
    """Health check response for persona agents"""
    persona_type: str
    persona_name: str
    status: str
    uptime_seconds: float
    memory_count: int
    learning_patterns_count: int
    last_interaction: Optional[datetime]


class PersonaManager:
    """
    Manages the lifecycle and interactions of persona agents within
    the Sophia Intel AI ecosystem.
    """
    
    def __init__(self):
        self.active_personas: Dict[str, BasePersonaAgent] = {}
        self.interaction_history: List[Dict[str, Any]] = []
        self.startup_time = datetime.utcnow()
        
    async def initialize_personas(self) -> Dict[str, str]:
        """Initialize all persona agents"""
        initialization_results = {}
        
        for persona_type in PERSONA_REGISTRY:
            try:
                persona_agent = create_persona_agent(persona_type)
                await persona_agent.initialize_agent()
                self.active_personas[persona_type] = persona_agent
                
                persona_info = PERSONA_REGISTRY[persona_type]
                initialization_results[persona_type] = f"✅ {persona_info['name']} initialized successfully"
                
            except Exception as e:
                initialization_results[persona_type] = f"❌ Failed to initialize: {str(e)}"
        
        return initialization_results
    
    async def interact_with_persona(
        self, 
        request: PersonaInteractionRequest
    ) -> PersonaInteractionResponse:
        """Handle interaction with a specific persona agent"""
        
        # Validate persona type
        if request.persona_type not in PERSONA_REGISTRY:
            available_types = list(PERSONA_REGISTRY.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Unknown persona type '{request.persona_type}'. Available: {available_types}"
            )
        
        # Get or create persona agent
        if request.persona_type not in self.active_personas:
            persona_agent = create_persona_agent(request.persona_type)
            await persona_agent.initialize_agent()
            self.active_personas[request.persona_type] = persona_agent
        else:
            persona_agent = self.active_personas[request.persona_type]
        
        # Set conversation context
        if request.session_id:
            persona_agent.conversation_id = request.session_id
        
        # Process the interaction
        try:
            interaction_result = await persona_agent.process_interaction(
                user_input=request.message,
                context=request.context
            )
            
            # Record interaction history
            interaction_record = {
                'timestamp': datetime.utcnow(),
                'persona_type': request.persona_type,
                'user_id': request.user_id,
                'session_id': request.session_id,
                'message': request.message,
                'response': interaction_result.get('response', ''),
                'context': request.context,
                'metadata': interaction_result
            }
            self.interaction_history.append(interaction_record)
            
            # Create response
            response = PersonaInteractionResponse(
                persona_name=persona_agent.profile.name,
                response=interaction_result.get('response', ''),
                interaction_type=interaction_result.get('coaching_type', 'general'),
                metadata=interaction_result,
                session_id=request.session_id,
                timestamp=datetime.utcnow()
            )
            
            return response
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing interaction with {persona_agent.profile.name}: {str(e)}"
            )
    
    def get_persona_greeting(self, persona_type: str, user_name: Optional[str] = None) -> str:
        """Get personalized greeting from a specific persona"""
        if persona_type not in self.active_personas:
            return f"Hello! The {persona_type} persona is not currently active."
        
        persona_agent = self.active_personas[persona_type]
        return persona_agent.get_persona_greeting(user_name)
    
    def get_persona_health_status(self, persona_type: str) -> PersonaHealthCheck:
        """Get health status of a specific persona agent"""
        if persona_type not in self.active_personas:
            raise HTTPException(
                status_code=404,
                detail=f"Persona type '{persona_type}' is not active"
            )
        
        persona_agent = self.active_personas[persona_type]
        uptime = (datetime.utcnow() - self.startup_time).total_seconds()
        
        # Get last interaction timestamp
        last_interaction = None
        for record in reversed(self.interaction_history):
            if record['persona_type'] == persona_type:
                last_interaction = record['timestamp']
                break
        
        return PersonaHealthCheck(
            persona_type=persona_type,
            persona_name=persona_agent.profile.name,
            status="active",
            uptime_seconds=uptime,
            memory_count=len(persona_agent.episodic_memory),
            learning_patterns_count=len(persona_agent.learned_patterns),
            last_interaction=last_interaction
        )
    
    def get_all_personas_status(self) -> Dict[str, PersonaHealthCheck]:
        """Get status of all active persona agents"""
        status_dict = {}
        
        for persona_type in self.active_personas:
            try:
                status_dict[persona_type] = self.get_persona_health_status(persona_type)
            except Exception as e:
                # Create error status
                status_dict[persona_type] = PersonaHealthCheck(
                    persona_type=persona_type,
                    persona_name="Unknown",
                    status=f"error: {str(e)}",
                    uptime_seconds=0,
                    memory_count=0,
                    learning_patterns_count=0,
                    last_interaction=None
                )
        
        return status_dict
    
    async def analyze_client_data(
        self, 
        persona_type: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use persona agent to analyze domain-specific data"""
        if persona_type not in self.active_personas:
            raise HTTPException(
                status_code=404,
                detail=f"Persona type '{persona_type}' is not active"
            )
        
        persona_agent = self.active_personas[persona_type]
        
        try:
            analysis_result = await persona_agent.analyze_domain_specific_data(data)
            return {
                'analyst': persona_agent.profile.name,
                'analysis_type': data.get('type', 'general'),
                'timestamp': datetime.utcnow().isoformat(),
                'results': analysis_result
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing data with {persona_agent.profile.name}: {str(e)}"
            )
    
    def provide_feedback_to_persona(
        self, 
        persona_type: str, 
        feedback: Dict[str, Any]
    ) -> Dict[str, str]:
        """Provide feedback to persona agent for learning"""
        if persona_type not in self.active_personas:
            raise HTTPException(
                status_code=404,
                detail=f"Persona type '{persona_type}' is not active"
            )
        
        persona_agent = self.active_personas[persona_type]
        
        try:
            persona_agent.adapt_personality(feedback)
            return {
                'status': 'success',
                'message': f'Feedback provided to {persona_agent.profile.name}',
                'persona': persona_agent.profile.name
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error providing feedback to {persona_agent.profile.name}: {str(e)}"
            )
    
    def get_persona_insights(self, persona_type: str) -> Dict[str, Any]:
        """Get insights and learned patterns from persona agent"""
        if persona_type not in self.active_personas:
            raise HTTPException(
                status_code=404,
                detail=f"Persona type '{persona_type}' is not active"
            )
        
        persona_agent = self.active_personas[persona_type]
        
        return {
            'persona_name': persona_agent.profile.name,
            'agent_state': persona_agent.get_agent_state(),
            'learned_patterns': [
                {
                    'type': pattern.pattern_type,
                    'description': pattern.description,
                    'confidence': pattern.confidence_score,
                    'usage_count': pattern.usage_count,
                    'created': pattern.created_at.isoformat()
                }
                for pattern in persona_agent.learned_patterns
            ],
            'behavioral_adjustments': persona_agent.behavioral_adjustments,
            'success_metrics': persona_agent.success_metrics,
            'active_goals': persona_agent.active_goals
        }
    
    def get_interaction_history(
        self, 
        persona_type: Optional[str] = None, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get interaction history, optionally filtered by persona type"""
        filtered_history = self.interaction_history
        
        if persona_type:
            filtered_history = [
                record for record in filtered_history 
                if record['persona_type'] == persona_type
            ]
        
        # Sort by timestamp (most recent first) and apply limit
        sorted_history = sorted(
            filtered_history, 
            key=lambda x: x['timestamp'], 
            reverse=True
        )
        
        return sorted_history[:limit]
    
    async def shutdown_personas(self) -> Dict[str, str]:
        """Gracefully shutdown all persona agents"""
        shutdown_results = {}
        
        for persona_type, persona_agent in self.active_personas.items():
            try:
                # Save final state or perform cleanup if needed
                agent_state = persona_agent.get_agent_state()
                
                # In a real implementation, you might save state to database here
                
                shutdown_results[persona_type] = f"✅ {persona_agent.profile.name} shutdown successfully"
                
            except Exception as e:
                shutdown_results[persona_type] = f"❌ Error during shutdown: {str(e)}"
        
        # Clear active personas
        self.active_personas.clear()
        
        return shutdown_results


# Integration with existing Agent Factory
class PersonaAgentFactory:
    """
    Factory extension for creating and managing persona agents within
    the existing agent factory system.
    """
    
    @staticmethod
    def integrate_persona_with_agent_factory(
        agent_factory: AgentFactory,
        persona_manager: PersonaManager
    ) -> None:
        """
        Integrate persona agents with the existing agent factory system.
        
        This allows persona agents to be managed alongside other agents
        in the Sophia Intel AI ecosystem.
        """
        
        # Add persona agents as special agent types in the factory
        for persona_type, persona_info in PERSONA_REGISTRY.items():
            # Register persona as an agent type
            agent_factory.register_agent_type(
                agent_type=f"persona_{persona_type}",
                description=persona_info["description"],
                capabilities=persona_info["expertise"],
                status=AgentStatus.ACTIVE
            )
    
    @staticmethod
    def create_persona_agent_blueprint(persona_type: str) -> Dict[str, Any]:
        """
        Create an agent blueprint for a persona agent that can be used
        with the existing agent factory system.
        """
        if persona_type not in PERSONA_REGISTRY:
            raise ValueError(f"Unknown persona type: {persona_type}")
        
        persona_info = PERSONA_REGISTRY[persona_type]
        
        return {
            'name': f"Persona Agent - {persona_info['name']}",
            'type': f"persona_{persona_type}",
            'description': persona_info['description'],
            'capabilities': persona_info['expertise'],
            'personality': persona_info['personality'],
            'configuration': {
                'persona_type': persona_type,
                'memory_capacity': 15000 if persona_type == 'sales_coach' else 20000,
                'learning_enabled': True,
                'adaptive_personality': True
            },
            'integration_points': [
                'crm_data_access',
                'client_health_monitoring', 
                'interaction_logging',
                'feedback_collection'
            ]
        }


# Global persona manager instance
persona_manager = PersonaManager()


# Convenience functions for easy integration
async def get_sales_coach_advice(
    message: str, 
    context: Dict[str, Any] = None,
    user_id: str = None
) -> str:
    """Quick access to sales coach advice"""
    request = PersonaInteractionRequest(
        persona_type="sales_coach",
        message=message,
        context=context or {},
        user_id=user_id
    )
    
    response = await persona_manager.interact_with_persona(request)
    return response.response


async def get_client_health_insights(
    client_data: Dict[str, Any],
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Quick access to client health analysis"""
    analysis_result = await persona_manager.analyze_client_data(
        persona_type="client_health",
        data=client_data
    )
    
    return analysis_result


# Export main integration components
__all__ = [
    'PersonaManager',
    'PersonaAgentFactory',
    'PersonaInteractionRequest',
    'PersonaInteractionResponse',
    'PersonaHealthCheck',
    'persona_manager',
    'get_sales_coach_advice',
    'get_client_health_insights'
]