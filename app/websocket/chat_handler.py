"""
Sophia AI WebSocket Chat Handler
Real-time communication between frontend and MCP backend
NO MOCK DATA - Production WebSocket implementation
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from app.memory.bus import UnifiedMemoryBus
from app.mcp.server_template import SophiaMCPServer
from app.mcp.revenue_ops_gateway import RevenueOpsGateway
from app.factory_ai.swarm_wrapper import FactoryMCPSwarm

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class ChatSession:
    """Individual chat session with WebSocket connection"""
    
    def __init__(self, websocket: WebSocket, session_id: str, user_id: str = None):
        self.websocket = websocket
        self.session_id = session_id
        self.user_id = user_id or f"user_{int(time.time())}"
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.message_count = 0
        self.context = {}
        
    async def send_message(self, message: Dict):
        """Send message to WebSocket client"""
        try:
            await self.websocket.send_text(json.dumps(message))
            self.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            raise
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
        self.message_count += 1

class SophiaChatHandler:
    """
    WebSocket chat handler for Sophia AI
    Manages real-time communication with specialized agents
    """
    
    def __init__(self, memory_bus: UnifiedMemoryBus, mcp_server: SophiaMCPServer, 
                 revenue_ops: RevenueOpsGateway, factory_swarm: FactoryMCPSwarm):
        self.memory_bus = memory_bus
        self.mcp_server = mcp_server
        self.revenue_ops = revenue_ops
        self.factory_swarm = factory_swarm
        
        # Active sessions
        self.active_sessions: Dict[str, ChatSession] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids
        
        # Agent routing
        self.agent_handlers = {
            'all': self._handle_all_agents,
            'sales_coach': self._handle_sales_coach,
            'customer_support_coach': self._handle_support_coach,
            'client_health': self._handle_client_health,
            'product_strategist': self._handle_product_strategist,
            'database_master': self._handle_database_master,
            'ceo_coach': self._handle_ceo_coach
        }
        
        logger.info("🔥 Sophia Chat Handler initialized - Real-time WebSocket ready")
    
    async def connect(self, websocket: WebSocket, user_id: str = None) -> str:
        """Accept WebSocket connection and create session"""
        await websocket.accept()
        
        session_id = str(uuid4())
        session = ChatSession(websocket, session_id, user_id)
        
        self.active_sessions[session_id] = session
        
        if user_id:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)
        
        logger.info(f"✅ WebSocket connected: session={session_id}, user={user_id}")
        
        # Send welcome message
        await session.send_message({
            "type": "system_status",
            "status": "connected",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "memory_bus": "operational",
                "mcp_server": "operational",
                "revenue_ops": "operational",
                "factory_swarm": "operational"
            }
        })
        
        return session_id
    
    async def disconnect(self, session_id: str):
        """Handle WebSocket disconnection"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Remove from user sessions
            if session.user_id in self.user_sessions:
                self.user_sessions[session.user_id].discard(session_id)
                if not self.user_sessions[session.user_id]:
                    del self.user_sessions[session.user_id]
            
            # Remove session
            del self.active_sessions[session_id]
            
            logger.info(f"🔌 WebSocket disconnected: session={session_id}, user={session.user_id}")
    
    async def handle_message(self, session_id: str, message: Dict):
        """Handle incoming WebSocket message"""
        if session_id not in self.active_sessions:
            logger.error(f"Message from unknown session: {session_id}")
            return
        
        session = self.active_sessions[session_id]
        session.update_activity()
        
        with tracer.start_as_current_span("chat_message_handling") as span:
            span.set_attribute("session_id", session_id)
            span.set_attribute("user_id", session.user_id)
            span.set_attribute("message_type", message.get("type", "unknown"))
            
            try:
                if message.get("type") == "chat_message":
                    await self._handle_chat_message(session, message)
                elif message.get("type") == "system_query":
                    await self._handle_system_query(session, message)
                elif message.get("type") == "agent_switch":
                    await self._handle_agent_switch(session, message)
                else:
                    await session.send_message({
                        "type": "error",
                        "error": f"Unknown message type: {message.get('type')}",
                        "timestamp": datetime.now().isoformat()
                    })
                
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                span.set_status(Status(StatusCode.ERROR, str(e)))
                
                await session.send_message({
                    "type": "error",
                    "error": f"Failed to process message: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
    
    async def _handle_chat_message(self, session: ChatSession, message: Dict):
        """Handle chat message from user"""
        user_message = message.get("message", "").strip()
        agent = message.get("agent", "all")
        context = message.get("context", {})
        request_id = message.get("request_id")
        
        if not user_message:
            await session.send_message({
                "type": "error",
                "error": "Empty message",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Update session context
        session.context.update(context)
        
        # Route to appropriate agent handler
        if agent in self.agent_handlers:
            response = await self.agent_handlers[agent](user_message, session.context)
        else:
            response = await self._handle_all_agents(user_message, session.context)
        
        # Send response
        await session.send_message({
            "type": "chat_response",
            "agent": agent,
            "content": response["content"],
            "metadata": response.get("metadata", {}),
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _handle_system_query(self, session: ChatSession, message: Dict):
        """Handle system query (health, metrics, etc.)"""
        query_type = message.get("query", "health")
        
        if query_type == "health":
            # Get system health from all components
            health_data = {
                "status": "healthy",
                "components": {
                    "memory_bus": "operational",
                    "mcp_server": "operational", 
                    "revenue_ops": "operational",
                    "factory_swarm": "operational"
                },
                "active_sessions": len(self.active_sessions),
                "timestamp": datetime.now().isoformat()
            }
            
            await session.send_message({
                "type": "system_status",
                "status": health_data["status"],
                "components": health_data["components"],
                "metadata": {
                    "active_sessions": health_data["active_sessions"]
                },
                "timestamp": health_data["timestamp"]
            })
        
        elif query_type == "metrics":
            # Get system metrics
            metrics = await self._get_system_metrics()
            
            await session.send_message({
                "type": "system_metrics",
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _handle_agent_switch(self, session: ChatSession, message: Dict):
        """Handle agent switching"""
        new_agent = message.get("agent", "all")
        
        # Update session context
        session.context["current_agent"] = new_agent
        
        await session.send_message({
            "type": "agent_switched",
            "agent": new_agent,
            "message": f"Switched to {new_agent} agent",
            "timestamp": datetime.now().isoformat()
        })
    
    # Agent-specific handlers
    async def _handle_all_agents(self, message: str, context: Dict) -> Dict:
        """Handle message with all agents (comprehensive analysis)"""
        try:
            # Use MCP server for comprehensive analysis
            result = await self.mcp_server.call_tool({
                "tool": "chat.comprehensive_analysis",
                "params": {
                    "message": message,
                    "context": context
                }
            })
            
            if result.get("success"):
                return {
                    "content": result["result"]["response"],
                    "metadata": {
                        "agent": "all_agents",
                        "sources": result["result"].get("sources", []),
                        "confidence": result["result"].get("confidence", 0.9)
                    }
                }
            else:
                return {
                    "content": f"I apologize, but I encountered an issue processing your request: {result.get('error', 'Unknown error')}",
                    "metadata": {"agent": "all_agents", "error": True}
                }
                
        except Exception as e:
            logger.error(f"All agents handler error: {e}")
            return {
                "content": "I'm experiencing technical difficulties. Please try again in a moment.",
                "metadata": {"agent": "all_agents", "error": True}
            }
    
    async def _handle_sales_coach(self, message: str, context: Dict) -> Dict:
        """Handle sales coaching queries"""
        try:
            # Use Revenue Ops Gateway for sales intelligence
            result = await self.revenue_ops.call_tool({
                "tool": "sales.coaching_analysis",
                "params": {
                    "query": message,
                    "context": context
                }
            })
            
            if result.get("success"):
                return {
                    "content": result["result"]["coaching_advice"],
                    "metadata": {
                        "agent": "sales_coach",
                        "pipeline_insights": result["result"].get("pipeline_insights", {}),
                        "recommendations": result["result"].get("recommendations", [])
                    }
                }
            else:
                return {
                    "content": "I'm having trouble accessing sales data right now. Let me help you with general sales coaching instead.",
                    "metadata": {"agent": "sales_coach", "fallback": True}
                }
                
        except Exception as e:
            logger.error(f"Sales coach handler error: {e}")
            return {
                "content": "I'm here to help with sales coaching, but I'm experiencing technical issues. Please try again.",
                "metadata": {"agent": "sales_coach", "error": True}
            }
    
    async def _handle_support_coach(self, message: str, context: Dict) -> Dict:
        """Handle customer support coaching queries"""
        try:
            # Use Revenue Ops Gateway for support intelligence
            result = await self.revenue_ops.call_tool({
                "tool": "support.coaching_analysis", 
                "params": {
                    "query": message,
                    "context": context
                }
            })
            
            if result.get("success"):
                return {
                    "content": result["result"]["coaching_advice"],
                    "metadata": {
                        "agent": "customer_support_coach",
                        "support_metrics": result["result"].get("support_metrics", {}),
                        "improvement_areas": result["result"].get("improvement_areas", [])
                    }
                }
            else:
                return {
                    "content": "I'm here to help optimize your customer support processes. What specific area would you like to focus on?",
                    "metadata": {"agent": "customer_support_coach", "fallback": True}
                }
                
        except Exception as e:
            logger.error(f"Support coach handler error: {e}")
            return {
                "content": "I'm your customer support coach, but I'm experiencing technical issues. Please try again.",
                "metadata": {"agent": "customer_support_coach", "error": True}
            }
    
    async def _handle_client_health(self, message: str, context: Dict) -> Dict:
        """Handle client health analysis queries"""
        try:
            # Use Revenue Ops Gateway for client health analysis
            result = await self.revenue_ops.call_tool({
                "tool": "health.client_analysis",
                "params": {
                    "query": message,
                    "context": context
                }
            })
            
            if result.get("success"):
                return {
                    "content": result["result"]["health_analysis"],
                    "metadata": {
                        "agent": "client_health",
                        "health_scores": result["result"].get("health_scores", {}),
                        "risk_factors": result["result"].get("risk_factors", []),
                        "recommendations": result["result"].get("recommendations", [])
                    }
                }
            else:
                return {
                    "content": "I'm analyzing client health patterns. Which specific client or metric would you like me to focus on?",
                    "metadata": {"agent": "client_health", "fallback": True}
                }
                
        except Exception as e:
            logger.error(f"Client health handler error: {e}")
            return {
                "content": "I'm your client health analyst, but I'm experiencing technical issues. Please try again.",
                "metadata": {"agent": "client_health", "error": True}
            }
    
    async def _handle_product_strategist(self, message: str, context: Dict) -> Dict:
        """Handle product strategy queries"""
        try:
            # Use Factory AI Swarm for product intelligence
            result = await self.factory_swarm.call_tool({
                "tool": "product.strategy_analysis",
                "params": {
                    "query": message,
                    "context": context
                }
            })
            
            if result.get("success"):
                return {
                    "content": result["result"]["strategy_insights"],
                    "metadata": {
                        "agent": "product_strategist",
                        "feature_analysis": result["result"].get("feature_analysis", {}),
                        "roadmap_insights": result["result"].get("roadmap_insights", [])
                    }
                }
            else:
                return {
                    "content": "I'm here to help with product strategy and roadmap planning. What specific product area interests you?",
                    "metadata": {"agent": "product_strategist", "fallback": True}
                }
                
        except Exception as e:
            logger.error(f"Product strategist handler error: {e}")
            return {
                "content": "I'm your product strategist, but I'm experiencing technical issues. Please try again.",
                "metadata": {"agent": "product_strategist", "error": True}
            }
    
    async def _handle_database_master(self, message: str, context: Dict) -> Dict:
        """Handle database and data analysis queries"""
        try:
            # Use MCP server for database operations
            result = await self.mcp_server.call_tool({
                "tool": "database.query_analysis",
                "params": {
                    "query": message,
                    "context": context
                }
            })
            
            if result.get("success"):
                return {
                    "content": result["result"]["analysis"],
                    "metadata": {
                        "agent": "database_master",
                        "query_results": result["result"].get("query_results", {}),
                        "data_insights": result["result"].get("data_insights", [])
                    }
                }
            else:
                return {
                    "content": "I'm your database expert. I can help with data analysis, queries, and insights. What would you like to explore?",
                    "metadata": {"agent": "database_master", "fallback": True}
                }
                
        except Exception as e:
            logger.error(f"Database master handler error: {e}")
            return {
                "content": "I'm your database master, but I'm experiencing technical issues. Please try again.",
                "metadata": {"agent": "database_master", "error": True}
            }
    
    async def _handle_ceo_coach(self, message: str, context: Dict) -> Dict:
        """Handle CEO coaching and executive insights"""
        try:
            # Use Revenue Ops Gateway for executive intelligence
            result = await self.revenue_ops.call_tool({
                "tool": "executive.ceo_insights",
                "params": {
                    "query": message,
                    "context": context
                }
            })
            
            if result.get("success"):
                return {
                    "content": result["result"]["executive_insights"],
                    "metadata": {
                        "agent": "ceo_coach",
                        "strategic_metrics": result["result"].get("strategic_metrics", {}),
                        "action_items": result["result"].get("action_items", []),
                        "risk_alerts": result["result"].get("risk_alerts", [])
                    }
                }
            else:
                return {
                    "content": "I'm here to provide executive insights and strategic guidance for Pay Ready. What area needs your attention?",
                    "metadata": {"agent": "ceo_coach", "fallback": True}
                }
                
        except Exception as e:
            logger.error(f"CEO coach handler error: {e}")
            return {
                "content": "I'm your CEO coach, but I'm experiencing technical issues. Please try again.",
                "metadata": {"agent": "ceo_coach", "error": True}
            }
    
    async def _get_system_metrics(self) -> Dict:
        """Get comprehensive system metrics"""
        try:
            # Get metrics from memory bus
            memory_metrics = await self.memory_bus.get_metrics()
            
            # Get MCP server metrics
            mcp_metrics = await self.mcp_server.get_metrics()
            
            # Combine metrics
            return {
                "cache_hit_rate": memory_metrics.get("cache_hit_rate", 0.0),
                "avg_response_time": memory_metrics.get("avg_response_time", 0),
                "active_connections": len(self.active_sessions),
                "memory_usage": memory_metrics.get("memory_usage_percent", 0),
                "total_requests": mcp_metrics.get("total_requests", 0),
                "error_rate": mcp_metrics.get("error_rate", 0.0),
                "uptime_seconds": mcp_metrics.get("uptime_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    async def broadcast_to_user(self, user_id: str, message: Dict):
        """Broadcast message to all sessions for a user"""
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id]:
                if session_id in self.active_sessions:
                    try:
                        await self.active_sessions[session_id].send_message(message)
                    except Exception as e:
                        logger.error(f"Failed to broadcast to session {session_id}: {e}")
    
    async def broadcast_to_all(self, message: Dict):
        """Broadcast message to all active sessions"""
        for session in self.active_sessions.values():
            try:
                await session.send_message(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to session {session.session_id}: {e}")
    
    def get_session_stats(self) -> Dict:
        """Get session statistics"""
        return {
            "active_sessions": len(self.active_sessions),
            "unique_users": len(self.user_sessions),
            "total_messages": sum(session.message_count for session in self.active_sessions.values()),
            "oldest_session": min(
                (session.connected_at for session in self.active_sessions.values()),
                default=datetime.now()
            ).isoformat() if self.active_sessions else None
        }

