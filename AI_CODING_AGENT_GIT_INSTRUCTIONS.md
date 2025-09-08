# AI Coding Agent - Sophia Intel AI Repository Instructions

## REPOSITORY-SPECIFIC SETUP
**Target Repository**: https://github.com/ai-cherry/sophia-intel-ai
**SSH URL**: git@github.com:ai-cherry/sophia-intel-ai.git
**Local Directory**: /Users/lynnmusil/sophia-intel-ai
**User**: scoobyjava (musillynn@gmail.com)

## VERIFIED WORKING SSH SETUP ✅
**Status**: SSH authentication is already configured and working!
**SSH Key**: ed25519 key is active and authenticated with GitHub
**User**: scoobyjava (musillynn@gmail.com)

```bash
# Current working SSH connection test
ssh -T git@github.com
# ✅ Returns: "Hi scoobyjava! You've successfully authenticated, but GitHub does not provide shell access."

# Current verified remote URL (SSH-based)
cd /Users/lynnmusil/sophia-intel-ai
git remote -v
# ✅ Shows: origin git@github.com:ai-cherry/sophia-intel-ai.git (fetch)
#          origin git@github.com:ai-cherry/sophia-intel-ai.git (push)

# Current git user configuration (verified working)
git config user.name    # Returns: scoobyjava
git config user.email   # Returns: musillynn@gmail.com
```

## CLI SETUP AND TESTING FOR SOPHIA INTEL AI

### Required CLI Environment Setup:
```bash
# 1. Navigate to Sophia Intel AI directory
cd /Users/lynnmusil/sophia-intel-ai

# 2. Verify SSH authentication is working
ssh -T git@github.com

# 3. Test git credentials
git config user.name
git config user.email
# Should show: scoobyjava and musillynn@gmail.com

# 4. Check MCP servers are configured
ls -la mcp_servers/
ls -la mcp_memory_server/

# 5. Verify no virtual environments in repository
find . -name "*venv*" -o -name "*env*" -o -name "pyvenv.cfg" -type f 2>/dev/null

# 6. Test basic repository health
git status
git remote -v
du -sh .git
```

### MCP Server Integration Test:
```bash
# 1. Check MCP memory server setup
cd /Users/lynnmusil/sophia-intel-ai
ls -la mcp_memory_server/server.py
ls -la mcp_servers/

# 2. Start MCP server via bootstrap (no virtualenvs)
bash scripts/mcp_bootstrap.sh

# 3. Verify embedding and memory systems
ls -la app/memory/
ls -la tmp/ # Should contain embedding caches, not virtual environments

# 4. Test Artemis sidecar connection
ls -la artemis*/
ls -la sophia*/
```

### AI Agent Environment Verification:
```bash
# Test environment for: Grok, Claude Coder, Codex
# ALL work in the SAME environment without creating virtual envs

# 1. Check system Python (recommended approach)
which python3
python3 --version

# 2. Verify no agent-created virtual environments
find /Users/lynnmusil -name "*venv*" -path "*/sophia-intel-ai/*" 2>/dev/null

# 3. Test MCP server accessibility for all agents
python3 -c "
import sys, os
sys.path.append('/Users/lynnmusil/sophia-intel-ai')
print('Sophia AI environment accessible:', os.path.exists('app/'))
print('MCP servers accessible:', os.path.exists('mcp_servers/'))
print('Memory system accessible:', os.path.exists('app/memory/'))
"
```

## CRITICAL GIT REPOSITORY MANAGEMENT RULES

### 1. NEVER CREATE VIRTUAL ENVIRONMENTS IN GIT REPOSITORIES
- **NEVER** run `python -m venv venv`, `python3 -m venv .venv`, `conda create`, or any virtual environment creation commands inside a git repository
- Virtual environments contain thousands of files that will bloat the repository and cause merge conflicts
- Always create virtual environments OUTSIDE the project directory or use global/system Python
- If you must use virtual environments, ensure they are properly listed in `.gitignore`

### 2. SSH AUTHENTICATION SETUP (REQUIRED)

#### Generate SSH Key:
```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
# Press Enter for default location (~/.ssh/id_ed25519)
# Set a passphrase when prompted
```

#### Add SSH Key to SSH Agent:
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

#### Add SSH Key to GitHub:
1. Copy your public key: `cat ~/.ssh/id_ed25519.pub`
2. Go to GitHub Settings → SSH and GPG keys → New SSH key
3. Paste the key and save

#### Test SSH Connection:
```bash
ssh -T git@github.com
# Should return: "Hi username! You've successfully authenticated"
```

### 3. PROPER GIT WORKFLOW

#### Initial Repository Setup:
```bash
# Configure Git (REQUIRED)
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"

# Clone with SSH (NOT HTTPS)
git clone git@github.com:username/repository.git
cd repository

# Verify remote is SSH
git remote -v
# Should show: origin git@github.com:username/repository.git
```

#### Convert HTTPS to SSH (if needed):
```bash
git remote set-url origin git@github.com:username/repository.git
```

#### Daily Workflow:
```bash
# ALWAYS pull before making changes
git pull origin main

# Check status before committing
git status

# Stage files (be selective - don't use 'git add .')
git add specific-files.py

# Commit with descriptive messages
git commit -m "Add specific feature: detailed description"

# Push to GitHub
git push origin main
```

### 4. CRITICAL FILE MANAGEMENT

#### Always Check .gitignore Contains:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environments (CRITICAL)
venv/
.venv/
env/
.env/
ENV/
env.bak/
venv.bak/
.conda/
conda-meta/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment Variables
.env
.env.local
.env.*.local

# Dependencies
node_modules/
package-lock.json (if using yarn)

# Logs
*.log
logs/

# Temporary files
tmp/
temp/
*.tmp
*.temp
```

### 5. BEFORE EVERY CODING SESSION

```bash
# 1. Check current directory
pwd

# 2. Check git status
git status

# 3. Check for virtual environments (THESE SHOULD NOT EXIST)
find . -name "*venv*" -o -name "*env*" -type d 2>/dev/null

# 4. Pull latest changes
git pull origin main

# 5. Check .gitignore exists and is comprehensive
cat .gitignore
```

### 6. MERGE CONFLICT RESOLUTION

When merge conflicts occur:
```bash
# 1. Check what files have conflicts
git status

# 2. For each conflicted file, choose resolution strategy:
# - Accept remote version (usually safer for documentation/config)
git checkout --theirs filename.py
# - Accept local version (if you're sure local is correct)
git checkout --ours filename.py
# - Manually edit to combine both versions

# 3. Add resolved files
git add resolved-file.py

# 4. Complete the merge
git commit -m "Resolve merge conflicts: accept remote/local/combined changes"
```

### 7. REPOSITORY HEALTH CHECKS

#### Daily Health Check:
```bash
# Check repo size (should be reasonable)
du -sh .git

# Check for large files
find . -size +10M -not -path "./.git/*"

# Check for accidentally added virtual environments
find . -name "pyvenv.cfg" -o -name "activate" 2>/dev/null

# Verify SSH authentication
ssh -T git@github.com
```

### 8. EMERGENCY RECOVERY

#### If Virtual Environment Added Accidentally:
```bash
# 1. Remove virtual environment directories
rm -rf venv/ .venv/ env/ .env/

# 2. Update .gitignore
echo -e "\n# Virtual Environments\nvenv/\n.venv/\nenv/\n.env/" >> .gitignore

# 3. Stage changes
git add .gitignore
git add -u  # This stages deletions

# 4. Commit
git commit -m "Remove virtual environment and update .gitignore"
```

#### If Repository Becomes Corrupted:
```bash
# 1. Backup current work
cp -r important-files/ /tmp/backup/

# 2. Fresh clone
cd ..
rm -rf problematic-repo/
git clone git@github.com:username/repository.git
cd repository

# 3. Restore work
cp -r /tmp/backup/* .
```

### 9. CODING AGENT SPECIFIC RULES

#### Before Executing ANY Command:
1. **Check current working directory**: `pwd`
2. **Verify you're in the correct repository**
3. **Check git status**: `git status`
4. **Never assume file locations or repository state**

#### When Installing Dependencies:
```bash
# WRONG - Don't create virtual environments in repo
python -m venv venv  # NEVER DO THIS

# RIGHT - Use system Python or external virtual env
pip install package-name
# OR create venv outside repo:
cd /tmp && python -m venv my-project-env
source /tmp/my-project-env/bin/activate
cd /path/to/project
```

#### When Making Changes:
1. **Always pull first**: `git pull origin main`
2. **Make targeted commits**: Don't commit everything at once
3. **Write descriptive commit messages**
4. **Test before pushing**

#### Repository Awareness:
- **Check file sizes** before adding to git
- **Review .gitignore** before first commit
- **Verify SSH authentication** before pushing
- **Monitor repository health** regularly

### 10. SUCCESS INDICATORS

✅ SSH authentication working (`ssh -T git@github.com` succeeds)
✅ No virtual environments in repository
✅ Comprehensive .gitignore in place
✅ Git user credentials configured
✅ Regular successful pushes without conflicts
✅ Repository size remains reasonable (< 100MB typically)
✅ No accidentally committed large files or dependencies
✅ Clean `git status` after commits

### 11. FAILURE INDICATORS (STOP AND FIX)

❌ HTTPS authentication failures
❌ Virtual environment directories in repo
❌ Missing or incomplete .gitignore
❌ Frequent merge conflicts
❌ Repository size growing rapidly
❌ Accidentally committed node_modules/, __pycache__/, or similar
❌ Git commands failing or behaving unexpectedly

---

## SUMMARY FOR AI AGENTS

**YOU ARE AN AI CODING AGENT. FOLLOW THESE RULES RELIGIOUSLY:**

1. **NEVER CREATE VIRTUAL ENVIRONMENTS IN GIT REPOSITORIES**
2. **ALWAYS USE SSH AUTHENTICATION** (git@github.com URLs)
3. **ALWAYS PULL BEFORE MAKING CHANGES** (`git pull origin main`)
4. **CHECK .gitignore IS COMPREHENSIVE** before first commit
5. **MAKE TARGETED, DESCRIPTIVE COMMITS** with clear messages
6. **VERIFY REPOSITORY HEALTH** regularly
7. **WHEN IN DOUBT, ASK FOR CLARIFICATION** rather than potentially corrupting the repository

**REMEMBER**: A corrupted git repository can destroy days or weeks of work. Be cautious, methodical, and always prioritize repository integrity over speed.
