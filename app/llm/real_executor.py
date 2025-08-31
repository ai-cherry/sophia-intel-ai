"""
Real LLM Executor with Portkey Integration
Replaces all mock/template responses with actual LLM calls.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime

from app.portkey_config import gateway, Role, MODEL_RECOMMENDATIONS
from app.swarms.coding.models import PoolType

logger = logging.getLogger(__name__)


class RealLLMExecutor:
    """Execute real LLM calls through Portkey gateway."""
    
    def __init__(self):
        self.gateway = gateway
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
    
    async def _execute_streaming(
        self,
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float,
        role: Optional[Role]
    ) -> Dict[str, Any]:
        """Execute streaming LLM call."""
        try:
            stream = await self.gateway.achat(
                messages=messages,
                model=model,
                temperature=temperature,
                role=role,
                stream=True
            )
            
            full_content = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_content += content_chunk
                    yield {
                        "type": "content_chunk",
                        "content": content_chunk,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Final result
            yield {
                "type": "complete",
                "content": full_content,
                "success": True,
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "token_count": len(full_content.split())
            }
            
        except Exception as e:
            logger.error(f"Streaming execution failed: {e}")
            yield {
                "type": "error",
                "content": f"Streaming error: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    async def _execute_non_streaming(
        self,
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float,
        role: Optional[Role]
    ) -> Dict[str, Any]:
        """Execute non-streaming LLM call."""
        try:
            content = await self.gateway.achat(
                messages=messages,
                model=model,
                temperature=temperature,
                role=role,
                stream=False
            )
            
            return {
                "content": content,
                "success": True,
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "token_count": len(content.split()) if content else 0,
                "role": role.value if role else None
            }
            
        except Exception as e:
            logger.error(f"Non-streaming execution failed: {e}")
            raise
    
    def _select_model(self, pool: str, role: Optional[Role]) -> str:
        """Select appropriate model based on pool and role."""
        try:
            pool_type = PoolType(pool.lower())
        except ValueError:
            pool_type = PoolType.BALANCED
            
        # Role-specific model selection
        if role and role in MODEL_RECOMMENDATIONS:
            if role == Role.GENERATOR:
                pool_models = MODEL_RECOMMENDATIONS[role].get(pool_type.value, [])
                if pool_models:
                    return pool_models[0]  # First model in pool
                return MODEL_RECOMMENDATIONS[role]["balanced"][0]
            else:
                return MODEL_RECOMMENDATIONS[role]["default"]
        
        # Default pool-based selection
        generator_models = MODEL_RECOMMENDATIONS[Role.GENERATOR]
        pool_models = generator_models.get(pool_type.value, generator_models["balanced"])
        return pool_models[0] if pool_models else "openai/gpt-4o"
    
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
        """Get appropriate temperature for role."""
        if not role:
            return 0.7
            
        return MODEL_RECOMMENDATIONS.get(role, {}).get("temperature", 0.7)

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

    async def embed_text(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text using real embedding models."""
        try:
            embeddings = await self.gateway.aembed(texts)
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Return zero vectors as fallback
            return [[0.0] * 1024 for _ in texts]


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