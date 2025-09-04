"""
Real-time Sales Intelligence Dashboard

This module provides live dashboard capabilities for sales intelligence:
- Real-time call metrics and analytics
- Live performance indicators  
- Risk alerts and notifications
- Competitive intelligence display
- Coaching feedback integration
- Team performance tracking
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import redis.asyncio as aioredis

from .agents import AgentOutput, AgentPriority
from .feedback_engine import FeedbackMessage, FeedbackType
from .gong_realtime import RealtimeCallData
from .unified_data_fetcher import UnifiedDataFetcher, get_unified_data

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics tracked on dashboard"""
    CALL_QUALITY = "call_quality"
    SENTIMENT = "sentiment"
    RISK_SCORE = "risk_score"
    TALK_TIME = "talk_time"
    QUESTION_QUALITY = "question_quality"
    COMPETITIVE_ACTIVITY = "competitive_activity"
    BUYING_SIGNALS = "buying_signals"
    COACHING_SCORE = "coaching_score"


@dataclass
class DashboardMetric:
    """Individual dashboard metric"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    call_id: str
    label: str
    unit: str
    trend: str  # "up", "down", "stable"
    color: str  # "green", "yellow", "red"
    target_value: Optional[float] = None


@dataclass
class CallSummaryCard:
    """Summary card for individual call"""
    call_id: str
    title: str
    duration: int
    participants: List[str]
    status: str  # "active", "completed", "paused"
    risk_level: str  # "low", "medium", "high", "critical"
    sentiment_score: float
    key_insights: List[str]
    last_update: datetime


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.connections: Set[WebSocket] = set()
        self.call_subscriptions: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, call_id: str = None):
        """Connect a WebSocket client"""
        await websocket.accept()
        self.connections.add(websocket)
        
        if call_id:
            if call_id not in self.call_subscriptions:
                self.call_subscriptions[call_id] = set()
            self.call_subscriptions[call_id].add(websocket)
        
        logger.info(f"WebSocket connected. Total connections: {len(self.connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        self.connections.discard(websocket)
        
        # Remove from call subscriptions
        for call_id, subscribers in self.call_subscriptions.items():
            subscribers.discard(websocket)
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.connections)}")
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.connections:
            return
        
        message_str = json.dumps(message, default=str)
        disconnected = set()
        
        for connection in self.connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_call(self, call_id: str, message: Dict[str, Any]):
        """Broadcast message to subscribers of specific call"""
        if call_id not in self.call_subscriptions:
            return
        
        message_str = json.dumps(message, default=str)
        disconnected = set()
        
        for connection in self.call_subscriptions[call_id]:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error sending call message to WebSocket: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.call_subscriptions[call_id].discard(connection)


class MetricsCalculator:
    """Calculates dashboard metrics from agent outputs"""
    
    def __init__(self):
        self.metric_history: Dict[str, List[DashboardMetric]] = {}
        
    def calculate_call_quality_score(self, agent_outputs: List[AgentOutput]) -> float:
        """Calculate overall call quality score (0-100)"""
        if not agent_outputs:
            return 50.0
        
        factors = {
            "sentiment": 0.3,
            "talk_time_balance": 0.2,
            "question_quality": 0.25,
            "engagement": 0.25
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for output in agent_outputs:
            if output.agent_type == "sentiment":
                sentiment = output.data.get("overall_sentiment", 0.0)
                # Convert -1 to 1 scale to 0 to 100
                score = ((sentiment + 1) / 2) * 100
                total_score += score * factors["sentiment"]
                total_weight += factors["sentiment"]
            
            elif output.agent_type == "coaching":
                talk_balance = output.data.get("talk_time_balance", {}).get("balance_score", 0.5)
                question_quality = output.data.get("questioning_analysis", {}).get("question_quality", 0.5)
                
                total_score += talk_balance * 100 * factors["talk_time_balance"]
                total_score += question_quality * 100 * factors["question_quality"]
                total_weight += factors["talk_time_balance"] + factors["question_quality"]
        
        if total_weight > 0:
            return total_score / total_weight
        return 50.0
    
    def calculate_risk_trend(self, call_id: str, current_risk: float) -> str:
        """Calculate risk trend based on history"""
        if call_id not in self.metric_history:
            return "stable"
        
        risk_metrics = [
            m for m in self.metric_history[call_id] 
            if m.metric_type == MetricType.RISK_SCORE
        ]
        
        if len(risk_metrics) < 2:
            return "stable"
        
        recent_risks = [m.value for m in risk_metrics[-3:]]
        
        if len(recent_risks) >= 2:
            if recent_risks[-1] > recent_risks[-2] + 0.1:
                return "up"
            elif recent_risks[-1] < recent_risks[-2] - 0.1:
                return "down"
        
        return "stable"
    
    def get_metric_color(self, metric_type: MetricType, value: float) -> str:
        """Get color coding for metric value"""
        color_rules = {
            MetricType.CALL_QUALITY: lambda v: "green" if v >= 70 else "yellow" if v >= 50 else "red",
            MetricType.SENTIMENT: lambda v: "green" if v >= 0.2 else "yellow" if v >= -0.2 else "red",
            MetricType.RISK_SCORE: lambda v: "red" if v >= 0.7 else "yellow" if v >= 0.4 else "green",
            MetricType.TALK_TIME: lambda v: "green" if 0.3 <= v <= 0.4 else "yellow" if 0.2 <= v <= 0.5 else "red",
            MetricType.QUESTION_QUALITY: lambda v: "green" if v >= 0.7 else "yellow" if v >= 0.5 else "red"
        }
        
        return color_rules.get(metric_type, lambda v: "gray")(value)


class SalesIntelligenceDashboard:
    """Main dashboard class for sales intelligence"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.websocket_manager = WebSocketManager()
        self.metrics_calculator = MetricsCalculator()
        self.active_calls: Dict[str, CallSummaryCard] = {}
        self.dashboard_metrics: Dict[str, List[DashboardMetric]] = {}
        self.redis_client = None
        self.redis_url = redis_url
        self.data_fetcher = UnifiedDataFetcher()
        self.platform_data = None
        
    async def initialize(self):
        """Initialize dashboard connections"""
        try:
            self.redis_client = await aioredis.from_url(self.redis_url)
            logger.info("Connected to Redis for dashboard state")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
        
        # Load initial platform data
        try:
            self.platform_data = await get_unified_data()
            logger.info(f"Loaded data from {self.platform_data.connected_platforms} platforms")
        except Exception as e:
            logger.error(f"Failed to load platform data: {e}")
    
    async def process_agent_output(self, output: AgentOutput):
        """Process agent output and update dashboard metrics"""
        call_id = output.call_id
        
        # Calculate metrics based on agent type
        metrics = []
        
        if output.agent_type == "sentiment":
            sentiment_metric = DashboardMetric(
                metric_type=MetricType.SENTIMENT,
                value=output.data.get("overall_sentiment", 0.0),
                timestamp=output.timestamp,
                call_id=call_id,
                label="Sentiment Score",
                unit="score",
                trend=self._calculate_trend(call_id, MetricType.SENTIMENT, output.data.get("overall_sentiment", 0.0)),
                color=self.metrics_calculator.get_metric_color(MetricType.SENTIMENT, output.data.get("overall_sentiment", 0.0))
            )
            metrics.append(sentiment_metric)
        
        elif output.agent_type == "risk_assessment":
            risk_score = output.data.get("overall_risk_score", 0.0)
            risk_metric = DashboardMetric(
                metric_type=MetricType.RISK_SCORE,
                value=risk_score,
                timestamp=output.timestamp,
                call_id=call_id,
                label="Deal Risk",
                unit="score",
                trend=self.metrics_calculator.calculate_risk_trend(call_id, risk_score),
                color=self.metrics_calculator.get_metric_color(MetricType.RISK_SCORE, risk_score),
                target_value=0.3
            )
            metrics.append(risk_metric)
        
        elif output.agent_type == "coaching":
            # Multiple metrics from coaching agent
            talk_time = output.data.get("talk_time_balance", {}).get("internal_ratio", 0.5)
            question_quality = output.data.get("questioning_analysis", {}).get("question_quality", 0.5)
            
            talk_metric = DashboardMetric(
                metric_type=MetricType.TALK_TIME,
                value=talk_time,
                timestamp=output.timestamp,
                call_id=call_id,
                label="Talk Time Ratio",
                unit="ratio",
                trend=self._calculate_trend(call_id, MetricType.TALK_TIME, talk_time),
                color=self.metrics_calculator.get_metric_color(MetricType.TALK_TIME, talk_time),
                target_value=0.35
            )
            
            question_metric = DashboardMetric(
                metric_type=MetricType.QUESTION_QUALITY,
                value=question_quality,
                timestamp=output.timestamp,
                call_id=call_id,
                label="Question Quality",
                unit="score",
                trend=self._calculate_trend(call_id, MetricType.QUESTION_QUALITY, question_quality),
                color=self.metrics_calculator.get_metric_color(MetricType.QUESTION_QUALITY, question_quality),
                target_value=0.7
            )
            
            metrics.extend([talk_metric, question_metric])
        
        elif output.agent_type == "competitive":
            competitive_activity = len(output.data.get("competitor_mentions", []))
            competitive_metric = DashboardMetric(
                metric_type=MetricType.COMPETITIVE_ACTIVITY,
                value=competitive_activity,
                timestamp=output.timestamp,
                call_id=call_id,
                label="Competitor Mentions",
                unit="count",
                trend="up" if competitive_activity > 0 else "stable",
                color="yellow" if competitive_activity > 0 else "green"
            )
            metrics.append(competitive_metric)
        
        # Store metrics
        if call_id not in self.dashboard_metrics:
            self.dashboard_metrics[call_id] = []
        
        self.dashboard_metrics[call_id].extend(metrics)
        
        # Update metrics history for trend calculation
        for metric in metrics:
            if call_id not in self.metrics_calculator.metric_history:
                self.metrics_calculator.metric_history[call_id] = []
            self.metrics_calculator.metric_history[call_id].append(metric)
        
        # Update call summary
        await self._update_call_summary(call_id, output)
        
        # Broadcast updates
        await self._broadcast_metrics_update(call_id, metrics)
    
    def _calculate_trend(self, call_id: str, metric_type: MetricType, current_value: float) -> str:
        """Calculate trend for a metric"""
        history = self.metrics_calculator.metric_history.get(call_id, [])
        recent_values = [
            m.value for m in history 
            if m.metric_type == metric_type and m.timestamp > datetime.now() - timedelta(minutes=5)
        ]
        
        if len(recent_values) < 2:
            return "stable"
        
        if current_value > recent_values[-2] * 1.1:
            return "up"
        elif current_value < recent_values[-2] * 0.9:
            return "down"
        else:
            return "stable"
    
    async def _update_call_summary(self, call_id: str, output: AgentOutput):
        """Update call summary card"""
        if call_id not in self.active_calls:
            # Create new call summary
            self.active_calls[call_id] = CallSummaryCard(
                call_id=call_id,
                title=f"Call {call_id[:8]}",
                duration=0,
                participants=[],
                status="active",
                risk_level="medium",
                sentiment_score=0.0,
                key_insights=[],
                last_update=datetime.now()
            )
        
        call_summary = self.active_calls[call_id]
        call_summary.last_update = datetime.now()
        
        # Update specific fields based on agent output
        if output.agent_type == "sentiment":
            call_summary.sentiment_score = output.data.get("overall_sentiment", 0.0)
        
        elif output.agent_type == "risk_assessment":
            risk_score = output.data.get("overall_risk_score", 0.0)
            if risk_score >= 0.8:
                call_summary.risk_level = "critical"
            elif risk_score >= 0.6:
                call_summary.risk_level = "high"
            elif risk_score >= 0.4:
                call_summary.risk_level = "medium"
            else:
                call_summary.risk_level = "low"
        
        # Add key insights
        if output.requires_action:
            insight = self._generate_insight_from_output(output)
            if insight and insight not in call_summary.key_insights:
                call_summary.key_insights.append(insight)
                # Keep only last 5 insights
                call_summary.key_insights = call_summary.key_insights[-5:]
    
    def _generate_insight_from_output(self, output: AgentOutput) -> Optional[str]:
        """Generate human-readable insight from agent output"""
        insights = {
            "sentiment": lambda d: f"Sentiment is {'positive' if d.get('overall_sentiment', 0) > 0.2 else 'negative' if d.get('overall_sentiment', 0) < -0.2 else 'neutral'}",
            "risk_assessment": lambda d: f"Deal risk is {'high' if d.get('overall_risk_score', 0) > 0.7 else 'moderate'}",
            "competitive": lambda d: f"Competitor {d.get('competitor_mentions', [{}])[0].get('competitor', 'unknown')} mentioned" if d.get('competitor_mentions') else None,
            "coaching": lambda d: f"Talk time balance needs improvement" if d.get('talk_time_balance', {}).get('internal_ratio', 0) > 0.6 else None
        }
        
        insight_generator = insights.get(output.agent_type)
        return insight_generator(output.data) if insight_generator else None
    
    async def _broadcast_metrics_update(self, call_id: str, metrics: List[DashboardMetric]):
        """Broadcast metrics update to WebSocket clients"""
        update_message = {
            "type": "metrics_update",
            "call_id": call_id,
            "metrics": [asdict(metric) for metric in metrics],
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_call(call_id, update_message)
        await self.websocket_manager.broadcast_to_all({
            "type": "global_metrics_update",
            "data": update_message
        })
    
    async def process_feedback_message(self, feedback: FeedbackMessage):
        """Process feedback message for dashboard display"""
        alert_message = {
            "type": "feedback_alert",
            "call_id": feedback.call_id,
            "feedback": {
                "id": feedback.id,
                "type": feedback.type.value,
                "priority": feedback.priority.value,
                "title": feedback.title,
                "message": feedback.message,
                "action_items": feedback.action_items,
                "expires_at": feedback.expires_at.isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_call(feedback.call_id, alert_message)
    
    def get_call_dashboard_data(self, call_id: str) -> Dict[str, Any]:
        """Get complete dashboard data for a specific call"""
        metrics = self.dashboard_metrics.get(call_id, [])
        call_summary = self.active_calls.get(call_id)
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            metric_type = metric.metric_type.value
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []
            metrics_by_type[metric_type].append(asdict(metric))
        
        # Get latest values for each metric type
        latest_metrics = {}
        for metric_type, metric_list in metrics_by_type.items():
            if metric_list:
                latest_metrics[metric_type] = max(metric_list, key=lambda m: m["timestamp"])
        
        return {
            "call_id": call_id,
            "call_summary": asdict(call_summary) if call_summary else None,
            "latest_metrics": latest_metrics,
            "metrics_history": metrics_by_type,
            "overall_score": self._calculate_overall_call_score(call_id)
        }
    
    def _calculate_overall_call_score(self, call_id: str) -> float:
        """Calculate overall call performance score"""
        if call_id not in self.dashboard_metrics:
            return 50.0
        
        metrics = self.dashboard_metrics[call_id]
        recent_metrics = [m for m in metrics if m.timestamp > datetime.now() - timedelta(minutes=10)]
        
        if not recent_metrics:
            return 50.0
        
        # Weight different metrics
        score = 0.0
        total_weight = 0.0
        
        for metric in recent_metrics:
            weight = {
                MetricType.SENTIMENT: 0.25,
                MetricType.RISK_SCORE: 0.30,
                MetricType.TALK_TIME: 0.20,
                MetricType.QUESTION_QUALITY: 0.25
            }.get(metric.metric_type, 0.1)
            
            # Normalize metric value to 0-100 scale
            if metric.metric_type == MetricType.SENTIMENT:
                normalized_value = ((metric.value + 1) / 2) * 100
            elif metric.metric_type == MetricType.RISK_SCORE:
                normalized_value = (1 - metric.value) * 100  # Lower risk is better
            else:
                normalized_value = metric.value * 100
            
            score += normalized_value * weight
            total_weight += weight
        
        return score / total_weight if total_weight > 0 else 50.0
    
    def get_team_dashboard_data(self) -> Dict[str, Any]:
        """Get team-wide dashboard data"""
        active_calls = list(self.active_calls.values())
        
        # Calculate team metrics
        total_calls = len(active_calls)
        high_risk_calls = len([c for c in active_calls if c.risk_level in ["high", "critical"]])
        avg_sentiment = sum(c.sentiment_score for c in active_calls) / total_calls if total_calls > 0 else 0.0
        
        # Recent activity
        recent_insights = []
        for call in active_calls:
            for insight in call.key_insights:
                recent_insights.append({
                    "call_id": call.call_id,
                    "insight": insight,
                    "timestamp": call.last_update.isoformat()
                })
        
        recent_insights.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Platform data summary
        platform_summary = {}
        if self.platform_data:
            platform_summary = {
                "total_records": self.platform_data.total_records,
                "connected_platforms": self.platform_data.connected_platforms,
                "last_sync": self.platform_data.last_sync.isoformat() if self.platform_data.last_sync else None,
                "platforms": {
                    "gong": {
                        "enabled": bool(self.platform_data.gong),
                        "count": self.platform_data.gong.count if self.platform_data.gong else 0,
                        "type": self.platform_data.gong.data_type if self.platform_data.gong else "calls"
                    },
                    "asana": {
                        "enabled": bool(self.platform_data.asana),
                        "count": self.platform_data.asana.count if self.platform_data.asana else 0,
                        "type": self.platform_data.asana.data_type if self.platform_data.asana else "projects"
                    },
                    "linear": {
                        "enabled": bool(self.platform_data.linear),
                        "count": self.platform_data.linear.count if self.platform_data.linear else 0,
                        "type": self.platform_data.linear.data_type if self.platform_data.linear else "teams"
                    },
                    "notion": {
                        "enabled": bool(self.platform_data.notion),
                        "count": self.platform_data.notion.count if self.platform_data.notion else 0,
                        "type": self.platform_data.notion.data_type if self.platform_data.notion else "databases"
                    },
                    "hubspot": {
                        "enabled": bool(self.platform_data.hubspot),
                        "count": self.platform_data.hubspot.count if self.platform_data.hubspot else 0,
                        "type": self.platform_data.hubspot.data_type if self.platform_data.hubspot else "contacts"
                    }
                }
            }
        
        return {
            "team_summary": {
                "total_active_calls": total_calls,
                "high_risk_calls": high_risk_calls,
                "average_sentiment": avg_sentiment,
                "calls_needing_attention": high_risk_calls
            },
            "platform_summary": platform_summary,
            "active_calls": [asdict(call) for call in active_calls],
            "recent_insights": recent_insights[:10],
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup_completed_calls(self):
        """Clean up data for completed calls"""
        cutoff_time = datetime.now() - timedelta(hours=2)
        
        completed_calls = [
            call_id for call_id, call in self.active_calls.items()
            if call.status == "completed" and call.last_update < cutoff_time
        ]
        
        for call_id in completed_calls:
            del self.active_calls[call_id]
            if call_id in self.dashboard_metrics:
                del self.dashboard_metrics[call_id]
            if call_id in self.metrics_calculator.metric_history:
                del self.metrics_calculator.metric_history[call_id]
        
        logger.info(f"Cleaned up {len(completed_calls)} completed calls")


# FastAPI integration for dashboard endpoints
def create_dashboard_app(dashboard: SalesIntelligenceDashboard) -> FastAPI:
    """Create FastAPI app with dashboard endpoints"""
    
    app = FastAPI(title="Sales Intelligence Dashboard", version="1.0.0")
    
    @app.websocket("/ws/{call_id}")
    async def websocket_endpoint(websocket: WebSocket, call_id: str):
        """WebSocket endpoint for real-time call updates"""
        await dashboard.websocket_manager.connect(websocket, call_id)
        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "subscribe_call":
                    # Already subscribed during connect
                    pass
                elif message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
        except WebSocketDisconnect:
            dashboard.websocket_manager.disconnect(websocket)
    
    @app.websocket("/ws")
    async def websocket_general(websocket: WebSocket):
        """WebSocket endpoint for general dashboard updates"""
        await dashboard.websocket_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
        except WebSocketDisconnect:
            dashboard.websocket_manager.disconnect(websocket)
    
    @app.get("/api/dashboard/call/{call_id}")
    async def get_call_dashboard(call_id: str):
        """Get dashboard data for specific call"""
        return dashboard.get_call_dashboard_data(call_id)
    
    @app.get("/api/dashboard/team")
    async def get_team_dashboard():
        """Get team dashboard data"""
        return dashboard.get_team_dashboard_data()
    
    @app.get("/api/dashboard/platforms")
    async def get_platform_data():
        """Get live platform data"""
        try:
            platform_data = await get_unified_data()
            dashboard.platform_data = platform_data  # Update cached data
            
            return {
                "success": True,
                "data": {
                    "total_records": platform_data.total_records,
                    "connected_platforms": platform_data.connected_platforms,
                    "last_sync": platform_data.last_sync.isoformat() if platform_data.last_sync else None,
                    "platforms": {
                        name: {
                            "enabled": bool(getattr(platform_data, name)),
                            "count": getattr(platform_data, name).count if getattr(platform_data, name) else 0,
                            "type": getattr(platform_data, name).data_type if getattr(platform_data, name) else "unknown",
                            "last_updated": getattr(platform_data, name).last_updated.isoformat() if getattr(platform_data, name) else None,
                            "metadata": getattr(platform_data, name).metadata if getattr(platform_data, name) else {}
                        }
                        for name in ["gong", "asana", "linear", "notion", "hubspot"]
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error fetching platform data: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    @app.get("/api/dashboard/metrics/{call_id}")
    async def get_call_metrics(call_id: str, metric_type: Optional[str] = None):
        """Get metrics for specific call"""
        metrics = dashboard.dashboard_metrics.get(call_id, [])
        
        if metric_type:
            metrics = [m for m in metrics if m.metric_type.value == metric_type]
        
        return {
            "call_id": call_id,
            "metrics": [asdict(metric) for metric in metrics],
            "count": len(metrics)
        }
    
    @app.get("/dashboard")
    async def dashboard_html():
        """Serve dashboard HTML"""
        return HTMLResponse(content=get_dashboard_html(), status_code=200)
    
    return app


def get_dashboard_html() -> str:
    """Get dashboard HTML template"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sales Intelligence Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
            }
            .dashboard {
                max-width: 1400px;
                margin: 0 auto;
            }
            .header {
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            .metric-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 4px solid #007bff;
            }
            .metric-card.green { border-left-color: #28a745; }
            .metric-card.yellow { border-left-color: #ffc107; }
            .metric-card.red { border-left-color: #dc3545; }
            .metric-value {
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .metric-label {
                color: #666;
                font-size: 0.9em;
            }
            .platform-summary {
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .platform-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            .platform-card {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                border-left: 3px solid #28a745;
                text-align: center;
            }
            .platform-card.disabled {
                border-left-color: #dc3545;
                opacity: 0.6;
            }
            .platform-name {
                font-weight: bold;
                font-size: 1.1em;
                margin-bottom: 5px;
                text-transform: capitalize;
            }
            .platform-count {
                font-size: 1.8em;
                font-weight: bold;
                color: #007bff;
                margin: 5px 0;
            }
            .platform-type {
                font-size: 0.9em;
                color: #666;
            }
            .calls-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }
            .call-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .call-title {
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .risk-badge {
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.8em;
                color: white;
            }
            .risk-low { background: #28a745; }
            .risk-medium { background: #ffc107; color: black; }
            .risk-high { background: #fd7e14; }
            .risk-critical { background: #dc3545; }
            .insights {
                margin-top: 10px;
            }
            .insight {
                background: #f8f9fa;
                padding: 8px;
                margin: 4px 0;
                border-radius: 4px;
                font-size: 0.9em;
            }
            .status-online {
                display: inline-block;
                width: 10px;
                height: 10px;
                background: #28a745;
                border-radius: 50%;
                margin-right: 5px;
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <h1>Sales Intelligence Dashboard</h1>
                <p>Real-time call analytics and coaching insights</p>
                <div class="status-online"></div>
                <span id="status">Connected</span>
            </div>
            
            <div class="metrics-grid" id="metrics-grid">
                <!-- Metrics will be populated by JavaScript -->
            </div>
            
            <div class="platform-summary" id="platform-summary">
                <h3>Connected Platforms</h3>
                <div class="platform-grid" id="platform-grid">
                    <!-- Platform data will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="calls-grid" id="calls-grid">
                <!-- Calls will be populated by JavaScript -->
            </div>
        </div>
        
        <script>
            class SalesDashboard {
                constructor() {
                    this.ws = null;
                    this.reconnectAttempts = 0;
                    this.maxReconnectAttempts = 5;
                    this.init();
                }
                
                init() {
                    this.connect();
                    this.loadInitialData();
                    this.loadPlatformData();
                }
                
                connect() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/ws`;
                    
                    this.ws = new WebSocket(wsUrl);
                    
                    this.ws.onopen = () => {
                        console.log('WebSocket connected');
                        document.getElementById('status').textContent = 'Connected';
                        this.reconnectAttempts = 0;
                    };
                    
                    this.ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    };
                    
                    this.ws.onclose = () => {
                        console.log('WebSocket disconnected');
                        document.getElementById('status').textContent = 'Disconnected';
                        this.reconnect();
                    };
                    
                    this.ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                    };
                }
                
                reconnect() {
                    if (this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.reconnectAttempts++;
                        setTimeout(() => {
                            console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                            this.connect();
                        }, 3000 * this.reconnectAttempts);
                    }
                }
                
                handleMessage(data) {
                    switch(data.type) {
                        case 'global_metrics_update':
                            this.updateMetrics(data.data);
                            break;
                        case 'feedback_alert':
                            this.showAlert(data);
                            break;
                    }
                }
                
                async loadInitialData() {
                    try {
                        const response = await fetch('/api/dashboard/team');
                        const data = await response.json();
                        this.renderTeamDashboard(data);
                    } catch (error) {
                        console.error('Error loading initial data:', error);
                    }
                }
                
                async loadPlatformData() {
                    try {
                        const response = await fetch('/api/dashboard/platforms');
                        const result = await response.json();
                        
                        if (result.success && result.data) {
                            this.renderPlatformData(result.data);
                        } else {
                            console.error('Platform data error:', result.error);
                        }
                    } catch (error) {
                        console.error('Error loading platform data:', error);
                    }
                }
                
                renderPlatformData(data) {
                    const platformGrid = document.getElementById('platform-grid');
                    
                    const platforms = ['gong', 'asana', 'linear', 'notion', 'hubspot'];
                    
                    platformGrid.innerHTML = platforms.map(platform => {
                        const platformData = data.platforms[platform];
                        const isEnabled = platformData.enabled;
                        
                        return `
                            <div class="platform-card ${isEnabled ? '' : 'disabled'}">
                                <div class="platform-name">${platform}</div>
                                <div class="platform-count">${platformData.count}</div>
                                <div class="platform-type">${platformData.type}</div>
                            </div>
                        `;
                    }).join('');
                    
                    // Update header with sync info
                    if (data.last_sync) {
                        const syncTime = new Date(data.last_sync).toLocaleTimeString();
                        document.querySelector('.platform-summary h3').textContent = 
                            `Connected Platforms (${data.connected_platforms}/5) - Last sync: ${syncTime}`;
                    }
                }
                
                renderTeamDashboard(data) {
                    const metricsGrid = document.getElementById('metrics-grid');
                    const callsGrid = document.getElementById('calls-grid');
                    
                    // Render team metrics
                    metricsGrid.innerHTML = `
                        <div class="metric-card">
                            <div class="metric-value">${data.team_summary.total_active_calls}</div>
                            <div class="metric-label">Active Calls</div>
                        </div>
                        <div class="metric-card ${data.team_summary.high_risk_calls > 0 ? 'red' : 'green'}">
                            <div class="metric-value">${data.team_summary.high_risk_calls}</div>
                            <div class="metric-label">High Risk Calls</div>
                        </div>
                        <div class="metric-card ${this.getSentimentColor(data.team_summary.average_sentiment)}">
                            <div class="metric-value">${data.team_summary.average_sentiment.toFixed(2)}</div>
                            <div class="metric-label">Average Sentiment</div>
                        </div>
                    `;
                    
                    // Render active calls
                    callsGrid.innerHTML = data.active_calls.map(call => `
                        <div class="call-card">
                            <div class="call-title">${call.title}</div>
                            <span class="risk-badge risk-${call.risk_level}">${call.risk_level.toUpperCase()}</span>
                            <p>Sentiment: ${call.sentiment_score.toFixed(2)}</p>
                            <p>Participants: ${call.participants.length}</p>
                            <div class="insights">
                                ${call.key_insights.map(insight => 
                                    `<div class="insight">${insight}</div>`
                                ).join('')}
                            </div>
                        </div>
                    `).join('');
                }
                
                getSentimentColor(sentiment) {
                    if (sentiment >= 0.2) return 'green';
                    if (sentiment >= -0.2) return 'yellow';
                    return 'red';
                }
                
                showAlert(alertData) {
                    // Simple alert implementation
                    const alert = document.createElement('div');
                    alert.style.cssText = `
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: #fff;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 16px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                        z-index: 1000;
                        max-width: 300px;
                    `;
                    alert.innerHTML = `
                        <h4>${alertData.feedback.title}</h4>
                        <p>${alertData.feedback.message}</p>
                    `;
                    
                    document.body.appendChild(alert);
                    
                    setTimeout(() => {
                        document.body.removeChild(alert);
                    }, 5000);
                }
            }
            
            // Initialize dashboard
            new SalesDashboard();
        </script>
    </body>
    </html>
    """


# Example usage
async def example_dashboard_usage():
    """Example of how to use the dashboard system"""
    
    from .agents import AgentOutput, AgentPriority, ConfidenceLevel
    
    # Create dashboard
    dashboard = SalesIntelligenceDashboard()
    await dashboard.initialize()
    
    # Simulate agent outputs
    outputs = [
        AgentOutput(
            agent_id="sentiment_1",
            agent_type="sentiment",
            call_id="demo_call_123",
            timestamp=datetime.now(),
            priority=AgentPriority.MEDIUM,
            confidence=ConfidenceLevel.HIGH,
            data={"overall_sentiment": 0.3, "engagement_level": 0.8}
        ),
        AgentOutput(
            agent_id="risk_1",
            agent_type="risk_assessment",
            call_id="demo_call_123",
            timestamp=datetime.now(),
            priority=AgentPriority.HIGH,
            confidence=ConfidenceLevel.HIGH,
            data={"overall_risk_score": 0.75, "red_flags": ["budget_concerns"]}
        )
    ]
    
    # Process outputs
    for output in outputs:
        await dashboard.process_agent_output(output)
    
    # Get dashboard data
    call_data = dashboard.get_call_dashboard_data("demo_call_123")
    team_data = dashboard.get_team_dashboard_data()
    
    print(f"Call dashboard data: {json.dumps(call_data, indent=2, default=str)}")
    print(f"Team dashboard data: {json.dumps(team_data, indent=2, default=str)}")


if __name__ == "__main__":
    asyncio.run(example_dashboard_usage())