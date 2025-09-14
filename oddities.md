# Entropy Hunt + Forensic Oddities Audit

Date: 2025-09-14
Scope: Read-only scan of repository at ./
Method: ripgrep-based detectors + targeted grep/git queries (no installs)

## Executive Summary (Top 10)

1) Pulumi ESC files commit plaintext API keys (blocker)
- Why it matters: Immediate credential exposure and third‑party account takeover risk. fn::secret markers don’t protect plaintext in Git.
- Evidence:
  - pulumi-esc-prod.yaml:42: sk-svcacct-… (OpenAI)
  - pulumi-esc-prod.yaml:45: sk-ant-api03-… (Anthropic)
  - pulumi-esc-prod.yaml:48: AIza… (Google)
  - pulumi-esc-prod.yaml:51: gsk_… (Groq)
  - pulumi-esc-prod.yaml:54: sk-… (DeepSeek)
  - pulumi-esc-prod.yaml:63: xai-… (XAI)
  - Command: rg -n -i -S "(AKIA|ASIA|BEGIN RSA|api_key|secret|password|token)" --hidden -g '!**/.git/**'
- Minimal fix: Remove these files from Git immediately; rotate all exposed keys.
- Fuller fix: Keep secrets only in Pulumi ESC/CI secret stores; commit templated configs referencing env vars.

2) Generated artifacts and dependencies checked in (high)
- Why it matters: Supply chain risk, bloat, drift, and confusing source vs. build outputs.
- Evidence:
  - .next/ (Next.js build output) present at repo root
  - backups/ultimate_…/node_modules and .next caches committed
  - .venv and .venv-litellm committed
  - Commands:
    - find . -type f -size +5M -not -path '*/.git/*' | sed -n '1,80p'
    - ls -la | rg -n "^\.next$|^\.venv|backups/.*node_modules"
- Minimal fix: Add to .gitignore; remove from repo history.
- Fuller fix: Store backups outside repo or as tarballs with .gitattributes to exclude.

3) UI code and build outputs in backend repo (policy drift) (high)
- Why it matters: Violates AGENTS.md separation (no UI here), creates cross-import and ownership confusion.
- Evidence:
  - workbench-ui/, webui/, .next/
  - AGENTS.md: “BI UI (Dashboards): External project — NOT in this repo”
  - Command: rg -n "BI UI (Dashboards).*NOT in this repo" AGENTS.md
- Minimal fix: Move UI dirs to separate repo.
- Fuller fix: Add CI guard to block UI paths in this repo.

4) Conflicting env single‑source policy vs. shadow loaders (high)
- Why it matters: Run-to-run config drift and hard-to-reproduce bugs across machines/CI.
- Evidence:
  - ENVIRONMENT.md: “single-source env only: .env.master … Do not use .env.local or ~/.config”
  - setup_config.sh writes .env.local; pulumi-esc-*.yaml includes .env.local.unified; many docs reference ~/.config/sophia/env
  - Commands: rg -n "\.env\.local|~/.config|SOPHIA_REPO_ENV_FILE|single-source env" -S
- Minimal fix: Remove .env.local and ~/.config fallbacks; enforce .env.master only.
- Fuller fix: Preflight check that errors on any alternate loaders; update all docs/scripts.

5) Dangerous eval of config values (med)
- Why it matters: Code execution if config is attacker-controlled (even indirectly via repo edits).
- Evidence:
  - scripts/config_unification.py:756: config_vars[var_name] = eval(var_value)
  - Command: rg -n -S "eval\("
- Minimal fix: Use ast.literal_eval or typed parsers.
- Fuller fix: Centralize config schema with strict types and Zod/Pydantic validators only.

6) Insecure pickle usage (med)
- Why it matters: Loading untrusted pickle enables RCE.
- Evidence:
  - scripts/complete_refactoring.py:84 pickle.load; :90 pickle.dump
  - Command: rg -n -S "pickle"
- Minimal fix: Avoid pickle; switch to JSON/msgpack for trusted data.
- Fuller fix: Only load signed blobs; document provenance and integrity checks.

7) shell=True and pipe-to-shell patterns (med)
- Why it matters: Shell injection risk and brittle scripts.
- Evidence:
  - scripts/agent_manager.py:163 Popen(…, shell=True)
  - scripts/upgrade_tech_stack.sh echoes wget|sh pattern
  - Command: rg -n -S "shell=True|wget\\s+|curl\\s+https?://"
- Minimal fix: Remove shell=True; pass arg lists.
- Fuller fix: Enforce checksums/signatures for any downloaded installers.

8) Hardcoded external endpoints in runtime (med)
- Why it matters: Exfil/accidental calls from tests or dev to prod; fragile infra coupling.
- Evidence:
  - app/api/routers/production.py:128 uses http://104.171.202.103:8080
  - router/top25.py calls https://openrouter.ai
  - Commands: rg -n -S "https?://[A-Za-z0-9._:/%-]+"
- Minimal fix: Gate via config; mock in tests.
- Fuller fix: Centralize endpoints in config with allowlists per env.

9) Missing LICENSE file despite references (med)
- Why it matters: Legal ambiguity for redistribution/contributions.
- Evidence:
  - README.md references LICENSE; no top-level LICENSE found
  - Commands: ls -1 | rg -n "^LICENSE$"; rg -n "MIT License - See"
- Minimal fix: Add correct LICENSE file.
- Fuller fix: Add SPDX headers and third‑party attributions.

10) OS cruft and secrets baseline hygiene (low/med)
- Why it matters: Noise and accidental leakage (
- Evidence:
  - .DS_Store in repo; .secrets.baseline present but plaintext secrets still committed
  - Commands: ls -la | rg -n "\.DS_Store|\.secrets.baseline"
- Minimal fix: Remove .DS_Store; re-run secret scans; prune exceptions.
- Fuller fix: Pre-commit hooks to block binaries/secrets.

---

## Risk Odors Catalog (selected)

- Secrets-in-repo
  - Smell: pulumi-esc-*.yaml with fn::secret plaintext values
  - Fix: purge + rotate + use ESC/CI only
- Generated vs source drift
  - Smell: .next/, node_modules/, .venv* committed
  - Fix: .gitignore + history purge
- Shadow configs
  - Smell: .env.local, ~/.config references vs .env.master policy
  - Fix: remove fallbacks; enforce single source
- Exec/deser hazards
  - Smell: eval(), pickle.load, shell=True
  - Fix: ast.literal_eval / safe formats; remove shell=True
- Hardcoded endpoints
  - Smell: public URLs in code/tests
  - Fix: env/config indirection; mocks in CI

---

## Negative Space List

- No top-level LICENSE file despite references in README/docs
- No CODEOWNERS; unclear module ownership
- No documented rollback plan for secret exposure (despite many scripts)
- CI has health/readiness probes; OK. Tests exist; OK.

---

## Drift Matrix (claims vs reality)

- AGENTS.md: “No UI inside this repo” → workbench-ui/, webui/, .next/ present
- ENVIRONMENT.md: “single-source .env.master; no ~/.config” → setup_config.sh creates .env.local; docs reference ~/.config
- “Centralized secrets” claims → plaintext API keys in pulumi-esc-*.yaml

---

## Commands Run (representative)

- rg --files -S | wc -l
- rg -n "TODO|FIXME|HACK|XXX|TEMP|WIP" -S
- rg -n -i "(remove after|deprecated|legacy|backup)"
- rg -n -S "eval\(|pickle|marshal|subprocess|shell=True|curl\s+https?://|wget\s+|os\.system\("
- rg -n -S "(sleep\(|time\.sleep\(|setTimeout\()"
- rg -n -S "(rand\(|random\.|Math\.random|seed|Date\(|datetime\.now\(|time\.time\()"
- rg -n -S "(SIGTERM|signal|graceful|shutdown)"
- rg -n -S "(DO NOT EDIT|Generated by|autogenerated)"
- rg -n -S "https?://[A-Za-z0-9._:/%-]+"
- git ls-files | sort -f | uniq -d
- find . -type f -size +5M -not -path '*/.git/*'

---

## Quick Wins (entropy cutters)

- Purge pulumi-esc-*.yaml from Git; rotate all credentials (blocker)
- Remove .next/, .venv*, backups/*/node_modules from repo; add to .gitignore
- Delete .env.local scaffolding; standardize on .env.master; update scripts/docs

## Overall Entropy Score

- 73/100 (high): Presence of real secrets in Git and build artifacts in repo are the main drivers; policy drift adds stealth risk.

