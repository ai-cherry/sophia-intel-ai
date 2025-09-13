"""
FastAPI routes for persona agents
Provides RESTful API and WebSocket endpoints for interacting with AI team members
"""
import logging
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from app.agents.personas import (
    PERSONA_REGISTRY,
    ClientHealthAssessment,
    DealAnalysis,
    PerformanceReview,
)
from app.agents.personas.client_health import ClientHealthAgent
from app.agents.personas.sales_coach import SalesCoachAgent
from app.api.auth import get_current_user
from app.swarms.core.task_router import TaskRouter
logger = logging.getLogger(__name__)
# Create router
router = APIRouter(prefix="/api/personas", tags=["personas"])
# Persona Manager class for managing active persona instances
class PersonaManager:
    def __init__(self):
        self.personas = {}
        self.interaction_history = []
    def has_persona(self, persona_id: str) -> bool:
        """Check if a persona is active"""
        return persona_id in self.personas
    def get_persona(self, persona_id: str):
        """Get an active persona instance"""
        return self.personas.get(persona_id)
    async def initialize_persona(self, persona_id: str) -> bool:
        """Initialize a specific persona"""
        try:
            if persona_id == "marcus":
                persona = SalesCoachAgent()
            elif persona_id == "sarah":
                persona = ClientHealthAgent()
            else:
                return False
            await persona.initialize()
            self.personas[persona_id] = persona
            return True
        except Exception as e:
            logger.error(f"Failed to initialize persona {persona_id}: {e}")
            return False
    async def interact_with_persona(
        self, persona_id: str, message: str, context: dict[str, Any]
    ) -> str:
        """Interact with a persona"""
        if not self.has_persona(persona_id):
            await self.initialize_persona(persona_id)
        persona = self.get_persona(persona_id)
        if persona:
            response = await persona.interact(message, context)
            self.interaction_history.append(
                {
                    "persona_id": persona_id,
                    "message": message,
                    "response": response,
                    "timestamp": datetime.now(),
                }
            )
            return response
        return "Persona not available"
    def process_feedback(
        self, persona_id: str, interaction_id: str, rating: int, feedback_text: str
    ) -> bool:
        """Process feedback for a persona interaction"""
        if self.has_persona(persona_id):
            persona = self.get_persona(persona_id)
            # Store feedback in persona's learning system
            persona.learn_from_feedback(
                {
                    "interaction_id": interaction_id,
                    "rating": rating,
                    "feedback": feedback_text,
                    "timestamp": datetime.now(),
                }
            )
            return True
        return False
    def get_health_status(self) -> dict[str, Any]:
        """Get health status of all personas"""
        status = {"all_healthy": True, "personas": {}}
        for persona_id, persona in self.personas.items():
            try:
                persona_status = {
                    "active": True,
                    "name": persona.personality.get("name", "Unknown"),
                    "interactions": persona.conversation_count,
                    "memory_size": len(persona.episodic_memory),
                }
                status["personas"][persona_id] = persona_status
            except Exception as e:
                status["personas"][persona_id] = {"active": False, "error": str(e)}
                status["all_healthy"] = False
        return status
# Initialize persona manager
persona_manager = PersonaManager()
task_router = TaskRouter()
# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
    async def connect(self, websocket: WebSocket, persona_id: str):
        await websocket.accept()
        if persona_id not in self.active_connections:
            self.active_connections[persona_id] = []
        self.active_connections[persona_id].append(websocket)
    def disconnect(self, websocket: WebSocket, persona_id: str):
        if persona_id in self.active_connections:
            self.active_connections[persona_id].remove(websocket)
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    async def broadcast_to_persona(self, message: str, persona_id: str):
        if persona_id in self.active_connections:
            for connection in self.active_connections[persona_id]:
                await connection.send_text(message)
manager = ConnectionManager()
# ============================================================================
# Persona Management Endpoints
# ============================================================================
@router.get("/team")
async def get_ai_team_members():
    """Get all AI team members (persistent personas)"""
    personas = []
    # Add Marcus if available
    if persona_manager.has_persona("marcus"):
        marcus = persona_manager.get_persona("marcus")
        personas.append(
            {
                "id": "marcus",
                "name": marcus.personality["name"],
                "title": marcus.personality["title"],
                "tagline": marcus.personality["tagline"],
                "avatar": "💪",
                "status": "online",
                "stats": marcus.get_stats(),
                "type": "sales_coach",
            }
        )
    # Add Sarah if available
    if persona_manager.has_persona("sarah"):
        sarah = persona_manager.get_persona("sarah")
        personas.append(
            {
                "id": "sarah",
                "name": sarah.personality["name"],
                "title": sarah.personality["title"],
                "tagline": sarah.personality["tagline"],
                "avatar": "🛡️",
                "status": "online",
                "stats": sarah.get_stats(),
                "type": "client_health",
            }
        )
    return {"success": True, "team_members": personas, "total": len(personas)}
@router.get("/persona/{persona_id}")
async def get_persona_details(persona_id: str):
    """Get detailed information about a specific persona"""
    if not persona_manager.has_persona(persona_id):
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")
    persona = persona_manager.get_persona(persona_id)
    return {
        "success": True,
        "persona": {
            "id": persona_id,
            "personality": persona.personality,
            "stats": persona.get_stats(),
            "memory_summary": {
                "episodic_count": len(persona.episodic_memory),
                "semantic_facts": len(persona.semantic_memory),
                "working_context": len(persona.working_memory),
            },
            "learning_metrics": persona.learning_patterns,
            "conversation_count": persona.conversation_count,
        },
    }
@router.post("/persona/{persona_id}/initialize")
async def initialize_persona(persona_id: str):
    """Initialize or reinitialize a persona"""
    try:
        success = await persona_manager.initialize_persona(persona_id)
        if success:
            return {
                "success": True,
                "message": f"Persona {persona_id} initialized successfully",
                "persona_id": persona_id,
            }
        else:
            raise HTTPException(
                status_code=400, detail=f"Failed to initialize persona {persona_id}"
            )
    except Exception as e:
        logger.error(f"Error initializing persona {persona_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# ============================================================================
# Sales Coach Specific Endpoints
# ============================================================================
@router.post("/marcus/coach-deal")
async def coach_deal(request: dict[str, Any]):
    """Get deal coaching from Marcus"""
    if not persona_manager.has_persona("marcus"):
        await persona_manager.initialize_persona("marcus")
    marcus = persona_manager.get_persona("marcus")
    # Get appropriate virtual key for coaching task
    virtual_key, routing_metadata = task_router.route_task(
        {
            "task_type": "sales_coaching",
            "estimated_tokens": 1500,
            "preferred_providers": ["openai", "anthropic"],
        }
    )
    # Create deal analysis
    deal_analysis = DealAnalysis(
        deal_id=request.get("deal_id", "unknown"),
        stage=request.get("stage", "discovery"),
        value=request.get("value", 0),
        probability=request.get("probability", 0.5),
        key_stakeholders=request.get("stakeholders", []),
        competitors=request.get("competitors", []),
        pain_points=request.get("pain_points", []),
        next_steps=request.get("next_steps", []),
        risks=request.get("risks", []),
        rep_name=request.get("rep_name", "Team Member"),
    )
    # Get coaching
    coaching = await marcus.coach_deal(deal_analysis)
    # Get response with personality
    response = await marcus.interact(
        f"I just analyzed the deal: {request.get('deal_name', 'your opportunity')}",
        {"deal_coaching": coaching, "virtual_key": virtual_key},
    )
    return {
        "success": True,
        "coaching": coaching,
        "message": response,
        "routing": routing_metadata,
        "persona": "marcus",
    }
@router.post("/marcus/skill-development")
async def get_skill_development(request: dict[str, Any]):
    """Get personalized skill development plan from Marcus"""
    if not persona_manager.has_persona("marcus"):
        await persona_manager.initialize_persona("marcus")
    marcus = persona_manager.get_persona("marcus")
    rep_id = request.get("rep_id", "unknown")
    skills = request.get("skills", [])
    goals = request.get("goals", [])
    plan = await marcus.create_skill_development_plan(rep_id, skills, goals)
    return {"success": True, "development_plan": plan, "persona": "marcus"}
@router.post("/marcus/performance-review")
async def review_performance(request: dict[str, Any]):
    """Get performance review from Marcus"""
    if not persona_manager.has_persona("marcus"):
        await persona_manager.initialize_persona("marcus")
    marcus = persona_manager.get_persona("marcus")
    review_data = PerformanceReview(
        rep_id=request.get("rep_id"),
        period=request.get("period", "monthly"),
        metrics=request.get("metrics", {}),
        deals_closed=request.get("deals_closed", []),
        deals_lost=request.get("deals_lost", []),
        activities=request.get("activities", {}),
    )
    review = await marcus.review_performance(review_data)
    return {"success": True, "performance_review": review, "persona": "marcus"}
# ============================================================================
# Client Health Specific Endpoints
# ============================================================================
@router.post("/sarah/assess-health")
async def assess_client_health(request: dict[str, Any]):
    """Get client health assessment from Sarah"""
    if not persona_manager.has_persona("sarah"):
        await persona_manager.initialize_persona("sarah")
    sarah = persona_manager.get_persona("sarah")
    # Get appropriate virtual key for analysis
    virtual_key, routing_metadata = task_router.route_task(
        {
            "task_type": "client_analysis",
            "estimated_tokens": 2000,
            "preferred_providers": ["anthropic", "openai"],
        }
    )
    assessment_data = ClientHealthAssessment(
        client_id=request.get("client_id"),
        client_name=request.get("client_name"),
        usage_metrics=request.get("usage_metrics", {}),
        engagement_score=request.get("engagement_score", 0),
        support_tickets=request.get("support_tickets", 0),
        last_contact_days=request.get("last_contact_days", 0),
        contract_value=request.get("contract_value", 0),
        renewal_date=request.get("renewal_date"),
        stakeholders=request.get("stakeholders", []),
    )
    assessment = await sarah.assess_client_health(assessment_data)
    # Get response with personality
    response = await sarah.interact(
        f"I just completed the health assessment for {request.get('client_name', 'your client')}",
        {"assessment": assessment, "virtual_key": virtual_key},
    )
    return {
        "success": True,
        "health_assessment": assessment,
        "message": response,
        "routing": routing_metadata,
        "persona": "sarah",
    }
@router.post("/sarah/predict-churn")
async def predict_churn(request: dict[str, Any]):
    """Get churn prediction from Sarah"""
    if not persona_manager.has_persona("sarah"):
        await persona_manager.initialize_persona("sarah")
    sarah = persona_manager.get_persona("sarah")
    client_id = request.get("client_id")
    assessment_data = request.get("assessment_data", {})
    prediction = await sarah.predict_churn_risk(client_id, assessment_data)
    return {"success": True, "churn_prediction": prediction, "persona": "sarah"}
@router.post("/sarah/success-plan")
async def create_success_plan(request: dict[str, Any]):
    """Get success plan from Sarah"""
    if not persona_manager.has_persona("sarah"):
        await persona_manager.initialize_persona("sarah")
    sarah = persona_manager.get_persona("sarah")
    client_id = request.get("client_id")
    goals = request.get("goals", [])
    timeline = request.get("timeline", "quarterly")
    plan = await sarah.create_success_plan(client_id, goals, timeline)
    return {"success": True, "success_plan": plan, "persona": "sarah"}
# ============================================================================
# Conversation & Interaction Endpoints
# ============================================================================
@router.post("/chat/{persona_id}")
async def chat_with_persona(
    persona_id: str, request: dict[str, Any], current_user=Depends(get_current_user)
):
    """Chat with a specific persona"""
    if not persona_manager.has_persona(persona_id):
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")
    message = request.get("message", "")
    context = request.get("context", {})
    # Add user info to context
    context["user"] = current_user.username if current_user else "anonymous"
    # Route to appropriate model based on conversation type
    task_type = "general_conversation"
    if persona_id == "marcus":
        task_type = "sales_coaching"
    elif persona_id == "sarah":
        task_type = "client_analysis"
    virtual_key, routing_metadata = task_router.route_task(
        {"task_type": task_type, "estimated_tokens": len(message) // 4 + 500}
    )
    context["virtual_key"] = virtual_key
    # Get response
    response = await persona_manager.interact_with_persona(persona_id, message, context)
    return {
        "success": True,
        "response": response,
        "persona_id": persona_id,
        "routing": routing_metadata,
        "timestamp": datetime.now().isoformat(),
    }
@router.websocket("/ws/{persona_id}")
async def websocket_chat(websocket: WebSocket, persona_id: str):
    """WebSocket endpoint for real-time chat with personas"""
    await manager.connect(websocket, persona_id)
    try:
        # Send welcome message
        if persona_manager.has_persona(persona_id):
            persona = persona_manager.get_persona(persona_id)
            welcome = {
                "type": "welcome",
                "message": f"Connected to {persona.personality['name']}",
                "persona": persona_id,
            }
            await websocket.send_json(welcome)
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            context = data.get("context", {})
            # Get response
            if persona_manager.has_persona(persona_id):
                response = await persona_manager.interact_with_persona(
                    persona_id, message, context
                )
                # Send response
                await websocket.send_json(
                    {
                        "type": "response",
                        "message": response,
                        "persona": persona_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            else:
                await websocket.send_json(
                    {"type": "error", "message": f"Persona {persona_id} not available"}
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket, persona_id)
        logger.info(f"WebSocket disconnected for persona {persona_id}")
# ============================================================================
# Learning & Feedback Endpoints
# ============================================================================
@router.post("/feedback/{persona_id}")
async def submit_feedback(persona_id: str, request: dict[str, Any]):
    """Submit feedback for a persona interaction"""
    if not persona_manager.has_persona(persona_id):
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")
    interaction_id = request.get("interaction_id")
    rating = request.get("rating", 5)  # 1-5 scale
    feedback_text = request.get("feedback", "")
    success = persona_manager.process_feedback(
        persona_id, interaction_id, rating, feedback_text
    )
    return {
        "success": success,
        "message": (
            "Feedback processed successfully"
            if success
            else "Failed to process feedback"
        ),
        "persona_id": persona_id,
    }
@router.get("/learning/{persona_id}")
async def get_learning_progress(persona_id: str):
    """Get learning progress for a persona"""
    if not persona_manager.has_persona(persona_id):
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")
    persona = persona_manager.get_persona(persona_id)
    return {
        "success": True,
        "persona_id": persona_id,
        "learning_metrics": {
            "total_interactions": persona.conversation_count,
            "patterns_learned": len(persona.learning_patterns),
            "confidence_scores": persona.pattern_confidence,
            "adaptation_rate": sum(persona.pattern_confidence.values())
            / max(len(persona.pattern_confidence), 1),
        },
    }
# ============================================================================
# Health & Status Endpoints
# ============================================================================
@router.get("/health")
async def health_check():
    """Health check for persona system"""
    health_status = persona_manager.get_health_status()
    return {
        "success": True,
        "status": "healthy" if health_status["all_healthy"] else "degraded",
        "personas": health_status["personas"],
        "timestamp": datetime.now().isoformat(),
    }
@router.get("/stats")
async def get_system_stats():
    """Get overall system statistics"""
    stats = {
        "total_personas": len(PERSONA_REGISTRY.list_personas()),
        "active_personas": len(
            [
                p
                for p in PERSONA_REGISTRY.list_personas()
                if persona_manager.has_persona(p)
            ]
        ),
        "total_interactions": sum(
            persona_manager.get_persona(p).conversation_count
            for p in PERSONA_REGISTRY.list_personas()
            if persona_manager.has_persona(p)
        ),
        "websocket_connections": sum(
            len(conns) for conns in manager.active_connections.values()
        ),
    }
    return {
        "success": True,
        "statistics": stats,
        "timestamp": datetime.now().isoformat(),
    }
# Export router
__all__ = ["router"]
