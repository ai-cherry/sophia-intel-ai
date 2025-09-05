#!/usr/bin/env python3
"""
Sophia Intelligence Platform - Standalone Server for Business Wisdom AI
Sales intelligence, client success, business strategy, and market wisdom
Now featuring Universal Business Orchestrator with natural language interface
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

from app.core.config import get_config

# Import Slack integration
from app.integrations.slack_integration import (
    SlackClient,
    SlackIntegrationError,
    get_slack_channels,
    send_slack_message,
    test_slack_connection,
)

# Import Sophia Business Agent Factory
from app.sophia.agent_factory import sophia_business_factory

# Import the AGNO Universal Business Orchestrator
from app.sophia.agno_orchestrator import BusinessContext, SophiaAGNOOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sophia Intelligence Platform",
    description="Universal Business Intelligence Orchestrator with Natural Language Interface",
    version="2.0.0",
)

# Initialize the AGNO Universal Business Orchestrator
sophia_orchestrator = SophiaAGNOOrchestrator()
orchestrator_initialized = False

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests
class BusinessRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    include_voice: bool = False
    company_context: Optional[dict[str, Any]] = None
    priority_level: str = "normal"


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    include_voice: bool = False


class AgentCreateRequest(BaseModel):
    template_id: str
    custom_config: Optional[dict[str, Any]] = None


class TeamCreateRequest(BaseModel):
    template_id: str
    custom_config: Optional[dict[str, Any]] = None


class TaskExecuteRequest(BaseModel):
    task: str
    context: Optional[dict[str, Any]] = None


# Slack API request models
class SlackMessageRequest(BaseModel):
    channel: str
    text: str
    thread_ts: Optional[str] = None
    blocks: Optional[list[dict[str, Any]]] = None
    attachments: Optional[list[dict[str, Any]]] = None


class SlackUpdateMessageRequest(BaseModel):
    channel: str
    ts: str
    text: str
    blocks: Optional[list[dict[str, Any]]] = None
    attachments: Optional[list[dict[str, Any]]] = None


class SlackDeleteMessageRequest(BaseModel):
    channel: str
    ts: str


# Serve the Agent Factory dashboard
@app.get("/agents/factory-dashboard.html")
async def get_dashboard():
    """Serve the Agent Factory dashboard"""
    dashboard_path = "app/agents/ui/agent_factory_dashboard.html"
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")


# Serve the Sophia Business Factory UI
@app.get("/sophia/factory")
async def get_sophia_factory_ui():
    """Serve the Sophia Business Factory UI"""
    factory_ui_path = "sophia_business_factory_ui.html"
    if os.path.exists(factory_ui_path):
        return FileResponse(factory_ui_path)
    else:
        raise HTTPException(status_code=404, detail="Factory UI not found")


# Serve static files
try:
    app.mount("/static", StaticFiles(directory="app/agents/ui"), name="static")
except Exception:
    pass  # Continue if static files can't be mounted


# Startup event to initialize orchestrator
@app.on_event("startup")
async def startup_event():
    global orchestrator_initialized
    logger.info(
        "🚀 Initializing Sophia AGNO Business Orchestrator with specialized intelligence teams..."
    )
    orchestrator_initialized = await sophia_orchestrator.initialize()
    if orchestrator_initialized:
        logger.info("💎 Sophia AGNO Orchestrator ready with specialized business intelligence teams")
    else:
        logger.error("❌ Failed to initialize Sophia AGNO orchestrator")


# Enhanced health check
@app.get("/health")
async def health_check():
    orchestrator_status = (
        await sophia_orchestrator.get_orchestrator_status()
        if orchestrator_initialized
        else {"status": "not_initialized"}
    )
    return {
        "status": "healthy" if orchestrator_initialized else "degraded",
        "service": "sophia_intelligence_platform",
        "orchestrator": orchestrator_status,
        "version": "2.0.0",
    }


# =============================================================================
# UNIVERSAL BUSINESS ORCHESTRATOR API ENDPOINTS
# =============================================================================


@app.post("/api/sophia/chat")
async def sophia_universal_chat(request: ChatRequest):
    """Universal chat interface for all business operations"""
    if not orchestrator_initialized:
        raise HTTPException(status_code=503, detail="Sophia orchestrator not initialized")

    try:
        # Create business context
        context = BusinessContext(
            user_id=request.user_id,
            session_id=request.session_id or f"session_{hash(request.message) % 10000}",
            include_voice=request.include_voice,
        )

        # Process through universal orchestrator
        response = await sophia_orchestrator.process_business_request(request.message, context)

        return {
            "success": response.success,
            "response": response.content,
            "command_type": response.command_type,
            "insights": response.insights,
            "recommendations": response.recommendations,
            "next_actions": response.next_actions,
            "voice_audio": response.voice_audio,
            "confidence": response.confidence,
            "execution_time": response.execution_time,
            "timestamp": response.timestamp,
            "metadata": response.metadata,
            "agno_teams_used": getattr(response, "agno_teams_used", []),
            "cross_team_synthesis": getattr(response, "cross_team_synthesis", None),
            "strategic_implications": getattr(response, "strategic_implications", []),
        }

    except Exception as e:
        logger.error(f"Sophia chat error: {str(e)}")
        return {
            "success": False,
            "response": f"I encountered a strategic challenge: {str(e)}. Let me recalibrate and try a different approach.",
            "error": str(e),
            "command_type": "error",
        }


@app.post("/api/sophia/business")
async def sophia_business_operation(request: BusinessRequest):
    """Dedicated business operation endpoint with full context"""
    if not orchestrator_initialized:
        raise HTTPException(status_code=503, detail="Sophia orchestrator not initialized")

    try:
        # Create comprehensive business context
        context = BusinessContext(
            user_id=request.user_id,
            session_id=request.session_id or f"biz_session_{hash(request.message) % 10000}",
            company_context=request.company_context,
            include_voice=request.include_voice,
            priority_level=request.priority_level,
        )

        # Process through universal orchestrator
        response = await sophia_orchestrator.process_business_request(request.message, context)

        return {
            "success": response.success,
            "response": response.content,
            "command_type": response.command_type,
            "data": response.data,
            "insights": response.insights,
            "recommendations": response.recommendations,
            "next_actions": response.next_actions,
            "voice_audio": response.voice_audio,
            "confidence": response.confidence,
            "execution_time": response.execution_time,
            "timestamp": response.timestamp,
            "metadata": response.metadata,
            "agno_teams_used": getattr(response, "agno_teams_used", []),
            "team_specific_insights": getattr(response, "team_specific_insights", {}),
            "cross_team_synthesis": getattr(response, "cross_team_synthesis", None),
            "strategic_implications": getattr(response, "strategic_implications", []),
        }

    except Exception as e:
        logger.error(f"Sophia business operation error: {str(e)}")
        return {
            "success": False,
            "response": f"Strategic roadblock encountered: {str(e)}. Analyzing alternative approaches...",
            "error": str(e),
            "command_type": "error",
        }


@app.get("/api/sophia/status")
async def sophia_status():
    """Get Sophia orchestrator status and capabilities"""
    if not orchestrator_initialized:
        return {"status": "not_initialized"}

    return await sophia_orchestrator.get_orchestrator_status()


@app.get("/api/sophia/insights")
async def sophia_business_insights():
    """Get consolidated business insights summary"""
    if not orchestrator_initialized:
        raise HTTPException(status_code=503, detail="Sophia orchestrator not initialized")

    return await sophia_orchestrator.get_business_insights_summary()


# Slack Integration Endpoints
@app.get("/api/slack/status")
async def slack_integration_status():
    """Get Slack integration status and test connection"""
    try:
        result = await test_slack_connection()
        return result
    except Exception as e:
        logger.error(f"Slack status check error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.post("/api/slack/send-message")
async def slack_send_message(request: SlackMessageRequest):
    """Send a message to a Slack channel"""
    try:
        result = await send_slack_message(
            channel=request.channel,
            text=request.text,
            thread_ts=request.thread_ts,
            blocks=request.blocks,
            attachments=request.attachments,
        )
        return result
    except Exception as e:
        logger.error(f"Slack send message error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.post("/api/slack/update-message")
async def slack_update_message(request: SlackUpdateMessageRequest):
    """Update an existing Slack message"""
    try:
        client = SlackClient()
        result = await client.update_message(
            channel=request.channel,
            ts=request.ts,
            text=request.text,
            blocks=request.blocks,
            attachments=request.attachments,
        )
        return result
    except SlackIntegrationError as e:
        logger.error(f"Slack update message error: {str(e)}")
        return {"success": False, "error": str(e), "error_code": e.error_code}
    except Exception as e:
        logger.error(f"Slack update message error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.post("/api/slack/delete-message")
async def slack_delete_message(request: SlackDeleteMessageRequest):
    """Delete a Slack message"""
    try:
        client = SlackClient()
        result = await client.delete_message(channel=request.channel, ts=request.ts)
        return result
    except SlackIntegrationError as e:
        logger.error(f"Slack delete message error: {str(e)}")
        return {"success": False, "error": str(e), "error_code": e.error_code}
    except Exception as e:
        logger.error(f"Slack delete message error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.get("/api/slack/channels")
async def slack_list_channels():
    """List all Slack channels in the workspace"""
    try:
        result = await get_slack_channels()
        return result
    except Exception as e:
        logger.error(f"Slack list channels error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.get("/api/slack/channel/{channel_id}")
async def slack_get_channel_info(channel_id: str):
    """Get information about a specific Slack channel"""
    try:
        client = SlackClient()
        result = await client.get_channel_info(channel_id)
        return result
    except SlackIntegrationError as e:
        logger.error(f"Slack get channel info error: {str(e)}")
        return {"success": False, "error": str(e), "error_code": e.error_code}
    except Exception as e:
        logger.error(f"Slack get channel info error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.get("/api/slack/users")
async def slack_list_users():
    """List all users in the Slack workspace"""
    try:
        client = SlackClient()
        result = await client.list_users()
        return result
    except SlackIntegrationError as e:
        logger.error(f"Slack list users error: {str(e)}")
        return {"success": False, "error": str(e), "error_code": e.error_code}
    except Exception as e:
        logger.error(f"Slack list users error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.get("/api/slack/user/{user_id}")
async def slack_get_user_info(user_id: str):
    """Get information about a specific Slack user"""
    try:
        client = SlackClient()
        result = await client.get_user_info(user_id)
        return result
    except SlackIntegrationError as e:
        logger.error(f"Slack get user info error: {str(e)}")
        return {"success": False, "error": str(e), "error_code": e.error_code}
    except Exception as e:
        logger.error(f"Slack get user info error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.get("/api/slack/history/{channel_id}")
async def slack_get_conversation_history(
    channel_id: str, limit: int = 100, oldest: Optional[str] = None, latest: Optional[str] = None
):
    """Get conversation history from a Slack channel"""
    try:
        client = SlackClient()
        result = await client.get_conversation_history(
            channel=channel_id, limit=limit, oldest=oldest, latest=latest
        )
        return result
    except SlackIntegrationError as e:
        logger.error(f"Slack get history error: {str(e)}")
        return {"success": False, "error": str(e), "error_code": e.error_code}
    except Exception as e:
        logger.error(f"Slack get history error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.post("/api/slack/join-channel/{channel_id}")
async def slack_join_channel(channel_id: str):
    """Join a Slack channel"""
    try:
        client = SlackClient()
        result = await client.join_channel(channel_id)
        return result
    except SlackIntegrationError as e:
        logger.error(f"Slack join channel error: {str(e)}")
        return {"success": False, "error": str(e), "error_code": e.error_code}
    except Exception as e:
        logger.error(f"Slack join channel error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.post("/api/slack/leave-channel/{channel_id}")
async def slack_leave_channel(channel_id: str):
    """Leave a Slack channel"""
    try:
        client = SlackClient()
        result = await client.leave_channel(channel_id)
        return result
    except SlackIntegrationError as e:
        logger.error(f"Slack leave channel error: {str(e)}")
        return {"success": False, "error": str(e), "error_code": e.error_code}
    except Exception as e:
        logger.error(f"Slack leave channel error: {str(e)}")
        return {"success": False, "error": str(e)}


# Legacy persona endpoints for backward compatibility
@app.get("/api/personas/team")
async def get_team_mock():
    """Legacy team endpoint - now powered by Universal Orchestrator"""
    return {
        "success": True,
        "message": "Upgraded to Sophia Universal Business Orchestrator",
        "team_members": [
            {
                "id": "sophia_universal",
                "name": "Sophia Universal Business Intelligence",
                "title": "Strategic Business Orchestrator",
                "tagline": "Smart, strategic, and savvy - your complete business intelligence partner!",
                "avatar": "💎",
                "status": "online",
                "stats": {
                    "business_operations": "unlimited",
                    "domain_coverage": "complete",
                    "intelligence_level": "strategic",
                    "response_time": "real-time",
                },
                "type": "universal_orchestrator",
                "capabilities": [
                    "Sales Intelligence",
                    "Pipeline Management",
                    "Client Success",
                    "Market Research",
                    "Competitive Intelligence",
                    "Business Analytics",
                    "Strategic Planning",
                    "Multi-step Workflows",
                ],
            }
        ],
        "total": 1,
        "orchestrator_status": "active" if orchestrator_initialized else "initializing",
    }


@app.post("/api/personas/chat/{persona_id}")
async def chat_legacy_endpoint(persona_id: str, request: dict):
    """Legacy chat endpoint - now routes to Universal Orchestrator"""
    message = request.get("message", "")

    # Route all requests to universal orchestrator
    if orchestrator_initialized and persona_id in [
        "apollo",
        "athena",
        "sophia_universal",
        "sophia",
    ]:
        try:
            context = BusinessContext(
                session_id=f"legacy_session_{persona_id}_{hash(message) % 1000}"
            )

            response = await sophia_orchestrator.process_business_request(message, context)

            return {
                "success": response.success,
                "response": response.content,
                "persona_id": "sophia_universal",
                "timestamp": response.timestamp,
                "command_type": response.command_type,
                "insights": response.insights[:3]
                if response.insights
                else [],  # Limit for legacy compatibility
                "recommendations": response.recommendations[:3] if response.recommendations else [],
            }
        except Exception as e:
            logger.error(f"Legacy chat routing error: {str(e)}")
            return {
                "success": False,
                "response": f"I encountered a strategic challenge: {str(e)}. Let me recalibrate...",
                "persona_id": persona_id,
                "timestamp": "2024-12-03T22:20:00Z",
                "error": str(e),
            }

    return {"success": False, "error": "Persona not available or orchestrator not initialized"}


# =============================================================================
# SOPHIA BUSINESS AGENT FACTORY API ENDPOINTS
# =============================================================================


@app.get("/api/sophia/factory/templates")
async def get_factory_templates():
    """Get all available business agent and team templates"""
    try:
        templates = sophia_business_factory.get_business_templates()
        return {
            "success": True,
            "templates": templates,
            "message": "Business templates retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get factory templates: {e}")
        return {"success": False, "error": str(e), "message": "Failed to retrieve templates"}


@app.post("/api/sophia/factory/create-agent")
async def create_business_agent(request: AgentCreateRequest):
    """Create a business agent from template"""
    try:
        agent_id = await sophia_business_factory.create_business_agent(
            template_id=request.template_id, custom_config=request.custom_config
        )

        return {
            "success": True,
            "agent_id": agent_id,
            "template_id": request.template_id,
            "message": "Business agent created successfully",
            "endpoints": {
                "execute": f"/api/sophia/factory/execute/{agent_id}",
                "status": f"/api/sophia/factory/agents/{agent_id}",
            },
        }
    except Exception as e:
        logger.error(f"Failed to create business agent: {e}")
        return {"success": False, "error": str(e), "message": "Failed to create business agent"}


@app.post("/api/sophia/factory/create-team")
async def create_business_team(request: TeamCreateRequest):
    """Create a business team from template"""
    try:
        team_id = await sophia_business_factory.create_business_team(
            template_id=request.template_id, custom_config=request.custom_config
        )

        return {
            "success": True,
            "team_id": team_id,
            "template_id": request.template_id,
            "message": "Business team created successfully",
            "endpoints": {
                "execute": f"/api/sophia/factory/execute/{team_id}",
                "status": f"/api/sophia/factory/teams/{team_id}",
            },
        }
    except Exception as e:
        logger.error(f"Failed to create business team: {e}")
        return {"success": False, "error": str(e), "message": "Failed to create business team"}


@app.get("/api/sophia/factory/agents")
async def list_created_agents():
    """List all created business agents"""
    try:
        agents = sophia_business_factory.get_created_agents()
        return {
            "success": True,
            "agents": agents,
            "total": len(agents),
            "message": "Created agents retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        return {"success": False, "error": str(e), "message": "Failed to retrieve agents"}


@app.get("/api/sophia/factory/teams")
async def list_created_teams():
    """List all created business teams"""
    try:
        teams = sophia_business_factory.get_created_teams()
        return {
            "success": True,
            "teams": teams,
            "total": len(teams),
            "message": "Created teams retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to list teams: {e}")
        return {"success": False, "error": str(e), "message": "Failed to retrieve teams"}


@app.get("/api/sophia/factory/agents/{agent_id}")
async def get_agent_info(agent_id: str):
    """Get information about a specific agent"""
    try:
        agents = sophia_business_factory.get_created_agents()
        agent_info = next((agent for agent in agents if agent["id"] == agent_id), None)

        if not agent_info:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        return {
            "success": True,
            "agent": agent_info,
            "message": "Agent information retrieved successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent info: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve agent information",
        }


@app.get("/api/sophia/factory/teams/{team_id}")
async def get_team_info(team_id: str):
    """Get information about a specific team"""
    try:
        teams = sophia_business_factory.get_created_teams()
        team_info = next((team for team in teams if team["id"] == team_id), None)

        if not team_info:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

        return {
            "success": True,
            "team": team_info,
            "message": "Team information retrieved successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team info: {e}")
        return {"success": False, "error": str(e), "message": "Failed to retrieve team information"}


@app.post("/api/sophia/factory/execute/{agent_or_team_id}")
async def execute_business_task(agent_or_team_id: str, request: TaskExecuteRequest):
    """Execute a business task with an agent or team"""
    try:
        result = await sophia_business_factory.execute_business_task(
            agent_or_team_id=agent_or_team_id, task=request.task, context=request.context
        )

        return {
            "success": result["success"],
            "result": result,
            "message": "Task executed successfully"
            if result["success"]
            else "Task execution failed",
        }
    except Exception as e:
        logger.error(f"Failed to execute business task: {e}")
        return {"success": False, "error": str(e), "message": "Failed to execute business task"}


@app.get("/api/sophia/factory/metrics")
async def get_factory_metrics():
    """Get performance metrics for the factory"""
    try:
        metrics = sophia_business_factory.get_performance_metrics()
        return {
            "success": True,
            "metrics": metrics,
            "message": "Factory metrics retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get factory metrics: {e}")
        return {"success": False, "error": str(e), "message": "Failed to retrieve factory metrics"}


@app.get("/api/personas/health")
async def health_mock():
    """Mock health endpoint"""
    return {
        "success": True,
        "status": "healthy",
        "personas": {
            "apollo": {"active": True, "name": "Apollo Thanos", "interactions": 156},
            "athena": {"active": True, "name": "Athena Sophia", "interactions": 203},
        },
    }


# Main route
@app.get("/")
async def root():
    return {
        "message": "Sophia Intelligence Platform - Universal Business Orchestrator",
        "version": "2.0.0",
        "orchestrator": "Sophia Universal Business Intelligence",
        "personality": "Smart, strategic, and savvy business partner",
        "capabilities": [
            "Sales Intelligence & Pipeline Management",
            "Client Success & Relationship Management",
            "Market Research & Competitive Intelligence",
            "Business Analytics & Strategic Planning",
            "Natural Language Business Operations",
            "Multi-step Workflow Execution",
            "Voice Integration Support",
        ],
        "endpoints": {
            "universal_chat": "/api/sophia/chat",
            "business_operations": "/api/sophia/business",
            "status": "/api/sophia/status",
            "insights": "/api/sophia/insights",
            "factory_templates": "/api/sophia/factory/templates",
            "factory_create_agent": "/api/sophia/factory/create-agent",
            "factory_create_team": "/api/sophia/factory/create-team",
            "factory_agents": "/api/sophia/factory/agents",
            "factory_teams": "/api/sophia/factory/teams",
            "factory_metrics": "/api/sophia/factory/metrics",
            "health": "/health",
            "docs": "/docs",
        },
        "status": "operational" if orchestrator_initialized else "initializing",
    }


if __name__ == "__main__":
    port = int(get_config().get("SOPHIA_PORT", "9000"))
    logger.info(
        f"""
💎 SOPHIA UNIVERSAL BUSINESS ORCHESTRATOR & AGENT FACTORY
=========================================================
🚀 Intelligence API:  http://localhost:{port}/api/sophia/chat
📊 Business Ops:      http://localhost:{port}/api/sophia/business
🏭 Agent Factory:     http://localhost:{port}/sophia/factory
📡 API Documentation: http://localhost:{port}/docs
💙 Health & Status:   http://localhost:{port}/health
🧠 Insights Summary:  http://localhost:{port}/api/sophia/insights

🤖 AGNO Business Intelligence Teams:
  💎 Sophia - Strategic Business AGNO Orchestrator
     • Smart, strategic, and savvy personality
     • 4 Specialized AGNO Teams with dedicated agents:
       🔸 Sales Intelligence Team (5 agents): Pipeline, deals, revenue
       🔸 Research Team (4 agents): Market research, competitive intel
       🔸 Client Success Team (4 agents): Health, retention, expansion
       🔸 Market Analysis Team (4 agents): Trends, opportunities, positioning
     • Cross-team synthesis and strategic implications analysis
     • Multi-team coordination for comprehensive business intelligence
     • Natural language multi-step workflow execution
     • Voice integration with business-appropriate responses

🏭 BUSINESS AGENT FACTORY:
  ✨ Create Custom Business Intelligence Agents:
     • Sales Pipeline Analyst (PERPLEXITY-VK for market research)
     • Revenue Forecaster (ANTHROPIC-VK for strategic analysis)
     • Client Success Manager (OPENAI-VK for relationship insights)
     • Market Research Specialist (DEEPSEEK-VK for data analysis)
     • Competitive Intelligence Agent (XAI-VK for creative insights)

  🎯 Pre-built Business Teams:
     • Sales Intelligence Team
     • Client Success Team
     • Market Research Team
     • Strategic Business Team (all agents)

  📊 Factory Endpoints:
     • GET  /api/sophia/factory/templates - List all templates
     • POST /api/sophia/factory/create-agent - Create business agent
     • POST /api/sophia/factory/create-team - Create business team
     • GET  /api/sophia/factory/agents - List created agents
     • GET  /api/sophia/factory/teams - List created teams
     • POST /api/sophia/factory/execute/{id} - Execute tasks
     • GET  /api/sophia/factory/metrics - Performance metrics

🔧 Domain Coverage:
  • Sales Intelligence    • Pipeline Management
  • Client Success        • Market Research
  • Competitive Intel     • Business Analytics
  • Strategic Planning    • Revenue Operations

💬 Chat Example:
  "Analyze my sales pipeline and identify top 3 deals to focus on this quarter"
  "Show me client health metrics and who needs immediate attention"
  "Research our main competitor's pricing strategy and give recommendations"

Starting Sophia Universal Business Orchestrator on port {port}...
"""
    )

    uvicorn.run(app, host="0.0.0.0", port=port)
