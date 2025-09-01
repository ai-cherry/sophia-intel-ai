"""
Real LLM Executor with Portkey Integration
Replaces all mock/template responses with actual LLM calls.
"""

import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime

from app.api.advanced_gateway_2025 import AdvancedAIGateway2025, TaskType # Corrected import
from app.elite_portkey_config import EliteAgentConfig # For model configs
from app.swarms.coding.models import PoolType # Assuming this is still needed
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
        self.gateway: AdvancedAIGateway2025 = AdvancedAIGateway2025() # Use the new gateway
        self.session_id = None
        
    async def execute(
        self,
        prompt: str,
        model_pool: str = "balanced",
        stream: bool = False,
        role: Optional[Role] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute real LLM call with proper model selection.
        
        Args:
            prompt: The prompt to send to the LLM
            model_pool: Model pool (fast, balanced, heavy)
            stream: Whether to stream the response
            role: Agent role for temperature/model selection
            context: Additional context for the request
            
        Returns:
            Dictionary with real LLM response and metadata
        """
        try:
            # Select model based on pool
            model = self._select_model(model_pool, role)
            
            # Build messages
            messages = self._build_messages(prompt, context)
            
            # Get temperature for role
            temperature = self._get_temperature_for_role(role)
            
            logger.info(f"Executing LLM call: model={model}, pool={model_pool}, role={role}")
            
            if stream:
                return await self._execute_streaming(messages, model, temperature, role)
            else:
                return await self._execute_non_streaming(messages, model, temperature, role)
                
        except Exception as e:
            logger.error(f"LLM execution failed: {e}", exc_info=True)
            return {
                "content": f"Error: {str(e)}",
                "success": False,
                "error": str(e),
                "model": model_pool,
                "timestamp": datetime.now().isoformat()
            }
    
    @with_circuit_breaker("external_api")
    async def _execute_streaming(
        self,
        messages: List[Dict[str, str]],
        model_name: str, # Changed from 'model' to 'model_name'
        temperature: float,
        role: Optional[Role]
    ) -> AsyncGenerator[Dict[str, Any], None]: # Changed return type to AsyncGenerator
        """Execute streaming LLM call using Portkey gateway."""
        try:
            stream_response = await self.gateway.chat_completion(
                messages=messages,
                task_type=TaskType.GENERAL, # Default to GENERAL, can be refined
                stream=True,
                model_name=model_name,
                temperature=temperature,
            )
            
            # Iterate through the streaming response directly from Portkey's result
            full_content = ""
            async for chunk in stream_response:
                # Assuming Portkey's streamed chunks have a 'choices' attribute
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_content += content_chunk
                    yield {
                        "type": "content_chunk",
                        "content": content_chunk,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Final result with token counts (if available from final chunk or inferred)
            # Note: Streaming responses often provide token counts in the final chunk or via metadata
            yield {
                "type": "complete",
                "content": full_content,
                "success": True,
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
                "token_count": len(full_content.split()), # Simplified count, ideally from API response
                "role": role.value if role else None
            }
            
        except Exception as e:
            logger.error(f"Streaming execution failed: {e}")
            yield {
                "type": "error",
                "content": f"Streaming error: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    @with_circuit_breaker("external_api")
    async def _execute_non_streaming(
        self,
        messages: List[Dict[str, str]],
        model_name: str, # Changed from 'model' to 'model_name'
        temperature: float,
        role: Optional[Role]
    ) -> Dict[str, Any]:
        """Execute non-streaming LLM call."""
        try:
            # Use gateway.chat_completion with the new args
            response = await self.gateway.chat_completion(
                messages=messages,
                task_type=TaskType.GENERAL, # Default to GENERAL, can be refined based on role/context
                stream=False,
                model_name=model_name, # Pass model_name
                temperature=temperature,
                # Additional Portkey config can be passed via kwargs too
            )
            
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return {
                "content": content,
                "success": True,
                "model": response.get("model_name"),
                "timestamp": datetime.now().isoformat(),
                "token_count": response.get("metrics", {}).get("total_tokens", 0), # Get from Portkey response
                "input_tokens": response.get("metrics", {}).get("prompt_tokens", 0),
                "output_tokens": response.get("metrics", {}).get("completion_tokens", 0),
                "role": role.value if role else None
            }
            
        except Exception as e:
            logger.error(f"Non-streaming execution failed: {e}")
            raise
    
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
    
    def _build_messages(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Build messages array for the LLM."""
        messages = []
        
        # Add system message based on context
        if context and context.get("system_prompt"):
            messages.append({
                "role": "system",
                "content": context["system_prompt"]
            })
        
        # Add context as conversation history if provided
        if context and context.get("conversation_history"):
            for msg in context["conversation_history"]:
                messages.append(msg)
        
        # Add user prompt
        messages.append({
            "role": "user", 
            "content": prompt
        })
        
        return messages
    
    def _get_temperature_for_role(self, role: Optional[Role]) -> float:
        """Get appropriate temperature for role from EliteAgentConfig."""
        role_key = role.value if role else "generator"
        return EliteAgentConfig.TEMPERATURES.get(role_key, 0.7)

    async def generate_code_streaming(
        self,
        task: str,
        role: Role = Role.GENERATOR,
        pool: str = "balanced",
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
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
                role=role
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Code generation streaming failed: {e}")
            yield {
                "type": "error",
                "content": f"Code generation error: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    def _build_coding_prompt(self, task: str, role: Role, context: Optional[Dict[str, Any]]) -> str:
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

Provide execution details and any issues found."""
        }
        
        prompt = base_prompts.get(role, base_prompts[Role.GENERATOR])
        
        # Add context if provided
        if context:
            if context.get("memory_results"):
                prompt += f"\n\nRelevant context from memory:\n{context['memory_results']}"
            if context.get("code_search_results"):
                prompt += f"\n\nRelevant code from repository:\n{context['code_search_results']}"
            if context.get("conversation_history"):
                prompt += f"\n\nPrevious discussion:\n{context['conversation_history'][-3:]}"  # Last 3 messages
        
        return prompt

    @with_circuit_breaker("external_api")
    async def embed_text(self, texts: List[str], strategy: str = "auto") -> List[List[float]]:
        """Generate embeddings for text using unified coordinator with graceful fallback."""
        # Prefer the local unified coordinator (embed_router + cache) when available
        try:
            if get_embedding_coordinator:
                # Run sync coordinator in a thread to avoid blocking event loop
                import asyncio
                coordinator = get_embedding_coordinator()
                result = await asyncio.to_thread(
                    coordinator.generate_embeddings,
                    texts,
                    strategy
                )
                embeddings = result.get("embeddings", [])
                if embeddings:
                    logger.info(f"Generated embeddings via coordinator ({result.get('strategy_used')}) for {len(texts)} texts")
                    return embeddings
        except Exception as e:
            logger.warning(f"Coordinator embedding failed, falling back to gateway: {e}")
        # Fallback to gateway (Portkey) if coordinator not available or failed
        try:
            embeddings_response = await self.gateway.generate_embeddings(texts)
            # Expecting {'data': [{'embedding': [...]}, ...]}
            embeddings = [item["embedding"] for item in embeddings_response.get("data", []) if "embedding" in item]
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
    problem: Dict, 
    agents: List[str], 
    pool: str = "balanced"
) -> Dict:
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
            "runner": Role.RUNNER
        }
        
        agent_role = role_map.get(agents[0] if agents else "generator", Role.GENERATOR)
        
        # Execute with real LLM
        result = await real_executor.execute(
            prompt=task,
            model_pool=pool,
            role=agent_role,
            context=problem.get("context")
        )
        
        return {
            "solution": result["content"],
            "confidence": 0.85 if result["success"] else 0.3,
            "agent": agents[0] if agents else "generator",
            "timestamp": result["timestamp"],
            "model": result.get("model"),
            "success": result["success"]
        }
        
    except Exception as e:
        logger.error(f"Legacy LLM execution failed: {e}")
        return {
            "solution": f"# Error executing with real LLM: {str(e)}",
            "confidence": 0.1,
            "error": str(e),
            "success": False
        }