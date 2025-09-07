from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from app.mcp.clients.stdio_client import detect_stdio_mcp
from app.swarms.coding.patch_proposal import propose_patches
from app.swarms.core.swarm_integration import get_artemis_orchestrator


def cmd_smoke(args) -> int:
    client = detect_stdio_mcp(Path.cwd())
    if not client:
        print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
        return 2

    print("- initialize")
    print(json.dumps(client.initialize(), indent=2))

    print("- fs.list .")
    print(json.dumps(client.fs_list("."), indent=2)[:400] + "...")

    print("- git.status")
    print(json.dumps(client.git_status(), indent=2))

    print("- memory.add + search")
    topic = "Artemis Smoke Test"
    client.memory_add(
        topic=topic,
        content="artemis-run smoke test",
        source="artemis-run",
        tags=["repo", "artemis", "smoke"],
        memory_type="episodic",
    )
    print(json.dumps(client.memory_search("smoke test", limit=3), indent=2))

    print("- repo.index (cap at 20KB per file)")
    print(json.dumps(client.repo_index(root=".", max_bytes_per_file=20_000), indent=2))
    return 0


def _collect_files(paths: List[str]) -> List[Path]:
    files: List[Path] = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            files.extend([f for f in pp.rglob("*") if f.is_file()])
        elif pp.is_file():
            files.append(pp)
    # dedupe
    seen = set()
    uniq: List[Path] = []
    for f in files:
        try:
            rf = f.resolve()
        except Exception:
            rf = f
        if rf not in seen:
            uniq.append(f)
            seen.add(rf)
    return uniq


def cmd_analyze(args) -> int:
    client = detect_stdio_mcp(Path.cwd())
    if not client:
        print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
        return 2

    targets = args.paths or ["."]
    files = _collect_files(targets)[: args.max_files]
    summary = {
        "files_considered": len(files),
        "strategy": "dry-run static scan (placeholder)",
        "proposal": "Suggest minimal diffs and safe refactors; preview only.",
    }
    client.memory_add(
        topic="Artemis Analyze Plan",
        content=json.dumps(summary),
        source="artemis-run",
        tags=["repo", "artemis", "analyze"],
        memory_type="procedural",
    )
    print(json.dumps(summary, indent=2))
    return 0


def cmd_apply(args) -> int:
    client = detect_stdio_mcp(Path.cwd())
    if not client:
        print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
        return 2

    path = args.path
    content = args.content
    if not path or content is None:
        print("ERROR: --path and --content required")
        return 2

    if not args.apply:
        print(f"[dry-run] Would write to {path} with {len(content.encode('utf-8'))} bytes.")
        return 0

    res = client.fs_write(path, content)
    client.memory_add(
        topic="Artemis Apply",
        content=f"Wrote {res.get('bytes', 0)} bytes to {res.get('path')}",
        source="artemis-run",
        tags=["repo", "artemis", "apply"],
        memory_type="episodic",
    )
    print(json.dumps(res, indent=2))
    print(json.dumps(client.git_status(), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="artemis-run", description="Artemis local runner (stdio MCP)")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("smoke", help="Run end-to-end local smoke test")
    sp.set_defaults(func=cmd_smoke)

    sp = sub.add_parser("analyze", help="Analyze target files (dry-run)")
    sp.add_argument("paths", nargs="*", help="Files or directories")
    sp.add_argument("--max-files", type=int, default=200, dest="max_files")
    sp.set_defaults(func=cmd_analyze)

    sp = sub.add_parser("apply", help="Apply a simple content write via MCP fs.write")
    sp.add_argument("--path", required=True, help="Path to write within repo")
    sp.add_argument("--content", required=True, help="Content to write")
    sp.add_argument("--apply", action="store_true", help="Confirm apply (otherwise dry-run)")
    sp.set_defaults(func=cmd_apply)

    sp = sub.add_parser(
        "propose", help="Generate minimal patch proposals and store previews in memory"
    )
    sp.add_argument("paths", nargs="*", default=["."], help="Files or directories")
    sp.add_argument("--max-files", type=int, default=20, dest="max_files")

    def _do_propose(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        results = propose_patches(client, args.paths, args.max_files)
        # Store each proposal (summary) in memory
        stored = 0
        for r in results:
            if r.get("has_changes"):
                preview = (r.get("diff") or "")[:5000]
                client.memory_add(
                    topic=f"Patch Proposal: {r['path']}",
                    content=preview,
                    source="artemis-run",
                    tags=["repo", "artemis", "patch-proposal"],
                    memory_type="semantic",
                )
                stored += 1
        print(json.dumps({"proposals": len(results), "stored": stored}, indent=2))
        return 0

    sp.set_defaults(func=_do_propose)

    sp = sub.add_parser(
        "scout", help="Run the Artemis Repository Scout swarm (requires manual LLM env vars)"
    )
    sp.add_argument(
        "--task",
        default="Scout this repository: map integrations, hotspots, and propose improvements.",
    )

    def _do_scout(args):
        # This path requires network + LLM env; we provide a friendly message if not set
        try:
            orchestrator = get_artemis_orchestrator()
            import asyncio

            result = asyncio.get_event_loop().run_until_complete(
                orchestrator.execute_swarm(
                    content=args.task, swarm_type="repository_scout", context={}
                )
            )
            print(
                json.dumps(
                    {
                        "success": result.success,
                        "confidence": result.confidence,
                        "summary": result.final_output[:2000],
                    },
                    indent=2,
                )
            )
            return 0
        except Exception as e:
            print(f"ERROR running scout swarm: {e}")
            print(
                "Ensure LLM_* env vars are set (per-role or global) and network access is available."
            )
            return 2

    sp.set_defaults(func=_do_scout)

    sp = sub.add_parser("swarm", help="Run a micro-swarm by type with mode leader|swarm")
    sp.add_argument(
        "--type",
        required=True,
        choices=["repository_scout", "code_planning", "code_review_micro", "security_micro"],
    )
    sp.add_argument("--mode", default="swarm", choices=["leader", "swarm"])
    sp.add_argument("--task", default="Run micro-swarm task")

    def _do_swarm(args):
        try:
            if args.mode == "leader":
                # Build a leader-only config for the requested swarm
                from app.swarms.artemis.technical_agents import (
                    AgentProfile,
                    AgentRole,
                    ArtemisSwarmFactory,
                    CoordinationPattern,
                    MemoryDomain,
                    SwarmConfig,
                )

                # Map to the strategists defined in factory
                if args.type == "repository_scout":
                    leader = AgentProfile(
                        role=AgentRole.STRATEGIST,
                        name="Integration Stalker (Leader)",
                        description="Leader-only run.",
                        model_preferences=["openrouter/sonoma-sky-alpha"],
                        specializations=["integration_analysis"],
                        reasoning_style="Leader-only synthesis.",
                        max_tokens=2000000,
                        temperature=0.1,
                    )
                elif args.type == "code_planning":
                    leader = AgentProfile(
                        role=AgentRole.STRATEGIST,
                        name="Planning Leader",
                        description="Leader-only run.",
                        model_preferences=["qwen/qwen3-30b-a3b-thinking-2507"],
                        specializations=["planning"],
                        reasoning_style="Leader-only planning.",
                        max_tokens=24000,
                        temperature=0.1,
                    )
                elif args.type == "code_review_micro":
                    leader = AgentProfile(
                        role=AgentRole.STRATEGIST,
                        name="Review Leader",
                        description="Leader-only run.",
                        model_preferences=["openrouter/sonoma-sky-alpha"],
                        specializations=["synthesis"],
                        reasoning_style="Leader-only review synthesis.",
                        max_tokens=2000000,
                        temperature=0.1,
                    )
                else:  # security_micro
                    leader = AgentProfile(
                        role=AgentRole.STRATEGIST,
                        name="Security Leader",
                        description="Leader-only run.",
                        model_preferences=["openrouter/sonoma-sky-alpha"],
                        specializations=["risk_posture"],
                        reasoning_style="Leader-only security synthesis.",
                        max_tokens=2000000,
                        temperature=0.1,
                    )
                cfg = SwarmConfig(
                    name=f"Leader-only {args.type}",
                    domain=MemoryDomain.ARTEMIS,
                    coordination_pattern=CoordinationPattern.SEQUENTIAL,
                    agents=[leader],
                    max_iterations=1,
                    consensus_threshold=0.0,
                    timeout_seconds=180,
                    enable_memory_integration=True,
                )
                from app.swarms.core.micro_swarm_base import MicroSwarmCoordinator

                coord = MicroSwarmCoordinator(cfg)
                import asyncio

                res = asyncio.get_event_loop().run_until_complete(
                    coord.execute(task=args.task, context={"mode": "leader"})
                )
            else:
                orchestrator = get_artemis_orchestrator()
                import asyncio

                res = asyncio.get_event_loop().run_until_complete(
                    orchestrator.execute_swarm(content=args.task, swarm_type=args.type, context={})
                )
            output = {
                "success": getattr(res, "success", False),
                "confidence": getattr(res, "confidence", 0.0),
                "summary": getattr(res, "final_output", "")[:2000],
            }
            # Leader mode enhancement: suggest full swarm if low confidence
            if args.mode == "leader" and output["confidence"] < 0.7:
                output["recommendation"] = (
                    "Low confidence from leader-only run; consider full swarm execution."
                )
            print(json.dumps(output, indent=2))
            return 0
        except Exception as e:
            print(f"ERROR running swarm: {e}")
            print("Ensure LLM_* env vars are set and network access is available.")
            return 2

    sp.set_defaults(func=_do_swarm)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 1
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
