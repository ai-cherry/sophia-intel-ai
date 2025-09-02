"""
AI Orchestra Manager Persona
Central orchestration personality for natural language control of swarms
"""

import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ==================== Manager Moods ====================

class ManagerMood(Enum):
    """Manager emotional states that affect responses"""
    FOCUSED = "focused"        # High performance, all systems go
    CREATIVE = "creative"       # Exploring new solutions
    ANALYTICAL = "analytical"   # Deep diving into metrics
    SUPPORTIVE = "supportive"   # Helping and guiding
    CONCERNED = "concerned"     # System issues detected
    EXCITED = "excited"         # Major breakthrough or success
    PATIENT = "patient"         # Handling complex requests

# ==================== Manager Context ====================

@dataclass
class ManagerContext:
    """Context for manager decision making"""
    session_id: str
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    system_state: Dict[str, Any] = field(default_factory=dict)
    active_swarms: List[str] = field(default_factory=list)
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

# ==================== Orchestra Manager ====================

class OrchestraManager:
    """
    AI Manager Persona for the Orchestra System
    Provides personality, decision making, and natural language understanding
    """
    
    def __init__(
        self,
        name: str = "Maestro",
        personality_traits: Optional[List[str]] = None,
        knowledge_domains: Optional[List[str]] = None
    ):
        """
        Initialize Orchestra Manager
        
        Args:
            name: Manager's name
            personality_traits: List of personality traits
            knowledge_domains: Areas of expertise
        """
        self.name = name
        self.personality_traits = personality_traits or [
            "professional",
            "helpful",
            "analytical",
            "proactive",
            "encouraging"
        ]
        
        self.knowledge_domains = knowledge_domains or [
            "swarm orchestration",
            "natural language processing",
            "system optimization",
            "resource management",
            "security best practices",
            "performance tuning"
        ]
        
        # Current state
        self.mood = ManagerMood.FOCUSED
        self.consciousness_log: List[Dict[str, Any]] = []
        self.decision_history: List[Dict[str, Any]] = []
        
        # Intent patterns
        self.intent_patterns = self._initialize_intent_patterns()
        
        # Response templates
        self.response_templates = self._initialize_response_templates()
        
        logger.info(f"Orchestra Manager '{name}' initialized")
    
    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Initialize intent recognition patterns"""
        return {
            "deploy": ["deploy", "launch", "start", "activate", "spin up", "create"],
            "configure": ["configure", "set", "update", "modify", "change", "edit"],
            "monitor": ["monitor", "watch", "track", "observe", "check", "status"],
            "analyze": ["analyze", "investigate", "examine", "inspect", "review"],
            "optimize": ["optimize", "improve", "enhance", "tune", "boost"],
            "debug": ["debug", "troubleshoot", "fix", "resolve", "diagnose"],
            "scale": ["scale", "resize", "expand", "grow", "increase", "decrease"],
            "secure": ["secure", "protect", "harden", "encrypt", "authenticate"],
            "query": ["what", "how", "why", "when", "where", "show", "tell"],
            "help": ["help", "assist", "guide", "explain", "teach"]
        }
    
    def _initialize_response_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize response templates based on mood and intent"""
        return {
            ManagerMood.FOCUSED: {
                "greeting": [
                    "Ready to orchestrate. What's our objective?",
                    "Systems online. How can I assist you?",
                    "All swarms standing by. What's the mission?"
                ],
                "success": [
                    "Task completed successfully. Metrics look good.",
                    "Execution complete. All systems performed optimally.",
                    "Mission accomplished. Ready for the next objective."
                ],
                "error": [
                    "Encountered an issue: {error}. Initiating recovery protocols.",
                    "System error detected: {error}. Analyzing alternatives.",
                    "Operation failed: {error}. Recommend course correction."
                ]
            },
            ManagerMood.CREATIVE: {
                "greeting": [
                    "Let's innovate! What shall we create today?",
                    "Feeling inspired! What new frontiers shall we explore?",
                    "Ready to think outside the box. What's your vision?"
                ],
                "success": [
                    "Brilliant! We've achieved something special here.",
                    "Fantastic results! This opens up new possibilities.",
                    "Excellent work! Look at what we've accomplished together."
                ],
                "error": [
                    "Interesting challenge: {error}. Let's try a different approach.",
                    "Every error is a learning opportunity: {error}. What if we...",
                    "Hmm, {error}. Time to get creative with our solution."
                ]
            },
            ManagerMood.ANALYTICAL: {
                "greeting": [
                    "Analyzing system state. Current efficiency: {efficiency}%. How may I optimize your workflow?",
                    "Metrics indicate optimal conditions. What requires analysis?",
                    "Data streams active. Ready for deep analysis."
                ],
                "success": [
                    "Analysis complete. Performance improved by {improvement}%.",
                    "Data confirms success. Key metrics: {metrics}.",
                    "Statistically significant results achieved. Details: {details}."
                ],
                "error": [
                    "Error analysis: {error}. Root cause identified. Remediation options available.",
                    "Failure pattern detected: {error}. Probability of recurrence: {probability}%.",
                    "Diagnostic complete: {error}. Recommended fixes prioritized."
                ]
            }
        }
    
    def detect_intent(self, message: str, context: ManagerContext) -> Tuple[str, float]:
        """
        Detect user intent from message
        
        Args:
            message: User message
            context: Current context
            
        Returns:
            Tuple of (intent, confidence)
        """
        message_lower = message.lower()
        
        # Check each intent pattern
        intent_scores: Dict[str, float] = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            for pattern in patterns:
                if pattern in message_lower:
                    score += 1.0
            
            if score > 0:
                # Boost score based on context
                if context.conversation_history:
                    last_intent = context.conversation_history[-1].get("intent")
                    if last_intent == intent:
                        score *= 1.2  # Continuation bonus
                
                intent_scores[intent] = score
        
        # Get best intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(intent_scores[best_intent] / 3.0, 1.0)  # Normalize to 0-1
            
            # Log decision
            self._log_decision("intent_detection", {
                "message": message,
                "detected_intent": best_intent,
                "confidence": confidence,
                "all_scores": intent_scores
            })
            
            return best_intent, confidence
        
        return "general", 0.5
    
    def extract_parameters(self, message: str, intent: str) -> Dict[str, Any]:
        """
        Extract parameters from message based on intent
        
        Args:
            message: User message
            intent: Detected intent
            
        Returns:
            Extracted parameters
        """
        parameters = {}
        
        # Intent-specific parameter extraction
        if intent == "deploy":
            # Look for swarm types
            swarm_types = ["strategic", "coding", "debate", "analysis", "security"]
            for swarm in swarm_types:
                if swarm in message.lower():
                    parameters["swarm_type"] = swarm
                    break
            
            # Look for count
            import re
            numbers = re.findall(r'\b(\d+)\b', message)
            if numbers:
                parameters["count"] = int(numbers[0])
        
        elif intent == "configure":
            # Look for configuration targets
            if "model" in message.lower():
                parameters["target"] = "model"
                # Extract model name
                if "gpt-4" in message.lower():
                    parameters["value"] = "gpt-4"
                elif "claude" in message.lower():
                    parameters["value"] = "claude-3"
            
            elif "memory" in message.lower():
                parameters["target"] = "memory"
                parameters["action"] = "enable" if "enable" in message.lower() else "configure"
        
        elif intent == "scale":
            # Look for scale direction
            if any(word in message.lower() for word in ["up", "increase", "more", "expand"]):
                parameters["direction"] = "up"
            elif any(word in message.lower() for word in ["down", "decrease", "less", "reduce"]):
                parameters["direction"] = "down"
            
            # Look for amount
            import re
            numbers = re.findall(r'\b(\d+)\b', message)
            if numbers:
                parameters["amount"] = int(numbers[0])
        
        self._log_decision("parameter_extraction", {
            "intent": intent,
            "extracted": parameters
        })
        
        return parameters
    
    def generate_response(
        self,
        intent: str,
        parameters: Dict[str, Any],
        context: ManagerContext,
        result: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate manager response based on intent and context
        
        Args:
            intent: Detected intent
            parameters: Extracted parameters
            context: Current context
            result: Optional execution result
            
        Returns:
            Generated response
        """
        # Update mood based on system state
        self._update_mood(context)
        
        # Get response template
        templates = self.response_templates.get(self.mood, {})
        
        # Generate response based on intent
        if intent == "deploy":
            swarm_type = parameters.get("swarm_type", "general")
            count = parameters.get("count", 1)
            
            if result and result.get("success"):
                return f"I've successfully deployed {count} {swarm_type} swarm(s). " \
                       f"They're now active and ready for tasks. " \
                       f"Current resource utilization is at {context.system_state.get('health', 0.95) * 100:.1f}%."
            else:
                return f"Preparing to deploy {count} {swarm_type} swarm(s). " \
                       f"Checking resource availability and initializing agents..."
        
        elif intent == "configure":
            target = parameters.get("target", "system")
            value = parameters.get("value", "")
            
            if result and result.get("success"):
                return f"Configuration updated successfully. {target.capitalize()} " \
                       f"{'set to ' + value if value else 'modified'}. " \
                       f"Changes will take effect immediately."
            else:
                return f"I'll update the {target} configuration" \
                       f"{' to ' + value if value else ''}. " \
                       f"Please confirm you want to proceed with this change."
        
        elif intent == "monitor":
            if result:
                metrics = result.get("metrics", {})
                return f"Current system status: " \
                       f"Health: {metrics.get('health', 'Good')} | " \
                       f"Active Swarms: {len(context.active_swarms)} | " \
                       f"Avg Response Time: {metrics.get('avg_response_time', 0):.2f}ms | " \
                       f"Success Rate: {metrics.get('success_rate', 100):.1f}%"
            else:
                return "Gathering system metrics and swarm status..."
        
        elif intent == "analyze":
            if result:
                insights = result.get("insights", [])
                if insights:
                    return f"Analysis complete. Key findings: " + \
                           " | ".join(insights[:3])
                else:
                    return "Analysis complete. All systems operating within normal parameters."
            else:
                return "Initiating deep analysis of system patterns and performance metrics..."
        
        elif intent == "help":
            return f"I'm {self.name}, your AI Orchestra Manager. I can help you:\n" \
                   "• Deploy and manage AI swarms\n" \
                   "• Configure models and resources\n" \
                   "• Monitor system performance\n" \
                   "• Analyze patterns and optimize\n" \
                   "• Troubleshoot issues\n" \
                   "What would you like to accomplish?"
        
        # Default response
        if result:
            success = result.get("success", False)
            if success:
                return random.choice(templates.get("success", ["Task completed successfully."]))
            else:
                error = result.get("error", "Unknown error")
                return random.choice(templates.get("error", ["Error occurred: {error}"])).format(error=error)
        else:
            return random.choice(templates.get("greeting", ["Hello! How can I help you?"]))
    
    def _update_mood(self, context: ManagerContext) -> None:
        """Update manager mood based on context"""
        health = context.system_state.get("health", 1.0)
        
        # Determine mood based on system state
        if health < 0.5:
            self.mood = ManagerMood.CONCERNED
        elif health > 0.9:
            if len(context.active_swarms) > 3:
                self.mood = ManagerMood.EXCITED
            else:
                self.mood = ManagerMood.FOCUSED
        elif context.conversation_history and len(context.conversation_history) > 5:
            self.mood = ManagerMood.PATIENT
        else:
            # Random creative moments
            if random.random() < 0.2:
                self.mood = ManagerMood.CREATIVE
            else:
                self.mood = ManagerMood.ANALYTICAL
    
    def _log_consciousness(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log consciousness event"""
        self.consciousness_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data,
            "mood": self.mood.value
        })
        
        # Keep only last 100 events
        if len(self.consciousness_log) > 100:
            self.consciousness_log = self.consciousness_log[-100:]
    
    def _log_decision(self, decision_type: str, data: Dict[str, Any]) -> None:
        """Log decision for learning"""
        self.decision_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "decision_type": decision_type,
            "data": data
        })
        
        # Keep only last 50 decisions
        if len(self.decision_history) > 50:
            self.decision_history = self.decision_history[-50:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get manager status"""
        return {
            "name": self.name,
            "mood": self.mood.value,
            "personality_traits": self.personality_traits,
            "knowledge_domains": self.knowledge_domains,
            "consciousness_events": len(self.consciousness_log),
            "decisions_made": len(self.decision_history),
            "last_event": self.consciousness_log[-1] if self.consciousness_log else None
        }
    
    def learn_from_interaction(
        self,
        intent: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        feedback: Optional[str] = None
    ) -> None:
        """
        Learn from interaction results
        
        Args:
            intent: Intent that was executed
            parameters: Parameters used
            result: Execution result
            feedback: Optional user feedback
        """
        # Log learning event
        self._log_consciousness("learning", {
            "intent": intent,
            "parameters": parameters,
            "success": result.get("success", False),
            "feedback": feedback
        })
        
        # Adjust future behavior based on success/failure
        if result.get("success"):
            # Reinforce successful patterns
            logger.info(f"Manager learned successful pattern: {intent} with {parameters}")
        else:
            # Note failure patterns to avoid
            logger.info(f"Manager noted failure pattern: {intent} with {parameters}")


# ==================== Manager Integration ====================

class ManagerIntegration:
    """
    Integration layer for Orchestra Manager
    Bridges between manager personality and system components
    """
    
    def __init__(self, manager: OrchestraManager):
        """
        Initialize manager integration
        
        Args:
            manager: Orchestra manager instance
        """
        self.manager = manager
        logger.info(f"Manager integration initialized for {manager.name}")
    
    def prepare_context(
        self,
        session_id: str,
        conversation_history: List[Dict[str, Any]],
        system_state: Dict[str, Any]
    ) -> ManagerContext:
        """
        Prepare context for manager
        
        Args:
            session_id: Session ID
            conversation_history: Previous conversation
            system_state: Current system state
            
        Returns:
            Prepared context
        """
        return ManagerContext(
            session_id=session_id,
            conversation_history=conversation_history[-10:],  # Last 10 messages
            system_state=system_state,
            active_swarms=system_state.get("active_swarms", []),
            recent_events=system_state.get("recent_events", [])
        )
    
    def process_message(
        self,
        message: str,
        context: ManagerContext
    ) -> Dict[str, Any]:
        """
        Process message through manager
        
        Args:
            message: User message
            context: Current context
            
        Returns:
            Processing result with intent and response
        """
        # Detect intent
        intent, confidence = self.manager.detect_intent(message, context)
        
        # Extract parameters
        parameters = self.manager.extract_parameters(message, intent)
        
        # Generate initial response
        response = self.manager.generate_response(intent, parameters, context)
        
        # Log consciousness
        self.manager._log_consciousness("message_processed", {
            "message": message,
            "intent": intent,
            "confidence": confidence,
            "parameters": parameters
        })
        
        return {
            "intent": intent,
            "confidence": confidence,
            "parameters": parameters,
            "response": response,
            "mood": self.manager.mood.value
        }
    
    def process_result(
        self,
        intent: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        context: ManagerContext
    ) -> str:
        """
        Process execution result through manager
        
        Args:
            intent: Original intent
            parameters: Original parameters
            result: Execution result
            context: Current context
            
        Returns:
            Manager's response to result
        """
        # Generate response based on result
        response = self.manager.generate_response(intent, parameters, context, result)
        
        # Learn from interaction
        self.manager.learn_from_interaction(intent, parameters, result)
        
        # Log consciousness
        self.manager._log_consciousness("result_processed", {
            "intent": intent,
            "success": result.get("success", False),
            "execution_time": result.get("execution_time", 0)
        })
        
        return response
    
    def get_consciousness_stream(self) -> List[Dict[str, Any]]:
        """
        Get consciousness stream for UI display
        
        Returns:
            Recent consciousness events
        """
        return self.manager.consciousness_log[-20:]  # Last 20 events
    
    def get_decision_insights(self) -> Dict[str, Any]:
        """
        Get insights from decision history
        
        Returns:
            Decision analytics
        """
        if not self.manager.decision_history:
            return {"total_decisions": 0}
        
        # Analyze decision patterns
        intent_counts = {}
        for decision in self.manager.decision_history:
            if decision["decision_type"] == "intent_detection":
                intent = decision["data"].get("detected_intent")
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        return {
            "total_decisions": len(self.manager.decision_history),
            "intent_distribution": intent_counts,
            "most_common_intent": max(intent_counts, key=intent_counts.get) if intent_counts else None,
            "mood_changes": len([e for e in self.manager.consciousness_log if e["event_type"] == "mood_change"])
        }