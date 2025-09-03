#!/usr/bin/env python3
"""
CLI tool to run coding debates with different generator pools.
"""

import argparse
import json
import sys

from app.core.ai_logger import logger
from app.swarms.approval import judge_allows_run
from app.swarms.coding.team import make_coding_swarm_pool, run_coding_debate


def main():
    """Main CLI entry point."""
    ap = argparse.ArgumentParser(
        description="Run a coding debate with a generator pool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fast pool for quick iterations
  python -m app.cli.debate --pool fast --task "Add pagination to repo list"
  
  # Heavy pool for complex refactoring
  python -m app.cli.debate --pool heavy --task "Refactor auth system with OAuth2"
  
  # Balanced pool for general tasks
  python -m app.cli.debate --pool balanced --task "Implement caching layer"
        """
    )

    ap.add_argument(
        "--pool",
        choices=["fast", "heavy", "balanced"],
        default="fast",
        help="Generator pool to use (fast=quick, heavy=thorough, balanced=mixed)"
    )

    ap.add_argument(
        "--task",
        required=True,
        help="Task/spec to implement"
    )

    ap.add_argument(
        "--output",
        choices=["json", "text", "both"],
        default="both",
        help="Output format"
    )

    ap.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    args = ap.parse_args()

    # ANSI color codes (disabled if --no-color)
    if args.no_color or not sys.stdout.isatty():
        GREEN = YELLOW = RED = BLUE = RESET = BOLD = ""
    else:
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        BLUE = "\033[94m"
        RESET = "\033[0m"
        BOLD = "\033[1m"

    logger.info(f"{BLUE}{BOLD}🚀 Starting Coding Debate{RESET}")
    logger.info(f"{BLUE}Pool: {args.pool}{RESET}")
    logger.info(f"{BLUE}Task: {args.task}{RESET}")
    logger.info("-" * 60)

    try:
        # Create team with selected pool
        team = make_coding_swarm_pool(args.pool)

        # Run the debate
        logger.info(f"\n{YELLOW}Running debate...{RESET}")
        outcome = run_coding_debate(team, args.task)

        # Display results based on output format
        if args.output in ("text", "both"):
            logger.info(f"\n{BOLD}=== CRITIC REVIEW ==={RESET}")
            critic = outcome.get("critic", {})
            if critic.get("_error"):
                logger.info(f"{RED}Error: {critic.get('_error')}{RESET}")
            else:
                verdict = critic.get("verdict", "unknown")
                color = GREEN if verdict == "pass" else YELLOW
                logger.info(f"Verdict: {color}{verdict}{RESET}")

                findings = critic.get("findings", {})
                if findings:
                    logger.info("Findings:")
                    for category, issues in findings.items():
                        if issues:
                            logger.info(f"  {category}: {len(issues)} issue(s)")

                must_fix = critic.get("must_fix", [])
                if must_fix:
                    logger.info(f"{YELLOW}Must Fix:{RESET}")
                    for fix in must_fix:
                        logger.info(f"  - {fix}")

            logger.info(f"\n{BOLD}=== JUDGE DECISION ==={RESET}")
            judge = outcome.get("judge", {})
            if judge.get("_error"):
                logger.info(f"{RED}Error: {judge.get('_error')}{RESET}")
            else:
                decision = judge.get("decision", "unknown")
                color = GREEN if decision == "accept" else (YELLOW if decision == "merge" else RED)
                logger.info(f"Decision: {color}{decision}{RESET}")

                selected = judge.get("selected")
                if selected:
                    logger.info(f"Selected: {selected}")

                rationale = judge.get("rationale", [])
                if rationale:
                    logger.info("Rationale:")
                    for reason in rationale[:3]:  # Show first 3
                        logger.info(f"  • {reason}")

                instructions = judge.get("runner_instructions", [])
                if instructions:
                    logger.info(f"\n{BOLD}Runner Instructions:{RESET}")
                    for i, instr in enumerate(instructions[:5], 1):  # Show first 5
                        logger.info(f"  {i}. {instr}")

            # Check runner gate
            approved = False
            if isinstance(outcome.get("judge"), dict):
                approved = judge_allows_run(outcome["judge"])

            logger.info(f"\n{BOLD}Runner Gate:{RESET} ", end="")
            if approved:
                logger.info(f"{GREEN}✅ ALLOWED{RESET}")
            else:
                logger.info(f"{RED}🚫 BLOCKED{RESET}")

            # Show errors if any
            errors = outcome.get("errors", [])
            if errors:
                logger.info(f"\n{RED}{BOLD}Errors:{RESET}")
                for error in errors:
                    logger.info(f"  {RED}• {error}{RESET}")

        if args.output in ("json", "both"):
            if args.output == "both":
                logger.info(f"\n{BOLD}=== JSON OUTPUT ==={RESET}")

            # Clean output for JSON serialization
            clean_outcome = {
                "task": args.task,
                "pool": args.pool,
                "critic": outcome.get("critic", {}),
                "judge": outcome.get("judge", {}),
                "runner_approved": outcome.get("runner_approved", False),
                "errors": outcome.get("errors", [])
            }

            logger.info(json.dumps(clean_outcome, indent=2, ensure_ascii=False))

        # Exit code based on success
        sys.exit(0 if outcome.get("runner_approved") else 1)

    except Exception as e:
        logger.info(f"\n{RED}{BOLD}Fatal Error:{RESET} {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
