from __future__ import annotations
from agno.eval.reliability import ReliabilityEval, ReliabilityResult
from agno.run.team import TeamRunResponse
def run_reliability_eval(
    team_response: TeamRunResponse,
    expected_tool_calls: list[str],
    print_results: bool = True,
) -> ReliabilityResult:
    """
    Asserts the Team produced expected tool calls in a run. Great for
    catching regressions (e.g., code_search should be called; runner shouldn't).
    """
    evaluation = ReliabilityEval(
        team_response=team_response,
        expected_tool_calls=expected_tool_calls,
    )
    result: ReliabilityResult | None = evaluation.run(print_results=print_results)
    if result:
        result.assert_passed()
    return result
