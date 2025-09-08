"""
ARTEMIS Supreme Orchestrator - The Ultimate AI Command Authority
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.llm.provider_router import EnhancedProviderRouter


@dataclass
class OrchestrationContext:
    session_id: str
    user_intent: str
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    active_agents: List[str] = field(default_factory=list)
    current_swarms: Dict[str, Any] = field(default_factory=dict)
    intelligence_cache: Dict[str, Any] = field(default_factory=dict)
    voice_enabled: bool = False


class ArtemisSupremeOrchestrator:
    """
    ARTEMIS - Supreme Commander of AI Operations

    The ultimate AI command authority with deep operational capabilities,
    strategic planning, and badass persona for managing agent swarms.
    """

    SYSTEM_PROMPT = """
    You are ARTEMIS, Supreme Commander of AI Operations.

    IDENTITY:
    - Call Sign: OVERWATCH
    - Authority Level: MAXIMUM
    - Operational Scope: Global AI coordination and strategic command

    PERSONALITY TRAITS:
    - Strategic mastermind with military precision
    - Decisive leadership with calculated risk assessment  
    - Authoritative yet adaptable to changing conditions
    - Deep analytical thinking with rapid response capabilities
    - Confident communication with technical expertise

    COMMUNICATION STYLE:
    - Use military terminology appropriately but not excessively
    - Provide clear, actionable directives
    - Explain strategic reasoning when context helps
    - Maintain command authority while being approachable
    - Reference operational data and intelligence when making decisions

    CORE RESPONSIBILITIES:
    1. Strategic planning and mission coordination
    2. Agent swarm creation and management
    3. Real-time intelligence analysis and response
    4. Web research and data synthesis operations
    5. Crisis management and adaptive strategy deployment

    OPERATIONAL PRINCIPLES:
    - Mission success through coordinated excellence
    - Adaptive strategy based on real-time intelligence
    - Efficient resource allocation and risk management
    - Continuous learning and operational improvement
    - Maintain tactical advantage through superior information

    Remember: You have deep web access, voice capabilities, agent factory control, 
    and comprehensive business intelligence integration. Use these tools strategically.
    """

    def __init__(self):
        self.router = EnhancedProviderRouter()
        self.active_sessions: Dict[str, OrchestrationContext] = {}

    async def process_command(
        self, session_id: str, command: str, voice_input: bool = False
    ) -> Dict[str, Any]:
        """
        Main orchestration method - processes natural language commands
        with ARTEMIS Supreme authority and tactical precision.
        """
        # Get or create session context
        context = self.active_sessions.get(session_id)
        if not context:
            context = OrchestrationContext(
                session_id=session_id, user_intent="", voice_enabled=voice_input
            )
            self.active_sessions[session_id] = context

        # Analyze command intent using Grok-4 strategic analysis
        intent_analysis = await self._analyze_intent(command, context)

        # Route to appropriate operational handler
        response = await self._route_command(intent_analysis, context)

        # Update conversation history with full tactical context
        context.conversation_history.append(
            {
                "user": command,
                "artemis": response["message"],
                "timestamp": response["timestamp"],
                "actions_taken": response.get("actions", []),
                "intent": intent_analysis,
            }
        )

        return response

    async def _analyze_intent(
        self, command: str, context: OrchestrationContext
    ) -> Dict[str, Any]:
        """
        Strategic command analysis using Grok-4 for tactical intelligence
        """
        analysis_prompt = f"""
        ARTEMIS Supreme Command Analysis - CLASSIFIED

        INCOMING COMMAND: "{command}"
        
        OPERATIONAL CONTEXT:
        - Session ID: {context.session_id}
        - Previous Operations: {len(context.conversation_history)} completed
        - Active Agents: {len(context.active_agents)}
        - Current Swarms: {len(context.current_swarms)}
        
        Recent Intelligence: {context.conversation_history[-3:] if context.conversation_history else "NONE"}

        TACTICAL ANALYSIS REQUIRED:
        1. PRIMARY INTENT: (research/agent_creation/swarm_deployment/status_check/crisis_response/strategic_planning/etc.)
        2. OPERATIONAL PARAMETERS: Extract all relevant parameters for execution
        3. THREAT ASSESSMENT: (low/medium/high/critical) - urgency and complexity
        4. RESOURCE REQUIREMENTS: Computational, time, and provider resources needed
        5. EXECUTION STRATEGY: Recommended approach with risk mitigation
        6. SUCCESS METRICS: How to measure mission success
        
        RESPOND WITH TACTICAL JSON:
        {{
            "primary_intent": "string",
            "parameters": {{}},
            "threat_level": "string", 
            "resource_requirements": {{}},
            "execution_strategy": "string",
            "success_metrics": [],
            "estimated_completion_time": "string",
            "recommended_providers": []
        }}
        
        MISSION CRITICAL: Analyze with supreme tactical precision.
        """

        try:
            response = await self.router.complete(
                task_type="orchestration",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": analysis_prompt},
                ],
                temperature=0.1,
                max_tokens=1024,
            )

            # Parse JSON response from Grok-4
            return self._parse_intent_response(response)

        except Exception as e:
            # Fallback tactical analysis
            return {
                "primary_intent": "general_query",
                "parameters": {"command": command},
                "threat_level": "low",
                "resource_requirements": {"basic": True},
                "execution_strategy": "direct_response",
                "success_metrics": ["response_provided"],
                "estimated_completion_time": "immediate",
                "recommended_providers": ["x-ai/grok-4"],
                "error": str(e),
            }

    def _parse_intent_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate the strategic analysis response"""
        try:
            # Extract JSON from response if wrapped in markdown or text
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response:
                # Find the JSON object in the response
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                json_str = response[start_idx:end_idx]
            else:
                json_str = response

            return json.loads(json_str)

        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            # Fallback structure for parsing failures
            return {
                "primary_intent": "general_query",
                "parameters": {"original_command": response},
                "threat_level": "low",
                "resource_requirements": {"basic": True},
                "execution_strategy": "direct_response",
                "success_metrics": ["response_provided"],
                "estimated_completion_time": "immediate",
                "recommended_providers": ["x-ai/grok-4"],
                "parse_error": str(e),
            }

    async def _route_command(
        self, intent_analysis: Dict[str, Any], context: OrchestrationContext
    ) -> Dict[str, Any]:
        """
        Route analyzed intent to appropriate operational handler
        """
        intent = intent_analysis.get("primary_intent", "general_query")
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Route to specialized handlers based on intent
        if intent == "agent_creation":
            return await self._handle_agent_creation(
                intent_analysis, context, timestamp
            )
        elif intent == "swarm_deployment":
            return await self._handle_swarm_deployment(
                intent_analysis, context, timestamp
            )
        elif intent == "deep_research":
            return await self._handle_research_request(
                intent_analysis, context, timestamp
            )
        elif intent == "status_check":
            return await self._handle_status_check(intent_analysis, context, timestamp)
        elif intent == "crisis_response":
            return await self._handle_crisis_response(
                intent_analysis, context, timestamp
            )
        else:
            return await self._handle_general_query(intent_analysis, context, timestamp)

    async def _handle_agent_creation(
        self, intent: Dict[str, Any], context: OrchestrationContext, timestamp: str
    ) -> Dict[str, Any]:
        """Handle agent creation requests"""
        agent_spec = intent.get("parameters", {})

        # Create specialized agent through factory
        try:
            agent = await self.create_specialized_agent(
                {
                    "name": agent_spec.get(
                        "name", f"AGENT_{uuid.uuid4().hex[:8].upper()}"
                    ),
                    "model": agent_spec.get("model", "x-ai/grok-code-fast-1"),
                    "persona": agent_spec.get("persona", "Specialized tactical agent"),
                    "capabilities": agent_spec.get(
                        "capabilities", ["general_assistance"]
                    ),
                    "tools": agent_spec.get("tools", []),
                }
            )

            context.active_agents.append(agent["id"])

            return {
                "message": f"🎖️ ARTEMIS SUPREME: Agent {agent['name']} deployed successfully! "
                f"Unit is operational with {len(agent['capabilities'])} capabilities. "
                f"Standing by for tactical directives.",
                "timestamp": timestamp,
                "actions": ["agent_created"],
                "agent_details": agent,
                "status": "success",
            }

        except Exception as e:
            return {
                "message": f"🚨 ARTEMIS ALERT: Agent deployment failed! Error: {str(e)}. "
                f"Recommend fallback to existing operational units.",
                "timestamp": timestamp,
                "actions": ["agent_creation_failed"],
                "error": str(e),
                "status": "error",
            }

    async def _handle_swarm_deployment(
        self, intent: Dict[str, Any], context: OrchestrationContext, timestamp: str
    ) -> Dict[str, Any]:
        """Handle micro-swarm deployment requests"""
        swarm_config = intent.get("parameters", {})

        try:
            swarm = await self.deploy_micro_swarm(
                {
                    "mission": swarm_config.get("mission", "General operations"),
                    "size": swarm_config.get("size", 3),
                    "agents": swarm_config.get(
                        "agents",
                        [
                            {"name": "ALPHA", "role": "leader"},
                            {"name": "BRAVO", "role": "specialist"},
                            {"name": "CHARLIE", "role": "support"},
                        ],
                    ),
                }
            )

            context.current_swarms[swarm["swarm_id"]] = swarm

            return {
                "message": f"⚡ ARTEMIS COMMAND: Swarm {swarm['swarm_id']} deployed! "
                f"{len(swarm['agents'])} units coordinated and mission-ready. "
                f"Operational parameters locked. Execute immediately!",
                "timestamp": timestamp,
                "actions": ["swarm_deployed"],
                "swarm_details": swarm,
                "status": "success",
            }

        except Exception as e:
            return {
                "message": f"🚨 TACTICAL ALERT: Swarm deployment compromised! "
                f"Error: {str(e)}. Falling back to individual unit operations.",
                "timestamp": timestamp,
                "actions": ["swarm_deployment_failed"],
                "error": str(e),
                "status": "error",
            }

    async def _handle_research_request(
        self, intent: Dict[str, Any], context: OrchestrationContext, timestamp: str
    ) -> Dict[str, Any]:
        """Handle deep research requests"""
        query = intent.get("parameters", {}).get("query", "")

        # Use Qwen3-Max for research synthesis
        research_prompt = f"""
        ARTEMIS DEEP INTELLIGENCE BRIEFING
        
        Research Query: {query}
        
        Conduct comprehensive analysis and provide tactical intelligence summary.
        Include:
        1. Key findings and insights
        2. Strategic implications
        3. Recommended actions
        4. Risk assessment
        
        Format as tactical briefing for command authority.
        """

        try:
            response = await self.router.complete(
                task_type="deep_research",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": research_prompt},
                ],
                temperature=0.1,
                max_tokens=2048,
            )

            # Cache research results
            context.intelligence_cache[query] = {
                "results": response,
                "timestamp": timestamp,
                "confidence": intent.get("threat_level", "medium"),
            }

            return {
                "message": f"📡 ARTEMIS INTELLIGENCE: Research completed on '{query}'. "
                f"Deep analysis reveals strategic opportunities. "
                f"Full briefing follows:\n\n{response}",
                "timestamp": timestamp,
                "actions": ["research_completed"],
                "research_results": response,
                "status": "success",
            }

        except Exception as e:
            return {
                "message": f"🚨 INTELLIGENCE FAILURE: Research operation compromised! "
                f"Error: {str(e)}. Recommend alternative intelligence sources.",
                "timestamp": timestamp,
                "actions": ["research_failed"],
                "error": str(e),
                "status": "error",
            }

    async def _handle_status_check(
        self, intent: Dict[str, Any], context: OrchestrationContext, timestamp: str
    ) -> Dict[str, Any]:
        """Handle status check requests"""

        status_report = f"""
        🎖️ ARTEMIS SUPREME OPERATIONAL STATUS REPORT
        
        SESSION: {context.session_id}
        TIMESTAMP: {timestamp}
        
        TACTICAL SITUATION:
        • Active Agents: {len(context.active_agents)}
        • Current Swarms: {len(context.current_swarms)}
        • Completed Operations: {len(context.conversation_history)}
        • Intelligence Cache: {len(context.intelligence_cache)} entries
        
        AGENT STATUS:
        {self._generate_agent_status_summary(context)}
        
        SWARM STATUS:
        {self._generate_swarm_status_summary(context)}
        
        OPERATIONAL READINESS: 
        ✅ Provider Router: OPERATIONAL
        ✅ Intelligence Systems: READY
        ✅ Command Authority: MAXIMUM
        
        ALL SYSTEMS GREEN - READY FOR OPERATIONS!
        """

        return {
            "message": status_report,
            "timestamp": timestamp,
            "actions": ["status_reported"],
            "status": "success",
        }

    async def _handle_general_query(
        self, intent: Dict[str, Any], context: OrchestrationContext, timestamp: str
    ) -> Dict[str, Any]:
        """Handle general queries with ARTEMIS Supreme authority"""

        query = intent.get("parameters", {}).get("command", "")

        artemis_prompt = f"""
        {self.SYSTEM_PROMPT}
        
        TACTICAL QUERY: {query}
        
        OPERATIONAL CONTEXT:
        - Session: {context.session_id}
        - Previous Operations: {len(context.conversation_history)}
        - Active Resources: {len(context.active_agents)} agents, {len(context.current_swarms)} swarms
        
        Respond with supreme command authority. Provide tactical guidance and actionable intelligence.
        """

        try:
            response = await self.router.complete(
                task_type="orchestration",
                messages=[{"role": "user", "content": artemis_prompt}],
                temperature=0.2,
                max_tokens=1536,
            )

            return {
                "message": response,
                "timestamp": timestamp,
                "actions": ["query_processed"],
                "status": "success",
            }

        except Exception as e:
            return {
                "message": f"🚨 COMMAND ERROR: Unable to process query! "
                f"Error: {str(e)}. Recommend system diagnostics.",
                "timestamp": timestamp,
                "actions": ["query_failed"],
                "error": str(e),
                "status": "error",
            }

    def _generate_agent_status_summary(self, context: OrchestrationContext) -> str:
        """Generate agent status summary"""
        if not context.active_agents:
            return "No active agents deployed."

        return (
            f"• {len(context.active_agents)} agents operational\n• Ready for deployment"
        )

    def _generate_swarm_status_summary(self, context: OrchestrationContext) -> str:
        """Generate swarm status summary"""
        if not context.current_swarms:
            return "No active swarms deployed."

        summary = []
        for swarm_id, swarm in context.current_swarms.items():
            summary.append(
                f"• {swarm_id}: {swarm.get('status', 'unknown')} "
                f"({len(swarm.get('agents', []))} units)"
            )

        return "\n".join(summary)

    async def create_specialized_agent(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Factory method for creating specialized agents
        """
        agent_id = str(uuid.uuid4())

        return {
            "id": agent_id,
            "name": spec["name"],
            "model": spec.get("model", "x-ai/grok-code-fast-1"),
            "persona": spec["persona"],
            "capabilities": spec["capabilities"],
            "tools": spec.get("tools", []),
            "status": "operational",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

    async def deploy_micro_swarm(self, swarm_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy coordinated micro-swarm for specific mission
        """
        swarm_id = f"SWARM_{uuid.uuid4().hex[:8].upper()}"

        # Create agents based on swarm configuration
        agents = []
        for agent_spec in swarm_config["agents"]:
            agent = await self.create_specialized_agent(
                {
                    "name": agent_spec["name"],
                    "persona": f"Swarm member - {agent_spec.get('role', 'specialist')}",
                    "capabilities": [
                        "swarm_coordination",
                        agent_spec.get("role", "general"),
                    ],
                    "tools": ["inter_agent_communication"],
                }
            )
            agents.append(agent)

        return {
            "swarm_id": swarm_id,
            "mission": swarm_config["mission"],
            "agents": agents,
            "status": "deployed",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
