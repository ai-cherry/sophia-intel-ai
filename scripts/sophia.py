#!/usr/bin/env python3
"""
Sophia CLI
Consistent entry for agents: grok, claude, codex.
Usage examples:
  python3 scripts/sophia.py agent grok code "Create REST API"
"""
import subprocess
import sys
from pathlib import Path
def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] != "agent":
        print("Usage: sophia.py agent {grok|claude|codex} [args...]")
        return 1
    agent = sys.argv[2]
    rest = sys.argv[3:]
    unified = Path(__file__).parent / "unified_ai_agents.py"
    cmd = [sys.executable, str(unified), "--agent", agent] + rest
    return subprocess.call(cmd)
if __name__ == "__main__":
    raise SystemExit(main())
