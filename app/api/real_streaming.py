"""
Real AI Streaming for Unified Server
Replaces mock responses with actual AI-generated content.
"""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from app.core.circuit_breaker import with_circuit_breaker
from app.llm.real_executor import Role, real_executor
from app.memory.enhanced_memory import get_enhanced_memory_instance
from app.swarms.coding.models import SwarmRequest

logger = logging.getLogger(__name__)


@with_circuit_breaker("database")
async def stream_real_ai_execution(request: Any) -> AsyncGenerator[str, None]:
    """
    Stream real AI execution with actual LLM calls.

    Args:
        request: RunRequest with message, team_id, pool, etc.

    Yields:
        Streaming JSON responses with real AI content
    """
    try:
        # Initialize
        yield json.dumps(
            {
                "phase": "initialization",
                "token": "🚀 Initializing Real AI System...",
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"
        await asyncio.sleep(0.2)

        # Memory search with real results
        memories_context = ""
        if hasattr(request, "use_memory") and request.use_memory:
            try:
                memory = await get_enhanced_memory_instance()
                search_results = await memory.search_memory(request.message, limit=5)
                memories_context = "\n".join([r.entry.content for r in search_results])

                yield json.dumps(
                    {
                        "phase": "memory",
                        "token": f"🧠 Found {len(search_results)} relevant memories",
                        "memory_count": len(search_results),
                        "timestamp": datetime.now().isoformat(),
                    }
                ) + "\n"
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.warning(f"Memory search failed: {e}")
                yield json.dumps(
                    {
                        "phase": "memory",
                        "token": "⚠️ Memory search unavailable, proceeding...",
                        "timestamp": datetime.now().isoformat(),
                    }
                ) + "\n"

        # Determine execution type based on team_id
        team_id = getattr(request, "team_id", "coding-swarm")

        if team_id == "coding-swarm":
            async for chunk in stream_coding_swarm_execution(request, memories_context):
                yield chunk
        else:
            async for chunk in stream_general_ai_execution(request, memories_context):
                yield chunk

    except Exception as e:
        logger.error(f"Real AI streaming failed: {e}", exc_info=True)
        yield json.dumps(
            {
                "phase": "error",
                "token": f"❌ AI execution failed: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"


async def stream_coding_swarm_execution(
    request: Any, memories_context: str
) -> AsyncGenerator[str, None]:
    """Stream real coding swarm execution."""
    try:
        # Planning phase
        yield json.dumps(
            {
                "phase": "planning",
                "token": "📋 AI Planner analyzing task...",
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"

        # Real planner execution
        planning_result = await real_executor.execute(
            prompt=request.message,
            model_pool=getattr(request, "pool", "balanced"),
            role=Role.PLANNER,
            context={
                "system_prompt": "You are a technical planner. Create a structured implementation plan.",
                "memory_results": memories_context,
            },
        )

        if planning_result["success"]:
            # Stream planning tokens
            plan_tokens = planning_result["content"].split()
            for i, token in enumerate(plan_tokens[:50]):  # First 50 tokens
                yield json.dumps(
                    {
                        "phase": "planning",
                        "token": token + " ",
                        "progress": i / min(50, len(plan_tokens)),
                        "timestamp": datetime.now().isoformat(),
                    }
                ) + "\n"
                await asyncio.sleep(0.05)

        yield json.dumps(
            {
                "phase": "planning_complete",
                "token": "✅ Planning phase complete",
                "planning_result": (
                    planning_result["content"][:500] + "..."
                    if planning_result["success"]
                    else "Planning failed"
                ),
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"
        await asyncio.sleep(0.3)

        # Code generation phase
        yield json.dumps(
            {
                "phase": "generation",
                "token": "💻 AI Generators creating solutions...",
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"

        # Real code generation
        generation_result = await real_executor.execute(
            prompt=f"Implement this task: {request.message}",
            model_pool=getattr(request, "pool", "balanced"),
            role=Role.GENERATOR,
            context={
                "system_prompt": "You are a senior software engineer. Write production-ready code.",
                "memory_results": memories_context,
                "planning_context": (
                    planning_result["content"] if planning_result["success"] else None
                ),
            },
        )

        if generation_result["success"]:
            # Stream generated code tokens
            code_tokens = generation_result["content"].split()
            for i, token in enumerate(code_tokens[:100]):  # First 100 tokens
                yield json.dumps(
                    {
                        "phase": "generation",
                        "token": token + " ",
                        "progress": i / min(100, len(code_tokens)),
                        "timestamp": datetime.now().isoformat(),
                    }
                ) + "\n"
                await asyncio.sleep(0.03)

        yield json.dumps(
            {
                "phase": "generation_complete",
                "token": "✅ Code generation complete",
                "generation_result": (
                    generation_result["content"][:500] + "..."
                    if generation_result["success"]
                    else "Generation failed"
                ),
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"
        await asyncio.sleep(0.3)

        # Critic review phase
        yield json.dumps(
            {
                "phase": "review",
                "token": "🔍 AI Critic reviewing code...",
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"

        # Real critic review
        critic_result = await real_executor.execute(
            prompt=f"Review this solution: {generation_result['content'][:1000] if generation_result['success'] else 'No code generated'}",
            model_pool=getattr(request, "pool", "balanced"),
            role=Role.CRITIC,
            context={
                "system_prompt": "You are a code reviewer. Provide structured feedback on quality, security, and maintainability.",
                "original_task": request.message,
            },
        )

        yield json.dumps(
            {
                "phase": "review_complete",
                "token": "✅ Code review complete",
                "critic_result": (
                    critic_result["content"][:300] + "..."
                    if critic_result["success"]
                    else "Review failed"
                ),
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"
        await asyncio.sleep(0.3)

        # Judge decision phase
        yield json.dumps(
            {
                "phase": "judgment",
                "token": "⚖️ AI Judge making final decision...",
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"

        judge_result = await real_executor.execute(
            prompt=f"Make a decision on this implementation based on the review: {critic_result['content'][:500] if critic_result['success'] else 'No review available'}",
            model_pool=getattr(request, "pool", "balanced"),
            role=Role.JUDGE,
            context={
                "system_prompt": "You are a technical judge. Make final decisions on code quality and next steps.",
                "original_task": request.message,
                "generation_result": (
                    generation_result["content"][:500]
                    if generation_result["success"]
                    else None
                ),
            },
        )

        yield json.dumps(
            {
                "phase": "judgment_complete",
                "token": "✅ Final decision made",
                "judge_result": (
                    judge_result["content"][:300] + "..."
                    if judge_result["success"]
                    else "Decision failed"
                ),
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"
        await asyncio.sleep(0.3)

        # Final results
        yield json.dumps(
            {
                "phase": "complete",
                "token": "🎯 Coding Swarm execution complete!",
                "final_results": {
                    "planning": (
                        planning_result["content"]
                        if planning_result["success"]
                        else None
                    ),
                    "generation": (
                        generation_result["content"]
                        if generation_result["success"]
                        else None
                    ),
                    "review": (
                        critic_result["content"] if critic_result["success"] else None
                    ),
                    "decision": (
                        judge_result["content"] if judge_result["success"] else None
                    ),
                    "success": all(
                        [
                            planning_result["success"],
                            generation_result["success"],
                            critic_result["success"],
                            judge_result["success"],
                        ]
                    ),
                },
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"

    except Exception as e:
        logger.error(f"Coding swarm execution failed: {e}", exc_info=True)
        yield json.dumps(
            {
                "phase": "error",
                "token": f"❌ Coding swarm error: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"


async def stream_general_ai_execution(
    request: Any, memories_context: str
) -> AsyncGenerator[str, None]:
    """Stream general AI execution for non-coding tasks."""
    try:
        yield json.dumps(
            {
                "phase": "processing",
                "token": "🤖 AI processing your request...",
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"
        await asyncio.sleep(0.2)

        # Determine appropriate role based on team_id
        role_mapping = {
            "research-swarm": Role.PLANNER,
            "security-swarm": Role.CRITIC,
            "development-swarm": Role.GENERATOR,
        }

        role = role_mapping.get(getattr(request, "team_id", ""), Role.GENERATOR)

        # Execute with streaming
        async for chunk in real_executor.generate_code_streaming(
            task=request.message,
            role=role,
            pool=getattr(request, "pool", "balanced"),
            context={
                "memory_results": memories_context,
                "team_context": getattr(request, "team_id", ""),
            },
        ):
            if chunk["type"] == "content_chunk":
                yield json.dumps(
                    {
                        "phase": "generation",
                        "token": chunk["content"],
                        "timestamp": chunk["timestamp"],
                    }
                ) + "\n"
            elif chunk["type"] == "complete":
                yield json.dumps(
                    {
                        "phase": "complete",
                        "token": "✅ AI execution complete",
                        "final_result": chunk["content"],
                        "success": chunk["success"],
                        "model": chunk.get("model"),
                        "timestamp": chunk["timestamp"],
                    }
                ) + "\n"
            elif chunk["type"] == "error":
                yield json.dumps(
                    {
                        "phase": "error",
                        "token": f'❌ {chunk["content"]}',
                        "error": chunk.get("error"),
                        "timestamp": datetime.now().isoformat(),
                    }
                ) + "\n"

            await asyncio.sleep(0.01)  # Small delay between chunks

    except Exception as e:
        logger.error(f"General AI execution failed: {e}", exc_info=True)
        yield json.dumps(
            {
                "phase": "error",
                "token": f"❌ AI execution error: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"


async def stream_real_swarm_request(
    swarm_request: SwarmRequest,
) -> AsyncGenerator[str, None]:
    """Stream execution of a real swarm request."""
    try:
        yield json.dumps(
            {
                "phase": "swarm_init",
                "token": "🔄 Initializing real swarm execution...",
                "config": swarm_request.configuration.model_dump(),
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"

        # Execute the swarm request with real implementation
        from app.swarms.coding.team import execute_swarm_request

        # This would ideally be streaming, but for now execute and return result
        result = await execute_swarm_request(swarm_request)

        # Stream the results
        if result.critic:
            yield json.dumps(
                {
                    "phase": "critic_complete",
                    "token": f"🔍 Critic verdict: {result.critic.verdict.value}",
                    "critic_data": result.critic.model_dump(),
                    "timestamp": datetime.now().isoformat(),
                }
            ) + "\n"

        if result.judge:
            yield json.dumps(
                {
                    "phase": "judge_complete",
                    "token": f"⚖️ Judge decision: {result.judge.decision.value}",
                    "judge_data": result.judge.model_dump(),
                    "timestamp": datetime.now().isoformat(),
                }
            ) + "\n"

        yield json.dumps(
            {
                "phase": "swarm_complete",
                "token": f'✅ Swarm execution {"approved" if result.runner_approved else "requires review"}',
                "final_result": result.model_dump(),
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"

    except Exception as e:
        logger.error(f"Swarm request execution failed: {e}", exc_info=True)
        yield json.dumps(
            {
                "phase": "swarm_error",
                "token": f"❌ Swarm execution failed: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        ) + "\n"
