#!/bin/bash
# Sophia AI Secret Management Dashboard Startup Script

set -e

echo "🎖️ Starting Sophia AI Secret Management Dashboard"
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Install dependencies if requirements file exists
if [ -f "requirements-dashboard.txt" ]; then
    echo "📦 Installing dashboard dependencies..."
    pip3 install -r requirements-dashboard.txt
fi

# Set default environment variables if not set
export DASHBOARD_HOST=${DASHBOARD_HOST:-"0.0.0.0"}
export DASHBOARD_PORT=${DASHBOARD_PORT:-8080}
export DASHBOARD_RELOAD=${DASHBOARD_RELOAD:-false}

# Set API keys from environment or use defaults for demo
export OPENAI_API_KEY=${OPENAI_API_KEY:-"demo-key"}
export ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-"demo-key"}
export LAMBDA_API_KEY=${LAMBDA_API_KEY:-"demo-key"}
export EXA_API_KEY=${EXA_API_KEY:-"fdf07f38-34ad-44a9-ab6f-74ca2ca90fd4"}

echo "🌍 Environment: ${DASHBOARD_ENV:-development}"
echo "🔗 Host: $DASHBOARD_HOST"
echo "🚪 Port: $DASHBOARD_PORT"
echo "🔄 Reload: $DASHBOARD_RELOAD"

# Start the dashboard
echo ""
echo "🚀 Starting Secret Management Dashboard..."
echo "📊 Dashboard: http://$DASHBOARD_HOST:$DASHBOARD_PORT"
echo "📈 Metrics: http://$DASHBOARD_HOST:$DASHBOARD_PORT/metrics"
echo "🔌 API: http://$DASHBOARD_HOST:$DASHBOARD_PORT/api/secrets/health"
echo ""

if [ "$DASHBOARD_RELOAD" = "true" ]; then
    python3 secret_management_dashboard.py --host $DASHBOARD_HOST --port $DASHBOARD_PORT --reload
else
    python3 secret_management_dashboard.py --host $DASHBOARD_HOST --port $DASHBOARD_PORT
fi

