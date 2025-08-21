# tests/test_action_schemas_v42.py
import re
from pathlib import Path

SCHEMAS = Path("ACTION_SCHEMAS.md").read_text(encoding="utf-8")

# Minimal required actions → handler fragments we expect to see somewhere nearby.
REQUIRED = {
    "code.create_file":       r"Handler:\s*`?code-mcp/create_file`?",
    "code.update_file":       r"Handler:\s*`?code-mcp/update_file`?",
    "code.commit_and_push":   r"Handler:\s*`?code-mcp/commit_and_push`?",
    "code.pr_open":           r"Handler:\s*`?sophia-code/pr_open`?",
    "context.store":          r"Handler:\s*`?sophia-context/store`?",
    "context.retrieve":       r"Handler:\s*`?sophia-context/retrieve`?",
    "business.create_task":   r"Handler:\s*`?sophia-business/create_task`?",
    "business.summarize_gong_calls": r"Handler:\s*`?business-mcp/summarize_gong_calls`?",
}

def _section_has_action(action: str) -> bool:
    # action must appear as a code-ish token in the md
    return bool(re.search(rf"(?mi)^\s*`?{re.escape(action)}`?\s*$", SCHEMAS)) or (action in SCHEMAS)

def _schemas_has_handler(pattern: str) -> bool:
    return bool(re.search(pattern, SCHEMAS))

def test_required_actions_registered():
    missing = [a for a in REQUIRED if not _section_has_action(a)]
    assert not missing, f"Missing actions in ACTION_SCHEMAS.md: {missing}"

def test_required_handlers_present():
    missing = [a for a, pat in REQUIRED.items() if not _schemas_has_handler(pat)]
    assert not missing, f"Missing or mismatched handlers for: {missing}"

def test_unified_response_format_present():
    assert "Unified Response Format" in SCHEMAS
    assert '"status": "success|failure|partial|timeout"' in SCHEMAS

