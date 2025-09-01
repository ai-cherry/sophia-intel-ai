#!/usr/bin/env python3
"""
Modern Agno 1.8.1 Playground with Portkey Gateway Integration.
Uses the latest Agno APIs and patterns for multi-agent orchestration.
"""

from fastapi import FastAPI
from agno.apps.fastapi import create_fastapi_app
from agno.agent import Agent
from agno.teams import Team
from agno.tools.duckduckgo import DuckDuckGo
from agno.memory import Memory
from typing import Dict, Any, List

# Import our custom tools
from app.tools.code_search import CodeSearch
from app.tools.repo_fs import ReadFile, WriteFile, ListDirectory
from app.tools.git_ops import GitStatus, GitDiff, GitCommit, GitAdd
from app.tools.test_ops import RunTests, RunTypeCheck

# Model routing via Portkey - these strings are mapped by Portkey to actual providers
# Using OpenRouter for most models, with fallbacks configured in Portkey
MODELS = {
    # Planning & Architecture
    "planner": "openrouter/anthropic/claude-3-7-sonnet",  # Best for strategic planning
    "architect": "openai/gpt-4o",  # Architecture decisions
    
    # Code Generation (multiple options for diversity)
    "coder_primary": "openrouter/qwen/qwen-2.5-coder-32b-instruct",  # Primary coder
    "coder_secondary": "openrouter/deepseek/deepseek-coder-v2",  # Alternative approach
    "coder_fast": "openrouter/deepseek/deepseek-coder-6.7b",  # Quick iterations
    
    # Analysis & Review
    "critic": "openai/gpt-4o-mini",  # Fast, accurate review
    "security": "anthropic/claude-3-haiku",  # Security analysis
    "performance": "openrouter/mistral/mistral-large",  # Performance review
    
    # Decision Making
    "judge": "openrouter/deepseek/deepseek-reasoner",  # Complex reasoning
    "evaluator": "openai/gpt-4o",  # Final evaluation
    
    # Specialized Tasks
    "researcher": "openrouter/perplexity/llama-3.1-sonar-large",  # Web research
    "documenter": "anthropic/claude-3-sonnet",  # Documentation
    "tester": "openrouter/qwen/qwen-2.5-coder-32b-instruct",  # Test generation
}

# Initialize shared components
memory = Memory()  # Local memory store (can upgrade to persistent later)
search_tool = DuckDuckGo()
code_search = CodeSearch()

# === Core Planning & Architecture Agents ===

planner = Agent(
    name="Strategic Planner",
    model=MODELS["planner"],
    tools=[code_search, ListDirectory(), GitStatus()],
    memory=memory,
    system_prompt="""You are a strategic planning specialist. Break down complex requirements into:
    - Clear milestones with dependencies
    - Executable epics and stories
    - Risk assessments and mitigation strategies
    - Tool recommendations
    - Success metrics
    Always output structured JSON for downstream consumption.""",
    reasoning=True,
    markdown=True,
)

architect = Agent(
    name="System Architect",
    model=MODELS["architect"],
    tools=[code_search, ReadFile(), ListDirectory()],
    memory=memory,
    system_prompt="""You are a system architect focused on:
    - Design patterns and best practices
    - Module boundaries and interfaces
    - Performance and scalability
    - Security architecture
    - Technology selection
    Provide clear architectural decisions with rationale.""",
    reasoning=True,
)

# === Code Generation Swarm (Diverse Approaches) ===

coder_primary = Agent(
    name="Primary Coder",
    model=MODELS["coder_primary"],
    tools=[code_search, ReadFile(), WriteFile(), RunTests()],
    memory=memory,
    system_prompt="""You are an expert software engineer using Qwen-2.5-Coder.
    Focus on:
    - Clean, idiomatic code
    - Comprehensive error handling
    - Minimal diff approach
    - Test-driven development
    - Performance optimization""",
    reasoning=True,
)

coder_secondary = Agent(
    name="Alternative Coder",
    model=MODELS["coder_secondary"],
    tools=[code_search, ReadFile(), WriteFile(), RunTests()],
    memory=memory,
    system_prompt="""You are a creative problem solver using DeepSeek-Coder.
    Provide alternative implementations focusing on:
    - Different algorithmic approaches
    - Novel design patterns
    - Edge case handling
    - Resource efficiency""",
    reasoning=True,
)

coder_fast = Agent(
    name="Fast Prototyper",
    model=MODELS["coder_fast"],
    tools=[code_search, ReadFile(), WriteFile()],
    memory=memory,
    system_prompt="""You are a rapid prototyping specialist.
    Quickly produce:
    - Working proof of concepts
    - Minimal viable implementations
    - Quick fixes and patches
    - Script automation""",
)

# === Quality Assurance Agents ===

critic = Agent(
    name="Code Critic",
    model=MODELS["critic"],
    tools=[ReadFile(), RunTests(), RunTypeCheck()],
    memory=memory,
    system_prompt="""You are a thorough code reviewer. Analyze for:
    - Logic errors and edge cases
    - Code quality and maintainability
    - Performance bottlenecks
    - Security vulnerabilities
    - Test coverage gaps
    Output structured feedback with severity levels.""",
    reasoning=True,
)

security_analyst = Agent(
    name="Security Analyst",
    model=MODELS["security"],
    tools=[ReadFile(), code_search],
    memory=memory,
    system_prompt="""You are a security specialist. Check for:
    - Authentication/authorization flaws
    - Injection vulnerabilities
    - Data exposure risks
    - Cryptographic weaknesses
    - Supply chain vulnerabilities
    Rate findings by CVSS severity.""",
)

performance_analyst = Agent(
    name="Performance Analyst",
    model=MODELS["performance"],
    tools=[ReadFile(), RunTests()],
    memory=memory,
    system_prompt="""You are a performance optimization expert. Analyze:
    - Time and space complexity
    - Database query efficiency
    - Caching opportunities
    - Concurrency patterns
    - Resource utilization
    Suggest concrete optimizations with benchmarks.""",
)

# === Decision & Integration Agents ===

judge = Agent(
    name="Technical Judge",
    model=MODELS["judge"],
    memory=memory,
    system_prompt="""You are the final arbiter using deep reasoning.
    - Compare multiple solutions objectively
    - Identify best practices from each approach
    - Merge compatible improvements
    - Make decisive recommendations
    - Explain trade-offs clearly
    Always provide actionable next steps.""",
    reasoning=True,
)

evaluator = Agent(
    name="Quality Evaluator",
    model=MODELS["evaluator"],
    tools=[RunTests(), RunTypeCheck()],
    memory=memory,
    system_prompt="""You are the quality gatekeeper.
    Evaluate solutions against:
    - Functional requirements
    - Non-functional requirements
    - Code quality standards
    - Test coverage thresholds
    - Performance benchmarks
    Provide PASS/FAIL with detailed scoring.""",
)

# === Specialized Support Agents ===

researcher = Agent(
    name="Technical Researcher",
    model=MODELS["researcher"],
    tools=[search_tool, code_search],
    memory=memory,
    system_prompt="""You are a research specialist.
    - Find best practices and patterns
    - Research library documentation
    - Analyze similar implementations
    - Investigate error solutions
    - Compare technology options
    Cite all sources with links.""",
)

documenter = Agent(
    name="Documentation Expert",
    model=MODELS["documenter"],
    tools=[ReadFile(), WriteFile()],
    memory=memory,
    system_prompt="""You are a technical writer.
    Create clear documentation:
    - API references
    - Architecture diagrams (mermaid)
    - Setup guides
    - Inline code comments
    - README updates
    Follow docs-as-code principles.""",
)

tester = Agent(
    name="Test Engineer",
    model=MODELS["tester"],
    tools=[ReadFile(), WriteFile(), RunTests()],
    memory=memory,
    system_prompt="""You are a test automation expert.
    Create comprehensive tests:
    - Unit tests with mocks
    - Integration tests
    - Property-based tests
    - Performance tests
    - Security tests
    Aim for >90% coverage.""",
)

# === Team Compositions ===

# Quick fixes and simple tasks (3 agents)
fast_team = Team(
    name="Fast Team",
    agents=[coder_fast, critic],
    judge=judge,
    description="Quick turnaround for simple tasks",
)

# Standard development team (5 agents)
standard_team = Team(
    name="Standard Team",
    agents=[planner, coder_primary, critic, tester],
    judge=judge,
    description="Balanced team for most development tasks",
)

# Advanced team with alternatives (7 agents)
advanced_team = Team(
    name="Advanced Team",
    agents=[planner, coder_primary, coder_secondary, critic, security_analyst],
    judge=judge,
    description="Multiple approaches with security review",
)

# Full swarm for critical features (10+ agents)
genesis_team = Team(
    name="GENESIS Team",
    agents=[
        planner,
        architect,
        coder_primary,
        coder_secondary,
        critic,
        security_analyst,
        performance_analyst,
        tester,
        documenter,
    ],
    judge=judge,
    description="Complete team for mission-critical features",
)

# Research and exploration team
research_team = Team(
    name="Research Team",
    agents=[researcher, architect, coder_fast],
    judge=evaluator,
    description="Exploration and proof of concepts",
)

# === Create FastAPI Application ===

app: FastAPI = create_fastapi_app(
    title="Sophia Intel AI - Agno 1.8.1 Playground",
    description="Multi-agent orchestration with Portkey gateway routing",
    version="2.0.0",
    agents={
        # Individual agents
        "planner": planner,
        "architect": architect,
        "coder_primary": coder_primary,
        "coder_secondary": coder_secondary,
        "critic": critic,
        "security": security_analyst,
        "performance": performance_analyst,
        "judge": judge,
        "researcher": researcher,
        "documenter": documenter,
        "tester": tester,
        
        # Teams
        "fast_team": fast_team,
        "standard_team": standard_team,
        "advanced_team": advanced_team,
        "genesis_team": genesis_team,
        "research_team": research_team,
    },
)

# === Custom Endpoints ===

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "agents_available": len(app.state.agents) if hasattr(app, "state") else 0,
        "teams_configured": 5,
    }

@app.get("/models")
def list_models():
    """List all configured models and their purposes."""
    return MODELS

@app.get("/agents/capabilities")
def agent_capabilities():
    """Describe agent capabilities and optimal use cases."""
    return {
        "individuals": {
            "planner": "Strategic planning and task breakdown",
            "architect": "System design and technology selection",
            "coder_primary": "Primary implementation (Qwen-2.5)",
            "coder_secondary": "Alternative implementation (DeepSeek)",
            "critic": "Code review and quality assurance",
            "security": "Security vulnerability analysis",
            "performance": "Performance optimization",
            "judge": "Decision making and conflict resolution",
            "researcher": "Technical research and documentation lookup",
            "documenter": "Documentation and guides",
            "tester": "Test creation and automation",
        },
        "teams": {
            "fast_team": "Quick fixes, patches, simple features",
            "standard_team": "Regular development tasks",
            "advanced_team": "Complex features with multiple approaches",
            "genesis_team": "Mission-critical, full-lifecycle development",
            "research_team": "Exploration, POCs, technology evaluation",
        },
    }

@app.post("/smart_route")
async def smart_route(task: Dict[str, Any]):
    """Intelligently route tasks to appropriate team based on complexity."""
    description = task.get("description", "")
    complexity = task.get("complexity", "medium")
    
    # Simple routing logic (can be enhanced with ML later)
    if complexity == "low" or "hotfix" in description.lower():
        team_name = "fast_team"
    elif complexity == "high" or "architecture" in description.lower():
        team_name = "genesis_team"
    elif "research" in description.lower() or "explore" in description.lower():
        team_name = "research_team"
    elif "security" in description.lower():
        team_name = "advanced_team"
    else:
        team_name = "standard_team"
    
    return {
        "recommended_team": team_name,
        "reasoning": f"Based on complexity '{complexity}' and task description",
        "alternatives": ["genesis_team", "advanced_team"] if complexity == "high" else ["fast_team"],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7777)