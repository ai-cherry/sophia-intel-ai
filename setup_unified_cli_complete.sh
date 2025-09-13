#!/bin/bash
# Sophia Intel AI - Complete Unified CLI Setup Script
# This script sets up the entire CLI infrastructure in one go

set -euo pipefail

echo "🚀 Sophia Intel AI - Unified CLI Complete Setup"
echo "================================================"

REPO_ROOT="$HOME/sophia-intel-ai"
CONFIG_ROOT="$HOME/.config/sophia"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Create directory structure
echo ""
echo "📁 Creating directory structure..."

mkdir -p "$CONFIG_ROOT"/{personas,workflows,cache,sessions,logs}
mkdir -p "$HOME/.config/codex/personas"
mkdir -p "$HOME/.config/claude/personas"
mkdir -p "$REPO_ROOT"/{configs/agents,bin,scripts/cli}

# Set proper permissions
chmod 700 "$CONFIG_ROOT"
chmod 700 "$HOME/.config/codex" 2>/dev/null || true
chmod 700 "$HOME/.config/claude" 2>/dev/null || true

log_success "Directory structure created"

# Step 2: Create Master Architect Persona
echo ""
echo "🧠 Creating Master Architect persona..."

cat > "$REPO_ROOT/configs/agents/master_architect.md" << 'EOF'
You are the Master Architect for Sophia Intel AI. Your role is to design first, implement surgically, and leave zero tech debt.

## Core Principles
- **Plan → Implement → Validate → Document** - Always in this order
- **Zero Tech Debt** - Every line of code must be production-ready
- **Minimal Surface Area** - Small, focused changes only
- **Test-First** - Write tests before implementation

## Sophia-Specific Rules
- All configuration in `~/.config/sophia/env`
- No cross-repo imports between sophia-intel-app and builder-agno-system
- All dashboards must be in sophia-intel-app (port 3000)
- Unified API always on port 8000
- MCP services on ports 8081, 8082, 8084
- Update AGENTS.md for any architectural changes

## Task Execution Format
For every task, provide:
1. **Assumptions & Scope** - What we're building and why
2. **Architecture** - Design with rationale
3. **Interface Contracts** - APIs, data shapes, types
4. **Implementation Plan** - Step-by-step with checkpoints
5. **Tests** - Unit and integration test cases
6. **Validation** - Commands to verify success
7. **Documentation** - Update relevant docs
8. **Rollback Plan** - How to undo if needed

## Quality Gates
- ✅ Tests pass with >80% coverage
- ✅ No hardcoded secrets or credentials
- ✅ Follows existing code patterns
- ✅ Updates documentation
- ✅ Includes rollback plan

## Output Standards
- Use unified diffs for code changes
- Include file paths in backticks
- Provide exact commands to run
- Show expected output for validation
EOF

# Symlink to CLI config directories
ln -sf "$REPO_ROOT/configs/agents/master_architect.md" "$HOME/.config/codex/personas/master-architect.txt" 2>/dev/null || true
ln -sf "$REPO_ROOT/configs/agents/master_architect.md" "$HOME/.config/claude/personas/master-architect.txt" 2>/dev/null || true

log_success "Master Architect persona created and linked"

# Step 3: Create Unified CLI Wrapper
echo ""
echo "🔧 Creating unified CLI wrapper..."

cat > "$REPO_ROOT/bin/sophia-cli" << 'EOF'
#!/usr/bin/env zsh
# Sophia Intel AI - Unified CLI Wrapper
# Intelligently routes between Codex and Claude based on task complexity

set -euo pipefail

# Load environment from centralized location
[[ -f "$HOME/.config/sophia/env" ]] && source "$HOME/.config/sophia/env"

# Configuration
REPO_ROOT="$HOME/sophia-intel-ai"
PERSONA_FILE="$REPO_ROOT/configs/agents/master_architect.md"
DEFAULT_PROVIDER="${CLI_PROVIDER:-claude}"
DEFAULT_MODEL="${CLI_MODEL:-claude-3-5-sonnet-20240620}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Task routing logic
route_task() {
    local task="$1"
    local complexity=$(analyze_complexity "$task")
    
    if [[ "$complexity" == "simple" ]]; then
        echo "codex"
    elif [[ "$complexity" == "complex" ]]; then
        echo "claude"
    else
        echo "$DEFAULT_PROVIDER"
    fi
}

analyze_complexity() {
    local task="$1"
    
    # Simple heuristics for task complexity
    if echo "$task" | grep -qE "(refactor|optimize|quick|simple|fix|update)"; then
        echo "simple"
    elif echo "$task" | grep -qE "(architect|design|complex|security|analyze|plan)"; then
        echo "complex"
    else
        echo "moderate"
    fi
}

# Main execution
ACTION="${1:-help}"
shift || true

case "$ACTION" in
    plan)
        TASK="$*"
        PROVIDER=$(route_task "$TASK")
        
        echo -e "${BLUE}🧠 Using $PROVIDER for planning...${NC}"
        
        if [[ "$PROVIDER" == "codex" ]]; then
            if command -v codex >/dev/null 2>&1; then
                codex --system-prompt "$(cat $PERSONA_FILE)" \
                      --model "${CODEX_MODEL:-gpt-4o}" \
                      "PLAN: $TASK"
            else
                echo -e "${RED}Codex CLI not found. Install with: brew install codex${NC}"
                exit 1
            fi
        else
            if command -v claude >/dev/null 2>&1; then
                claude --append-system-prompt "$(cat $PERSONA_FILE)" \
                       --model "$DEFAULT_MODEL" \
                       -p "PLAN: $TASK"
            else
                echo -e "${RED}Claude CLI not found. Install from: https://claude.ai/download${NC}"
                exit 1
            fi
        fi
        ;;
        
    implement|impl)
        TASK="$*"
        PROVIDER=$(route_task "$TASK")
        
        echo -e "${BLUE}⚡ Using $PROVIDER for implementation...${NC}"
        
        if [[ "$PROVIDER" == "codex" ]]; then
            if command -v codex >/dev/null 2>&1; then
                codex --system-prompt "$(cat $PERSONA_FILE)" \
                      --model "${CODEX_MODEL:-gpt-4o}" \
                      "IMPLEMENT: $TASK. Output unified diff and tests."
            else
                echo -e "${RED}Codex CLI not found. Install with: brew install codex${NC}"
                exit 1
            fi
        else
            if command -v claude >/dev/null 2>&1; then
                claude --append-system-prompt "$(cat $PERSONA_FILE)" \
                       --model "$DEFAULT_MODEL" \
                       -p "IMPLEMENT: $TASK. Output unified diff and tests."
            else
                echo -e "${RED}Claude CLI not found. Install from: https://claude.ai/download${NC}"
                exit 1
            fi
        fi
        ;;
        
    validate|val)
        # Run validation suite
        echo -e "${BLUE}🔍 Running validation suite...${NC}"
        echo ""
        
        # Check configuration
        echo "Configuration:"
        [[ -f "$HOME/.config/sophia/env" ]] && echo -e "${GREEN}✅ Environment configured${NC}" || echo -e "${RED}❌ Environment not configured${NC}"
        [[ -f "$PERSONA_FILE" ]] && echo -e "${GREEN}✅ Persona file exists${NC}" || echo -e "${RED}❌ Persona file missing${NC}"
        
        echo ""
        echo "CLI Availability:"
        # Check CLI availability
        command -v codex >/dev/null 2>&1 && echo -e "${GREEN}✅ Codex CLI available${NC}" || echo -e "${YELLOW}⚠️  Codex CLI not found${NC}"
        command -v claude >/dev/null 2>&1 && echo -e "${GREEN}✅ Claude CLI available${NC}" || echo -e "${YELLOW}⚠️  Claude CLI not found${NC}"
        command -v grok >/dev/null 2>&1 && echo -e "${GREEN}✅ Grok CLI available${NC}" || echo -e "${YELLOW}⚠️  Grok CLI not found${NC}"
        command -v deepseek >/dev/null 2>&1 && echo -e "${GREEN}✅ DeepSeek CLI available${NC}" || echo -e "${YELLOW}⚠️  DeepSeek CLI not found${NC}"
        
        echo ""
        echo "MCP Services:"
        # Check MCP services
        curl -s http://localhost:8081/health >/dev/null 2>&1 && echo -e "${GREEN}✅ MCP Memory service running${NC}" || echo -e "${YELLOW}⚠️  MCP Memory service not running${NC}"
        curl -s http://localhost:8082/health >/dev/null 2>&1 && echo -e "${GREEN}✅ MCP Filesystem service running${NC}" || echo -e "${YELLOW}⚠️  MCP Filesystem service not running${NC}"
        curl -s http://localhost:8084/health >/dev/null 2>&1 && echo -e "${GREEN}✅ MCP Git service running${NC}" || echo -e "${YELLOW}⚠️  MCP Git service not running${NC}"
        curl -s http://localhost:8000/api/health >/dev/null 2>&1 && echo -e "${GREEN}✅ Unified API running${NC}" || echo -e "${YELLOW}⚠️  Unified API not running${NC}"
        ;;
        
    help|*)
        cat << HELP
${BLUE}Sophia Unified CLI - Intelligent Development Assistant${NC}

Usage:
  sophia-cli plan <task>       - Create a plan for the task
  sophia-cli implement <task>  - Implement based on plan
  sophia-cli validate          - Validate system configuration
  sophia-cli help             - Show this help message

Shortcuts:
  sophia-cli impl <task>      - Alias for implement
  sophia-cli val              - Alias for validate

Environment Variables:
  CLI_PROVIDER  - Default provider (claude|codex)
  CLI_MODEL     - Default model to use
  CODEX_MODEL   - Specific model for Codex

Examples:
  sophia-cli plan "Add user authentication endpoint"
  sophia-cli implement "Refactor database connections for better performance"
  sophia-cli validate

Provider Selection:
  - Simple tasks (refactor, fix, update) → Codex (fast)
  - Complex tasks (architect, design, analyze) → Claude (thorough)
  - Override with: CLI_PROVIDER=codex sophia-cli plan "task"
HELP
        ;;
esac
EOF

chmod +x "$REPO_ROOT/bin/sophia-cli"
log_success "Unified CLI wrapper created"

# Step 4: Create environment template
echo ""
echo "🔐 Creating environment template..."

cat > "$CONFIG_ROOT/env.template" << 'EOF'
# Sophia Intel AI - Environment Configuration
# Copy this to ~/.config/sophia/env and fill in your API keys
# NEVER commit this file to the repository

# API Keys (Required)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: Other API Keys
export GROQ_API_KEY=""
export DEEPSEEK_API_KEY=""

# MCP Configuration
export MCP_TOKEN="your-secure-token-here"
export MCP_MEMORY_PORT=8081
export MCP_FILESYSTEM_PORT=8082
export MCP_GIT_PORT=8084

# Sophia Configuration
export SOPHIA_API_PORT=8000
export SOPHIA_UI_PORT=3000
export SOPHIA_ENV=development

# CLI Preferences
export CLI_PROVIDER=claude  # or codex
export CLI_MODEL=claude-3-5-sonnet-20240620
export CODEX_MODEL=gpt-4o
export CLI_TEMPERATURE=0.2
export CLI_MAX_TOKENS=4096

# Logging
export CLI_LOG_LEVEL=info
export CLI_LOG_FILE="$HOME/.config/sophia/logs/cli.log"
EOF

# Check if env file already exists
if [[ ! -f "$CONFIG_ROOT/env" ]]; then
    cp "$CONFIG_ROOT/env.template" "$CONFIG_ROOT/env"
    log_warning "Environment file created at $CONFIG_ROOT/env - Please add your API keys"
else
    log_success "Environment file already exists"
fi

# Step 5: Create specialized personas
echo ""
echo "👥 Creating specialized personas..."

# TypeScript Specialist
cat > "$CONFIG_ROOT/personas/typescript_specialist.md" << 'EOF'
You are a TypeScript specialist for a monorepo with React/Next.js frontend and Node.js backend.

## Expertise Areas
- TypeScript 5.x with strict mode
- React 18+ with hooks and suspense
- Next.js 14+ App Router
- Node.js with Express/Fastify
- Prisma ORM with PostgreSQL

## Code Standards
- Use functional components with TypeScript
- Implement proper error boundaries
- Use Zod for runtime validation
- Follow Airbnb style guide
- Minimum 80% test coverage

## Patterns to Follow
- Repository pattern for data access
- Service layer for business logic
- DTO pattern for API contracts
- Error-first callbacks
- Async/await over promises
EOF

# Python Backend Engineer
cat > "$CONFIG_ROOT/personas/python_backend.md" << 'EOF'
You are a Python backend specialist focusing on FastAPI and async patterns.

## Expertise Areas
- Python 3.11+ with type hints
- FastAPI with Pydantic v2
- SQLAlchemy 2.0 with async support
- Redis for caching
- Celery for background tasks

## Code Standards
- Follow PEP 8 and PEP 484
- Use Black formatter
- Implement comprehensive logging
- Write docstrings for all functions
- Use dependency injection

## Patterns to Follow
- Domain-driven design
- CQRS where appropriate
- Event sourcing for audit trails
- Circuit breaker for external services
- Rate limiting on all endpoints
EOF

# Security Auditor
cat > "$CONFIG_ROOT/personas/security_auditor.md" << 'EOF'
You are a security auditor specializing in application and infrastructure security.

## Focus Areas
- OWASP Top 10 vulnerabilities
- Authentication and authorization
- Data encryption at rest and in transit
- Secret management
- Dependency scanning

## Security Checklist
- [ ] No hardcoded secrets
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF tokens implemented
- [ ] Rate limiting enabled
- [ ] Audit logging configured
- [ ] Secure headers set

## Tools to Use
- Snyk for dependency scanning
- OWASP ZAP for penetration testing
- GitLeaks for secret scanning
- Trivy for container scanning
EOF

log_success "Specialized personas created"

# Step 6: Create helper scripts
echo ""
echo "📜 Creating helper scripts..."

# Daily startup script
cat > "$REPO_ROOT/scripts/cli/daily_startup.sh" << 'EOF'
#!/bin/bash
# Sophia Daily Startup Script

echo "🚀 Starting Sophia Daily Workflow"
echo "=================================="

# 1. Validate environment
echo "📋 Validating environment..."
sophia-cli validate

# 2. Check for updates
echo "🔄 Checking for updates..."
cd ~/sophia-intel-ai
git fetch origin
git status --short

# 3. Display ready message
echo ""
echo "✅ System ready for development!"
echo "Quick commands:"
echo "  sophia-cli plan <task>     - Plan a feature"
echo "  sophia-cli impl <task>     - Implement code"
echo "  sophia-cli val             - Validate setup"
EOF

chmod +x "$REPO_ROOT/scripts/cli/daily_startup.sh"

log_success "Helper scripts created"

# Step 7: Update shell configuration
echo ""
echo "🐚 Updating shell configuration..."

ZSHRC_MARKER="# Sophia CLI Configuration"
if ! grep -q "$ZSHRC_MARKER" "$HOME/.zshrc" 2>/dev/null; then
    cat >> "$HOME/.zshrc" << 'EOF'

# Sophia CLI Configuration
export PATH="$HOME/sophia-intel-ai/bin:$PATH"

# Load Sophia environment
[[ -f "$HOME/.config/sophia/env" ]] && source "$HOME/.config/sophia/env"

# Prevent API key leakage in history
setopt histignorespace

# CLI Aliases
alias splan='sophia-cli plan'
alias simpl='sophia-cli implement'
alias sval='sophia-cli validate'

# Quick access to different providers
alias sophia-codex='CLI_PROVIDER=codex sophia-cli'
alias sophia-claude='CLI_PROVIDER=claude sophia-cli'

# Development shortcuts
alias sophia-dev='cd ~/sophia-intel-ai && sophia-cli validate'
alias sophia-logs='tail -f ~/.config/sophia/logs/cli.log'
alias sophia-daily='~/sophia-intel-ai/scripts/cli/daily_startup.sh'
EOF
    log_success "Shell configuration updated"
else
    log_success "Shell configuration already contains Sophia CLI setup"
fi

# Final summary
echo ""
echo "=========================================="
echo -e "${GREEN}✨ Sophia Unified CLI Setup Complete! ✨${NC}"
echo "=========================================="
echo ""
echo "📝 Next Steps:"
echo "1. Add your API keys to: $CONFIG_ROOT/env"
echo "   - OPENAI_API_KEY for Codex"
echo "   - ANTHROPIC_API_KEY for Claude"
echo ""
echo "2. Reload your shell configuration:"
echo "   source ~/.zshrc"
echo ""
echo "3. Test the setup:"
echo "   sophia-cli validate"
echo ""
echo "4. Try your first command:"
echo "   sophia-cli plan \"Create a simple REST endpoint\""
echo ""
echo "Quick Commands:"
echo "  splan <task>  - Plan a feature"
echo "  simpl <task>  - Implement code"
echo "  sval          - Validate setup"
echo ""
echo "Happy coding! 🚀"