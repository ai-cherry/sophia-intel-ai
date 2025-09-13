# Scripts Directory

This folder contains a small set of essential, maintained scripts. Use `scripts/manifest.py` to generate a quick MANIFEST.json of available scripts with their docstrings.

Essential
- env_doctor.py — Detects env fragmentation, merges to .env.local, validates key formats and service URLs.
- env.sh — Unified shell loader for ~/.config/sophia/env, .env, .env.local.
- audit_scripts.py — Flags scripts that reference Sophia or legacy patterns.
- fragmentation_score.sh — Quick, approximate fragmentation metric.

Monitoring and Enforcement
- check_env_variants.sh — Blocks unauthorized .env* variants.
- check_root_docs.sh — Blocks non-whitelisted root docs.
- check_sophia_paths.sh — Blocks Sophia code paths in Sophia repo.

Utilities
- manifest.py — Emits scripts/MANIFEST.json (name → top-level docstring).

Notes
- Sophia-oriented scripts are removed from this repo and live in ai-cherry/sophia-cli.
- Keep this directory lean (≈10–15 scripts). Propose removals in PRs if a script is no longer needed.

