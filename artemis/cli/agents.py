"""
Artemis CLI aggregator for local agent entry.
Provides a minimal AgentCLI wrapper to unify agent invocation.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class AgentCLI:
    def __init__(self) -> None:
        self.unified = (
            Path(__file__).resolve().parents[2] / "scripts" / "unified_ai_agents.py"
        )

    def execute(self, agent_name: str, *args: str) -> int:
        cmd = [sys.executable, str(self.unified), "--agent", agent_name] + list(args)
        return subprocess.call(cmd)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m artemis.cli.agents {grok|claude|codex} [args...]")
        return 1
    agent = sys.argv[1]
    rest = sys.argv[2:]
    return AgentCLI().execute(agent, *rest)


if __name__ == "__main__":
    raise SystemExit(main())
