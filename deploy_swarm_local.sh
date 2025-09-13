#!/bin/bash
# Sophia Intel AI - Enhanced Local Deployment with Swarm Support
# Merges unified CLI with multi-agent orchestration

set -euo pipefail

echo "🚀 SOPHIA INTEL AI - SWARM-ENABLED DEPLOYMENT"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
REPO_ROOT="$HOME/sophia-intel-ai"
CONFIG_ROOT="$HOME/.config/sophia"

# Step 1: Prerequisites
echo -e "${CYAN}📋 Checking prerequisites...${NC}"
command -v python3 >/dev/null || { echo "❌ Python 3 required"; exit 1; }
command -v redis-cli >/dev/null || { echo "❌ Redis required"; exit 1; }
command -v node >/dev/null || { echo "❌ Node.js required"; exit 1; }
command -v rg >/dev/null || { echo "❌ ripgrep required (brew install ripgrep)"; exit 1; }
echo -e "${GREEN}✅ All prerequisites met${NC}"

# Step 2: Install Python dependencies
echo -e "${CYAN}📦 Installing Python dependencies...${NC}"
pip3 install -q fastapi uvicorn httpx redis pydantic toml

# Step 3: Update environment configuration
echo -e "${CYAN}🔧 Updating environment configuration...${NC}"
cat >> "$CONFIG_ROOT/env" << 'EOF'

# Swarm Configuration
export SWARM_ENABLED=true
export WORKTREES_DIR="$HOME/sophia-intel-ai/../worktrees"
export LOG_DIR="$HOME/sophia-intel-ai/logs"

# LLM Model Mix
export CLAUDE_MODEL="claude-opus-4.1"
export GROK_MODEL="grok-5"
export LLAMA_MODEL="llama-scout-4"
export FLASH_MODEL="google-flash-2.5"
export DEEPSEEK_MODEL="deepseek-v3"

# MCP Ports (canonical)
export MCP_MEMORY_PORT=8081
export MCP_FILESYSTEM_PORT=8082
export MCP_GIT_PORT=8084

# Anti-fragmentation
export DUP_CHECK_ENABLED=true
export SEMANTIC_THRESHOLD=0.8
EOF

# Step 4: Setup worktree functions
echo -e "${CYAN}🌳 Setting up worktree management...${NC}"
cat >> "$HOME/.zshrc" << 'EOF'

# Sophia Worktree Functions
source ~/sophia-intel-ai/bin/worktree.sh
export WORKTREES_DIR="$HOME/sophia-intel-ai/../worktrees"
EOF

# Step 5: Make scripts executable
echo -e "${CYAN}🔨 Setting up executables...${NC}"
chmod +x "$REPO_ROOT/bin/sophia-cli-v2"
chmod +x "$REPO_ROOT/bin/worktree.sh"
chmod +x "$REPO_ROOT/scripts/dup_scan.py"

# Create symlink for new CLI
ln -sf "$REPO_ROOT/bin/sophia-cli-v2" "$REPO_ROOT/bin/sophia-cli"

# Step 6: Create necessary directories
echo -e "${CYAN}📁 Creating directory structure...${NC}"
mkdir -p "$REPO_ROOT/logs/handoffs"
mkdir -p "$REPO_ROOT/../worktrees"
mkdir -p "$CONFIG_ROOT/personas"

# Step 7: Start Redis if not running
echo -e "${CYAN}🔴 Starting Redis...${NC}"
if ! redis-cli ping >/dev/null 2>&1; then
    redis-server --daemonize yes
    sleep 2
fi
echo -e "${GREEN}✅ Redis running${NC}"

# Step 8: Start MCP servers
echo -e "${CYAN}🚀 Starting MCP servers...${NC}"

# Kill any existing MCP servers
pkill -f "mcp/memory_server.py" 2>/dev/null || true
pkill -f "mcp/filesystem/server.py" 2>/dev/null || true
pkill -f "mcp/git/server.py" 2>/dev/null || true

sleep 1

# Start fresh instances
nohup python3 "$REPO_ROOT/mcp/memory_server.py" > "$REPO_ROOT/logs/mcp_memory.log" 2>&1 &
echo "  Memory server starting on port 8081..."

nohup python3 -m uvicorn mcp.filesystem.server:app --host 0.0.0.0 --port 8082 > "$REPO_ROOT/logs/mcp_filesystem.log" 2>&1 &
echo "  Filesystem server starting on port 8082..."

nohup python3 -m uvicorn mcp.git.server:app --host 0.0.0.0 --port 8084 > "$REPO_ROOT/logs/mcp_git.log" 2>&1 &
echo "  Git server starting on port 8084..."

sleep 3

# Step 9: Verify MCP servers
echo -e "${CYAN}✅ Verifying MCP servers...${NC}"
python3 -c "
import httpx
import asyncio

async def verify():
    async with httpx.AsyncClient(timeout=2.0) as client:
        services = [
            ('Memory', 'http://localhost:8081/health'),
            ('Filesystem', 'http://localhost:8082/health'),
            ('Git', 'http://localhost:8084/health')
        ]
        
        all_healthy = True
        for name, url in services:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    print(f'  ✅ {name} MCP')
                else:
                    print(f'  ❌ {name} MCP - Not healthy')
                    all_healthy = False
            except:
                print(f'  ❌ {name} MCP - Not responding')
                all_healthy = False
        
        return all_healthy

result = asyncio.run(verify())
exit(0 if result else 1)
"

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Some MCP servers failed to start. Check logs in $REPO_ROOT/logs/${NC}"
fi

# Step 10: Initialize repository index
echo -e "${CYAN}🔍 Building repository index...${NC}"
if [[ -f "$REPO_ROOT/builder_cli/lib/indexer.py" ]]; then
    python3 -c "
import sys
sys.path.insert(0, '$REPO_ROOT')
try:
    from builder_cli.lib.indexer import build_full_index
    build_full_index()
    print('  ✅ Repository indexed')
except Exception as e:
    print(f'  ⚠️  Indexing failed: {e}')
"
fi

# Step 11: Configure Claude and Codex CLIs
echo -e "${CYAN}⚙️  Configuring CLI tools...${NC}"

# Claude configuration
cat > "$CONFIG_ROOT/claude/claude_desktop_config.json" << EOF
{
  "mcpServers": {
    "sophia-memory": {
      "command": "python3",
      "args": ["$REPO_ROOT/mcp/memory_server.py"],
      "env": {
        "REDIS_URL": "redis://localhost:6379/1"
      }
    },
    "sophia-filesystem": {
      "command": "python3",
      "args": ["-m", "uvicorn", "mcp.filesystem.server:app", "--host", "0.0.0.0", "--port", "8082"],
      "env": {
        "WORKSPACE_PATH": "$REPO_ROOT"
      }
    },
    "sophia-git": {
      "command": "python3",
      "args": ["-m", "uvicorn", "mcp.git.server:app", "--host", "0.0.0.0", "--port", "8084"],
      "env": {
        "REPO_PATH": "$REPO_ROOT"
      }
    }
  }
}
EOF
echo -e "  ${GREEN}✅ Claude configured${NC}"

# Codex configuration
cat > "$CONFIG_ROOT/codex/config.toml" << EOF
[mcp]
enabled = true

[mcp.servers.memory]
url = "http://localhost:8081"
capabilities = ["store", "retrieve", "search"]

[mcp.servers.filesystem]
url = "http://localhost:8082"
capabilities = ["read", "write", "index"]

[mcp.servers.git]
url = "http://localhost:8084"
capabilities = ["symbols", "deps", "history"]

[indexing]
enabled = true
redis_url = "redis://localhost:6379/2"
EOF
echo -e "  ${GREEN}✅ Codex configured${NC}"

# Step 12: Test the setup
echo -e "${CYAN}🧪 Testing the setup...${NC}"

# Test CLI
if "$REPO_ROOT/bin/sophia-cli" status >/dev/null 2>&1; then
    echo -e "  ${GREEN}✅ CLI working${NC}"
else
    echo -e "  ${YELLOW}⚠️  CLI not fully configured${NC}"
fi

# Test worktree functions
if bash -c "source $REPO_ROOT/bin/worktree.sh && type wt" >/dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Worktree functions available${NC}"
else
    echo -e "  ${YELLOW}⚠️  Worktree functions not loaded${NC}"
fi

# Test deduplication scanner
if python3 "$REPO_ROOT/scripts/dup_scan.py" --help >/dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Deduplication scanner ready${NC}"
else
    echo -e "  ${YELLOW}⚠️  Deduplication scanner error${NC}"
fi

# Final summary
echo ""
echo "==========================================="
echo -e "${GREEN}✨ SWARM DEPLOYMENT COMPLETE! ✨${NC}"
echo "==========================================="
echo ""
echo "📝 Next Steps:"
echo "1. Reload your shell: source ~/.zshrc"
echo "2. Test the swarm: sophia-cli swarm \"Build a simple feature\""
echo "3. Check status: sophia-cli status"
echo ""
echo "🎯 Quick Commands:"
echo "  sophia-cli swarm <task>  - Launch multi-agent swarm"
echo "  sophia-cli plan <task>   - Single agent planning"
echo "  sophia-cli status        - Check all systems"
echo "  wt <name>               - Create agent worktree"
echo "  wtl                     - List worktrees"
echo "  wtc                     - Clean all worktrees"
echo ""
echo "📚 Documentation:"
echo "  Agent rules: $REPO_ROOT/AGENTS.md"
echo "  CLI help: sophia-cli help"
echo ""
echo "🚀 Your code army is ready for battle!"
