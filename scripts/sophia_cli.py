#!/usr/bin/env python3
"""
Minimal Sophia CLI wrapper for swarm and memory commands.
Bridges Makefile.dev targets to existing unified_ai_agents CLI.
"""
import argparse
import asyncio
import subprocess
import sys
from typing import List


def run_subprocess(cmd: List[str]) -> int:
    return subprocess.call(cmd)


async def swarm_start(task: str, agents: List[str]) -> int:
    """Very lightweight 'swarm': run agents sequentially for now."""
    exit_code = 0
    for agent in agents:
        print(f"\n=== Running agent: {agent} ===\n")
        code = run_subprocess(
            [
                sys.executable,
                "scripts/unified_ai_agents.py",
                "--agent",
                agent,
                "--mode",
                "code",
                "--task",
                task,
            ]
        )
        exit_code = exit_code or code
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(prog="sophia_cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # swarm commands
    swarm = sub.add_parser("swarm", help="Swarm utilities")
    swarm_sub = swarm.add_subparsers(dest="swarm_cmd", required=True)

    s_start = swarm_sub.add_parser("start", help="Start a simple swarm")
    s_start.add_argument("task", help="Task to execute")
    s_start.add_argument(
        "--agents",
        default="grok,claude",
        help="Comma-separated agent list (e.g., grok,claude,codex)",
    )

    swarm_sub.add_parser("status", help="Show swarm status (placeholder)")

    # memory commands (placeholder)
    mem = sub.add_parser("memory", help="Memory utilities")
    mem_sub = mem.add_subparsers(dest="mem_cmd", required=True)
    m_search = mem_sub.add_parser("search", help="Search memory (placeholder)")
    m_search.add_argument("query", help="Search query")

    args = parser.parse_args()

    if args.cmd == "swarm":
        if args.swarm_cmd == "start":
            agents = [a.strip() for a in args.agents.split(",") if a.strip()]
            return asyncio.run(swarm_start(args.task, agents))
        if args.swarm_cmd == "status":
            print("No persistent swarm orchestrator status yet.")
            return 0

    if args.cmd == "memory":
        if args.mem_cmd == "search":
            print("Memory search not yet implemented in this stub CLI.")
            print("Use: python3 scripts/unified_ai_agents.py --whoami for env info")
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
