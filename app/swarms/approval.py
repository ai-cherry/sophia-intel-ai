"""
Approval gates for controlling agent actions.
"""

from typing import Dict, Any

def judge_allows_run(judge_json: Dict[str, Any]) -> bool:
    """
    Check if judge decision allows runner to proceed.
    
    Args:
        judge_json: Parsed judge decision JSON
    
    Returns:
        True if runner is approved to execute
    """
    ok = judge_json.get("decision") in ("accept", "merge")
    instr = judge_json.get("runner_instructions") or []
    return ok and len(instr) > 0

def critic_requires_revision(critic_json: Dict[str, Any]) -> bool:
    """
    Check if critic verdict requires revision.
    
    Args:
        critic_json: Parsed critic review JSON
    
    Returns:
        True if revision is required
    """
    return critic_json.get("verdict") == "revise"

def get_risk_level(generator_json: Dict[str, Any]) -> str:
    """
    Extract risk level from generator output.
    
    Args:
        generator_json: Parsed generator plan JSON
    
    Returns:
        Risk level (low/medium/high)
    """
    return generator_json.get("risk_level", "unknown")