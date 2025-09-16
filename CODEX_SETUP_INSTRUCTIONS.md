# CODEX COMPLETE SETUP AND GIT SYNC - EXECUTION INSTRUCTIONS

## Overview
This directory contains two powerful tools for completing the full Codex CLI setup, API key configuration, and Git repository synchronization:

1. **`codex_setup_agent_prompt.json`** - Detailed JSON prompt for another AI coding agent
2. **`execute_codex_setup.sh`** - Direct executable bash script

## Quick Start - Immediate Execution

### Option 1: Direct Script Execution (RECOMMENDED)
```bash
# Make script executable (already done)
chmod +x execute_codex_setup.sh

# Execute the complete setup
./execute_codex_setup.sh
```

### Option 2: Manual Command Execution
```bash
# Set the API key and run verification
export OPENAI_API_KEY="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"

# Run original verification script
bash scripts/codex/verify_codex.sh || true
```

## What The Script Does

### STEP 1: IMMEDIATE CODEX VERIFICATION
- ✅ Sets OPENAI_API_KEY in current session
- ✅ Runs `scripts/codex/verify_codex.sh`
- ✅ Confirms Codex CLI is installed and functional

### STEP 2: PERSISTENT KEY SETUP  
- ✅ Adds OPENAI_API_KEY to `~/.zshrc` permanently
- ✅ Sources the updated shell profile
- ✅ Ensures key persists across sessions

### STEP 3: AGGRESSIVE GIT SYNC
- ✅ Fetches all remote branches with `git fetch --all --prune`
- ✅ Switches to main branch
- ✅ Fast-forward pulls from origin/main
- ✅ Cleans up merged branches

### STEP 4: BRANCH AUDIT REPORT
- ✅ Lists all local branches with tracking info
- ✅ Lists all remote branches
- ✅ Identifies unmerged branches
- ✅ Shows commit comparison between branches and main

### STEP 5: PULL REQUEST ANALYSIS
- ✅ Lists open pull requests (if GitHub CLI available)
- ✅ Shows PR status summary
- ✅ Gracefully skips if `gh` not installed

### STEP 6: CODEX FUNCTIONALITY TESTS
- ✅ Tests `npm run codex:chat`
- ✅ Tests `npm run codex:agent`  
- ✅ Tests `npm run codex:review`
- ✅ Continues even if individual tests fail

### STEP 7: CI/CD VERIFICATION
- ✅ Checks for `.github/workflows/codex-review.yml`
- ✅ Displays workflow configuration if present
- ✅ Reports status

### STEP 8: FINAL VERIFICATION REPORT
- ✅ Comprehensive completion report
- ✅ Final run of verification script
- ✅ System status summary

## Using the JSON Agent Prompt

If you prefer to use another AI coding agent (like Aider, Continue, etc.):

```bash
# Copy the prompt content
cat codex_setup_agent_prompt.json

# Or provide the file path to your agent
# The JSON contains detailed execution instructions and error handling
```

## Expected Output

The script will produce colored output with:
- 🔵 **Blue timestamps** for step progress
- ✅ **Green checkmarks** for successful operations  
- ⚠️ **Yellow warnings** for non-critical issues
- ❌ **Red errors** for failures (script continues anyway)

## Verification of Success

After completion, you should see:
- ✅ Codex CLI found and verified
- ✅ OPENAI_API_KEY present and working
- ✅ Main branch synchronized
- ✅ At least one Codex npm script working
- ✅ Comprehensive completion report

## Manual Verification Commands

```bash
# Check Codex installation
which codex
codex --version

# Check API key
echo $OPENAI_API_KEY

# Test Codex functionality  
npm run codex:chat -- -p "test"

# Check Git status
git status
git branch -vv
```

## Troubleshooting

### If Codex CLI Not Found:
```bash
# Install via Homebrew
arch -arm64 brew install codex-cli

# Or via npm
arch -arm64 npm install -g @codex/cli
```

### If API Key Issues:
```bash
# Manually add to shell profile
echo 'export OPENAI_API_KEY="your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### If Git Sync Issues:
```bash
# Force reset to remote main
git fetch origin
git reset --hard origin/main
```

## Files Created

- `codex_setup_agent_prompt.json` - AI agent instructions
- `execute_codex_setup.sh` - Executable setup script  
- `CODEX_SETUP_INSTRUCTIONS.md` - This file
- Log files: `codex_setup_log_YYYYMMDD_HHMMSS.log`

## Security Note

The provided OPENAI_API_KEY is embedded in these files. If sharing this repo:
1. Remove or redact the API key
2. Use environment variables instead
3. Consider using `.env` files with `.gitignore`

## Next Steps After Setup

1. **Test CI Integration**: Create a small PR to trigger the Codex review workflow
2. **Configure .codexrc.yml**: Customize Codex behavior for your project
3. **Integrate with Development Workflow**: Add Codex commands to your regular dev process

---

**MISSION CRITICAL**: This setup ensures Codex CLI is fully functional, API keys are configured, and your Git repository is synchronized. Execute immediately for complete system readiness.
