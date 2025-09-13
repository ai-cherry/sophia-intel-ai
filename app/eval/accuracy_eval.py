from __future__ import annotations
from agno.eval.accuracy import AccuracyEval, AccuracyResult
from agno.models.openai import OpenAIChat
from agno.team import Team
def run_accuracy_eval(
    team: Team,
    prompt: str,
    expected: str,
    model_id: str = "z-ai/glm-4.5-air",
    iterations: int = 1,
    print_results: bool = True,
) -> AccuracyResult:
    """
    Lightweight harness to score a Team's response against an expected output.
    Use sparingly (dev or CI), not on every interactive request.
    """
    eval_model = OpenAIChat(id=model_id)
    evaluation = AccuracyEval(
        model=eval_model,
        team=team,
        input=prompt,
        expected_output=expected,
        num_iterations=iterations,
    )
    result: AccuracyResult | None = evaluation.run(print_results=print_results)
    return result
