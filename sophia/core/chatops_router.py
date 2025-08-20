"""
ChatOps Router - Hybrid Natural Language + Command Interface
Handles both natural language parsing and explicit commands for SOPHIA.
"""

import os
import re
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .ultimate_model_router import UltimateModelRouter
from .constants import APPROVED_MODELS

logger = logging.getLogger(__name__)

class ChatMode(Enum):
    """Chat interaction modes"""
    NATURAL = "natural"
    COMMAND = "command"
    HYBRID = "hybrid"

@dataclass
class ExecutionPlan:
    """Represents an execution plan for user approval"""
    id: str
    title: str
    description: str
    operations: List[Dict[str, Any]]
    risks: List[str]
    costs: Dict[str, Any]
    affected_services: List[str]
    estimated_duration: str
    requires_approval: bool = True

@dataclass
class ParsedIntent:
    """Represents parsed user intent"""
    intent_type: str
    action: str
    parameters: Dict[str, Any]
    confidence: float
    raw_text: str

class SOPHIAChatOpsRouter:
    """
    Hybrid natural language + command router for SOPHIA.
    Supports both conversational AI and explicit command interfaces.
    """
    
    def __init__(self, model_router: Optional[UltimateModelRouter] = None):
        self.model_router = model_router or UltimateModelRouter()
        self.mode = ChatMode.HYBRID
        self.pending_plans: Dict[str, ExecutionPlan] = {}
        
        # Intent patterns for NL parsing
        self.intent_patterns = {
            "deploy": [
                r"deploy\s+(?:the\s+)?(\w+)(?:\s+(?:service|app|application))?\s*(?:to\s+(\w+))?",
                r"ship\s+(?:the\s+)?(\w+)",
                r"push\s+(?:the\s+)?(\w+)\s*(?:to\s+(\w+))?"
            ],
            "gong_summary": [
                r"summarize\s+(?:yesterday's\s+|recent\s+|last\s+)?gong\s+calls?",
                r"gong\s+(?:call\s+)?summar(?:y|ies)",
                r"what\s+happened\s+(?:in\s+|on\s+)?(?:yesterday's\s+|recent\s+)?(?:gong\s+)?calls?"
            ],
            "create_task": [
                r"create\s+(?:an?\s+)?(?:asana\s+)?task",
                r"add\s+(?:to\s+)?asana",
                r"create\s+(?:linear\s+)?issue",
                r"add\s+(?:to\s+)?linear"
            ],
            "research": [
                r"research\s+(.+)",
                r"find\s+(?:out\s+)?(?:about\s+)?(.+)",
                r"look\s+up\s+(.+)",
                r"search\s+(?:for\s+)?(.+)"
            ],
            "status": [
                r"(?:what's\s+the\s+)?status\s+(?:of\s+)?(.+)",
                r"how\s+(?:is|are)\s+(.+)\s+(?:doing|performing)",
                r"check\s+(.+)"
            ]
        }
        
        # Command patterns
        self.command_patterns = {
            "/plan": r"^/plan\s+(.+)$",
            "/approve": r"^/approve(?:\s+(\w+))?$",
            "/execute": r"^/execute(?:\s+(\w+))?$",
            "/cancel": r"^/cancel(?:\s+(\w+))?$",
            "/mode": r"^/mode\s+(natural|command|hybrid)$",
            "/status": r"^/status(?:\s+(.+))?$",
            "/help": r"^/help(?:\s+(.+))?$"
        }
        
        logger.info("Initialized SOPHIAChatOpsRouter in hybrid mode")
    
    def set_mode(self, mode: ChatMode) -> str:
        """Set chat interaction mode"""
        self.mode = mode
        logger.info(f"Chat mode set to: {mode.value}")
        
        mode_descriptions = {
            ChatMode.NATURAL: "Natural language mode - I'll interpret your requests conversationally",
            ChatMode.COMMAND: "Command mode - Use explicit /commands for operations",
            ChatMode.HYBRID: "Hybrid mode - I accept both natural language and /commands"
        }
        
        return mode_descriptions[mode]
    
    async def parse_input(self, user_input: str) -> Tuple[str, ParsedIntent]:
        """
        Parse user input and determine intent.
        Returns (response_type, parsed_intent)
        """
        user_input = user_input.strip()
        
        # Check for explicit commands first
        for command, pattern in self.command_patterns.items():
            match = re.match(pattern, user_input, re.IGNORECASE)
            if match:
                return await self._handle_command(command, match.groups())
        
        # If in command-only mode and no command found, guide user
        if self.mode == ChatMode.COMMAND:
            return "error", ParsedIntent(
                intent_type="invalid_command",
                action="help",
                parameters={},
                confidence=1.0,
                raw_text=user_input
            )
        
        # Parse natural language intent
        return await self._parse_natural_language(user_input)
    
    async def _handle_command(self, command: str, args: Tuple[str, ...]) -> Tuple[str, ParsedIntent]:
        """Handle explicit commands"""
        if command == "/plan":
            plan_spec = args[0] if args else ""
            return await self._create_execution_plan(plan_spec)
        
        elif command == "/approve":
            plan_id = args[0] if args else None
            return await self._approve_plan(plan_id)
        
        elif command == "/execute":
            plan_id = args[0] if args else None
            return await self._execute_plan(plan_id)
        
        elif command == "/cancel":
            plan_id = args[0] if args else None
            return await self._cancel_plan(plan_id)
        
        elif command == "/mode":
            mode_str = args[0] if args else "hybrid"
            try:
                new_mode = ChatMode(mode_str)
                response = self.set_mode(new_mode)
                return "success", ParsedIntent(
                    intent_type="mode_change",
                    action="set_mode",
                    parameters={"mode": mode_str, "response": response},
                    confidence=1.0,
                    raw_text=f"/mode {mode_str}"
                )
            except ValueError:
                return "error", ParsedIntent(
                    intent_type="invalid_mode",
                    action="error",
                    parameters={"error": f"Invalid mode: {mode_str}. Use: natural, command, or hybrid"},
                    confidence=1.0,
                    raw_text=f"/mode {mode_str}"
                )
        
        elif command == "/status":
            service = args[0] if args else None
            return await self._get_status(service)
        
        elif command == "/help":
            topic = args[0] if args else None
            return await self._get_help(topic)
        
        return "error", ParsedIntent(
            intent_type="unknown_command",
            action="error",
            parameters={"error": f"Unknown command: {command}"},
            confidence=1.0,
            raw_text=f"{command} {' '.join(args) if args else ''}"
        )
    
    async def _parse_natural_language(self, text: str) -> Tuple[str, ParsedIntent]:
        """Parse natural language using AI models"""
        # First, try pattern matching for common intents
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return await self._handle_pattern_match(intent_type, match, text)
        
        # If no pattern matches, use AI for intent classification
        return await self._classify_with_ai(text)
    
    async def _handle_pattern_match(self, intent_type: str, match, text: str) -> Tuple[str, ParsedIntent]:
        """Handle pattern-matched intents"""
        groups = match.groups()
        
        if intent_type == "deploy":
            service = groups[0] if groups else "unknown"
            environment = groups[1] if len(groups) > 1 and groups[1] else "production"
            
            return await self._create_deployment_plan(service, environment, text)
        
        elif intent_type == "gong_summary":
            return await self._create_gong_summary_plan(text)
        
        elif intent_type == "create_task":
            if "asana" in text.lower():
                return await self._create_asana_task_plan(text)
            elif "linear" in text.lower():
                return await self._create_linear_issue_plan(text)
            else:
                return await self._create_generic_task_plan(text)
        
        elif intent_type == "research":
            query = groups[0] if groups else text
            return await self._create_research_plan(query, text)
        
        elif intent_type == "status":
            service = groups[0] if groups else "all"
            return await self._get_status(service)
        
        return "plan", ParsedIntent(
            intent_type=intent_type,
            action="create_plan",
            parameters={"matches": groups, "text": text},
            confidence=0.8,
            raw_text=text
        )
    
    async def _classify_with_ai(self, text: str) -> Tuple[str, ParsedIntent]:
        """Use AI model to classify intent"""
        try:
            # Use the best available model for intent classification
            model = self.model_router.select_model("reasoning", ["intent_classification"])
            
            prompt = f"""
You are SOPHIA's intent classifier. Analyze this user input and determine the intent.

User input: "{text}"

Classify the intent as one of:
- deploy: User wants to deploy a service/app
- gong_summary: User wants Gong call summaries
- create_task: User wants to create tasks/issues in Asana/Linear
- research: User wants research/information
- status: User wants status of services/systems
- chat: General conversation
- unclear: Intent is unclear

Respond with JSON:
{{
    "intent": "intent_type",
    "confidence": 0.0-1.0,
    "parameters": {{"key": "value"}},
    "suggested_action": "what to do next"
}}
"""
            
            response = await self.model_router.call_model(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse AI response
            try:
                result = json.loads(response.strip())
                intent_type = result.get("intent", "unclear")
                confidence = result.get("confidence", 0.5)
                parameters = result.get("parameters", {})
                suggested_action = result.get("suggested_action", "")
                
                if intent_type == "unclear" or confidence < 0.6:
                    return "clarification", ParsedIntent(
                        intent_type="unclear",
                        action="clarify",
                        parameters={"suggestion": suggested_action},
                        confidence=confidence,
                        raw_text=text
                    )
                
                # Create execution plan based on classified intent
                return await self._create_plan_from_intent(intent_type, parameters, text)
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse AI intent classification: {response}")
                return "clarification", ParsedIntent(
                    intent_type="parse_error",
                    action="clarify",
                    parameters={},
                    confidence=0.0,
                    raw_text=text
                )
        
        except Exception as e:
            logger.error(f"AI intent classification failed: {e}")
            return "error", ParsedIntent(
                intent_type="classification_error",
                action="error",
                parameters={"error": str(e)},
                confidence=0.0,
                raw_text=text
            )
    
    async def _create_plan_from_intent(self, intent_type: str, parameters: Dict, text: str) -> Tuple[str, ParsedIntent]:
        """Create execution plan from classified intent"""
        if intent_type == "deploy":
            service = parameters.get("service", "unknown")
            environment = parameters.get("environment", "production")
            return await self._create_deployment_plan(service, environment, text)
        
        elif intent_type == "gong_summary":
            return await self._create_gong_summary_plan(text)
        
        elif intent_type == "create_task":
            return await self._create_generic_task_plan(text)
        
        elif intent_type == "research":
            query = parameters.get("query", text)
            return await self._create_research_plan(query, text)
        
        elif intent_type == "status":
            service = parameters.get("service", "all")
            return await self._get_status(service)
        
        elif intent_type == "chat":
            return "chat", ParsedIntent(
                intent_type="chat",
                action="respond",
                parameters=parameters,
                confidence=0.9,
                raw_text=text
            )
        
        return "plan", ParsedIntent(
            intent_type=intent_type,
            action="create_plan",
            parameters=parameters,
            confidence=0.7,
            raw_text=text
        )
    
    async def _create_deployment_plan(self, service: str, environment: str, text: str) -> Tuple[str, ExecutionPlan]:
        """Create deployment execution plan"""
        plan_id = f"deploy_{service}_{environment}_{int(datetime.now().timestamp())}"
        
        plan = ExecutionPlan(
            id=plan_id,
            title=f"Deploy {service} to {environment}",
            description=f"Deploy the {service} service to {environment} environment using Fly.io",
            operations=[
                {"type": "github", "action": "create_branch", "params": {"name": f"deploy-{service}-{environment}"}},
                {"type": "github", "action": "commit_changes", "params": {"message": f"Deploy {service} to {environment}"}},
                {"type": "fly", "action": "deploy", "params": {"app": service, "environment": environment}},
                {"type": "monitoring", "action": "health_check", "params": {"service": service}}
            ],
            risks=[
                f"Service downtime during deployment",
                f"Potential rollback required if deployment fails",
                f"Database migrations may be required"
            ],
            costs={
                "estimated_time": "5-10 minutes",
                "compute_cost": "$0.01-0.05",
                "risk_level": "medium"
            },
            affected_services=[service, f"{service}-{environment}"],
            estimated_duration="5-10 minutes"
        )
        
        self.pending_plans[plan_id] = plan
        return "plan", plan
    
    async def _create_gong_summary_plan(self, text: str) -> Tuple[str, ExecutionPlan]:
        """Create Gong summary execution plan"""
        plan_id = f"gong_summary_{int(datetime.now().timestamp())}"
        
        plan = ExecutionPlan(
            id=plan_id,
            title="Summarize Recent Gong Calls",
            description="Analyze recent Gong calls and create summaries with action items",
            operations=[
                {"type": "gong", "action": "list_recent_calls", "params": {"days": 7}},
                {"type": "ai", "action": "summarize_calls", "params": {"model": "claude-sonnet-4"}},
                {"type": "memory", "action": "store_summaries", "params": {"collection": "gong_summaries"}},
                {"type": "optional", "action": "create_tasks", "params": {"services": ["asana", "linear"]}}
            ],
            risks=[
                "API rate limits may slow processing",
                "Large number of calls may require batching"
            ],
            costs={
                "estimated_time": "2-5 minutes",
                "api_calls": "10-50 Gong API calls",
                "ai_tokens": "5000-20000 tokens",
                "risk_level": "low"
            },
            affected_services=["gong", "memory", "ai_models"],
            estimated_duration="2-5 minutes"
        )
        
        self.pending_plans[plan_id] = plan
        return "plan", plan
    
    async def _create_asana_task_plan(self, text: str) -> Tuple[str, ExecutionPlan]:
        """Create Asana task creation plan"""
        plan_id = f"asana_task_{int(datetime.now().timestamp())}"
        
        plan = ExecutionPlan(
            id=plan_id,
            title="Create Asana Task",
            description="Create a new task in Asana based on the request",
            operations=[
                {"type": "asana", "action": "list_projects", "params": {}},
                {"type": "ai", "action": "extract_task_details", "params": {"text": text}},
                {"type": "asana", "action": "create_task", "params": {"from_ai": True}},
                {"type": "memory", "action": "store_task_info", "params": {"collection": "asana_tasks"}}
            ],
            risks=[
                "Task may be created in wrong project",
                "Task details may need refinement"
            ],
            costs={
                "estimated_time": "1-2 minutes",
                "api_calls": "2-5 Asana API calls",
                "risk_level": "low"
            },
            affected_services=["asana", "memory"],
            estimated_duration="1-2 minutes"
        )
        
        self.pending_plans[plan_id] = plan
        return "plan", plan
    
    async def _create_linear_issue_plan(self, text: str) -> Tuple[str, ExecutionPlan]:
        """Create Linear issue creation plan"""
        plan_id = f"linear_issue_{int(datetime.now().timestamp())}"
        
        plan = ExecutionPlan(
            id=plan_id,
            title="Create Linear Issue",
            description="Create a new issue in Linear based on the request",
            operations=[
                {"type": "linear", "action": "list_teams", "params": {}},
                {"type": "ai", "action": "extract_issue_details", "params": {"text": text}},
                {"type": "linear", "action": "create_issue", "params": {"from_ai": True}},
                {"type": "memory", "action": "store_issue_info", "params": {"collection": "linear_issues"}}
            ],
            risks=[
                "Issue may be created in wrong team",
                "Priority level may need adjustment"
            ],
            costs={
                "estimated_time": "1-2 minutes",
                "api_calls": "2-5 Linear API calls",
                "risk_level": "low"
            },
            affected_services=["linear", "memory"],
            estimated_duration="1-2 minutes"
        )
        
        self.pending_plans[plan_id] = plan
        return "plan", plan
    
    async def _create_generic_task_plan(self, text: str) -> Tuple[str, ExecutionPlan]:
        """Create generic task creation plan"""
        plan_id = f"task_{int(datetime.now().timestamp())}"
        
        plan = ExecutionPlan(
            id=plan_id,
            title="Create Task/Issue",
            description="Create a task or issue in the appropriate system",
            operations=[
                {"type": "ai", "action": "determine_best_system", "params": {"text": text}},
                {"type": "conditional", "action": "create_in_system", "params": {"systems": ["asana", "linear", "notion"]}},
                {"type": "memory", "action": "store_task_info", "params": {"collection": "tasks"}}
            ],
            risks=[
                "May need user input to choose system",
                "Task details may need clarification"
            ],
            costs={
                "estimated_time": "2-3 minutes",
                "api_calls": "3-8 API calls",
                "risk_level": "low"
            },
            affected_services=["asana", "linear", "notion", "memory"],
            estimated_duration="2-3 minutes"
        )
        
        self.pending_plans[plan_id] = plan
        return "plan", plan
    
    async def _create_research_plan(self, query: str, text: str) -> Tuple[str, ExecutionPlan]:
        """Create research execution plan"""
        plan_id = f"research_{int(datetime.now().timestamp())}"
        
        plan = ExecutionPlan(
            id=plan_id,
            title=f"Research: {query[:50]}...",
            description=f"Conduct comprehensive research on: {query}",
            operations=[
                {"type": "research", "action": "multi_source_search", "params": {"query": query}},
                {"type": "ai", "action": "synthesize_results", "params": {"model": "claude-sonnet-4"}},
                {"type": "memory", "action": "store_research", "params": {"collection": "research"}},
                {"type": "optional", "action": "create_notion_page", "params": {"title": f"Research: {query}"}}
            ],
            risks=[
                "Research may take longer for complex topics",
                "Some sources may be unavailable"
            ],
            costs={
                "estimated_time": "3-10 minutes",
                "api_calls": "20-100 search API calls",
                "ai_tokens": "10000-50000 tokens",
                "risk_level": "low"
            },
            affected_services=["research_apis", "ai_models", "memory", "notion"],
            estimated_duration="3-10 minutes"
        )
        
        self.pending_plans[plan_id] = plan
        return "plan", plan
    
    async def _approve_plan(self, plan_id: Optional[str]) -> Tuple[str, ParsedIntent]:
        """Approve an execution plan"""
        if not plan_id:
            # Get most recent plan
            if not self.pending_plans:
                return "error", ParsedIntent(
                    intent_type="no_plans",
                    action="error",
                    parameters={"error": "No pending plans to approve"},
                    confidence=1.0,
                    raw_text="/approve"
                )
            plan_id = max(self.pending_plans.keys(), key=lambda x: self.pending_plans[x].id)
        
        if plan_id not in self.pending_plans:
            return "error", ParsedIntent(
                intent_type="plan_not_found",
                action="error",
                parameters={"error": f"Plan {plan_id} not found"},
                confidence=1.0,
                raw_text=f"/approve {plan_id}"
            )
        
        plan = self.pending_plans[plan_id]
        
        return "approved", ParsedIntent(
            intent_type="plan_approved",
            action="execute",
            parameters={"plan": plan, "plan_id": plan_id},
            confidence=1.0,
            raw_text=f"/approve {plan_id}"
        )
    
    async def _execute_plan(self, plan_id: Optional[str]) -> Tuple[str, ParsedIntent]:
        """Execute an approved plan"""
        if not plan_id:
            if not self.pending_plans:
                return "error", ParsedIntent(
                    intent_type="no_plans",
                    action="error",
                    parameters={"error": "No pending plans to execute"},
                    confidence=1.0,
                    raw_text="/execute"
                )
            plan_id = max(self.pending_plans.keys(), key=lambda x: self.pending_plans[x].id)
        
        if plan_id not in self.pending_plans:
            return "error", ParsedIntent(
                intent_type="plan_not_found",
                action="error",
                parameters={"error": f"Plan {plan_id} not found"},
                confidence=1.0,
                raw_text=f"/execute {plan_id}"
            )
        
        plan = self.pending_plans.pop(plan_id)
        
        return "executing", ParsedIntent(
            intent_type="plan_executing",
            action="execute",
            parameters={"plan": plan, "plan_id": plan_id},
            confidence=1.0,
            raw_text=f"/execute {plan_id}"
        )
    
    async def _cancel_plan(self, plan_id: Optional[str]) -> Tuple[str, ParsedIntent]:
        """Cancel a pending plan"""
        if not plan_id:
            if not self.pending_plans:
                return "error", ParsedIntent(
                    intent_type="no_plans",
                    action="error",
                    parameters={"error": "No pending plans to cancel"},
                    confidence=1.0,
                    raw_text="/cancel"
                )
            plan_id = max(self.pending_plans.keys(), key=lambda x: self.pending_plans[x].id)
        
        if plan_id not in self.pending_plans:
            return "error", ParsedIntent(
                intent_type="plan_not_found",
                action="error",
                parameters={"error": f"Plan {plan_id} not found"},
                confidence=1.0,
                raw_text=f"/cancel {plan_id}"
            )
        
        plan = self.pending_plans.pop(plan_id)
        
        return "cancelled", ParsedIntent(
            intent_type="plan_cancelled",
            action="cancel",
            parameters={"plan": plan, "plan_id": plan_id},
            confidence=1.0,
            raw_text=f"/cancel {plan_id}"
        )
    
    async def _get_status(self, service: Optional[str]) -> Tuple[str, ParsedIntent]:
        """Get system status"""
        return "status", ParsedIntent(
            intent_type="status_check",
            action="get_status",
            parameters={"service": service or "all"},
            confidence=1.0,
            raw_text=f"/status {service or ''}"
        )
    
    async def _get_help(self, topic: Optional[str]) -> Tuple[str, ParsedIntent]:
        """Get help information"""
        help_content = {
            "commands": """
Available Commands:
/plan <operation> - Create execution plan
/approve [plan_id] - Approve pending plan
/execute [plan_id] - Execute approved plan
/cancel [plan_id] - Cancel pending plan
/mode <natural|command|hybrid> - Set interaction mode
/status [service] - Get system status
/help [topic] - Show help

Natural Language Examples:
"Deploy the research service to staging"
"Summarize yesterday's Gong calls"
"Create an Asana task for follow-up"
"Research AI orchestration patterns"
""",
            "modes": """
Chat Modes:
- natural: Conversational AI interface
- command: Explicit /command interface only
- hybrid: Both natural language and commands (default)
""",
            "examples": """
Example Interactions:

Natural Language:
"Sophia, deploy the API service to production"
"Summarize recent Gong calls and create tasks"
"Research competitor analysis for Q1"

Commands:
/plan deploy:api:production
/approve
/execute
/status api
"""
        }
        
        content = help_content.get(topic, help_content["commands"])
        
        return "help", ParsedIntent(
            intent_type="help",
            action="show_help",
            parameters={"topic": topic, "content": content},
            confidence=1.0,
            raw_text=f"/help {topic or ''}"
        )
    
    def get_pending_plans(self) -> List[ExecutionPlan]:
        """Get all pending execution plans"""
        return list(self.pending_plans.values())
    
    def clear_pending_plans(self) -> int:
        """Clear all pending plans and return count"""
        count = len(self.pending_plans)
        self.pending_plans.clear()
        return count

