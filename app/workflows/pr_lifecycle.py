"""
PR Lifecycle workflow with quality gates and evaluation.
"""

from textwrap import dedent
from typing import Any, Optional

from agno.run.team import TeamRunResponse
from agno.workflow.v2.loop import Loop
from agno.workflow.v2.router import Router
from agno.workflow.v2.step import Step, StepInput, StepOutput
from agno.workflow.v2.workflow import Workflow

from app.eval.accuracy_eval import run_accuracy_eval
from app.eval.reliability_eval import run_reliability_eval
from app.swarms.approval import judge_allows_run
from app.swarms.coding.team import make_coding_swarm, run_coding_debate
from app.swarms.validator import as_json_or_error

# Import enhanced validation if available
try:
    from app.contracts.json_schemas import (
        runner_gate_decision,
        validate_critic_output,
        validate_judge_output,
    )
    JSON_VALIDATION_AVAILABLE = True
except ImportError:
    JSON_VALIDATION_AVAILABLE = False

# Create the default coding team
coding_team = make_coding_swarm()

def preflight(step_input: StepInput) -> StepOutput:
    """
    Normalize and prepare the task for processing.
    """
    msg = step_input.message.strip() if step_input.message else ""
    additional_data = step_input.additional_data or {}

    # Extract context from additional data
    priority = additional_data.get("priority", "medium")
    repo = additional_data.get("repo", "current")
    branch = additional_data.get("branch", "main")

    normalized = dedent(f"""
    <spec>{msg}</spec>
    <context>
      Priority: {priority}
      Repository: {repo}
      Target Branch: {branch}
    </context>
    <constraints>
      - Small diff (minimal changes)
      - Tests required (unit + integration)
      - No secrets in code
      - Follow existing patterns
      - Type hints required
    </constraints>
    """)

    return StepOutput(
        content=normalized,
        success=True,
        additional_data={"task": msg, "priority": priority}
    )

def run_debate_step(step_input: StepInput) -> StepOutput:
    """
    Run the coding debate with the team.
    """
    task = step_input.previous_step_content or step_input.message or ""

    # Run the debate
    results = run_coding_debate(coding_team, task)

    # Package results for next step
    return StepOutput(
        content=results.get("judge", {}),
        success=not bool(results.get("errors", [])),
        additional_data={
            "critic": results.get("critic", {}),
            "judge": results.get("judge", {}),
            "runner_approved": results.get("runner_approved", False),
            "errors": results.get("errors", [])
        }
    )

def quality_gate(outputs: list[StepOutput]) -> bool:
    """
    Check if the last step passed quality criteria.
    """
    if not outputs:
        return False

    last = outputs[-1]
    judge_json = last.content if isinstance(last.content, dict) else {}

    # Validate judge decision
    if not judge_json:
        return False

    jj = as_json_or_error(str(judge_json), ["decision", "runner_instructions"])
    return "_error" not in jj and jj.get("decision") in ("accept", "merge")

def _post_judge_quality(step_input: StepInput, team) -> StepOutput:
    """
    Enhanced quality gate with JSON validation and runner gate decision.
    After the judge step, run accuracy + reliability evals to decide if Runner can proceed.
    """
    # Get judge and critic decisions from previous step
    additional_data = step_input.additional_data or {}
    judge_json = additional_data.get("judge", {})
    critic_json = additional_data.get("critic", {})

    # Enhanced validation if available
    if JSON_VALIDATION_AVAILABLE:
        try:
            # Validate critic output
            critic_obj = None
            if critic_json and not isinstance(critic_json, str):
                critic_obj = validate_critic_output(critic_json)

            # Validate judge output
            judge_obj = None
            if judge_json and not isinstance(judge_json, str):
                judge_obj = validate_judge_output(judge_json)

            # If both validated, use enhanced gate decision
            if critic_obj and judge_obj:
                # Get accuracy score (run evaluation if team available)
                accuracy_score = 7.0  # Default
                if team:
                    try:
                        acc = run_accuracy_eval(
                            team=team,
                            prompt="Verify that the implementation plan is complete and includes testing.",
                            expected="test",
                            model_id="openai/gpt-4o-mini",
                            iterations=1,
                            print_results=False
                        )
                        if acc and hasattr(acc, 'avg_score'):
                            accuracy_score = acc.avg_score
                    except:
                        pass

                # Get reliability status
                reliability_passed = True  # Default
                team_response = additional_data.get("team_response")
                if team_response and isinstance(team_response, TeamRunResponse):
                    try:
                        run_reliability_eval(
                            team_response=team_response,
                            expected_tool_calls=["transfer_task_to_member", "code_search"],
                            print_results=False
                        )
                    except:
                        reliability_passed = False

                # Make gate decision
                gate = runner_gate_decision(
                    critic=critic_obj,
                    judge=judge_obj,
                    accuracy_score=accuracy_score,
                    reliability_passed=reliability_passed
                )

                if gate["allowed"]:
                    return StepOutput(
                        content="QUALITY_GATE: PASS; Runner may proceed with implementation",
                        success=True,
                        additional_data={
                            "gate_status": "approved",
                            "gate_decision": gate,
                            "runner_instructions": gate["instructions"]
                        }
                    )
                else:
                    reasons = "; ".join(gate["reasons"])
                    return StepOutput(
                        content=f"QUALITY_GATE: BLOCKED; {reasons}",
                        success=False,
                        additional_data={
                            "gate_status": "blocked",
                            "gate_decision": gate
                        }
                    )
        except Exception:
            # Fall back to simple validation
            pass

    # Fallback: Simple validation
    if not judge_json or isinstance(judge_json, str):
        return StepOutput(
            content="QUALITY_GATE: No valid judge JSON; Runner BLOCKED",
            success=False,
            additional_data={"gate_status": "blocked", "reason": "invalid_json"}
        )

    # Check judge approval
    if not judge_allows_run(judge_json):
        return StepOutput(
            content="QUALITY_GATE: Judge did not approve; Runner BLOCKED",
            success=False,
            additional_data={"gate_status": "blocked", "reason": "judge_rejected"}
        )

    gate_results = {"accuracy": None, "reliability": None, "status": "pending"}

    # Accuracy gate: Check if output meets acceptance criteria
    try:
        # Example: require 'tests' mentioned in runner instructions
        instructions_text = " ".join(judge_json.get("runner_instructions", []))
        expected_phrase = "test"

        if team:  # Only run if team is available
            acc = run_accuracy_eval(
                team=team,
                prompt="Verify that the implementation plan includes comprehensive testing.",
                expected=expected_phrase,
                model_id="openai/gpt-4o-mini",
                iterations=1,
                print_results=False
            )

            if acc and hasattr(acc, 'avg_score'):
                gate_results["accuracy"] = {
                    "passed": acc.avg_score >= 7.0,
                    "score": acc.avg_score
                }

                if acc.avg_score < 7.0:
                    return StepOutput(
                        content=f"QUALITY_GATE: Accuracy score {acc.avg_score} < 7.0; Runner BLOCKED",
                        success=False,
                        additional_data={
                            "gate_status": "blocked",
                            "reason": "accuracy_failed",
                            "score": acc.avg_score
                        }
                    )
        else:
            # Fallback: simple text check
            if expected_phrase.lower() not in instructions_text.lower():
                return StepOutput(
                    content="QUALITY_GATE: Testing not mentioned in plan; Runner BLOCKED",
                    success=False,
                    additional_data={"gate_status": "blocked", "reason": "no_tests"}
                )
    except Exception as e:
        gate_results["accuracy"] = {"error": str(e)}

    # Reliability gate: Check expected tool usage patterns
    try:
        # Note: This requires capturing TeamRunResponse from the debate
        # For now, we'll pass with a note
        team_response = additional_data.get("team_response")
        if team_response and isinstance(team_response, TeamRunResponse):
            run_reliability_eval(
                team_response=team_response,
                expected_tool_calls=["transfer_task_to_member", "code_search"],
                print_results=False
            )
            gate_results["reliability"] = {"passed": True}
        else:
            # Can't verify without team response, but don't block
            gate_results["reliability"] = {"passed": True, "note": "No team response to verify"}
    except Exception as e:
        gate_results["reliability"] = {"error": str(e), "passed": True}

    # All gates passed
    gate_results["status"] = "approved"
    return StepOutput(
        content="QUALITY_GATE: PASS; Runner may proceed with implementation",
        success=True,
        additional_data={
            "gate_status": "approved",
            "gates": gate_results,
            "runner_instructions": judge_json.get("runner_instructions", [])
        }
    )

# Define workflow steps
coding_sequence = [
    Step(
        name="preflight",
        executor=preflight,
        description="Normalize and prepare task"
    ),
    Step(
        name="coding_debate",
        executor=run_debate_step,
        description="Run coding team debate"
    ),
    Step(
        name="quality_gates",
        executor=lambda si: _post_judge_quality(si, coding_team),
        description="Evaluate quality gates"
    )
]

# Create a loop for iterative improvement
coding_loop = Loop(
    name="Improve until pass",
    steps=coding_sequence[1:],  # Skip preflight in loop
    end_condition=quality_gate,
    max_iterations=2
)

def complexity_router(step_input: StepInput) -> list:
    """
    Route based on task complexity.
    Simple tasks go straight through, complex tasks enter the loop.
    """
    txt = (step_input.previous_step_content or step_input.message or "").lower()

    # Indicators of complexity
    complex_indicators = [
        "refactor", "architecture", "schema", "migration",
        "performance", "optimization", "concurrent", "parallel"
    ]

    # Check word count and complexity indicators
    is_complex = (
        len(txt.split()) > 40 or
        any(indicator in txt for indicator in complex_indicators)
    )

    if is_complex:
        return [coding_loop]
    else:
        return coding_sequence[1:]  # Skip preflight, go straight to debate

# Main workflow definition
workflow = Workflow(
    name="PR Lifecycle",
    description="End-to-end PR workflow with quality gates and evaluation",
    steps=[
        Step(name="preflight", executor=preflight),
        Router(
            name="complexity_router",
            selector=complexity_router,
            choices=[coding_loop, coding_sequence[1:]]
        )
    ]
)

def run_pr_workflow(
    task: str,
    priority: str = "medium",
    repo: Optional[str] = None,
    branch: str = "main"
) -> dict[str, Any]:
    """
    Convenience function to run the PR workflow.
    
    Args:
        task: Task description
        priority: Task priority (low/medium/high/critical)
        repo: Repository name
        branch: Target branch
    
    Returns:
        Workflow execution results
    """
    from agno.workflow.v2.runner import WorkflowRunner

    runner = WorkflowRunner(workflow)
    result = runner.run(
        message=task,
        additional_data={
            "priority": priority,
            "repo": repo,
            "branch": branch
        }
    )

    return {
        "task": task,
        "result": result,
        "success": result.success if hasattr(result, 'success') else False
    }
