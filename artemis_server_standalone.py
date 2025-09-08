#!/usr/bin/env python3
"""
Artemis AI Command Center - Standalone Server for Technical AI Operations
Tactical intelligence, code analysis, system operations, and technical problem solving
Now featuring Universal Technical Orchestrator with natural language interface
"""

import logging
import os
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import Artemis Agent Factory
from app.artemis.agent_factory import router as factory_router

# Import the AGNO Universal Technical Orchestrator
from app.artemis.agno_orchestrator import ArtemisAGNOOrchestrator, TechnicalContext
from app.core.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Artemis AI Command Center",
    description="Universal Technical Intelligence Orchestrator with Natural Language Interface",
    version="2.0.0",
)

# Initialize the AGNO Universal Technical Orchestrator
artemis_orchestrator = ArtemisAGNOOrchestrator()
orchestrator_initialized = False

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Artemis Agent Factory router
app.include_router(factory_router)

# Include Research Swarm router
try:
    from app.api.routers.research_swarm import router as research_swarm_router

    app.include_router(research_swarm_router)
    logger.info("✅ Research Swarm router included")
except ImportError as e:
    logger.warning(f"Could not import research swarm router: {e}")


# Pydantic models for API requests
class TechnicalRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    include_voice: bool = False
    repository_context: Optional[dict[str, Any]] = None
    system_context: Optional[dict[str, Any]] = None
    priority_level: str = "normal"
    environment: str = "development"


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    include_voice: bool = False


# Serve the Artemis Command Center dashboard
@app.get("/artemis/command-center.html")
async def get_command_center():
    """Serve the Artemis Command Center dashboard"""
    dashboard_path = "app/artemis/ui/command_center.html"
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        raise HTTPException(status_code=404, detail="Command Center not found")


# Serve static files
try:
    app.mount("/static", StaticFiles(directory="app/artemis/ui"), name="static")
except Exception:
    pass  # Continue if static files can't be mounted


# Startup event to initialize orchestrator
@app.on_event("startup")
async def startup_event():
    global orchestrator_initialized
    logger.info(
        "⛔️ Initializing Artemis AGNO Technical Orchestrator with specialized tactical teams..."
    )
    orchestrator_initialized = await artemis_orchestrator.initialize()
    if orchestrator_initialized:
        logger.info(
            "🚀 Artemis AGNO Orchestrator ready with specialized technical intelligence teams"
        )
    else:
        logger.error("❌ Failed to initialize Artemis AGNO orchestrator")


# Enhanced health check
@app.get("/health")
async def health_check():
    orchestrator_status = (
        await artemis_orchestrator.get_orchestrator_status()
        if orchestrator_initialized
        else {"status": "not_initialized"}
    )
    return {
        "status": "operational" if orchestrator_initialized else "degraded",
        "service": "artemis_command_center",
        "mission": "ready" if orchestrator_initialized else "initializing",
        "orchestrator": orchestrator_status,
        "version": "2.0.0",
    }


# =============================================================================
# UNIVERSAL TECHNICAL ORCHESTRATOR API ENDPOINTS
# =============================================================================


@app.post("/api/artemis/chat")
async def artemis_universal_chat(request: ChatRequest):
    """Universal chat interface for all technical operations"""
    if not orchestrator_initialized:
        raise HTTPException(status_code=503, detail="Artemis orchestrator not initialized")

    try:
        # Create technical context
        context = TechnicalContext(
            user_id=request.user_id,
            session_id=request.session_id or f"tech_session_{hash(request.message) % 10000}",
            include_voice=request.include_voice,
        )

        # Process through universal orchestrator
        response = await artemis_orchestrator.process_technical_request(request.message, context)

        return {
            "success": response.success,
            "response": response.content,
            "command_type": response.command_type,
            "findings": response.findings,
            "recommendations": response.recommendations,
            "action_items": response.action_items,
            "code_snippets": response.code_snippets,
            "voice_audio": response.voice_audio,
            "confidence": response.confidence,
            "execution_time": response.execution_time,
            "timestamp": response.timestamp,
            "metadata": response.metadata,
            "agno_teams_used": getattr(response, "agno_teams_used", []),
            "cross_team_synthesis": getattr(response, "cross_team_synthesis", None),
            "tactical_implications": getattr(response, "tactical_implications", []),
        }

    except Exception as e:
        logger.error(f"Artemis chat error: {str(e)}")
        return {
            "success": False,
            "response": f"Well, shit. Hit a technical snag: {str(e)}. Let me recalibrate and take another tactical approach...",
            "error": str(e),
            "command_type": "error",
        }


@app.post("/api/artemis/technical")
async def artemis_technical_operation(request: TechnicalRequest):
    """Dedicated technical operation endpoint with full context"""
    if not orchestrator_initialized:
        raise HTTPException(status_code=503, detail="Artemis orchestrator not initialized")

    try:
        # Create comprehensive technical context
        context = TechnicalContext(
            user_id=request.user_id,
            session_id=request.session_id or f"tech_ops_{hash(request.message) % 10000}",
            repository_context=request.repository_context,
            system_context=request.system_context,
            include_voice=request.include_voice,
            priority_level=request.priority_level,
            environment=request.environment,
        )

        # Process through universal orchestrator
        response = await artemis_orchestrator.process_technical_request(request.message, context)

        return {
            "success": response.success,
            "response": response.content,
            "command_type": response.command_type,
            "data": response.data,
            "findings": response.findings,
            "recommendations": response.recommendations,
            "action_items": response.action_items,
            "code_snippets": response.code_snippets,
            "voice_audio": response.voice_audio,
            "confidence": response.confidence,
            "execution_time": response.execution_time,
            "timestamp": response.timestamp,
            "metadata": response.metadata,
            "agno_teams_used": getattr(response, "agno_teams_used", []),
            "team_specific_findings": getattr(response, "team_specific_findings", {}),
            "cross_team_synthesis": getattr(response, "cross_team_synthesis", None),
            "tactical_implications": getattr(response, "tactical_implications", []),
        }

    except Exception as e:
        logger.error(f"Artemis technical operation error: {str(e)}")
        return {
            "success": False,
            "response": f"Technical roadblock encountered: {str(e)}. Analyzing alternative approaches...",
            "error": str(e),
            "command_type": "error",
        }


@app.get("/api/artemis/status")
async def artemis_status():
    """Get Artemis orchestrator status and capabilities"""
    if not orchestrator_initialized:
        return {"status": "not_initialized"}

    return await artemis_orchestrator.get_orchestrator_status()


@app.get("/api/artemis/insights")
async def artemis_technical_insights():
    """Get consolidated technical insights summary"""
    if not orchestrator_initialized:
        raise HTTPException(status_code=503, detail="Artemis orchestrator not initialized")

    return await artemis_orchestrator.get_technical_insights_summary()


# Legacy tactical team endpoint for backward compatibility
@app.get("/api/tactical/team")
async def get_tactical_team():
    """Legacy tactical team endpoint - now powered by Universal Orchestrator"""
    return {
        "success": True,
        "message": "Upgraded to Artemis Universal Technical Orchestrator",
        "tactical_agents": [
            {
                "id": "artemis_universal",
                "name": "Artemis Universal Technical Intelligence",
                "title": "Tactical Technical Orchestrator",
                "tagline": "Smart, tactical, and passionate - your complete technical intelligence partner!",
                "avatar": "⛔️",
                "status": "operational",
                "stats": {
                    "technical_operations": "unlimited",
                    "domain_coverage": "complete",
                    "intelligence_level": "tactical",
                    "response_time": "real-time",
                },
                "type": "universal_orchestrator",
                "capabilities": [
                    "Code Analysis & Review",
                    "System Architecture",
                    "Security Auditing",
                    "Performance Optimization",
                    "Infrastructure Management",
                    "Technical Debt Management",
                    "Testing Strategy",
                    "Multi-step Development",
                ],
            }
        ],
        "total": 1,
        "command_status": "fully_operational" if orchestrator_initialized else "initializing",
    }


@app.post("/api/tactical/chat/{agent_id}")
async def tactical_chat_legacy_endpoint(agent_id: str, request: dict):
    """Legacy tactical chat endpoint - now routes to Universal Orchestrator"""
    message = request.get("message", "")

    # Route all requests to universal orchestrator
    if orchestrator_initialized and agent_id in [
        "ares",
        "athena_tactical",
        "apollo_tech",
        "artemis_universal",
        "artemis",
    ]:
        try:
            context = TechnicalContext(
                session_id=f"legacy_tech_session_{agent_id}_{hash(message) % 1000}"
            )

            response = await artemis_orchestrator.process_technical_request(message, context)

            return {
                "success": response.success,
                "response": response.content,
                "agent_id": "artemis_universal",
                "timestamp": response.timestamp,
                "tactical_status": "operational",
                "command_type": response.command_type,
                "findings": (
                    response.findings[:3] if response.findings else []
                ),  # Limit for legacy compatibility
                "recommendations": response.recommendations[:3] if response.recommendations else [],
            }
        except Exception as e:
            logger.error(f"Legacy tactical chat routing error: {str(e)}")
            return {
                "success": False,
                "response": f"Well, shit. Hit a technical snag: {str(e)}. Let me recalibrate and take another tactical approach...",
                "agent_id": agent_id,
                "timestamp": "2024-12-03T22:20:00Z",
                "tactical_status": "error",
                "error": str(e),
            }

    return {"success": False, "error": "Agent not available or orchestrator not initialized"}


@app.get("/api/tactical/status")
async def tactical_status():
    """Artemis command center status"""
    return {
        "success": True,
        "status": "fully_operational",
        "command_center": {
            "ares": {
                "active": True,
                "name": "Ares Rex",
                "operations": 312,
                "status": "combat_ready",
            },
            "athena_tactical": {
                "active": True,
                "name": "Athena Prime",
                "operations": 445,
                "status": "shields_up",
            },
            "apollo_tech": {
                "active": True,
                "name": "Apollo Prime",
                "operations": 156,
                "status": "engineering",
            },
        },
        "mission_status": "ready_for_deployment",
    }


# Main route
@app.get("/")
async def root():
    return {
        "message": "Artemis AI Command Center - Universal Technical Orchestrator",
        "version": "2.0.0",
        "orchestrator": "Artemis Universal Technical Intelligence",
        "personality": "Smart, tactical, and passionate technical partner",
        "capabilities": [
            "Code Analysis & Review Systems",
            "System Architecture Assessment",
            "Security Monitoring & Threat Analysis",
            "Performance Optimization & Analysis",
            "Infrastructure Management",
            "Technical Debt Management",
            "Testing Strategy & Quality Assurance",
            "Multi-step Development Workflows",
            "Technical Agent Factory Operations",
            "Tactical Team Assembly and Deployment",
        ],
        "endpoints": {
            "universal_chat": "/api/artemis/chat",
            "technical_operations": "/api/artemis/technical",
            "status": "/api/artemis/status",
            "insights": "/api/artemis/insights",
            "factory_create_agent": "/api/artemis/factory/create-agent",
            "factory_create_team": "/api/artemis/factory/create-team",
            "factory_templates": "/api/artemis/factory/templates",
            "factory_agents": "/api/artemis/factory/agents",
            "factory_teams": "/api/artemis/factory/teams",
            "factory_metrics": "/api/artemis/factory/metrics",
            "health": "/health",
            "docs": "/docs",
        },
        "status": "operational" if orchestrator_initialized else "initializing",
        "motto": "Through tactical superiority, we achieve technical victory",
    }


if __name__ == "__main__":
    port = int(get_config().get("ARTEMIS_PORT", "8000"))
    logger.info(
        f"""
⛔️ ARTEMIS UNIVERSAL TECHNICAL ORCHESTRATOR + AGENT FACTORY
==========================================================
🚀 Technical API:     http://localhost:{port}/api/artemis/chat
🔧 Tech Operations:   http://localhost:{port}/api/artemis/technical
🏭 Agent Factory:     http://localhost:{port}/api/artemis/factory/
📡 API Documentation: http://localhost:{port}/docs
💚 Health & Status:   http://localhost:{port}/health
🧠 Insights Summary:  http://localhost:{port}/api/artemis/insights

🤖 AGNO Technical Intelligence Teams:
  ⛔️ Artemis - Tactical Technical AGNO Orchestrator
     • Smart, tactical, and passionate personality
     • 4 Specialized AGNO Teams with dedicated agents:
       🔸 Code Analysis Team (5 agents): Review, quality, refactoring
       🔸 Security Team (4 agents): Audits, vulnerabilities, compliance
       🔸 Architecture Team (4 agents): Design, scalability, patterns
       🔸 Performance Team (4 agents): Optimization, monitoring, load testing
     • Cross-team synthesis and tactical implications analysis
     • Multi-team coordination for comprehensive technical intelligence
     • Natural language multi-step development workflows
     • Voice integration with tactical technical personality

🏭 ARTEMIS TECHNICAL AGENT FACTORY:
  ⛔️ Specialized Technical Agents with Tactical Personalities:
     🔸 Code Review Specialist (DEEPSEEK-VK) - Critical analytical precision
     🔸 Security Auditor (ANTHROPIC-VK) - Security paranoid thoroughness
     🔸 Performance Optimizer (GROQ-VK) - Speed obsessed optimization
     🔸 Architecture Critic (OPENAI-VK) - Tactical architectural precision
     🔸 Vulnerability Scanner (MISTRAL-VK) - Threat hunting mentality

  ⚡ Factory Operations:
     • Create Agent:  POST /api/artemis/factory/create-agent
     • Create Team:   POST /api/artemis/factory/create-team
     • List Templates: GET /api/artemis/factory/templates
     • Agent Status:   GET /api/artemis/factory/agents
     • Team Status:    GET /api/artemis/factory/teams
     • Metrics:        GET /api/artemis/factory/metrics

🔧 Domain Coverage:
  • Code Analysis         • System Architecture
  • Security Auditing     • Performance Optimization
  • Infrastructure Mgmt   • Technical Debt
  • Testing Strategy      • Development Workflows
  • Agent Factory Ops     • Tactical Team Assembly

💬 Chat Examples:
  "Review this code for security vulnerabilities and performance issues"
  "Analyze our system architecture and recommend optimizations"
  "Create a code analysis team with security focus"
  "Deploy tactical agents for comprehensive security audit"

🏭 Factory Examples:
  "Create a security auditor agent for vulnerability assessment"
  "Assemble a full technical team for code review and optimization"
  "List all available technical agent templates"
  "Show metrics for all deployed tactical agents"

Mission Status: READY FOR TACTICAL DEPLOYMENT WITH AGENT FACTORY
"""
    )

    uvicorn.run(app, host="0.0.0.0", port=port)
