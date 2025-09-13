#!/bin/bash
# Sophia Intel AI - Unified CLI Demo
# This script demonstrates the capabilities of the unified CLI system

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}     SOPHIA INTEL AI - UNIFIED CLI DEMONSTRATION${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Load environment
source ~/.zshrc 2>/dev/null || true

# Demo 1: Validation
echo -e "${MAGENTA}━━━ Demo 1: System Validation ━━━${NC}"
echo -e "${BLUE}Running: sophia-cli validate${NC}"
echo ""
~/sophia-intel-ai/bin/sophia-cli validate
echo ""
sleep 2

# Demo 2: Simple task routing to Codex
echo -e "${MAGENTA}━━━ Demo 2: Simple Task (Routes to Codex) ━━━${NC}"
echo -e "${BLUE}Command: sophia-cli plan \"Fix typo in README\"${NC}"
echo -e "${YELLOW}Expected: Fast response from Codex${NC}"
echo ""
echo "(Would execute: codex --model gpt-4o \"PLAN: Fix typo in README\")"
echo ""
sleep 2

# Demo 3: Complex task routing to Claude
echo -e "${MAGENTA}━━━ Demo 3: Complex Task (Routes to Claude) ━━━${NC}"
echo -e "${BLUE}Command: sophia-cli plan \"Design microservices architecture for payment system\"${NC}"
echo -e "${YELLOW}Expected: Thorough analysis from Claude${NC}"
echo ""
echo "(Would execute: claude --model claude-3-5-sonnet \"PLAN: Design microservices architecture\")"
echo ""
sleep 2

# Demo 4: Implementation with automatic routing
echo -e "${MAGENTA}━━━ Demo 4: Implementation with Smart Routing ━━━${NC}"
echo -e "${BLUE}Command: sophia-cli implement \"Add error handling to user service\"${NC}"
echo -e "${YELLOW}Expected: Implementation with tests and unified diff${NC}"
echo ""
sleep 2

# Demo 5: Using aliases
echo -e "${MAGENTA}━━━ Demo 5: Quick Aliases ━━━${NC}"
echo -e "${GREEN}Available aliases:${NC}"
echo "  splan <task>   - Quick planning"
echo "  simpl <task>   - Quick implementation"  
echo "  sval           - Quick validation"
echo ""
echo -e "${BLUE}Example: splan \"Create user authentication\"${NC}"
echo ""
sleep 2

# Demo 6: Provider override
echo -e "${MAGENTA}━━━ Demo 6: Manual Provider Selection ━━━${NC}"
echo -e "${BLUE}Force Codex: CLI_PROVIDER=codex sophia-cli plan \"Complex task\"${NC}"
echo -e "${BLUE}Force Claude: CLI_PROVIDER=claude sophia-cli implement \"Simple task\"${NC}"
echo ""
sleep 2

# Demo 7: Daily workflow
echo -e "${MAGENTA}━━━ Demo 7: Daily Workflow Example ━━━${NC}"
echo -e "${GREEN}Morning Routine:${NC}"
echo "1. sophia-daily         # Run startup checks"
echo "2. git status          # Check repo state"
echo "3. sval                # Validate environment"
echo ""
echo -e "${GREEN}Development Session:${NC}"
echo "1. splan \"Today's feature\"     # Plan the work"
echo "2. simpl \"First component\"     # Implement iteratively"
echo "3. simpl \"Add tests\"           # Add test coverage"
echo "4. git commit -m \"feat: ...\"   # Commit changes"
echo ""
sleep 2

# Demo 8: MCP Integration
echo -e "${MAGENTA}━━━ Demo 8: MCP Services Status ━━━${NC}"
echo -e "${BLUE}Checking MCP services...${NC}"
echo ""

# Check each service
services=(
    "8081:MCP Memory"
    "8082:MCP Filesystem"
    "8084:MCP Git"
    "8000:Unified API"
)

for service in "${services[@]}"; do
    IFS=':' read -r port name <<< "$service"
    if curl -s "http://localhost:$port/health" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ $name (port $port) - Running${NC}"
    else
        echo -e "  ${YELLOW}⚠️  $name (port $port) - Not running${NC}"
    fi
done
echo ""
sleep 2

# Demo 9: Specialized Personas
echo -e "${MAGENTA}━━━ Demo 9: Specialized Personas ━━━${NC}"
echo -e "${GREEN}Available personas:${NC}"
echo "  • Master Architect - System design and architecture"
echo "  • TypeScript Specialist - React/Next.js development"
echo "  • Python Backend - FastAPI and async patterns"
echo "  • Security Auditor - Vulnerability assessment"
echo ""
echo -e "${BLUE}Located in: ~/.config/sophia/personas/${NC}"
echo ""
sleep 2

# Summary
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}                    DEMO COMPLETE${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✨ Key Features Demonstrated:${NC}"
echo "  • Intelligent task routing (Codex vs Claude)"
echo "  • Unified configuration management"
echo "  • MCP service integration"
echo "  • Production-ready personas"
echo "  • Daily workflow optimization"
echo ""
echo -e "${YELLOW}📚 Next Steps:${NC}"
echo "  1. Add your API keys to ~/.config/sophia/env"
echo "  2. Try: sophia-cli plan \"Your first feature\""
echo "  3. Read: ~/sophia-intel-ai/CLI_QUICK_START.md"
echo ""
echo -e "${CYAN}Happy coding with Sophia Intel AI! 🚀${NC}"