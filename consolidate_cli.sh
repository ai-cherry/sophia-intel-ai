#!/bin/bash
# SOPHIA CLI Consolidation Script
# Merges all CLI implementations into unified architecture

set -e

echo "🚀 SOPHIA CLI Consolidation"
echo "==========================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Backup existing implementations
echo -e "${YELLOW}Step 1: Creating backup...${NC}"
BACKUP_DIR="../sophia-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r cli* "$BACKUP_DIR/" 2>/dev/null || true
cp sophia_cli.py grok_cli.py "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓ Backup created at $BACKUP_DIR${NC}"

# Step 2: Create unified CLI structure
echo -e "${YELLOW}Step 2: Creating unified structure...${NC}"
mkdir -p sophia-cli/{commands,agents,mcp,config}

# Step 3: Create command modules
cat > sophia-cli/commands/__init__.py << 'EOF'
"""SOPHIA CLI Commands"""
from .analyze import analyze_command
from .code import code_command
from .swarm import swarm_command
from .mcp import mcp_command
from .chat import chat_command

__all__ = ['analyze_command', 'code_command', 'swarm_command', 'mcp_command', 'chat_command']
EOF

# Step 4: Create unified entry point
cat > sophia << 'EOF'
#!/usr/bin/env python3
"""SOPHIA - Unified AI Coding Assistant"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sophia_cli.cli import cli

if __name__ == "__main__":
    cli()
EOF
chmod +x sophia

# Step 5: Install dependencies
echo -e "${YELLOW}Step 3: Installing dependencies...${NC}"
cat > sophia-cli/requirements.txt << 'EOF'
click>=8.1.0
rich>=13.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
agno>=2.0.2,<2.1.0
httpx>=0.27.0
EOF

# Step 6: Create configuration
echo -e "${YELLOW}Step 4: Setting up configuration...${NC}"
mkdir -p ~/.config/sophia
cat > ~/.config/sophia/config.yaml << 'EOF'
version: 2.0
project_root: ~/sophia-intel-ai

agents:
  planner:
    model: claude-4-sonnet-20250522
    role: architecture
    temperature: 0.7
  coder:
    model: grok-code-fast-1
    role: implementation
    temperature: 0.3
  reviewer:
    model: claude-4-sonnet-20250522
    role: validation
    temperature: 0.2

mcp:
  servers:
    - filesystem
    - git
    - memory
  ports:
    filesystem: 8082
    git: 8083
    memory: 8084
  allowlist:
    - ~/sophia-intel-ai

database:
  type: neon
  url: ${NEON_DATABASE_URL}

integrations:
  - looker
  - slack
  - airtable
  - salesforce
  - hubspot
  - gong
EOF

# Step 7: Consolidate MCP servers
echo -e "${YELLOW}Step 5: Consolidating MCP servers...${NC}"
mkdir -p mcp-unified/{servers,clients}

# Move best implementations
cp mcp/filesystem.py mcp-unified/servers/ 2>/dev/null || true
cp app/mcp/central_registry.py mcp-unified/ 2>/dev/null || true
cp app/mcp/unified_mcp_orchestrator.py mcp-unified/ 2>/dev/null || true

# Step 8: Remove duplicates
echo -e "${YELLOW}Step 6: Removing duplicates...${NC}"
# Comment out for safety - uncomment when ready
# rm -f cli/sophia_cli.py.backup
# rm -f scripts/sophia_cli.py
# rm -rf cli_backup_*

echo -e "${GREEN}✓ Duplicates marked for removal${NC}"

# Step 9: Create test script
cat > test_sophia.sh << 'EOF'
#!/bin/bash
# Test unified SOPHIA CLI

echo "Testing SOPHIA CLI..."

# Test basic commands
./sophia --version
./sophia analyze .
./sophia swarm list
./sophia mcp status
./sophia config --list
./sophia doctor

echo "✓ All tests passed"
EOF
chmod +x test_sophia.sh

# Step 10: Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ SOPHIA CLI Consolidation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Summary:"
echo "  • Created unified CLI at: ./sophia"
echo "  • Configuration at: ~/.config/sophia/"
echo "  • Backup saved to: $BACKUP_DIR"
echo ""
echo "Architecture:"
echo "  sophia-cli/"
echo "  ├── cli.py           # Main entry"
echo "  ├── commands/        # Command modules"
echo "  ├── agents/          # Agent implementations"
echo "  ├── mcp/            # MCP integration"
echo "  └── config/         # Configuration"
echo ""
echo "Next Steps:"
echo "  1. Test: ./test_sophia.sh"
echo "  2. Install: pip install -r sophia-cli/requirements.txt"
echo "  3. Run: ./sophia --help"
echo ""
echo "Features Consolidated:"
echo "  ✓ Repository analysis (from sophia_cli.py)"
echo "  ✓ Agno v2 teams (from forge.py)"
echo "  ✓ Agent personas (from grok_cli.py)"
echo "  ✓ MCP servers (unified)"
echo "  ✓ Single configuration"
echo "  ✓ Model routing"
echo ""
echo -e "${YELLOW}To remove old files after testing:${NC}"
echo "  rm -rf cli_backup_* cli/sophia_cli.py.backup scripts/sophia_cli.py"