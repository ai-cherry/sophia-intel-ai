#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
def main():
    cli = Path(__file__).parent / "unified_ai_agents.py"
    cmd = [sys.executable, str(cli), "--agent", "codex"] + sys.argv[1:]
    raise SystemExit(subprocess.call(cmd))
if __name__ == "__main__":
    main()
