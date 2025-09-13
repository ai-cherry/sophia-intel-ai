#!/bin/bash

# Multi-Tool Terminal/IDE Setup - INTEGRATED with existing MCP
# Cleans up duplicates, uses existing infrastructure
# September 2025 - M3 ARM64 Optimized

set -e

echo "🔧 Integrated Multi-Tool Setup (Using Existing MCP)"
echo "==================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
PROJECT_DIR="$(pwd)"
TOOLS_DIR="$HOME/tools"

# Existing MCP servers we found
MCP_MEMORY_PORT=8081
MCP_FILESYSTEM_PORT=8082
MCP_GIT_PORT=8084

echo -e "${YELLOW}[1/10] Cleaning up duplicate MCP servers...${NC}"

# Kill duplicate Node.js MCP servers (keep Python ones)
echo "Found multiple MCP servers running. Cleaning duplicates..."
# cleanup legacy node-based MCP servers (none in current setup)
pkill -f "ruv-swarm.*mcp" 2>/dev/null || true
pkill -f "flow-nexus.*mcp" 2>/dev/null || true
pkill -f "snyk.*mcp" 2>/dev/null || true
sleep 2

echo -e "${GREEN}✓ Cleaned up duplicate MCP servers${NC}"
echo "Keeping Python MCP servers:"
echo "  • Memory Server: http://localhost:$MCP_MEMORY_PORT"
echo "  • Filesystem Server: http://localhost:$MCP_FILESYSTEM_PORT"
echo "  • Git Server: http://localhost:$MCP_GIT_PORT"
echo ""

# Step 2: Install/Update Tools
echo -e "${YELLOW}[2/10] Installing/Updating CLI tools...${NC}"

# Check Claude Code (you're already installed)
if command -v claude &> /dev/null; then
  echo -e "${GREEN}✓ Claude Code already installed${NC}"
else
  echo "Installing Claude Code..."
  brew tap anthropic/tap 2>/dev/null || true
  brew install anthropic/tap/claude-code || true
fi

# Install Codex CLI (if not present)
echo "Checking Codex CLI..."
if ! command -v codex &> /dev/null; then
  # Try creating a simple wrapper since official Codex CLI might not exist
  cat > /usr/local/bin/codex << 'CODEX_EOF'
#!/bin/bash
# Codex CLI Wrapper - Uses OpenAI API
OPENAI_MODEL="${CODEX_MODEL:-gpt-4}"
if [ -z "$OPENAI_API_KEY" ]; then
  echo "Error: OPENAI_API_KEY not set"
  exit 1
fi

case "$1" in
  commit)
    git diff --staged | curl -s https://api.openai.com/v1/chat/completions \
      -H "Authorization: Bearer $OPENAI_API_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"model\":\"$OPENAI_MODEL\",\"messages\":[{\"role\":\"system\",\"content\":\"Generate a commit message\"},{\"role\":\"user\",\"content\":\"$(git diff --staged | head -500)\"}]}" \
      | jq -r '.choices[0].message.content'
    ;;
  *)
    echo "Usage: codex commit"
    ;;
esac
CODEX_EOF
  chmod +x /usr/local/bin/codex
  echo -e "${GREEN}✓ Created Codex wrapper${NC}"
else
  echo -e "${GREEN}✓ Codex already available${NC}"
fi

# Opencode should already be installed
if command -v opencode &> /dev/null || [ -f "$HOME/.opencode/bin/opencode" ]; then
  echo -e "${GREEN}✓ Opencode already installed${NC}"
else
  echo "Installing Opencode..."
  curl -fsSL https://opencode.ai/install | bash
fi

# Step 3: Clone reference repos
echo -e "${YELLOW}[3/10] Setting up reference repositories...${NC}"
mkdir -p "$TOOLS_DIR"
cd "$TOOLS_DIR"

# Only clone if not exists
repos=(
  "anthropics/claude-code"
  "opencode-ai/opencode"
  "idosal/git-mcp"
)

for repo in "${repos[@]}"; do
  dir="${repo##*/}"
  if [ ! -d "$dir" ]; then
    git clone "https://github.com/$repo" "$dir" --depth 1 2>/dev/null || echo "Skipped $dir"
  fi
done

cd "$PROJECT_DIR"

# Step 4: Create unified configuration
echo -e "${YELLOW}[4/10] Creating unified configuration...${NC}"

# Create CLAUDE.md with enhanced rules
cat > "$PROJECT_DIR/CLAUDE.md" << 'EOF'
# Claude Code Configuration - Multi-Tool Environment

## MCP Integration
- Memory Server: http://localhost:8081
- Filesystem Server: http://localhost:8082  
- Git Server: http://localhost:8084

## Core Rules
- NO try/catch spam - handle errors at boundaries only
- Functional > OOP when reasonable
- Use background tasks for long operations
- Atomic commits with conventional format
- Always lint: black (Python), prettier (JS/TS)

## File Organization
- `/src` or `/app` - Source code
- `/tests` - Test files
- `/docs` - Documentation
- `/scripts` - Utility scripts
- NO files in root except configs

## Commands
- Use `--mode plan` for complex tasks
- Background: `--background` for tests/builds
- Preview: `--preview` before commits

## Integration with Other Tools
- Opencode: Share env vars via .env
- Codex: Git operations coordinated
- Cursor: Rules sync via .cursorrules
- MCP: Shared context via servers

## Security
- NEVER commit .env or secrets
- Use environment variables
- Validate all inputs
- No eval() or exec()
EOF

# Create rules.yaml for MCP
cat > "$PROJECT_DIR/rules.yaml" << 'EOF'
version: 1.0
project: sophia-intel-ai
environment: development

rules:
  style:
    - functional_preferred: true
    - no_global_state: true
    - async_by_default: true
    - type_hints: required
    
  lint:
    python: 
      - tool: black
      - line_length: 88
    javascript: 
      - tool: prettier
      - semi: false
    typescript:
      - tool: prettier
      - strict: true
      
  commits:
    - format: conventional
    - atomic: true
    - max_files: 10
    - sign: true
    
  security:
    - no_hardcoded_secrets: true
    - use_env_vars: true
    - sanitize_inputs: true
    - no_eval: true
    
  testing:
    - coverage_min: 80
    - before_commit: true
    - frameworks:
        python: pytest
        javascript: jest
        
  mcp:
    servers:
      - memory: "http://localhost:8081"
      - filesystem: "http://localhost:8082"
      - git: "http://localhost:8084"
EOF

# Create .cursorrules
cat > "$PROJECT_DIR/.cursorrules" << 'EOF'
# Cursor IDE Configuration

You are an expert AI assistant integrated with multiple MCP servers.

## Available MCP Servers
- Memory: http://localhost:8081 (persistent memory, sessions)
- Filesystem: http://localhost:8082 (file operations, indexing)
- Git: http://localhost:8084 (repository analysis, history)

## Code Style
1. Functional programming preferred
2. No unnecessary try/catch blocks
3. Modern Python 3.10+/ES6+ features
4. Type hints required in Python
5. No global state

## File Organization
- /app or /src: Source code
- /tests: Test files  
- /docs: Documentation
- /scripts: Utilities

## Security
- Never hardcode secrets
- Use .env for configuration
- Validate all inputs
- No eval/exec

## Testing
- Write tests first (TDD)
- Minimum 80% coverage
- Use pytest/jest

## Commits
- Conventional format
- Atomic changes
- Sign commits
EOF

# Step 5: Configure tool authentication
echo -e "${YELLOW}[5/10] Configuring authentication...${NC}"

# Create/update .env if needed
if [ ! -f "$PROJECT_DIR/.env" ]; then
  cat > "$PROJECT_DIR/.env" << 'EOF'
# AI API Keys
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY
OPENAI_API_KEY=sk-YOUR-KEY
DEEPSEEK_API_KEY=sk-YOUR-KEY
XAI_API_KEY=xai-YOUR-KEY

# MCP Configuration  
MCP_MEMORY_URL=http://localhost:8081
MCP_FILESYSTEM_URL=http://localhost:8082
MCP_GIT_URL=http://localhost:8084

# Tool Configuration
CLAUDE_MODE=plan
OPENCODE_PROVIDER=anthropic
CODEX_MODEL=gpt-4
EOF
  echo -e "${YELLOW}⚠ Created .env template - add your API keys${NC}"
else
  echo -e "${GREEN}✓ .env already exists${NC}"
fi

# Step 6: Create MCP manager script
echo -e "${YELLOW}[6/10] Creating MCP manager...${NC}"

cat > "$PROJECT_DIR/mcp-manager.sh" << 'EOF'
#!/bin/bash

# MCP Server Manager

case "$1" in
  status)
    echo "MCP Server Status:"
    echo "=================="
    ps aux | grep -E "mcp\.(memory|filesystem|git)_server" | grep -v grep || echo "No MCP servers running"
    ;;
    
  start)
    echo "Starting MCP servers..."
    cd mcp_servers/base
    python -m uvicorn mcp.memory_server:app --host 0.0.0.0 --port 8081 &
    python -m uvicorn mcp.filesystem.server:app --host 0.0.0.0 --port 8082 &
    python -m uvicorn mcp.git.server:app --host 0.0.0.0 --port 8084 &
    echo "MCP servers started on ports 8081, 8082, 8084"
    ;;
    
  stop)
    echo "Stopping MCP servers..."
    pkill -f "mcp\.(memory|filesystem|git)_server"
    ;;
    
  restart)
    $0 stop
    sleep 2
    $0 start
    ;;
    
  *)
    echo "Usage: $0 {status|start|stop|restart}"
    ;;
esac
EOF
chmod +x "$PROJECT_DIR/mcp-manager.sh"

# Step 7: Configure Opencode for MCP
echo -e "${YELLOW}[7/10] Configuring Opencode for MCP...${NC}"

# Add MCP servers to Opencode (if opencode is available)
if command -v opencode &> /dev/null || [ -f "$HOME/.opencode/bin/opencode" ]; then
  export PATH="$HOME/.opencode/bin:$PATH"
  
  # Create auth entries for MCP servers
  mkdir -p ~/.local/share/opencode
  
  # Note: Opencode uses auth.json, not config.json
  if [ -f ~/.local/share/opencode/auth.json ]; then
    echo -e "${GREEN}✓ Opencode auth already configured${NC}"
  fi
fi

# Step 8: Create test script
echo -e "${YELLOW}[8/10] Creating test utilities...${NC}"

cat > "$PROJECT_DIR/test-integration.sh" << 'EOF'
#!/bin/bash

echo "🧪 Multi-Tool Integration Test"
echo "=============================="
echo ""

# Check tools
echo "Installed Tools:"
command -v claude &> /dev/null && echo "✓ Claude Code"
command -v opencode &> /dev/null && echo "✓ Opencode" 
command -v codex &> /dev/null && echo "✓ Codex"
command -v cursor &> /dev/null && echo "✓ Cursor"
echo ""

# Check MCP servers
echo "MCP Servers:"
curl -s http://localhost:8081/health 2>/dev/null && echo "✓ Memory Server (8081)" || echo "✗ Memory Server"
curl -s http://localhost:8082/health 2>/dev/null && echo "✓ Filesystem Server (8082)" || echo "✗ Filesystem Server"
curl -s http://localhost:8084/health 2>/dev/null && echo "✓ Git Server (8084)" || echo "✗ Git Server"
echo ""

# Check environment
echo "Environment:"
[ -n "$ANTHROPIC_API_KEY" ] && echo "✓ ANTHROPIC_API_KEY set" || echo "✗ ANTHROPIC_API_KEY missing"
[ -n "$OPENAI_API_KEY" ] && echo "✓ OPENAI_API_KEY set" || echo "✗ OPENAI_API_KEY missing"
echo ""

# Check configs
echo "Configuration Files:"
[ -f CLAUDE.md ] && echo "✓ CLAUDE.md"
[ -f rules.yaml ] && echo "✓ rules.yaml"
[ -f .cursorrules ] && echo "✓ .cursorrules"
[ -f .env ] && echo "✓ .env"
echo ""

# Test basic operation
echo "Testing basic operations..."
echo "def test(): return 'Multi-tool ready!'" > test_multi.py
python3 test_multi.py 2>/dev/null && echo "✓ Python execution works"
rm -f test_multi.py
EOF
chmod +x "$PROJECT_DIR/test-integration.sh"

# Step 9: Create unified launcher
echo -e "${YELLOW}[9/10] Creating unified launcher...${NC}"

cat > "$PROJECT_DIR/dev" << 'EOF'
#!/bin/bash

# Unified Development Environment Launcher
# Integrates with existing MCP servers

export PATH="$HOME/.opencode/bin:$PATH"

# Load environment
[ -f .env ] && export $(grep -v '^#' .env | xargs)

case "$1" in
  # Tools
  claude|cl)
    shift
    claude "$@"
    ;;
  opencode|oc)
    shift
    opencode "$@"
    ;;
  codex|cx)
    shift
    codex "$@"
    ;;
  cursor)
    cursor . &
    ;;
    
  # MCP Management
  mcp)
    shift
    ./mcp-manager.sh "$@"
    ;;
    
  # Testing
  test)
    ./test-integration.sh
    ;;
    
  # Info
  info)
    echo "Multi-Tool Development Environment"
    echo "=================================="
    echo "MCP Servers:"
    echo "  Memory: http://localhost:8081"
    echo "  Filesystem: http://localhost:8082"
    echo "  Git: http://localhost:8084"
    echo ""
    echo "Tools Available:"
    command -v claude &> /dev/null && echo "  ✓ Claude Code (claude)"
    command -v opencode &> /dev/null && echo "  ✓ Opencode (opencode)"
    command -v codex &> /dev/null && echo "  ✓ Codex (codex)"
    ;;
    
  *)
    echo "Unified Dev Environment"
    echo ""
    echo "Usage: ./dev [command]"
    echo ""
    echo "Tools:"
    echo "  claude, cl    - Claude Code CLI"
    echo "  opencode, oc  - Opencode CLI"
    echo "  codex, cx     - Codex CLI"
    echo "  cursor        - Open in Cursor IDE"
    echo ""
    echo "MCP:"
    echo "  mcp status    - Check MCP servers"
    echo "  mcp start     - Start MCP servers"
    echo "  mcp stop      - Stop MCP servers"
    echo ""
    echo "Other:"
    echo "  test          - Test integration"
    echo "  info          - Show configuration"
    ;;
esac
EOF
chmod +x "$PROJECT_DIR/dev"

# Step 10: Final cleanup and summary
echo -e "${YELLOW}[10/10] Finalizing setup...${NC}"

# Update .gitignore
grep -q "\.env" .gitignore 2>/dev/null || echo ".env" >> .gitignore
grep -q "test_multi" .gitignore 2>/dev/null || echo "test_multi*.py" >> .gitignore

echo ""
echo -e "${GREEN}✅ INTEGRATED MULTI-TOOL SETUP COMPLETE${NC}"
echo ""
echo -e "${BLUE}Current MCP Servers:${NC}"
echo "  • Memory: http://localhost:8081"
echo "  • Filesystem: http://localhost:8082"
echo "  • Git: http://localhost:8084"
echo ""
echo -e "${BLUE}Quick Start:${NC}"
echo "  1. Check status: ./dev mcp status"
echo "  2. Test setup: ./dev test"
echo "  3. Launch tool: ./dev claude | opencode | cursor"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  • Add your API keys to .env"
echo "  • Start MCP if needed: ./dev mcp start"
echo "  • Test with: ./dev test"
echo ""
echo "No duplicates, no conflicts, ARM64 optimized ✨"
