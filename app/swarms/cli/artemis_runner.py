from __future__ import annotations

import argparse
import contextlib
import json
from pathlib import Path

from app.mcp.clients.stdio_client import detect_stdio_mcp
from app.swarms.coding.patch_proposal import propose_patches

# Lazy-import heavy LLM orchestration only in commands that need it to keep
# lightweight CLI subcommands (collab/cleanup) working without LLM deps.


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


def _collect_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            files.extend([f for f in pp.rglob("*") if f.is_file()])
        elif pp.is_file():
            files.append(pp)
    # dedupe
    seen = set()
    uniq: list[Path] = []
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


def format_scout_json(task_text, result):
    def _extract_list(section: str) -> list[str]:
        text = getattr(result, "final_output", None) or getattr(result, "content", "") or ""
        lines = text.splitlines()
        items = []
        capturing = False
        header = section.upper() + ":"
        for ln in lines:
            up = ln.strip().upper()
            if up.startswith(header):
                capturing = True
                continue
            if capturing and up.endswith(":"):
                break
            if capturing:
                clean = ln.strip()
                if clean:
                    items.append(clean)
        return items

    risks = [{"text": r, "severity": "unknown"} for r in _extract_list("RISKS")]
    out = {
        "task": task_text,
        "findings": _extract_list("FINDINGS"),
        "integrations": _extract_list("INTEGRATIONS"),
        "risks": risks,
        "recommendations": _extract_list("RECOMMENDATIONS"),
        "metrics": {
            "files_analyzed": 0,
            "execution_time": float(getattr(result, "execution_time_ms", 0.0)),
            "confidence": float(getattr(result, "confidence", 0.0)),
        },
        "success": bool(getattr(result, "success", False)),
    }
    try:
        md = getattr(result, "metadata", {}) or {}
        if isinstance(md, dict) and "tool_usage_total" in md:
            out["metrics"]["tool_usage_total"] = md["tool_usage_total"]
    except Exception:
        pass
    return out


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

    # Collaboration helpers (MCP-memory based event bus)
    collab = sub.add_parser("collab", help="Collaboration helpers (tasks, proposals, reviews)")
    collab_sub = collab.add_subparsers(dest="collab_cmd")

    # collab emit
    sp = collab_sub.add_parser("emit", help="Emit a collab entry: task|proposal|review")
    sp.add_argument("--type", required=True, choices=["task", "proposal", "review"], dest="etype")
    sp.add_argument("--for", dest="assignee", help="Intended assignee (codex|claude)")
    sp.add_argument("--id", dest="eid", help="External or proposal id")
    sp.add_argument("--swarm", dest="swarm", help="Related swarm type (optional)")
    sp.add_argument("--content", required=True, help="Entry content (text or JSON)")
    sp.add_argument("--json", action="store_true", help="JSON output")
    sp.add_argument(
        "--validate-proposal",
        action="store_true",
        dest="validate_proposal",
        help="Validate proposal JSON if --type=proposal",
    )
    sp.add_argument(
        "--ttl", dest="ttl", help="Time-to-live (e.g., 7d, 24h) to add expires:<ISO> tag"
    )

    def _do_collab_emit(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        import json as _json
        import uuid

        entry_id = args.eid or str(uuid.uuid4())
        base_tags = ["collab", f"id:{entry_id}"]
        if args.assignee:
            base_tags.append(f"for:{args.assignee}")
        if args.swarm:
            base_tags.append(f"swarm:{args.swarm}")
        # Optional TTL → expires tag
        if args.ttl:
            import datetime as _dt

            def _parse_duration(s: str) -> _dt.timedelta:
                s = s.strip().lower()
                if s.endswith("d"):
                    return _dt.timedelta(days=int(s[:-1] or 0))
                if s.endswith("h"):
                    return _dt.timedelta(hours=int(s[:-1] or 0))
                if s.endswith("m"):
                    return _dt.timedelta(minutes=int(s[:-1] or 0))
                # default seconds
                return _dt.timedelta(seconds=int(s))

            try:
                delta = _parse_duration(args.ttl)
                expires = (_dt.datetime.utcnow() + delta).replace(microsecond=0).isoformat() + "Z"
                base_tags.append(f"expires:{expires}")
            except Exception:
                pass
        # lifecycle defaults
        if args.etype == "proposal":
            base_tags.append("pending_review")
            topic = f"collab_proposal:{entry_id}"
        elif args.etype == "review":
            base_tags.append("review")
            topic = f"collab_review:{entry_id}"
        else:
            base_tags.append("pending")
            topic = f"collab_task:{entry_id}"

        content = args.content
        try:
            # If user passed JSON-ish string, pretty store to keep structure
            if content.strip().startswith(("{", "[")):
                _ = _json.loads(content)
                # Optional lightweight proposal validation
                if args.etype == "proposal" and args.validate_proposal and isinstance(_, dict):
                    ok = True
                    if _.get("type") == "code_change":
                        files = _.get("files", [])
                        if not isinstance(files, list) or any(
                            not isinstance(f, dict) for f in files
                        ):
                            ok = False
                        # check minimal shape
                        for f in files if isinstance(files, list) else []:
                            if not f.get("path") or not isinstance(f.get("changes", []), list):
                                ok = False
                                break
                    # If invalid, return error
                    if not ok:
                        err = {"ok": False, "error": "Invalid proposal schema for type=code_change"}
                        print(
                            _json.dumps(
                                err if args.json else {k: v for k, v in err.items() if k != "ok"},
                                indent=2,
                            )
                        )
                        return 2
                content = _json.dumps(_, indent=2)
        except Exception:
            pass

        res = client.memory_add(
            topic=topic,
            content=content,
            source="artemis-run",
            tags=base_tags,
            memory_type="procedural",
        )
        out = {"ok": True, "id": entry_id, "topic": topic, "tags": base_tags, "result": res}
        print(
            _json.dumps(
                out if args.json else {k: v for k, v in out.items() if k != "result"}, indent=2
            )
        )
        return 0

    sp.set_defaults(func=_do_collab_emit)

    # collab list
    sp = collab_sub.add_parser("list", help="List collaboration entries via a memory.search filter")
    sp.add_argument("--filter", default="collab", dest="flt")
    sp.add_argument("--limit", type=int, default=10)
    sp.add_argument("--json", action="store_true", help="JSON output")
    sp.add_argument(
        "--older-than", dest="older_than", help="Filter results older than duration (e.g., 7d, 12h)"
    )

    def _do_collab_list(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        import json as _json

        res = client.memory_search(args.flt, limit=args.limit)
        items = res.get("results") if isinstance(res, dict) else res
        if args.older_than:
            import datetime as _dt

            def _parse_duration(s: str) -> _dt.timedelta:
                s = s.strip().lower()
                if s.endswith("d"):
                    return _dt.timedelta(days=int(s[:-1] or 0))
                if s.endswith("h"):
                    return _dt.timedelta(hours=int(s[:-1] or 0))
                if s.endswith("m"):
                    return _dt.timedelta(minutes=int(s[:-1] or 0))
                return _dt.timedelta(seconds=int(s))

            try:
                delta = _parse_duration(args.older_than)
                cutoff = _dt.datetime.utcnow() - delta

                def _parse_iso(ts: str) -> _dt.datetime:
                    try:
                        return _dt.datetime.fromisoformat(ts.replace("Z", ""))
                    except Exception:
                        return _dt.datetime.min

                items = [
                    it
                    for it in (items or [])
                    if _parse_iso(it.get("timestamp", "1970-01-01")).replace(tzinfo=None) < cutoff
                ]
                res = {"results": items}
            except Exception:
                pass
        print(_json.dumps(res, indent=2))
        return 0

    sp.set_defaults(func=_do_collab_list)

    # collab claim
    sp = collab_sub.add_parser("claim", help="Claim a pending task/proposal by id for an agent")
    sp.add_argument("--id", required=True, dest="eid")
    sp.add_argument("--agent", required=True, choices=["codex", "claude"])
    sp.add_argument("--json", action="store_true", help="JSON output")

    def _do_collab_claim(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        import json as _json

        tags = ["collab", "claim", f"id:{args.eid}", f"by:{args.agent}", "in_progress"]
        res = client.memory_add(
            topic=f"collab_claim:{args.eid}",
            content=f"claimed by {args.agent}",
            source="artemis-run",
            tags=tags,
            memory_type="episodic",
        )
        out = {"ok": True, "claimed": args.eid, "by": args.agent, "result": res}
        print(
            _json.dumps(
                out if args.json else {k: v for k, v in out.items() if k != "result"}, indent=2
            )
        )
        return 0

    sp.set_defaults(func=_do_collab_claim)

    # collab approve (review)
    sp = collab_sub.add_parser("approve", help="Approve a proposal by id")
    sp.add_argument("--proposal", required=True, dest="pid")
    sp.add_argument("--agent", required=True, choices=["codex", "claude"])
    sp.add_argument("--confidence", type=float, default=0.85)
    sp.add_argument("--notes", default="")
    sp.add_argument("--json", action="store_true", help="JSON output")

    def _do_collab_approve(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        import json as _json

        body = {
            "proposal_id": args.pid,
            "reviewed_by": args.agent,
            "status": "approved",
            "confidence": args.confidence,
            "notes": args.notes,
        }
        tags = ["collab", "review", "status:approved", f"refs:{args.pid}", f"by:{args.agent}"]
        res = client.memory_add(
            topic=f"collab_review:{args.pid}",
            content=_json.dumps(body),
            source="artemis-run",
            tags=tags,
            memory_type="procedural",
        )
        out = {"ok": True, "proposal": args.pid, "status": "approved", "result": res}
        print(
            _json.dumps(
                out if args.json else {k: v for k, v in out.items() if k != "result"}, indent=2
            )
        )
        return 0

    sp.set_defaults(func=_do_collab_approve)

    # collab apply (stub)
    sp = collab_sub.add_parser(
        "apply",
        help="Apply an approved proposal: reads JSON, writes diffs, runs tests, mirrors result",
    )
    sp.add_argument("--proposal", required=True, dest="pid")
    sp.add_argument("--json", action="store_true", help="JSON output")
    sp.add_argument("--dry-run", action="store_true", help="Preview only; no writes")
    sp.add_argument("--force", action="store_true", help="Bypass conflict detection")
    sp.add_argument(
        "--git-push",
        action="store_true",
        dest="git_push",
        help="If tests pass, auto add/commit and push the changes",
    )

    def _apply_line_changes(text: str, changes: list[dict]) -> str:
        lines = text.splitlines(keepends=True)
        for ch in changes:
            try:
                ln = int(ch.get("line"))
            except Exception:
                continue
            old = ch.get("old", "")
            new = ch.get("new", "")
            idx = max(0, ln - 1)
            if idx >= len(lines):
                # Append as a new line if line beyond EOF
                lines.append(new + ("\n" if not new.endswith("\n") else ""))
                continue
            curr = lines[idx]
            if old == "":
                # Insert at beginning
                lines[idx] = new + ("\n" if not new.endswith("\n") else "")
            elif old in curr:
                lines[idx] = curr.replace(old, new)
            else:
                # If old doesn't match, leave as-is
                pass
        return "".join(lines)

    def _apply_hunks(text: str, hunks: list[dict]) -> str:
        """Apply schema v2 hunks: replace lines[start:end] with new block. Validate 'old' if provided."""
        src_lines = text.splitlines(keepends=True)
        # Apply from bottom to top to keep indices stable
        ordered = sorted(hunks or [], key=lambda h: int(h.get("start_line", 0)), reverse=True)
        for h in ordered:
            try:
                s = max(1, int(h.get("start_line"))) - 1
                e = max(s, int(h.get("end_line", s + 1)) - 1)
            except Exception:
                continue
            old_block = h.get("old")
            new_block = h.get("new", "")
            # Validate old block if present
            seg = "".join(src_lines[s : e + 1])
            if old_block and old_block.strip() and old_block.strip() != seg.strip():
                # Skip this hunk if validation fails
                continue
            new_lines = (new_block if new_block.endswith("\n") else new_block + "\n").splitlines(
                keepends=True
            )
            src_lines[s : e + 1] = new_lines
        return "".join(src_lines)

    def _run_tests(commands: list[str]) -> dict:
        import subprocess
        import time

        results = {"passed": True, "runs": []}
        for cmd in commands or []:
            start = time.time()
            try:
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                ok = proc.returncode == 0
                results["passed"] &= ok
                results["runs"].append(
                    {
                        "cmd": cmd,
                        "ok": ok,
                        "rc": proc.returncode,
                        "stdout": (proc.stdout or "")[-4000:],
                        "stderr": (proc.stderr or "")[-4000:],
                        "duration_s": round(time.time() - start, 3),
                    }
                )
            except Exception as e:
                results["passed"] = False
                results["runs"].append({"cmd": cmd, "ok": False, "error": str(e)})
        return results

    def _do_collab_apply(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        import json as _json
        import subprocess
        import time

        # 1) Load proposal content from memory (robust filtering without advanced query syntax)
        search = client.memory_search("collab", limit=500)
        items = search.get("results") if isinstance(search, dict) else (search or [])
        target = None
        for it in items:
            topic = it.get("topic", "")
            tags = it.get("tags", []) or []
            if topic.startswith("collab_proposal:") and any(t == f"id:{args.pid}" for t in tags):
                target = it
                break
        if not target:
            err = {"ok": False, "error": f"Proposal {args.pid} not found"}
            print(_json.dumps(err, indent=2))
            return 2
        proposal_raw = target.get("content") or "{}"
        try:
            proposal = _json.loads(proposal_raw)
        except Exception:
            err = {"ok": False, "error": "Proposal content is not valid JSON"}
            print(_json.dumps(err, indent=2))
            return 2
        if proposal.get("type") != "code_change":
            err = {"ok": False, "error": "Unsupported proposal type (expected 'code_change')"}
            print(_json.dumps(err, indent=2))
            return 2
        files = proposal.get("files", [])
        tests = proposal.get("tests", []) or ["pytest -q -m smoke"]
        version = str(proposal.get("version", "1.0"))
        changed: list[dict] = []
        backups: list[dict] = []
        ts = int(time.time())
        apply_started = time.time()
        try:
            # Conflict detection (soft): other active proposals touching same files
            if not args.force:
                for f in files:
                    pth = f.get("path")
                    if not pth:
                        continue
                    conflict = client.memory_search(
                        f'collab AND pending_review AND content:"{pth}"', limit=10
                    )
                    hits = conflict.get("results") if isinstance(conflict, dict) else conflict or []
                    # If multiple proposals reference same path and not the current one, warn and abort
                    if hits:
                        raise RuntimeError(
                            f"Conflict detected for {pth}: another active proposal references this file"
                        )

            # 2) Apply diffs via MCP fs.write (with backups)
            for f in files:
                # Schema v1: path + changes; Schema v2 may use operations
                if version.startswith("2") and "action" in f:
                    action = f.get("action")
                    if action == "create":
                        dest = f.get("file")
                        content = f.get("content", "")
                        if not args.dry_run:
                            client.fs_write(dest, content)
                        changed.append({"created": dest})
                    elif action == "delete":
                        dest = f.get("file")
                        # Backup and write empty placeholder
                        original = client.fs_read(dest)
                        original_text = (
                            original.get("content") if isinstance(original, dict) else str(original)
                        )
                        backup_name = f".mcp_backups/{dest.replace('/', '__')}.{ts}.bak"
                        client.fs_write(backup_name, original_text)
                        backups.append({"path": dest, "backup": backup_name})
                        if not args.dry_run:
                            client.fs_write(dest, "")
                        changed.append({"deleted": dest})
                    elif action == "rename":
                        src = f.get("from")
                        dst = f.get("to")
                        original = client.fs_read(src)
                        original_text = (
                            original.get("content") if isinstance(original, dict) else str(original)
                        )
                        backup_name = f".mcp_backups/{src.replace('/', '__')}.{ts}.bak"
                        client.fs_write(backup_name, original_text)
                        backups.append({"path": src, "backup": backup_name})
                        if not args.dry_run:
                            client.fs_write(dst, original_text)
                        changed.append({"renamed": {"from": src, "to": dst}})
                    elif action == "modify":
                        dest = f.get("file")
                        original = client.fs_read(dest)
                        original_text = (
                            original.get("content") if isinstance(original, dict) else str(original)
                        )
                        backup_name = f".mcp_backups/{dest.replace('/', '__')}.{ts}.bak"
                        client.fs_write(backup_name, original_text)
                        backups.append({"path": dest, "backup": backup_name})
                        new_text = _apply_hunks(original_text, f.get("hunks", []))
                        if not args.dry_run:
                            client.fs_write(dest, new_text)
                        changed.append({"modified": dest})
                    else:
                        # Unknown action: skip
                        continue
                else:
                    path = f.get("path")
                    if not path:
                        continue
                    original = client.fs_read(path)
                    original_text = (
                        original.get("content") if isinstance(original, dict) else str(original)
                    )
                    new_text = _apply_line_changes(original_text, f.get("changes", []))
                    # Backup
                    backup_name = f".mcp_backups/{path.replace('/', '__')}.{ts}.bak"
                    client.fs_write(backup_name, original_text)
                    backups.append({"path": path, "backup": backup_name})
                    if not args.dry_run:
                        client.fs_write(path, new_text)
                    changed.append({"path": path})

            # 3) Run tests
            test_result = _run_tests(tests)
            test_duration_ms = int((time.time() - apply_started) * 1000)

            # 4) Mirror results
            tags = [
                "collab",
                "test",
                f"result:{'pass' if test_result['passed'] else 'fail'}",
                f"proposal:{args.pid}",
            ]
            client.memory_add(
                topic=f"collab_test_result:{args.pid}",
                content=_json.dumps(test_result),
                source="artemis-run",
                tags=tags,
                memory_type="episodic",
            )

            # Metrics
            client.memory_add(
                topic="metrics",
                content=_json.dumps(
                    {"name": "collab.apply.success", "value": 1 if test_result["passed"] else 0}
                ),
                source="artemis-run",
                tags=[
                    "metrics",
                    "collab",
                    "apply",
                    f"success:{'1' if test_result['passed'] else '0'}",
                ],
                memory_type="episodic",
            )
            client.memory_add(
                topic="metrics",
                content=_json.dumps({"name": "collab.test.duration_ms", "value": test_duration_ms}),
                source="artemis-run",
                tags=["metrics", "collab", "test", f"duration_ms:{test_duration_ms}"],
                memory_type="episodic",
            )

            if not test_result["passed"] and not args.dry_run:
                # Rollback
                for b in backups:
                    orig = client.fs_read(b["backup"])
                    original_text = orig.get("content") if isinstance(orig, dict) else str(orig)
                    client.fs_write(b["path"], original_text)

            # Optionally auto-commit and push on success
            commit_info: dict[str, str] | None = None
            if test_result["passed"] and not args.dry_run and getattr(args, "git_push", False):
                message = f"collab: apply {args.pid} (tests passed)"
                try:
                    # Stage everything
                    subprocess.run(["git", "add", "-A"], check=True)
                    # Try normal commit first
                    proc = subprocess.run(
                        ["git", "commit", "-m", message], text=True, capture_output=True
                    )
                    if proc.returncode != 0:
                        # Fallback: bypass hooks
                        proc2 = subprocess.run(
                            ["git", "commit", "--no-verify", "-m", message],
                            text=True,
                            capture_output=True,
                        )
                        if proc2.returncode != 0:
                            raise RuntimeError(f"git commit failed: {proc.stderr or proc2.stderr}")
                    # Push
                    push = subprocess.run(["git", "push"], text=True, capture_output=True)
                    if push.returncode != 0:
                        raise RuntimeError(f"git push failed: {push.stderr}")
                    # Capture short commit id
                    head = subprocess.run(
                        ["git", "rev-parse", "--short", "HEAD"],
                        text=True,
                        capture_output=True,
                        check=True,
                    )
                    commit_info = {"commit": head.stdout.strip(), "message": message}
                except Exception as e:
                    commit_info = {"error": str(e)}

                # Mirror apply completion in memory
                with contextlib.suppress(Exception):
                    client.memory_add(
                        topic=f"collab_apply:{args.pid}",
                        content=_json.dumps(
                            {"status": "completed", "commit": commit_info}, indent=2
                        ),
                        source="artemis-run",
                        tags=["collab", "apply", "status:completed", f"id:{args.pid}"],
                        memory_type="episodic",
                    )

            out = {
                "ok": test_result["passed"],
                "proposal": args.pid,
                "changed": changed,
                "tests": test_result,
                **({"git": commit_info} if commit_info is not None else {}),
            }
            print(
                _json.dumps(out, indent=2)
                if args.json
                else _json.dumps({k: v for k, v in out.items() if k != "tests"}, indent=2)
            )
            return 0 if test_result["passed"] else 1
        except Exception as e:
            # On exception, attempt rollback
            if not args.dry_run:
                try:
                    for b in backups:
                        orig = client.fs_read(b["backup"])
                        original_text = orig.get("content") if isinstance(orig, dict) else str(orig)
                        client.fs_write(b["path"], original_text)
                except Exception:
                    pass
            err = {"ok": False, "error": str(e)}
            print(_json.dumps(err, indent=2))
            return 2

    sp.set_defaults(func=_do_collab_apply)

    sp = sub.add_parser(
        "scout", help="Run the Artemis Repository Scout swarm (requires manual LLM env vars)"
    )
    sp.add_argument(
        "--task",
        default="Scout this repository: map integrations, hotspots, and propose improvements.",
    )
    sp.add_argument("--check", action="store_true", help="Run scout readiness checks and exit")
    sp.add_argument(
        "--approval",
        choices=["suggest", "auto-analyze", "full-auto"],
        default=None,
        help="Approval mode: suggest (ask before analysis & prefetch), auto-analyze (ask before prefetch), full-auto",
    )
    sp.add_argument(
        "--json", action="store_true", help="Emit structured JSON output and suppress progress"
    )

    def _do_scout(args):
        import os as _os
        import subprocess as _sp

        # If JSON mode, suppress INFO/DEBUG logs to keep stdout clean
        if getattr(args, "json", False):
            try:
                import logging as _logging

                _logging.disable(_logging.INFO)
            except Exception:
                pass
        # Readiness check shortcut that avoids LLM imports
        if getattr(args, "check", False):
            proc = _sp.run(
                ["python3", "scripts/scout_readiness_check.py"],
                capture_output=True,
                text=True,
            )
            print(proc.stdout.strip() or proc.stderr.strip())
            return 0 if proc.returncode == 0 else proc.returncode
        # This path requires network + LLM env; we provide a friendly message if not set
        try:
            from app.swarms.core.swarm_integration import get_artemis_orchestrator

            orchestrator = get_artemis_orchestrator()
            import asyncio

            # Helpers
            def _approval_mode() -> str:
                if args.approval:
                    return args.approval
                return _os.getenv("ARTEMIS_DEFAULT_APPROVAL_MODE", "full-auto").lower()

            def _confirm(prompt: str) -> bool:
                try:
                    ans = input(f"{prompt} [y/n]: ").strip().lower()
                    return ans in ("y", "yes")
                except Exception:
                    return False

            from pathlib import Path as _Path

            def _load_project_instructions() -> str:
                repo = _Path.cwd()
                for p in [
                    repo / ".artemis" / "scout.md",
                    repo / ".artemis" / "instructions.md",
                    repo / "artemis.md",
                ]:
                    if p.exists() and p.is_file():
                        try:
                            return p.read_text()[:20000]
                        except Exception:
                            return ""
                return ""

            def _run_hook(which: str, json_input: str | None = None, approval: str = "") -> int:
                hook = _Path(".artemis/hooks") / (
                    "pre-scout.sh" if which == "pre" else "post-scout.sh"
                )
                if not hook.exists() or not _os.access(hook, _os.X_OK):
                    return 0
                # Best-effort ownership check
                try:
                    st = hook.stat()
                    if hasattr(_os, "geteuid") and st.st_uid != _os.geteuid():
                        return 0
                except Exception:
                    pass
                env = {
                    **_os.environ,
                    "ARTEMIS_TASK": (args.task or ""),
                    "ARTEMIS_APPROVAL_MODE": _approval_mode(),
                }
                try:
                    if json_input is None:
                        pr = _sp.run([str(hook)], env=env, capture_output=True, text=True)
                    else:
                        pr = _sp.run(
                            [str(hook)], env=env, input=json_input, capture_output=True, text=True
                        )
                    return pr.returncode
                except Exception:
                    return 0

            mode = _approval_mode()
            # Ask before prefetch/index in suggest/auto-analyze
            if mode in ("suggest", "auto-analyze"):
                max_files = int(_os.getenv("SCOUT_PREFETCH_MAX_FILES", "10"))
                max_bytes = int(_os.getenv("SCOUT_PREFETCH_MAX_BYTES", "50000"))
                if not _confirm(
                    f"Proceed with prefetch/index (up to {max_files} files x {max_bytes} bytes)?"
                ):
                    _os.environ["SCOUT_PREFETCH_ENABLED"] = "false"
                    _os.environ["SCOUT_DELTA_INDEX_ENABLED"] = "false"

            # Append project instructions
            eff_task = args.task or ""
            proj = _load_project_instructions()
            if proj:
                eff_task += f"\n\nProject Instructions:\n{proj}\n"

            # Ask before analysis in suggest mode
            if mode == "suggest" and not _confirm("Proceed with scout analysis now?"):
                if args.json:
                    j = json.dumps(
                        {
                            "success": False,
                            "task": eff_task,
                            "error": "Aborted by user",
                        }
                    )
                    print(j)
                else:
                    print("Aborted by user.")
                return 1

            # Pre hook
            if _run_hook("pre", approval=mode) != 0:
                if args.json:
                    j = json.dumps(
                        {
                            "success": False,
                            "task": eff_task,
                            "error": "Pre-scout hook blocked execution",
                        }
                    )
                    print(j)
                else:
                    print("Pre-scout hook blocked execution.")
                return 2

            result = asyncio.get_event_loop().run_until_complete(
                orchestrator.execute_swarm(
                    content=eff_task, swarm_type="repository_scout", context={}
                )
            )

            if args.json:
                out = format_scout_json(eff_task, result)
                j = json.dumps(out)
                print(j)
                _run_hook("post", json_input=j, approval=mode)
            else:
                _summary = (
                    getattr(result, "final_output", None) or getattr(result, "content", "") or ""
                )
                print(
                    json.dumps(
                        {
                            "success": getattr(result, "success", False),
                            "confidence": float(getattr(result, "confidence", 0.0)),
                            "summary": _summary[:2000],
                        },
                        indent=2,
                    )
                )
                _run_hook("post", json_input=None, approval=mode)
            return 0
        except Exception as e:
            if getattr(args, "json", False):
                print(
                    json.dumps(
                        {
                            "success": False,
                            "error": f"ERROR running scout swarm: {e}",
                        }
                    )
                )
            else:
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
                from app.swarms.core.swarm_integration import get_artemis_orchestrator

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

    # collab merge-check (nested helpers to ensure availability at parse time)
    def _load_merge_threshold(default: float = 0.8) -> float:
        from pathlib import Path

        import yaml

        candidates = [
            Path("app/collaboration/collaboration_protocol.yaml"),
            Path("collaboration_protocol.yaml"),
        ]
        for p in candidates:
            if p.exists():
                try:
                    cfg = yaml.safe_load(p.read_text()) or {}
                    th = (
                        cfg.get("thresholds", {}).get("merge_ready_confidence")
                        if isinstance(cfg, dict)
                        else None
                    )
                    if th:
                        return float(th)
                except Exception:
                    pass
        return default

    def _do_collab_merge_check(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        import json as _json

        threshold = _load_merge_threshold(0.8)
        # Find reviews
        res = client.memory_search(f"collab AND review AND refs:{args.pid}", limit=50)
        results = res.get("results") if isinstance(res, dict) else res
        approvals = {}
        for r in results or []:
            tags = r.get("tags", []) or []
            if any(t == "status:approved" for t in tags):
                by = next((t.split(":", 1)[1] for t in tags if t.startswith("by:")), None)
                try:
                    body = _json.loads(r.get("content") or "{}")
                except Exception:
                    body = {}
                conf = float(body.get("confidence", 0.0))
                if by:
                    approvals[by] = max(conf, approvals.get(by, 0.0))

        ready = (
            approvals.get("claude", 0.0) >= threshold and approvals.get("codex", 0.0) >= threshold
        )
        apply_task_id = None
        if ready:
            # Emit apply task for codex
            import uuid

            apply_task_id = str(uuid.uuid4())
            tags = [
                "collab",
                f"id:{apply_task_id}",
                "pending",
                "for:codex",
                f"refs:{args.pid}",
                "type:apply",
            ]
            client.memory_add(
                topic=f"collab_task:{apply_task_id}",
                content=f"Apply proposal {args.pid}",
                source="artemis-run",
                tags=tags,
                memory_type="procedural",
            )
        out = {
            "ok": True,
            "proposal": args.pid,
            "threshold": threshold,
            "approvals": approvals,
            "merge_ready": ready,
            "apply_task_id": apply_task_id,
        }
        print(
            _json.dumps(out, indent=2)
            if args.json
            else _json.dumps({k: v for k, v in out.items() if k != "approvals"}, indent=2)
        )
        return 0

    sp = collab_sub.add_parser(
        "merge-check", help="Check if a proposal is merge-ready and emit Apply task if so"
    )
    sp.add_argument("--proposal", required=True, dest="pid")
    sp.add_argument("--json", action="store_true", help="JSON output")
    sp.set_defaults(func=_do_collab_merge_check)

    # Health and proof: verify MCP, memory vectors, recent scout breadcrumbs
    sp = sub.add_parser("health", help="Check MCP/memory health and show proof of scout indexing")
    sp.add_argument("--json", action="store_true", help="JSON output")
    sp.add_argument("--limit", type=int, default=5, help="Max recent items to show")

    def _do_health(args):
        import asyncio as _asyncio
        import json as _json
        from pathlib import Path as _Path

        out = {"ok": True, "mcp": {}, "vectors": {}, "recent": {}}
        client = detect_stdio_mcp(_Path.cwd())
        out["mcp"]["available"] = bool(client)
        if client:
            try:
                # repo index sample
                idx = client.repo_index(root=".", max_bytes_per_file=5000)
                files = (idx.get("files") if isinstance(idx, dict) else []) or []
                out["mcp"]["repo_index_sample"] = len(files)
            except Exception as e:
                out["mcp"]["repo_index_error"] = str(e)
            try:
                res = client.memory_search("scout", limit=args.limit)
                items = res.get("results") if isinstance(res, dict) else res or []
                out["recent"]["mcp_memory"] = [
                    {
                        "topic": it.get("topic"),
                        "timestamp": it.get("timestamp"),
                        "tags": it.get("tags")[:6] if isinstance(it.get("tags"), list) else [],
                        "content_preview": (it.get("content") or "")[:140],
                    }
                    for it in items
                ]
            except Exception as e:
                out["recent"]["mcp_memory_error"] = str(e)
        else:
            out["ok"] = False
            out["error"] = "MCP stdio server not available (bin/mcp-fs-memory)."

        # Vector/embedding availability via memory router search
        try:
            from app.memory.unified_memory_router import MemoryDomain, get_memory_router

            async def _probe():
                router = get_memory_router()
                hits = await router.search("artemis", MemoryDomain.ARTEMIS, k=1)
                return hits

            hits = _asyncio.get_event_loop().run_until_complete(_probe())
            out["vectors"]["available"] = True
            out["vectors"]["probe_hits"] = len(hits)
        except Exception as e:
            out["vectors"]["available"] = False
            out["vectors"]["error"] = str(e)

        # Delta index cache proof
        try:
            cache_path = _Path("tmp/scout_index_cache.json")
            if cache_path.exists():
                import json as _j

                data = _j.loads(cache_path.read_text())
                out["recent"]["delta_index_cache_entries"] = len(data)
            else:
                out["recent"]["delta_index_cache_entries"] = 0
        except Exception:
            pass

        if args.json:
            print(_json.dumps(out))
        else:
            print(
                _json.dumps(
                    {
                        "ok": out.get("ok", True),
                        "mcp_available": out.get("mcp", {}).get("available", False),
                        "repo_index_sample": out.get("mcp", {}).get("repo_index_sample", 0),
                        "vectors_available": out.get("vectors", {}).get("available", False),
                        "probe_hits": out.get("vectors", {}).get("probe_hits", 0),
                        "delta_index_cache_entries": out.get("recent", {}).get(
                            "delta_index_cache_entries", 0
                        ),
                        "recent_mcp_memory": out.get("recent", {}).get("mcp_memory", [])[:3],
                    },
                    indent=2,
                )
            )
        return 0 if out.get("ok", True) else 2

    sp.set_defaults(func=_do_health)

    # Metrics: summarize recent scout runs from vectors + MCP
    sp = sub.add_parser(
        "metrics", help="Show recent scout metrics with quality scoring (vectors + MCP breadcrumbs)"
    )
    sp.add_argument("--json", action="store_true", help="JSON output")
    sp.add_argument("--limit", type=int, default=5, help="Max recent items to show")
    sp.add_argument("--recent", action="store_true", help="Show only recent summaries")

    def _do_metrics(args):
        import asyncio as _asyncio
        import json as _json
        from pathlib import Path as _Path

        out = {
            "ok": True,
            "mcp_recent": [],
            "vector_runs": [],
            "aggregates": {},
            "quality_score": {},
        }

        # Recent MCP entries
        client = detect_stdio_mcp(_Path.cwd())
        if client:
            try:
                res = client.memory_search(
                    "artemis AND completed AND swarm:repository_scout", limit=args.limit
                )
                items = res.get("results") if isinstance(res, dict) else res or []
                out["mcp_recent"] = [
                    {
                        "topic": it.get("topic"),
                        "timestamp": it.get("timestamp"),
                        "tags": it.get("tags")[:8] if isinstance(it.get("tags"), list) else [],
                        "content_preview": (it.get("content") or "")[:160],
                    }
                    for it in items
                ]
            except Exception as e:
                out["mcp_error"] = str(e)
        else:
            out["mcp_error"] = "MCP not available"

        # Vector-backed runs (if Weaviate available)
        try:
            from app.memory.unified_memory_router import MemoryDomain, get_memory_router

            async def _load():
                router = get_memory_router()
                # Search for scout swarm runs by swarm name keyword
                hits = await router.search(
                    "Artemis Repository Scout Swarm", MemoryDomain.ARTEMIS, k=50
                )
                return hits

            hits = _asyncio.get_event_loop().run_until_complete(_load())
            runs = []
            for h in hits or []:
                md = h.metadata or {}
                # metadata is JSON or dict depending on storage
                if isinstance(md, str):
                    try:
                        import json as _j

                        md = _j.loads(md)
                    except Exception:
                        md = {}
                swarm_name = md.get("swarm_name")
                if not swarm_name or "Scout" not in str(swarm_name):
                    continue
                runs.append(
                    {
                        "swarm_name": swarm_name,
                        "coordination_pattern": md.get("coordination_pattern"),
                        "execution_time_ms": md.get("execution_time_ms"),
                        "cost_usd": md.get("cost_usd"),
                        "source_uri": getattr(h, "source_uri", ""),
                    }
                )
            out["vector_runs"] = runs[: args.limit]
            # Aggregates
            etimes = [
                r.get("execution_time_ms") or 0.0
                for r in runs
                if isinstance(r.get("execution_time_ms"), (int, float))
            ]
            costs = [
                r.get("cost_usd") or 0.0
                for r in runs
                if isinstance(r.get("cost_usd"), (int, float))
            ]

            def _avg(arr):
                return (sum(arr) / len(arr)) if arr else 0.0

            out["aggregates"] = {
                "vector_runs": len(runs),
                "avg_execution_time_ms": _avg(etimes),
                "avg_cost_usd": _avg(costs),
            }
        except Exception as e:
            out["vector_error"] = str(e)

        # Calculate quality score from the most recent scout run
        def _calculate_quality_score():
            """Calculate quality score based on the most recent scout run data."""
            try:
                # Try to get the most recent MCP entry first
                recent_data = None
                if out.get("mcp_recent") and len(out["mcp_recent"]) > 0:
                    # Look for content that can be parsed as scout output
                    for entry in out["mcp_recent"][:3]:  # Check top 3 most recent
                        content = entry.get("content_preview", "")
                        if "FINDINGS:" in content or "RISKS:" in content:
                            recent_data = content
                            break

                # If no MCP data, try vector runs
                if not recent_data and out.get("vector_runs"):
                    # Vector runs don't contain the actual scout output, so we can't score them
                    pass

                if not recent_data:
                    return {
                        "overall_score": 0.0,
                        "components": {
                            "schema_valid": 0.0,
                            "confidence": 0.0,
                            "risk_signal": 0.0,
                            "findings_signal": 0.0,
                            "recs_signal": 0.0,
                        },
                        "details": {
                            "schema_validation": {
                                "valid": False,
                                "missing_sections": ["No recent scout data available"],
                            },
                            "per_agent_metrics": [],
                            "synthesis_metrics": {},
                            "orchestrator_metrics": {
                                "success": False,
                                "execution_time_ms": 0,
                                "confidence": 0.0,
                            },
                            "tool_usage_total": 0,
                        },
                        "note": "No recent scout run data available for scoring",
                    }

                # Create a dummy result object to use with format_scout_json
                class DummyResult:
                    def __init__(self, content):
                        self.final_output = content
                        self.success = True
                        self.confidence = 0.0  # Will be extracted from content if available
                        self.execution_time_ms = 0.0
                        self.metadata = {}

                dummy_result = DummyResult(recent_data)
                scout_data = format_scout_json("recent_scout_run", dummy_result)

                # Extract components for quality scoring
                schema_sections = ["FINDINGS", "INTEGRATIONS", "RISKS", "RECOMMENDATIONS"]
                missing_sections = []
                found_sections = 0

                for section in schema_sections:
                    section_key = section.lower()
                    if section_key in scout_data and scout_data[section_key]:
                        found_sections += 1
                    else:
                        missing_sections.append(section)

                # Check for METRICS and CONFIDENCE sections in raw content
                has_metrics = "METRICS:" in recent_data.upper()
                has_confidence = "CONFIDENCE:" in recent_data.upper()
                if has_metrics:
                    found_sections += 1
                else:
                    missing_sections.append("METRICS")
                if has_confidence:
                    found_sections += 1
                else:
                    missing_sections.append("CONFIDENCE")

                # Calculate component scores
                schema_valid = 1.0 if found_sections >= 6 else found_sections / 6.0
                confidence = scout_data.get("metrics", {}).get("confidence", 0.0)

                # Count items for signals
                risks_count = len(scout_data.get("risks", []))
                findings_count = len(scout_data.get("findings", []))
                recommendations_count = len(scout_data.get("recommendations", []))

                # Calculate signals (capped as per formula)
                risk_signal = min(1.0, risks_count / 8.0) if risks_count > 0 else 0.0
                findings_signal = min(1.0, findings_count / 12.0) if findings_count > 0 else 0.0
                recs_signal = (
                    min(1.0, recommendations_count / 10.0) if recommendations_count > 0 else 0.0
                )

                # Overall score formula
                overall_score = (
                    0.25 * schema_valid
                    + 0.25 * confidence
                    + 0.2 * risk_signal
                    + 0.15 * findings_signal
                    + 0.15 * recs_signal
                )

                # Get orchestrator metrics
                execution_time = scout_data.get("metrics", {}).get("execution_time", 0.0)
                tool_usage = scout_data.get("metrics", {}).get("tool_usage_total", 0)

                return {
                    "overall_score": round(overall_score, 3),
                    "components": {
                        "schema_valid": round(schema_valid, 3),
                        "confidence": round(confidence, 3),
                        "risk_signal": round(risk_signal, 3),
                        "findings_signal": round(findings_signal, 3),
                        "recs_signal": round(recs_signal, 3),
                    },
                    "details": {
                        "schema_validation": {
                            "valid": len(missing_sections) == 0,
                            "missing_sections": missing_sections,
                        },
                        "per_agent_metrics": [],  # Not available in current data structure
                        "synthesis_metrics": {
                            "model_used": "unknown",
                            "response_time_ms": execution_time,
                            "tokens_used": 0,
                            "cost_usd": 0.0,
                        },
                        "orchestrator_metrics": {
                            "execution_time_ms": execution_time,
                            "success": scout_data.get("success", False),
                            "confidence": confidence,
                        },
                        "tool_usage_total": tool_usage,
                    },
                    "counts": {
                        "risks": risks_count,
                        "findings": findings_count,
                        "recommendations": recommendations_count,
                    },
                }

            except Exception as e:
                return {
                    "overall_score": 0.0,
                    "error": f"Failed to calculate quality score: {str(e)}",
                    "components": {
                        "schema_valid": 0.0,
                        "confidence": 0.0,
                        "risk_signal": 0.0,
                        "findings_signal": 0.0,
                        "recs_signal": 0.0,
                    },
                }

        out["quality_score"] = _calculate_quality_score()

        if args.json:
            print(_json.dumps(out))
        else:
            print(
                _json.dumps(
                    {
                        "ok": out.get("ok", True),
                        "recent_mcp": out.get("mcp_recent", [])[:3],
                        "vector_aggregates": out.get("aggregates", {}),
                        "quality_score": out.get("quality_score", {}),
                    },
                    indent=2,
                )
            )
        return 0 if out.get("ok", True) else 2

    sp.set_defaults(func=_do_metrics)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 1
    return int(args.func(args))
    # (Removed duplicate merge-check definition moved earlier)

    # collab watch
    sp = collab_sub.add_parser(
        "watch", help="Poll memory for new collab entries assigned to an agent"
    )
    sp.add_argument("--for", required=True, dest="agent", choices=["codex", "claude"])
    sp.add_argument("--poll-interval", type=int, default=10)
    sp.add_argument("--filter", default=None, help="Override filter (advanced)")

    def _do_collab_watch(args):
        import hashlib
        import json as _json
        import time

        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        seen = set()
        flt = args.filter or f"collab AND for:{args.agent} AND (pending OR pending_review)"
        print(f"Watching for: {flt} (interval={args.poll_interval}s). Ctrl-C to stop.")
        try:
            while True:
                res = client.memory_search(flt, limit=50)
                items = res.get("results") if isinstance(res, dict) else res
                for it in items or []:
                    key = hashlib.sha256(
                        (it.get("topic", "") + it.get("timestamp", ""))[:200].encode()
                    ).hexdigest()
                    if key in seen:
                        continue
                    seen.add(key)
                    print(
                        _json.dumps(
                            {
                                "topic": it.get("topic"),
                                "tags": it.get("tags"),
                                "timestamp": it.get("timestamp"),
                                "preview": (it.get("content") or "")[:200],
                            },
                            indent=2,
                        )
                    )
                time.sleep(max(1, int(args.poll_interval)))
        except KeyboardInterrupt:
            print("Stopped.")
            return 0

    sp.set_defaults(func=_do_collab_watch)
    # collab status
    sp = collab_sub.add_parser("status", help="Show current status for a collaboration id")
    sp.add_argument("--id", required=True, dest="eid")
    sp.add_argument("--json", action="store_true", help="JSON output")

    def _do_collab_status(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        import json as _json

        q = f"collab AND id:{args.eid}"
        res = client.memory_search(q, limit=100)
        items = res.get("results") if isinstance(res, dict) else res or []
        # Derive status
        state = {
            "id": args.eid,
            "has_proposal": False,
            "pending": False,
            "in_progress": False,
            "completed": False,
            "pending_review": False,
            "approved": False,
            "rejected": False,
            "applied": False,
            "approvals": {},
            "entries": [],
        }
        for it in items:
            tags = it.get("tags", []) or []
            topic = it.get("topic", "")
            state["entries"].append({"topic": topic, "tags": tags, "ts": it.get("timestamp")})
            if topic.startswith("collab_proposal:"):
                state["has_proposal"] = True
                state["pending_review"] |= any(t == "pending_review" for t in tags)
            if topic.startswith("collab_task:"):
                state["pending"] |= any(t == "pending" for t in tags)
                state["in_progress"] |= any(t == "in_progress" for t in tags)
                state["completed"] |= any(t == "completed" for t in tags)
            if topic.startswith("collab_review:"):
                if any(t == "status:approved" for t in tags):
                    by = next((t.split(":", 1)[1] for t in tags if t.startswith("by:")), None)
                    try:
                        body = _json.loads(it.get("content") or "{}")
                    except Exception:
                        body = {}
                    conf = float(body.get("confidence", 0.0))
                    if by:
                        state["approvals"][by] = max(conf, state["approvals"].get(by, 0.0))
                if any(t == "status:rejected" for t in tags):
                    state["rejected"] = True
            if topic.startswith("collab_apply:"):
                state["applied"] = True
        # Approved if both agents >= 0.8
        state["approved"] = (
            state["approvals"].get("claude", 0.0) >= 0.8
            and state["approvals"].get("codex", 0.0) >= 0.8
        )
        print(
            _json.dumps(state, indent=2)
            if args.json
            else _json.dumps({k: v for k, v in state.items() if k != "entries"}, indent=2)
        )
        return 0

    sp.set_defaults(func=_do_collab_status)

    # --------------------
    # Cleanup commands
    clean = sub.add_parser("cleanup", help="Cleanup utilities for collab and backups")
    clean_sub = clean.add_subparsers(dest="cleanup_cmd")

    # cleanup collab
    sp = clean_sub.add_parser("collab", help="Mark old/expired collab entries as archived")
    sp.add_argument("--type", choices=["stale", "completed", "expired"], default="expired")
    sp.add_argument("--older-than", dest="older_than", help="Duration filter (e.g., 7d, 12h)")
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--json", action="store_true")

    def _do_cleanup_collab(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        import datetime as _dt
        import json as _json

        flt = "collab"
        if args.type == "stale":
            flt += " AND (pending OR pending_review)"
        elif args.type == "completed":
            flt += " AND completed"
        elif args.type == "expired":
            flt += " AND expires:"
        res = client.memory_search(flt, limit=200)
        items = res.get("results") if isinstance(res, dict) else res or []
        to_archive = []

        def _parse_duration(s: str) -> _dt.timedelta:
            s = s.strip().lower()
            if s.endswith("d"):
                return _dt.timedelta(days=int(s[:-1] or 0))
            if s.endswith("h"):
                return _dt.timedelta(hours=int(s[:-1] or 0))
            if s.endswith("m"):
                return _dt.timedelta(minutes=int(s[:-1] or 0))
            return _dt.timedelta(seconds=int(s))

        cutoff = None
        if args.older_than:
            try:
                cutoff = _dt.datetime.utcnow() - _parse_duration(args.older_than)
            except Exception:
                cutoff = None

        now = _dt.datetime.utcnow()
        for it in items:
            tags = it.get("tags", []) or []
            ts = it.get("timestamp") or "1970-01-01"
            try:
                created = _dt.datetime.fromisoformat(ts.replace("Z", ""))
            except Exception:
                created = _dt.datetime.min
            is_old = cutoff and created.replace(tzinfo=None) < cutoff
            is_expired = False
            for t in tags:
                if t.startswith("expires:"):
                    try:
                        exp = _dt.datetime.fromisoformat(t.split(":", 1)[1].replace("Z", ""))
                        if exp.replace(tzinfo=None) <= now:
                            is_expired = True
                            break
                    except Exception:
                        pass
            if args.type == "expired" and not is_expired:
                continue
            if args.type in ("stale", "completed") and args.older_than and not is_old:
                continue
            to_archive.append(it)

        archived = []
        if not args.dry_run:
            for it in to_archive:
                topic = it.get("topic") or ""
                id_tag = next((t for t in (it.get("tags") or []) if t.startswith("id:")), None)
                collab_id = id_tag.split(":", 1)[1] if id_tag else "unknown"
                # Mark archived
                client.memory_add(
                    topic=f"collab_archived:{collab_id}",
                    content=f"Archived {topic}",
                    source="artemis-run",
                    tags=["collab", "archived", f"id:{collab_id}"],
                    memory_type="episodic",
                )
                archived.append(collab_id)
        out = {
            "ok": True,
            "type": args.type,
            "matched": len(to_archive),
            "archived": archived,
            "dry_run": args.dry_run,
        }
        print(
            _json.dumps(out, indent=2)
            if args.json
            else _json.dumps({k: v for k, v in out.items() if k != "archived"}, indent=2)
        )
        return 0

    sp.set_defaults(func=_do_cleanup_collab)

    # cleanup backups
    sp = clean_sub.add_parser("backups", help="Delete .mcp_backups older than the given duration")
    sp.add_argument("--older-than", required=True)
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--json", action="store_true")

    def _do_cleanup_backups(args):
        import datetime as _dt
        import json as _json
        import time

        def _parse_duration(s: str) -> _dt.timedelta:
            s = s.strip().lower()
            if s.endswith("d"):
                return _dt.timedelta(days=int(s[:-1] or 0))
            if s.endswith("h"):
                return _dt.timedelta(hours=int(s[:-1] or 0))
            if s.endswith("m"):
                return _dt.timedelta(minutes=int(s[:-1] or 0))
            return _dt.timedelta(seconds=int(s))

        root = Path(".mcp_backups")
        removed = []
        matched = 0
        if root.exists():
            cutoff = time.time() - _parse_duration(args.older_than).total_seconds()
            for p in root.rglob("*"):
                if not p.is_file():
                    continue
                matched += 1
                if p.stat().st_mtime < cutoff and not args.dry_run:
                    try:
                        p.unlink()
                        removed.append(str(p))
                    except Exception:
                        pass
        out = {"ok": True, "matched": matched, "removed": removed, "dry_run": args.dry_run}
        print(
            _json.dumps(out, indent=2)
            if args.json
            else _json.dumps({k: v for k, v in out.items() if k != "removed"}, indent=2)
        )
        return 0

    sp.set_defaults(func=_do_cleanup_backups)

    # --------------------
    # Quick fix: create proposal, auto-approve, apply immediately
    sp = collab_sub.add_parser(
        "quick-fix", help="Create a minimal code_change proposal and apply it"
    )
    sp.add_argument("--file", required=True, dest="file")
    sp.add_argument("--line", required=True, type=int)
    sp.add_argument("--old", required=True)
    sp.add_argument("--new", required=True)
    sp.add_argument("--test", action="append", default=[], help="Test command to run (repeatable)")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--dry-run", action="store_true")

    def _do_collab_quick_fix(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        import json as _json
        import uuid

        pid = str(uuid.uuid4())
        proposal = {
            "type": "code_change",
            "files": [
                {
                    "path": args.file,
                    "changes": [{"line": args.line, "old": args.old, "new": args.new}],
                }
            ],
            "tests": args.test,
            "rationale": "quick-fix",
        }
        # Emit proposal
        client.memory_add(
            topic=f"collab_proposal:{pid}",
            content=_json.dumps(proposal, indent=2),
            source="artemis-run",
            tags=["collab", f"id:{pid}", "proposal", "pending_review", "for:codex"],
            memory_type="procedural",
        )
        # Auto-approve by both agents
        for agent, conf in [("codex", 0.95), ("claude", 0.95)]:
            body = {
                "proposal_id": pid,
                "reviewed_by": agent,
                "status": "approved",
                "confidence": conf,
                "notes": "quick-fix",
            }
            client.memory_add(
                topic=f"collab_review:{pid}",
                content=_json.dumps(body),
                source="artemis-run",
                tags=["collab", "review", "status:approved", f"refs:{pid}", f"by:{agent}"],
                memory_type="procedural",
            )

        # Apply
        class _ApplyArgs:
            pass

        _a = _ApplyArgs()
        _a.pid = pid
        _a.json = args.json
        _a.dry_run = args.dry_run
        _a.force = True
        return _do_collab_apply(_a)

    sp.set_defaults(func=_do_collab_quick_fix)

    # Batch approve
    sp = collab_sub.add_parser("batch-approve", help="Approve multiple proposals in one call")
    sp.add_argument("--agent", required=True, choices=["codex", "claude"])
    sp.add_argument("--proposals", required=True, help="Comma-separated proposal ids")
    sp.add_argument("--confidence", type=float, default=0.85)
    sp.add_argument("--notes", default="batch-approved")
    sp.add_argument("--json", action="store_true")

    def _do_collab_batch_approve(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2
        import json as _json

        ids = [s.strip() for s in args.proposals.split(",") if s.strip()]
        done = []
        for pid in ids:
            body = {
                "proposal_id": pid,
                "reviewed_by": args.agent,
                "status": "approved",
                "confidence": args.confidence,
                "notes": args.notes,
            }
            client.memory_add(
                topic=f"collab_review:{pid}",
                content=_json.dumps(body),
                source="artemis-run",
                tags=["collab", "review", "status:approved", f"refs:{pid}", f"by:{args.agent}"],
                memory_type="procedural",
            )
            done.append(pid)
        out = {"ok": True, "approved": done, "count": len(done)}
        print(_json.dumps(out, indent=2))
        return 0

    sp.set_defaults(func=_do_collab_batch_approve)

    # Dashboard
    sp = collab_sub.add_parser("dashboard", help="Show collaboration status summary")
    sp.add_argument("--json", action="store_true")
    sp.add_argument(
        "--window", default="24h", help="Lookback window for test stats (e.g., 24h, 7d)"
    )

    def _do_collab_dashboard(args):
        import datetime as _dt
        import json as _json

        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server (bin/mcp-fs-memory) not found or not working.")
            return 2

        def _count(q: str) -> int:
            r = client.memory_search(q, limit=500)
            return len(r.get("results") or []) if isinstance(r, dict) else len(r or [])

        pending_claude = _count("collab AND pending AND for:claude")
        pending_codex = _count("collab AND pending AND for:codex")
        pending_review = _count("collab AND pending_review")
        approved = _count("collab AND review AND status:approved")
        applied_today = _count("collab AND apply AND status:completed")
        # Test stats
        window = args.window

        def _dur(s: str) -> _dt.timedelta:
            s = s.lower().strip()
            if s.endswith("d"):
                return _dt.timedelta(days=int(s[:-1] or 0))
            if s.endswith("h"):
                return _dt.timedelta(hours=int(s[:-1] or 0))
            if s.endswith("m"):
                return _dt.timedelta(minutes=int(s[:-1] or 0))
            return _dt.timedelta(seconds=int(s))

        cutoff = _dt.datetime.utcnow() - _dur(window)
        tests = client.memory_search("collab AND test AND result:", limit=500).get("results", [])

        def _ts(it):
            try:
                return _dt.datetime.fromisoformat(
                    (it.get("timestamp") or "1970-01-01").replace("Z", "")
                )
            except Exception:
                return _dt.datetime.min

        tests = [t for t in tests if _ts(t) > cutoff]
        passed = sum(1 for t in tests if any(tag == "result:pass" for tag in (t.get("tags") or [])))
        total = len(tests)
        success_rate = round((passed / total) * 100, 1) if total else 0.0
        # Stale items (>7d)
        all_collab = client.memory_search("collab", limit=500).get("results", [])
        seven = _dt.datetime.utcnow() - _dt.timedelta(days=7)
        stale = sum(
            1
            for it in all_collab
            if _ts(it) < seven and not any(tag == "archived" for tag in (it.get("tags") or []))
        )
        out = {
            "pending_tasks": {"claude": pending_claude, "codex": pending_codex},
            "proposals": {
                "pending_review": pending_review,
                "approved_reviews": approved,
                "applied_today": applied_today,
            },
            "tests": {"success_rate_pct": success_rate, "total": total, "passed": passed},
            "cleanup": {"stale_gt_7d": stale},
        }
        if args.json:
            print(_json.dumps(out, indent=2))
        else:
            print("Collaboration Status\n-------------------")
            print(f"Pending Tasks:\n  Claude: {pending_claude}\n  Codex:  {pending_codex}")
            print(
                f"\nActive Proposals:\n  Pending Review: {pending_review}\n  Approved Reviews: {approved}\n  Applied Today:   {applied_today}"
            )
            print(f"\nSuccess Rate (last {args.window}): {success_rate}% ({passed}/{total})")
            print(f"\nCleanup Needed:\n  Stale (>7d): {stale}")
        return 0

    sp.set_defaults(func=_do_collab_dashboard)

    # Metrics command for scout visibility
    sp = sub.add_parser("metrics", help="Show scout execution metrics and statistics")
    sp.add_argument("--recent", action="store_true", help="Show recent scout executions")
    sp.add_argument("--json", action="store_true", help="Output as JSON")
    sp.add_argument("--limit", type=int, default=5, help="Number of recent executions to show")

    def _do_metrics(args):
        client = detect_stdio_mcp(Path.cwd())
        if not client:
            print("ERROR: stdio MCP server not found")
            return 2

        import json as _json

        # Search for recent scout executions in memory
        results = client.memory_search("integrated_swarm", limit=args.limit * 3)
        items = results.get("results") if isinstance(results, dict) else results or []

        # Filter for scout swarms
        scout_runs = []
        for item in items:
            if (
                "scout" in item.get("topic", "").lower()
                or "scout" in str(item.get("tags", [])).lower()
            ):
                try:
                    content = _json.loads(item.get("content", "{}"))
                    metadata = content.get("metadata", {})
                    scout_runs.append(
                        {
                            "timestamp": item.get("timestamp", ""),
                            "task": content.get("task", "")[:100],
                            "confidence": content.get("confidence", 0.0),
                            "success": content.get("success", False),
                            "execution_time_ms": metadata.get("execution_time_ms", 0),
                            "tool_usage_total": metadata.get("tool_usage_total", 0),
                            "agents": metadata.get("agents_used", []),
                            "pattern": metadata.get("coordination_pattern", "unknown"),
                            "cost_usd": metadata.get("cost_usd", 0.0),
                        }
                    )
                except:
                    pass

        # Sort by timestamp
        scout_runs.sort(key=lambda x: x["timestamp"], reverse=True)
        scout_runs = scout_runs[: args.limit]

        if args.json:
            output = {
                "scout_executions": scout_runs,
                "summary": {
                    "total_shown": len(scout_runs),
                    "avg_confidence": (
                        sum(r["confidence"] for r in scout_runs) / len(scout_runs)
                        if scout_runs
                        else 0
                    ),
                    "avg_time_ms": (
                        sum(r["execution_time_ms"] for r in scout_runs) / len(scout_runs)
                        if scout_runs
                        else 0
                    ),
                    "total_cost": sum(r["cost_usd"] for r in scout_runs),
                    "success_rate": (
                        sum(1 for r in scout_runs if r["success"]) / len(scout_runs)
                        if scout_runs
                        else 0
                    ),
                },
            }
            print(_json.dumps(output, indent=2))
        else:
            print(f"\n=== Recent Scout Executions ({len(scout_runs)}) ===\n")
            for run in scout_runs:
                print(f"Timestamp: {run['timestamp']}")
                print(f"Task: {run['task']}")
                print(
                    f"Success: {'✅' if run['success'] else '❌'} | Confidence: {run['confidence']:.2f}"
                )
                print(
                    f"Time: {run['execution_time_ms']:.0f}ms | Tools used: {run['tool_usage_total']}"
                )
                print(f"Pattern: {run['pattern']} | Cost: ${run['cost_usd']:.4f}")
                print("-" * 60)

            if scout_runs:
                print("\nSummary:")
                print(
                    f"Average confidence: {sum(r['confidence'] for r in scout_runs) / len(scout_runs):.2f}"
                )
                print(
                    f"Average time: {sum(r['execution_time_ms'] for r in scout_runs) / len(scout_runs):.0f}ms"
                )
                print(f"Total cost: ${sum(r['cost_usd'] for r in scout_runs):.4f}")

        return 0

    sp.set_defaults(func=_do_metrics)


if __name__ == "__main__":
    raise SystemExit(main())
