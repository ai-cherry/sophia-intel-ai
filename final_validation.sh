#!/bin/bash
# final_validation.sh - Sophia AI Platform v3.2 Enhanced Validation
# This script is now integrated into sophia.sh - use ./sophia.sh validate instead

echo "⚠️  This script has been superseded by the unified management system."
echo "Please use: ./sophia.sh validate"
echo ""
echo "For full management capabilities:"
echo "  ./sophia.sh validate  - Run comprehensive validation"
echo "  ./sophia.sh launch    - Start all services"
echo "  ./sophia.sh status    - Check service status"
echo "  ./sophia.sh logs      - View service logs"
echo ""

# Redirect to unified script
if [ -f "./sophia.sh" ]; then
    echo "Running unified validation..."
    ./sophia.sh validate
else
    echo "❌ Unified management script not found!"
    exit 1
fi

