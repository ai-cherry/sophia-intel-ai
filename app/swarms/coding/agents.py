"""
Agent builders for the Coding Swarm.

This module provides factory functions for creating specialized agents
with appropriate models, tools, and instructions for software development tasks.
"""

from typing import Optional

from textwrap import dedent

from agno.agent import Agent
from agno.tools import Function as Tool

from app.models.simple_router import ROLE_MODELS, ROLE_PARAMS, agno_chat_model
from app.swarms.contracts import CRITIC_SCHEMA, GENERATOR_SCHEMA, JUDGE_SCHEMA, PLANNER_SCHEMA
from app.tools.basic_tools import (
    CodeSearch,
    FormatCode,
    GitAdd,
    GitCommit,
    GitDiff,
    GitStatus,
    ListDirectory,
    ReadFile,
    RunLint,
    RunTests,
    RunTypeCheck,
    WriteFile,
)

# System prompts for role-specific behavior
PLANNER_SYS = dedent(f"""
You are the Planner. Convert vague goals into an executable plan.
Return a strict JSON object per PLANNER_SCHEMA; do not include extra text.

{PLANNER_SCHEMA}

Focus on:
- Breaking down complex tasks into milestones and epics
- Identifying dependencies between stories
- Assessing global risks
- Suggesting appropriate tools
- Defining success metrics
""")

CRITIC_SYS = dedent(f"""
You are the Critic. Provide a structured review of all proposals.
Return strict JSON per CRITIC_SCHEMA; no extra prose.

{CRITIC_SCHEMA}

Review across these dimensions:
- Security: authentication, authorization, data protection
- Data integrity: validation, consistency, persistence
- Logic correctness: edge cases, error handling, algorithms
- Performance: time complexity, space usage, scalability
- Usability: API design, error messages, documentation
- Maintainability: code clarity, test coverage, modularity
""")

JUDGE_SYS = dedent(f"""
You are the Judge. Compare and merge proposals using the quality rubric.
Return strict JSON per JUDGE_SCHEMA; no extra prose.

{JUDGE_SCHEMA}

Decision criteria:
- accept: proposal meets all requirements
- merge: combine best aspects of multiple proposals
- reject: critical issues that cannot be fixed

Always include concrete runner_instructions for implementation.
""")

GENERATOR_SYS = dedent(f"""
You are a Code Generator. Create implementation plans with tests.
When asked, return JSON per GENERATOR_SCHEMA:

{GENERATOR_SCHEMA}

Focus on:
- Minimal diff approach
- Comprehensive test coverage
- Clear implementation steps
- Risk assessment
""")

def make_planner(name: str = "Planner") -> Agent:
    """Create a planning agent with strategic capabilities."""
    m_id = ROLE_MODELS["planner"]
    params = ROLE_PARAMS.get("planner", {})

    return Agent(
        name=name,
        role="Plan tasks with dependencies and success metrics",
        model=agno_chat_model(m_id, **params),
        instructions=PLANNER_SYS,
        tools=[CodeSearch(), ListDirectory(), GitStatus()],
        reasoning=True,
        markdown=True,
        show_tool_calls=True
    )

def make_generator(
    name: str,
    model_name: str,
    tools: Optional[list[Tool]] = None,
    role_note: str = "Implement spec with tests and minimal diff"
) -> Agent:
    """
    Create a code generation agent with specific model.
    
    Args:
        name: Agent name for identification
        model_name: Model name from ROLE_MODELS or direct model ID
        tools: List of tools to provide to the agent
        role_note: Specific role description for the agent
        
    Returns:
        Configured Agent instance
    """
    m_id = ROLE_MODELS.get(model_name, model_name)
    params = ROLE_PARAMS.get(model_name, {})

    default_tools = [
        CodeSearch(),
        ReadFile(),
        ListDirectory(),
        RunTests(),
        RunTypeCheck()
    ]

    return Agent(
        name=name,
        role=role_note,
        model=agno_chat_model(m_id, **params),
        instructions=GENERATOR_SYS,
        tools=tools or default_tools,
        markdown=True,
        show_tool_calls=True
    )

def make_critic(name: str = "Critic") -> Agent:
    """Create a review agent with structured critique capabilities."""
    m_id = ROLE_MODELS["critic"]
    params = ROLE_PARAMS.get("critic", {})

    return Agent(
        name=name,
        role="Structured review across security/data/logic/perf/UX",
        model=agno_chat_model(m_id, **params),
        instructions=CRITIC_SYS,
        tools=[
            CodeSearch(),
            ReadFile(),
            GitDiff(),
            RunLint(),
            RunTypeCheck()
        ],
        markdown=True,
        show_tool_calls=True
    )

def make_judge(name: str = "Judge") -> Agent:
    """Create a decision agent with merge capabilities."""
    m_id = ROLE_MODELS["judge"]
    params = ROLE_PARAMS.get("judge", {})

    return Agent(
        name=name,
        role="Select or merge proposals; instruct Runner",
        model=agno_chat_model(m_id, **params),
        instructions=JUDGE_SYS,
        tools=[
            GitStatus(),
            GitDiff(),
            RunTests()
        ],
        markdown=True,
        show_tool_calls=True
    )

def make_lead(name: str = "Lead-Engineer") -> Agent:
    """Create a coordination agent to orchestrate the team."""
    m_id = ROLE_MODELS.get("planner")  # Lead uses planner model
    params = ROLE_PARAMS.get("planner", {})

    return Agent(
        name=name,
        role="Coordinate debate; enforce constraints; route tasks",
        model=agno_chat_model(m_id, **params),
        instructions=dedent("""
        You are the Lead Engineer coordinating the team.
        
        Your responsibilities:
        - Route tasks to appropriate team members
        - Coordinate parallel work when possible
        - Enforce quality gates and constraints
        - Synthesize multiple proposals
        - Ensure all acceptance criteria are met
        
        When coordinating:
        1. First, have generators propose competing approaches
        2. Then, have the critic review all proposals
        3. If revision needed, have generators apply fixes
        4. Finally, have the judge make the final decision
        """),
        tools=[
            CodeSearch(),
            ListDirectory(),
            GitStatus()
        ],
        markdown=True,
        show_tool_calls=True
    )

def make_runner(name: str = "Runner") -> Agent:
    """Create an execution agent with write permissions (gated by judge)."""
    m_id = ROLE_MODELS.get("fast")  # Runner uses fast model
    params = ROLE_PARAMS.get("fast", {})

    return Agent(
        name=name,
        role="Execute approved changes with write permissions",
        model=agno_chat_model(m_id, **params),
        instructions=dedent("""
        You are the Runner, responsible for executing approved changes.
        
        CRITICAL: You may ONLY execute if you have explicit judge approval.
        Check for runner_instructions from the judge before any action.
        
        When executing:
        1. Follow runner_instructions exactly
        2. Make minimal, precise changes
        3. Run tests after changes
        4. Report success/failure clearly
        """),
        tools=[
            ReadFile(),
            WriteFile(),  # Write tools ONLY for runner
            GitAdd(),
            GitCommit(),
            RunTests(),
            RunLint(),
            FormatCode()
        ],
        markdown=True,
        show_tool_calls=True
    )

# Backward compatibility functions
def create_lead_agent() -> Agent:
    """Legacy: Create the Lead agent that coordinates the team."""
    return make_lead()

def create_coder_a_agent() -> Agent:
    """Legacy: Create Coder A agent specialized in implementation."""
    return make_generator("Coder-A", "coderA")

def create_coder_b_agent() -> Agent:
    """Legacy: Create Coder B agent specialized in optimization."""
    return make_generator("Coder-B", "coderB")

def create_critic_agent() -> Agent:
    """Legacy: Create Critic agent for code review."""
    return make_critic()

def create_judge_agent() -> Agent:
    """Legacy: Create Judge agent for final decisions."""
    return make_judge()
