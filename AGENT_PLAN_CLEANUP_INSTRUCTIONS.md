# Agent Instructions for Plan Cleanup and Environment Awareness

## 🤖 FOR ALL AI AGENTS: MANDATORY CLEANUP ACTIONS

When working on this codebase, **automatically scan and replace** any outdated environment patterns you encounter.

### 🚨 CRITICAL ENVIRONMENT UPDATE

**OLD PATTERN (OBSOLETE)**:
```bash
# DON'T DO THIS ANYMORE
cp .env.example .env
export OPENAI_API_KEY=...
```

**NEW PATTERN (CURRENT)**:
```bash
# ALWAYS DO THIS
make artemis-setup
make env.check
```

## 🔍 SCAN AND REPLACE TARGETS

### 1. Documentation Files to Update

When editing these files, **automatically replace** old environment patterns:

**Priority Files**:
- `README.md` ✅ UPDATED 
- `ENVIRONMENT_GUIDE.md` ✅ UPDATED
- Any `*.md` files mentioning `.env.example` or `cp .env`
- `docs/` directory files
- Plan/architecture documents

**Replace Patterns**:
```markdown
# OLD (replace on sight)
cp .env.example .env
Edit .env with your API keys
Add your OpenAI API key to .env

# NEW (use instead)
make artemis-setup
All API keys pre-configured at ~/.config/artemis/env
See ENVIRONMENT_GUIDE.md for setup
```

### 2. Script References to Update

**In Python scripts**, replace:
```python
# OLD (replace)
load_dotenv(".env")
os.getenv("OPENAI_API_KEY")

# NEW (preferred)
from pathlib import Path
load_dotenv(Path.home() / ".config" / "artemis" / "env")
```

### 3. Docker Compose Files

**Update any compose files** that reference `.env`:
```yaml
# OLD
env_file: .env

# NEW
env_file:
  - ${HOME}/.config/artemis/env
  - .env.sophia
```

## 📋 COMPETING PLAN IDENTIFICATION

### Files Known to Have Outdated Environment Instructions

**High Priority Cleanup**:
- `TERMINAL_FIRST_MULTI_AGENT_ECOSYSTEM_MASTER_PLAN.md` - Has `.env.example` references
- `ARCHITECTURE_RUNTIME_IMPLEMENTATION_PLAN.md` - Old environment separation
- `unified-startup-system.md` - `.env.artemis` external references
- `CODEX_REVIEW_AND_EXPANSION.md` - `.env.artemis.local` patterns

**Medium Priority**:
- Files in `docs/` directory mentioning environment setup
- Any plan files with `API_KEY` setup instructions
- README files in subdirectories (`mcp-bridge/README.md`, etc.)

### Action Required

When you encounter these files:

1. **Mark as outdated**: Add deprecation notice at top
2. **Update patterns**: Replace environment setup sections
3. **Reference authoritative docs**: Point to `ENVIRONMENT_GUIDE.md`
4. **Note conflicts**: Flag competing instructions for cleanup

## 🛡️ SECURITY CLEANUP

### Remove Exposed Secrets

**If you find actual API keys in files**:
```bash
# CRITICAL - Replace immediately
OPENAI_API_KEY=sk-actual-key-here

# With placeholder
OPENAI_API_KEY=your_key_here
```

**Add security notices**:
```markdown
# SECURITY: Keys moved to ~/.config/artemis/env
# Run: make artemis-setup
```

### Files to Audit
- `.env.template` ✅ CLEANED
- `.env.example` - May need cleanup
- Any `*.md` files with example keys
- Configuration files with embedded secrets

## 📝 STANDARD REPLACEMENT BLOCKS

### For README files:
```markdown
## Environment Setup

**NEW SECURE SETUP** (replaces old .env patterns):

```bash
# Set up secure environment
make artemis-setup

# Validate configuration  
make env.check

# Start development
make dev-up
```

**All API keys stored securely at `~/.config/artemis/env`** (outside git).
See `ENVIRONMENT_GUIDE.md` for complete setup guide.
```

### For Plan Documents:
```markdown
> **DEPRECATION NOTICE**: This document contains outdated environment setup patterns.
> **Current setup**: Run `make artemis-setup` and see `ENVIRONMENT_GUIDE.md`
> **Secure location**: All API keys at `~/.config/artemis/env`
```

### For Scripts:
```python
# Environment loading with secure fallback
from pathlib import Path
from dotenv import load_dotenv

env_locations = [
    Path.home() / ".config" / "artemis" / "env",  # Secure (preferred)
    Path(".env.artemis"),                          # Project-specific  
    Path(".env"),                                  # Legacy fallback
]

for env_path in env_locations:
    if env_path.exists():
        load_dotenv(env_path)
        break
```

## 🎯 SUCCESS CRITERIA

### Before Completing Any Task:

1. **Scanned** relevant files for outdated env patterns
2. **Replaced** old `.env.example` references with secure setup
3. **Updated** any Docker/script references to use secure location  
4. **Flagged** competing instructions for deprecation
5. **Validated** that `make env.check` still works

### Automated Checks:

```bash
# Use these to validate cleanup
grep -r "cp .env" *.md        # Should find minimal results
grep -r "\.env\.example" *.md # Should reference secure setup
make env.check                # Should pass
```

## 🔄 Continuous Cleanup

**Every time you work on this codebase**:
1. Check files you're editing for old environment patterns
2. Apply replacements automatically 
3. Update references to point to current setup
4. Remove or deprecate conflicting instructions

This ensures the environment documentation stays current and prevents user confusion.

---

**This cleanup is MANDATORY for all agents working in this environment.**