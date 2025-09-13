#!/bin/bash

# Sophia + Sophia Deployment Script
# Handles environment setup, dependency installation, and service startup

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
SECRETS_VAULT="$PROJECT_ROOT/.secrets"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."

    # Check Python version
    if ! python3 --version | grep -E "3\.(10|11|12)" > /dev/null; then
        log_error "Python 3.10+ required"
        exit 1
    fi

    # Check for required tools
    for tool in docker redis-cli; do
        if ! command -v $tool &> /dev/null; then
            log_warn "$tool not found, some features may be limited"
        fi
    done

    log_info "System requirements check complete"
}

setup_environment() {
    log_info "Setting up environment..."

    # Create .env if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        log_info "Creating .env file from template..."
        cat > "$ENV_FILE" << 'EOF'
# Sophia + Sophia Environment Configuration

# Deployment Environment
ENVIRONMENT=development
LOG_LEVEL=INFO

# Portkey Virtual Keys (DO NOT COMMIT ACTUAL KEYS)
PORTKEY_API_KEY=
DEEPSEEK_VK=deepseek-vk-24102f
OPENAI_VK=openai-vk-190a60
ANTHROPIC_VK=anthropic-vk-b42804
OPENROUTER_VK=vkj-openrouter-cc4151
PERPLEXITY_VK=perplexity-vk-56c172
GROQ_VK=groq-vk-6b9b52
MISTRAL_VK=mistral-vk-f92861

# Memory Configuration
REDIS_URL=redis://localhost:6379
WEAVIATE_URL=http://localhost:8080
POSTGRES_URL=postgresql://user:pass@localhost/sophia
S3_BUCKET=sophia-sophia-storage

# Security
SECRET_KEY=
ENCRYPTION_KEY=
JWT_SECRET=

# OAuth Tokens (Enterprise Integrations)
SLACK_TOKEN=
LINEAR_TOKEN=
NOTION_TOKEN=
GITHUB_TOKEN=
GONG_API_KEY=

# Feature Flags
ENABLE_SOPHIA=true
ENABLE_ARTEMIS=true
ENABLE_WEB_RESEARCH=true
ENABLE_CACHING=true

EOF
        log_warn "Please configure your .env file with actual values"
    fi

    # Create secrets vault directory
    mkdir -p "$SECRETS_VAULT"
    chmod 700 "$SECRETS_VAULT"

    log_info "Environment setup complete"
}

install_dependencies() {
    log_info "Installing Python dependencies..."

    cd "$PROJECT_ROOT"

    # Use system Python - no virtual environment

    # Upgrade pip for user
    python3 -m pip install --user --upgrade pip

    # Install dependencies with uv if available
    if command -v uv &> /dev/null; then
        log_info "Installing with uv..."
        uv pip sync requirements.txt
    else
        log_info "Installing with pip..."
        pip3 install --user -r requirements.txt
    fi

    # Install development dependencies
    if [ "${1:-}" = "--dev" ]; then
        log_info "Installing development dependencies..."
        [ -f requirements-dev.txt ] && pip3 install --user -r requirements-dev.txt || true
        pre-commit install
    fi

    log_info "Dependencies installed successfully"
}

setup_infrastructure() {
    log_info "Setting up infrastructure services..."

    # Start Redis
    if command -v docker &> /dev/null; then
        log_info "Starting Redis..."
        docker run -d --name sophia-redis \
            -p 6379:6379 \
            --restart unless-stopped \
            redis:alpine 2>/dev/null || log_warn "Redis container already exists"
    else
        log_warn "Docker not found, please start Redis manually"
    fi

    # Start Weaviate (optional for vector memory)
    if [ "${ENABLE_WEAVIATE:-false}" = "true" ]; then
        log_info "Starting Weaviate..."
        docker run -d --name sophia-weaviate \
            -p 8080:8080 \
            --restart unless-stopped \
            -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
            -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
            semitechnologies/weaviate:latest 2>/dev/null || log_warn "Weaviate container already exists"
    fi

    log_info "Infrastructure setup complete"
}

initialize_system() {
    log_info "Initializing Sophia + Sophia system..."

    cd "$PROJECT_ROOT"
    # No venv activation - using system Python

    # Initialize secrets
    log_info "Initializing secrets manager..."
    python3 << 'EOF'
from app.core.secrets_manager import get_secrets_manager
import os

manager = get_secrets_manager()

# Migrate environment variables to secure vault
env_vars = [
    "PORTKEY_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "SECRET_KEY",
    "ENCRYPTION_KEY",
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        manager.set_secret(var, value)
        print(f"✓ Migrated {var} to secure vault")

print("Secrets initialization complete")
EOF

    # Initialize Portkey configuration
    log_info "Validating Portkey configuration..."
    python3 << 'EOF'
from app.core.portkey_manager import get_portkey_manager

try:
    manager = get_portkey_manager()
    print("✓ Portkey manager initialized")
    print(f"  Available providers: {len(manager.VIRTUAL_KEYS)}")
except Exception as e:
    print(f"✗ Portkey initialization failed: {e}")
EOF

    # Test memory router
    log_info "Testing memory router..."
    python3 << 'EOF'
import asyncio
from app.memory.unified_memory_router import get_memory_router

async def test_memory():
    router = get_memory_router()
    try:
        # Test ephemeral storage
        await router.put_ephemeral("test_key", "test_value", ttl_s=60)
        value = await router.get_ephemeral("test_key")
        if value == "test_value":
            print("✓ Memory router operational")
        else:
            print("✗ Memory router test failed")
    except Exception as e:
        print(f"⚠ Memory router partial: {e}")

asyncio.run(test_memory())
EOF

    log_info "System initialization complete"
}

start_services() {
    log_info "Starting Sophia + Sophia services..."

    cd "$PROJECT_ROOT"
    # No venv activation - using system Python

    # Start based on deployment mode
    case "${DEPLOYMENT_MODE:-development}" in
        development)
            log_info "Starting in development mode..."
            python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
            ;;
        production)
            log_info "Starting in production mode..."
            gunicorn app.main:app \
                --workers 4 \
                --worker-class uvicorn.workers.UvicornWorker \
                --bind 0.0.0.0:8000 \
                --access-logfile - \
                --error-logfile -
            ;;
        test)
            log_info "Running tests..."
            pytest tests/ -v --cov=app
            ;;
        *)
            log_error "Unknown deployment mode: ${DEPLOYMENT_MODE}"
            exit 1
            ;;
    esac
}

health_check() {
    log_info "Running health checks..."

    # Check API endpoint
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_info "✓ API is healthy"
    else
        log_warn "✗ API is not responding"
    fi

    # Check Redis
    if redis-cli ping > /dev/null 2>&1; then
        log_info "✓ Redis is healthy"
    else
        log_warn "✗ Redis is not responding"
    fi

    # Check orchestrators
    python3 << 'EOF'
import asyncio
from app.sophia.sophia_orchestrator import SophiaOrchestrator
from app.sophia.sophia_orchestrator import ArtemisOrchestrator

async def check_orchestrators():
    try:
        sophia = SophiaOrchestrator()
        sophia = ArtemisOrchestrator()
        print("✓ Orchestrators initialized")
    except Exception as e:
        print(f"✗ Orchestrator check failed: {e}")

asyncio.run(check_orchestrators())
EOF
}

cleanup() {
    log_info "Cleaning up..."

    # Stop services gracefully
    if [ -f "/tmp/sophia-sophia.pid" ]; then
        kill $(cat /tmp/sophia-sophia.pid) 2>/dev/null || true
        rm /tmp/sophia-sophia.pid
    fi

    # Optionally stop Docker containers
    if [ "${STOP_CONTAINERS:-false}" = "true" ]; then
        docker stop sophia-redis sophia-weaviate 2>/dev/null || true
    fi

    log_info "Cleanup complete"
}

# Main execution
main() {
    case "${1:-}" in
        install)
            check_requirements
            setup_environment
            install_dependencies "${2:-}"
            ;;
        setup)
            check_requirements
            setup_environment
            install_dependencies
            setup_infrastructure
            initialize_system
            ;;
        start)
            DEPLOYMENT_MODE="${2:-development}" start_services
            ;;
        test)
            DEPLOYMENT_MODE="test" start_services
            ;;
        health)
            health_check
            ;;
        clean)
            cleanup
            ;;
        all)
            check_requirements
            setup_environment
            install_dependencies
            setup_infrastructure
            initialize_system
            start_services
            ;;
        *)
            echo "Usage: $0 {install|setup|start|test|health|clean|all} [options]"
            echo ""
            echo "Commands:"
            echo "  install [--dev]  Install dependencies"
            echo "  setup           Full environment setup"
            echo "  start [mode]    Start services (development/production)"
            echo "  test            Run test suite"
            echo "  health          Health check"
            echo "  clean           Cleanup resources"
            echo "  all             Complete setup and start"
            exit 1
            ;;
    esac
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
