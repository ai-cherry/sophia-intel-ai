"""
Tests for workflow evaluation framework.
"""

from unittest.mock import Mock, patch

import pytest
from agno.run.team import TeamRunResponse

from app.eval.accuracy_eval import run_accuracy_eval
from app.eval.reliability_eval import run_reliability_eval
from app.swarms.approval import critic_requires_revision, judge_allows_run
from app.swarms.coding.team import make_coding_swarm, make_coding_swarm_pool
from app.swarms.validator import as_json_or_error, extract_json_from_markdown


def test_accuracy_gate_smoke():
    """Test accuracy evaluation with a mock team."""
    # Create a mock team
    team = Mock()
    team.run = Mock(return_value=Mock(content="tests are included"))

    # Mock the AccuracyEval to avoid actual API calls
    with patch('app.eval.accuracy_eval.AccuracyEval') as MockAccuracyEval:
        mock_eval = Mock()
        mock_eval.run = Mock(return_value=Mock(avg_score=8.5))
        MockAccuracyEval.return_value = mock_eval

        result = run_accuracy_eval(
            team=team,
            prompt="Confirm plan mentions tests explicitly",
            expected="tests",
            model_id="openai/gpt-4o-mini",
            iterations=1,
            print_results=False
        )

        assert result is not None
        assert result.avg_score > 7.0

def test_reliability_gate_smoke():
    """Test reliability evaluation with mock response."""
    # Create a mock TeamRunResponse
    team_response = Mock(spec=TeamRunResponse)
    team_response.tool_calls = ["transfer_task_to_member", "code_search"]

    # Mock the ReliabilityEval
    with patch('app.eval.reliability_eval.ReliabilityEval') as MockReliabilityEval:
        mock_eval = Mock()
        mock_eval.run = Mock(return_value=Mock())
        mock_eval.run.return_value.assert_passed = Mock()
        MockReliabilityEval.return_value = mock_eval

        result = run_reliability_eval(
            team_response=team_response,
            expected_tool_calls=["transfer_task_to_member"],
            print_results=False
        )

        # Verify the eval was created and run
        MockReliabilityEval.assert_called_once()
        mock_eval.run.assert_called_once()

def test_json_validator():
    """Test JSON validation and extraction."""
    # Valid JSON
    valid_json = '{"verdict": "pass", "findings": {}, "must_fix": []}'
    result = as_json_or_error(valid_json, ["verdict", "findings", "must_fix"])
    assert "_error" not in result
    assert result["verdict"] == "pass"

    # Invalid JSON
    invalid_json = "not json at all"
    result = as_json_or_error(invalid_json, ["verdict"])
    assert "_error" in result
    assert result["_error"] == "invalid-json"

    # Missing required fields
    incomplete_json = '{"verdict": "pass"}'
    result = as_json_or_error(incomplete_json, ["verdict", "missing_field"])
    assert "_error" in result
    assert "missing-keys" in result["_error"]

def test_extract_json_from_markdown():
    """Test JSON extraction from markdown blocks."""
    # JSON in markdown
    markdown = """
    Here's the result:
    ```json
    {"key": "value", "number": 42}
    ```
    """
    extracted = extract_json_from_markdown(markdown)
    assert '{"key": "value", "number": 42}' in extracted

    # Plain JSON
    plain = '{"plain": true}'
    extracted = extract_json_from_markdown(plain)
    assert extracted == plain

def test_judge_approval():
    """Test judge approval logic."""
    # Approved case
    judge_json = {
        "decision": "accept",
        "runner_instructions": ["step 1", "step 2"]
    }
    assert judge_allows_run(judge_json) is True

    # Rejected case
    judge_json = {
        "decision": "reject",
        "runner_instructions": ["fix this first"]
    }
    assert judge_allows_run(judge_json) is False

    # No instructions
    judge_json = {
        "decision": "accept",
        "runner_instructions": []
    }
    assert judge_allows_run(judge_json) is False

def test_critic_revision_check():
    """Test critic revision requirement check."""
    # Revision required
    critic_json = {"verdict": "revise"}
    assert critic_requires_revision(critic_json) is True

    # Pass through
    critic_json = {"verdict": "pass"}
    assert critic_requires_revision(critic_json) is False

@pytest.mark.parametrize("pool", ["fast", "heavy", "balanced"])
def test_pool_creation(pool):
    """Test that different pools can be created."""
    with patch('app.swarms.coding.team.make_lead') as mock_lead, \
         patch('app.swarms.coding.team.make_critic') as mock_critic, \
         patch('app.swarms.coding.team.make_judge') as mock_judge, \
         patch('app.swarms.coding.team.Agent') as MockAgent:

        # Mock the agent creation
        mock_lead.return_value = Mock(name="Lead")
        mock_critic.return_value = Mock(name="Critic")
        mock_judge.return_value = Mock(name="Judge")
        MockAgent.return_value = Mock()

        team = make_coding_swarm_pool(pool)
        assert team is not None
        assert f"Coding Swarm ({pool})" in team.name

def test_concurrent_models_configuration():
    """Test concurrent model configuration."""
    with patch('app.swarms.coding.team.make_lead') as mock_lead, \
         patch('app.swarms.coding.team.make_critic') as mock_critic, \
         patch('app.swarms.coding.team.make_judge') as mock_judge, \
         patch('app.swarms.coding.team.make_generator') as mock_gen:

        # Mock agent creation
        mock_lead.return_value = Mock(name="Lead")
        mock_critic.return_value = Mock(name="Critic")
        mock_judge.return_value = Mock(name="Judge")
        mock_gen.return_value = Mock(name="Generator")

        # Create swarm with custom concurrent models
        team = make_coding_swarm(
            concurrent_models=["coderA", "coderB", "coderC"],
            include_default_pair=False,
            include_runner=True
        )

        assert team is not None
        # Verify generator was called for each concurrent model
        assert mock_gen.call_count >= 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
