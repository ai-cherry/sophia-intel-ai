# QA Runbook

This runbook guides QA reviewers through scanning and structured reviews using provided tools and the QA prompt.

## Quick Scans
- Shell scanner: `tools/scan_sophia_repo.sh`
  - Outputs to `scan_results/REPORT.md` and related txt files
  - Checks: duplicates, suspicious imports, TODO/FIXME, empty files, potential secrets, bare excepts, TSX `< number` patterns
- Deep scanner: `python3 tools/deep_scan.py`
  - Outputs to `scan_results/deep_scan.json`
  - Checks: bare excepts, `any` usage, console.log, naive circular Python imports

## Review Focus
- Recently changed files (git log) and core paths (agents, routers, telemetry)
- UI: dashboards (refactored data hooks), unified streaming, telemetry panel
- Integration surfaces: API bridge, MCP servers, telemetry endpoints

## How to Use the Prompt
- Use `docs/QA_AGENT_PROMPT.md` as the template for findings
- Fill with concrete file paths/lines and actionable fixes

## Flags to Enable for UI QA
- `NEXT_PUBLIC_SHOW_METRICS_DEBUG=1` — shows MetricsDebugPanel
- `NEXT_PUBLIC_USE_REALTIME_MANAGER=1` — opt‑in for RealtimeManager trial (when available)
- `NEXT_PUBLIC_USE_UNIFIED_CHAT=1` — opt‑in for unified chat reader (when available)

## Suggested Flow
1) Run scanners; skim REPORT and deep_scan.json for hotspots
2) Smoke test UI dashboards and chat flows locally
3) Verify telemetry p95 updates for chat.stream and API categories
4) Write findings using the QA prompt structure and open issues/PR comments

