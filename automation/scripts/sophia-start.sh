#!/bin/bash
# ==============================================
# SOPHIA INTEL AI - UNIVERSAL START SCRIPT
# Cross-platform startup with auto-detection
# ==============================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
AUTOMATION_DIR="${PROJECT_ROOT}/automation"

# Default values
MODE="auto"
ENVIRONMENT="auto"
PROFILE="development"
VERBOSE="false"
DRY_RUN="false"
FORCE="false"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%H:%M:%S')

    case $level in
        "INFO")  echo -e "${BLUE}[${timestamp}] ℹ️  ${message}${NC}" ;;
        "SUCCESS") echo -e "${GREEN}[${timestamp}] ✅ ${message}${NC}" ;;
        "WARNING") echo -e "${YELLOW}[${timestamp}] ⚠️  ${message}${NC}" ;;
        "ERROR")   echo -e "${RED}[${timestamp}] ❌ ${message}${NC}" ;;
        "DEBUG")   [[ "$VERBOSE" == "true" ]] && echo -e "${PURPLE}[${timestamp}] 🔍 ${message}${NC}" ;;
        "HEADER")  echo -e "${CYAN}[${timestamp}] 🚀 ${message}${NC}" ;;
    esac
}

# Platform detection
detect_platform() {
    case "$(uname -s)" in
        "Darwin")
            echo "macos"
            ;;
        "Linux")
            if [[ -f /etc/os-release ]]; then
                . /etc/os-release
                case "$ID" in
                    "ubuntu"|"debian") echo "linux-debian" ;;
                    "centos"|"rhel"|"fedora") echo "linux-rhel" ;;
                    "alpine") echo "linux-alpine" ;;
                    *) echo "linux-generic" ;;
                esac
            else
                echo "linux-generic"
            fi
            ;;
        "MINGW"*|"CYGWIN"*|"MSYS"*)
            echo "windows"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Environment detection
detect_environment() {
    if [[ -n "${KUBERNETES_SERVICE_HOST:-}" ]]; then
        echo "kubernetes"
    elif [[ -n "${DOCKER_HOST:-}" ]] || [[ -f "/.dockerenv" ]]; then
        echo "docker"
    elif [[ -f "/etc/systemd/system.conf" ]] && [[ "$USER" == "root" ]]; then
        echo "systemd"
    elif [[ -d "/Library/LaunchDaemons" ]] && [[ "$(uname -s)" == "Darwin" ]]; then
        echo "launchd"
    else
        echo "development"
    fi
}

# Check system requirements
check_requirements() {
    log "INFO" "Checking system requirements"

    local missing_deps=()
    local platform=$(detect_platform)
    local environment=$(detect_environment)

    # Platform-specific requirements
    case "$platform" in
        "macos")
            command -v brew >/dev/null || missing_deps+=("homebrew")
            ;;
        "linux-debian"|"linux-generic")
            command -v apt >/dev/null || command -v apt-get >/dev/null || missing_deps+=("apt")
            ;;
        "linux-rhel")
            command -v yum >/dev/null || command -v dnf >/dev/null || missing_deps+=("yum/dnf")
            ;;
    esac

    # Common requirements
    command -v docker >/dev/null || missing_deps+=("docker")
    command -v python3 >/dev/null || missing_deps+=("python3")
    command -v curl >/dev/null || missing_deps+=("curl")

    # Environment-specific requirements
    case "$environment" in
        "kubernetes")
            command -v kubectl >/dev/null || missing_deps+=("kubectl")
            ;;
        "docker")
            command -v docker-compose >/dev/null || docker compose version >/dev/null 2>&1 || missing_deps+=("docker-compose")
            ;;
    esac

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log "ERROR" "Missing dependencies: ${missing_deps[*]}"
        log "INFO" "Please install missing dependencies and try again"
        return 1
    fi

    log "SUCCESS" "All system requirements satisfied"
    return 0
}

# Install dependencies automatically
install_dependencies() {
    local platform=$(detect_platform)

    log "INFO" "Installing system dependencies for $platform"

    case "$platform" in
        "macos")
            # Install Homebrew if not present
            if ! command -v brew >/dev/null; then
                log "INFO" "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi

            # Install required packages
            brew install --quiet docker docker-compose python3 curl || true
            ;;

        "linux-debian"|"linux-generic")
            if command -v apt-get >/dev/null; then
                sudo apt-get update -qq
                sudo apt-get install -y docker.io docker-compose python3 python3-pip curl

                # Add user to docker group
                sudo usermod -aG docker "$USER" || true
            fi
            ;;

        "linux-rhel")
            if command -v dnf >/dev/null; then
                sudo dnf install -y docker docker-compose python3 python3-pip curl
            elif command -v yum >/dev/null; then
                sudo yum install -y docker docker-compose python3 python3-pip curl
            fi

            # Start Docker service
            sudo systemctl enable docker
            sudo systemctl start docker
            sudo usermod -aG docker "$USER" || true
            ;;

        "linux-alpine")
            sudo apk update
            sudo apk add docker docker-compose python3 py3-pip curl
            sudo rc-update add docker boot
            sudo service docker start
            sudo addgroup "$USER" docker || true
            ;;
    esac

    log "SUCCESS" "Dependencies installed (may require logout/login for Docker group)"
}

# Create configuration
setup_configuration() {
    log "INFO" "Setting up configuration for $ENVIRONMENT environment"

    local config_file="${PROJECT_ROOT}/.env.${ENVIRONMENT}"

    if [[ ! -f "$config_file" ]] && [[ -f "${PROJECT_ROOT}/.env.template" ]]; then
        log "INFO" "Creating environment configuration from template"
        cp "${PROJECT_ROOT}/.env.template" "$config_file"

        # Environment-specific adjustments
        case "$ENVIRONMENT" in
            "development")
                sed -i.bak 's/SOPHIA_ENVIRONMENT=production/SOPHIA_ENVIRONMENT=development/' "$config_file"
                sed -i.bak 's/LOG_LEVEL=ERROR/LOG_LEVEL=INFO/' "$config_file"
                rm -f "${config_file}.bak"
                ;;
            "production")
                sed -i.bak 's/SOPHIA_ENVIRONMENT=development/SOPHIA_ENVIRONMENT=production/' "$config_file"
                sed -i.bak 's/LOG_LEVEL=DEBUG/LOG_LEVEL=ERROR/' "$config_file"
                rm -f "${config_file}.bak"
                ;;
        esac

        log "WARNING" "Please review and update $config_file with your actual configuration"
    fi

    # Create symbolic link for current environment
    if [[ -f "$config_file" ]]; then
        ln -sf ".env.${ENVIRONMENT}" "${PROJECT_ROOT}/.env"
        log "SUCCESS" "Environment configuration linked: .env -> .env.${ENVIRONMENT}"
    fi
}

# Start services based on detected mode
start_services() {
    local mode=$1
    local environment=$2

    log "HEADER" "Starting Sophia Intel AI ($mode mode, $environment environment)"

    case "$mode" in
        "development"|"docker")
            if [[ -f "${PROJECT_ROOT}/docker-compose.enhanced.yml" ]]; then
                log "INFO" "Using enhanced Docker Compose configuration"
                docker-compose -f "${PROJECT_ROOT}/docker-compose.enhanced.yml" up -d
            else
                log "INFO" "Using standard Docker Compose configuration"
                docker-compose -f "${PROJECT_ROOT}/docker-compose.yml" up -d
            fi
            ;;

        "kubernetes")
            if [[ -d "${PROJECT_ROOT}/k8s" ]]; then
                log "INFO" "Deploying to Kubernetes"
                kubectl apply -k "${PROJECT_ROOT}/k8s/overlays/${environment}"
                log "INFO" "Waiting for deployments to be ready..."
                kubectl wait --for=condition=available --timeout=300s deployment --all -n sophia-intel-ai
            else
                log "ERROR" "Kubernetes manifests not found"
                return 1
            fi
            ;;

        "helm")
            if [[ -d "${PROJECT_ROOT}/helm/sophia-intel-ai" ]]; then
                log "INFO" "Deploying with Helm"
                helm upgrade --install sophia-intel-ai "${PROJECT_ROOT}/helm/sophia-intel-ai" \
                    --namespace sophia-intel-ai --create-namespace \
                    --values "${PROJECT_ROOT}/helm/sophia-intel-ai/values-${environment}.yaml" \
                    --wait --timeout 10m
            else
                log "ERROR" "Helm charts not found"
                return 1
            fi
            ;;

        "systemd")
            log "INFO" "Starting with systemd"
            if [[ -f "${AUTOMATION_DIR}/system-services/linux/sophia-intel-ai.service" ]]; then
                sudo cp "${AUTOMATION_DIR}/system-services/linux/sophia-intel-ai.service" /etc/systemd/system/
                sudo systemctl daemon-reload
                sudo systemctl enable sophia-intel-ai
                sudo systemctl start sophia-intel-ai
            else
                log "ERROR" "Systemd service file not found"
                return 1
            fi
            ;;

        "launchd")
            log "INFO" "Starting with launchd"
            if [[ -f "${AUTOMATION_DIR}/system-services/macos/com.sophia.intel.ai.plist" ]]; then
                cp "${AUTOMATION_DIR}/system-services/macos/com.sophia.intel.ai.plist" ~/Library/LaunchAgents/
                launchctl load ~/Library/LaunchAgents/com.sophia.intel.ai.plist
            else
                log "ERROR" "LaunchAgent plist not found"
                return 1
            fi
            ;;

        *)
            log "ERROR" "Unknown startup mode: $mode"
            return 1
            ;;
    esac

    log "SUCCESS" "Services started successfully"
}

# Health check after startup
verify_startup() {
    log "INFO" "Verifying system startup"

    # Wait for services to be ready
    sleep 30

    if command -v python3 >/dev/null; then
        log "INFO" "Running comprehensive health check"
        if python3 "${AUTOMATION_DIR}/scripts/health-check.py" --check-only --format=text; then
            log "SUCCESS" "🎉 All services are healthy!"
            return 0
        else
            log "ERROR" "❌ Some services are not healthy"
            return 1
        fi
    else
        log "WARNING" "Python3 not available, skipping health check"
        return 0
    fi
}

# Show system information
show_info() {
    local platform=$(detect_platform)
    local environment=$(detect_environment)

    echo -e "${CYAN}"
    echo "════════════════════════════════════════════════════════════════"
    echo "  🧠 SOPHIA INTEL AI - STARTUP SCRIPT"
    echo "  📅 $(date '+%Y-%m-%d %H:%M:%S')"
    echo "────────────────────────────────────────────────────────────────"
    echo "  🖥️  Platform: $platform"
    echo "  🌍 Environment: $environment"
    echo "  📂 Project Root: $PROJECT_ROOT"
    echo "  🔧 Mode: $MODE"
    echo "  📊 Profile: $PROFILE"
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

# Show usage information
show_usage() {
    cat << EOF
Sophia Intel AI Universal Startup Script

USAGE:
    $0 [OPTIONS] [COMMAND]

COMMANDS:
    start       Start all services (default)
    stop        Stop all services
    restart     Restart all services
    status      Show service status
    install     Install system dependencies
    config      Setup configuration
    health      Run health check

OPTIONS:
    --mode=MODE             Startup mode (auto|development|kubernetes|helm|systemd|launchd)
    --environment=ENV       Environment (auto|development|staging|production)
    --profile=PROFILE       Configuration profile (development|testing|production)
    --verbose              Enable verbose logging
    --dry-run              Show what would be done without executing
    --force                Force operation even if checks fail
    --help, -h             Show this help message

EXAMPLES:
    $0                                    # Auto-detect and start
    $0 --mode=kubernetes --environment=production
    $0 --profile=development --verbose
    $0 install                           # Install dependencies
    $0 config                            # Setup configuration
    $0 health                            # Run health check

ENVIRONMENT VARIABLES:
    SOPHIA_MODE             Override auto-detected mode
    SOPHIA_ENVIRONMENT      Override auto-detected environment
    SOPHIA_PROFILE          Configuration profile to use
    SOPHIA_VERBOSE          Enable verbose output (true/false)

EOF
}

# Main execution function
main() {
    # Parse command line arguments
    local command="start"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode=*)
                MODE="${1#*=}"
                shift
                ;;
            --environment=*)
                ENVIRONMENT="${1#*=}"
                shift
                ;;
            --profile=*)
                PROFILE="${1#*=}"
                shift
                ;;
            --verbose)
                VERBOSE="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --force)
                FORCE="true"
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            start|stop|restart|status|install|config|health)
                command="$1"
                shift
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Override with environment variables
    MODE="${SOPHIA_MODE:-$MODE}"
    ENVIRONMENT="${SOPHIA_ENVIRONMENT:-$ENVIRONMENT}"
    PROFILE="${SOPHIA_PROFILE:-$PROFILE}"
    VERBOSE="${SOPHIA_VERBOSE:-$VERBOSE}"

    # Auto-detect if needed
    if [[ "$MODE" == "auto" ]]; then
        MODE=$(detect_environment)
        log "DEBUG" "Auto-detected mode: $MODE"
    fi

    if [[ "$ENVIRONMENT" == "auto" ]]; then
        ENVIRONMENT="development"
        if [[ -n "${KUBERNETES_SERVICE_HOST:-}" ]]; then
            ENVIRONMENT="production"
        elif [[ "$USER" == "root" ]]; then
            ENVIRONMENT="production"
        fi
        log "DEBUG" "Auto-detected environment: $ENVIRONMENT"
    fi

    # Show system information
    show_info

    # Execute command
    case "$command" in
        "start")
            if [[ "$DRY_RUN" == "true" ]]; then
                log "INFO" "DRY RUN: Would start services in $MODE mode"
                exit 0
            fi

            check_requirements || [[ "$FORCE" == "true" ]] || exit 1
            setup_configuration
            start_services "$MODE" "$ENVIRONMENT"
            verify_startup
            ;;

        "stop")
            log "INFO" "Stopping services"
            case "$MODE" in
                "development"|"docker")
                    docker-compose -f "${PROJECT_ROOT}/docker-compose.yml" down
                    ;;
                "kubernetes")
                    kubectl delete -k "${PROJECT_ROOT}/k8s/overlays/${ENVIRONMENT}"
                    ;;
                "helm")
                    helm uninstall sophia-intel-ai --namespace sophia-intel-ai
                    ;;
                "systemd")
                    sudo systemctl stop sophia-intel-ai
                    ;;
                "launchd")
                    launchctl unload ~/Library/LaunchAgents/com.sophia.intel.ai.plist
                    ;;
            esac
            ;;

        "restart")
            $0 stop "${@:2}"
            sleep 5
            $0 start "${@:2}"
            ;;

        "status")
            log "INFO" "Checking service status"
            case "$MODE" in
                "development"|"docker")
                    docker-compose -f "${PROJECT_ROOT}/docker-compose.yml" ps
                    ;;
                "kubernetes")
                    kubectl get all -n sophia-intel-ai
                    ;;
                "systemd")
                    systemctl status sophia-intel-ai
                    ;;
                "launchd")
                    launchctl list | grep com.sophia.intel.ai
                    ;;
            esac
            ;;

        "install")
            install_dependencies
            ;;

        "config")
            setup_configuration
            ;;

        "health")
            python3 "${AUTOMATION_DIR}/scripts/health-check.py" --check-only --format=text
            ;;

        *)
            log "ERROR" "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Signal handlers
trap 'log "WARNING" "🛑 Startup interrupted by user"; exit 130' INT TERM

# Execute main function
main "$@"
