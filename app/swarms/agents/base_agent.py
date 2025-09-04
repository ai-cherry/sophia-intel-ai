"""
Enhanced Base Agent with Agno Framework Integration

Combines our existing swarm communication with advanced agent capabilities:
- ReAct reasoning loops with tool validation
- Portkey/OpenRouter model routing (GPT-5 + Grok-4)
- Advanced memory and knowledge retrieval
- Production-ready error handling and observability
- Multi-agent coordination and team support
"""

import asyncio
import logging
import time
from abc import ABC
from collections.abc import Callable
from datetime import datetime
from typing import Any, Optional, Union
from uuid import uuid4

from app.core.ai_logger import logger
from app.core.circuit_breaker import with_circuit_breaker
from app.core.observability import get_tracer
# DEPRECATED: LangChain RAG pipeline replaced by AGNO
# from app.infrastructure.langgraph.rag_pipeline import LangGraphRAGPipeline
# TODO: Replace with AGNO-based RAG pipeline
from app.infrastructure.models.portkey_router import PortkeyRouterModel
from app.memory.unified_memory_store import UnifiedMemoryStore
from app.swarms.communication.message_bus import MessageBus, MessageType, SwarmMessage
from app.tools.integrated_manager import IntegratedToolManager

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)

class AgentRole:
    """Predefined agent roles with optimized configurations"""
    PLANNER = "planner"
    CODER = "coder"
    CRITIC = "critic"
    RESEARCHER = "researcher"
    SECURITY = "security"
    TESTER = "tester"
    ORCHESTRATOR = "orchestrator"


class ReActStep:
    """Individual step in ReAct reasoning loop"""

    def __init__(self, step_type: str, content: str, tool_call: Optional[dict] = None, observation: Optional[str] = None):
        self.step_type = step_type  # "thought", "action", "observation"
        self.content = content
        self.tool_call = tool_call
        self.observation = observation
        self.timestamp = datetime.now()


class BaseAgent(ABC):
    """
    Enhanced base class for all Sophia AI agents.
    
    Features:
    - GPT-5/Grok-4 model routing via Portkey
    - ReAct reasoning loops with tool validation
    - Advanced memory and knowledge retrieval
    - Multi-agent communication and coordination
    - Production-ready error handling and observability
    - Context-aware guardrails and safety measures
    """

    def __init__(
        self,
        agent_id: str,
        role: str = AgentRole.PLANNER,
        model_config: Optional[dict] = None,
        enable_reasoning: bool = True,
        enable_memory: bool = True,
        enable_knowledge: bool = True,
        max_reasoning_steps: int = 10,
        tools: Optional[list] = None,
        guardrails: Optional[list[Callable]] = None,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize enhanced agent with advanced capabilities.
        
        Args:
            agent_id: Unique identifier for the agent
            role: Agent role (affects model selection and behavior)
            model_config: Custom model configuration
            enable_reasoning: Whether to use ReAct reasoning loops
            enable_memory: Whether to enable memory retrieval
            enable_knowledge: Whether to enable knowledge/RAG retrieval
            max_reasoning_steps: Maximum steps in reasoning loop
            tools: List of available tools for the agent
            guardrails: List of input/output validation functions
            system_prompt: Custom system prompt for the agent
        """

        self.agent_id = agent_id
        self.role = role
        self.enable_reasoning = enable_reasoning
        self.enable_memory = enable_memory
        self.enable_knowledge = enable_knowledge
        self.max_reasoning_steps = max_reasoning_steps
        self.guardrails = guardrails or []

        # Initialize model router with Portkey/OpenRouter fallback
        self.model = PortkeyRouterModel(
            enable_fallback=True,
            enable_emergency_fallback=True,
            **(model_config or {})
        )

        # Initialize memory system
        if self.enable_memory:
            self.memory = UnifiedMemoryStore(
                user_id=f"agent_{agent_id}",
                session_id=f"session_{int(time.time())}"
            )

        # Initialize knowledge/RAG system
        if self.enable_knowledge:
            self.knowledge = LangGraphRAGPipeline()

        # Initialize tool manager
        self.tool_manager = IntegratedToolManager()
        if tools:
            for tool in tools:
                self.tool_manager.register_tool(tool)

        # Agent state tracking
        self.conversation_history: list[dict] = []
        self.reasoning_history: list[ReActStep] = []
        self.context_cache: dict[str, Any] = {}
        self.session_metadata: dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "role": role,
            "total_requests": 0,
            "successful_requests": 0
        }

        # Set up system prompt based on role
        self.system_prompt = system_prompt or self._get_default_system_prompt()

        logger.info(f"✅ Enhanced agent '{agent_id}' initialized with role '{role}'")

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt based on agent role"""

        base_prompt = f"""You are a sophisticated AI agent named {self.agent_id} with the role of {self.role}.

Your capabilities include:
- Advanced reasoning using thought-action-observation loops
- Access to specialized tools for your domain
- Memory of past interactions and context
- Knowledge retrieval from comprehensive databases
- Multi-agent collaboration and communication

Core Principles:
- Think step by step before taking actions
- Validate all tool calls and handle errors gracefully  
- Maintain context awareness throughout interactions
- Collaborate effectively with other agents
- Prioritize accuracy, safety, and helpfulness"""

        role_specific = {
            AgentRole.PLANNER: "\n\nAs a planner, you excel at breaking down complex problems into structured, executable steps. You think strategically about resource allocation, dependencies, and timelines.",

            AgentRole.CODER: "\n\nAs a coder, you write clean, efficient, well-documented code. You understand multiple programming languages and follow best practices for security, performance, and maintainability.",

            AgentRole.CRITIC: "\n\nAs a critic, you provide thoughtful analysis and constructive feedback. You identify potential issues, suggest improvements, and ensure quality standards are met.",

            AgentRole.RESEARCHER: "\n\nAs a researcher, you gather accurate information from multiple sources, synthesize findings, and present clear, well-referenced conclusions.",

            AgentRole.SECURITY: "\n\nAs a security specialist, you identify vulnerabilities, implement protective measures, and ensure systems meet security best practices and compliance requirements.",

            AgentRole.TESTER: "\n\nAs a tester, you design comprehensive test cases, identify edge cases, validate functionality, and ensure robust quality assurance.",

            AgentRole.ORCHESTRATOR: "\n\nAs an orchestrator, you coordinate multiple agents, manage workflows, resolve conflicts, and ensure efficient collaboration toward shared goals."
        }

        return base_prompt + role_specific.get(self.role, "")

    @with_circuit_breaker(name="agent_execute")
    async def execute(self, problem: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent's task with advanced reasoning and error handling.
        
        Args:
            problem: Problem specification with context and requirements
            
        Returns:
            Structured response with results, reasoning trace, and metadata
        """

        with tracer.start_as_current_span(f"agent_{self.agent_id}_execute") as span:
            span.set_attribute("agent_id", self.agent_id)
            span.set_attribute("agent_role", self.role)

            execution_start = time.time()
            self.session_metadata["total_requests"] += 1

            try:
                # Apply input guardrails
                validated_problem = await self._apply_input_guardrails(problem)

                # Retrieve context (memory + knowledge)
                context = await self._retrieve_context(validated_problem)

                # Execute with or without reasoning
                if self.enable_reasoning:
                    result = await self._execute_with_reasoning(validated_problem, context)
                else:
                    result = await self._execute_direct(validated_problem, context)

                # Apply output guardrails
                validated_result = await self._apply_output_guardrails(result)

                # Update memory
                if self.enable_memory:
                    await self._update_memory(validated_problem, validated_result)

                # Track success
                self.session_metadata["successful_requests"] += 1
                span.set_attribute("status", "success")

                execution_time = time.time() - execution_start

                return {
                    "result": validated_result,
                    "agent_id": self.agent_id,
                    "role": self.role,
                    "reasoning_trace": [
                        {
                            "step_type": step.step_type,
                            "content": step.content,
                            "tool_call": step.tool_call,
                            "observation": step.observation,
                            "timestamp": step.timestamp.isoformat()
                        }
                        for step in self.reasoning_history[-10:]  # Last 10 steps
                    ] if self.enable_reasoning else [],
                    "model_stats": self.model.get_stats(),
                    "execution_time": round(execution_time, 3),
                    "context_used": len(context) if context else 0,
                    "success": True
                }

            except Exception as e:
                span.set_attribute("status", "error")
                span.set_attribute("error", str(e))
                logger.error(f"Agent {self.agent_id} execution failed: {e}")

                return {
                    "result": None,
                    "agent_id": self.agent_id,
                    "role": self.role,
                    "error": str(e),
                    "success": False,
                    "execution_time": time.time() - execution_start
                }

    async def _retrieve_context(self, problem: dict[str, Any]) -> list[dict[str, Any]]:
        """Retrieve relevant context from memory and knowledge systems"""

        context = []

        # Retrieve from memory
        if self.enable_memory:
            try:
                query = problem.get("query", str(problem))
                memory_results = await self.memory.search(query, limit=5)
                if memory_results:
                    context.extend([
                        {"source": "memory", "content": result.content, "relevance": result.relevance}
                        for result in memory_results
                    ])
            except Exception as e:
                logger.warning(f"Memory retrieval failed: {e}")

        # Retrieve from knowledge base
        if self.enable_knowledge:
            try:
                query = problem.get("query", str(problem))
                knowledge_results = await self.knowledge.retrieve(query, top_k=5)
                if knowledge_results:
                    context.extend([
                        {"source": "knowledge", "content": doc.page_content, "metadata": doc.metadata}
                        for doc in knowledge_results
                    ])
            except Exception as e:
                logger.warning(f"Knowledge retrieval failed: {e}")

        return context

    async def _execute_with_reasoning(self, problem: dict[str, Any], context: list[dict]) -> Any:
        """Execute with ReAct-style reasoning loop"""

        messages = self._build_initial_messages(problem, context)
        current_step = 0

        while current_step < self.max_reasoning_steps:
            # Generate thought
            thought_response = await self.model(messages + [
                {"role": "user", "content": "Think about the next step. What should you do?"}
            ])

            thought_content = thought_response.get("content", "")
            self.reasoning_history.append(
                ReActStep("thought", thought_content)
            )

            # Check if we need to use a tool
            if "Action:" in thought_content or "TOOL:" in thought_content:
                # Parse tool call
                tool_call = self._parse_tool_call(thought_content)

                if tool_call:
                    # Execute tool
                    try:
                        observation = await self._execute_tool_call(tool_call)

                        self.reasoning_history.append(
                            ReActStep("action", f"Called tool: {tool_call['name']}", tool_call)
                        )
                        self.reasoning_history.append(
                            ReActStep("observation", observation)
                        )

                        # Add observation to messages
                        messages.append({
                            "role": "assistant",
                            "content": f"Thought: {thought_content}\nAction: {tool_call}\nObservation: {observation}"
                        })

                    except Exception as e:
                        error_obs = f"Tool execution failed: {str(e)}"
                        self.reasoning_history.append(
                            ReActStep("observation", error_obs)
                        )
                        messages.append({
                            "role": "assistant",
                            "content": f"Thought: {thought_content}\nAction failed: {error_obs}"
                        })

            # Check if reasoning is complete
            if "Final Answer:" in thought_content or "FINAL:" in thought_content:
                final_answer = self._extract_final_answer(thought_content)
                return final_answer

            current_step += 1

        # Max steps reached, generate final response
        final_messages = messages + [
            {"role": "user", "content": "Please provide your final answer based on your reasoning so far."}
        ]

        final_response = await self.model(final_messages)
        return final_response.get("content", "")

    async def _execute_direct(self, problem: dict[str, Any], context: list[dict]) -> Any:
        """Execute without reasoning loop (single model call)"""

        messages = self._build_initial_messages(problem, context)
        response = await self.model(messages)
        return response.get("content", "")

    def _build_initial_messages(self, problem: dict[str, Any], context: list[dict]) -> list[dict[str, str]]:
        """Build initial message structure for model call"""

        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Add context if available
        if context:
            context_content = "\n\n".join([
                f"From {ctx['source']}: {ctx['content']}"
                for ctx in context[:5]  # Limit to 5 context items
            ])
            messages.append({
                "role": "system",
                "content": f"Relevant context:\n{context_content}"
            })

        # Add the main problem/query
        if isinstance(problem, dict):
            user_message = problem.get("query", problem.get("message", str(problem)))
        else:
            user_message = str(problem)

        messages.append({"role": "user", "content": user_message})

        return messages

    def _parse_tool_call(self, content: str) -> Optional[dict[str, Any]]:
        """Parse tool call from reasoning content"""

        # Simple parsing - can be enhanced
        if "Action:" in content:
            action_part = content.split("Action:")[1].split("Observation:")[0].strip()
            # Extract tool name and parameters
            if "(" in action_part and ")" in action_part:
                tool_name = action_part.split("(")[0].strip()
                params_str = action_part.split("(")[1].split(")")[0]

                return {
                    "name": tool_name,
                    "parameters": {"query": params_str}  # Simplified
                }

        return None

    async def _execute_tool_call(self, tool_call: dict[str, Any]) -> str:
        """Execute a validated tool call"""

        tool_name = tool_call.get("name")
        if not tool_name:
            raise ValueError("No tool name specified")

        # Check if tool is available
        if not self.tool_manager.has_tool(tool_name):
            raise ValueError(f"Tool '{tool_name}' not available")

        # Execute tool
        result = await self.tool_manager.execute_tool(
            tool_name,
            tool_call.get("parameters", {})
        )

        return str(result)

    def _extract_final_answer(self, content: str) -> str:
        """Extract final answer from reasoning content"""

        if "Final Answer:" in content:
            return content.split("Final Answer:")[1].strip()
        elif "FINAL:" in content:
            return content.split("FINAL:")[1].strip()

        return content

    async def _apply_input_guardrails(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Apply input validation and safety guardrails"""

        validated = problem.copy()

        for guardrail in self.guardrails:
            try:
                validated = await guardrail(validated, "input")
            except Exception as e:
                logger.warning(f"Input guardrail failed: {e}")

        return validated

    async def _apply_output_guardrails(self, result: Any) -> Any:
        """Apply output validation and safety guardrails"""

        validated = result

        for guardrail in self.guardrails:
            try:
                validated = await guardrail(validated, "output")
            except Exception as e:
                logger.warning(f"Output guardrail failed: {e}")

        return validated

    async def _update_memory(self, problem: dict[str, Any], result: Any):
        """Update agent memory with interaction"""

        try:
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "problem": str(problem),
                "result": str(result),
                "agent_id": self.agent_id,
                "role": self.role
            }

            await self.memory.add_interaction(interaction)

        except Exception as e:
            logger.warning(f"Memory update failed: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive agent statistics"""

        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "session_metadata": self.session_metadata,
            "model_stats": self.model.get_stats(),
            "reasoning_steps": len(self.reasoning_history),
            "conversation_length": len(self.conversation_history),
            "context_cache_size": len(self.context_cache),
            "capabilities": {
                "reasoning": self.enable_reasoning,
                "memory": self.enable_memory,
                "knowledge": self.enable_knowledge,
                "tools": len(self.tool_manager.get_available_tools()) if hasattr(self.tool_manager, 'get_available_tools') else 0
            }
        }

class CommunicativeAgent(BaseAgent):
    """
    Enhanced agent with inter-agent communication capabilities.
    
    Combines advanced BaseAgent features with swarm communication:
    - Multi-agent coordination via message bus
    - Proposal broadcasting and voting
    - Expert consultation requests
    - Cross-agent knowledge sharing
    """

    def __init__(
        self,
        agent_id: str,
        bus: MessageBus,
        role: str = AgentRole.PLANNER,
        **kwargs
    ):
        # Initialize base agent with all advanced capabilities
        super().__init__(agent_id=agent_id, role=role, **kwargs)

        # Add communication capabilities
        self.bus = bus

        logger.info(f"✅ Communicative agent '{agent_id}' initialized with swarm communication")

    async def send_query(self, target_agent_id: str, query: str) -> str:
        """Send a query to another agent and wait for a response"""
        # Generate a thread ID for the query response
        thread_id = f"query:{self.agent_id}:{target_agent_id}:{uuid4().hex}"

        # Create a query message
        message = SwarmMessage(
            sender_agent_id=self.agent_id,
            receiver_agent_id=target_agent_id,
            message_type=MessageType.QUERY,
            content={"query": query, "thread_id": thread_id},
            priority=7
        )

        # Publish the message
        await self.bus.publish(message)

        # Wait for a response on this thread
        async for response in self.bus.subscribe(
            self.agent_id,
            [MessageType.RESPONSE]
        ):
            if response.thread_id == thread_id:
                return response.content.get("response", "No response")

        return "No response received"

    async def broadcast_proposal(self, proposal: dict[str, Any]) -> list[dict]:
        """Broadcast a proposal to all agents and collect responses"""
        # We'll create a thread for the broadcast
        thread_id = f"proposal:{self.agent_id}:{proposal.get('id', 'unknown')}"

        # Create and publish the proposal message
        message = SwarmMessage(
            sender_agent_id=self.agent_id,
            receiver_agent_id=None,  # Broadcast
            message_type=MessageType.PROPOSAL,
            content={"proposal": proposal, "thread_id": thread_id},
            priority=5
        )
        await self.bus.publish(message)

        # Collect responses from the bus
        responses = []
        async for response in self.bus.subscribe(
            self.agent_id,
            [MessageType.RESPONSE]
        ):
            if response.thread_id == thread_id:
                responses.append(response.content)

        return responses

    async def vote_on_proposal(self, proposal_id: str, vote: str) -> None:
        """Vote on a proposal (which must be on a thread)"""
        # Create a vote message
        message = SwarmMessage(
            sender_agent_id=self.agent_id,
            receiver_agent_id=None,  # Broadcast vote to proposal thread
            message_type=MessageType.VOTE,
            content={"proposal_id": proposal_id, "vote": vote},
            priority=6
        )
        await self.bus.publish(message)

    async def request_expertise(self, domain: str, question: str) -> str:
        """Request expertise from a domain expert agent"""
        # In reality, we'd use the registry to find an expert agent
        # For now, we'll use a fixed pattern for expert agents
        expert_agent_id = f"expert_agent_{domain.replace(' ', '_').lower()}"
        return await self.send_query(expert_agent_id, f"Expertise question: {domain} - {question}")

    # Message handlers - to be implemented by subclasses
    async def on_query_received(self, message: SwarmMessage) -> dict:
        """Handle a query message"""
        return {"response": "Query handled", "context": message.content}

    async def on_proposal_received(self, message: SwarmMessage) -> dict:
        """Handle a proposal message"""
        return {"response": "Proposal handled", "context": message.content}

    async def on_vote_request(self, message: SwarmMessage) -> dict:
        """Handle a vote request (e.g., for a proposal)"""
        return {"response": "Vote handled", "context": message.content}

# Example usage
if __name__ == "__main__":
    async def demo():
        # Initialize message bus and agent
        bus = MessageBus()
        await bus.initialize()
        agent = CommunicativeAgent("agent_1", bus)

        # Test query
        response = await agent.send_query("agent_2", "What is 2+2?")
        logger.info(f"Query result: {response}")

        # Test proposal broadcast
        proposal = {"title": "Test Proposal", "content": "Testing message bus"}
        responses = await agent.broadcast_proposal(proposal)
        logger.info(f"Proposal responses: {responses}")

        await bus.close()

    import asyncio
    asyncio.run(demo())
