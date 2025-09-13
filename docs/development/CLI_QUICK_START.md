# 🚀 Sophia Intel AI - CLI Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Run the Setup Script (30 seconds)
```bash
cd ~/sophia-intel-ai
chmod +x setup_unified_cli_complete.sh
./setup_unified_cli_complete.sh
```

### Step 2: Add Your API Keys (2 minutes)
```bash
# Edit the environment file
./bin/keys edit  # edits <repo>/.env.master (chmod 600)

# Add these two required keys:
export OPENAI_API_KEY="sk-..."        # For Codex
export ANTHROPIC_API_KEY="sk-ant-..." # For Claude
```

### Step 3: Reload Your Shell (10 seconds)
```bash
source ~/.zshrc
```

### Step 4: Validate Setup (30 seconds)
```bash
sophia-cli validate
```

### Step 5: Test It! (1 minute)
```bash
# Plan a feature
sophia-cli plan "Create a user authentication endpoint"

# Implement code
sophia-cli implement "Add POST /api/auth/login endpoint with JWT"
```

## 🎯 Daily Workflow Commands

### Quick Aliases (Already Set Up!)
```bash
splan <task>   # Plan a feature
simpl <task>   # Implement code  
sval           # Validate setup
```

### Examples for Common Tasks

#### Backend Development
```bash
# Plan an API endpoint
splan "Design REST API for user management with CRUD operations"

# Implement with tests
simpl "Create POST /api/users endpoint with validation and tests"

# Refactor existing code
simpl "Refactor database connection pool for better performance"
```

#### Frontend Development
```bash
# Plan a React component
splan "Design responsive dashboard component with real-time updates"

# Implement the component
simpl "Create Dashboard.tsx with TypeScript and Material-UI"

# Add tests
simpl "Write unit tests for Dashboard component using Jest"
```

#### Security & Performance
```bash
# Security audit
sophia-claude plan "Audit authentication system for vulnerabilities"

# Performance optimization
sophia-codex implement "Optimize database queries in user service"
```

## 📊 30-Minute Productivity Session

### Morning Routine (5 minutes)
```bash
# Start your day
sophia-daily  # Runs startup checks

# Check what needs work
git status
sophia-cli validate
```

### Development Sprint (20 minutes)
```bash
# 1. Plan your feature (2 min)
splan "Today's main task description"

# 2. Implement iteratively (15 min)
simpl "First part of implementation"
simpl "Second part with tests"
simpl "Final touches and optimization"

# 3. Validate your work (3 min)
npm test  # or pytest
git diff  # Review changes
```

### Wrap Up (5 minutes)
```bash
# Commit your work
git add -A
git commit -m "feat: completed feature X"
git push origin feature-branch

# Plan tomorrow
splan "Tomorrow's priority task" > ~/work/tomorrow.md
```

## 🧠 Smart CLI Features

### Automatic Provider Selection
The CLI automatically chooses the best tool:
- **Simple tasks** → Codex (fast)
- **Complex tasks** → Claude (thorough)

```bash
# These automatically route to Codex (fast):
simpl "Fix typo in README"
simpl "Update import statements"

# These automatically route to Claude (thorough):
splan "Design microservices architecture"
splan "Security audit for payment system"
```

### Override Provider When Needed
```bash
# Force Codex for speed
CLI_PROVIDER=codex sophia-cli plan "Complex task but need it fast"

# Force Claude for thoroughness
CLI_PROVIDER=claude sophia-cli implement "Simple task but need quality"
```

## 🛠️ Troubleshooting

### If CLIs Are Not Found
```bash
# Install Codex
brew install codex

# Install Claude
curl -fsSL https://claude.ai/install.sh | bash
```

### If Commands Don't Work
```bash
# Check your PATH
echo $PATH | grep sophia-intel-ai

# Manually add to PATH if needed
export PATH="$HOME/sophia-intel-ai/bin:$PATH"
```

### If API Keys Don't Work
```bash
# Verify keys are loaded
echo $OPENAI_API_KEY | head -c 10
echo $ANTHROPIC_API_KEY | head -c 10

# Re-source environment
./sophia start  # loads <repo>/.env.master and exports to child processes
```

## 💡 Pro Tips

### 1. Use Personas for Specialized Tasks
```bash
# TypeScript development
sophia-cli plan "Component using TypeScript persona" \
  --persona typescript_specialist

# Python backend
sophia-cli implement "FastAPI endpoint" \
  --persona python_backend
```

### 2. Chain Commands for Complex Workflows
```bash
# Plan → Implement → Test → Document
splan "Feature X" && \
simpl "Based on plan above" && \
simpl "Add comprehensive tests" && \
simpl "Update documentation"
```

### 3. Save Common Patterns
```bash
# Create reusable templates
echo "Create CRUD endpoints for {model}" > ~/.config/sophia/templates/crud.txt

# Use template
splan "$(cat ~/.config/sophia/templates/crud.txt | sed 's/{model}/User/g')"
```

### 4. Track Your Productivity
```bash
# Log your commands
sophia-cli plan "Feature Y" | tee -a ~/work/$(date +%Y%m%d).log

# Review what you built today
grep "IMPLEMENT\|PLAN" ~/work/$(date +%Y%m%d).log
```

## 🎯 What to Build First

Start with these to test the system:

1. **Simple API Endpoint** (5 min)
   ```bash
   splan "GET /api/health endpoint"
   simpl "Implement health check with status response"
   ```

2. **Database Model** (10 min)
   ```bash
   splan "User model with authentication fields"
   simpl "Create User model with Prisma/SQLAlchemy"
   ```

3. **React Component** (10 min)
   ```bash
   splan "Login form component"
   simpl "Create LoginForm.tsx with validation"
   ```

4. **Test Suite** (5 min)
   ```bash
   simpl "Unit tests for User model"
   simpl "Integration tests for auth endpoints"
   ```

## 🚀 You're Ready!

You now have:
- ✅ Unified CLI for both Codex and Claude
- ✅ Intelligent task routing
- ✅ Production-ready personas
- ✅ Zero-config workflow
- ✅ All tools at your fingertips

**Start building with:** `sophia-cli plan "Your first awesome feature"`

---

*Need help? Run `sophia-cli help` or check `~/sophia-intel-ai/CLI_UNIFIED_IMPLEMENTATION_MASTER_PLAN.md`*
