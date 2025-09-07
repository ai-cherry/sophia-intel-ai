"""
Base Micro-Swarm Architecture
3-agent coordination system for specialized AI reasoning
"""

import asyncio
import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.core.portkey_manager import TaskType, get_portkey_manager
from app.memory.unified_memory_router import DocChunk, MemoryDomain, get_memory_router
from app.models.approved_models import is_model_approved
from app.models.llm_policy import get_llm_policy
from app.orchestrators.base_orchestrator import BaseOrchestrator, Result, Task

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Roles within micro-swarm coordination"""

    ANALYST = "analyst"  # Deep analysis and research
    STRATEGIST = "strategist"  # Planning and synthesis
    VALIDATOR = "validator"  # Quality control and verification


class CoordinationPattern(Enum):
    """Coordination patterns for agent interaction"""

    SEQUENTIAL = "sequential"  # One agent -> next agent -> final agent
    PARALLEL = "parallel"  # All agents work simultaneously, then merge
    DEBATE = "debate"  # Agents challenge each other's reasoning
    HIERARCHICAL = "hierarchical"  # Lead agent coordinates sub-agents
    CONSENSUS = "consensus"  # Agents must reach agreement


class MessageType(Enum):
    """Types of messages in agent braiding"""

    TASK_ASSIGNMENT = "task_assignment"
    ANALYSIS_RESULT = "analysis_result"
    CHALLENGE = "challenge"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    FINAL_OUTPUT = "final_output"


@dataclass
class SwarmMessage:
    """Message passed between agents in micro-swarm"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_role: AgentRole = None
    recipient_role: Optional[AgentRole] = None
    message_type: MessageType = MessageType.ANALYSIS_RESULT
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    reasoning: str = ""
    citations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    thread_id: str = ""


@dataclass
class AgentProfile:
    """Profile defining agent capabilities and behavior"""

    role: AgentRole
    name: str
    description: str
    model_preferences: List[str]  # Preferred LLM models
    specializations: List[str]
    reasoning_style: str
    confidence_threshold: float = 0.8
    max_tokens: int = 4000
    temperature: float = 0.2


@dataclass
class SwarmConfig:
    """Configuration for micro-swarm execution"""

    name: str
    domain: MemoryDomain
    coordination_pattern: CoordinationPattern
    agents: List[AgentProfile]
    max_iterations: int = 3
    consensus_threshold: float = 0.85
    timeout_seconds: int = 120
    enable_memory_integration: bool = True
    enable_debate: bool = True
    cost_limit_usd: float = 1.0


@dataclass
class SwarmResult:
    """Result from micro-swarm execution"""

    success: bool
    final_output: str
    confidence: float
    reasoning_chain: List[SwarmMessage]
    agent_contributions: Dict[AgentRole, List[SwarmMessage]]
    consensus_achieved: bool
    iterations_used: int
    total_cost: float
    execution_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class MicroSwarmAgent:
    """Individual agent within micro-swarm"""

    def __init__(self, profile: AgentProfile, swarm_id: str):
        self.profile = profile
        self.swarm_id = swarm_id
        self.message_history: List[SwarmMessage] = []
        self.portkey = get_portkey_manager()
        self.memory = get_memory_router()

    async def process_message(self, message: SwarmMessage, context: Dict[str, Any]) -> SwarmMessage:
        """Process incoming message and generate response"""

        # Add to message history
        self.message_history.append(message)

        # Build prompt based on role and message type
        prompt = await self._build_role_prompt(message, context)

        # Build messages
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": message.content},
        ]

        try:
            policy = get_llm_policy()
            # Clamp output tokens to a sane ceiling to avoid provider errors
            try:
                max_tokens_cap = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "8000"))
            except Exception:
                max_tokens_cap = 8000
            safe_max_tokens = min(self.profile.max_tokens, max_tokens_cap)
            if policy.mode == "manual":
                # Strict manual mode: allow per-role overrides; fall back to global force vars
                role_key = self.profile.role.value.upper()  # ANALYST/STRATEGIST/VALIDATOR
                provider = os.getenv(f"LLM_{role_key}_PROVIDER") or os.getenv("LLM_FORCE_PROVIDER")
                model = os.getenv(f"LLM_{role_key}_MODEL") or os.getenv("LLM_FORCE_MODEL")
                if not provider or not model:
                    raise RuntimeError(
                        "LLM manual mode active. Set LLM_FORCE_PROVIDER/LLM_FORCE_MODEL or per-role LLM_"
                        f"{role_key}_PROVIDER / LLM_{role_key}_MODEL to proceed."
                    )
                # Enforce central approval list unless explicitly disabled
                if (
                    os.getenv("LLM_APPROVAL_STRICT", "true").lower() in {"1", "true", "yes"}
                ) and not is_model_approved(provider, model):
                    raise RuntimeError(
                        f"Model not approved: provider='{provider}', model='{model}'."
                        " Update app/models/approved_models.py or set LLM_APPROVAL_STRICT=false to override."
                    )
                response = await self.portkey.execute_manual(
                    provider=provider,
                    model=model,
                    messages=messages,
                    max_tokens=safe_max_tokens,
                    temperature=self.profile.temperature,
                )
                model_used = f"{provider}/{model}"
                est_cost = 0.0
            else:
                # Auto mode: use routing + fallbacks
                routing = self.portkey.route_request(
                    task_type=self._get_task_type(),
                    estimated_tokens=self.profile.max_tokens,
                    prefer_provider=(
                        self.profile.model_preferences[0]
                        if self.profile.model_preferences
                        else None
                    ),
                )
                response = await self.portkey.execute_with_fallback(
                    task_type=self._get_task_type(),
                    messages=messages,
                    max_tokens=safe_max_tokens,
                    temperature=self.profile.temperature,
                )
                model_used = routing.model
                est_cost = routing.estimated_cost

            # Parse response
            response_content = response.choices[0].message.content

            # Create response message
            response_msg = SwarmMessage(
                sender_role=self.profile.role,
                message_type=self._get_response_type(message.message_type),
                content=response_content,
                confidence=self._extract_confidence(response_content),
                reasoning=self._extract_reasoning(response_content),
                thread_id=message.thread_id,
                metadata={
                    "model_used": model_used,
                    "tokens_used": getattr(response, "usage", {}).get("total_tokens", 0),
                    "cost": est_cost,
                },
            )

            return response_msg

        except Exception as e:
            logger.error(f"Agent {self.profile.name} failed to process message: {e}")
            return SwarmMessage(
                sender_role=self.profile.role,
                message_type=MessageType.ANALYSIS_RESULT,
                content=f"Error processing request: {str(e)}",
                confidence=0.0,
                thread_id=message.thread_id,
            )

    async def _build_role_prompt(self, message: SwarmMessage, context: Dict[str, Any]) -> str:
        """Build role-specific prompt"""

        base_prompt = f"""You are {self.profile.name}, a {self.profile.role.value} in a micro-swarm AI system.

Your role: {self.profile.description}
Your specializations: {', '.join(self.profile.specializations)}
Your reasoning style: {self.profile.reasoning_style}

You are part of a collaborative system working on: {context.get('original_task', 'Unknown task')}

Current coordination pattern: {context.get('coordination_pattern', 'Unknown')}
"""

        # Add message history context
        if self.message_history:
            base_prompt += "\n\nPrevious messages in this thread:\n"
            for msg in self.message_history[-3:]:  # Last 3 messages
                role_label = (
                    msg.sender_role.value if getattr(msg, "sender_role", None) else "system"
                )
                base_prompt += f"- {role_label}: {msg.content[:200]}...\n"

        # Role-specific instructions
        if self.profile.role == AgentRole.ANALYST:
            base_prompt += """
Your job is to:
1. Perform deep analysis of the given information
2. Identify patterns, insights, and key findings
3. Ask probing questions to uncover deeper understanding
4. Provide detailed reasoning with evidence

Always include:
- CONFIDENCE: Your confidence level (0.0-1.0)
- REASONING: Your step-by-step thinking process
- FINDINGS: Key discoveries and insights
"""

        elif self.profile.role == AgentRole.STRATEGIST:
            base_prompt += """
Your job is to:
1. Synthesize information from multiple sources
2. Develop strategic recommendations and plans
3. Consider trade-offs and alternatives
4. Focus on actionable outcomes

Always include:
- CONFIDENCE: Your confidence level (0.0-1.0)
- REASONING: Your strategic thinking process
- STRATEGY: Clear strategic recommendations
- NEXT_STEPS: Specific actions to take
"""

        elif self.profile.role == AgentRole.VALIDATOR:
            base_prompt += """
Your job is to:
1. Critically evaluate proposals and analyses
2. Identify potential flaws, gaps, or risks
3. Verify facts and logic
4. Ensure quality and accuracy

Always include:
- CONFIDENCE: Your confidence level (0.0-1.0)
- REASONING: Your validation process
- ISSUES: Any problems or concerns identified
- VERIFICATION: Confirmation of key facts
"""

        return base_prompt

    def _get_task_type(self) -> TaskType:
        """Get appropriate task type for routing"""
        if self.profile.role == AgentRole.ANALYST:
            return TaskType.WEB_RESEARCH
        elif self.profile.role == AgentRole.STRATEGIST:
            return TaskType.LONG_PLANNING
        else:  # VALIDATOR
            return TaskType.CODE_REVIEW

    def _get_response_type(self, input_type: MessageType) -> MessageType:
        """Determine response message type"""
        if input_type == MessageType.TASK_ASSIGNMENT:
            return MessageType.ANALYSIS_RESULT
        elif input_type == MessageType.CHALLENGE:
            return MessageType.VALIDATION
        else:
            return MessageType.SYNTHESIS

    def _extract_confidence(self, content: str) -> float:
        """Extract confidence score from response"""
        try:
            if "CONFIDENCE:" in content:
                line = [l for l in content.split("\n") if "CONFIDENCE:" in l][0]
                score_str = line.split("CONFIDENCE:")[1].strip().split()[0]
                return float(score_str)
        except:
            pass
        return 0.75  # Default confidence - improved based on empirical data

    def _extract_reasoning(self, content: str) -> str:
        """Extract reasoning section from response"""
        try:
            if "REASONING:" in content:
                lines = content.split("\n")
                reasoning_start = next(i for i, l in enumerate(lines) if "REASONING:" in l)
                reasoning_end = len(lines)
                for i in range(reasoning_start + 1, len(lines)):
                    if any(
                        marker in lines[i]
                        for marker in ["FINDINGS:", "STRATEGY:", "ISSUES:", "VERIFICATION:"]
                    ):
                        reasoning_end = i
                        break
                return (
                    "\n".join(lines[reasoning_start:reasoning_end])
                    .replace("REASONING:", "")
                    .strip()
                )
        except:
            pass
        return ""


class MicroSwarmCoordinator:
    """Coordinates execution of micro-swarm with 3-agent pattern"""

    def __init__(self, config: SwarmConfig):
        self.config = config
        self.agents: Dict[AgentRole, MicroSwarmAgent] = {}
        self.message_threads: Dict[str, List[SwarmMessage]] = {}
        self.memory = get_memory_router()
        self.swarm_id = str(uuid.uuid4())

        # Initialize agents
        for agent_profile in config.agents:
            self.agents[agent_profile.role] = MicroSwarmAgent(agent_profile, self.swarm_id)

        logger.info(f"Initialized micro-swarm '{config.name}' with {len(self.agents)} agents")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> SwarmResult:
        """Execute micro-swarm coordination"""
        start_time = datetime.now()
        thread_id = str(uuid.uuid4())
        context = context or {}
        context.update(
            {
                "original_task": task,
                "coordination_pattern": self.config.coordination_pattern.value,
                "swarm_name": self.config.name,
            }
        )

        result = SwarmResult(
            success=False,
            final_output="",
            confidence=0.0,
            reasoning_chain=[],
            agent_contributions={role: [] for role in AgentRole},
            consensus_achieved=False,
            iterations_used=0,
            total_cost=0.0,
            execution_time_ms=0.0,
        )

        try:
            # Load relevant memory context
            if self.config.enable_memory_integration:
                memory_context = await self._load_memory_context(task)
                context["memory_context"] = memory_context

            # Execute coordination pattern
            if self.config.coordination_pattern == CoordinationPattern.SEQUENTIAL:
                result = await self._execute_sequential(task, context, thread_id)
            elif self.config.coordination_pattern == CoordinationPattern.PARALLEL:
                result = await self._execute_parallel(task, context, thread_id)
            elif self.config.coordination_pattern == CoordinationPattern.DEBATE:
                result = await self._execute_debate(task, context, thread_id)
            elif self.config.coordination_pattern == CoordinationPattern.CONSENSUS:
                result = await self._execute_consensus(task, context, thread_id)
            else:
                result = await self._execute_hierarchical(task, context, thread_id)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time

            # Store results in memory
            if self.config.enable_memory_integration and result.success:
                await self._store_swarm_results(task, result)

            logger.info(f"Micro-swarm '{self.config.name}' completed in {execution_time:.2f}ms")

        except Exception as e:
            logger.error(f"Micro-swarm execution failed: {e}")
            result.errors.append(str(e))

        return result

    async def _execute_sequential(
        self, task: str, context: Dict[str, Any], thread_id: str
    ) -> SwarmResult:
        """Execute sequential coordination (Analyst -> Strategist -> Validator)"""

        current_content = task
        messages = []
        total_cost = 0.0

        # Sequential flow: Analyst -> Strategist -> Validator
        agent_order = [AgentRole.ANALYST, AgentRole.STRATEGIST, AgentRole.VALIDATOR]

        for i, role in enumerate(agent_order):
            if role not in self.agents:
                continue

            agent = self.agents[role]

            # Create message for agent
            message = SwarmMessage(
                recipient_role=role,
                message_type=MessageType.TASK_ASSIGNMENT if i == 0 else MessageType.SYNTHESIS,
                content=current_content,
                thread_id=thread_id,
            )

            # Process message
            response = await agent.process_message(message, context)
            messages.append(response)
            total_cost += response.metadata.get("cost", 0.0)

            # Update content for next agent
            current_content = response.content

        # Final result
        final_confidence = messages[-1].confidence if messages else 0.0

        return SwarmResult(
            success=True,
            final_output=current_content,
            confidence=final_confidence,
            reasoning_chain=messages,
            agent_contributions=self._organize_contributions(messages),
            consensus_achieved=final_confidence >= self.config.consensus_threshold,
            iterations_used=1,
            total_cost=total_cost,
            execution_time_ms=0.0,
        )

    async def _execute_parallel(
        self, task: str, context: Dict[str, Any], thread_id: str
    ) -> SwarmResult:
        """Execute parallel coordination - all agents work simultaneously"""

        messages = []
        total_cost = 0.0

        # Create tasks for all agents simultaneously
        tasks = []
        for role, agent in self.agents.items():
            message = SwarmMessage(
                recipient_role=role,
                message_type=MessageType.TASK_ASSIGNMENT,
                content=task,
                thread_id=thread_id,
            )
            tasks.append(agent.process_message(message, context))

        # Execute all agents in parallel
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process responses
        valid_responses = []
        for response in responses:
            if isinstance(response, SwarmMessage):
                messages.append(response)
                valid_responses.append(response)
                total_cost += response.metadata.get("cost", 0.0)

        # Synthesize results
        if valid_responses:
            synthesis_content = await self._synthesize_parallel_results(valid_responses, context)
            avg_confidence = sum(r.confidence for r in valid_responses) / len(valid_responses)
        else:
            synthesis_content = "No valid responses from agents"
            avg_confidence = 0.0

        return SwarmResult(
            success=len(valid_responses) > 0,
            final_output=synthesis_content,
            confidence=avg_confidence,
            reasoning_chain=messages,
            agent_contributions=self._organize_contributions(messages),
            consensus_achieved=avg_confidence >= self.config.consensus_threshold,
            iterations_used=1,
            total_cost=total_cost,
            execution_time_ms=0.0,
        )

    async def _execute_debate(
        self, task: str, context: Dict[str, Any], thread_id: str
    ) -> SwarmResult:
        """Execute debate coordination - agents challenge each other"""

        messages = []
        total_cost = 0.0
        iterations = 0

        # Initial analysis phase
        if AgentRole.ANALYST in self.agents:
            initial_msg = SwarmMessage(
                recipient_role=AgentRole.ANALYST,
                message_type=MessageType.TASK_ASSIGNMENT,
                content=task,
                thread_id=thread_id,
            )

            response = await self.agents[AgentRole.ANALYST].process_message(initial_msg, context)
            messages.append(response)
            total_cost += response.metadata.get("cost", 0.0)
            current_analysis = response.content
        else:
            current_analysis = task

        # Debate rounds
        for iteration in range(self.config.max_iterations):
            iterations = iteration + 1
            round_messages = []

            # Strategist challenges/builds on analysis
            if AgentRole.STRATEGIST in self.agents:
                challenge_msg = SwarmMessage(
                    sender_role=AgentRole.ANALYST,
                    recipient_role=AgentRole.STRATEGIST,
                    message_type=MessageType.CHALLENGE,
                    content=f"Current analysis: {current_analysis}\n\nProvide your strategic perspective and challenge any assumptions.",
                    thread_id=thread_id,
                )

                strategy_response = await self.agents[AgentRole.STRATEGIST].process_message(
                    challenge_msg, context
                )
                round_messages.append(strategy_response)
                total_cost += strategy_response.metadata.get("cost", 0.0)

            # Validator evaluates both
            if AgentRole.VALIDATOR in self.agents and round_messages:
                validation_msg = SwarmMessage(
                    sender_role=AgentRole.STRATEGIST,
                    recipient_role=AgentRole.VALIDATOR,
                    message_type=MessageType.VALIDATION,
                    content=f"Original analysis: {current_analysis}\n\nStrategic response: {round_messages[-1].content}\n\nValidate and identify any issues or improvements needed.",
                    thread_id=thread_id,
                )

                validation_response = await self.agents[AgentRole.VALIDATOR].process_message(
                    validation_msg, context
                )
                round_messages.append(validation_response)
                total_cost += validation_response.metadata.get("cost", 0.0)

            messages.extend(round_messages)

            # Check for consensus
            if round_messages:
                avg_confidence = sum(msg.confidence for msg in round_messages) / len(round_messages)
                if avg_confidence >= self.config.consensus_threshold:
                    break

        # Final synthesis
        final_output = await self._create_debate_synthesis(messages, context)
        final_confidence = messages[-1].confidence if messages else 0.0

        return SwarmResult(
            success=True,
            final_output=final_output,
            confidence=final_confidence,
            reasoning_chain=messages,
            agent_contributions=self._organize_contributions(messages),
            consensus_achieved=final_confidence >= self.config.consensus_threshold,
            iterations_used=iterations,
            total_cost=total_cost,
            execution_time_ms=0.0,
        )

    async def _execute_consensus(
        self, task: str, context: Dict[str, Any], thread_id: str
    ) -> SwarmResult:
        """Execute consensus coordination - agents must agree"""

        messages = []
        total_cost = 0.0
        consensus_achieved = False

        for iteration in range(self.config.max_iterations):
            # Get input from all agents
            round_messages = []

            for role, agent in self.agents.items():
                if iteration == 0:
                    message = SwarmMessage(
                        recipient_role=role,
                        message_type=MessageType.TASK_ASSIGNMENT,
                        content=task,
                        thread_id=thread_id,
                    )
                else:
                    # Include previous round context
                    prev_context = "\n\n".join(
                        [
                            f"{msg.sender_role.value}: {msg.content}"
                            for msg in messages[-len(self.agents) :]
                        ]
                    )
                    message = SwarmMessage(
                        recipient_role=role,
                        message_type=MessageType.SYNTHESIS,
                        content=f"Original task: {task}\n\nPrevious round:\n{prev_context}\n\nProvide your updated perspective for consensus.",
                        thread_id=thread_id,
                    )

                response = await agent.process_message(message, context)
                round_messages.append(response)
                total_cost += response.metadata.get("cost", 0.0)

            messages.extend(round_messages)

            # Check consensus
            confidences = [msg.confidence for msg in round_messages]
            avg_confidence = sum(confidences) / len(confidences)
            confidence_variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(
                confidences
            )

            if avg_confidence >= self.config.consensus_threshold and confidence_variance < 0.1:
                consensus_achieved = True
                break

        # Synthesize consensus
        final_output = await self._create_consensus_synthesis(
            messages[-len(self.agents) :], context
        )

        return SwarmResult(
            success=consensus_achieved,
            final_output=final_output,
            confidence=avg_confidence,
            reasoning_chain=messages,
            agent_contributions=self._organize_contributions(messages),
            consensus_achieved=consensus_achieved,
            iterations_used=iteration + 1,
            total_cost=total_cost,
            execution_time_ms=0.0,
        )

    async def _execute_hierarchical(
        self, task: str, context: Dict[str, Any], thread_id: str
    ) -> SwarmResult:
        """Execute hierarchical coordination - Strategist leads, coordinates others"""

        messages = []
        total_cost = 0.0

        # Strategist as coordinator assigns sub-tasks
        if AgentRole.STRATEGIST not in self.agents:
            return SwarmResult(
                success=False,
                final_output="No strategist agent available",
                confidence=0.0,
                reasoning_chain=[],
                agent_contributions={},
                consensus_achieved=False,
                iterations_used=0,
                total_cost=0.0,
                execution_time_ms=0.0,
            )

        coordinator = self.agents[AgentRole.STRATEGIST]

        # Initial coordination
        coord_msg = SwarmMessage(
            recipient_role=AgentRole.STRATEGIST,
            message_type=MessageType.TASK_ASSIGNMENT,
            content=f"As the coordinator, break down this task and determine how to utilize the other agents: {task}",
            thread_id=thread_id,
        )

        coord_response = await coordinator.process_message(coord_msg, context)
        messages.append(coord_response)
        total_cost += coord_response.metadata.get("cost", 0.0)

        # Execute sub-tasks with other agents
        sub_tasks = []
        for role, agent in self.agents.items():
            if role != AgentRole.STRATEGIST:
                sub_msg = SwarmMessage(
                    sender_role=AgentRole.STRATEGIST,
                    recipient_role=role,
                    message_type=MessageType.TASK_ASSIGNMENT,
                    content=f"Coordinator directive: {coord_response.content}\n\nYour specific task: {task}",
                    thread_id=thread_id,
                )
                sub_tasks.append(agent.process_message(sub_msg, context))

        # Execute sub-tasks
        if sub_tasks:
            sub_responses = await asyncio.gather(*sub_tasks, return_exceptions=True)
            for response in sub_responses:
                if isinstance(response, SwarmMessage):
                    messages.append(response)
                    total_cost += response.metadata.get("cost", 0.0)

        # Final coordination
        if len(messages) > 1:
            sub_results = "\n\n".join(
                [f"{msg.sender_role.value}: {msg.content}" for msg in messages[1:]]
            )
            final_msg = SwarmMessage(
                message_type=MessageType.SYNTHESIS,
                content=f"Original task: {task}\n\nSub-agent results:\n{sub_results}\n\nProvide final synthesis.",
                thread_id=thread_id,
            )

            final_response = await coordinator.process_message(final_msg, context)
            messages.append(final_response)
            total_cost += final_response.metadata.get("cost", 0.0)

            final_output = final_response.content
            final_confidence = final_response.confidence
        else:
            final_output = coord_response.content
            final_confidence = coord_response.confidence

        return SwarmResult(
            success=True,
            final_output=final_output,
            confidence=final_confidence,
            reasoning_chain=messages,
            agent_contributions=self._organize_contributions(messages),
            consensus_achieved=final_confidence >= self.config.consensus_threshold,
            iterations_used=1,
            total_cost=total_cost,
            execution_time_ms=0.0,
        )

    async def _load_memory_context(self, task: str) -> Dict[str, Any]:
        """Load relevant context from memory"""
        try:
            # Search for relevant information
            hits = await self.memory.search(query=task, domain=self.config.domain, k=5)
            if not hits:
                hits = []

            return {
                "relevant_documents": [
                    {"content": hit.content[:500], "source": hit.source_uri, "score": hit.score}
                    for hit in hits
                ],
                "document_count": len(hits),
            }
        except Exception as e:
            logger.error(f"Failed to load memory context: {e}")
            return {}

    async def _store_swarm_results(self, task: str, result: SwarmResult) -> None:
        """Store swarm execution results in memory"""
        try:
            # Create document chunk
            chunk = DocChunk(
                content=json.dumps(
                    {
                        "task": task,
                        "result": result.final_output,
                        "reasoning_chain": [msg.content[:200] for msg in result.reasoning_chain],
                        "confidence": result.confidence,
                        "consensus_achieved": result.consensus_achieved,
                    }
                ),
                source_uri=f"swarm://{self.config.name}/{self.swarm_id}",
                domain=self.config.domain,
                metadata={
                    "swarm_name": self.config.name,
                    "coordination_pattern": self.config.coordination_pattern.value,
                    "agents_used": [role.value for role in result.agent_contributions.keys()],
                    "execution_time_ms": result.execution_time_ms,
                    "cost_usd": result.total_cost,
                },
                confidence=result.confidence,
            )

            await self.memory.upsert_chunks([chunk], self.config.domain)

        except Exception as e:
            logger.error(f"Failed to store swarm results: {e}")

    async def _synthesize_parallel_results(
        self, responses: List[SwarmMessage], context: Dict[str, Any]
    ) -> str:
        """Synthesize results from parallel execution"""
        synthesis = f"Synthesis of {len(responses)} parallel agent analyses:\n\n"

        for response in responses:
            synthesis += f"{response.sender_role.value.upper()}:\n{response.content[:300]}...\n\n"

        synthesis += "INTEGRATED CONCLUSION:\n"
        synthesis += "Based on the collective analysis above, the key insights and recommendations are synthesized into a unified response."

        return synthesis

    async def _create_debate_synthesis(
        self, messages: List[SwarmMessage], context: Dict[str, Any]
    ) -> str:
        """Create synthesis from debate messages"""
        synthesis = f"Synthesis from {len(messages)} debate messages:\n\n"

        # Group by agent role
        by_role = {}
        for msg in messages:
            role = msg.sender_role.value
            if role not in by_role:
                by_role[role] = []
            by_role[role].append(msg.content[:200])

        for role, contents in by_role.items():
            synthesis += f"{role.upper()} PERSPECTIVE:\n"
            synthesis += f"- {contents[-1]}\n\n"  # Latest perspective

        synthesis += "DEBATE CONCLUSION:\n"
        synthesis += "After thorough debate and validation, the final recommendation synthesizes the strongest arguments and addresses identified concerns."

        return synthesis

    async def _create_consensus_synthesis(
        self, messages: List[SwarmMessage], context: Dict[str, Any]
    ) -> str:
        """Create synthesis from consensus messages"""
        synthesis = f"CONSENSUS REACHED among {len(messages)} agents:\n\n"

        # Include each agent's final position
        for msg in messages:
            synthesis += f"{msg.sender_role.value.upper()}: {msg.content[:300]}...\n\n"

        synthesis += "UNIFIED AGREEMENT:\n"
        synthesis += "All agents have reached consensus on the analysis and recommendations above."

        return synthesis

    def _organize_contributions(
        self, messages: List[SwarmMessage]
    ) -> Dict[AgentRole, List[SwarmMessage]]:
        """Organize messages by agent role"""
        contributions = {role: [] for role in AgentRole}

        for message in messages:
            if message.sender_role:
                contributions[message.sender_role].append(message)

        return contributions


# Default agent profiles for common use cases
SOPHIA_AGENTS = {
    "business_analyst": AgentProfile(
        role=AgentRole.ANALYST,
        name="Sophia Business Analyst",
        description="Expert in business intelligence, market analysis, and data interpretation",
        model_preferences=["gpt-4", "claude-3-opus"],
        specializations=[
            "market_research",
            "competitive_analysis",
            "financial_modeling",
            "customer_insights",
        ],
        reasoning_style="Data-driven analysis with focus on business metrics and KPIs",
        confidence_threshold=0.8,
        max_tokens=6000,
    ),
    "strategy_consultant": AgentProfile(
        role=AgentRole.STRATEGIST,
        name="Sophia Strategy Consultant",
        description="Strategic planning and business transformation specialist",
        model_preferences=["gpt-4", "claude-3-sonnet"],
        specializations=[
            "strategic_planning",
            "business_transformation",
            "growth_strategy",
            "operational_excellence",
        ],
        reasoning_style="Strategic thinking with focus on long-term value creation",
        confidence_threshold=0.85,
        max_tokens=6000,
    ),
    "business_validator": AgentProfile(
        role=AgentRole.VALIDATOR,
        name="Sophia Business Validator",
        description="Business proposal validation and risk assessment expert",
        model_preferences=["claude-3-opus", "gpt-4"],
        specializations=[
            "risk_assessment",
            "financial_validation",
            "compliance_check",
            "feasibility_analysis",
        ],
        reasoning_style="Critical evaluation with focus on practical implementation",
        confidence_threshold=0.9,
        max_tokens=4000,
    ),
}

ARTEMIS_AGENTS = {
    "code_analyst": AgentProfile(
        role=AgentRole.ANALYST,
        name="Artemis Code Analyst",
        description="Expert in code analysis, architecture review, and technical assessment",
        model_preferences=["deepseek-coder", "gpt-4"],
        specializations=[
            "code_analysis",
            "architecture_review",
            "performance_analysis",
            "security_scan",
        ],
        reasoning_style="Technical deep-dive with focus on code quality and best practices",
        confidence_threshold=0.85,
        max_tokens=8000,
    ),
    "tech_strategist": AgentProfile(
        role=AgentRole.STRATEGIST,
        name="Artemis Tech Strategist",
        description="Technical architecture and development strategy specialist",
        model_preferences=["gpt-4", "claude-3-sonnet"],
        specializations=[
            "technical_strategy",
            "system_design",
            "technology_roadmap",
            "team_coordination",
        ],
        reasoning_style="Technical strategy with focus on scalability and maintainability",
        confidence_threshold=0.8,
        max_tokens=6000,
    ),
    "code_validator": AgentProfile(
        role=AgentRole.VALIDATOR,
        name="Artemis Code Validator",
        description="Code quality assurance and technical validation expert",
        model_preferences=["deepseek-coder", "claude-3-opus"],
        specializations=[
            "code_review",
            "testing_strategy",
            "quality_assurance",
            "security_validation",
        ],
        reasoning_style="Rigorous technical validation with focus on reliability and security",
        confidence_threshold=0.9,
        max_tokens=6000,
    ),
}
