#!/usr/bin/env python3
"""
Agno 1.8.1 Playground with centralized environment configuration.
Uses env_loader for all API keys and settings.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from agno.apps.fastapi import create_fastapi_app
from agno.agent import Agent
from agno.teams import Team
from agno.tools.duckduckgo import DuckDuckGo
from agno.memory import Memory
from typing import Dict, Any, List, Optional

# Import our environment loader
from app.config.env_loader import get_env_config, validate_environment

# Import our custom tools
try:
    from app.tools.code_search import CodeSearch
    from app.tools.repo_fs import ReadFile, WriteFile, ListDirectory
    from app.tools.git_ops import GitStatus, GitDiff, GitCommit, GitAdd
    from app.tools.test_ops import RunTests, RunTypeCheck
    CUSTOM_TOOLS_AVAILABLE = True
except ImportError:
    CUSTOM_TOOLS_AVAILABLE = False
    print("⚠️  Custom tools not available, using basic tools only")

# Load environment configuration
print("Loading environment configuration...")
config = get_env_config()

# Validate environment
if not validate_environment():
    print("\n⚠️  WARNING: Environment not fully configured")
    print("Some features may not work without proper API keys")
    print("Copy .env.complete to .env and add your keys\n")

# Configure Agno with loaded settings
import os
os.environ["AGNO_TELEMETRY"] = str(config.agno_telemetry).lower()
if config.agno_api_key:
    os.environ["AGNO_API_KEY"] = config.agno_api_key

# Model routing based on configuration
# These will use Portkey gateway if configured, or direct providers
MODELS = {
    # Use configured gateway or fallback to defaults
    "planner": os.getenv("PLANNER_MODEL", "openrouter/anthropic/claude-3-7-sonnet"),
    "architect": os.getenv("ARCHITECT_MODEL", "openai/gpt-4o"),
    "coder_primary": os.getenv("CODER_PRIMARY_MODEL", "openrouter/qwen/qwen-2.5-coder-32b-instruct"),
    "coder_secondary": os.getenv("CODER_SECONDARY_MODEL", "openrouter/deepseek/deepseek-coder-v2"),
    "coder_fast": os.getenv("CODER_FAST_MODEL", "openrouter/deepseek/deepseek-coder-6.7b"),
    "critic": os.getenv("CRITIC_MODEL", "openai/gpt-4o-mini"),
    "security": os.getenv("SECURITY_MODEL", "anthropic/claude-3-haiku"),
    "performance": os.getenv("PERFORMANCE_MODEL", "openrouter/mistral/mistral-large"),
    "judge": os.getenv("JUDGE_MODEL", "openrouter/deepseek/deepseek-reasoner"),
    "evaluator": os.getenv("EVALUATOR_MODEL", "openai/gpt-4o"),
    "researcher": os.getenv("RESEARCHER_MODEL", "openrouter/perplexity/llama-3.1-sonar-large"),
    "documenter": os.getenv("DOCUMENTER_MODEL", "anthropic/claude-3-sonnet"),
    "tester": os.getenv("TESTER_MODEL", "openrouter/qwen/qwen-2.5-coder-32b-instruct"),
}

# Initialize shared components
memory = Memory()
search_tool = DuckDuckGo()

# Initialize custom tools if available
if CUSTOM_TOOLS_AVAILABLE:
    code_search = CodeSearch()
    read_file = ReadFile()
    write_file = WriteFile() if config.enable_writes else None
    list_dir = ListDirectory()
    git_status = GitStatus()
    git_diff = GitDiff()
    git_commit = GitCommit() if config.enable_writes else None
    git_add = GitAdd() if config.enable_writes else None
    run_tests = RunTests()
    run_typecheck = RunTypeCheck()
else:
    code_search = None

# === Agent Creation Functions ===

def create_planner_agent() -> Agent:
    """Create strategic planning agent."""
    tools = [search_tool]
    if code_search:
        tools.extend([code_search, list_dir, git_status])
        
    return Agent(
        name="Strategic Planner",
        model=MODELS["planner"],
        tools=tools,
        memory=memory if config.enable_memory else None,
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

def create_architect_agent() -> Agent:
    """Create system architect agent."""
    tools = [search_tool]
    if CUSTOM_TOOLS_AVAILABLE:
        tools.extend([code_search, read_file, list_dir])
        
    return Agent(
        name="System Architect",
        model=MODELS["architect"],
        tools=tools,
        memory=memory if config.enable_memory else None,
        system_prompt="""You are a system architect focused on:
        - Design patterns and best practices
        - Module boundaries and interfaces
        - Performance and scalability
        - Security architecture
        - Technology selection
        Provide clear architectural decisions with rationale.""",
        reasoning=True,
    )

def create_coder_agent(model_key: str, name: str, prompt: str) -> Agent:
    """Create a code generation agent."""
    tools = [search_tool]
    if CUSTOM_TOOLS_AVAILABLE:
        tools.extend([code_search, read_file])
        if config.enable_writes:
            tools.append(write_file)
        tools.extend([run_tests])
        
    return Agent(
        name=name,
        model=MODELS[model_key],
        tools=tools,
        memory=memory if config.enable_memory else None,
        system_prompt=prompt,
        reasoning=True,
    )

def create_review_agent(model_key: str, name: str, prompt: str) -> Agent:
    """Create a review/analysis agent."""
    tools = []
    if CUSTOM_TOOLS_AVAILABLE:
        tools.extend([read_file, run_tests, run_typecheck])
        
    return Agent(
        name=name,
        model=MODELS[model_key],
        tools=tools,
        memory=memory if config.enable_memory else None,
        system_prompt=prompt,
        reasoning=True,
    )

# === Create All Agents ===

# Planning & Architecture
planner = create_planner_agent()
architect = create_architect_agent()

# Code Generation
coder_primary = create_coder_agent(
    "coder_primary",
    "Primary Coder",
    """You are an expert software engineer using Qwen-2.5-Coder.
    Focus on: Clean code, error handling, minimal diff, TDD, performance."""
)

coder_secondary = create_coder_agent(
    "coder_secondary",
    "Alternative Coder",
    """You are a creative problem solver using DeepSeek-Coder.
    Provide alternative implementations with different approaches."""
)

coder_fast = create_coder_agent(
    "coder_fast",
    "Fast Prototyper",
    """You are a rapid prototyping specialist.
    Quickly produce working POCs and minimal implementations."""
)

# Quality Assurance
critic = create_review_agent(
    "critic",
    "Code Critic",
    """You are a thorough code reviewer. Analyze for:
    logic errors, code quality, performance, security, test coverage.
    Output structured feedback with severity levels."""
)

security_analyst = create_review_agent(
    "security",
    "Security Analyst",
    """You are a security specialist. Check for:
    auth flaws, injection, data exposure, crypto weaknesses.
    Rate findings by CVSS severity."""
)

performance_analyst = create_review_agent(
    "performance",
    "Performance Analyst",
    """You are a performance optimization expert.
    Analyze complexity, efficiency, caching, concurrency.
    Suggest concrete optimizations with benchmarks."""
)

# Decision Making
judge = Agent(
    name="Technical Judge",
    model=MODELS["judge"],
    memory=memory if config.enable_memory else None,
    system_prompt="""You are the final arbiter using deep reasoning.
    Compare solutions, identify best practices, make decisions.
    Always provide actionable next steps.""",
    reasoning=True,
)

evaluator = create_review_agent(
    "evaluator",
    "Quality Evaluator",
    """You are the quality gatekeeper.
    Evaluate against requirements, standards, coverage, performance.
    Provide PASS/FAIL with detailed scoring."""
)

# Support
researcher = Agent(
    name="Technical Researcher",
    model=MODELS["researcher"],
    tools=[search_tool, code_search] if code_search else [search_tool],
    memory=memory if config.enable_memory else None,
    system_prompt="""You are a research specialist.
    Find best practices, research docs, analyze implementations.
    Cite all sources with links.""",
)

documenter = create_coder_agent(
    "documenter",
    "Documentation Expert",
    """You are a technical writer.
    Create clear API docs, guides, READMEs, comments.
    Follow docs-as-code principles."""
)

tester = create_coder_agent(
    "tester",
    "Test Engineer",
    """You are a test automation expert.
    Create comprehensive unit, integration, property tests.
    Aim for >90% coverage."""
)

# === Team Compositions ===

# Only create teams if feature is enabled
if config.enable_teams:
    fast_team = Team(
        name="Fast Team",
        agents=[coder_fast, critic],
        judge=judge,
        description="Quick turnaround for simple tasks",
    )
    
    standard_team = Team(
        name="Standard Team",
        agents=[planner, coder_primary, critic, tester],
        judge=judge,
        description="Balanced team for most development tasks",
    )
    
    advanced_team = Team(
        name="Advanced Team",
        agents=[planner, coder_primary, coder_secondary, critic, security_analyst],
        judge=judge,
        description="Multiple approaches with security review",
    )
    
    genesis_team = Team(
        name="GENESIS Team",
        agents=[
            planner, architect, coder_primary, coder_secondary,
            critic, security_analyst, performance_analyst,
            tester, documenter,
        ],
        judge=judge,
        description="Complete team for mission-critical features",
    )
    
    research_team = Team(
        name="Research Team",
        agents=[researcher, architect, coder_fast],
        judge=evaluator,
        description="Exploration and proof of concepts",
    )
else:
    # Teams disabled
    fast_team = None
    standard_team = None
    advanced_team = None
    genesis_team = None
    research_team = None

# === Create FastAPI Application ===

# Build agents dictionary
agents_dict = {
    "planner": planner,
    "architect": architect,
    "coder_primary": coder_primary,
    "coder_secondary": coder_secondary,
    "coder_fast": coder_fast,
    "critic": critic,
    "security": security_analyst,
    "performance": performance_analyst,
    "judge": judge,
    "evaluator": evaluator,
    "researcher": researcher,
    "documenter": documenter,
    "tester": tester,
}

# Add teams if enabled
if config.enable_teams:
    agents_dict.update({
        "fast_team": fast_team,
        "standard_team": standard_team,
        "advanced_team": advanced_team,
        "genesis_team": genesis_team,
        "research_team": research_team,
    })

app: FastAPI = create_fastapi_app(
    title="Sophia Intel AI - Agno 1.8.1",
    description="Multi-agent orchestration with centralized configuration",
    version="2.1.0",
    agents=agents_dict,
)

# === Custom Endpoints ===

@app.get("/health")
def health_check():
    """Health check with configuration status."""
    validation = {
        "gateway": bool(config.openai_api_key or config.portkey_api_key),
        "llm_provider": any([
            config.openrouter_api_key,
            config.anthropic_api_key,
            config.openai_native_api_key,
            config.groq_api_key,
        ]),
        "custom_tools": CUSTOM_TOOLS_AVAILABLE,
        "teams_enabled": config.enable_teams,
        "memory_enabled": config.enable_memory,
        "writes_enabled": config.enable_writes,
    }
    
    return {
        "status": "healthy" if validation["gateway"] else "degraded",
        "version": "2.1.0",
        "configuration": validation,
        "agents_available": len([a for a in agents_dict.values() if a is not None]),
        "teams_configured": 5 if config.enable_teams else 0,
        "environment": "production" if not config.local_dev_mode else "development",
    }

@app.get("/config/status")
def config_status():
    """Get configuration status."""
    return {
        "env_source": "pulumi_esc" if os.getenv("USE_PULUMI_ESC") == "true" else "env_file",
        "gateway_configured": bool(config.openai_api_key),
        "providers_configured": {
            "openrouter": bool(config.openrouter_api_key),
            "anthropic": bool(config.anthropic_api_key),
            "openai": bool(config.openai_native_api_key),
            "groq": bool(config.groq_api_key),
            "together": bool(config.together_api_key),
            "deepseek": bool(config.deepseek_api_key),
        },
        "features": {
            "streaming": config.enable_streaming,
            "memory": config.enable_memory,
            "teams": config.enable_teams,
            "evaluation_gates": config.enable_evaluation_gates,
            "writes": config.enable_writes,
        },
        "limits": {
            "daily_budget_usd": config.daily_budget_usd,
            "max_tokens": config.max_tokens_per_request,
            "max_requests_per_minute": config.max_requests_per_minute,
        },
    }

@app.get("/models")
def list_models():
    """List all configured models."""
    return MODELS

@app.post("/smart_route")
async def smart_route(task: Dict[str, Any]):
    """Intelligently route tasks to appropriate team."""
    if not config.enable_teams:
        raise HTTPException(status_code=503, detail="Teams feature is disabled")
        
    description = task.get("description", "")
    complexity = task.get("complexity", "medium")
    
    # Routing logic
    if complexity == "low" or "hotfix" in description.lower():
        team_name = "fast_team"
    elif complexity == "high" or "architecture" in description.lower():
        team_name = "genesis_team"
    elif "research" in description.lower():
        team_name = "research_team"
    elif "security" in description.lower():
        team_name = "advanced_team"
    else:
        team_name = "standard_team"
    
    return {
        "recommended_team": team_name,
        "reasoning": f"Based on complexity '{complexity}' and task description",
        "configuration": {
            "max_tokens": config.max_tokens_per_request,
            "timeout": config.timeout_seconds,
        },
    }

if __name__ == "__main__":
    import uvicorn
    
    print(f"\n🚀 Starting Agno Playground on port {config.playground_port}")
    print(f"📝 API Docs: http://127.0.0.1:{config.playground_port}/docs")
    print(f"🎨 Connect Agent UI to: http://127.0.0.1:{config.playground_port}")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=config.playground_port,
        reload=config.local_dev_mode
    )