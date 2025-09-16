# CODEX COMPLETE SETUP AND GIT SYNC - EXECUTION INSTRUCTIONS

## Overview
This directory contains two tools for completing the Codex CLI setup, API key configuration, and Git repository synchronization:

1. `codex_setup_agent_prompt.json` — Detailed JSON prompt for another AI coding agent
2. `execute_codex_setup.sh` — Direct executable bash script

## Quick Start — Immediate Execution

### Option 1: Direct Script Execution (RECOMMENDED)
```
chmod +x codex-setup/execute_codex_setup.sh
./codex-setup/execute_codex_setup.sh
```

### Option 2: Manual Command Execution
```
# Set the API key and run verification
export OPENAI_API_KEY="<YOUR-OPENAI-API-KEY>"
bash scripts/codex/verify_codex.sh || true
```

## What The Script Does

### STEP 1: IMMEDIATE CODEX VERIFICATION
- Sets OPENAI_API_KEY in current session (if provided)
- Runs `scripts/codex/verify_codex.sh`
- Confirms Codex CLI binary and basic functionality

### STEP 2: PERSISTENT KEY SETUP
- Adds OPENAI_API_KEY to `~/.zshrc`
- Sources the updated shell profile
- Ensures key persists across sessions

### STEP 3: AGGRESSIVE GIT SYNC
- Fetches all remotes with prune
- Switches to `main` (or `master` if not present)
- Fast-forward pulls from origin
- Cleans up merged local branches

### STEP 4: BRANCH AUDIT REPORT
- Lists all local branches with tracking info
- Lists remote branches
- Identifies unmerged branches
- Shows ahead/behind status vs upstream

### STEP 5: PULL REQUEST ANALYSIS
- Lists open PRs (if GitHub CLI `gh` is available)
- Shows PR status summary
- Gracefully skips if `gh` is not installed

### STEP 6: CODEX FUNCTIONALITY TESTS
- Tests `npm run codex:chat`
- Tests `npm run codex:agent`
- Tests `npm run codex:review`
- Continues even if individual tests fail

### STEP 7: CI/CD VERIFICATION
- Checks for `.github/workflows/codex-review.yml`
- Displays workflow configuration if present

### STEP 8: FINAL VERIFICATION REPORT
- Comprehensive completion report
- Final run of verification script
- System status summary

## Using the JSON Agent Prompt

If you prefer to use another AI coding agent (Aider, Continue, etc.):

```
cat codex-setup/codex_setup_agent_prompt.json
```

The JSON contains structured execution instructions and error handling guidance.

## Expected Output

The script produces colored output with:
- Blue timestamps for step progress
- Green checkmarks for successes
- Yellow warnings for non-critical issues
- Red errors for failures (script continues where reasonable)

## Verification of Success

After completion, you should see:
- Codex CLI found and verified
- OPENAI_API_KEY present and working
- Main branch synchronized
- At least one Codex npm script working
- Completion report with a log file path

## Manual Verification Commands

```
which codex
codex --version
echo $OPENAI_API_KEY
npm run codex:chat -- -p "test"
git status
git branch -vv
```

## Troubleshooting

### If Codex CLI Not Found
```
arch -arm64 brew install codex-cli
# or
arch -arm64 npm install -g @codex/cli
```

### If API Key Issues
```
echo 'export OPENAI_API_KEY="<YOUR-OPENAI-API-KEY>"' >> ~/.zshrc
source ~/.zshrc
```

### If Git Sync Issues
```
git fetch origin
git reset --hard origin/main
```

## Files Created

- `codex-setup/codex_setup_agent_prompt.json`
- `codex-setup/execute_codex_setup.sh`
- `codex-setup/CODEX_SETUP_INSTRUCTIONS.md` (this file)
- Log files: `codex_setup_log_YYYYMMDD_HHMMSS.log` (repo root)

## Security Note

- Do not commit API keys to version control. Use environment variables or CI secrets.
- If you plan to share this repository, redact any keys from logs and shell profiles.

## Next Steps After Setup

1. Create a small PR to trigger the Codex review workflow
2. Optionally customize `~/.codexrc.yml` using `.codexrc.yml.example`
3. Integrate Codex into your routine via the provided npm scripts

