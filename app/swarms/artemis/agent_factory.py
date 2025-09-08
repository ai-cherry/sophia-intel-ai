"""
Artemis Agent Factory - Creates specialized agents with task-specific models.
Manual-only mode: Models are explicitly assigned per Lynn's specifications.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from app.llm.multi_transport import MultiTransportLLM
from app.swarms.core.micro_swarm_base import AgentProfile, AgentRole, MicroSwarmAgent


@dataclass
class TaskConfig:
    """Configuration for a specific task type."""

    provider: str
    model: str
    max_tokens: int = 1024
    temperature: float = 0.0
    system_prompt: str = ""


class ArtemisAgent(MicroSwarmAgent):
    """Extended Artemis agent with task-specific LLM routing."""

    def __init__(
        self,
        profile: AgentProfile,
        task_config: TaskConfig,
        swarm_id: str | None = None,
    ):
        import uuid

        super().__init__(profile, swarm_id or str(uuid.uuid4()))
        self.task_config = task_config
        self.llm = MultiTransportLLM()

    async def process_task(
        self, task: str, context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Process a task using the configured model."""

        messages = [
            {
                "role": "system",
                "content": self.task_config.system_prompt or self.profile.description,
            },
            {"role": "user", "content": task},
        ]

        # Add context if provided
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            messages.insert(
                1, {"role": "system", "content": f"Context:\n{context_str}"}
            )

        # Execute with task-specific model
        response = await self.llm.complete(
            provider=self.task_config.provider,
            model=self.task_config.model,
            messages=messages,
            max_tokens=self.task_config.max_tokens,
            temperature=self.task_config.temperature,
        )

        return {
            "result": response.text,
            "model_used": f"{response.provider}/{response.model}",
            "tokens": response.usage,
        }


class ArtemisAgentFactory:
    """Factory for creating task-specific Artemis agents."""

    @staticmethod
    def load_task_config(task_type: str) -> TaskConfig:
        """Load task configuration from environment variables."""

        # Map task types to env var prefixes
        task_env_map = {
            "code_review": "CODE_REVIEW",
            "refactor": "REFACTOR",
            "test": "TEST",
            "architecture": "ARCHITECTURE",
            "security": "SECURITY",
            "docs": "DOCS",
            "vision": "VISION",
            "quick_check": "QUICK_CHECK",
            "planning": "PLANNING",
        }

        prefix = task_env_map.get(task_type)
        if not prefix:
            raise ValueError(f"Unknown task type: {task_type}")

        provider = os.getenv(f"LLM_{prefix}_PROVIDER")
        model = os.getenv(f"LLM_{prefix}_MODEL")

        if not provider or not model:
            raise RuntimeError(
                f"Task '{task_type}' requires LLM_{prefix}_PROVIDER and LLM_{prefix}_MODEL to be set"
            )

        # Task-specific system prompts
        system_prompts = {
            "code_review": """You are an expert code reviewer. Analyze code for:
- Correctness and logic errors
- Performance issues
- Security vulnerabilities
- Code style and best practices
- Potential edge cases
Provide specific, actionable feedback.""",
            "refactor": """You are a refactoring specialist. When refactoring code:
- Preserve all functionality
- Improve readability and maintainability
- Follow established patterns in the codebase
- Make incremental, safe changes
- Document significant changes""",
            "test": """You are a test generation expert. Create tests that:
- Cover happy paths and edge cases
- Follow the project's testing conventions
- Include clear assertions and error messages
- Test both success and failure scenarios
- Are maintainable and readable""",
            "architecture": """You are a software architect. Analyze and design:
- System architecture and patterns
- Component interactions and dependencies
- Scalability and performance considerations
- Technology choices and trade-offs
- Long-term maintainability""",
            "security": """You are a security specialist. Identify and address:
- Security vulnerabilities (OWASP Top 10, etc.)
- Authentication and authorization issues
- Data validation and sanitization
- Secure coding practices
- Potential attack vectors""",
            "docs": """You are a technical documentation expert. Create:
- Clear, concise documentation
- API documentation with examples
- Architecture diagrams and explanations
- User guides and tutorials
- Comprehensive changelogs""",
        }

        return TaskConfig(
            provider=provider,
            model=model,
            system_prompt=system_prompts.get(task_type, ""),
        )

    @staticmethod
    def create_agent(task_type: str, name: str | None = None) -> ArtemisAgent:
        """Create an Artemis agent for a specific task type."""

        task_config = ArtemisAgentFactory.load_task_config(task_type)

        # Map task types to agent roles
        role_map = {
            "code_review": AgentRole.ANALYST,
            "refactor": AgentRole.STRATEGIST,
            "test": AgentRole.VALIDATOR,
            "architecture": AgentRole.STRATEGIST,
            "security": AgentRole.VALIDATOR,
            "docs": AgentRole.ANALYST,
            "vision": AgentRole.ANALYST,
            "quick_check": AgentRole.VALIDATOR,
            "planning": AgentRole.STRATEGIST,
        }

        # Create agent profile
        profile = AgentProfile(
            name=name or f"artemis_{task_type}",
            role=role_map.get(task_type, AgentRole.ANALYST),
            description=f"Artemis agent specialized in {task_type}",
            model_preferences=[
                f"{task_config.provider}/{task_config.model}"
            ],  # For documentation only
            specializations=[task_type],
            reasoning_style=f"Focused on {task_type} with systematic analysis",
            confidence_threshold=0.8,
            max_tokens=task_config.max_tokens,
        )

        return ArtemisAgent(profile, task_config)

    @staticmethod
    def create_code_reviewer(name: str = "artemis_reviewer") -> ArtemisAgent:
        """Create a code review agent."""
        return ArtemisAgentFactory.create_agent("code_review", name)

    @staticmethod
    def create_refactorer(name: str = "artemis_refactor") -> ArtemisAgent:
        """Create a refactoring agent."""
        return ArtemisAgentFactory.create_agent("refactor", name)

    @staticmethod
    def create_test_generator(name: str = "artemis_tester") -> ArtemisAgent:
        """Create a test generation agent."""
        return ArtemisAgentFactory.create_agent("test", name)

    @staticmethod
    def create_architect(name: str = "artemis_architect") -> ArtemisAgent:
        """Create an architecture review agent."""
        return ArtemisAgentFactory.create_agent("architecture", name)

    @staticmethod
    def create_security_auditor(name: str = "artemis_security") -> ArtemisAgent:
        """Create a security assessment agent."""
        return ArtemisAgentFactory.create_agent("security", name)

    @staticmethod
    def create_doc_writer(name: str = "artemis_docs") -> ArtemisAgent:
        """Create a documentation agent."""
        return ArtemisAgentFactory.create_agent("docs", name)
