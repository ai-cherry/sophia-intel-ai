#!/bin/bash
# launch_production.sh - Sophia AI Platform v3.2 Enhanced Launch
# This script is now integrated into sophia.sh - use ./sophia.sh launch instead

echo "⚠️  This script has been superseded by the unified management system."
echo "Please use: ./sophia.sh launch"
echo ""
echo "For full management capabilities:"
echo "  ./sophia.sh validate  - Run comprehensive validation"
echo "  ./sophia.sh launch    - Start all services"
echo "  ./sophia.sh stop      - Stop all services"
echo "  ./sophia.sh restart   - Restart all services"
echo "  ./sophia.sh status    - Check service status"
echo "  ./sophia.sh logs      - View service logs"
echo ""

# Redirect to unified script
if [ -f "./sophia.sh" ]; then
    echo "Running unified launch..."
    ./sophia.sh launch
else
    echo "❌ Unified management script not found!"
    exit 1
fi

