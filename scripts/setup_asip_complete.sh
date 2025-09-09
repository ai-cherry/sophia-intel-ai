#!/bin/bash
# Master Setup Script for Sophia AI with ASIP + Portkey Integration
# Combines all best ideas: ASIP performance, Portkey Gateway, Codespaces support, Lambda GPU option

set -e

echo "🚀 Sophia AI Complete Setup - ASIP + Portkey + Codespaces"
echo "=========================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Check environment
echo "1️⃣  Checking environment..."
if [ "$CODESPACES" = "true" ]; then
    print_status "Running in GitHub Codespaces"
    ENVIRONMENT="codespaces"
else
    print_warning "Not in Codespaces - some features may be limited"
    ENVIRONMENT="local"
fi

# 2. Create necessary directories
echo ""
echo "2️⃣  Creating directory structure..."
mkdir -p config/portkey
mkdir -p asip/rust_core/src
mkdir -p apps/codespaces_ai
mkdir -p apps/vscode_extension
mkdir -p apps/lambda_compute
mkdir -p logs
mkdir -p .cache
print_status "Directories created"

# 3. Check for environment file
echo ""
echo "3️⃣  Setting up environment variables..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        print_warning "Created .env from .env.example - please update with your API keys"
    else
        print_error "No .env.example found - creating minimal .env"
        cat > .env << 'EOF'
# Minimal environment configuration
ENVIRONMENT=development
CODESPACES=false
PORTKEY_API_KEY=
PORTKEY_BASE_URL=https://api.portkey.ai/v1
MAX_DAILY_SPEND=50
CACHE_ENABLED=true
FALLBACK_ENABLED=true
EOF
    fi
else
    print_status "Environment file exists"
fi

# 4. Install Python dependencies
echo ""
echo "4️⃣  Installing Python dependencies..."
if [ -f requirements-asip.txt ]; then
    pip install -q -r requirements-asip.txt
    print_status "ASIP requirements installed"
elif [ -f requirements.txt ]; then
    pip install -q -r requirements.txt
    print_status "Standard requirements installed"
else
    print_error "No requirements file found"
fi

# Special handling for optional packages
pip install -q portkey-ai 2>/dev/null && print_status "Portkey SDK installed" || print_warning "Portkey SDK not available"
pip install -q numba 2>/dev/null && print_status "Numba JIT installed" || print_warning "Numba not available"
pip install -q uvloop 2>/dev/null && print_status "UVLoop installed" || print_warning "UVLoop not available"

# 5. Create Portkey configuration
echo ""
echo "5️⃣  Setting up Portkey Gateway configuration..."
if [ ! -f config/portkey/config.json ]; then
    cat > config/portkey/config.json << 'EOF'
{
  "gateways": [
    {
      "name": "openrouter-gateway",
      "type": "openrouter",
      "config": {
        "retry": {
          "attempts": 3,
          "on_status_codes": [429, 500, 502, 503],
          "delay_ms": 1000
        },
        "cache": {
          "enabled": true,
          "ttl": 3600,
          "max_size": 1000
        },
        "fallback": {
          "enabled": true,
          "strategy": "cheapest_first"
        },
        "load_balancing": {
          "strategy": "least_latency"
        },
        "monitoring": {
          "log_requests": true,
          "track_costs": true,
          "alert_threshold_usd": 50
        }
      }
    }
  ],
  "models": {
    "primary": {
      "complex": "anthropic/claude-opus-4.1",
      "balanced": "anthropic/claude-sonnet-4",
      "code": "qwen/qwen3-coder",
      "fast": "google/gemini-2.5-flash",
      "long_context": "moonshotai/kimi-k2",
      "backup": "z-ai/glm-4.5"
    },
    "cost_per_1m_tokens": {
      "anthropic/claude-opus-4.1": 15.0,
      "anthropic/claude-sonnet-4": 3.0,
      "qwen/qwen3-coder": 0.20,
      "google/gemini-2.5-flash": 0.075,
      "moonshotai/kimi-k2": 3.0,
      "z-ai/glm-4.5": 1.0
    }
  }
}
EOF
    print_status "Portkey configuration created"
else
    print_status "Portkey configuration exists"
fi

# 6. Update main configuration
echo ""
echo "6️⃣  Updating Sophia configuration..."
if [ ! -f config/sophia.yaml ]; then
    cat > config/sophia.yaml << 'EOF'
# Sophia AI Configuration - Minimal and Powerful
app:
  name: sophia-ai
  version: 2.0.0
  environment: development

asip:
  enabled: true
  mode: MAXIMUM_PERFORMANCE
  orchestrator: UltimateAdaptiveOrchestrator
  entropy_thresholds:
    reactive: 0.3
    deliberative: 0.7
    symbiotic: 0.9
  performance_targets:
    instantiation_time_us: 3
    throughput_tasks_sec: 15000
    latency_p99_ms: 10

portkey:
  enabled: true
  cache: true
  fallback: true
  cost_tracking: true
  
services:
  database: postgresql://localhost/sophia
  redis: ${REDIS_URL}
  vector_db: http://localhost:6333
  
ai:
  default_model: qwen/qwen3-coder
  temperature: 0.7
  max_tokens: 2000
  
security:
  jwt_enabled: true
  cors_enabled: true
  
monitoring:
  prometheus: true
  metrics_port: 9090
EOF
    print_status "Sophia configuration created"
else
    print_status "Sophia configuration exists"
fi

# 7. Build Rust extensions (if Rust is available)
echo ""
echo "7️⃣  Checking for Rust extensions..."
if command -v cargo &> /dev/null; then
    if [ -f asip/rust_core/Cargo.toml ]; then
        print_status "Building Rust extensions..."
        cd asip/rust_core
        cargo build --release 2>/dev/null && print_status "Rust extensions built" || print_warning "Rust build failed"
        cd ../..
    else
        print_warning "No Rust extensions to build"
    fi
else
    print_warning "Rust not installed - skipping extensions"
fi

# 8. Compile Numba JIT functions
echo ""
echo "8️⃣  Pre-compiling Numba JIT functions..."
python << 'EOF' 2>/dev/null
import sys
try:
    from asip.numba_ops import warmup_jit
    import asyncio
    asyncio.run(warmup_jit())
    print("✅ Numba JIT compilation complete")
except ImportError:
    print("⚠️  Numba not available - will use fallback")
except Exception as e:
    print(f"⚠️  JIT compilation skipped: {e}")
EOF

# 9. Setup Lambda connection (optional)
echo ""
echo "9️⃣  Checking Lambda Labs configuration..."
if [ -n "$LAMBDA_API_KEY" ]; then
    print_status "Lambda API key found"
    
    # Create Lambda setup script
    cat > scripts/setup_lambda_tunnel.sh << 'EOF'
#!/bin/bash
# Setup SSH tunnel to Lambda GPU
LAMBDA_IP=${LAMBDA_GPU_IP:-}
if [ -n "$LAMBDA_IP" ]; then
    echo "Setting up tunnel to Lambda GPU at $LAMBDA_IP..."
    ssh -N -L 5555:localhost:5555 ubuntu@$LAMBDA_IP &
    echo "Tunnel established on port 5555"
else
    echo "No Lambda GPU IP configured"
fi
EOF
    chmod +x scripts/setup_lambda_tunnel.sh
    print_status "Lambda setup script created"
else
    print_warning "No Lambda API key - GPU features disabled"
fi

# 10. Create VS Code extension (for Codespaces)
if [ "$ENVIRONMENT" = "codespaces" ]; then
    echo ""
    echo "🔟 Setting up VS Code extension for Codespaces..."
    
    # Create minimal VS Code settings
    mkdir -p .vscode
    cat > .vscode/settings.json << 'EOF'
{
    "sophia-ai.enabled": true,
    "sophia-ai.api.endpoint": "http://localhost:${AGENT_API_PORT:-8003}",
    "sophia-ai.shortcuts.assist": "alt+a",
    "sophia-ai.shortcuts.review": "alt+r",
    "sophia-ai.shortcuts.optimize": "alt+o",
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true
}
EOF
    print_status "VS Code settings configured"
fi

# 11. Start services
echo ""
echo "1️⃣1️⃣ Starting Sophia AI services..."

# Check if Redis is running
if command -v redis-cli &> /dev/null; then
    redis-cli ping > /dev/null 2>&1 && print_status "Redis is running" || {
        print_warning "Starting Redis..."
        redis-server --daemonize yes
    }
fi

# Start the backend
echo ""
echo "🎯 Starting Sophia AI Backend..."
cd backend
nohup python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../.backend_pid
cd ..

# Wait for backend to start
sleep 3

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_status "Backend started (PID: $BACKEND_PID)"
else
    print_error "Backend failed to start - check logs/backend.log"
fi

# 12. Run validation tests
echo ""
echo "1️⃣2️⃣ Running validation tests..."
python << 'EOF'
import requests
import time

print("Testing API endpoints...")

try:
    # Test health endpoint
    response = requests.get(f"http://localhost:{os.getenv('AGENT_API_PORT','8003')}/health", timeout=5)
    if response.status_code == 200:
        print("✅ Health check passed")
        data = response.json()
        print(f"   Version: {data.get('version')}")
        print(f"   ASIP: {data.get('asip')}")
        print(f"   Portkey: {data.get('portkey')}")
    else:
        print("❌ Health check failed")
except Exception as e:
    print(f"⚠️  API not responding: {e}")

# Test performance
print("\nBenchmarking performance...")
try:
    from asip.numba_ops import benchmark_entropy, benchmark_parallel_scoring
    benchmark_entropy(10000)
    benchmark_parallel_scoring(1000)
except:
    print("⚠️  Performance benchmarks not available")
EOF

# 13. Display final status
echo ""
echo "=============================================="
echo "✨ SOPHIA AI SETUP COMPLETE!"
echo "=============================================="
echo ""
echo "📊 Status Summary:"
echo "   • Environment: $ENVIRONMENT"
echo "   • Backend: http://localhost:${AGENT_API_PORT:-8003}"
echo "   • API Docs: http://localhost:${AGENT_API_PORT:-8003}/docs"
echo "   • Health: http://localhost:${AGENT_API_PORT:-8003}/health"
echo "   • Metrics: http://localhost:${AGENT_API_PORT:-8003}/metrics"
echo ""

if [ "$ENVIRONMENT" = "codespaces" ]; then
    echo "💡 Codespaces Quick Start:"
    echo "   • Select code + Alt+A for AI assistance"
    echo "   • Alt+R to review current file"
    echo "   • Alt+O to optimize selection"
    echo ""
fi

echo "💰 Cost Optimization:"
echo "   • Qwen3-Coder: \$0.20/1M tokens (code)"
echo "   • Gemini Flash: \$0.075/1M tokens (fast)"
echo "   • Claude Sonnet: \$3/1M tokens (balanced)"
echo "   • All routed through Portkey with caching"
echo ""

echo "⚡ Performance Targets:"
echo "   • Agent instantiation: 3μs"
echo "   • Throughput: 15k tasks/sec"
echo "   • API cost reduction: 75%"
echo ""

echo "📝 Next Steps:"
echo "   1. Update .env with your API keys"
echo "   2. Configure Portkey virtual keys"
echo "   3. Test API: curl http://localhost:${AGENT_API_PORT:-8003}/health"
echo "   4. View logs: tail -f logs/backend.log"
echo ""

echo "🎉 Happy coding with Sophia AI!"
