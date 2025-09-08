"""
Modular Reasoning Engine

This module provides a dedicated reasoning engine that separates reasoning logic
from agent implementation, simplifying extension and testing.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.tools.tool_schemas import ToolCall, ToolResponse

logger = logging.getLogger(__name__)


class ReasoningStepType(str, Enum):
    """Types of reasoning steps"""

    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    PLANNING = "planning"
    EVALUATION = "evaluation"
    CONCLUSION = "conclusion"


class ReasoningStep(BaseModel):
    """Individual step in reasoning process"""

    step_type: ReasoningStepType
    content: str
    tool_call: Optional[ToolCall] = None
    tool_response: Optional[ToolResponse] = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class ReasoningContext(BaseModel):
    """Context for reasoning process"""

    problem: str
    goal: Optional[str] = None
    constraints: list[str] = Field(default_factory=list)
    available_tools: list[str] = Field(default_factory=list)
    memory_context: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_context: list[dict[str, Any]] = Field(default_factory=list)
    previous_steps: list[ReasoningStep] = Field(default_factory=list)
    max_steps: int = Field(10, ge=1, le=100)
    current_step: int = Field(0, ge=0)


class ReasoningStrategy(ABC):
    """Abstract base class for reasoning strategies"""

    @abstractmethod
    async def next_step(self, context: ReasoningContext) -> Optional[ReasoningStep]:
        """Generate the next reasoning step"""
        pass

    @abstractmethod
    async def should_continue(self, context: ReasoningContext) -> bool:
        """Determine if reasoning should continue"""
        pass

    @abstractmethod
    async def extract_conclusion(self, context: ReasoningContext) -> str:
        """Extract final conclusion from reasoning process"""
        pass


class ReActStrategy(ReasoningStrategy):
    """ReAct (Reasoning and Acting) strategy implementation"""

    def __init__(self, model_client: Any, tool_executor: Any):
        self.model_client = model_client
        self.tool_executor = tool_executor

    async def next_step(self, context: ReasoningContext) -> Optional[ReasoningStep]:
        """Generate next ReAct step"""
        # Determine step type based on previous steps
        last_step = context.previous_steps[-1] if context.previous_steps else None

        if last_step is None or last_step.step_type == ReasoningStepType.OBSERVATION:
            # Generate a thought
            return await self._generate_thought(context)
        elif last_step.step_type == ReasoningStepType.THOUGHT:
            # Decide on action or conclusion
            if await self._should_act(context):
                return await self._generate_action(context)
            else:
                return await self._generate_conclusion(context)
        elif last_step.step_type == ReasoningStepType.ACTION:
            # Execute action and observe
            return await self._generate_observation(context)

        return None

    async def should_continue(self, context: ReasoningContext) -> bool:
        """Check if reasoning should continue"""
        if context.current_step >= context.max_steps:
            return False

        if context.previous_steps:
            last_step = context.previous_steps[-1]
            if last_step.step_type == ReasoningStepType.CONCLUSION:
                return False

        return True

    async def extract_conclusion(self, context: ReasoningContext) -> str:
        """Extract conclusion from reasoning trace"""
        for step in reversed(context.previous_steps):
            if step.step_type == ReasoningStepType.CONCLUSION:
                return step.content

        # Generate conclusion if not found
        conclusion_step = await self._generate_conclusion(context)
        return conclusion_step.content if conclusion_step else "No conclusion reached"

    async def _generate_thought(self, context: ReasoningContext) -> ReasoningStep:
        """Generate a thought step"""
        prompt = self._build_thought_prompt(context)
        response = await self.model_client.generate(prompt)

        return ReasoningStep(
            step_type=ReasoningStepType.THOUGHT, content=response, confidence=0.8
        )

    async def _generate_action(self, context: ReasoningContext) -> ReasoningStep:
        """Generate an action step"""
        prompt = self._build_action_prompt(context)
        response = await self.model_client.generate(prompt)

        # Parse tool call from response
        tool_call = self._parse_tool_call(response)

        return ReasoningStep(
            step_type=ReasoningStepType.ACTION,
            content=f"Executing tool: {tool_call.tool_name}",
            tool_call=tool_call,
            confidence=0.7,
        )

    async def _generate_observation(self, context: ReasoningContext) -> ReasoningStep:
        """Execute action and generate observation"""
        last_action = None
        for step in reversed(context.previous_steps):
            if step.step_type == ReasoningStepType.ACTION and step.tool_call:
                last_action = step
                break

        if not last_action or not last_action.tool_call:
            return ReasoningStep(
                step_type=ReasoningStepType.OBSERVATION,
                content="No action to observe",
                confidence=0.5,
            )

        # Execute tool
        tool_response = await self.tool_executor.execute(last_action.tool_call)

        return ReasoningStep(
            step_type=ReasoningStepType.OBSERVATION,
            content=f"Tool result: {tool_response.result}",
            tool_response=tool_response,
            confidence=0.9,
        )

    async def _generate_conclusion(self, context: ReasoningContext) -> ReasoningStep:
        """Generate a conclusion step"""
        prompt = self._build_conclusion_prompt(context)
        response = await self.model_client.generate(prompt)

        return ReasoningStep(
            step_type=ReasoningStepType.CONCLUSION, content=response, confidence=0.85
        )

    async def _should_act(self, context: ReasoningContext) -> bool:
        """Determine if an action is needed"""
        # Simple heuristic: act if tools are available and not used recently
        if not context.available_tools:
            return False

        recent_actions = sum(
            1
            for step in context.previous_steps[-3:]
            if step.step_type == ReasoningStepType.ACTION
        )

        return recent_actions < 1

    def _build_thought_prompt(self, context: ReasoningContext) -> str:
        """Build prompt for thought generation"""
        return f"""
Problem: {context.problem}
Goal: {context.goal or 'Solve the problem'}

Previous reasoning:
{self._format_previous_steps(context)}

What should we consider next? Think step by step.
"""

    def _build_action_prompt(self, context: ReasoningContext) -> str:
        """Build prompt for action generation"""
        return f"""
Based on our reasoning, what tool should we use?

Available tools: {', '.join(context.available_tools)}

Recent thoughts:
{self._format_recent_thoughts(context)}

Specify the tool and parameters in this format:
Tool: [tool_name]
Parameters: [parameters as JSON]
"""

    def _build_conclusion_prompt(self, context: ReasoningContext) -> str:
        """Build prompt for conclusion generation"""
        return f"""
Based on our complete reasoning process, provide the final answer.

Problem: {context.problem}

Reasoning trace:
{self._format_previous_steps(context)}

Final Answer:
"""

    def _format_previous_steps(self, context: ReasoningContext) -> str:
        """Format previous steps for prompt"""
        formatted = []
        for step in context.previous_steps[-10:]:  # Last 10 steps
            formatted.append(f"{step.step_type}: {step.content[:200]}")
        return "\n".join(formatted)

    def _format_recent_thoughts(self, context: ReasoningContext) -> str:
        """Format recent thoughts for prompt"""
        thoughts = [
            step.content
            for step in context.previous_steps[-5:]
            if step.step_type == ReasoningStepType.THOUGHT
        ]
        return "\n".join(thoughts)

    def _parse_tool_call(self, response: str) -> ToolCall:
        """Parse tool call from model response"""
        # Simple parsing logic - would be more sophisticated in practice
        import json
        import re

        tool_match = re.search(r"Tool:\s*(\w+)", response)
        params_match = re.search(r"Parameters:\s*({.*})", response, re.DOTALL)

        tool_name = tool_match.group(1) if tool_match else "unknown"
        params = {}

        if params_match:
            try:
                params = json.loads(params_match.group(1))
            except json.JSONDecodeError:
                logger.warning("Failed to parse tool parameters")

        return ToolCall(tool_name=tool_name, parameters=params)


class ChainOfThoughtStrategy(ReasoningStrategy):
    """Chain of Thought reasoning strategy"""

    def __init__(self, model_client: Any):
        self.model_client = model_client

    async def next_step(self, context: ReasoningContext) -> Optional[ReasoningStep]:
        """Generate next chain-of-thought step"""
        if context.current_step == 0:
            return await self._generate_planning(context)
        elif context.current_step < context.max_steps - 1:
            return await self._generate_reasoning(context)
        else:
            return await self._generate_conclusion(context)

    async def should_continue(self, context: ReasoningContext) -> bool:
        """Check if reasoning should continue"""
        return context.current_step < context.max_steps and not self._has_conclusion(
            context
        )

    async def extract_conclusion(self, context: ReasoningContext) -> str:
        """Extract conclusion from reasoning"""
        for step in reversed(context.previous_steps):
            if step.step_type == ReasoningStepType.CONCLUSION:
                return step.content
        return "No conclusion reached"

    async def _generate_planning(self, context: ReasoningContext) -> ReasoningStep:
        """Generate initial planning step"""
        prompt = f"""
Problem: {context.problem}
Goal: {context.goal or 'Solve the problem'}

Let's break this down into steps. What's our approach?
"""
        response = await self.model_client.generate(prompt)

        return ReasoningStep(
            step_type=ReasoningStepType.PLANNING, content=response, confidence=0.75
        )

    async def _generate_reasoning(self, context: ReasoningContext) -> ReasoningStep:
        """Generate reasoning step"""
        prompt = f"""
Continuing our analysis...

Previous reasoning:
{self._format_previous_steps(context)}

What's the next logical step in our thinking?
"""
        response = await self.model_client.generate(prompt)

        return ReasoningStep(
            step_type=ReasoningStepType.THOUGHT, content=response, confidence=0.8
        )

    async def _generate_conclusion(self, context: ReasoningContext) -> ReasoningStep:
        """Generate conclusion"""
        prompt = f"""
Based on our analysis:
{self._format_previous_steps(context)}

What's our final conclusion?
"""
        response = await self.model_client.generate(prompt)

        return ReasoningStep(
            step_type=ReasoningStepType.CONCLUSION, content=response, confidence=0.85
        )

    def _format_previous_steps(self, context: ReasoningContext) -> str:
        """Format previous steps"""
        return "\n".join(
            [
                f"Step {i+1}: {step.content[:150]}"
                for i, step in enumerate(context.previous_steps[-5:])
            ]
        )

    def _has_conclusion(self, context: ReasoningContext) -> bool:
        """Check if conclusion exists"""
        return any(
            step.step_type == ReasoningStepType.CONCLUSION
            for step in context.previous_steps
        )


class ReasoningEngine:
    """Main reasoning engine that orchestrates strategies"""

    def __init__(
        self,
        strategy: ReasoningStrategy,
        enable_logging: bool = True,
        enable_metrics: bool = True,
    ):
        self.strategy = strategy
        self.enable_logging = enable_logging
        self.enable_metrics = enable_metrics
        self._reasoning_history: list[ReasoningContext] = []

    async def reason(
        self,
        problem: str,
        goal: Optional[str] = None,
        constraints: Optional[list[str]] = None,
        available_tools: Optional[list[str]] = None,
        max_steps: int = 10,
    ) -> tuple[str, list[ReasoningStep]]:
        """Execute reasoning process"""
        context = ReasoningContext(
            problem=problem,
            goal=goal,
            constraints=constraints or [],
            available_tools=available_tools or [],
            max_steps=max_steps,
        )

        if self.enable_logging:
            logger.info(f"Starting reasoning for: {problem[:100]}...")

        while await self.strategy.should_continue(context):
            try:
                step = await self.strategy.next_step(context)
                if step:
                    context.previous_steps.append(step)
                    context.current_step += 1

                    if self.enable_logging:
                        logger.debug(
                            f"Reasoning step {context.current_step}: {step.step_type}"
                        )
                else:
                    break

            except Exception as e:
                logger.error(f"Error in reasoning step: {e}")
                break

        conclusion = await self.strategy.extract_conclusion(context)

        self._reasoning_history.append(context)

        if self.enable_metrics:
            self._record_metrics(context)

        return conclusion, context.previous_steps

    def _record_metrics(self, context: ReasoningContext):
        """Record reasoning metrics"""
        # This would integrate with Prometheus/OpenTelemetry
        metrics = {
            "total_steps": len(context.previous_steps),
            "thought_steps": sum(
                1
                for s in context.previous_steps
                if s.step_type == ReasoningStepType.THOUGHT
            ),
            "action_steps": sum(
                1
                for s in context.previous_steps
                if s.step_type == ReasoningStepType.ACTION
            ),
            "average_confidence": (
                sum(s.confidence for s in context.previous_steps)
                / len(context.previous_steps)
                if context.previous_steps
                else 0
            ),
        }

        logger.info(f"Reasoning metrics: {metrics}")

    def get_history(self) -> list[ReasoningContext]:
        """Get reasoning history"""
        return self._reasoning_history

    def clear_history(self):
        """Clear reasoning history"""
        self._reasoning_history = []
