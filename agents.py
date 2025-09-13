"""
Agent registry and swarm patterns for the unified Sophia CLI.
Models/providers are placeholders; direct provider calls are out-of-scope for now.
"""
from __future__ import annotations

from typing import Dict, List


def get_agent_registry() -> Dict[str, dict]:
    # Conservative, real-ish models could be wired later via OpenRouter/Portkey.
    return {
        "architect": {
            "model": "claude-3-opus",
            "temperature": 0.3,
            "role": "Design system architecture and break down complex problems",
            "capabilities": ["system_design", "api_design", "database_schema", "dependency_analysis"],
            "provider": "anthropic",
        },
        "coder": {
            "model": "deepseek-coder-33b",
            "temperature": 0.2,
            "role": "Write production-quality code with proper error handling",
            "capabilities": ["code_generation", "refactoring", "optimization", "documentation"],
            "provider": "deepseek",
        },
        "reviewer": {
            "model": "gpt-4-turbo",
            "temperature": 0.1,
            "role": "Review code for bugs, security issues, and best practices",
            "capabilities": ["bug_detection", "security_audit", "performance_review", "style_check"],
            "provider": "openai",
        },
        "tester": {
            "model": "gpt-4",
            "temperature": 0.2,
            "role": "Write comprehensive test suites",
            "capabilities": ["unit_tests", "integration_tests", "edge_cases", "mocking"],
            "provider": "openai",
        },
        "documenter": {
            "model": "claude-3-sonnet",
            "temperature": 0.4,
            "role": "Create clear documentation and API references",
            "capabilities": ["docstrings", "readme_files", "api_docs", "tutorials"],
            "provider": "anthropic",
        },
    }


def get_swarm_patterns() -> Dict[str, List[str]]:
    return {
        "simple_task": ["coder", "reviewer"],
        "complex_feature": ["architect", "coder", "reviewer", "tester"],
        "refactoring": ["architect", "coder", "reviewer", "documenter"],
        "debugging": ["reviewer", "coder", "tester"],
        "documentation": ["documenter", "reviewer"],
    }

