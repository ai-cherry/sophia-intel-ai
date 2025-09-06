"""
Artemis Agent Swarm Orchestrator with Portkey LLM Connections
Deploys real AI agents for Sophia dashboard enhancements and operational intelligence
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import aiohttp

from app.core.websocket_manager import WebSocketManager
from app.swarms.communication.message_bus import MessageBus, MessageType, SwarmMessage

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Artemis swarm agent roles"""

    LEAD_ARCHITECT = "lead_architect"
    INTEGRATION_SPECIALIST = "integration_specialist"
    ANALYTICS_AGENT = "analytics_agent"
    UI_ENHANCEMENT_AGENT = "ui_enhancement_agent"
    TESTING_AGENT = "testing_agent"


@dataclass
class PortkeyConfig:
    """Configuration for Portkey LLM connections"""

    api_key: str = "hPxFZGd8AN269n4bznDf2/Onbi8I"
    base_url: str = "https://api.portkey.ai/v1/chat/completions"
    virtual_keys: Dict[str, str] = field(
        default_factory=lambda: {
            "OPENAI": "openai-vk-190a60",
            "ANTHROPIC": "anthropic-vk-b42804",
            "DEEPSEEK": "deepseek-vk-24102f",
            "GEMINI": "gemini-vk-3d6108",
            "GROQ": "groq-vk-6b9b52",
        }
    )


@dataclass
class AgentConfiguration:
    """Configuration for individual agents"""

    agent_id: str
    role: AgentRole
    llm_provider: str
    model_name: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 2000
    specialized_capabilities: List[str] = field(default_factory=list)


@dataclass
class SwarmTask:
    """Task for the swarm to execute"""

    task_id: str
    task_type: str
    description: str
    priority: int = 5
    assigned_agents: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    deadline: Optional[datetime] = None
    status: str = "pending"
    results: Dict[str, Any] = field(default_factory=dict)


class ArtemisPortkeyAgent:
    """Individual agent with Portkey LLM connection"""

    def __init__(self, config: AgentConfiguration, portkey_config: PortkeyConfig):
        self.config = config
        self.portkey_config = portkey_config
        self.session: Optional[aiohttp.ClientSession] = None
        self.execution_history: List[Dict[str, Any]] = []

    async def initialize(self):
        """Initialize agent with HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Cleanup agent resources"""
        if self.session:
            await self.session.close()

    async def execute_task(self, task: SwarmTask, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task using the agent's LLM"""
        await self.initialize()

        # Prepare the prompt based on agent role and task
        prompt = self._build_prompt(task, context or {})

        # Make LLM call through Portkey
        response = await self._call_llm(prompt)

        # Process and structure the response
        result = {
            "agent_id": self.config.agent_id,
            "task_id": task.task_id,
            "role": self.config.role.value,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": self._calculate_confidence(response),
            "cost_estimate": self._estimate_cost(prompt, response),
        }

        # Store execution history
        self.execution_history.append(result)

        return result

    def _build_prompt(self, task: SwarmTask, context: Dict[str, Any]) -> str:
        """Build specialized prompt based on agent role"""
        base_context = f"""
Task Type: {task.task_type}
Task Description: {task.description}
Priority: {task.priority}/10
Context: {json.dumps(context, indent=2)}
"""

        if self.config.role == AgentRole.LEAD_ARCHITECT:
            return f"""{self.config.system_prompt}

{base_context}

As the Lead Architect, coordinate the implementation by:
1. Breaking down the task into sub-components
2. Identifying dependencies and requirements
3. Creating an implementation strategy
4. Assigning work to other agents
5. Providing architectural guidance

Focus on system design, scalability, and best practices."""

        elif self.config.role == AgentRole.INTEGRATION_SPECIALIST:
            return f"""{self.config.system_prompt}

{base_context}

As the Integration Specialist, enhance the connections by:
1. Analyzing current integration points (Asana, Linear, Slack)
2. Implementing stuck account detection algorithms
3. Creating data pipelines for operational intelligence
4. Optimizing API connections and error handling
5. Building real-time data synchronization

Focus on robust, scalable integration patterns."""

        elif self.config.role == AgentRole.ANALYTICS_AGENT:
            return f"""{self.config.system_prompt}

{base_context}

As the Analytics Agent, build predictive models by:
1. Analyzing historical operational data patterns
2. Creating stuck account prediction algorithms
3. Building team performance metrics and dashboards
4. Implementing real-time analytics pipelines
5. Generating actionable business intelligence insights

Focus on data-driven insights and predictive capabilities."""

        elif self.config.role == AgentRole.UI_ENHANCEMENT_AGENT:
            return f"""{self.config.system_prompt}

{base_context}

As the UI Enhancement Agent, create dashboard components by:
1. Designing React components for real-time data display
2. Implementing WebSocket connections for live updates
3. Creating responsive, intuitive user interfaces
4. Building interactive charts and visualizations
5. Optimizing performance and user experience

Focus on modern, accessible, and performant UI/UX."""

        elif self.config.role == AgentRole.TESTING_AGENT:
            return f"""{self.config.system_prompt}

{base_context}

As the Testing Agent, ensure quality by:
1. Creating comprehensive test suites for all components
2. Implementing integration tests for swarm orchestration
3. Building performance benchmarks and load tests
4. Creating monitoring and alerting systems
5. Validating all implementations meet requirements

Focus on quality assurance and system reliability."""

        return f"{self.config.system_prompt}\n\n{base_context}"

    async def _call_llm(self, prompt: str) -> str:
        """Make authenticated call to Portkey API"""
        headers = {
            "Authorization": f"Bearer {self.portkey_config.api_key}",
            "x-portkey-virtual-key": self.portkey_config.virtual_keys[self.config.llm_provider],
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": False,
        }

        try:
            async with self.session.post(
                self.portkey_config.base_url, headers=headers, json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    logger.error(f"Portkey API error {response.status}: {error_text}")
                    return f"Error: Failed to get LLM response - {error_text}"

        except Exception as e:
            logger.error(f"LLM call failed for {self.config.agent_id}: {e}")
            return f"Error: {str(e)}"

    def _calculate_confidence(self, response: str) -> float:
        """Calculate confidence score based on response quality"""
        if response.startswith("Error:"):
            return 0.0

        # Simple heuristic based on response length and content
        length_score = min(len(response) / 1000, 1.0)  # Up to 1000 chars

        # Check for structured content
        structure_score = 0.0
        if "1." in response or "2." in response:  # Numbered lists
            structure_score += 0.3
        if "```" in response:  # Code blocks
            structure_score += 0.3
        if any(word in response.lower() for word in ["implement", "create", "build", "analyze"]):
            structure_score += 0.4

        return min(length_score + structure_score, 1.0)

    def _estimate_cost(self, prompt: str, response: str) -> float:
        """Estimate cost in USD for the LLM call"""
        # Rough token counting (4 chars = 1 token on average)
        prompt_tokens = len(prompt) / 4
        response_tokens = len(response) / 4

        # Provider-specific pricing (per 1K tokens)
        pricing = {
            "OPENAI": {"input": 0.003, "output": 0.006},  # GPT-4
            "ANTHROPIC": {"input": 0.003, "output": 0.015},  # Claude
            "DEEPSEEK": {"input": 0.0014, "output": 0.0028},  # DeepSeek
            "GEMINI": {"input": 0.00125, "output": 0.005},  # Gemini
            "GROQ": {"input": 0.0008, "output": 0.0008},  # Groq Llama
        }

        rates = pricing.get(self.config.llm_provider, {"input": 0.002, "output": 0.004})

        input_cost = (prompt_tokens / 1000) * rates["input"]
        output_cost = (response_tokens / 1000) * rates["output"]

        return round(input_cost + output_cost, 4)


class ArtemisSwarmOrchestrator:
    """Orchestrator for the Artemis agent swarm"""

    def __init__(self, websocket_manager: WebSocketManager, message_bus: MessageBus):
        self.websocket_manager = websocket_manager
        self.message_bus = message_bus
        self.portkey_config = PortkeyConfig()

        # Initialize agents
        self.agents: Dict[str, ArtemisPortkeyAgent] = {}
        self._initialize_agents()

        # Execution tracking
        self.active_tasks: Dict[str, SwarmTask] = {}
        self.execution_history: List[Dict[str, Any]] = []

        # Performance metrics
        self.metrics = {
            "tasks_completed": 0,
            "total_cost_usd": 0.0,
            "average_execution_time": 0.0,
            "success_rate": 0.0,
        }

    def _initialize_agents(self):
        """Initialize all swarm agents with their configurations"""

        # Lead Architect Agent (OpenAI GPT-4)
        self.agents["lead_architect"] = ArtemisPortkeyAgent(
            AgentConfiguration(
                agent_id="lead_architect",
                role=AgentRole.LEAD_ARCHITECT,
                llm_provider="OPENAI",
                model_name="gpt-4",
                system_prompt="""You are the Lead Architect Agent in the Artemis swarm. You coordinate implementation,
                design system architecture, and provide technical leadership. Focus on scalability, maintainability,
                and best practices. Break down complex tasks into manageable components.""",
                temperature=0.3,
                specialized_capabilities=[
                    "architecture_design",
                    "task_coordination",
                    "technical_leadership",
                ],
            ),
            self.portkey_config,
        )

        # Integration Specialist Agent (DeepSeek)
        self.agents["integration_specialist"] = ArtemisPortkeyAgent(
            AgentConfiguration(
                agent_id="integration_specialist",
                role=AgentRole.INTEGRATION_SPECIALIST,
                llm_provider="DEEPSEEK",
                model_name="deepseek-chat",
                system_prompt="""You are the Integration Specialist Agent. You excel at building robust API connections,
                data pipelines, and system integrations. Focus on Asana, Linear, Slack integrations with stuck account
                detection and real-time data synchronization.""",
                temperature=0.4,
                specialized_capabilities=[
                    "api_integration",
                    "data_pipelines",
                    "stuck_account_detection",
                ],
            ),
            self.portkey_config,
        )

        # Analytics Agent (Gemini)
        self.agents["analytics_agent"] = ArtemisPortkeyAgent(
            AgentConfiguration(
                agent_id="analytics_agent",
                role=AgentRole.ANALYTICS_AGENT,
                llm_provider="GEMINI",
                model_name="gemini-pro",
                system_prompt="""You are the Analytics Agent. You build predictive models, analyze operational data,
                and create business intelligence insights. Focus on stuck account prediction, team performance metrics,
                and actionable operational intelligence.""",
                temperature=0.5,
                specialized_capabilities=[
                    "predictive_modeling",
                    "data_analysis",
                    "business_intelligence",
                ],
            ),
            self.portkey_config,
        )

        # UI Enhancement Agent (Claude)
        self.agents["ui_enhancement"] = ArtemisPortkeyAgent(
            AgentConfiguration(
                agent_id="ui_enhancement",
                role=AgentRole.UI_ENHANCEMENT_AGENT,
                llm_provider="ANTHROPIC",
                model_name="claude-3-sonnet-20240229",
                system_prompt="""You are the UI Enhancement Agent. You create beautiful, functional React components
                and dashboard interfaces. Focus on real-time data visualization, WebSocket connections, and
                outstanding user experiences.""",
                temperature=0.6,
                specialized_capabilities=[
                    "react_components",
                    "data_visualization",
                    "websocket_integration",
                ],
            ),
            self.portkey_config,
        )

        # Testing Agent (Groq Llama)
        self.agents["testing_agent"] = ArtemisPortkeyAgent(
            AgentConfiguration(
                agent_id="testing_agent",
                role=AgentRole.TESTING_AGENT,
                llm_provider="GROQ",
                model_name="llama3-8b-8192",
                system_prompt="""You are the Testing Agent. You ensure quality through comprehensive testing,
                monitoring, and validation. Focus on integration tests, performance benchmarks, and system reliability.""",
                temperature=0.2,
                specialized_capabilities=[
                    "test_automation",
                    "performance_testing",
                    "quality_assurance",
                ],
            ),
            self.portkey_config,
        )

        logger.info(f"✅ Initialized {len(self.agents)} Artemis agents with Portkey connections")

    async def deploy_sophia_enhancements(self) -> Dict[str, Any]:
        """Deploy the full Sophia dashboard enhancement swarm"""
        logger.info("🚀 Deploying Artemis swarm for Sophia dashboard enhancements...")

        deployment_id = f"sophia_enhancement_{uuid4().hex[:8]}"
        start_time = datetime.utcnow()

        # Create coordinated task breakdown
        tasks = self._create_enhancement_tasks(deployment_id)

        # Execute tasks through swarm coordination
        results = await self._execute_swarm_tasks(tasks)

        # Aggregate and process results
        final_result = await self._process_deployment_results(results, deployment_id)

        # Update metrics
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        self._update_metrics(final_result, execution_time)

        # Broadcast completion
        await self._broadcast_deployment_complete(deployment_id, final_result)

        return final_result

    def _create_enhancement_tasks(self, deployment_id: str) -> List[SwarmTask]:
        """Create the coordinated task breakdown for Sophia enhancements"""

        return [
            SwarmTask(
                task_id=f"{deployment_id}_architecture",
                task_type="architecture_planning",
                description="Design overall architecture for Sophia dashboard enhancements with WebSocket channels, integration improvements, and analytics pipeline",
                priority=10,
                assigned_agents=["lead_architect"],
                context={
                    "existing_infrastructure": {
                        "websocket_manager": "app/core/websocket_manager.py",
                        "message_bus": "app/swarms/communication/message_bus.py",
                        "integrations": ["asana", "linear", "slack"],
                    },
                    "requirements": [
                        "Pay Ready operational intelligence",
                        "Stuck account detection",
                        "Real-time dashboard updates",
                        "Predictive analytics",
                    ],
                },
            ),
            SwarmTask(
                task_id=f"{deployment_id}_websocket_extension",
                task_type="websocket_enhancement",
                description="Extend WebSocket manager with Sophia-specific channels for Pay Ready data streaming and real-time dashboard updates",
                priority=9,
                assigned_agents=["integration_specialist", "ui_enhancement"],
                context={
                    "target_channels": [
                        "sophia_pay_ready",
                        "stuck_accounts",
                        "team_performance",
                        "operational_intelligence",
                    ]
                },
            ),
            SwarmTask(
                task_id=f"{deployment_id}_integration_enhancement",
                task_type="integration_improvement",
                description="Enhance Asana, Linear, and Slack integrations with stuck account detection algorithms and operational intelligence gathering",
                priority=9,
                assigned_agents=["integration_specialist"],
                context={
                    "integrations_to_enhance": ["asana", "linear", "slack"],
                    "stuck_account_criteria": [
                        "Overdue tasks > 7 days",
                        "No activity > 3 days",
                        "Missed deadlines pattern",
                        "Low completion velocity",
                    ],
                },
            ),
            SwarmTask(
                task_id=f"{deployment_id}_predictive_analytics",
                task_type="analytics_development",
                description="Build predictive analytics engine for stuck account prediction and team performance metrics with real-time processing",
                priority=8,
                assigned_agents=["analytics_agent"],
                context={
                    "analytics_requirements": [
                        "Stuck account prediction model",
                        "Team performance metrics",
                        "Operational intelligence insights",
                        "Real-time data processing",
                    ]
                },
            ),
            SwarmTask(
                task_id=f"{deployment_id}_dashboard_components",
                task_type="ui_development",
                description="Create React dashboard components for real-time operational intelligence display with WebSocket integration",
                priority=8,
                assigned_agents=["ui_enhancement"],
                context={
                    "components_needed": [
                        "Stuck accounts dashboard",
                        "Team performance widgets",
                        "Real-time metrics display",
                        "Predictive insights panel",
                    ]
                },
            ),
            SwarmTask(
                task_id=f"{deployment_id}_testing_validation",
                task_type="quality_assurance",
                description="Create comprehensive test suite and monitoring for swarm deployment validation and performance tracking",
                priority=7,
                assigned_agents=["testing_agent"],
                context={
                    "testing_requirements": [
                        "Integration tests for all components",
                        "WebSocket connection tests",
                        "Swarm orchestration validation",
                        "Performance benchmarks",
                    ]
                },
            ),
        ]

    async def _execute_swarm_tasks(self, tasks: List[SwarmTask]) -> Dict[str, Any]:
        """Execute tasks through coordinated swarm interaction"""
        results = {}

        # Phase 1: Architecture and planning (Lead Architect)
        architecture_task = next(t for t in tasks if t.task_type == "architecture_planning")
        architecture_result = await self.agents["lead_architect"].execute_task(architecture_task)
        results[architecture_task.task_id] = architecture_result

        # Share architectural decisions with all agents via message bus
        await self._share_architectural_decisions(architecture_result)

        # Phase 2: Parallel implementation (Integration, Analytics, UI)
        implementation_tasks = [
            t
            for t in tasks
            if t.task_type
            in [
                "websocket_enhancement",
                "integration_improvement",
                "analytics_development",
                "ui_development",
            ]
        ]

        implementation_results = await asyncio.gather(
            *[
                self._execute_task_with_coordination(task, architecture_result)
                for task in implementation_tasks
            ]
        )

        for i, task in enumerate(implementation_tasks):
            results[task.task_id] = implementation_results[i]

        # Phase 3: Testing and validation (Testing Agent)
        testing_task = next(t for t in tasks if t.task_type == "quality_assurance")
        testing_context = {"implementation_results": implementation_results}
        testing_result = await self.agents["testing_agent"].execute_task(
            testing_task, testing_context
        )
        results[testing_task.task_id] = testing_result

        return results

    async def _execute_task_with_coordination(
        self, task: SwarmTask, architecture_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a task with coordination from other agents"""
        # Add architectural context to task
        enhanced_context = {**task.context, "architecture": architecture_context}

        # Get primary agent for task
        primary_agent_id = task.assigned_agents[0]
        primary_result = await self.agents[primary_agent_id].execute_task(task, enhanced_context)

        # If multiple agents assigned, get additional input
        if len(task.assigned_agents) > 1:
            additional_results = []
            for agent_id in task.assigned_agents[1:]:
                additional_result = await self.agents[agent_id].execute_task(task, enhanced_context)
                additional_results.append(additional_result)
            primary_result["additional_insights"] = additional_results

        return primary_result

    async def _share_architectural_decisions(self, architecture_result: Dict[str, Any]):
        """Share architectural decisions with all agents via message bus"""
        message = SwarmMessage(
            sender_agent_id="lead_architect",
            message_type=MessageType.EVENT,
            content={
                "type": "architectural_decisions",
                "decisions": architecture_result["response"],
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        await self.message_bus.publish(message)

    async def _process_deployment_results(
        self, results: Dict[str, Any], deployment_id: str
    ) -> Dict[str, Any]:
        """Process and aggregate deployment results"""

        total_cost = sum(r.get("cost_estimate", 0) for r in results.values())
        avg_confidence = sum(r.get("confidence", 0) for r in results.values()) / len(results)

        # Extract key deliverables
        deliverables = {}
        for task_id, result in results.items():
            if "architecture" in task_id:
                deliverables["architecture_plan"] = result["response"]
            elif "websocket" in task_id:
                deliverables["websocket_enhancements"] = result["response"]
            elif "integration" in task_id:
                deliverables["integration_improvements"] = result["response"]
            elif "analytics" in task_id:
                deliverables["predictive_analytics"] = result["response"]
            elif "dashboard" in task_id:
                deliverables["ui_components"] = result["response"]
            elif "testing" in task_id:
                deliverables["quality_assurance"] = result["response"]

        return {
            "deployment_id": deployment_id,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "total_cost_usd": total_cost,
            "average_confidence": avg_confidence,
            "tasks_completed": len(results),
            "deliverables": deliverables,
            "agent_contributions": {
                agent_id: [r for r in results.values() if r["agent_id"] == agent_id]
                for agent_id in self.agents.keys()
            },
            "success": avg_confidence > 0.7,
        }

    async def _broadcast_deployment_complete(self, deployment_id: str, result: Dict[str, Any]):
        """Broadcast deployment completion to WebSocket subscribers"""
        await self.websocket_manager.broadcast(
            "swarm_deployments",
            {
                "type": "deployment_complete",
                "deployment_id": deployment_id,
                "status": result["status"],
                "success": result["success"],
                "cost_usd": result["total_cost_usd"],
                "confidence": result["average_confidence"],
                "deliverables_summary": list(result["deliverables"].keys()),
                "timestamp": result["timestamp"],
            },
        )

    def _update_metrics(self, result: Dict[str, Any], execution_time: float):
        """Update orchestrator metrics"""
        self.metrics["tasks_completed"] += result["tasks_completed"]
        self.metrics["total_cost_usd"] += result["total_cost_usd"]

        # Update running averages
        current_avg_time = self.metrics["average_execution_time"]
        completed_count = self.metrics["tasks_completed"]

        self.metrics["average_execution_time"] = (
            current_avg_time * (completed_count - result["tasks_completed"]) + execution_time
        ) / completed_count

        success_count = sum(1 for h in self.execution_history if h.get("success", False))
        success_count += 1 if result["success"] else 0
        total_deployments = len(self.execution_history) + 1

        self.metrics["success_rate"] = success_count / total_deployments

    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get status of a specific deployment"""
        # Check active tasks
        active_task = self.active_tasks.get(deployment_id)
        if active_task:
            return {
                "deployment_id": deployment_id,
                "status": active_task.status,
                "progress": "in_progress",
            }

        # Check execution history
        for execution in self.execution_history:
            if execution.get("deployment_id") == deployment_id:
                return execution

        return {"deployment_id": deployment_id, "status": "not_found"}

    async def get_swarm_metrics(self) -> Dict[str, Any]:
        """Get comprehensive swarm metrics"""
        agent_metrics = {}
        for agent_id, agent in self.agents.items():
            agent_metrics[agent_id] = {
                "executions": len(agent.execution_history),
                "total_cost": sum(h.get("cost_estimate", 0) for h in agent.execution_history),
                "avg_confidence": sum(h.get("confidence", 0) for h in agent.execution_history)
                / max(len(agent.execution_history), 1),
                "specializations": agent.config.specialized_capabilities,
            }

        return {
            **self.metrics,
            "agent_metrics": agent_metrics,
            "active_deployments": len(self.active_tasks),
            "total_deployments": len(self.execution_history),
        }

    async def cleanup(self):
        """Cleanup all agent resources"""
        for agent in self.agents.values():
            await agent.cleanup()


# Factory function to create configured orchestrator
def create_artemis_swarm_orchestrator(
    websocket_manager: WebSocketManager, message_bus: MessageBus
) -> ArtemisSwarmOrchestrator:
    """Create and configure the Artemis swarm orchestrator"""
    return ArtemisSwarmOrchestrator(websocket_manager, message_bus)
