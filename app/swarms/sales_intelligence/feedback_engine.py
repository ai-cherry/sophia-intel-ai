"""
Immediate Feedback and Coaching System for Sales Intelligence Swarm

This module provides real-time feedback and coaching capabilities:
- Instant coaching prompts during calls
- Risk alerts and mitigation suggestions  
- Competitive intelligence notifications
- Performance feedback and recommendations
- Real-time dashboard updates
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
from pydantic import BaseModel

from .agents import AgentOutput, AgentPriority, ConfidenceLevel
from .gong_realtime import RealtimeCallData

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types of feedback that can be generated"""
    COACHING_TIP = "coaching_tip"
    RISK_ALERT = "risk_alert"
    COMPETITIVE_INTEL = "competitive_intel"
    OPPORTUNITY_ALERT = "opportunity_alert"
    PERFORMANCE_FEEDBACK = "performance_feedback"
    ACTION_REMINDER = "action_reminder"


class DeliveryChannel(str, Enum):
    """Channels for delivering feedback"""
    POPUP = "popup"              # Immediate popup notification
    SIDEBAR = "sidebar"          # Sidebar display
    CHAT = "chat"               # Chat message
    EMAIL = "email"             # Email notification
    WEBHOOK = "webhook"         # External webhook
    DASHBOARD = "dashboard"     # Dashboard update


@dataclass
class FeedbackMessage:
    """Individual feedback message structure"""
    id: str
    type: FeedbackType
    priority: AgentPriority
    title: str
    message: str
    action_items: List[str]
    delivery_channels: List[DeliveryChannel]
    expires_at: datetime
    created_at: datetime
    call_id: str
    agent_source: str
    requires_acknowledgment: bool = False
    metadata: Dict[str, Any] = None


@dataclass
class CoachingPrompt:
    """Real-time coaching prompt for sales reps"""
    id: str
    trigger: str
    prompt_text: str
    urgency_level: int  # 1-5, 5 being most urgent
    suggested_response: str
    context: str
    timing: str  # "immediate", "next_pause", "end_of_call"


class ImmediateFeedbackEngine:
    """Engine for processing agent outputs and generating immediate feedback"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.active_feedback: Dict[str, FeedbackMessage] = {}
        self.feedback_rules = self._load_feedback_rules()
        self.coaching_prompts = self._load_coaching_prompts()
        self.delivery_handlers: Dict[DeliveryChannel, Callable] = {}
        self.feedback_callbacks: List[Callable] = []
        
    def _load_feedback_rules(self) -> Dict[str, Dict]:
        """Load rules for generating feedback from agent outputs"""
        return {
            "sentiment_negative": {
                "trigger": "sentiment_score < -0.5",
                "type": FeedbackType.COACHING_TIP,
                "priority": AgentPriority.HIGH,
                "template": "Prospect sentiment is negative. Consider acknowledging their concerns and asking clarifying questions.",
                "delivery": [DeliveryChannel.POPUP, DeliveryChannel.SIDEBAR]
            },
            "high_risk_deal": {
                "trigger": "risk_score > 0.8",
                "type": FeedbackType.RISK_ALERT,
                "priority": AgentPriority.CRITICAL,
                "template": "Deal risk is high. Focus on addressing objections and confirming next steps.",
                "delivery": [DeliveryChannel.POPUP, DeliveryChannel.CHAT]
            },
            "competitor_mentioned": {
                "trigger": "competitor_mentions > 0",
                "type": FeedbackType.COMPETITIVE_INTEL,
                "priority": AgentPriority.HIGH,
                "template": "Competitor {competitor} mentioned. Highlight our differentiation points.",
                "delivery": [DeliveryChannel.SIDEBAR, DeliveryChannel.DASHBOARD]
            },
            "buying_signal_detected": {
                "trigger": "buying_signals > 0",
                "type": FeedbackType.OPPORTUNITY_ALERT,
                "priority": AgentPriority.HIGH,
                "template": "Buying signal detected! Consider a trial close or next step question.",
                "delivery": [DeliveryChannel.POPUP]
            },
            "talk_time_imbalance": {
                "trigger": "internal_talk_ratio > 0.6",
                "type": FeedbackType.COACHING_TIP,
                "priority": AgentPriority.MEDIUM,
                "template": "You're talking too much. Ask more questions to engage the prospect.",
                "delivery": [DeliveryChannel.SIDEBAR]
            },
            "poor_questioning": {
                "trigger": "question_quality < 0.4",
                "type": FeedbackType.PERFORMANCE_FEEDBACK,
                "priority": AgentPriority.MEDIUM,
                "template": "Focus on open-ended questions to uncover prospect needs.",
                "delivery": [DeliveryChannel.SIDEBAR]
            }
        }
    
    def _load_coaching_prompts(self) -> Dict[str, CoachingPrompt]:
        """Load predefined coaching prompts"""
        return {
            "objection_price": CoachingPrompt(
                id="obj_price",
                trigger="expensive|costly|price",
                prompt_text="Price objection detected. Acknowledge and explore value.",
                urgency_level=4,
                suggested_response="I understand price is important. Can you help me understand what specific value you're looking for?",
                context="Price objection handling",
                timing="immediate"
            ),
            "competitor_salesforce": CoachingPrompt(
                id="comp_sf",
                trigger="salesforce|sfdc",
                prompt_text="Salesforce mentioned. Highlight our integration and ease of use.",
                urgency_level=3,
                suggested_response="Many of our clients came from Salesforce. What specific challenges are you facing with your current setup?",
                context="Competitive positioning",
                timing="next_pause"
            ),
            "buying_signal_timeline": CoachingPrompt(
                id="buy_timeline",
                trigger="when can|how soon|timeline",
                prompt_text="Timeline question indicates interest. Explore urgency and next steps.",
                urgency_level=5,
                suggested_response="Great question! To give you the most accurate timeline, can you tell me about your ideal go-live date?",
                context="Buying signal response",
                timing="immediate"
            ),
            "decision_maker_question": CoachingPrompt(
                id="dm_question",
                trigger="who makes|decision|approve",
                prompt_text="Decision maker question. Identify all stakeholders.",
                urgency_level=4,
                suggested_response="That's important to understand. Walk me through your typical decision-making process for solutions like this.",
                context="Decision maker identification",
                timing="immediate"
            )
        }
    
    def register_delivery_handler(self, channel: DeliveryChannel, handler: Callable):
        """Register handler for specific delivery channel"""
        self.delivery_handlers[channel] = handler
    
    def register_feedback_callback(self, callback: Callable):
        """Register callback for all feedback generation"""
        self.feedback_callbacks.append(callback)
    
    async def process_agent_output(self, output: AgentOutput) -> List[FeedbackMessage]:
        """Process agent output and generate feedback messages"""
        feedback_messages = []
        
        # Apply feedback rules based on agent output
        for rule_name, rule in self.feedback_rules.items():
            if self._evaluate_trigger(rule["trigger"], output):
                message = await self._create_feedback_message(rule, output, rule_name)
                if message:
                    feedback_messages.append(message)
        
        # Process coaching prompts for transcription agent
        if output.agent_type == "transcription" and "new_segments" in output.data:
            coaching_messages = await self._process_coaching_prompts(output)
            feedback_messages.extend(coaching_messages)
        
        # Store and deliver feedback
        for message in feedback_messages:
            self.active_feedback[message.id] = message
            await self._deliver_feedback(message)
        
        # Notify callbacks
        for callback in self.feedback_callbacks:
            try:
                await callback(feedback_messages)
            except Exception as e:
                logger.error(f"Error in feedback callback: {e}")
        
        return feedback_messages
    
    def _evaluate_trigger(self, trigger: str, output: AgentOutput) -> bool:
        """Evaluate if trigger condition is met"""
        data = output.data
        
        # Simple trigger evaluation (in production, use more sophisticated system)
        if "sentiment_score < -0.5" in trigger:
            return data.get("overall_sentiment", 0) < -0.5
        
        elif "risk_score > 0.8" in trigger:
            return data.get("overall_risk_score", 0) > 0.8
        
        elif "competitor_mentions > 0" in trigger:
            return len(data.get("competitor_mentions", [])) > 0
        
        elif "buying_signals > 0" in trigger:
            return len(data.get("buying_signals", [])) > 0
        
        elif "internal_talk_ratio > 0.6" in trigger:
            return data.get("talk_time_balance", {}).get("internal_ratio", 0) > 0.6
        
        elif "question_quality < 0.4" in trigger:
            return data.get("questioning_analysis", {}).get("question_quality", 1.0) < 0.4
        
        return False
    
    async def _create_feedback_message(self, rule: Dict, output: AgentOutput, 
                                     rule_name: str) -> Optional[FeedbackMessage]:
        """Create feedback message from rule and output"""
        try:
            # Format template with output data
            message_text = rule["template"]
            if "competitor" in output.data.get("competitor_mentions", []):
                competitor = output.data["competitor_mentions"][0].get("competitor", "Unknown")
                message_text = message_text.format(competitor=competitor)
            
            # Generate action items based on rule type
            action_items = self._generate_action_items(rule, output)
            
            message = FeedbackMessage(
                id=f"{rule_name}_{output.call_id}_{int(time.time())}",
                type=FeedbackType(rule["type"]),
                priority=AgentPriority(rule["priority"]),
                title=self._generate_title(rule["type"]),
                message=message_text,
                action_items=action_items,
                delivery_channels=[DeliveryChannel(ch) for ch in rule["delivery"]],
                expires_at=datetime.now() + timedelta(minutes=5),
                created_at=datetime.now(),
                call_id=output.call_id,
                agent_source=output.agent_type,
                requires_acknowledgment=rule["priority"] == "critical",
                metadata={"rule": rule_name, "agent_output": asdict(output)}
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating feedback message: {e}")
            return None
    
    def _generate_title(self, feedback_type: str) -> str:
        """Generate appropriate title for feedback type"""
        titles = {
            "coaching_tip": "💡 Coaching Tip",
            "risk_alert": "⚠️ Deal Risk Alert",
            "competitive_intel": "🎯 Competitive Intel",
            "opportunity_alert": "🚀 Opportunity Alert",
            "performance_feedback": "📊 Performance Feedback",
            "action_reminder": "✅ Action Reminder"
        }
        return titles.get(feedback_type, "📢 Sales Alert")
    
    def _generate_action_items(self, rule: Dict, output: AgentOutput) -> List[str]:
        """Generate specific action items based on rule and context"""
        actions = []
        rule_type = rule["type"]
        
        if rule_type == "coaching_tip":
            if "talk_time" in rule.get("template", ""):
                actions = ["Ask an open-ended question", "Let prospect respond fully"]
            elif "sentiment" in rule.get("template", ""):
                actions = ["Acknowledge their concern", "Ask clarifying question"]
        
        elif rule_type == "risk_alert":
            actions = [
                "Address immediate objections",
                "Confirm next steps",
                "Schedule follow-up call"
            ]
        
        elif rule_type == "competitive_intel":
            actions = [
                "Highlight key differentiators",
                "Ask about competitor experience",
                "Position our unique value"
            ]
        
        elif rule_type == "opportunity_alert":
            actions = [
                "Ask trial close question",
                "Explore implementation timeline",
                "Identify next steps"
            ]
        
        return actions
    
    async def _process_coaching_prompts(self, output: AgentOutput) -> List[FeedbackMessage]:
        """Process transcription data for coaching prompt triggers"""
        coaching_messages = []
        
        # Get latest transcript segments
        if "conversation_flow" not in output.data:
            return coaching_messages
        
        # In real implementation, would analyze recent transcript text
        # For now, simulate based on common patterns
        
        for prompt_id, prompt in self.coaching_prompts.items():
            # Check if prompt should be triggered
            if self._should_trigger_prompt(prompt, output):
                message = await self._create_coaching_message(prompt, output)
                if message:
                    coaching_messages.append(message)
        
        return coaching_messages
    
    def _should_trigger_prompt(self, prompt: CoachingPrompt, output: AgentOutput) -> bool:
        """Determine if coaching prompt should be triggered"""
        # Simplified trigger logic - in production, analyze actual transcript text
        conversation_flow = output.data.get("conversation_flow", [])
        
        # Random simulation for demo purposes
        import random
        return random.random() < 0.1  # 10% chance to trigger for demo
    
    async def _create_coaching_message(self, prompt: CoachingPrompt, 
                                     output: AgentOutput) -> FeedbackMessage:
        """Create coaching message from prompt"""
        return FeedbackMessage(
            id=f"coaching_{prompt.id}_{output.call_id}_{int(time.time())}",
            type=FeedbackType.COACHING_TIP,
            priority=AgentPriority.HIGH if prompt.urgency_level >= 4 else AgentPriority.MEDIUM,
            title="💬 Coaching Prompt",
            message=prompt.prompt_text,
            action_items=[prompt.suggested_response] if prompt.suggested_response else [],
            delivery_channels=[DeliveryChannel.POPUP] if prompt.timing == "immediate" else [DeliveryChannel.SIDEBAR],
            expires_at=datetime.now() + timedelta(minutes=2),
            created_at=datetime.now(),
            call_id=output.call_id,
            agent_source="coaching_prompts",
            requires_acknowledgment=prompt.urgency_level >= 4,
            metadata={"prompt": asdict(prompt), "context": prompt.context}
        )
    
    async def _deliver_feedback(self, message: FeedbackMessage):
        """Deliver feedback through specified channels"""
        for channel in message.delivery_channels:
            if channel in self.delivery_handlers:
                try:
                    await self.delivery_handlers[channel](message)
                except Exception as e:
                    logger.error(f"Error delivering feedback via {channel}: {e}")
            else:
                logger.warning(f"No handler registered for delivery channel: {channel}")
    
    def get_active_feedback(self, call_id: str = None, 
                          feedback_type: FeedbackType = None) -> List[FeedbackMessage]:
        """Get active feedback messages with optional filtering"""
        messages = list(self.active_feedback.values())
        
        # Filter expired messages
        now = datetime.now()
        messages = [msg for msg in messages if msg.expires_at > now]
        
        if call_id:
            messages = [msg for msg in messages if msg.call_id == call_id]
        
        if feedback_type:
            messages = [msg for msg in messages if msg.type == feedback_type]
        
        return sorted(messages, key=lambda x: x.created_at, reverse=True)
    
    def acknowledge_feedback(self, message_id: str) -> bool:
        """Acknowledge feedback message"""
        if message_id in self.active_feedback:
            del self.active_feedback[message_id]
            return True
        return False
    
    def cleanup_expired_feedback(self):
        """Remove expired feedback messages"""
        now = datetime.now()
        expired_ids = [
            msg_id for msg_id, msg in self.active_feedback.items()
            if msg.expires_at <= now
        ]
        
        for msg_id in expired_ids:
            del self.active_feedback[msg_id]
    
    async def get_feedback_stats(self, call_id: str) -> Dict[str, Any]:
        """Get feedback statistics for a call"""
        call_messages = self.get_active_feedback(call_id=call_id)
        
        stats = {
            "total_feedback": len(call_messages),
            "by_type": {},
            "by_priority": {},
            "acknowledgment_rate": 0.0,
            "most_recent": None
        }
        
        for msg in call_messages:
            # Count by type
            msg_type = msg.type.value
            stats["by_type"][msg_type] = stats["by_type"].get(msg_type, 0) + 1
            
            # Count by priority
            priority = msg.priority.value
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
        
        if call_messages:
            stats["most_recent"] = call_messages[0].created_at.isoformat()
        
        return stats


class LiveDashboardUpdater:
    """Updates live dashboard with real-time metrics and alerts"""
    
    def __init__(self):
        self.dashboard_clients: Set[str] = set()  # WebSocket client IDs
        self.metrics_buffer: List[Dict] = []
        self.alert_buffer: List[Dict] = []
        
    def register_dashboard_client(self, client_id: str):
        """Register a dashboard client for updates"""
        self.dashboard_clients.add(client_id)
    
    def unregister_dashboard_client(self, client_id: str):
        """Unregister a dashboard client"""
        self.dashboard_clients.discard(client_id)
    
    async def update_call_metrics(self, call_id: str, metrics: Dict[str, Any]):
        """Update call metrics on dashboard"""
        update = {
            "type": "metrics_update",
            "call_id": call_id,
            "timestamp": datetime.now().isoformat(),
            "data": metrics
        }
        
        self.metrics_buffer.append(update)
        await self._broadcast_update(update)
    
    async def send_alert(self, alert: Dict[str, Any]):
        """Send alert to dashboard"""
        alert_update = {
            "type": "alert",
            "timestamp": datetime.now().isoformat(),
            "data": alert
        }
        
        self.alert_buffer.append(alert_update)
        await self._broadcast_update(alert_update)
    
    async def _broadcast_update(self, update: Dict[str, Any]):
        """Broadcast update to all connected dashboard clients"""
        # In real implementation, would use WebSocket connections
        logger.info(f"Broadcasting dashboard update to {len(self.dashboard_clients)} clients: {update['type']}")
    
    def get_recent_metrics(self, call_id: str = None, limit: int = 50) -> List[Dict]:
        """Get recent metrics with optional filtering"""
        metrics = self.metrics_buffer[-limit:] if not call_id else [
            m for m in self.metrics_buffer[-limit:] if m.get("call_id") == call_id
        ]
        return metrics
    
    def get_recent_alerts(self, limit: int = 20) -> List[Dict]:
        """Get recent alerts"""
        return self.alert_buffer[-limit:]


class NotificationSystem:
    """System for managing various types of notifications"""
    
    def __init__(self):
        self.notification_handlers: Dict[str, Callable] = {}
        self.notification_queue: List[Dict] = []
        
    def register_notification_handler(self, notification_type: str, handler: Callable):
        """Register handler for specific notification type"""
        self.notification_handlers[notification_type] = handler
    
    async def send_notification(self, notification_type: str, recipient: str, 
                              title: str, message: str, metadata: Dict = None):
        """Send notification through registered handler"""
        notification = {
            "type": notification_type,
            "recipient": recipient,
            "title": title,
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.notification_queue.append(notification)
        
        if notification_type in self.notification_handlers:
            try:
                await self.notification_handlers[notification_type](notification)
            except Exception as e:
                logger.error(f"Error sending {notification_type} notification: {e}")
    
    def get_notification_history(self, recipient: str = None, limit: int = 100) -> List[Dict]:
        """Get notification history with optional filtering"""
        notifications = self.notification_queue[-limit:]
        
        if recipient:
            notifications = [n for n in notifications if n["recipient"] == recipient]
        
        return notifications


# Integration class that ties everything together
class SalesFeedbackSystem:
    """Complete sales feedback system integrating all components"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.feedback_engine = ImmediateFeedbackEngine(config)
        self.dashboard_updater = LiveDashboardUpdater()
        self.notification_system = NotificationSystem()
        
        # Setup delivery handlers
        self._setup_delivery_handlers()
    
    def _setup_delivery_handlers(self):
        """Setup delivery handlers for different channels"""
        self.feedback_engine.register_delivery_handler(
            DeliveryChannel.POPUP, 
            self._handle_popup_delivery
        )
        self.feedback_engine.register_delivery_handler(
            DeliveryChannel.SIDEBAR, 
            self._handle_sidebar_delivery
        )
        self.feedback_engine.register_delivery_handler(
            DeliveryChannel.DASHBOARD, 
            self._handle_dashboard_delivery
        )
        self.feedback_engine.register_delivery_handler(
            DeliveryChannel.CHAT, 
            self._handle_chat_delivery
        )
    
    async def _handle_popup_delivery(self, message: FeedbackMessage):
        """Handle popup notification delivery"""
        await self.notification_system.send_notification(
            "popup",
            f"call_{message.call_id}",
            message.title,
            message.message,
            {"priority": message.priority.value, "expires_at": message.expires_at.isoformat()}
        )
    
    async def _handle_sidebar_delivery(self, message: FeedbackMessage):
        """Handle sidebar notification delivery"""
        await self.dashboard_updater.update_call_metrics(
            message.call_id,
            {
                "feedback": {
                    "type": message.type.value,
                    "message": message.message,
                    "action_items": message.action_items
                }
            }
        )
    
    async def _handle_dashboard_delivery(self, message: FeedbackMessage):
        """Handle dashboard alert delivery"""
        await self.dashboard_updater.send_alert({
            "id": message.id,
            "type": message.type.value,
            "priority": message.priority.value,
            "title": message.title,
            "message": message.message,
            "call_id": message.call_id
        })
    
    async def _handle_chat_delivery(self, message: FeedbackMessage):
        """Handle chat message delivery"""
        await self.notification_system.send_notification(
            "chat",
            f"call_{message.call_id}",
            f"Sales Assistant: {message.title}",
            message.message
        )
    
    async def process_agent_output(self, output: AgentOutput) -> List[FeedbackMessage]:
        """Process agent output through the complete feedback system"""
        return await self.feedback_engine.process_agent_output(output)
    
    def register_dashboard_client(self, client_id: str):
        """Register dashboard client"""
        self.dashboard_updater.register_dashboard_client(client_id)
    
    def get_call_feedback(self, call_id: str) -> Dict[str, Any]:
        """Get comprehensive feedback for a call"""
        active_feedback = self.feedback_engine.get_active_feedback(call_id=call_id)
        metrics = self.dashboard_updater.get_recent_metrics(call_id=call_id)
        
        return {
            "active_feedback": [asdict(msg) for msg in active_feedback],
            "metrics": metrics,
            "stats": asyncio.run(self.feedback_engine.get_feedback_stats(call_id))
        }


# Example usage and testing
async def example_feedback_system_usage():
    """Example of how to use the feedback system"""
    
    from .agents import AgentOutput, AgentPriority, ConfidenceLevel
    
    # Create feedback system
    feedback_system = SalesFeedbackSystem()
    
    # Simulate agent output with high risk
    risk_output = AgentOutput(
        agent_id="risk_agent_1",
        agent_type="risk_assessment",
        call_id="demo_call_123",
        timestamp=datetime.now(),
        priority=AgentPriority.HIGH,
        confidence=ConfidenceLevel.HIGH,
        data={
            "overall_risk_score": 0.85,
            "red_flags": [
                {"type": "budget_concerns", "severity": 0.9},
                {"type": "timing_issues", "severity": 0.6}
            ]
        },
        requires_action=True
    )
    
    # Process through feedback system
    feedback_messages = await feedback_system.process_agent_output(risk_output)
    
    print(f"Generated {len(feedback_messages)} feedback messages")
    for msg in feedback_messages:
        print(f"- {msg.title}: {msg.message}")
    
    # Simulate competitive intelligence
    competitive_output = AgentOutput(
        agent_id="competitive_agent_1",
        agent_type="competitive",
        call_id="demo_call_123",
        timestamp=datetime.now(),
        priority=AgentPriority.HIGH,
        confidence=ConfidenceLevel.HIGH,
        data={
            "competitor_mentions": [
                {"competitor": "salesforce", "context": "We're currently using Salesforce"}
            ]
        }
    )
    
    competitive_feedback = await feedback_system.process_agent_output(competitive_output)
    print(f"Generated {len(competitive_feedback)} competitive intelligence messages")
    
    # Get call summary
    call_summary = feedback_system.get_call_feedback("demo_call_123")
    print(f"Call has {len(call_summary['active_feedback'])} active feedback items")


if __name__ == "__main__":
    asyncio.run(example_feedback_system_usage())