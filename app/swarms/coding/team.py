from agno import Team
from agno.agent import Agent
from app.swarms.coding.agents import (
    make_lead,
    make_generator,
    make_critic,
    make_judge,
    make_runner,
    create_lead_agent,
    create_coder_a_agent,
    create_coder_b_agent,
    create_critic_agent,
    create_judge_agent
)
from app.tools.code_search import CodeSearch
from app.swarms.validator import as_json_or_error, extract_json_from_markdown
from app.swarms.approval import judge_allows_run
from app.models.router import ROLE_MODELS, agno_chat_model
from app.swarms.coding.pools import POOLS
from typing import List, Optional, Dict, Any

def _build_generators(model_keys: List[str]) -> List[Agent]:
    """Build generator agents from model keys."""
    gens: List[Agent] = []
    for i, key in enumerate(model_keys, start=1):
        name = f"Coder-{i}"
        gens.append(
            make_generator(
                name,
                key,
                tools=[CodeSearch()],
                role_note=f"Implement approach {i} with tests and minimal diff."
            )
        )
    return gens

def _build_generators_from_ids(model_ids: List[str]) -> List[Agent]:
    """
    Build generator agents from explicit OpenRouter model IDs (not ROLE_MODELS keys).
    """
    gens: List[Agent] = []
    for i, mid in enumerate(model_ids, start=1):
        name = f"CoderX-{i}"
        a = Agent(
            name=name,
            role=f"Implement approach {i} with tests; minimal diff.",
            model=agno_chat_model(mid),
            tools=[CodeSearch()],
            markdown=True,
            show_tool_calls=True,
        )
        gens.append(a)
    return gens

def make_coding_swarm(
    concurrent_models: Optional[List[str]] = None,
    include_default_pair: bool = True,
    include_runner: bool = False
) -> Team:
    """
    Create an advanced coding swarm with concurrent generators.
    
    Args:
        concurrent_models: List of ROLE_MODELS keys for generator creation
                          e.g., ["coderA", "coderB", "coderC"]
        include_default_pair: Include the default Coder-A and Coder-B
        include_runner: Include the Runner agent (with write permissions)
    
    Returns:
        Configured Team with concurrent execution capabilities
    """
    lead = make_lead()
    critic = make_critic()
    judge = make_judge()
    
    members = [lead]
    
    # Add default generators if requested
    if include_default_pair:
        members += _build_generators(["coderA", "coderB"])
    
    # Add additional concurrent generators
    if concurrent_models:
        members += _build_generators(concurrent_models)
    
    # Add critic and judge
    members += [critic, judge]
    
    # Optionally add runner (gated by judge approval)
    if include_runner:
        members.append(make_runner())
    
    team = Team(
        name="Coding Swarm",
        mode="coordinate",
        members=members,
        markdown=True,
        show_members_responses=True,
        instructions="""
        Advanced coding swarm with concurrent generation and quality gates.
        
        Workflow:
        1. Lead coordinates parallel proposals from generators
        2. Critic provides structured JSON review
        3. Generators apply fixes if needed
        4. Judge makes final decision with runner instructions
        5. Runner executes only with judge approval
        
        Principles:
        - Quality > Speed
        - Structured JSON outputs
        - Minimal diffs
        - Comprehensive testing
        - Security-first approach
        """
    )
    
    # Set the lead as manager for coordination
    team.set_manager(lead)
    
    return team

def run_coding_debate(team: Team, task: str) -> Dict[str, Any]:
    """
    High-level helper to run a full debate cycle with JSON validation.
    
    Args:
        team: The coding swarm team
        task: The task description or ticket
    
    Returns:
        Dictionary with critic and judge JSON outputs
    """
    results = {"task": task, "critic": {}, "judge": {}, "errors": []}
    
    # Round 1: Prompt generators via the lead
    try:
        team.print_response(
            f"[LEAD] Plan and propose competing patches for:\n{task}",
            stream=False
        )
    except Exception as e:
        results["errors"].append(f"Round 1 error: {str(e)}")
    
    # Round 2: Critic review
    try:
        critic_prompt = "Critic: Return strictly CRITIC_SCHEMA JSON for the proposals."
        critic_response = team.run(critic_prompt)
        critic_out = critic_response.content or ""
        
        # Try to extract JSON from markdown if present
        critic_out = extract_json_from_markdown(critic_out)
        critic_json = as_json_or_error(critic_out, ["verdict", "findings", "must_fix"])
        
        if critic_json.get("_error"):
            # One retry with more explicit prompt
            critic_out = team.run(
                "Critic: Reformat your review as valid JSON only, following CRITIC_SCHEMA exactly."
            ).content or ""
            critic_out = extract_json_from_markdown(critic_out)
            critic_json = as_json_or_error(critic_out, ["verdict", "findings", "must_fix"])
        
        results["critic"] = critic_json
    except Exception as e:
        results["errors"].append(f"Critic error: {str(e)}")
    
    # Round 3: Apply fixes if needed
    if results["critic"].get("verdict") == "revise":
        try:
            must_fix = results["critic"].get("must_fix", [])
            fix_prompt = f"Generators: Apply minimal fixes for: {', '.join(must_fix)}"
            team.print_response(fix_prompt, stream=False)
        except Exception as e:
            results["errors"].append(f"Fix round error: {str(e)}")
    
    # Round 4: Judge decision
    try:
        judge_prompt = """Judge: Return strictly JUDGE_SCHEMA JSON with:
        - decision (accept/merge/reject)
        - runner_instructions (concrete implementation steps)
        - rationale (reasoning for decision)"""
        
        judge_response = team.run(judge_prompt)
        judge_out = judge_response.content or ""
        
        # Extract and validate judge JSON
        judge_out = extract_json_from_markdown(judge_out)
        judge_json = as_json_or_error(
            judge_out,
            ["decision", "runner_instructions", "rationale"]
        )
        
        results["judge"] = judge_json
        
        # Check if runner is approved
        if judge_allows_run(judge_json):
            results["runner_approved"] = True
        else:
            results["runner_approved"] = False
    except Exception as e:
        results["errors"].append(f"Judge error: {str(e)}")
    
    return results

def make_coding_swarm_pool(pool: str = "fast") -> Team:
    """
    Build a Coding Swarm using a predefined model pool (see pools.py).
    Executes generators concurrently under the lead in coordinate mode.
    """
    lead = make_lead()
    critic = make_critic()
    judge = make_judge()

    model_ids = POOLS.get(pool, [])
    if not model_ids:
        raise ValueError(f"Unknown pool '{pool}'. Available: {list(POOLS.keys())}")

    gens = _build_generators_from_ids(model_ids)
    members = [lead, *gens, critic, judge]

    team = Team(
        name=f"Coding Swarm ({pool})",
        mode="coordinate",
        members=members,
        markdown=True,
        show_members_responses=True,
    )
    
    # Set the lead as manager
    team.set_manager(lead)
    
    return team

def create_coding_team() -> Team:
    """
    Legacy function for backward compatibility.
    Creates the original Coding Team configuration.
    """
    # Create all agents using legacy functions
    lead = create_lead_agent()
    coder_a = create_coder_a_agent()
    coder_b = create_coder_b_agent()
    critic = create_critic_agent()
    judge = create_judge_agent()
    
    # Create the team
    team = Team(
        name="Coding Team",
        description="A collaborative team for software development tasks",
        agents=[lead, coder_a, coder_b, critic, judge],
        instructions="""
        This team collaborates on software development tasks following this workflow:
        
        1. The Lead analyzes requirements and creates a plan
        2. Coder-A and Coder-B implement features in parallel or sequence
        3. The Critic reviews all code changes
        4. The Judge makes final decisions on quality and merge readiness
        5. The team iterates based on feedback until the task is complete
        
        Key principles:
        - Code quality over speed
        - Test-driven development when applicable
        - Clear documentation and comments
        - Following project conventions and standards
        - Collaborative problem-solving
        """
    )
    
    # Set the lead as the entry point
    team.set_manager(lead)
    
    return team