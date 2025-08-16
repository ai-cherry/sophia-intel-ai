"""
Coding Agent implementation using Agno framework.
Provides code analysis, modification, and generation capabilities.
"""

import asyncio
import difflib
import json
from typing import Any, Dict, List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from loguru import logger

from config.config import settings
from libs.mcp_client.memory_client import MCPMemoryClient

from .base_agent import BaseAgent


class CodingAgent(BaseAgent):
    """
    Agent specialized in code-related tasks using Agno framework.
    Integrates with MCP memory service for context-aware responses.
    """

    def __init__(self, concurrency: int = None, timeout_seconds: int = None):
        """Initialize the coding agent with Agno backend."""
        super().__init__(
            name="CodingAgent",
            concurrency=concurrency or settings.AGENT_CONCURRENCY,
            timeout_seconds=timeout_seconds or settings.AGENT_TIMEOUT_SECONDS,
        )

        # Initialize MCP Memory Client
        self.memory_client = MCPMemoryClient()

        # Initialize Agno agent with base instructions
        base_instructions = [
            "You are an expert software engineer and code analyst.",
            "Always respond with valid JSON in this exact format:",
            '{"summary": "Brief description of changes made", "patch": "unified diff format patch"}',
            "For the patch field, use unified diff format (--- +++ @@ syntax).",
            "Make minimal, targeted changes that solve the specific problem.",
            "If no changes are needed, return empty string for patch.",
            "Include proper context lines (3 lines before/after) in diffs.",
            "Focus on code quality, best practices, and maintainability.",
        ]

        # Apply the No Bullshit policy and other system rules
        final_instructions = self.apply_system_prompt_rules(base_instructions)

        self.agno = Agent(
            name="Sophia Coding Agent",
            model=OpenAIChat(
                id="gpt-4o",
                api_key=settings.OPENROUTER_API_KEY,
                base_url=("https://api.openrouter.ai/v1" if settings.openrouter_API_KEY else None),
                extra_headers=(
                    {
                        "X-ROUTER-TARGET": "openrouter",
                        "X-openrouter-API-KEY": settings.openrouter_API_KEY,
                    }
                    if settings.openrouter_API_KEY
                    else {}
                ),
            ),
            storage=SqliteStorage(
                table_name="coding_agent_conversations",
                db_file=settings.AGNO_STORAGE_DB,
            ),
            instructions=final_instructions,
            add_datetime_to_instructions=True,
            add_history_to_messages=True,
            num_history_responses=5,
            markdown=False,
            response_model=None,  # We'll handle JSON parsing ourselves
            show_tool_calls=False,
        )

    async def _process_task_impl(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process coding task with context from MCP memory service.

        Expected task_data format:
        {
            "session_id": str,
            "code": str,
            "query": str,
            "file_path": str (optional),
            "language": str (optional)
        }
        """
        session_id = task_data.get("session_id", "default")
        code = task_data.get("code", "")
        query = task_data.get("query", "Analyze and improve this code")
        file_path = task_data.get("file_path", "")
        language = task_data.get("language", "")

        logger.info(f"Processing coding task for session {session_id}")

        # Fetch relevant context from MCP memory
        context_results = await self._fetch_memory_context(session_id, query)

        # Build comprehensive prompt
        prompt = self._build_prompt(code, query, context_results, file_path, language)

        # Store current task context in MCP
        await self._store_task_context(session_id, task_id, code, query)

        # Execute via Agno (run in thread pool since Agno is sync)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: self.agno.run(prompt, session_id=session_id))

        # Parse and validate response
        result = self._parse_response(str(response), code)

        # Store result context in MCP
        await self._store_result_context(session_id, task_id, result)

        return result

    async def _fetch_memory_context(self, session_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Fetch relevant context from MCP memory service."""
        try:
            return await self.memory_client.query(session_id=session_id, query=query, top_k=top_k, threshold=0.7)
        except Exception as e:
            logger.warning(f"Failed to fetch memory context: {e}")
            return []

    async def _store_task_context(self, session_id: str, task_id: str, code: str, query: str) -> None:
        """Store task context in MCP memory."""
        try:
            await self.memory_client.store(
                session_id=session_id,
                content=f"Task: {query}\nCode:\n{code}",
                metadata={
                    "task_id": task_id,
                    "context_type": "coding_task",
                    "query": query,
                },
                context_type="coding_task",
            )
        except Exception as e:
            logger.warning(f"Failed to store task context: {e}")

    async def _store_result_context(self, session_id: str, task_id: str, result: Dict[str, Any]) -> None:
        """Store result context in MCP memory."""
        try:
            await self.memory_client.store(
                session_id=session_id,
                content=f"Result: {result['summary']}\nPatch:\n{result['patch']}",
                metadata={
                    "task_id": task_id,
                    "context_type": "coding_result",
                    "summary": result["summary"],
                },
                context_type="coding_result",
            )
        except Exception as e:
            logger.warning(f"Failed to store result context: {e}")

    def _build_prompt(
        self,
        code: str,
        query: str,
        context: List[Dict[str, Any]],
        file_path: str = "",
        language: str = "",
    ) -> str:
        """Build comprehensive prompt for the coding task."""
        prompt_parts = []

        # Add context if available
        if context:
            prompt_parts.append("## Relevant Context:")
            for ctx in context:
                prompt_parts.append(f"- {ctx.get('content', '')[:200]}...")

        # Add task description
        prompt_parts.append("## Task:")
        prompt_parts.append(query)

        # Add file info if available
        if file_path:
            prompt_parts.append("## File Path:")
            prompt_parts.append(file_path)

        if language:
            prompt_parts.append("## Language:")
            prompt_parts.append(language)

        # Add code
        prompt_parts.append("## Code to Analyze:")
        prompt_parts.append(f"```{language}")
        prompt_parts.append(code)
        prompt_parts.append("```")

        # Add instructions
        prompt_parts.append("\n## Instructions:")
        prompt_parts.append("Analyze the code and provide improvements according to the task.")
        prompt_parts.append("Return ONLY a valid JSON response with 'summary' and 'patch' fields.")
        prompt_parts.append("Use unified diff format for the patch field.")

        return "\n".join(prompt_parts)

    def _parse_response(self, response: str, original_code: str) -> Dict[str, Any]:
        """Parse and validate agent response."""
        try:
            # Try to extract JSON from response
            response = response.strip()

            # Handle potential markdown wrapping
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]

            # Parse JSON
            result = json.loads(response)

            # Validate required fields
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")

            if "summary" not in result or "patch" not in result:
                raise ValueError("Missing required fields (summary, patch)")

            # Validate types
            if not isinstance(result["summary"], str):
                raise ValueError("Summary must be a string")

            if not isinstance(result["patch"], str):
                raise ValueError("Patch must be a string")

            # If patch is empty, that's valid (no changes needed)
            return {"summary": result["summary"], "patch": result["patch"]}

        except Exception as e:
            logger.error(f"Failed to parse agent response: {e}")
            logger.debug(f"Raw response: {response}")

            # Return fallback response
            return {"summary": f"Failed to parse agent response: {e}", "patch": ""}

    def _generate_unified_diff(self, original: str, modified: str, filename: str = "file") -> str:
        """Generate unified diff format patch."""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm="",
        )

        return "".join(diff)
