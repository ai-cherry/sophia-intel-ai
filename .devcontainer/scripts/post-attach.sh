#!/bin/bash
set -euo pipefail

echo "👋 SOPHIA AI PLATFORM - WELCOME"
echo "Setting up your development session..."

# Color codes
GREEN='\033[0;32m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_welcome() { echo -e "${CYAN}[WELCOME]${NC} $1"; }
log_tip() { echo -e "${PURPLE}[TIP]${NC} $1"; }

# 1. Display welcome message
echo ""
log_welcome "🚀 Sophia AI Platform Development Environment"
log_welcome "Enterprise-grade AI platform with zero recovery mode tolerance"
echo ""

# 2. Show environment status
log_info "Environment Status:"
echo "  📍 Workspace: $(pwd)"
echo "  🐍 Python: $(python3 --version)"
echo "  📦 UV: $(uv --version 2>/dev/null || echo 'Not available')"
echo "  🟢 Node: $(node --version 2>/dev/null || echo 'Not available')"
echo ""

# 3. Show available services
log_info "Available Services:"
echo "  🌐 Backend API: http://localhost:8000"
echo "  📚 API Docs: http://localhost:8000/api/docs"
echo "  ❤️  Health Check: http://localhost:8000/health"
echo "  🎨 Frontend: ${SOPHIA_FRONTEND_ENDPOINT} (if configured)"
echo ""

# 4. Show quick commands
log_info "Quick Commands:"
echo "  🚀 Start backend: cd backend && python main.py"
echo "  🧪 Run tests: pytest"
echo "  🛡️  Security scan: ./security_quick_fix.sh"
echo "  📊 Preflight check: ./codespaces_preflight_check.sh"
echo "  🔍 View logs: tail -f logs/startup.log"
echo ""

# 5. Show recent activity
if [ -f "/workspace/logs/startup.log" ]; then
    log_info "Recent Activity:"
    tail -3 /workspace/logs/startup.log | sed 's/^/  /'
    echo ""
fi

# 6. Security status
if [ -d "/workspace/security-reports" ]; then
    REPORT_COUNT=$(ls -1 /workspace/security-reports/*.json 2>/dev/null | wc -l)
    if [ "$REPORT_COUNT" -gt 0 ]; then
        log_info "🛡️  Security: $REPORT_COUNT scan reports available in security-reports/"
    fi
fi

# 7. Development tips
log_tip "💡 Development Tips:"
echo "  • Use 'uv add <package>' to add new dependencies"
echo "  • Run 'pre-commit run --all-files' before committing"
echo "  • Check 'setup-summary.md' for detailed setup information"
echo "  • Security scans run automatically on git commits"
echo ""

# 8. Update session log
echo "$(date): User session attached" >> /workspace/logs/startup.log

log_welcome "🎯 Ready for enterprise AI development!"
echo "═══════════════════════════════════════════════════════════════════"

