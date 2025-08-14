# Roo-only Devtools Normalization

## What Changed
- Updated .roomodes with all 5 modes (added Debugger mode)
- Added safety excludeRegex to all edit groups
- Shipped resilient stdio MCP server for code context
- Added health scripts and one-minute checks
- Added CI tooling smoke workflow
- Removed Continue assets (.continue directory, references in devcontainer.json)
- Normalized .vscode/mcp.json to official schema

## Why
- Simpler, faster, fewer moving parts
- Model choice moved to Roo UI (no hardcoding)
- Better safety with file exclusions
- More resilient MCP with timeouts, retries, and graceful errors

## How to Use
See [docs/roo_code_setup.md](docs/roo_code_setup.md) for details. Quick start:
```bash
bash scripts/mcp/healthcheck.sh
bash scripts/start_all_mcps.sh
bash scripts/stop_all_mcps.sh
```

## Rollback
If needed, revert this single commit:
```bash
git revert ddd3de2
```

