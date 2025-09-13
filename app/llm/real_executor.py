"""
Real LLM Executor with Portkey Integration
Replaces all mock/template responses with actual LLM calls.
"""
import logging
import time
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, Optional
from app.api.advanced_gateway_2025 import (
    AdvancedAIGateway2025,
    TaskType,
)  # Corrected import
from app.elite_portkey_config import EliteAgentConfig  # For model configs
from app.llm.response_models import LLMResponse, ResponseStatus, TokenStats
# Unified embedding coordinator (preferred path)
try:
    from app.memory.embedding_coordinator import get_embedding_coordinator
except Exception:
    get_embedding_coordinator = None
# Define Role enum locally if not already defined globally or imported
# This ensures Role is available after removing app.portkey_config
from enum import Enum
from app.core.circuit_breaker import with_circuit_breaker
class Role(Enum):
    PLANNER = "planner"
    GENERATOR = "generator"
    CRITIC = "critic"
    JUDGE = "judge"
    LEAD = "lead"
    RUNNER = "runner"
    ARCHITECT = "architect"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    DEBUGGER = "debugger"
    REFACTORER = "refactorer"
    SPAWNER = "spawner"
    EVOLUTIONIST = "evolutionist"
    CONSCIOUSNESS = "consciousness"
    FAST_CODER = "fast_coder"
    HEAVY_CODER = "heavy_coder"
    BALANCED_CODER = "balanced_coder"
logger = logging.getLogger(__name__)
class RealLLMExecutor:
    """Execute real LLM calls through Portkey gateway."""
    def __init__(self):
        self.gateway: AdvancedAIGateway2025 = (
            AdvancedAIGateway2025()
        )  # Use the new gateway
        self.session_id = None
    async def execute(
        self,
        prompt: str,
        model_pool: str = "balanced",
        stream: bool = False,
        role: Optional[Role] = None,
        context: Optional[dict[str, Any]] = None,
        task_type: Optional[TaskType] = None,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> LLMResponse:
        """
        Execute real LLM call with fallback chain and proper model selection.
        Args:
            prompt: The prompt to send to the LLM
            model_pool: Model pool (fast, balanced, heavy)
            stream: Whether to stream the response
            role: Agent role for temperature/model selection
            context: Additional context for the request
            task_type: Type of task for model selection
            trace_id: Trace ID for request correlation
            session_id: Session ID for context
        Returns:
            LLMResponse with real LLM response and metadata
        """
        # Determine task type from role if not provided
        if not task_type:
            task_type = self._get_task_type_from_role(role)
        # Build messages
        messages = self._build_messages(prompt, context)
        # Get temperature for role
        temperature = self._get_temperature_for_role(role)
        # Define fallback chain based on model pool
        fallback_models = self._get_fallback_chain(model_pool, role)
        attempts = []
        last_error = None
        # Try each model in the fallback chain
        for model in fallback_models:
            try:
                logger.info(
                    f"Attempting LLM call: model={model}, pool={model_pool}, role={role}"
                )
                if stream:
                    # For now, streaming returns dict - update streaming to return LLMResponse
                    result = await self._execute_streaming(
                        messages, model, temperature, role
                    )
                    return LLMResponse(
                        content=result.get("content", ""),
                        success=result.get("success", False),
                        status=(
                            ResponseStatus.SUCCESS
                            if result.get("success")
                            else ResponseStatus.ERROR
                        ),
                        model=model,
                        trace_id=trace_id,
                        session_id=session_id,
                    )
                else:
                    response = await self._execute_non_streaming(
                        messages, model, temperature, role, task_type
                    )
                    if response.success:
                        response.trace_id = trace_id
                        response.session_id = session_id
                        response.attempts = attempts
                        response.final_model = model
                        return response
                    else:
                        attempts.append(
                            {
                                "model": model,
                                "error": response.error,
                                "timestamp": response.timestamp.isoformat(),
                            }
                        )
                        last_error = response.error
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                attempts.append(
                    {
                        "model": model,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                last_error = str(e)
                continue
        # All models failed - check cache as last resort
        cached_response = await self._check_cache(prompt, model_pool)
        if cached_response:
            cached_response.status = ResponseStatus.CACHED
            cached_response.attempts = attempts
            return cached_response
        # Return error response
        return LLMResponse(
            content="",
            success=False,
            status=ResponseStatus.ERROR,
            error=last_error or "All models in fallback chain failed",
            error_code="FALLBACK_CHAIN_EXHAUSTED",
            attempts=attempts,
            trace_id=trace_id,
            session_id=session_id,
        )
    @with_circuit_breaker("external_api")
    async def _execute_streaming(
        self,
        messages: list[dict[str, str]],
        model_name: str,  # Changed from 'model' to 'model_name'
        temperature: float,
        role: Optional[Role],
    ) -> AsyncGenerator[dict[str, Any], None]:  # Changed return type to AsyncGenerator
        """Execute streaming LLM call using Portkey gateway."""
        try:
            stream_response = await self.gateway.chat_completion(
                messages=messages,
                task_type=TaskType.GENERAL,  # Default to GENERAL, can be refined
                stream=True,
                model_name=model_name,
                temperature=temperature,
            )
            # Iterate through the streaming response directly from Portkey's result
            full_content = ""
            async for chunk in stream_response:
                # Assuming Portkey's streamed chunks have a 'choices' attribute
                if (
                    chunk.choices
                    and chunk.choices[0].delta
                    and chunk.choices[0].delta.content
                ):
                    content_chunk = chunk.choices[0].delta.content
                    full_content += content_chunk
                    yield {
                        "type": "content_chunk",
                        "content": content_chunk,
                        "timestamp": datetime.now().isoformat(),
                    }
            # Final result with token counts (if available from final chunk or inferred)
            # Note: Streaming responses often provide token counts in the final chunk or via metadata
            yield {
                "type": "complete",
                "content": full_content,
                "success": True,
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
                "token_count": len(
                    full_content.split()
                ),  # Simplified count, ideally from API response
                "role": role.value if role else None,
            }
        except Exception as e:
            logger.error(f"Streaming execution failed: {e}")
            yield {
                "type": "error",
                "content": f"Streaming error: {str(e)}",
                "success": False,
                "error": str(e),
            }
    @with_circuit_breaker("external_api")
    async def _execute_non_streaming(
        self,
        messages: list[dict[str, str]],
        model_name: str,  # Changed from 'model' to 'model_name'
        temperature: float,
        role: Optional[Role],
        task_type: TaskType = TaskType.GENERAL,
    ) -> LLMResponse:
        """Execute non-streaming LLM call and return standardized response."""
        start_time = time.time()
        try:
            # Use gateway.chat_completion with the new args
            response = await self.gateway.chat_completion(
                messages=messages,
                task_type=task_type,
                stream=False,
                model_name=model_name,
                temperature=temperature,
            )
            content = (
                response.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            # Extract token stats if available
            metrics = response.get("metrics", {})
            token_stats = TokenStats(
                prompt_tokens=metrics.get("prompt_tokens", 0),
                completion_tokens=metrics.get("completion_tokens", 0),
                total_tokens=metrics.get("total_tokens", 0),
            )
            latency_ms = (time.time() - start_time) * 1000
            return LLMResponse(
                content=content,
                success=True,
                status=ResponseStatus.SUCCESS,
                model=response.get("model_name", model_name),
                provider="portkey",
                task_type=task_type.value if task_type else None,
                latency_ms=latency_ms,
                token_stats=token_stats,
                estimated_cost=token_stats.cost_estimate,
                metadata={
                    "role": role.value if role else None,
                    "temperature": temperature,
                },
            )
        except Exception as e:
            logger.error(f"Non-streaming execution failed: {e}")
            return LLMResponse.from_error(
                error=str(e), error_code="LLM_EXECUTION_ERROR"
            )
    def _select_model(self, pool: str, role: Optional[Role]) -> str:
        """Select appropriate model based on pool and role from EliteAgentConfig."""
        role_key = role.value if role else "generator"
        # Prioritize role-specific model
        if role_key in EliteAgentConfig.MODELS:
            return EliteAgentConfig.MODELS[role_key]
        # Fallback to pool-based selection if role has no direct mapping
        # This logic needs to be refined if 'pool' maps to different models than roles
        # For now, it will default to generator if a specific role model isn't found
        default_model = EliteAgentConfig.MODELS["generator"]
        return default_model
    def _build_messages(
        self, prompt: str, context: Optional[dict[str, Any]] = None
    ) -> list[dict[str, str]]:
        """Build messages array for the LLM."""
        messages = []
        # Add system message based on context
        if context and context.get("system_prompt"):
            messages.append({"role": "system", "content": context["system_prompt"]})
        # Add context as conversation history if provided
        if context and context.get("conversation_history"):
            for msg in context["conversation_history"]:
                messages.append(msg)
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        return messages
    def _get_temperature_for_role(self, role: Optional[Role]) -> float:
        """Get appropriate temperature for role from EliteAgentConfig."""
        role_key = role.value if role else "generator"
        return EliteAgentConfig.TEMPERATURES.get(role_key, 0.7)
    def _get_task_type_from_role(self, role: Optional[Role]) -> TaskType:
        """Determine task type from role."""
        if not role:
            return TaskType.GENERAL
        role_task_mapping = {
            Role.PLANNER: TaskType.PLANNING,
            Role.GENERATOR: TaskType.CODE_GENERATION,
            Role.CRITIC: TaskType.CODE_REVIEW,
            Role.DEBUGGER: TaskType.DEBUGGING,
            Role.REFACTORER: TaskType.REFACTORING,
            Role.TESTING: TaskType.TESTING,
            Role.SECURITY: TaskType.SECURITY_ANALYSIS,
            Role.PERFORMANCE: TaskType.OPTIMIZATION,
            Role.ARCHITECT: TaskType.ARCHITECTURE,
        }
        return role_task_mapping.get(role, TaskType.GENERAL)
    def _get_fallback_chain(self, model_pool: str, role: Optional[Role]) -> list[str]:
        """Get fallback model chain based on pool and role."""
        # Define fallback chains for different pools
        fallback_chains = {
            "fast": [
                "google/gemini-2.5-flash",
                "z-ai/glm-4.5-air",
                "deepseek/deepseek-chat-v3-0324",
            ],
            "balanced": [
                "google/gemini-2.5-pro",
                "qwen/qwen3-30b-a3b",
                "anthropic/claude-sonnet-4",
            ],
            "heavy": ["openai/gpt-5", "x-ai/grok-4", "anthropic/claude-sonnet-4"],
        }
        # Get primary model for the role
        primary_model = self._select_model(model_pool, role)
        # Get fallback chain for the pool
        chain = fallback_chains.get(model_pool, fallback_chains["balanced"])
        # Put primary model first if not already in chain
        if primary_model not in chain:
            chain = [primary_model] + chain
        else:
            # Move primary model to front
            chain.remove(primary_model)
            chain = [primary_model] + chain
        return chain[:3]  # Limit to 3 attempts
    async def _check_cache(self, prompt: str, model_pool: str) -> Optional[LLMResponse]:
        """Check cache for previous response to similar prompt."""
        # Implement semantic cache lookup
        # For now, return None (no cache hit)
        return None
    async def generate_code_streaming(
        self,
        task: str,
        role: Role = Role.GENERATOR,
        pool: str = "balanced",
        context: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Generate code with streaming response.
        Args:
            task: The coding task
            role: Agent role
            pool: Model pool to use
            context: Additional context
        Yields:
            Streaming response chunks
        """
        # Build appropriate prompt for coding
        coding_prompt = self._build_coding_prompt(task, role, context)
        try:
            async for chunk in self._execute_streaming(
                messages=self._build_messages(coding_prompt, context),
                model=self._select_model(pool, role),
                temperature=self._get_temperature_for_role(role),
                role=role,
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Code generation streaming failed: {e}")
            yield {
                "type": "error",
                "content": f"Code generation error: {str(e)}",
                "success": False,
                "error": str(e),
            }
    def _build_coding_prompt(
        self, task: str, role: Role, context: Optional[dict[str, Any]]
    ) -> str:
        """Build role-specific coding prompt."""
        base_prompts = {
            Role.PLANNER: f"""You are a technical planner. Analyze this coding task and create a structured plan:
Task: {task}
Provide a detailed plan with:
1. Requirements analysis
2. Architecture decisions
3. Implementation milestones
4. Risk assessment
5. Testing strategy
Return your response as structured text with clear sections.""",
            Role.GENERATOR: f"""You are a code generator. Create production-ready code for this task:
Task: {task}
Requirements:
- Write clean, maintainable code
- Include proper error handling
- Add docstrings and comments
- Follow best practices
- Include usage examples
Provide the complete implementation with explanations.""",
            Role.CRITIC: f"""You are a code reviewer. Analyze this task and provide a structured review:
Task: {task}
Review across these dimensions:
- Security vulnerabilities
- Performance implications
- Code quality and maintainability
- Error handling
- Test coverage needs
- Documentation quality
Provide specific, actionable feedback.""",
            Role.JUDGE: f"""You are a technical judge. Evaluate proposals for this task:
Task: {task}
Make a decision on:
- Which approach is best
- What changes are needed
- Implementation priority
- Risk level assessment
Provide clear reasoning and next steps.""",
            Role.RUNNER: f"""You are a code runner. Execute the approved solution for:
Task: {task}
Focus on:
- Implementing the exact specifications
- Running tests
- Verifying functionality
- Reporting results
Provide execution details and any issues found.""",
        }
        prompt = base_prompts.get(role, base_prompts[Role.GENERATOR])
        # Add context if provided
        if context:
            if context.get("memory_results"):
                prompt += (
                    f"\n\nRelevant context from memory:\n{context['memory_results']}"
                )
            if context.get("code_search_results"):
                prompt += f"\n\nRelevant code from repository:\n{context['code_search_results']}"
            if context.get("conversation_history"):
                prompt += f"\n\nPrevious discussion:\n{context['conversation_history'][-3:]}"  # Last 3 messages
        return prompt
    @with_circuit_breaker("external_api")
    async def embed_text(
        self, texts: list[str], strategy: str = "auto"
    ) -> list[list[float]]:
        """Generate embeddings for text using unified coordinator with graceful fallback."""
        # Prefer the local unified coordinator (embed_router + cache) when available
        try:
            if get_embedding_coordinator:
                # Run sync coordinator in a thread to avoid blocking event loop
                import asyncio
                coordinator = get_embedding_coordinator()
                result = await asyncio.to_thread(
                    coordinator.generate_embeddings, texts, strategy
                )
                embeddings = result.get("embeddings", [])
                if embeddings:
                    logger.info(
                        f"Generated embeddings via coordinator ({result.get('strategy_used')}) for {len(texts)} texts"
                    )
                    return embeddings
        except Exception as e:
            logger.warning(
                f"Coordinator embedding failed, falling back to gateway: {e}"
            )
        # Fallback to gateway (Portkey) if coordinator not available or failed
        try:
            embeddings_response = await self.gateway.generate_embeddings(texts)
            # Expecting {'data': [{'embedding': [...]}, ...]}
            embeddings = [
                item["embedding"]
                for item in embeddings_response.get("data", [])
                if "embedding" in item
            ]
            if embeddings:
                logger.info(f"Generated embeddings via gateway for {len(texts)} texts")
                return embeddings
            raise ValueError("Gateway returned no embeddings")
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}", exc_info=True)
            # Return zero vectors as last resort (dimension heuristic)
            fallback_dim = 1024
            return [[0.0] * fallback_dim for _ in texts]
# Global instance
real_executor = RealLLMExecutor()
# Backward compatibility functions
async def execute_with_real_llm(
    problem: dict, agents: list[str], pool: str = "balanced"
) -> dict:
    """Execute problem with real LLM calls (backward compatible)."""
    try:
        # Convert old format to new
        task = problem.get("query") or problem.get("description") or str(problem)
        # Use first agent role or default to generator
        role_map = {
            "code_generator": Role.GENERATOR,
            "planner": Role.PLANNER,
            "critic": Role.CRITIC,
            "judge": Role.JUDGE,
            "runner": Role.RUNNER,
        }
        agent_role = role_map.get(agents[0] if agents else "generator", Role.GENERATOR)
        # Execute with real LLM
        result = await real_executor.execute(
            prompt=task,
            model_pool=pool,
            role=agent_role,
            context=problem.get("context"),
        )
        return {
            "solution": result["content"],
            "confidence": 0.85 if result["success"] else 0.3,
            "agent": agents[0] if agents else "generator",
            "timestamp": result["timestamp"],
            "model": result.get("model"),
            "success": result["success"],
        }
    except Exception as e:
        logger.error(f"Legacy LLM execution failed: {e}")
        return {
            "solution": f"# Error executing with real LLM: {str(e)}",
            "confidence": 0.1,
            "error": str(e),
            "success": False,
        }
