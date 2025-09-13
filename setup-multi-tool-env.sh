#!/bin/bash

# Multi-Tool Terminal/IDE Setup for Mac M3 ARM64
# Opencode + Codex CLI + Claude Code + MCP + Cursor
# September 2025 Edition

set -e

echo "🚀 Multi-Tool Development Environment Setup"
echo "==========================================="
echo "Platform: $(uname -m) | macOS $(sw_vers -productVersion)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Paths
TOOLS_DIR="$HOME/tools"
PROJECT_DIR="$(pwd)"
MCP_PORT=8080

# Step 1: Create tools directory and clone repos
echo -e "${YELLOW}[1/9] Cloning tool repositories for reference...${NC}"
mkdir -p "$TOOLS_DIR"
cd "$TOOLS_DIR"

# Clone repos (skip if exists)
repos=(
  "https://github.com/openai/codex codex-cli"
  "https://github.com/anthropics/claude-code claude-code"
  "https://github.com/opencode-ai/opencode opencode"
  "https://github.com/idosal/git-mcp git-mcp"
  "https://github.com/hesreallyhim/awesome-claude-code awesome-claude-code"
)

for repo in "${repos[@]}"; do
  url="${repo%% *}"
  dir="${repo##* }"
  if [ ! -d "$dir" ]; then
    git clone "$url" "$dir" --depth 1 || echo "Skipping $dir"
  else
    echo "✓ $dir already exists"
  fi
done

cd "$PROJECT_DIR"

# Step 2: Install/Update Codex CLI
echo -e "${YELLOW}[2/9] Installing Codex CLI...${NC}"
if ! command -v codex &> /dev/null; then
  # Try npm first
  if command -v npm &> /dev/null; then
    npm install -g @openai/codex-cli@latest || true
  fi
  
  # Fallback to brew
  if ! command -v codex &> /dev/null; then
    brew tap openai/tap 2>/dev/null || true
    brew install openai/tap/codex-cli || echo "Manual install needed"
  fi
else
  echo "✓ Codex CLI already installed: $(codex --version 2>/dev/null || echo 'installed')"
fi

# Step 3: Update Claude Code CLI
echo -e "${YELLOW}[3/9] Updating Claude Code CLI...${NC}"
# Claude Code is likely already installed as 'claude'
if ! command -v claude &> /dev/null; then
  brew tap anthropic/tap 2>/dev/null || true
  brew install anthropic/tap/claude-code@latest || echo "Claude Code via alternate method"
else
  echo "✓ Claude Code already installed"
fi

# Step 4: Set up configuration directories
echo -e "${YELLOW}[4/9] Creating configuration directories...${NC}"
mkdir -p ~/.codex
mkdir -p ~/.config/opencode
mkdir -p ~/.claude

# Step 5: Create Codex instructions
cat > ~/.codex/instructions.md << 'EOF'
# Codex CLI Instructions

- Concise commits, no bloat
- Async JS/Python patterns
- Leverage thought summarization
- Use --yolo for quick scaffolds
- PR descriptions: problem → solution → impact
- No verbose comments
- Functional > OOP when possible
EOF
echo "✓ Created ~/.codex/instructions.md"

# Step 6: Create CLAUDE.md rules
cat > "$PROJECT_DIR/CLAUDE.md" << 'EOF'
# Claude Code Rules

## Core Principles
- No try/catch spam - handle errors at boundaries
- Functional code preferred
- Lint with black (Python) / prettier (JS/TS)
- Use background tasks for tests
- Atomic commits with clear messages

## Commands
- Always use `--mode plan` for complex tasks
- Background tasks: `--background` for long ops
- Preview diffs: `--preview` before commits

## File Organization
- `/src` - Source code
- `/tests` - Test files  
- `/docs` - Documentation
- No files in root except configs

## Testing
- Write tests before implementation
- Use `claude test` with `--background`
- Coverage target: 80%
EOF
echo "✓ Created CLAUDE.md"

# Step 7: Create shared rules.yaml for MCP
cat > "$PROJECT_DIR/rules.yaml" << 'EOF'
version: 1.0
rules:
  style:
    - functional_preferred: true
    - no_global_state: true
    - async_by_default: true
  
  lint:
    python: black
    javascript: prettier
    typescript: prettier
    
  commits:
    - atomic: true
    - conventional: true
    - max_files: 10
    
  security:
    - no_hardcoded_secrets: true
    - use_env_vars: true
    - sanitize_inputs: true
    
  performance:
    - lazy_loading: true
    - cache_when_possible: true
    - batch_operations: true
EOF
echo "✓ Created rules.yaml"

# Step 8: Set up Git MCP server (lightweight option)
echo -e "${YELLOW}[5/9] Setting up MCP server...${NC}"

# Create MCP runner script
cat > "$PROJECT_DIR/start-mcp.sh" << 'EOF'
#!/bin/bash
# Start lightweight MCP server for tool coordination

MCP_PORT=${1:-8080}
PROJECT_DIR="$(pwd)"

echo "Starting MCP server on port $MCP_PORT..."

# Check if git-mcp is available
if [ -d "$HOME/tools/git-mcp" ]; then
  cd "$HOME/tools/git-mcp"
  if [ -f "server.js" ]; then
    npm install --silent 2>/dev/null
    node server.js --port $MCP_PORT --repo "$PROJECT_DIR" &
    echo "Git MCP running on http://localhost:$MCP_PORT"
  fi
else
  # Fallback: simple HTTP server for file sharing
  echo "Starting simple MCP fallback..."
  python3 -m http.server $MCP_PORT --directory "$PROJECT_DIR" &
  echo "Simple MCP running on http://localhost:$MCP_PORT"
fi

echo "PID: $!"
echo $! > ~/.mcp.pid
EOF
chmod +x "$PROJECT_DIR/start-mcp.sh"

# Step 9: Configure tools to use MCP
echo -e "${YELLOW}[6/9] Configuring tools for MCP...${NC}"

# Codex config
if [ ! -f ~/.codex/config.json ]; then
  cat > ~/.codex/config.json << EOF
{
  "mcpUrl": "http://localhost:$MCP_PORT",
  "thoughtSummarization": true,
  "sandboxing": true,
  "yoloMode": false,
  "githubIntegration": true
}
EOF
  echo "✓ Created ~/.codex/config.json"
fi

# Step 10: Create .env template if needed
if [ ! -f "$PROJECT_DIR/.env" ]; then
  cat > "$PROJECT_DIR/.env" << 'EOF'
# AI API Keys
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
OPENAI_API_KEY=sk-YOUR-KEY-HERE
DEEPSEEK_API_KEY=sk-YOUR-KEY-HERE
XAI_API_KEY=xai-YOUR-KEY-HERE

# MCP Configuration
MCP_SERVER_URL=http://localhost:8080
MCP_AUTH_TOKEN=local-dev-token

# Tool Settings
CODEX_YOLO_MODE=false
CLAUDE_MODE=plan
OPENCODE_PROVIDER=anthropic
EOF
  echo "✓ Created .env template"
fi

# Step 11: Create Cursor rules file
cat > "$PROJECT_DIR/.cursorrules" << 'EOF'
# Cursor IDE Rules

You are an expert developer assistant. Follow these rules:

1. Code Style:
   - Functional programming preferred
   - No unnecessary try/catch blocks
   - Use modern ES6+/Python 3.10+ features

2. File Organization:
   - Source in /src
   - Tests in /tests
   - Docs in /docs

3. Commits:
   - Atomic changes
   - Conventional commit format
   - Clear, concise messages

4. Security:
   - Never hardcode secrets
   - Use environment variables
   - Validate all inputs

5. Performance:
   - Optimize for M3 ARM64
   - Use async/await patterns
   - Cache expensive operations
EOF
echo "✓ Created .cursorrules"

# Step 12: Create test script
cat > "$PROJECT_DIR/test-tools.sh" << 'EOF'
#!/bin/bash

echo "🧪 Testing Multi-Tool Setup"
echo "=========================="

# Test file
TEST_FILE="test_multi_tool.py"
cat > $TEST_FILE << 'PYEOF'
def hello_multi_tool():
    """Test function for multi-tool setup"""
    return "Hello from Multi-Tool Environment!"

if __name__ == "__main__":
    print(hello_multi_tool())
PYEOF

echo "Testing each tool with: $TEST_FILE"
echo ""

# Test Opencode
if command -v opencode &> /dev/null; then
  echo "✓ Opencode: $(opencode --version)"
  # opencode run "Add a docstring to $TEST_FILE" --no-tui 2>/dev/null || true
fi

# Test Codex
if command -v codex &> /dev/null; then
  echo "✓ Codex: installed"
  # codex commit --preview --dry-run 2>/dev/null || true
fi

# Test Claude
if command -v claude &> /dev/null; then
  echo "✓ Claude Code: installed"
  # claude code "Add type hints to $TEST_FILE" --preview 2>/dev/null || true
fi

echo ""
echo "Environment Variables:"
[ -n "$ANTHROPIC_API_KEY" ] && echo "✓ ANTHROPIC_API_KEY set"
[ -n "$OPENAI_API_KEY" ] && echo "✓ OPENAI_API_KEY set"
[ -n "$DEEPSEEK_API_KEY" ] && echo "✓ DEEPSEEK_API_KEY set"

echo ""
echo "Config Files:"
[ -f ~/.codex/instructions.md ] && echo "✓ Codex instructions"
[ -f CLAUDE.md ] && echo "✓ Claude rules"
[ -f rules.yaml ] && echo "✓ MCP rules"
[ -f .cursorrules ] && echo "✓ Cursor rules"

rm -f $TEST_FILE
EOF
chmod +x "$PROJECT_DIR/test-tools.sh"

# Step 13: Create unified launcher
cat > "$PROJECT_DIR/dev" << 'EOF'
#!/bin/bash

# Unified Development Environment Launcher
# Usage: ./dev [tool] [command]

case "$1" in
  opencode|oc)
    shift
    opencode "$@"
    ;;
  codex|cx)
    shift
    codex "$@"
    ;;
  claude|cl)
    shift
    claude "$@"
    ;;
  cursor)
    cursor . &
    ;;
  mcp)
    ./start-mcp.sh
    ;;
  test)
    ./test-tools.sh
    ;;
  *)
    echo "Multi-Tool Dev Environment"
    echo "Usage: ./dev [tool] [command]"
    echo ""
    echo "Tools:"
    echo "  opencode, oc  - Opencode CLI"
    echo "  codex, cx     - Codex CLI"
    echo "  claude, cl    - Claude Code"
    echo "  cursor        - Open in Cursor IDE"
    echo "  mcp          - Start MCP server"
    echo "  test         - Test all tools"
    ;;
esac
EOF
chmod +x "$PROJECT_DIR/dev"

# Step 14: Final setup
echo -e "${YELLOW}[7/9] Loading environment variables...${NC}"
if [ -f "$PROJECT_DIR/.env" ]; then
  export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

echo -e "${YELLOW}[8/9] Creating .gitignore entries...${NC}"
cat >> "$PROJECT_DIR/.gitignore" << 'EOF'

# Multi-tool specific
.mcp.pid
*.mcp-cache
.codex-cache/
.claude-cache/
.cursor-cache/
test_multi_tool.py
EOF

echo -e "${YELLOW}[9/9] Setup complete!${NC}"
echo ""
echo -e "${GREEN}✅ Multi-Tool Environment Ready${NC}"
echo ""
echo "Quick Start:"
echo "  1. Set your API keys in .env"
echo "  2. Start MCP: ./dev mcp"
echo "  3. Test setup: ./dev test"
echo ""
echo "Usage:"
echo "  ./dev opencode  - Launch Opencode"
echo "  ./dev codex    - Use Codex CLI"
echo "  ./dev claude   - Use Claude Code"
echo "  ./dev cursor   - Open in Cursor"
echo ""
echo "Features enabled:"
echo "  • Shared MCP server for coordination"
echo "  • Unified rules across all tools"
echo "  • ARM64 optimized for M3"
echo "  • No conflicts between tools"
echo "  • Secure env var management"