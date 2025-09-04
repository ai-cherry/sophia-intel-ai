"""
Universal Sophia Integration for Sales Intelligence Swarm

This module integrates the Sales Intelligence Swarm with the Universal Sophia chat interface:
- Natural language commands for sales intelligence
- Real-time call status queries
- Coaching and feedback integration
- Competitive intelligence queries
- Risk assessment commands
- Performance analytics access
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .agents import SalesAgentOrchestrator, AgentOutput
from .gong_realtime import GongRealtimeConnector, RealtimeCallData
from .feedback_engine import SalesFeedbackSystem, FeedbackMessage
from .dashboard import SalesIntelligenceDashboard

logger = logging.getLogger(__name__)


class SalesCommandType(str, Enum):
    """Types of sales intelligence commands"""
    CALL_STATUS = "call_status"
    RISK_ASSESSMENT = "risk_assessment"
    COMPETITIVE_INTEL = "competitive_intel"
    COACHING_FEEDBACK = "coaching_feedback"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    PERFORMANCE_METRICS = "performance_metrics"
    CALL_SUMMARY = "call_summary"
    TEAM_OVERVIEW = "team_overview"


@dataclass
class SalesQuery:
    """Structured query for sales intelligence"""
    command_type: SalesCommandType
    call_id: Optional[str] = None
    time_range: Optional[str] = None
    specific_metric: Optional[str] = None
    filters: Dict[str, Any] = None
    natural_query: str = ""


class NaturalLanguageProcessor:
    """Processes natural language queries for sales intelligence"""
    
    def __init__(self):
        self.command_patterns = self._load_command_patterns()
        self.keyword_mappings = self._load_keyword_mappings()
        
    def _load_command_patterns(self) -> Dict[str, Dict]:
        """Load patterns for recognizing different command types"""
        return {
            "call_status": {
                "keywords": ["status", "how is", "what's happening", "current call", "live call"],
                "patterns": [
                    r"(?:what's|how's|show me) (?:the )?(?:status|progress) (?:of|for) (?:call|meeting) ([a-zA-Z0-9-_]+)",
                    r"(?:status|update) (?:on|for) (?:call|meeting) ([a-zA-Z0-9-_]+)",
                    r"how (?:is|are) (?:the )?(?:call|meeting|conversation) (?:with|going)"
                ]
            },
            "risk_assessment": {
                "keywords": ["risk", "deal risk", "probability", "chance", "likely"],
                "patterns": [
                    r"(?:what's|what is) (?:the )?(?:risk|probability|chance)",
                    r"(?:how )?(?:risky|likely) (?:is )?(?:this|the) (?:deal|call)",
                    r"(?:deal|call) (?:risk|assessment|probability)"
                ]
            },
            "competitive_intel": {
                "keywords": ["competitor", "competition", "mentioned", "vs", "versus", "alternative"],
                "patterns": [
                    r"(?:any )?(?:competitor|competition) (?:mentioned|discussion)",
                    r"(?:who|what) (?:competitors|alternatives) (?:were )?(?:mentioned|discussed)",
                    r"(?:competitive|competitor) (?:intel|intelligence|activity)"
                ]
            },
            "coaching_feedback": {
                "keywords": ["coaching", "feedback", "improve", "suggestions", "tips"],
                "patterns": [
                    r"(?:any )?(?:coaching|feedback|suggestions) (?:for|available)",
                    r"(?:how )?(?:can|should) (?:i|we) (?:improve|do better)",
                    r"(?:coaching|performance) (?:tips|feedback|recommendations)"
                ]
            },
            "sentiment_analysis": {
                "keywords": ["sentiment", "feeling", "mood", "emotion", "tone"],
                "patterns": [
                    r"(?:what's|how's) (?:the )?(?:sentiment|mood|feeling|tone)",
                    r"(?:how )?(?:is )?(?:the )?(?:prospect|client|customer) (?:feeling|responding)",
                    r"(?:sentiment|emotional|mood) (?:analysis|state|level)"
                ]
            },
            "performance_metrics": {
                "keywords": ["performance", "metrics", "statistics", "analytics", "numbers"],
                "patterns": [
                    r"(?:show|get) (?:me )?(?:performance|metrics|stats|analytics)",
                    r"(?:how )?(?:am|are) (?:i|we) (?:doing|performing)",
                    r"(?:performance|call|sales) (?:metrics|statistics|numbers|data)"
                ]
            }
        }
    
    def _load_keyword_mappings(self) -> Dict[str, str]:
        """Load keyword mappings for entity extraction"""
        return {
            # Time references
            "today": "today",
            "this week": "week",
            "this month": "month",
            "last hour": "hour",
            "recent": "recent",
            
            # Metrics
            "talk time": "talk_time",
            "questions": "question_quality",
            "risk score": "risk_score",
            "sentiment": "sentiment_score",
            
            # Call references
            "current call": "current",
            "active call": "active",
            "this call": "current"
        }
    
    def parse_query(self, natural_query: str) -> SalesQuery:
        """Parse natural language query into structured command"""
        query_lower = natural_query.lower()
        
        # Determine command type
        command_type = self._classify_command(query_lower)
        
        # Extract entities
        call_id = self._extract_call_id(query_lower)
        time_range = self._extract_time_range(query_lower)
        specific_metric = self._extract_metric(query_lower)
        
        return SalesQuery(
            command_type=command_type,
            call_id=call_id,
            time_range=time_range,
            specific_metric=specific_metric,
            natural_query=natural_query
        )
    
    def _classify_command(self, query: str) -> SalesCommandType:
        """Classify the type of command from natural language"""
        import re
        
        # Score each command type based on keyword matches
        scores = {}
        
        for cmd_type, config in self.command_patterns.items():
            score = 0
            
            # Keyword matching
            for keyword in config["keywords"]:
                if keyword in query:
                    score += 1
            
            # Pattern matching
            for pattern in config["patterns"]:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 2
            
            scores[cmd_type] = score
        
        # Return highest scoring command type
        best_match = max(scores.items(), key=lambda x: x[1])
        
        if best_match[1] > 0:
            return SalesCommandType(best_match[0])
        
        # Default to call status if no clear match
        return SalesCommandType.CALL_STATUS
    
    def _extract_call_id(self, query: str) -> Optional[str]:
        """Extract call ID from query"""
        import re
        
        # Look for explicit call ID patterns
        patterns = [
            r"call ([a-zA-Z0-9-_]+)",
            r"meeting ([a-zA-Z0-9-_]+)",
            r"id ([a-zA-Z0-9-_]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        # Check for "current" or "this" call references
        if any(ref in query for ref in ["current call", "this call", "active call"]):
            return "current"
        
        return None
    
    def _extract_time_range(self, query: str) -> Optional[str]:
        """Extract time range from query"""
        for keyword, mapping in self.keyword_mappings.items():
            if keyword in query and mapping in ["today", "week", "month", "hour", "recent"]:
                return mapping
        return None
    
    def _extract_metric(self, query: str) -> Optional[str]:
        """Extract specific metric from query"""
        for keyword, mapping in self.keyword_mappings.items():
            if keyword in query and mapping in ["talk_time", "question_quality", "risk_score", "sentiment_score"]:
                return mapping
        return None


class SalesIntelligenceOrchestrator:
    """Main orchestrator for sales intelligence integration with Sophia"""
    
    def __init__(self, 
                 gong_access_key: str = None, 
                 gong_client_secret: str = None):
        self.nlp_processor = NaturalLanguageProcessor()
        self.agent_orchestrator = SalesAgentOrchestrator()
        self.gong_connector = None
        self.feedback_system = SalesFeedbackSystem()
        self.dashboard = SalesIntelligenceDashboard()
        
        # Initialize Gong connector if credentials provided
        if gong_access_key and gong_client_secret:
            from .gong_realtime import GongRealtimeConnector
            self.gong_connector = GongRealtimeConnector(gong_access_key, gong_client_secret)
        
        self.active_calls: Dict[str, RealtimeCallData] = {}
        self.current_call_id: Optional[str] = None
        
    async def initialize(self):
        """Initialize all components"""
        await self.dashboard.initialize()
        
        # Start agent orchestrator
        await self.agent_orchestrator.start_all_agents()
        
        logger.info("Sales Intelligence Orchestrator initialized")
    
    async def process_sophia_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process query from Sophia chat interface"""
        try:
            # Parse natural language query
            sales_query = self.nlp_processor.parse_query(query)
            
            # Route to appropriate handler
            handler_map = {
                SalesCommandType.CALL_STATUS: self._handle_call_status,
                SalesCommandType.RISK_ASSESSMENT: self._handle_risk_assessment,
                SalesCommandType.COMPETITIVE_INTEL: self._handle_competitive_intel,
                SalesCommandType.COACHING_FEEDBACK: self._handle_coaching_feedback,
                SalesCommandType.SENTIMENT_ANALYSIS: self._handle_sentiment_analysis,
                SalesCommandType.PERFORMANCE_METRICS: self._handle_performance_metrics,
                SalesCommandType.CALL_SUMMARY: self._handle_call_summary,
                SalesCommandType.TEAM_OVERVIEW: self._handle_team_overview
            }
            
            handler = handler_map.get(sales_query.command_type, self._handle_default)
            result = await handler(sales_query, context)
            
            return {
                "success": True,
                "command_type": sales_query.command_type.value,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing Sophia query: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_call_status(self, query: SalesQuery, context: Dict) -> Dict[str, Any]:
        """Handle call status queries"""
        call_id = await self._resolve_call_id(query.call_id)
        
        if not call_id:
            return {
                "message": "No active call found. Please specify a call ID or start a call.",
                "active_calls": list(self.active_calls.keys())
            }
        
        # Get current call data
        call_data = self.active_calls.get(call_id)
        if not call_data:
            return {
                "message": f"Call {call_id} not found or no longer active.",
                "active_calls": list(self.active_calls.keys())
            }
        
        # Get dashboard data
        dashboard_data = self.dashboard.get_call_dashboard_data(call_id)
        
        # Format response
        status_response = {
            "call_id": call_id,
            "title": call_data.metadata.title,
            "duration_minutes": (datetime.now() - call_data.metadata.actual_start).total_seconds() / 60 if call_data.metadata.actual_start else 0,
            "participants": len(call_data.metadata.participants),
            "is_active": call_data.is_active,
            "transcript_segments": len(call_data.transcripts),
            "overall_score": dashboard_data.get("overall_score", 50),
            "key_metrics": dashboard_data.get("latest_metrics", {}),
            "summary": f"Call has been running for {int(status_response.get('duration_minutes', 0))} minutes with {len(call_data.transcripts)} transcript segments."
        }
        
        return status_response
    
    async def _handle_risk_assessment(self, query: SalesQuery, context: Dict) -> Dict[str, Any]:
        """Handle risk assessment queries"""
        call_id = await self._resolve_call_id(query.call_id)
        
        if not call_id:
            return {"message": "No active call found for risk assessment."}
        
        # Get latest risk assessment from agents
        risk_outputs = self.agent_orchestrator.get_recent_outputs(agent_type="risk_assessment")
        call_risk_outputs = [o for o in risk_outputs if o.call_id == call_id]
        
        if not call_risk_outputs:
            return {
                "message": "No risk assessment available yet. Risk analysis is still processing.",
                "call_id": call_id
            }
        
        latest_risk = call_risk_outputs[0]
        risk_data = latest_risk.data
        
        # Format risk response
        risk_level = "high" if risk_data.get("overall_risk_score", 0) > 0.7 else "medium" if risk_data.get("overall_risk_score", 0) > 0.4 else "low"
        
        response = {
            "call_id": call_id,
            "risk_score": risk_data.get("overall_risk_score", 0),
            "risk_level": risk_level,
            "probability_score": risk_data.get("probability_score", 0.5),
            "red_flags": risk_data.get("red_flags", []),
            "buying_signals": risk_data.get("buying_signals", []),
            "summary": f"Deal risk is {risk_level} ({risk_data.get('overall_risk_score', 0):.1%}). " +
                      f"Win probability: {risk_data.get('probability_score', 0.5):.1%}.",
            "recommendations": self._generate_risk_recommendations(risk_data)
        }
        
        return response
    
    async def _handle_competitive_intel(self, query: SalesQuery, context: Dict) -> Dict[str, Any]:
        """Handle competitive intelligence queries"""
        call_id = await self._resolve_call_id(query.call_id)
        
        if not call_id:
            return {"message": "No active call found for competitive analysis."}
        
        # Get competitive intelligence from agents
        competitive_outputs = self.agent_orchestrator.get_recent_outputs(agent_type="competitive")
        call_competitive_outputs = [o for o in competitive_outputs if o.call_id == call_id]
        
        if not call_competitive_outputs:
            return {
                "message": "No competitive activity detected in this call.",
                "call_id": call_id
            }
        
        latest_competitive = call_competitive_outputs[0]
        competitive_data = latest_competitive.data
        
        response = {
            "call_id": call_id,
            "competitor_mentions": competitive_data.get("competitor_mentions", []),
            "threat_level": competitive_data.get("threat_level", 0),
            "comparison_statements": competitive_data.get("comparison_statements", []),
            "feature_discussions": competitive_data.get("feature_discussions", {}),
            "positioning_analysis": competitive_data.get("competitive_positioning", {}),
            "summary": self._generate_competitive_summary(competitive_data),
            "recommendations": self._generate_competitive_recommendations(competitive_data)
        }
        
        return response
    
    async def _handle_coaching_feedback(self, query: SalesQuery, context: Dict) -> Dict[str, Any]:
        """Handle coaching feedback queries"""
        call_id = await self._resolve_call_id(query.call_id)
        
        if not call_id:
            return {"message": "No active call found for coaching analysis."}
        
        # Get coaching outputs
        coaching_outputs = self.agent_orchestrator.get_recent_outputs(agent_type="coaching")
        call_coaching_outputs = [o for o in coaching_outputs if o.call_id == call_id]
        
        # Get active feedback
        active_feedback = self.feedback_system.feedback_engine.get_active_feedback(call_id=call_id)
        coaching_feedback = [f for f in active_feedback if f.type.value in ["coaching_tip", "performance_feedback"]]
        
        if not call_coaching_outputs and not coaching_feedback:
            return {
                "message": "No coaching feedback available yet. Continue the conversation for more insights.",
                "call_id": call_id
            }
        
        response = {
            "call_id": call_id,
            "active_coaching": [
                {
                    "title": f.title,
                    "message": f.message,
                    "action_items": f.action_items,
                    "priority": f.priority.value
                }
                for f in coaching_feedback
            ],
            "performance_analysis": {},
            "coaching_recommendations": []
        }
        
        if call_coaching_outputs:
            latest_coaching = call_coaching_outputs[0]
            coaching_data = latest_coaching.data
            
            response["performance_analysis"] = {
                "talk_time_balance": coaching_data.get("talk_time_balance", {}),
                "questioning_quality": coaching_data.get("questioning_analysis", {}),
                "listening_score": coaching_data.get("listening_score", 0),
                "performance_score": coaching_data.get("performance_score", 0)
            }
            
            response["coaching_recommendations"] = coaching_data.get("coaching_recommendations", [])
            
        response["summary"] = f"Found {len(response['active_coaching'])} active coaching tips and {len(response['coaching_recommendations'])} recommendations."
        
        return response
    
    async def _handle_sentiment_analysis(self, query: SalesQuery, context: Dict) -> Dict[str, Any]:
        """Handle sentiment analysis queries"""
        call_id = await self._resolve_call_id(query.call_id)
        
        if not call_id:
            return {"message": "No active call found for sentiment analysis."}
        
        # Get sentiment outputs
        sentiment_outputs = self.agent_orchestrator.get_recent_outputs(agent_type="sentiment")
        call_sentiment_outputs = [o for o in sentiment_outputs if o.call_id == call_id]
        
        if not call_sentiment_outputs:
            return {
                "message": "No sentiment analysis available yet. Analysis is still processing.",
                "call_id": call_id
            }
        
        latest_sentiment = call_sentiment_outputs[0]
        sentiment_data = latest_sentiment.data
        
        overall_sentiment = sentiment_data.get("overall_sentiment", 0)
        sentiment_label = "positive" if overall_sentiment > 0.2 else "negative" if overall_sentiment < -0.2 else "neutral"
        
        response = {
            "call_id": call_id,
            "overall_sentiment": overall_sentiment,
            "sentiment_label": sentiment_label,
            "engagement_level": sentiment_data.get("engagement_level", 0.5),
            "speaker_emotions": sentiment_data.get("speaker_emotions", {}),
            "stress_indicators": sentiment_data.get("stress_indicators", 0),
            "rapport_score": sentiment_data.get("rapport_score", 0.5),
            "emotional_trajectory": sentiment_data.get("emotional_trajectory", []),
            "summary": f"Overall sentiment is {sentiment_label} ({overall_sentiment:+.2f}). " +
                      f"Engagement level: {sentiment_data.get('engagement_level', 0.5):.1%}. " +
                      f"Rapport score: {sentiment_data.get('rapport_score', 0.5):.1%}."
        }
        
        return response
    
    async def _handle_performance_metrics(self, query: SalesQuery, context: Dict) -> Dict[str, Any]:
        """Handle performance metrics queries"""
        call_id = await self._resolve_call_id(query.call_id)
        
        if call_id:
            # Call-specific metrics
            dashboard_data = self.dashboard.get_call_dashboard_data(call_id)
            return {
                "scope": "call",
                "call_id": call_id,
                "metrics": dashboard_data.get("latest_metrics", {}),
                "overall_score": dashboard_data.get("overall_score", 50),
                "metrics_history": dashboard_data.get("metrics_history", {})
            }
        else:
            # Team-wide metrics
            team_data = self.dashboard.get_team_dashboard_data()
            return {
                "scope": "team",
                "team_summary": team_data.get("team_summary", {}),
                "active_calls": team_data.get("active_calls", []),
                "recent_insights": team_data.get("recent_insights", [])
            }
    
    async def _handle_call_summary(self, query: SalesQuery, context: Dict) -> Dict[str, Any]:
        """Handle call summary queries"""
        call_id = await self._resolve_call_id(query.call_id)
        
        if not call_id:
            return {"message": "No active call found for summarization."}
        
        # Get summary from agents
        summary_outputs = self.agent_orchestrator.get_recent_outputs(agent_type="summary")
        call_summary_outputs = [o for o in summary_outputs if o.call_id == call_id]
        
        if not call_summary_outputs:
            return {
                "message": "Call summary not available yet. Summary will be generated when the call ends or reaches sufficient length.",
                "call_id": call_id
            }
        
        latest_summary = call_summary_outputs[0]
        summary_data = latest_summary.data
        
        return {
            "call_id": call_id,
            "call_summary": summary_data.get("call_summary", ""),
            "key_topics": summary_data.get("key_topics", []),
            "action_items": summary_data.get("action_items", []),
            "next_steps": summary_data.get("next_steps", []),
            "call_outcome": summary_data.get("call_outcome", ""),
            "follow_up_recommendations": summary_data.get("follow_up_recommendations", [])
        }
    
    async def _handle_team_overview(self, query: SalesQuery, context: Dict) -> Dict[str, Any]:
        """Handle team overview queries"""
        team_data = self.dashboard.get_team_dashboard_data()
        
        return {
            "team_summary": team_data.get("team_summary", {}),
            "active_calls": team_data.get("active_calls", []),
            "recent_insights": team_data.get("recent_insights", []),
            "performance_highlights": self._generate_team_highlights(team_data)
        }
    
    async def _handle_default(self, query: SalesQuery, context: Dict) -> Dict[str, Any]:
        """Handle unrecognized queries"""
        return {
            "message": "I can help you with sales intelligence queries. Try asking about:",
            "available_commands": [
                "call status",
                "deal risk assessment", 
                "competitive intelligence",
                "coaching feedback",
                "sentiment analysis",
                "performance metrics",
                "call summary",
                "team overview"
            ],
            "example_queries": [
                "What's the status of the current call?",
                "How risky is this deal?",
                "Any competitors mentioned?",
                "Give me coaching feedback",
                "What's the sentiment like?",
                "Show me performance metrics"
            ]
        }
    
    async def _resolve_call_id(self, call_id_hint: str) -> Optional[str]:
        """Resolve call ID from hint or context"""
        if call_id_hint == "current" or call_id_hint is None:
            # Return the most recent active call
            if self.current_call_id:
                return self.current_call_id
            
            active_calls = [cid for cid, call_data in self.active_calls.items() if call_data.is_active]
            if active_calls:
                return active_calls[0]  # Return first active call
            
            return None
        
        # Check if explicit call ID exists
        if call_id_hint in self.active_calls:
            return call_id_hint
        
        return None
    
    def _generate_risk_recommendations(self, risk_data: Dict) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        risk_score = risk_data.get("overall_risk_score", 0)
        red_flags = risk_data.get("red_flags", [])
        
        if risk_score > 0.7:
            recommendations.append("Consider scheduling a follow-up call to address concerns")
            recommendations.append("Prepare objection handling materials")
        
        for flag in red_flags:
            flag_type = flag.get("type", "")
            if flag_type == "budget_concerns":
                recommendations.append("Focus on ROI and value proposition")
            elif flag_type == "timing_issues":
                recommendations.append("Explore urgency drivers and timeline flexibility")
            elif flag_type == "authority_issues":
                recommendations.append("Identify and engage decision makers")
        
        return recommendations[:5]  # Limit to top 5
    
    def _generate_competitive_summary(self, competitive_data: Dict) -> str:
        """Generate competitive intelligence summary"""
        mentions = competitive_data.get("competitor_mentions", [])
        threat_level = competitive_data.get("threat_level", 0)
        
        if not mentions:
            return "No competitor activity detected in this call."
        
        competitor_names = list(set(m.get("competitor", "") for m in mentions))
        
        summary = f"{len(mentions)} competitor mention(s) detected: {', '.join(competitor_names)}. "
        
        if threat_level > 0.7:
            summary += "High competitive threat - prepare strong differentiation."
        elif threat_level > 0.4:
            summary += "Moderate competitive threat - emphasize unique value."
        else:
            summary += "Low competitive threat - opportunity to position strongly."
        
        return summary
    
    def _generate_competitive_recommendations(self, competitive_data: Dict) -> List[str]:
        """Generate competitive response recommendations"""
        recommendations = []
        mentions = competitive_data.get("competitor_mentions", [])
        
        for mention in mentions[:3]:  # Top 3 mentions
            competitor = mention.get("competitor", "")
            recommendations.append(f"Address {competitor} comparison with differentiation points")
        
        if competitive_data.get("threat_level", 0) > 0.6:
            recommendations.append("Prepare competitive battle cards")
            recommendations.append("Highlight unique capabilities and success stories")
        
        return recommendations
    
    def _generate_team_highlights(self, team_data: Dict) -> List[str]:
        """Generate team performance highlights"""
        highlights = []
        summary = team_data.get("team_summary", {})
        
        total_calls = summary.get("total_active_calls", 0)
        high_risk_calls = summary.get("high_risk_calls", 0)
        avg_sentiment = summary.get("average_sentiment", 0)
        
        highlights.append(f"{total_calls} active calls in progress")
        
        if high_risk_calls > 0:
            highlights.append(f"{high_risk_calls} calls need immediate attention")
        else:
            highlights.append("All calls performing well")
        
        if avg_sentiment > 0.2:
            highlights.append("Positive sentiment across calls")
        elif avg_sentiment < -0.2:
            highlights.append("Sentiment needs improvement - coaching recommended")
        
        return highlights
    
    async def start_call_monitoring(self, call_id: str) -> Dict[str, Any]:
        """Start monitoring a specific call"""
        if not self.gong_connector:
            return {"error": "Gong integration not configured"}
        
        try:
            # Set up event handlers
            event_handlers = {
                "call_started": [self._handle_call_started],
                "transcript_update": [self._handle_transcript_update],
                "call_ended": [self._handle_call_ended]
            }
            
            # Start monitoring
            await self.gong_connector.start_monitoring_call(call_id, event_handlers)
            
            self.current_call_id = call_id
            
            return {
                "success": True,
                "call_id": call_id,
                "message": f"Started monitoring call {call_id}"
            }
            
        except Exception as e:
            logger.error(f"Error starting call monitoring: {e}")
            return {"error": str(e)}
    
    async def _handle_call_started(self, call_id: str, data: Dict, call_data: RealtimeCallData):
        """Handle call started event"""
        self.active_calls[call_id] = call_data
        logger.info(f"Call {call_id} started monitoring")
    
    async def _handle_transcript_update(self, call_id: str, data: Dict, call_data: RealtimeCallData):
        """Handle transcript update event"""
        if call_id in self.active_calls:
            self.active_calls[call_id] = call_data
            
            # Process through agent orchestrator
            await self.agent_orchestrator.process_call_data(call_data)
            
            # Get agent outputs and process through feedback system
            recent_outputs = self.agent_orchestrator.get_recent_outputs()
            for output in recent_outputs:
                if output.call_id == call_id:
                    await self.feedback_system.process_agent_output(output)
                    await self.dashboard.process_agent_output(output)
    
    async def _handle_call_ended(self, call_id: str, data: Dict, call_data: RealtimeCallData):
        """Handle call ended event"""
        if call_id in self.active_calls:
            self.active_calls[call_id].is_active = False
            logger.info(f"Call {call_id} ended")


# Integration function for MCP server
def create_sales_intelligence_commands() -> Dict[str, callable]:
    """Create sales intelligence commands for Sophia integration"""
    
    orchestrator = SalesIntelligenceOrchestrator()
    
    async def sales_query_handler(query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle sales intelligence queries from Sophia"""
        return await orchestrator.process_sophia_query(query, context)
    
    async def start_call_monitoring_handler(call_id: str) -> Dict[str, Any]:
        """Start monitoring a call"""
        return await orchestrator.start_call_monitoring(call_id)
    
    return {
        "sales_intelligence": sales_query_handler,
        "start_call_monitoring": start_call_monitoring_handler
    }


# Example usage and testing
async def example_sophia_integration():
    """Example of Sophia integration usage"""
    
    orchestrator = SalesIntelligenceOrchestrator()
    await orchestrator.initialize()
    
    # Example queries
    queries = [
        "What's the status of the current call?",
        "How risky is this deal?",
        "Any competitors mentioned?",
        "Give me some coaching feedback",
        "What's the sentiment like?",
        "Show me performance metrics"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        response = await orchestrator.process_sophia_query(query)
        print(f"Response: {json.dumps(response, indent=2, default=str)}")


if __name__ == "__main__":
    asyncio.run(example_sophia_integration())