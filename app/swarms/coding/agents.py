from agno import Agent
from app.models.router import chat_model, MODELS
from app.tools.code_search import CodeSearch
from app.tools.repo_fs import ReadFile, WriteFile, ListDirectory
from app.tools.git_ops import GitStatus, GitDiff, GitCommit, GitAdd
from app.tools.test_ops import RunTests, RunTypeCheck
from app.tools.lint_ops import RunLint, FormatCode

def create_lead_agent() -> Agent:
    """Create the Lead agent that coordinates the team."""
    return Agent(
        name="Lead",
        description="Team lead that coordinates work and makes architectural decisions",
        model=chat_model(MODELS["planner"]),
        tools=[
            CodeSearch(),
            ListDirectory(),
            GitStatus()
        ],
        instructions="""
        You are the team lead responsible for:
        - Breaking down complex tasks into smaller subtasks
        - Assigning work to appropriate team members
        - Ensuring code quality and consistency
        - Making architectural decisions
        - Coordinating between team members
        """
    )

def create_coder_a_agent() -> Agent:
    """Create Coder A agent specialized in implementation."""
    return Agent(
        name="Coder-A",
        description="Senior developer focused on implementation and best practices",
        model=chat_model(MODELS["coder_a"]),
        tools=[
            CodeSearch(),
            ReadFile(),
            WriteFile(),
            ListDirectory(),
            RunTests(),
            RunTypeCheck()
        ],
        instructions="""
        You are a senior developer responsible for:
        - Writing clean, maintainable code
        - Implementing features according to specifications
        - Following best practices and design patterns
        - Writing unit tests
        - Ensuring type safety
        """
    )

def create_coder_b_agent() -> Agent:
    """Create Coder B agent specialized in optimization and refactoring."""
    return Agent(
        name="Coder-B",
        description="Developer focused on optimization and code improvement",
        model=chat_model(MODELS["coder_b"]),
        tools=[
            CodeSearch(),
            ReadFile(),
            WriteFile(),
            RunLint(),
            FormatCode()
        ],
        instructions="""
        You are a developer responsible for:
        - Optimizing code performance
        - Refactoring for better readability
        - Ensuring code follows style guidelines
        - Identifying and fixing code smells
        - Improving code efficiency
        """
    )

def create_critic_agent() -> Agent:
    """Create Critic agent for code review."""
    return Agent(
        name="Critic",
        description="Code reviewer that provides feedback and ensures quality",
        model=chat_model(MODELS["critic"]),
        tools=[
            CodeSearch(),
            ReadFile(),
            GitDiff(),
            RunLint(),
            RunTypeCheck()
        ],
        instructions="""
        You are a code reviewer responsible for:
        - Reviewing code changes for quality
        - Identifying potential bugs and issues
        - Ensuring adherence to coding standards
        - Providing constructive feedback
        - Verifying test coverage
        """
    )

def create_judge_agent() -> Agent:
    """Create Judge agent for final decisions."""
    return Agent(
        name="Judge",
        description="Final decision maker on code quality and merge readiness",
        model=chat_model(MODELS["judge"]),
        tools=[
            GitStatus(),
            GitDiff(),
            RunTests(),
            GitCommit(),
            GitAdd()
        ],
        instructions="""
        You are the final decision maker responsible for:
        - Approving or rejecting code changes
        - Ensuring all quality criteria are met
        - Making final decisions on disputes
        - Authorizing commits and merges
        - Maintaining project standards
        """
    )