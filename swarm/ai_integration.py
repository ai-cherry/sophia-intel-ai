"""
AI Router Integration for Swarm System
Provides integration between Sophia's AI Router and the Swarm system.
"""

import os
import asyncio
import time
from typing import Dict, Any, List, Optional
from loguru import logger
import json

# LangChain imports
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# Conditionally import the AI Router
try:
    from mcp_servers.ai_router import AIRouter, TaskRequest, TaskType
    HAS_AI_ROUTER = True
except ImportError:
    HAS_AI_ROUTER = False
    logger.warning("AI Router not available, will use fallback LLM selection")


class RouterLLM:
    """
    LLM implementation that uses the AI Router for model selection and execution.
    Compatible with the LangChain interface used in the Swarm system.
    """

    def __init__(self):
        """Initialize the RouterLLM"""
        self._router = None
        self._initialize_router()
        self._cache = {}

    def _initialize_router(self):
        """Initialize the AI Router instance"""
        if not HAS_AI_ROUTER:
            return

        try:
            self._router = AIRouter()
            logger.info("AI Router initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI Router: {e}")
            self._router = None

    @property
    def is_available(self) -> bool:
        """Check if the AI Router is available"""
        return self._router is not None

    def _get_task_type(self, agent_role: str = None) -> TaskType:
        """
        Determine appropriate task type based on agent role
        """
        if agent_role == "architect":
            return TaskType.ANALYSIS
        elif agent_role == "builder":
            return TaskType.CODE_GENERATION
        elif agent_role == "tester":
            return TaskType.CODE_REVIEW
        elif agent_role == "operator":
            return TaskType.DOCUMENTATION

        # If no specific match, determine based on env var or default
        task_type_str = os.getenv("SWARM_TASK_TYPE", "code_generation")
        try:
            return TaskType(task_type_str)
        except (ValueError, TypeError):
            return TaskType.CODE_GENERATION

    def _format_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Format LangChain messages into a prompt string for the router"""
        prompt = ""

        for msg in messages:
            # Handle dict messages
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role == "system":
                    prompt += f"System: {content}\n\n"
                elif role == "user":
                    prompt += f"User: {content}\n\n"
                elif role == "assistant":
                    prompt += f"Assistant: {content}\n\n"
            # Handle LangChain message objects
            else:
                if isinstance(msg, SystemMessage):
                    prompt += f"System: {msg.content}\n\n"
                elif isinstance(msg, HumanMessage):
                    prompt += f"User: {msg.content}\n\n"
                elif isinstance(msg, AIMessage):
                    prompt += f"Assistant: {msg.content}\n\n"

        return prompt.strip()

    async def _async_invoke(self, messages):
        """Async implementation of invoke using the AI Router"""
        agent_role = os.getenv("SWARM_CURRENT_AGENT", "")
        task_type = self._get_task_type(agent_role)

        # Create prompt from messages
        prompt = self._format_messages(messages)

        # Cache key to avoid duplicate requests
        cache_key = f"{hash(prompt)}_{task_type}"
        if cache_key in self._cache:
            logger.info(f"Using cached response for {agent_role}")
            return self._cache[cache_key]

        # Configure model selection parameters based on agent role
        quality_req = "premium" if agent_role in [
            "architect", "builder"] else "high"

        # Create task request
        request = TaskRequest(
            prompt=prompt,
            task_type=task_type,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            quality_requirement=os.getenv("LLM_QUALITY", quality_req),
            latency_requirement=os.getenv("LLM_LATENCY", "normal"),
            cost_preference=os.getenv("LLM_COST", "balanced"),
            metadata={
                "source": "swarm",
                "agent": agent_role,
                "swarm_stage": agent_role
            }
        )

        try:
            # Get routing decision
            decision = await self._router.route_request(request)
            logger.info(
                f"Selected model: {decision.selected_model} from {decision.selected_provider}")

            # Execute task with selected model
            response = await self._router.execute_task(request, decision)

            # Create AIMessage response
            result = AIMessage(content=response.content)

            # Cache the result
            self._cache[cache_key] = result

            # Log success
            self._log_router_usage(decision, agent_role,
                                   len(prompt), len(response.content))

            return result

        except Exception as e:
            logger.error(f"AI Router execution failed: {e}")
            raise

    def _log_router_usage(self, decision, agent_role, prompt_len, response_len):
        """Log router usage for telemetry"""
        try:
            log_data = {
                "timestamp": time.time(),
                "agent": agent_role,
                "model": decision.selected_model,
                "provider": decision.selected_provider,
                "confidence": decision.confidence_score,
                "estimated_cost": decision.estimated_cost,
                "prompt_length": prompt_len,
                "response_length": response_len,
                "event_type": "model_selection"
            }

            # Write to handoffs log
            log_file = os.getenv("SWARM_LOG_FILE", ".swarm_handoffs.log")
            with open(log_file, "a") as f:
                f.write(json.dumps(log_data) + "\n")

        except Exception as e:
            logger.error(f"Failed to log router usage: {e}")

    def invoke(self, messages):
        """
        Synchronous interface for invoking the AI Router
        Compatible with LangChain interface
        """
        if not self.is_available:
            raise ValueError("AI Router is not available")

        # Run the async method in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context
                # This is tricky - ideally we'd use asyncio.create_task
                # but for now we'll use a synchronous approach
                future = asyncio.run_coroutine_threadsafe(
                    self._async_invoke(messages), loop
                )
                return future.result(timeout=float(os.getenv("LLM_TIMEOUT", "60")))
            else:
                # No event loop running, create one
                return loop.run_until_complete(self._async_invoke(messages))

        except Exception as e:
            logger.error(f"Failed to invoke AI Router: {e}")
            raise


def get_router_llm():
    """Factory function to get a RouterLLM instance"""
    llm = RouterLLM()
    if llm.is_available:
        return llm
    return None
