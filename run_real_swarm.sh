#!/bin/bash
# Real Swarm Launcher - Parallel Orchestrator
echo "🐝 LAUNCHING REAL PARALLEL SWARM ORCHESTRATOR"
echo "============================================="

# Check if task provided
if [ -z "$1" ]; then
    echo "Usage: ./run_real_swarm.sh \"your task here\""
    echo "Example: ./run_real_swarm.sh \"analyze codebase architecture\""
    exit 1
fi

# Run the REAL swarm that actually executes in parallel
cd /Users/lynnmusil/sophia-intel-ai
python3 scripts/real_swarm_orchestrator_complete.py "$1"

echo ""
echo "✅ REAL SWARM EXECUTION COMPLETE"
echo "📄 Results saved to JSON file in current directory"
echo "📊 Check swarm.log for detailed execution logs"
